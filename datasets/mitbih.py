"""
datasets/mitbih.py — MIT-BIH Arrhythmia Dataset Loader
=======================================================
Loads the MIT-BIH Arrhythmia Database (PhysioNet) for external validation.

Official source:
  https://www.physionet.org/content/mitdb/1.0.0/

Expected local path:
  data/raw/mitbih/

Download:
  python -c "import wfdb; wfdb.dl_database('mitdb', dl_dir='data/raw/mitbih')"

Annotation mapping to canonical labels:
  'N' (Normal beat) → NORMAL
  'V' (PVC), 'A' (APB), 'F', 'f', 'j', 'a', 'E', 'e', 'S',
  'R', 'L', 'B', 'T' → ABNORMAL
  '/' (Paced), '~' (Artifact), '+' (Rhythm change) → EXCLUDE

IMPORTANT: MIT-BIH is used ONLY for external validation.
MODEL_V1 is never retrained or tuned on this dataset.
"""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── MIT-BIH Annotation → Canonical ─────────────────────────────────────────

MITBIH_BEAT_TO_CANONICAL = {
    # Normal
    "N": "NORMAL",
    # Supraventricular ectopic beats
    "A": "ABNORMAL",   # Atrial premature beat
    "a": "ABNORMAL",   # Aberrated atrial premature beat
    "J": "ABNORMAL",   # Nodal (junctional) premature beat
    "S": "ABNORMAL",   # Supraventricular premature beat
    # Ventricular ectopic beats
    "V": "ABNORMAL",   # Premature ventricular contraction
    "E": "ABNORMAL",   # Ventricular escape beat
    "F": "ABNORMAL",   # Fusion of ventricular and normal beat
    # Bundle branch blocks
    "L": "ABNORMAL",   # Left bundle branch block beat
    "R": "ABNORMAL",   # Right bundle branch block beat
    "B": "ABNORMAL",   # Bundle branch block beat (unspecified)
    # Other
    "j": "ABNORMAL",   # Nodal (junctional) escape beat
    "e": "ABNORMAL",   # Atrial escape beat
    "f": "ABNORMAL",   # Fusion of paced and normal beat
    # Exclude
    "/": "EXCLUDE",    # Paced beat
    "~": "EXCLUDE",    # Signal quality change
    "+": "EXCLUDE",    # Rhythm change
    "Q": "EXCLUDE",    # Unclassifiable beat
    "?": "EXCLUDE",    # Beat not classified during learning
    "|": "EXCLUDE",    # Isolated QRS-like artifact
}

CANONICAL_TO_INT = {"NORMAL": 0, "ABNORMAL": 1}


def majority_window_label(beat_labels: np.ndarray) -> Optional[str]:
    """Return a canonical window label, excluding invalid and tied windows.

    This is deliberately independent of the signal loader so the pre-registered
    vote rule can be unit-tested.  A tie is ambiguous evidence and must not be
    converted into a normal window.
    """
    usable = [label for label in beat_labels if label in CANONICAL_TO_INT]
    if not usable:
        return None
    n_normal = sum(label == "NORMAL" for label in usable)
    n_abnormal = sum(label == "ABNORMAL" for label in usable)
    if n_normal == n_abnormal:
        return None
    return "ABNORMAL" if n_abnormal > n_normal else "NORMAL"

# Known MIT-BIH record IDs
MITBIH_RECORD_IDS = [
    "100", "101", "102", "103", "104", "105", "106", "107",
    "108", "109", "111", "112", "113", "114", "115", "116",
    "117", "118", "119", "121", "122", "123", "124", "200",
    "201", "202", "203", "205", "207", "208", "209", "210",
    "212", "213", "214", "215", "217", "219", "220", "221",
    "222", "223", "228", "230", "231", "232", "233", "234",
]


@dataclass
class MITBIHRecord:
    """Canonical representation of a single MIT-BIH record."""
    record_id: str
    participant_id: str       # Same as record_id (1 patient per record)
    sampling_rate: int        # 360 Hz native
    n_samples: int
    n_leads: int
    lead_names: List[str]
    source_dataset: str = "mitbih"
    dataset_version: str = "1.0.0"
    file_path: str = ""
    is_valid: bool = True
    validation_notes: List[str] = field(default_factory=list)


@dataclass
class MITBIHWindow:
    """A windowed ECG segment with beat-level label."""
    record_id: str
    participant_id: str
    window_index: int
    start_sample: int
    end_sample: int
    label_canonical: str
    label_int: int
    sampling_rate: int
    source_dataset: str = "mitbih"
    preprocessing_version: str = "1.0.0"


class MITBIHDataset:
    """
    MIT-BIH Arrhythmia Database loader for external validation.

    IMPORTANT: This dataset must only be used for evaluation,
    never for training or hyperparameter tuning.
    """

    LEAD_NAMES_DEFAULT = ["MLII", "V1"]

    def __init__(
        self,
        data_dir: str = "data/raw/mitbih",
        target_lead: str = "MLII",
        window_samples: int = 2500,   # 10s at 250 Hz equivalent
        preprocessing_version: str = "1.0.0",
    ):
        self.data_dir = Path(data_dir)
        self.target_lead = target_lead
        self.window_samples = window_samples
        self.preprocessing_version = preprocessing_version
        self._records: Optional[List[MITBIHRecord]] = None

    def is_available(self) -> bool:
        """Return True if MIT-BIH data directory exists with records."""
        return (self.data_dir.exists() and
                len(list(self.data_dir.glob("*.dat"))) > 0)

    def load_all_records(self) -> List[MITBIHRecord]:
        """Discover and parse all MIT-BIH records."""
        if self._records is not None:
            return self._records

        if not self.is_available():
            raise FileNotFoundError(
                f"MIT-BIH not found at {self.data_dir}. Download with:\n"
                f"  python -c \"import wfdb; wfdb.dl_database('mitdb', "
                f"dl_dir='{self.data_dir}')\""
            )

        records = []
        for record_id in MITBIH_RECORD_IDS:
            rec_path = self.data_dir / record_id
            if not (rec_path.with_suffix(".dat")).exists():
                logger.warning(f"MIT-BIH record {record_id} not found, skipping")
                continue

            try:
                import wfdb
                hdr = wfdb.rdheader(str(rec_path))
                records.append(MITBIHRecord(
                    record_id=record_id,
                    participant_id=record_id,
                    sampling_rate=hdr.fs,
                    n_samples=hdr.sig_len,
                    n_leads=hdr.n_sig,
                    lead_names=hdr.sig_name,
                    file_path=str(rec_path),
                ))
            except Exception as exc:
                logger.warning(f"Failed to load header for {record_id}: {exc}")
                records.append(MITBIHRecord(
                    record_id=record_id,
                    participant_id=record_id,
                    sampling_rate=360,
                    n_samples=0,
                    n_leads=2,
                    lead_names=self.LEAD_NAMES_DEFAULT,
                    is_valid=False,
                    validation_notes=[str(exc)],
                ))

        self._records = records
        logger.info(
            f"MIT-BIH: found {len(records)} records "
            f"({sum(r.is_valid for r in records)} valid)"
        )
        return records

    def load_signal_with_annotations(
        self, record_id: str
    ) -> Tuple[np.ndarray, int, np.ndarray, np.ndarray]:
        """
        Load ECG signal and beat annotations for a record.

        Returns
        -------
        signal : np.ndarray (n_samples,)
        fs : int
        beat_samples : np.ndarray (n_beats,) — sample index of each beat
        beat_labels : np.ndarray (n_beats,) — canonical label strings
        """
        import wfdb
        rec_path = str(self.data_dir / record_id)

        record = wfdb.rdrecord(rec_path)
        annotation = wfdb.rdann(rec_path, "atr")

        # Select lead
        lead_names = record.sig_name
        if self.target_lead in lead_names:
            lead_idx = lead_names.index(self.target_lead)
        else:
            lead_idx = 0
            logger.warning(
                f"{record_id}: Lead '{self.target_lead}' not found, "
                f"using lead index 0 ({lead_names[0] if lead_names else 'unknown'})"
            )

        signal = record.p_signal[:, lead_idx].astype(np.float32)
        fs = record.fs

        # Map annotations
        beat_samples = np.array(annotation.sample)
        raw_labels = np.array(annotation.symbol)
        canonical_labels = np.array([
            MITBIH_BEAT_TO_CANONICAL.get(sym, "EXCLUDE")
            for sym in raw_labels
        ])

        return signal, fs, beat_samples, canonical_labels

    def build_windows(
        self,
        window_seconds: float = 10.0,
        stride_seconds: float = 5.0,
        target_fs: int = 250,
    ) -> pd.DataFrame:
        """
        Build windowed segments from all valid MIT-BIH records.
        Windows are labelled based on majority beat class within them.

        Parameters
        ----------
        window_seconds : float
        stride_seconds : float
        target_fs : int — canonical sampling rate (signals will be resampled)

        Returns
        -------
        DataFrame with window metadata. Signals are NOT stored here —
        they are loaded on-demand during evaluation.
        """
        records = self.load_all_records()
        window_samples_at_target = int(window_seconds * target_fs)
        stride_samples_at_target = int(stride_seconds * target_fs)

        all_windows = []
        for rec in records:
            if not rec.is_valid:
                continue
            try:
                windows = self._windows_for_record(
                    rec, window_samples_at_target,
                    stride_samples_at_target, target_fs
                )
                all_windows.extend(windows)
            except Exception as exc:
                logger.warning(f"Failed to window {rec.record_id}: {exc}")

        df = pd.DataFrame([
            {
                "record_id": w.record_id,
                "participant_id": w.participant_id,
                "window_index": w.window_index,
                "start_sample": w.start_sample,
                "end_sample": w.end_sample,
                "label_canonical": w.label_canonical,
                "label_int": w.label_int,
                "sampling_rate": target_fs,
                "source_dataset": "mitbih",
                "preprocessing_version": self.preprocessing_version,
            }
            for w in all_windows
        ])
        logger.info(
            f"MIT-BIH windows: {len(df)} "
            f"(NORMAL={sum(df['label_canonical'] == 'NORMAL')}, "
            f"ABNORMAL={sum(df['label_canonical'] == 'ABNORMAL')})"
        )
        return df

    def _windows_for_record(
        self, rec: MITBIHRecord, window_samples: int,
        stride_samples: int, target_fs: int
    ) -> List[MITBIHWindow]:
        """Generate windows for a single record."""
        from scipy.signal import resample

        signal, fs, beat_samples, beat_labels = (
            self.load_signal_with_annotations(rec.record_id)
        )

        # Resample to canonical rate
        if fs != target_fs:
            ratio = target_fs / fs
            n_out = int(len(signal) * ratio)
            signal = resample(signal, n_out).astype(np.float32)
            beat_samples = (beat_samples * ratio).astype(int)

        n_total = len(signal)
        windows = []
        win_idx = 0

        for start in range(0, n_total - window_samples + 1, stride_samples):
            end = start + window_samples

            # Find beats in this window
            mask = (beat_samples >= start) & (beat_samples < end)
            window_beats = beat_labels[mask]

            label = majority_window_label(window_beats)
            if label is None:
                win_idx += 1
                continue
            label_int = CANONICAL_TO_INT[label]

            windows.append(MITBIHWindow(
                record_id=rec.record_id,
                participant_id=rec.participant_id,
                window_index=win_idx,
                start_sample=start,
                end_sample=end,
                label_canonical=label,
                label_int=label_int,
                sampling_rate=target_fs,
                preprocessing_version=self.preprocessing_version,
            ))
            win_idx += 1

        return windows
