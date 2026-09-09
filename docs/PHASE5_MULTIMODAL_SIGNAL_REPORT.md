# Phase 5 — PPG, SpO₂, BIDMC, and Fusion Interfaces

Phase 5 establishes deterministic multimodal signal processing and the late
fusion interface. It does not make a supervised multimodal performance claim
because the supplied BIDMC records do not expose labels compatible with the
canonical binary task.

## Implemented

- `BIDMCDataset` loads synchronized waveform and numeric WFDB records.
- ECG and pleth are aligned at 125 Hz; HR and SpO₂ numerics are aligned at
  their observed 1 Hz rate.
- The availability mask explicitly records missing ECG, PPG, HR, and SpO₂.
- PPG processing performs DC removal, bandpass filtering, pulse detection,
  pulse intervals, heart-rate derivation, morphology/amplitude features, and
  quality state assignment.
- SpO₂ processing validates and smooths observed values; missing or invalid
  values remain invalid and are never replaced by a constant.
- PPG SQI now computes finite-sample, SNR, pulse-stability, and amplitude
  components with `GOOD`, `DEGRADED`, and `UNRELIABLE` states.
- `MultimodalFusionModel` provides ECG/PPG encoders plus scalar features and an
  availability mask for controlled ablations.

## Dataset limitation

BIDMC provides a pleth waveform rather than separate red/IR optical channels,
and its numeric/ICU observations are not silently converted into ECG abnormality
labels. Therefore the planned ECG/PPG/HR/SpO₂ supervised ablation table is
deferred until compatible labelled multimodal data is available. BIDMC remains
valid for synchronization, quality, feature, and missing-modality validation.
