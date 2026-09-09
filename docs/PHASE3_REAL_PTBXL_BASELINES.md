# Phase 3 — Real PTB-XL Baseline Report

This report records the first centralized real-data run. It is a research
prototype result and is not a clinical performance claim.

## Locked run

- Dataset: PTB-XL 1.0.1, supplied locally
- Valid records: 21,430
- Windows: train 15,039; validation 3,181; internal test 3,210
- Split: deterministic participant-level 70/15/15, seed 42
- Input: lead II, 250 Hz, 10-second windows, 5-second stride
- Preprocessing: frozen statistics fitted on training records only
- Quality: unusable windows excluded using the canonical SQI gate
- CNN: compact 1D CNN, 188,002 parameters, five epochs on CPU

## Results

| Model | Validation F1 | Validation AUROC | Test F1 | Test AUROC | Test sensitivity | Test specificity |
|---|---:|---:|---:|---:|---:|---:|
| Majority baseline | 0.7304 | 0.5000 | 0.7198 | 0.5000 | 1.0000 | 0.0000 |
| Logistic Regression | 0.7892 | 0.8507 | 0.7938 | 0.8566 | 0.7623 | 0.7964 |
| Random Forest | 0.8064 | 0.8607 | 0.8015 | 0.8666 | 0.7839 | 0.7786 |
| Compact ECG CNN | **0.8359** | **0.9022** | **0.8369** | **0.9029** | 0.8133 | 0.8327 |

The CNN checkpoint was selected using validation F1. The internal test set
was not used for model selection or threshold tuning. These results should be
reproduced from the runner before being used in later reports.

## Reproduction

```bash
python training/run_ptbxl_baselines.py --models all
```

Artifacts from the recorded run are under `experiments/ptbxl_phase3/`:
preprocessing statistics, split/data summary, classical models, CNN
checkpoints, training log, and machine-readable metrics.
