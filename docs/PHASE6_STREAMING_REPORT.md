# Phase 6 — Deterministic Streaming Inference

Implemented `StreamingInferenceEngine` buffers incoming samples, emits 10-second
windows every 5 seconds, calls a canonical predictor, applies probability
smoothing, and tracks `NORMAL`, `POTENTIALLY_ABNORMAL`, and `UNRELIABLE`
states. Events record start/end times, peak probability, and window count.

The `locked_model_predictor` factory loads the Phase 3 CNN, frozen preprocessing
statistics, and the Phase 4 calibrator. It rejects poor-quality windows as
`UNRELIABLE`; it never converts them into abnormal predictions.

Phase-gate tests verify chunk-boundary invariance, deterministic replay,
abnormal-event coalescing, and unreliable-signal behavior. Event summary fields
include processed windows, abnormal-event count, false alarms per hour,
unreliable periods, and state-flapping count. Ground-truth event sensitivity and
detection delay require an event-labelled replay corpus and remain pending.
