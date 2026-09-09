from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, Boolean
from backend.db.database import Base
from datetime import datetime

class SystemEvent(Base):
    __tablename__ = "system_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)
    source = Column(String)
    message = Column(String)
    extra_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="disconnected")
    sampling_rate = Column(Integer, default=250)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)


class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"
    id = Column(String, primary_key=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    subject_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    status = Column(String, default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_samples = Column(Integer, default=0)


class InferenceRun(Base):
    __tablename__ = "inference_runs"
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    model_version = Column(String, nullable=False)
    model_mode = Column(String, default="ECG_ONLY")
    source = Column(String, default="LIVE")
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    inference_run_id = Column(String, index=True, nullable=False)
    prediction = Column(String, nullable=False)
    probability_abnormal = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    signal_quality = Column(String, nullable=False)
    available_modalities = Column(JSON, default=list)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SignalRecording(Base):
    __tablename__ = "signal_recordings"
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    modality = Column(String, nullable=False)
    artifact_ref = Column(String, nullable=True)
    sampling_rate = Column(Float, nullable=False)
    n_samples = Column(Integer, default=0)
    quality_state = Column(String, default="UNRELIABLE")
    created_at = Column(DateTime, default=datetime.utcnow)
