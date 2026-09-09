# Phase 4 — Calibration, External Validation, and Noise

This is a locked research evaluation of the PTB-XL-trained `MODEL_V1`. It is
not a diagnosis or clinical validation.

## Locked calibration

- Temperature scaling fit on PTB-XL validation predictions only.
- Learned temperature: `1.1677122332`.
- Abnormal threshold: `0.4046099574`.
- Threshold rule: maximum validation F1, then higher sensitivity, then higher
  threshold for deterministic tie resolution.
- The PTB-XL internal test set and MIT-BIH were not used for calibration or
  threshold selection.

Calibrated PTB-XL internal test performance:

| F1 | AUROC | AUPRC | Sensitivity | Specificity | Brier score |
|---:|---:|---:|---:|---:|---:|
| 0.8394 | 0.9029 | 0.9340 | 0.8687 | 0.7416 | 0.124832 |

## MIT-BIH external validation

The locked model was evaluated on 16,559 labelled windows from all 48 supplied
MIT-BIH records, without retraining or tuning:

| F1 | AUROC | AUPRC | Sensitivity | Specificity |
|---:|---:|---:|---:|---:|
| 0.4078 | 0.7387 | 0.4587 | 1.0000 | 0.0696 |

This distribution shift produces a high false-positive rate. It is retained
as an external validation result, not hidden or used to revise `MODEL_V1`.

## Noise Stress Test

All configured SNR levels were evaluated: `24, 18, 12, 6, 0, -6 dB`.
The supplied Noise Stress Test files do not contain labels compatible with the
canonical binary task, so F1, sensitivity, specificity, AUROC, and AUPRC are
intentionally not reported. The machine-readable report instead records
window count, SQI, unreliable fraction, and predicted-abnormal fraction.

The complete machine-readable output is in
`experiments/ptbxl_phase4/phase4_report.json`; calibration and threshold are
stored separately beside it.
