from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import InferenceRun, Prediction, MonitoringSession
from backend.services.model_service import model_service, ModelUnavailable

router = APIRouter(prefix="/inference", tags=["inference"])


class InferenceRequest(BaseModel):
    session_id: str = Field(min_length=1)
    samples: list[float] = Field(min_length=1)
    sampling_rate: int = Field(default=250, gt=0)
    source: str = "LIVE"


@router.post("", status_code=201)
async def infer(payload: InferenceRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(MonitoringSession, payload.session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    try:
        result = model_service.predict_ecg(payload.samples, payload.sampling_rate)
    except ModelUnavailable as exc:
        raise HTTPException(503, str(exc))
    run_id = str(uuid4())
    run = InferenceRun(id=run_id, session_id=payload.session_id,
                       model_version=result["model_version"], model_mode=result["model_mode"],
                       source=payload.source, latency_ms=result["latency_ms"])
    prediction = Prediction(id=str(uuid4()), session_id=payload.session_id,
                            inference_run_id=run_id, prediction=result["prediction"],
                            probability_abnormal=float(result.get("probability_abnormal") or 0.0),
                            confidence=result["confidence"], signal_quality=result["signal_quality"],
                            available_modalities=result["available_modalities"])
    session.total_samples += len(payload.samples)
    db.add_all([run, prediction])
    await db.commit()
    result.update({"inference_run_id": run_id, "timestamp": prediction.timestamp.isoformat()})
    return result
