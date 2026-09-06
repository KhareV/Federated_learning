# P1 ECG Data Contract

This document defines the canonical format for all ECG data flowing through the P1 pipeline, ensuring interoperability between public datasets (PTB-XL, MIT-BIH) and real wearable hardware (AD8232/ESP32).

## Canonical Representation

Regardless of the source, all data entering the preprocessing pipeline MUST be formatted into the following dictionary structure:

```json
{
  "participant_id": "string (unique identifier for the patient/user)",
  "session_id": "string (unique identifier for the recording session)",
  "record_id": "string (participant_id + '_' + session_id)",
  "signal": "numpy.ndarray (1D array, raw float values)",
  "sampling_rate": "int (original sampling rate in Hz, e.g., 250, 360, 500)",
  "channel": "string (e.g., 'MLII', 'AD8232_LEAD_I')",
  "units": "string (e.g., 'mV')",
  "source_dataset": "string ('ptbxl' | 'mitbih' | 'wearable_ad8232')",
  "timestamp_start": "string (ISO 8601, optional)",
  "timestamp_end": "string (ISO 8601, optional)",
  "is_valid": "boolean",
  "validation_notes": ["list of strings with any known issues"],
  "preprocessing_version": "string (e.g., '1.0.0')"
}
```

## Hardware Specifics (AD8232 / ESP32)

Real wearable data is expected to be recorded at **12-bit ADC resolution** (values 0–4095).
The `datasets.wearable.WearableDataset` loader is responsible for converting these raw ADC values to millivolts (mV) using the formula:

`voltage_mv = (adc - 2048) / 4095 * (VREF / GAIN)`

(Assuming 3.3V VREF and a gain of ~1000 for the AD8232 module).

## The Pipeline

1. **Loader:** Reads dataset-specific format (WFDB, CSV, JSON) and outputs the Canonical Data Contract.
2. **Preprocessor:** Takes the canonical dict, resamples to `250 Hz`, filters (bandpass 0.5–40 Hz, notch 50/60 Hz), and normalizes.
3. **Windower:** Slices the continuous preprocessed signal into fixed 10-second (2500 sample) windows.
4. **SQI Assessor:** Assigns a 0–100 score to each window.
5. **Model:** Operates EXCLUSIVELY on 2500-sample, 250 Hz, normalized windows.

This contract prevents the model from overfitting to dataset-specific artifacts (like varying sampling rates or baseline voltages).
