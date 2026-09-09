# MODEL_V2 External Evaluation

`MODEL_V2` is a reproducible PTB-XL-trained ECG candidate, not a released model.

## Frozen protocol

- Development: PTB-XL train/validation only.
- Candidate selection: validation F1, with epoch 14 selected by the training run.
- Calibration and threshold: temperature scaling and a F1 threshold selected solely on the locked PTB-XL validation partition.
- Internal test and MIT-BIH: evaluated only after the candidate, preprocessing artifact, calibrator, and threshold were frozen.
- MIT-BIH was not used to tune labels, architecture, weights, calibration, or threshold.

## Results

| Dataset | AUROC | Sensitivity | Specificity | F1 |
| --- | ---: | ---: | ---: | ---: |
| PTB-XL internal test | 0.8988 | 0.8388 | 0.7708 | 0.8316 |
| MIT-BIH external | 0.7614 | 0.9766 | 0.1620 | 0.4304 |

The pre-registered external release gate requires AUROC >= 0.80, sensitivity >= 0.70, and specificity >= 0.70. `MODEL_V2` fails AUROC and specificity, so its release status is `BLOCKED_EXTERNAL_GATE`.

The retained artifacts are `experiments/centralized_ecg_v2/` and `experiments/centralized_ecg_v2_evaluation/`. The latter contains the calibration, locked threshold, metrics, noise-quality results, and release-gate decision. The active service remains explicitly unavailable for released-model inference.

This is a research prototype and never a medical diagnosis.
