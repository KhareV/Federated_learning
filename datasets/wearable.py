"""
datasets/wearable.py — AD8232/ESP32 Wearable ECG Loader
========================================================
Ingests real ECG data from the AD8232 + ESP32 wearable device.

Supported input formats:
  - CSV (default ESP32 serial export)
  - JSON (backend API format)
  - Binary (raw ADC values, configurable)

The wearable data is converted into the EXACT same canonical
format as PTB-XL/MIT-BIH. This ensures a single preprocessing
pipeline handles both public datasets and real device data.

ESP32 CSV format (default):
  timestamp_ms,ecg_raw,quality_flag
  0,2048,1
  4,2051,1
  ...

Typical AD8232 characteristics:
  - Sampling rate: 250 Hz (configurable)
  - ADC resolution: 12-bit (0–4095) → normalized to mV
  - Single lead (modified Lead I or Lead II depending on placement)
  - VCC = 3.3V, gain ~1000
"""

import logging
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Canonical Data Structures ────────────────────────────────────────────────

@dataclass
class WearableRecord:
    """Canonical representation of a wearable ECG recording session."""
    participant_id: str
    session_id: str
    record_id: str               # participant_id + "_" + session_id
    sampling_rate: int           # Hz (from config or header)
    n_samples: int
    duration_seconds: float
    channel: str                 # e.g. "AD8232_LEAD_I"
    units: str                   # "mV" (after ADC conversion)
    source_dataset: str = "wearable_ad8232"
    dataset_version: str = "1.0"
    file_path: str = ""
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    device_id: Optional[str] = None
    firmware_version: Optional[str] = None
    is_valid: bool = True
    validation_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WearableDataset:
    """
    Loader for AD8232/ESP32 wearable ECG recordings.

    This class converts raw device output into the canonical ECG format
    understood by the preprocessing pipeline and MODEL_V1 inference.

    Parameters
    ----------
    data_dir : str
        Directory containing wearable ECG files.
    sampling_rate : int
        Device sampling rate in Hz (default 250).
    adc_resolution : int
        ADC bit depth (default 12 for ESP32).
    adc_vref_mv : float
        ADC reference voltage in mV (default 3300 for 3.3V VCC).
    amplifier_gain : float
        Signal amplifier gain (default 1000 for AD8232).
    preprocessing_version : str
        Version for traceability.
    """

    SUPPORTED_FORMATS = ["csv", "json", "binary"]

    def __init__(
        self,
        data_dir: str = "data/raw/wearable",
        sampling_rate: int = 250,
        adc_resolution: int = 12,
        adc_vref_mv: float = 3300.0,
        amplifier_gain: float = 1000.0,
        preprocessing_version: str = "1.0.0",
    ):
        self.data_dir = Path(data_dir)
        self.sampling_rate = sampling_rate
        self.adc_resolution = adc_resolution
        self.adc_vref_mv = adc_vref_mv
        self.amplifier_gain = amplifier_gain
        self.preprocessing_version = preprocessing_version
        self._adc_max = (2 ** adc_resolution) - 1
        self._adc_midpoint = self._adc_max / 2

    def is_available(self) -> bool:
        """Return True if wearable data directory has files."""
        if not self.data_dir.exists():
            return False
        return any(
            self.data_dir.glob(f"*.{fmt}")
            for fmt in self.SUPPORTED_FORMATS
        )

    # ── ADC Conversion ────────────────────────────────────────────────────────

    def adc_to_mv(self, adc_values: np.ndarray) -> np.ndarray:
        """
        Convert raw 12-bit ADC values to millivolts.

        Formula:
          voltage_mv = (adc - midpoint) / max * vref_mv / gain
          ≈ (adc - 2048) / 4095 * 3300 / 1000 mV

        Parameters
        ----------
        adc_values : np.ndarray of raw ADC integers (0–4095)

        Returns
        -------
        np.ndarray of float32 values in mV
        """
        centered = adc_values.astype(np.float32) - self._adc_midpoint
        mv = centered / self._adc_max * self.adc_vref_mv / self.amplifier_gain
        return mv

    # ── Loaders by Format ─────────────────────────────────────────────────────

    def load_csv(
        self,
        file_path: str,
        participant_id: str,
        session_id: str,
        ecg_column: str = "ecg_raw",
        timestamp_column: Optional[str] = "timestamp_ms",
        quality_column: Optional[str] = "quality_flag",
    ) -> Tuple[WearableRecord, np.ndarray]:
        """
        Load a CSV file produced by the ESP32 serial port logger.

        Expected columns (configurable):
          timestamp_ms, ecg_raw, [quality_flag]

        Returns
        -------
        (WearableRecord, signal_mv) where signal_mv is float32 ndarray
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Wearable CSV not found: {file_path}")

        df = pd.read_csv(path)

        if ecg_column not in df.columns:
            raise ValueError(
                f"ECG column '{ecg_column}' not in {list(df.columns)}"
            )

        raw_values = df[ecg_column].values.astype(np.float32)
        # Detect whether values are raw ADC (int > 100) or already mV
        if raw_values.max() > 100:
            signal_mv = self.adc_to_mv(raw_values)
        else:
            signal_mv = raw_values  # Already in mV

        n_samples = len(signal_mv)
        duration = n_samples / self.sampling_rate

        # Estimate timestamps
        t_start = None
        t_end = None
        if timestamp_column and timestamp_column in df.columns:
            t_start = str(df[timestamp_column].iloc[0])
            t_end = str(df[timestamp_column].iloc[-1])

        record = WearableRecord(
            participant_id=participant_id,
            session_id=session_id,
            record_id=f"{participant_id}_{session_id}",
            sampling_rate=self.sampling_rate,
            n_samples=n_samples,
            duration_seconds=duration,
            channel="AD8232_LEAD_I",
            units="mV",
            file_path=file_path,
            timestamp_start=t_start,
            timestamp_end=t_end,
        )

        self._validate_signal_basic(signal_mv, record)
        return record, signal_mv

    def load_json(
        self,
        file_path: str,
        participant_id: str,
        session_id: str,
    ) -> Tuple[WearableRecord, np.ndarray]:
        """
        Load a JSON file from the backend API format.

        Expected JSON schema:
        {
          "participant_id": "...",
          "session_id": "...",
          "sampling_rate": 250,
          "device_id": "ESP32_001",
          "firmware_version": "1.4.2",
          "timestamp_start": "2026-09-05T10:00:00",
          "ecg_samples": [2048, 2051, ...]
        }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Wearable JSON not found: {file_path}")

        with open(path) as f:
            data = json.load(f)

        ecg_samples = np.array(data.get("ecg_samples", []), dtype=np.float32)
        if len(ecg_samples) == 0:
            raise ValueError("Empty ecg_samples in JSON")

        fs = data.get("sampling_rate", self.sampling_rate)

        # Convert ADC if needed
        if ecg_samples.max() > 100:
            signal_mv = self.adc_to_mv(ecg_samples)
        else:
            signal_mv = ecg_samples

        n_samples = len(signal_mv)
        record = WearableRecord(
            participant_id=data.get("participant_id", participant_id),
            session_id=data.get("session_id", session_id),
            record_id=f"{participant_id}_{session_id}",
            sampling_rate=fs,
            n_samples=n_samples,
            duration_seconds=n_samples / fs,
            channel="AD8232_LEAD_I",
            units="mV",
            file_path=file_path,
            timestamp_start=data.get("timestamp_start"),
            device_id=data.get("device_id"),
            firmware_version=data.get("firmware_version"),
        )
        self._validate_signal_basic(signal_mv, record)
        return record, signal_mv

    def load_synthetic_demo(
        self,
        n_seconds: float = 30.0,
        label: str = "NORMAL",
        noise_std: float = 0.05,
        seed: int = 42,
    ) -> Tuple[WearableRecord, np.ndarray]:
        """
        Generate a synthetic wearable ECG for pipeline testing.
        Used when real AD8232 hardware data is not available.
        Clearly labeled as SYNTHETIC.
        """
        from preprocessing.ecg import synthesize_ecg_segment
        rng = np.random.RandomState(seed)
        n_samples = int(n_seconds * self.sampling_rate)
        signal = synthesize_ecg_segment(
            n_samples, self.sampling_rate, noise_std=noise_std, rng=rng
        )
        record = WearableRecord(
            participant_id="SYNTHETIC_001",
            session_id="SYN_SESSION_001",
            record_id="SYNTHETIC_001_SYN_SESSION_001",
            sampling_rate=self.sampling_rate,
            n_samples=len(signal),
            duration_seconds=n_seconds,
            channel="AD8232_LEAD_I_SYNTHETIC",
            units="mV",
            source_dataset="wearable_synthetic",
            metadata={"label_hint": label, "noise_std": noise_std},
        )
        return record, signal

    # ── Batch Loading ─────────────────────────────────────────────────────────

    def discover_and_load_all(self) -> List[Tuple[WearableRecord, np.ndarray]]:
        """
        Discover all wearable files in data_dir and load them.
        Files must be named: {participant_id}_{session_id}.{ext}
        """
        if not self.is_available():
            logger.warning(
                f"No wearable data at {self.data_dir}. "
                "Using synthetic demo data."
            )
            rec, sig = self.load_synthetic_demo()
            return [(rec, sig)]

        results = []
        for ext in self.SUPPORTED_FORMATS:
            for fp in sorted(self.data_dir.glob(f"*.{ext}")):
                stem = fp.stem
                parts = stem.rsplit("_", 1)
                participant_id = parts[0] if len(parts) > 1 else stem
                session_id = parts[1] if len(parts) > 1 else "S001"

                try:
                    if ext == "csv":
                        rec, sig = self.load_csv(
                            str(fp), participant_id, session_id
                        )
                    elif ext == "json":
                        rec, sig = self.load_json(
                            str(fp), participant_id, session_id
                        )
                    else:
                        logger.warning(
                            f"Binary format not yet implemented for {fp}"
                        )
                        continue
                    results.append((rec, sig))
                    logger.info(
                        f"Loaded wearable: {fp.name} "
                        f"({rec.n_samples} samples, {rec.duration_seconds:.1f}s)"
                    )
                except Exception as exc:
                    logger.warning(f"Failed to load {fp}: {exc}")

        return results

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_signal_basic(
        self, signal: np.ndarray, record: WearableRecord
    ):
        """Basic signal quality validation."""
        issues = []
        if len(signal) == 0:
            issues.append("Empty signal")
        if not np.isfinite(signal).all():
            issues.append(f"NaN or Inf: {np.sum(~np.isfinite(signal))} samples")
        if np.std(signal) < 1e-5:
            issues.append("Flatline signal")
        if record.duration_seconds < 5.0:
            issues.append(f"Signal too short: {record.duration_seconds:.1f}s")

        if issues:
            record.is_valid = False
            record.validation_notes.extend(issues)
            for issue in issues:
                logger.warning(f"{record.record_id}: {issue}")
        else:
            record.is_valid = True

    # ── Canonical Format Conversion ───────────────────────────────────────────

    def to_canonical_dict(
        self,
        record: WearableRecord,
        signal: np.ndarray,
    ) -> dict:
        """
        Convert a wearable recording to the canonical P1 data contract format.
        This dict can be passed directly to the preprocessing pipeline.
        """
        return {
            "participant_id": record.participant_id,
            "session_id": record.session_id,
            "record_id": record.record_id,
            "signal": signal,
            "sampling_rate": record.sampling_rate,
            "channel": record.channel,
            "units": record.units,
            "source_dataset": record.source_dataset,
            "timestamp_start": record.timestamp_start,
            "timestamp_end": record.timestamp_end,
            "is_valid": record.is_valid,
            "validation_notes": record.validation_notes,
            "preprocessing_version": self.preprocessing_version,
        }
