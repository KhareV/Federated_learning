"""
preprocessing/windowing.py — Deterministic ECG Window Generator
===============================================================
Generates fixed-length, strided windows from ECG signals.

Critical guarantees:
  - Patient IDs are NEVER mixed across splits by this module.
  - Every window carries full provenance (participant, record, dataset, etc.)
  - Window generation is deterministic (same input → same windows).
  - Windows are created AFTER patient-level splitting, not before.

Default window: 10 seconds at 250 Hz = 2500 samples.
Default stride: 5 seconds = 1250 samples (50% overlap).
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Iterator

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PREPROCESSING_VERSION = "1.0.0"


@dataclass
class WindowRecord:
    """
    A single windowed ECG segment with full provenance.
    The signal is stored in-memory but can be written to disk via to_dict().
    """
    # Identity
    window_id: str                  # "{record_id}_w{window_index:05d}"
    participant_id: str
    record_id: str
    window_index: int
    split: str                      # "train" | "val" | "test"

    # Signal
    signal: np.ndarray              # Preprocessed (n_samples,) float32
    n_samples: int
    sampling_rate: int

    # Position in source record
    start_sample: int               # In the preprocessed signal
    end_sample: int

    # Labelling
    label_canonical: str            # "NORMAL" | "ABNORMAL"
    label_int: int                  # 0 | 1

    # Provenance
    source_dataset: str
    dataset_version: str = "unknown"
    preprocessing_version: str = PREPROCESSING_VERSION

    # SQI (filled by quality_ecg.py after windowing)
    sqi_score: float = -1.0         # -1 means not yet computed
    sqi_state: str = "NOT_COMPUTED"

    def to_dict(self, include_signal: bool = False) -> dict:
        d = {
            "window_id": self.window_id,
            "participant_id": self.participant_id,
            "record_id": self.record_id,
            "window_index": self.window_index,
            "split": self.split,
            "n_samples": self.n_samples,
            "sampling_rate": self.sampling_rate,
            "start_sample": self.start_sample,
            "end_sample": self.end_sample,
            "label_canonical": self.label_canonical,
            "label_int": self.label_int,
            "source_dataset": self.source_dataset,
            "dataset_version": self.dataset_version,
            "preprocessing_version": self.preprocessing_version,
            "sqi_score": self.sqi_score,
            "sqi_state": self.sqi_state,
        }
        if include_signal:
            d["signal"] = self.signal.tolist()
        return d


class ECGWindower:
    """
    Generates fixed-length, strided windows from preprocessed ECG signals.

    IMPORTANT: Call this AFTER patient-level splitting. This ensures that
    no windows from the same patient appear in multiple splits.

    Parameters
    ----------
    window_seconds : float
        Window length in seconds.
    stride_seconds : float
        Stride between window starts in seconds.
    sampling_rate : int
        Expected sampling rate (must match preprocessed signal).
    min_valid_fraction : float
        Reject windows with more than (1 - min_valid_fraction) bad samples.
    """

    def __init__(
        self,
        window_seconds: float = 10.0,
        stride_seconds: float = 5.0,
        sampling_rate: int = 250,
        min_valid_fraction: float = 0.8,
    ):
        self.window_seconds = window_seconds
        self.stride_seconds = stride_seconds
        self.sampling_rate = sampling_rate
        self.min_valid_fraction = min_valid_fraction

        self.window_samples = int(window_seconds * sampling_rate)
        self.stride_samples = int(stride_seconds * sampling_rate)

        logger.info(
            f"ECGWindower: window={self.window_samples} samples "
            f"({window_seconds}s), stride={self.stride_samples} samples "
            f"({stride_seconds}s) at {sampling_rate} Hz"
        )

    def window_signal(
        self,
        signal: np.ndarray,
        participant_id: str,
        record_id: str,
        label_canonical: str,
        label_int: int,
        split: str,
        source_dataset: str,
        dataset_version: str = "unknown",
    ) -> List[WindowRecord]:
        """
        Generate all valid windows from a single preprocessed signal.

        Parameters
        ----------
        signal : np.ndarray (1D float32)
        participant_id : str
        record_id : str
        label_canonical : str — "NORMAL" or "ABNORMAL"
        label_int : int — 0 or 1
        split : str — "train" | "val" | "test"
        source_dataset : str
        dataset_version : str

        Returns
        -------
        List[WindowRecord]
        """
        n = len(signal)
        windows = []

        if n < self.window_samples:
            logger.debug(
                f"Record {record_id} too short ({n} < {self.window_samples}), "
                "no windows generated"
            )
            return windows

        for idx, start in enumerate(
            range(0, n - self.window_samples + 1, self.stride_samples)
        ):
            end = start + self.window_samples
            window_sig = signal[start:end].copy()

            # Reject windows with too many bad samples
            valid_fraction = np.mean(np.isfinite(window_sig))
            if valid_fraction < self.min_valid_fraction:
                logger.debug(
                    f"Window {idx} of {record_id} rejected "
                    f"(valid_fraction={valid_fraction:.2f})"
                )
                continue

            window_id = f"{record_id}_w{idx:05d}"
            windows.append(WindowRecord(
                window_id=window_id,
                participant_id=participant_id,
                record_id=record_id,
                window_index=idx,
                split=split,
                signal=window_sig.astype(np.float32),
                n_samples=self.window_samples,
                sampling_rate=self.sampling_rate,
                start_sample=start,
                end_sample=end,
                label_canonical=label_canonical,
                label_int=label_int,
                source_dataset=source_dataset,
                dataset_version=dataset_version,
            ))

        return windows

    def window_manifest_records(
        self,
        manifest_df: pd.DataFrame,
        signal_loader_fn,
        preprocessor,
        split: Optional[str] = None,
    ) -> Iterator[WindowRecord]:
        """
        Yield windowed records for all rows in a manifest DataFrame.
        Signals are loaded and preprocessed on-the-fly.

        Parameters
        ----------
        manifest_df : pd.DataFrame (from PTBXLDataset.build_manifest())
        signal_loader_fn : callable(record_id) → (signal, fs)
            Function that loads raw signal for a given record.
        preprocessor : ECGPreprocessor
        split : str, optional — filter to specific split

        Yields
        ------
        WindowRecord (one at a time, to avoid loading all into RAM)
        """
        df = manifest_df
        if split is not None:
            df = df[df["split"] == split]

        for _, row in df.iterrows():
            record_id = str(row["record_id"])
            participant_id = str(row["participant_id"])
            label_canonical = str(row["label_canonical"])
            label_int = int(row["label_int"])
            row_split = str(row.get("split", "unknown"))
            source_dataset = str(row.get("source_dataset", "unknown"))
            dataset_version = str(row.get("dataset_version", "unknown"))

            try:
                raw_signal, fs = signal_loader_fn(record_id)
                prep = preprocessor.process(
                    raw_signal, fs,
                    record_id=record_id,
                    source_dataset=source_dataset,
                )

                if not prep.is_valid:
                    logger.warning(
                        f"Skip {record_id}: {prep.validation_notes}"
                    )
                    continue

                windows = self.window_signal(
                    signal=prep.signal,
                    participant_id=participant_id,
                    record_id=record_id,
                    label_canonical=label_canonical,
                    label_int=label_int,
                    split=row_split,
                    source_dataset=source_dataset,
                    dataset_version=dataset_version,
                )

                for w in windows:
                    yield w

            except Exception as exc:
                logger.error(f"Failed to process record {record_id}: {exc}")
                continue

    def build_windows_to_df(
        self,
        manifest_df: pd.DataFrame,
        signal_loader_fn,
        preprocessor,
        split: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Convenience method: collect all windows into a DataFrame of metadata
        (without storing signals — signals can be loaded on demand).

        Returns
        -------
        pd.DataFrame with window metadata rows (no signal column).
        """
        rows = []
        for window in self.window_manifest_records(
            manifest_df, signal_loader_fn, preprocessor, split
        ):
            rows.append(window.to_dict(include_signal=False))

        if not rows:
            logger.warning("No windows generated from manifest")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        logger.info(
            f"Generated {len(df)} windows "
            f"(NORMAL={sum(df['label_canonical']=='NORMAL')}, "
            f"ABNORMAL={sum(df['label_canonical']=='ABNORMAL')})"
        )
        return df

    @property
    def config_dict(self) -> dict:
        """Serializable config for experiment tracking."""
        return {
            "window_seconds": self.window_seconds,
            "stride_seconds": self.stride_seconds,
            "sampling_rate": self.sampling_rate,
            "window_samples": self.window_samples,
            "stride_samples": self.stride_samples,
            "min_valid_fraction": self.min_valid_fraction,
        }
