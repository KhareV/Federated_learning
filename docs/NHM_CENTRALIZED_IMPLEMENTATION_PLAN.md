# NHM Centralized Software-First Implementation Plan

This file is the implementation source of truth for the centralized software
milestone. The attached project documents define the scientific intent,
ownership, handoffs, and future federated/hardware work. The user's explicit
constraints define the current scope: complete centralized ML and software,
remove authentication, use SvelteKit `frontend/`, and defer hardware,
federated learning, secure aggregation, DP, and edge optimization.

## Execution order

1. Contracts, dataset registry, and authentication removal
2. Dataset validation and immutable manifests
3. Canonical ECG preprocessing and SQI
4. Real PTB-XL baselines and ECG `MODEL_V1`
5. Calibration, internal test, MIT-BIH external validation, and noise testing
6. PPG, SpO₂, BIDMC synchronization, and centralized multimodal ML
7. Streaming inference and temporal event logic
8. Hosted model service and backend persistence/API
9. SvelteKit frontend reconciliation
10. Software-only end-to-end validation
11. `CENTRALIZED_SYSTEM_V1` lock

## Scientific decisions

- Primary output: `NORMAL_MONITORED_PATTERN`, `POTENTIALLY_ABNORMAL`, or
  `UNRELIABLE_SIGNAL`; this is not a diagnosis.
- PTB-XL is the centralized ECG development dataset.
- MIT-BIH Arrhythmia is external validation only.
- MIT-BIH Noise Stress Test is controlled robustness testing only.
- BIDMC is for synchronized multimodal signal, feature, and quality work.
  Supervised fusion claims require compatible labels; ICU/status metadata is
  not silently treated as an ECG abnormality label.
- Canonical ECG input is 250 Hz, Lead II approximation, 10-second windows,
  5-second stride, with patient-level 70/15/15 splits.
- Threshold selection uses validation data, maximizing F1 and breaking ties
  toward higher sensitivity; the threshold is locked before test evaluation.

## Phase gates and status

| Phase | Gate | Status | Verification evidence |
|---|---|---|---|
| 0 | Contracts frozen; authentication removed; synthetic artifacts labelled | **Complete** | Contract docs present; auth route/dependency scan passed; 82 tests passed |
| 1 | Supplied datasets registered, structurally validated, and manifestable | **Complete** | `scripts/validate_datasets.py` passed for PTB-XL, MIT-BIH, Noise Stress, BIDMC; inventory written |
| 2 | Train-only normalization, canonical ECG path, and SQI gate verified | **Complete** | `tests/test_phase2_ecg_contract.py`; full suite: 86 passed |
| 3 | Real PTB-XL baselines and reproducible `MODEL_V1` | **Complete** | `docs/PHASE3_REAL_PTBXL_BASELINES.md`; full real-data run and checkpoint artifacts |
| 4 | Calibration, locked threshold, external and noise reports | **Complete** | `docs/PHASE4_CALIBRATION_EXTERNAL_NOISE_REPORT.md`; calibrated PTB-XL, locked MIT-BIH external evaluation, all six SNR levels |
| 5 | PPG/SpO₂ pipeline, BIDMC synchronization, fusion/ablations | **Complete** | `docs/PHASE5_MULTIMODAL_SIGNAL_REPORT.md`; BIDMC synchronization and missing-modality tests; supervised ablations deferred because compatible labels are unavailable |
| 6 | Deterministic streaming state/event evaluation | **Complete** | `docs/PHASE6_STREAMING_REPORT.md`; deterministic replay, event coalescing, and unreliable-state tests |
| 7 | Hosted model, database, and backend API contracts | **Complete** | `docs/PHASE7_HOSTED_BACKEND_REPORT.md`; session/inference persistence integration tests; 98 total tests passed |
| 8 | SvelteKit routes use backend data; no fabricated metrics | **Complete** | `docs/PHASE8_FRONTEND_RECONCILIATION_REPORT.md`; Svelte type-check: 0 errors; production build passed |
| 9 | Software-only replay reaches the frontend end to end | **Complete** | `docs/PHASE9_SOFTWARE_E2E_REPORT.md`; replay/API persistence, WebSocket handshake, full Python suite, frontend check/build |
| 10 | `CENTRALIZED_SYSTEM_V1` artifact and evidence bundle | **Complete** | `docs/CENTRALIZED_SYSTEM_V1.md`; checksummed lock manifest at `artifacts/CENTRALIZED_SYSTEM_V1/LOCK_MANIFEST.json`; all phase gates verified |

## Phase 0 deliverables

The following documents are the contract baseline for implementation:

- `PROJECT_ML_SPEC.md` — scope, claims, datasets, and scientific constraints.
- `DATA_CONTRACT.md` — canonical record/window and multimodal availability schema.
- `LABEL_SCHEMA.md` — canonical labels and dataset mappings.
- `EVALUATION_PROTOCOL.md` — split, metrics, calibration, and external evaluation.
- `EXPERIMENT_MATRIX.md` — pre-registered baseline and ablation sequence.
- `MODEL_CONTRACT.md` — model artifact and prediction requirements.
- `INFERENCE_CONTRACT.md` — serving response and unreliable-signal behavior.
- `REPRODUCIBILITY.md` — commands, seeds, versions, and artifact requirements.

Authentication was removed from the active backend and SvelteKit application.
The legacy frontend is excluded from the repository's active application scope;
identity is represented only by explicit subject/session/device identifiers.

## Verification policy

Every phase must add or update tests and must pass the prior phase gates. A
phase is not complete because code exists: its output must be reproducible,
versioned, and exercised by automated checks. Dataset-derived research results
must never be replaced by synthetic demo results.

## Deferred work

ESP32/AD8232/MAX30102 hardware, wearable-domain validation, FedAvg, FedProx,
non-IID federation, QAPFL claims, secure aggregation, differential privacy,
quantization, and energy benchmarks begin only after the centralized system is
locked.
