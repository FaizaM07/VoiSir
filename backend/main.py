from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import os
from pathlib import Path
from jiwer import wer
from typing import List

from database import init_db, get_db, TranscriptionRecord
from schemas import (
    TranscriptionResponse, 
    EvaluationRequest, 
    EvaluationResponse,
    RecordResponse
)
from models import get_stt_models

app = FastAPI(title="STT Comparison API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize database
init_db()

# Load models on startup
@app.on_event("startup")
async def startup_event():
    print("Initializing STT models...")
    get_stt_models()
    print("Server ready!")

@app.get("/")
def read_root():
    return {"message": "STT Comparison API is running!"}
@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Receive audio file and transcribe using both models
    """
    print(f"\n=== Transcription Request ===")
    print(f"Filename: {file.filename}")
    print(f"Content Type: {file.content_type}")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    print(f"Saving file to: {file_path}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File saved to: {file_path}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")
    
    # Get models
    try:
        models = get_stt_models()
        print("Models retrieved successfully")
    except Exception as e:
        print(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model loading error: {str(e)}")
    
    try:
        # Transcribe with Whisper
        print("Starting Whisper transcription...")
        whisper_text, whisper_latency = models.transcribe_whisper(str(file_path))
        print(f"Whisper done: {whisper_text[:50]}... (latency: {whisper_latency}s)")
        
        # Transcribe with Wav2Vec2
        print("Starting Wav2Vec2 transcription...")
        wav2vec2_text, wav2vec2_latency = models.transcribe_wav2vec2(str(file_path))
        print(f"Wav2Vec2 done: {wav2vec2_text[:50]}... (latency: {wav2vec2_latency}s)")
        
        return TranscriptionResponse(
            whisper_output=whisper_text,
            wav2vec2_output=wav2vec2_text,
            whisper_latency=round(whisper_latency, 3),
            wav2vec2_latency=round(wav2vec2_latency, 3)
        )
    except Exception as e:
        import traceback
        print(f"\n=== TRANSCRIPTION ERROR ===")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_transcriptions(
    eval_request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate transcriptions against ground truth and save to database
    """
    ground_truth = eval_request.ground_truth.lower().strip()
    whisper_output = eval_request.whisper_output.lower().strip()
    wav2vec2_output = eval_request.wav2vec2_output.lower().strip()
    
    # Calculate Word Error Rate (WER)
    whisper_wer = wer(ground_truth, whisper_output) if ground_truth else 0
    wav2vec2_wer = wer(ground_truth, wav2vec2_output) if ground_truth else 0
    
    # Calculate accuracy (1 - WER)
    whisper_accuracy = max(0, (1 - whisper_wer) * 100)
    wav2vec2_accuracy = max(0, (1 - wav2vec2_wer) * 100)
    
    # Save to database
    db_record = TranscriptionRecord(
        audio_filename=eval_request.audio_filename,
        whisper_output=eval_request.whisper_output,
        wav2vec2_output=eval_request.wav2vec2_output,
        ground_truth=eval_request.ground_truth,
        whisper_accuracy=round(whisper_accuracy, 2),
        wav2vec2_accuracy=round(wav2vec2_accuracy, 2),
        whisper_latency=eval_request.whisper_latency,
        wav2vec2_latency=eval_request.wav2vec2_latency
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return EvaluationResponse(
        whisper_accuracy=round(whisper_accuracy, 2),
        wav2vec2_accuracy=round(wav2vec2_accuracy, 2),
        whisper_wer=round(whisper_wer, 4),
        wav2vec2_wer=round(wav2vec2_wer, 4),
        message="Evaluation completed and saved to database"
    )

@app.get("/records", response_model=List[RecordResponse])
async def get_all_records(db: Session = Depends(get_db)):
    """
    Get all transcription records from database
    """
    records = db.query(TranscriptionRecord).order_by(
        TranscriptionRecord.created_at.desc()
    ).all()
    return records

@app.delete("/records/{record_id}")
async def delete_record(record_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific record
    """
    record = db.query(TranscriptionRecord).filter(
        TranscriptionRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Delete associated audio file
    audio_path = UPLOAD_DIR / record.audio_filename
    if audio_path.exists():
        os.remove(audio_path)
    
    db.delete(record)
    db.commit()
    
    return {"message": "Record deleted successfully"}