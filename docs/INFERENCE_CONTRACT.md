# NHM Inference Contract

The centralized inference response contains:

```json
{
  "model_version": "MODEL_V1",
  "prediction": "NORMAL_MONITORED_PATTERN",
  "confidence": 0.94,
  "signal_quality": "GOOD",
  "available_modalities": ["ECG"],
  "model_mode": "ECG_ONLY",
  "timestamp": "ISO-8601 UTC",
  "latency_ms": 21,
  "disclaimer": "Research prototype; not a medical diagnosis."
}
```

Confidence is calibrated validation output. The response also carries input
source (`LIVE`, `REPLAY`, `SIMULATED`, or `HISTORICAL`) and provenance needed
to reproduce the result.

