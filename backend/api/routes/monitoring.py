from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import MonitoringSession, Prediction

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class SessionRequest(BaseModel):
    subject_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)


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
