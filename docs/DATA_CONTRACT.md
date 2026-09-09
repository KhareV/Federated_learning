# Canonical Signal Data Contract

This document defines the canonical record and window metadata shared by the
centralized loaders, preprocessing, inference, backend, and Svelte frontend.
It applies to PTB-XL, MIT-BIH, Noise Stress Test, BIDMC, replay data, and
future wearable inputs.

## Canonical Representation

Every source record MUST be normalized to this structure before preprocessing.
Arrays may remain file/artifact-backed; the contract stores their reference and
metadata rather than requiring database storage of large payloads.

```json
{
  "participant_id": "string (unique identifier for the patient/user)",
  "session_id": "string (unique identifier for the recording session)",
  "device_id": "string (dataset or device identifier)",
  "record_id": "string (stable source-record identifier)",
  "window_id": "string (stable record-window identifier, optional for records)",
  "timestamp_start": "string (ISO 8601 or source-relative timestamp)",
  "timestamp_end": "string (ISO 8601 or source-relative timestamp)",
  "modalities": {
    "ECG": {"artifact_ref": "string", "sampling_rate_hz": "number", "lead": "string", "units": "string"},
    "PPG_RED": {"artifact_ref": "string", "sampling_rate_hz": "number", "units": "string"},
    "PPG_IR": {"artifact_ref": "string", "sampling_rate_hz": "number", "units": "string"},
    "HR": {"artifact_ref": "string", "sampling_rate_hz": "number", "units": "bpm"},
    "SpO2": {"artifact_ref": "string", "sampling_rate_hz": "number", "units": "%"}
  },
  "availability_mask": {"ECG": "boolean", "PPG_RED": "boolean", "PPG_IR": "boolean", "HR": "boolean", "SpO2": "boolean"},
  "label": "NORMAL_MONITORED_PATTERN | POTENTIALLY_ABNORMAL | null",
  "source_dataset": "string",
  "source_version": "string",
  "quality": {"state": "GOOD | DEGRADED | UNRELIABLE", "score": "number | null", "reasons": ["string"]},
  "provenance": {"path": "string", "checksum": "string | null", "loader_version": "string"}
}
```

Required identifiers and provenance fields must not be fabricated. Unknown
timestamps, labels, or modality values are represented as `null` and explained
in provenance/quality metadata. `UNRELIABLE` is a signal-quality state, not an
abnormal physiology label.

## Hardware Specifics (AD8232 / ESP32)

Real wearable data is expected to be recorded at **12-bit ADC resolution** (values 0–4095).
The `datasets.wearable.WearableDataset` loader is responsible for converting these raw ADC values to millivolts (mV) using the formula:

`voltage_mv = (adc - 2048) / 4095 * (VREF / GAIN)`

(Assuming 3.3V VREF and a gain of ~1000 for the AD8232 module).

## Canonical ECG Pipeline

1. **Loader:** Reads dataset-specific format (WFDB, CSV, JSON) and outputs the Canonical Data Contract.
2. **Preprocessor:** Takes the canonical dict, resamples to `250 Hz`, filters (bandpass 0.5–40 Hz, notch 50/60 Hz), and normalizes.
3. **Windower:** Slices the continuous preprocessed signal into fixed 10-second (2500 sample) windows.
4. **SQI Assessor:** Assigns a documented score and `GOOD`, `DEGRADED`, or
   `UNRELIABLE` state with reasons.
5. **Model:** Operates EXCLUSIVELY on 2500-sample, 250 Hz, normalized windows.

The same record/window contract is used for PPG, SpO₂, and multimodal
synchronization. Missing modalities remain missing and are handled through the
availability mask; fabricated values are prohibited.
