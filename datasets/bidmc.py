"""BIDMC synchronized ECG/PPG/numeric loader.

BIDMC provides WFDB waveform records at 125 Hz and paired numeric records at
1 Hz. It does not provide red/IR optical channels; SpO2 is therefore loaded as
an observed numeric modality and is never fabricated from the pleth channel.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


@dataclass
class BIDMCSession:
    participant_id: str
    session_id: str
    record_id: str
    sampling_rate: float
    signals: Dict[str, np.ndarray]
    numeric_sampling_rate: float
    numerics: Dict[str, np.ndarray]
    source_dataset: str = "bidmc"
    dataset_version: str = "1.0.0"


class BIDMCDataset:
    SIGNAL_ALIASES = {
        "II": "ECG", "ECG": "ECG", "PLETH": "PPG", "PPG": "PPG",
        "V": "ECG_V", "AVR": "ECG_AVR", "RESP": "RESP",
    }
    NUMERIC_ALIASES = {"HR": "HR", "PULSE": "PULSE", "SPO2": "SpO2", "RESP": "RESP"}

    def __init__(self, data_dir="data/raw/bidmc", dataset_version="1.0.0"):
        self.data_dir = Path(data_dir)
        self.dataset_version = dataset_version

    def record_ids(self) -> List[str]:
        return sorted(p.stem for p in self.data_dir.glob("bidmc[0-9][0-9].hea"))

    def _read(self, record_id):
        import wfdb
        return wfdb.rdrecord(str(self.data_dir / record_id))

    @staticmethod
    def _clean_name(name):
        return name.strip().rstrip(",").upper()

    def load_session(self, record_id: str) -> BIDMCSession:
        import wfdb
        waveform = self._read(record_id)
        numeric_id = record_id + "n"
        numeric = self._read(numeric_id) if (self.data_dir / (numeric_id + ".hea")).exists() else None
        signals = {}
        for index, name in enumerate(waveform.sig_name):
            canonical = self.SIGNAL_ALIASES.get(self._clean_name(name))
            if canonical and canonical not in signals:
                signals[canonical] = waveform.p_signal[:, index].astype(np.float32)
        numerics = {}
        if numeric is not None:
            for index, name in enumerate(numeric.sig_name):
                canonical = self.NUMERIC_ALIASES.get(self._clean_name(name))
                if canonical and canonical not in numerics:
                    numerics[canonical] = numeric.p_signal[:, index].astype(np.float32)
        return BIDMCSession(
            participant_id=record_id, session_id=record_id, record_id=record_id,
            sampling_rate=float(waveform.fs), signals=signals,
            numeric_sampling_rate=float(numeric.fs) if numeric is not None else 1.0,
            numerics=numerics, dataset_version=self.dataset_version,
        )

    def synchronized_windows(self, record_id: str, window_seconds=10, stride_seconds=5):
        """Yield canonical synchronized windows; labels remain unavailable."""
        session = self.load_session(record_id)
        if "ECG" not in session.signals and "PPG" not in session.signals:
            return
        fs = int(session.sampling_rate)
        window = int(window_seconds * fs)
        stride = int(stride_seconds * fs)
        length = max((len(value) for value in session.signals.values()), default=0)
        for start in range(0, max(0, length - window + 1), stride):
            end = start + window
            numeric_start = int(start / fs * session.numeric_sampling_rate)
            numeric_end = int(end / fs * session.numeric_sampling_rate)
            yield {
                "window_id": f"{record_id}_w{start // stride:05d}",
                "participant_id": session.participant_id,
                "record_id": record_id,
                "start_seconds": start / fs,
                "end_seconds": end / fs,
                "ECG": session.signals.get("ECG", np.array([], dtype=np.float32))[start:end],
                "PPG": session.signals.get("PPG", np.array([], dtype=np.float32))[start:end],
                "HR": session.numerics.get("HR", np.array([], dtype=np.float32))[numeric_start:numeric_end],
                "SpO2": session.numerics.get("SpO2", np.array([], dtype=np.float32))[numeric_start:numeric_end],
                "availability_mask": {
                    "ECG": "ECG" in session.signals, "PPG": "PPG" in session.signals,
                    "HR": "HR" in session.numerics, "SpO2": "SpO2" in session.numerics,
                },
                "label": None, "source_dataset": "bidmc", "dataset_version": session.dataset_version,
            }
