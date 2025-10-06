from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TranscriptionResponse(BaseModel):
    whisper_output: str
    wav2vec2_output: str
    whisper_latency: float
    wav2vec2_latency: float

class EvaluationRequest(BaseModel):
    audio_filename: str
    whisper_output: str
    wav2vec2_output: str
    ground_truth: str
    whisper_latency: float
    wav2vec2_latency: float

class EvaluationResponse(BaseModel):
    whisper_accuracy: float
    wav2vec2_accuracy: float
    whisper_wer: float
    wav2vec2_wer: float
    message: str

class RecordResponse(BaseModel):
    id: int
    audio_filename: str
    whisper_output: str
    wav2vec2_output: str
    ground_truth: str
    whisper_accuracy: float
    wav2vec2_accuracy: float
    whisper_latency: float
    wav2vec2_latency: float
    created_at: datetime

    class Config:
        from_attributes = True