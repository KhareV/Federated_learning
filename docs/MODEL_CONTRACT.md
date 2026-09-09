# NHM Model Contract

## ECG `MODEL_V1`

- Input: float32 tensor shaped `(batch, 1, 2500)`.
- Sampling rate: 250 Hz.
- Lead: canonical single-channel Lead II approximation.
- Labels: `NORMAL=0`, `ABNORMAL=1`.
- Output: two-class logits/probabilities plus model and preprocessing versions.
- Checkpoint metadata: dataset version, split version, seed, configuration,
  calibration artifact, threshold, and code revision.

## Multimodal model

Inputs are named rather than positionally implicit: ECG, PPG red/IR, HR, SpO₂,
quality features, and modality availability mask. Missing or unusable inputs
must be represented explicitly and never replaced with fabricated physiology.

