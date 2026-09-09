from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import MonitoringSession, Prediction, MonitoringEvent, SignalRecording
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class SessionRequest(BaseModel):
    subject_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)


class SignalChunkRequest(BaseModel):
    samples: list[float] = Field(min_length=1, max_length=10000)
    sampling_rate: int = Field(default=250, gt=0, le=1000)
    source: str = Field(default="REPLAY", pattern="^(LIVE|REPLAY|HISTORICAL)$")


def _session_dict(row):
    return {"id": row.id, "session_id": row.session_id, "subject_id": row.subject_id,
            "device_id": row.device_id, "status": row.status,
            "start_time": row.started_at.isoformat() if row.started_at else None,
            "end_time": row.ended_at.isoformat() if row.ended_at else None,
            "total_samples": row.total_samples}


@router.get("/sessions")
async def sessions(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(MonitoringSession).order_by(MonitoringSession.started_at.desc()))).scalars()
    return [_session_dict(row) for row in rows]


@router.post("/sessions/start", status_code=201)
async def start_session(payload: SessionRequest, db: AsyncSession = Depends(get_db)):
    session_id = str(uuid4())
    row = MonitoringSession(id=session_id, session_id=session_id,
                            subject_id=payload.subject_id, device_id=payload.device_id)
    db.add(row)
    await db.commit()
    return _session_dict(row)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(MonitoringSession).where(MonitoringSession.session_id == session_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Session not found")
    return _session_dict(row)


@router.put("/sessions/{session_id}/stop")
async def stop_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(MonitoringSession).where(MonitoringSession.session_id == session_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Session not found")
    row.status = "stopped"
    row.ended_at = datetime.utcnow()
    await db.commit()
    return _session_dict(row)


@router.get("/sessions/{session_id}/predictions")
async def prediction_history(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Prediction).where(Prediction.session_id == session_id).order_by(Prediction.timestamp.desc()))).scalars()
    return [{"id": row.id, "prediction": row.prediction, "confidence": row.confidence,
             "probability_abnormal": row.probability_abnormal, "signal_quality": row.signal_quality,
             "timestamp": row.timestamp.isoformat() if row.timestamp else None} for row in rows]


@router.post("/sessions/{session_id}/chunks", status_code=202)
async def ingest_chunk(session_id: str, payload: SignalChunkRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(MonitoringSession, session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    if session.status != "active":
        raise HTTPException(409, "Session is not active")
    try:
        messages = await monitoring_service.ingest(db, session_id, payload.samples, payload.sampling_rate, payload.source)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    session.total_samples += len(payload.samples)
    await db.commit()
    return {"session_id": session_id, "accepted_samples": len(payload.samples), "emitted_inferences": messages}


@router.get("/sessions/{session_id}/events")
async def event_history(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(MonitoringEvent).where(MonitoringEvent.session_id == session_id).order_by(MonitoringEvent.start_time.desc()))).scalars()
    return [{"id": row.id, "state": row.state, "source": row.source, "start_time": row.start_time.isoformat() if row.start_time else None, "end_time": row.end_time.isoformat() if row.end_time else None, "peak_probability": row.peak_probability, "n_windows": row.n_windows} for row in rows]


@router.get("/sessions/{session_id}/signals")
async def signal_history(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(SignalRecording).where(SignalRecording.session_id == session_id).order_by(SignalRecording.created_at.desc()))).scalars()
    return [{"id": row.id, "modality": row.modality, "sampling_rate": row.sampling_rate, "n_samples": row.n_samples, "quality_state": row.quality_state, "created_at": row.created_at.isoformat() if row.created_at else None} for row in rows]
