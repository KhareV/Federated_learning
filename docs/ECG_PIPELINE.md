# P1 ECG Preprocessing Pipeline

This document outlines the standard canonical preprocessing steps applied to all ECG signals in the P1 Work Package. 

## Philosophy

1. **One Pipeline to Rule Them All:** Public datasets (PTB-XL, MIT-BIH) and real wearable device data MUST pass through the exact same preprocessing pipeline.
2. **Determinism:** The pipeline must yield the exact same float32 array for the same input and configuration.
3. **No Leakage:** Normalization statistics (mean, std) must be derived **only from the training split** and applied statically to validation/test sets and inference.

## The Pipeline Steps

Implemented in `preprocessing.ecg.ECGPreprocessor`:

1. **Input Validation:** Handle `NaN`/`Inf` (replaced with 0.0), flag empty signals.
2. **Resampling:** Convert input sampling rate to the canonical `250 Hz` using a robust polyphase filter (`scipy.signal.resample_poly`).
3. **Bandpass Filtering (0.5 - 40 Hz):**
   - Uses a 4th-order Butterworth filter (applied via `sosfiltfilt` for zero-phase).
   - Removes baseline wander (< 0.5 Hz) and high-frequency noise/muscle artifact (> 40 Hz).
4. **Powerline Interference Notch (50/60 Hz):**
   - Uses an IIR notch filter (`filtfilt` for zero-phase, Q=30).
   - 50 Hz default (configurable in `ecg_preprocessing.yaml`).
5. **Z-Score Normalization:**
   - `signal = (signal - mean) / std`
   - Training stats must be passed during inference.
6. **Clipping:**
   - Limit extreme outliers: values clamped to `±5σ` (configurable).

## Windowing

Implemented in `preprocessing.windowing.ECGWindower`:

After preprocessing, signals are sliced into fixed-length windows.
- **Window Length:** 10 seconds (2500 samples at 250 Hz)
- **Stride:** 5 seconds (50% overlap, 1250 samples)

*Critical Constraint:* Windowing must occur **after** patient-level dataset splitting. A window from Patient A must never be in the training set if another window from Patient A is in the test set.

## Signal Quality Index (SQI)

Implemented in `preprocessing.quality_ecg.ECGQualityAssessor`:

Each 10-second window is assessed and scored from 0 to 100 based on:
1. **SNR (30%):** Estimated signal-to-noise ratio.
2. **Baseline Stability (25%):** Energy in the low-frequency band.
3. **Amplitude (20%):** Penalizes unusually small (poor contact) or large (saturation) peak-to-peak ranges.
4. **Clipping (15%):** Penalizes signals that rail against ADC max/min limits.
5. **Flatline (10%):** Hard 0 if standard deviation is below a minimum threshold.

**States:**
- **EXCELLENT:** SQI ≥ 80
- **GOOD:** SQI ≥ 60
- **FAIR:** SQI ≥ 40
- **POOR:** SQI < 40 (often rejected depending on `reject_below` config).
