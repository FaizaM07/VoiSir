from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./stt_comparison.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class TranscriptionRecord(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    audio_filename = Column(String, index=True)
    whisper_output = Column(String)
    wav2vec2_output = Column(String)
    ground_truth = Column(String)
    whisper_accuracy = Column(Float)
    wav2vec2_accuracy = Column(Float)
    whisper_latency = Column(Float)
    wav2vec2_latency = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()