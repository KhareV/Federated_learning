# NHM Evaluation Protocol

- Split by participant/patient, never by overlapping windows.
- Use deterministic 70% train, 15% validation, 15% internal test partitions.
- Use validation only for model selection, calibration, threshold selection,
  and early stopping.
- Use the internal test once for the final development-dataset report.
- Keep MIT-BIH external and Noise Stress Test experiments separate from model
  development and tuning.
- Report accuracy, precision, recall/sensitivity, specificity, F1, AUROC,
  AUPRC, confusion matrix, class support, calibration/Brier score, and failure
  cases. Streaming reports additionally include false alarms/hour, event
  sensitivity, and detection delay.
- Every report records dataset/version, split version, preprocessing version,
  model version, seed, configuration, and code revision.

