"""Stateful centralized streaming ingestion for active monitoring sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.websocket_manager import manager
from backend.db.models import InferenceRun, MonitoringEvent, Prediction, SignalRecording
from backend.services.model_service import model_service
from inference.streaming import StreamingInferenceEngine, WindowInference


@dataclass
class _Runtime:
	engine: StreamingInferenceEngine
	source: str
	last_state: str | None = None
	open_event_id: str | None = None


class MonitoringService:
	def __init__(self):
		self._runtimes: dict[str, _Runtime] = {}

	def _runtime(self, session_id: str, sampling_rate: int, source: str) -> _Runtime:
		runtime = self._runtimes.get(session_id)
		if runtime is not None:
			if runtime.engine.source_fs != sampling_rate:
				raise ValueError("sampling_rate cannot change within a session")
			return runtime

		def predictor(window, fs):
			result = model_service.predict_ecg(window, fs)
			return WindowInference(float(result.get("probability_abnormal") or 0.5), "UNRELIABLE" if result["prediction"] == "UNRELIABLE_SIGNAL" else result["signal_quality"], float(result["confidence"]))

		runtime = _Runtime(StreamingInferenceEngine(predictor, sampling_rate), source)
		self._runtimes[session_id] = runtime
		return runtime

	async def ingest(self, db: AsyncSession, session_id: str, samples: list[float], sampling_rate: int, source: str) -> list[dict]:
		runtime = self._runtime(session_id, sampling_rate, source)
		chunk = np.asarray(samples, dtype=np.float32)
		recording = SignalRecording(id=str(uuid4()), session_id=session_id, modality="ECG", sampling_rate=sampling_rate, n_samples=len(chunk), quality_state="PENDING")
		db.add(recording)
		outputs = runtime.engine.push(chunk)
		messages = []
		for output in outputs:
			state, probability = output["state"], float(output["smoothed_probability"])
			prediction = "UNRELIABLE_SIGNAL" if state == "UNRELIABLE" else ("POTENTIALLY_ABNORMAL" if state == "POTENTIALLY_ABNORMAL" else "NORMAL_MONITORED_PATTERN")
			run_id = str(uuid4())
			db.add(InferenceRun(id=run_id, session_id=session_id, model_version=model_service.model_version, model_mode="ECG_ONLY", source=source, latency_ms=0.0))
			db.add(Prediction(id=str(uuid4()), session_id=session_id, inference_run_id=run_id, prediction=prediction, probability_abnormal=probability, confidence=max(probability, 1 - probability) if state != "UNRELIABLE" else 0.0, signal_quality=output["signal_quality"], available_modalities=["ECG"]))
			await self._update_event(db, runtime, session_id, state, probability, source)
			messages.append({"type": "inference", "session_id": session_id, "source": source, "timestamp": datetime.utcnow().isoformat(), "model_version": model_service.model_version, "prediction": prediction, "confidence": round(max(probability, 1 - probability) if state != "UNRELIABLE" else 0.0, 4), "probability_abnormal": round(probability, 4), "signal_quality": output["signal_quality"], "window_start_seconds": output["window_start_seconds"], "window_end_seconds": output["window_end_seconds"], "latency_ms": 0.0})
		recording.quality_state = outputs[-1]["signal_quality"] if outputs else "PENDING"
		await db.commit()
		for message in messages:
			await manager.broadcast("live", message)
		return messages

	async def _update_event(self, db: AsyncSession, runtime: _Runtime, session_id: str, state: str, probability: float, source: str) -> None:
		if state == runtime.last_state and runtime.open_event_id:
			event = await db.get(MonitoringEvent, runtime.open_event_id)
			if event:
				event.n_windows += 1
				event.peak_probability = max(event.peak_probability, probability)
			return
		if runtime.open_event_id:
			event = await db.get(MonitoringEvent, runtime.open_event_id)
			if event:
				event.end_time = datetime.utcnow()
			runtime.open_event_id = None
		runtime.last_state = state
		if state != "NORMAL":
			event_id = str(uuid4())
			db.add(MonitoringEvent(id=event_id, session_id=session_id, state=state, peak_probability=probability, n_windows=1, source=source))
			runtime.open_event_id = event_id


monitoring_service = MonitoringService()
