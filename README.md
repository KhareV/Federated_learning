# NHM Centralized ECG Monitor

An authentication-free, centralized ECG research prototype. Its output is
`NORMAL_MONITORED_PATTERN`, `POTENTIALLY_ABNORMAL`, or `UNRELIABLE_SIGNAL`;
it is not a medical diagnosis, treatment system, or emergency tool.

## Current scope

- Real PTB-XL patient-level development, preprocessing, calibration, and ECG CNN inference.
- MIT-BIH external evaluation using a frozen protocol.
- Session-bound streaming ingestion, persisted predictions/events, WebSocket inference messages, and the SvelteKit central-monitor dashboard.
- BIDMC synchronization, PPG/SpO₂ quality processing, and missing-modality interfaces only. No supervised multimodal performance is claimed because compatible labels are not available.

Federated learning, secure aggregation, differential privacy, edge optimization, hardware collection, and wearable-domain validation are deferred.

## Release status

The historical `MODEL_V1` is **not release eligible**: its corrected MIT-BIH external evaluation has AUROC 0.7404 and specificity 0.0710. A candidate is eligible only if frozen MIT-BIH evaluation reaches AUROC >= 0.80, sensitivity >= 0.70, and specificity >= 0.70 without tuning on MIT-BIH. See `docs/EXTERNAL_GATE_AUDIT.md`.

## Run

```bash
python3 scripts/validate_datasets.py
python3 scripts/audit_label_contracts.py
python3 -m pytest -q
python3 scripts/run_demo.py --duration-seconds 10 --seed 91
```

Start the backend with `uvicorn backend.main:app --port 8000`, then run the SvelteKit frontend from `frontend/` with `npm run dev`. The active API is:

- `GET /system/health`, `GET /system/model`
- session lifecycle under `/monitoring/sessions`
- `POST /monitoring/sessions/{session_id}/chunks`
- prediction, event, and signal history under the same session
- `GET /reports` for committed evidence artifacts
- WebSocket `/ws/live/{client_id}` for inference messages

Use `configs/centralized_ecg_release_v2.json` as the source configuration for the current centralized release campaign. Raw datasets remain under `data/raw/` and are not committed.
