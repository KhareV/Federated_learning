# Phase 7 — Hosted MODEL_V1 and Backend Persistence

Implemented a centralized hosted model service and backend persistence layer.

- `ModelService` loads the CNN, frozen preprocessing statistics, calibration,
  and threshold once per process.
- `/inference` accepts a session-bound ECG window and returns the model,
  prediction, confidence, signal quality, latency, and disclaimer contract.
- `MonitoringSession`, `InferenceRun`, `Prediction`, `SignalRecording`, and
  `Device` database entities are available through SQLAlchemy.
- Session start/lookup/stop and prediction history routes persist data in the
  configured SQLite database.
- Missing model artifacts return an explicit unavailable state rather than a
  fabricated prediction.
- Authentication is not required; subjects, sessions, and devices are explicit
  data identifiers only.

API integration tests cover session lifecycle, real locked-model inference,
prediction persistence, and unknown-session rejection. Frontend `/api` proxy
and route reconciliation are handled in Phase 8.
