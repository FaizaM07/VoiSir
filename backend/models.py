import whisper
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import librosa
import time
import numpy as np
from scipy.io import wavfile
import subprocess
import os

class STTModels:
    def __init__(self):
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        
        print("Loading Wav2Vec2 model...")
        self.wav2vec2_processor = Wav2Vec2Processor.from_pretrained(
            "facebook/wav2vec2-base-960h"
        )
        self.wav2vec2_model = Wav2Vec2ForCTC.from_pretrained(
            "facebook/wav2vec2-base-960h"
        )
        
        print("Models loaded successfully!")

    def load_audio_file(self, audio_path: str):
        """Load audio file regardless of format"""
        try:
            # Try reading as WAV first
            sample_rate, audio = wavfile.read(audio_path)
            
            # Convert to float32 and normalize
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            else:
                audio = audio.astype(np.float32)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            # Convert stereo to mono if needed
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
                
            return audio
            
        except (ValueError, Exception) as e:
            print(f"Failed to read as WAV: {e}")
            print("Attempting to read as WebM/other format with pydub...")
            
            # Try using pydub for other formats (WebM, MP3, etc.)
            try:
                from pydub import AudioSegment
                
                # Load audio with pydub
                audio_segment = AudioSegment.from_file(audio_path)
                
                # Convert to mono and set sample rate to 16kHz
                audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
                
                # Convert to numpy array
                samples = np.array(audio_segment.get_array_of_samples())
                audio = samples.astype(np.float32) / 32768.0  # Normalize
                
                return audio
                
            except ImportError:
                raise Exception(
                    "pydub is not installed. Install it with: pip install pydub\n"
                    "Note: pydub also requires FFmpeg to be installed on your system."
                )
            except Exception as e:
                raise Exception(f"Failed to load audio file: {str(e)}")

    def transcribe_whisper(self, audio_path: str):
        """Transcribe audio using Whisper"""
        start_time = time.time()
        
        # Load audio (handles multiple formats)
        audio = self.load_audio_file(audio_path)
        
        # Transcribe with pre-loaded audio
        result = self.whisper_model.transcribe(audio, fp16=False)
        latency = time.time() - start_time
        return result["text"].strip(), latency

    def transcribe_wav2vec2(self, audio_path: str):
        """Transcribe audio using Wav2Vec2"""
        start_time = time.time()
        
        try:
            # Load audio (handles multiple formats)
            speech = self.load_audio_file(audio_path)
            
            # Process audio
            inputs = self.wav2vec2_processor(
                speech, 
                sampling_rate=16000, 
                return_tensors="pt", 
                padding=True
            )
            
            # Get logits
            with torch.no_grad():
                logits = self.wav2vec2_model(inputs.input_values).logits
            
            # Decode
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.wav2vec2_processor.batch_decode(predicted_ids)[0]
            
            latency = time.time() - start_time
            return transcription.strip(), latency
            
        except Exception as e:
            print(f"Wav2Vec2 transcription error: {str(e)}")
            raise

# Global instance
stt_models = None

def get_stt_models():
    global stt_models
    if stt_models is None:
        stt_models = STTModels()
    return stt_models