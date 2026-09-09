"""Deterministic windowed streaming inference and event state machine."""

from collections import deque
from dataclasses import asdict, dataclass
from typing import Callable, List, Optional

import numpy as np


STREAM_STATES = ("NORMAL", "POTENTIALLY_ABNORMAL", "UNRELIABLE")


def locked_model_predictor(model_path, preprocessing_path, calibration_path=None):
    """Build a streaming predictor from the frozen centralized artifacts."""
    import torch
    from calibration.temperature import TemperatureScaler
    from models.ecg_cnn import ECGCNN1D
    from preprocessing.ecg import ECGPreprocessor
    from preprocessing.quality_ecg import ECGQualityAssessor

    model, checkpoint = ECGCNN1D.load_checkpoint(str(model_path), device="cpu")
    preprocessor = ECGPreprocessor.load_normalization_stats(preprocessing_path)
    assessor = ECGQualityAssessor(fs=preprocessor.target_fs)
    calibrator = TemperatureScaler.load(calibration_path) if calibration_path else None

    def predict_window(raw_window, source_fs):
        processed = preprocessor.transform(raw_window, source_fs, "stream", "replay")
        quality = assessor.assess(processed.signal)
        if not quality.is_usable:
            return WindowInference(0.5, "UNRELIABLE", 0.0)
        signal = processed.signal[:2500]
        with torch.no_grad():
            logits = model(torch.from_numpy(signal).float().view(1, 1, -1))
            probability = float(torch.softmax(logits, dim=1)[0, 1].item())
        if calibrator:
            probability = float(calibrator.transform([probability])[0])
        return WindowInference(probability, quality.canonical_state, max(probability, 1 - probability))

    return predict_window, checkpoint["config"]["model_version"]


@dataclass(frozen=True)
class WindowInference:
    probability_abnormal: float
    signal_quality: str = "GOOD"
    confidence: float = 0.0


@dataclass(frozen=True)
class StreamEvent:
    state: str
    start_seconds: float
    end_seconds: Optional[float]
    peak_probability: float
    n_windows: int

    def to_dict(self):
        return asdict(self)


class StreamingInferenceEngine:
    """Buffer samples, infer fixed windows, and coalesce temporal events.

    The predictor is called with one raw window and its source sampling rate.
    It must return WindowInference. All timestamps are source-relative sample
    times, making replay deterministic and independent of wall-clock time.
    """

    def __init__(self, predictor: Callable, source_fs: int, window_seconds=10.0,
                 stride_seconds=5.0, threshold=0.5, smoothing_windows=3):
        if source_fs <= 0 or window_seconds <= 0 or stride_seconds <= 0:
            raise ValueError("sampling rate and window/stride must be positive")
        self.predictor = predictor
        self.source_fs = int(source_fs)
        self.window_samples = int(window_seconds * source_fs)
        self.stride_samples = int(stride_seconds * source_fs)
        self.threshold = float(threshold)
        self.smoothing_windows = max(1, int(smoothing_windows))
        self._buffer = np.empty(0, dtype=np.float32)
        self._buffer_start = 0
        self._next_start = 0
        self._probabilities = deque(maxlen=self.smoothing_windows)
        self._current_state = None
        self._current_event_start = None
        self._current_peak = 0.0
        self._current_windows = 0
        self._events: List[StreamEvent] = []
        self._flaps = 0
        self._processed_windows = 0

    @property
    def events(self):
        return list(self._events)

    @property
    def state_flap_count(self):
        return self._flaps

    def _state_for(self, result: WindowInference) -> tuple[str, float]:
        if result.signal_quality == "UNRELIABLE":
            self._probabilities.clear()
            return "UNRELIABLE", float(result.probability_abnormal)
        probability = float(np.clip(result.probability_abnormal, 0.0, 1.0))
        self._probabilities.append(probability)
        smoothed = float(np.mean(self._probabilities))
        return ("POTENTIALLY_ABNORMAL" if smoothed >= self.threshold else "NORMAL"), smoothed

    def _close_event(self, end_seconds):
        if self._current_event_start is not None:
            self._events.append(StreamEvent(
                self._current_state, self._current_event_start, end_seconds,
                self._current_peak, self._current_windows,
            ))
        self._current_event_start = None
        self._current_peak = 0.0
        self._current_windows = 0

    def _transition(self, state, start_seconds, probability):
        if state == self._current_state:
            if state == "POTENTIALLY_ABNORMAL":
                self._current_peak = max(self._current_peak, probability)
            self._current_windows += 1
            return
        if self._current_state is not None:
            self._close_event(start_seconds)
            self._flaps += 1
        self._current_state = state
        if state != "NORMAL":
            self._current_event_start = start_seconds
            self._current_windows = 1
        if state == "POTENTIALLY_ABNORMAL":
            self._current_peak = probability
        else:
            self._current_peak = 0.0

    def push(self, samples) -> List[dict]:
        """Push a chunk and return inference records for newly completed windows."""
        chunk = np.asarray(samples, dtype=np.float32).flatten()
        if len(chunk) == 0:
            return []
        self._buffer = np.concatenate((self._buffer, chunk))
        outputs = []
        while self._next_start + self.window_samples <= self._buffer_start + len(self._buffer):
            offset = self._next_start - self._buffer_start
            window = self._buffer[offset:offset + self.window_samples].copy()
            result = self.predictor(window, self.source_fs)
            if not isinstance(result, WindowInference):
                raise TypeError("predictor must return WindowInference")
            state, smoothed = self._state_for(result)
            self._transition(state, self._next_start / self.source_fs, smoothed)
            outputs.append({
                "window_start_seconds": self._next_start / self.source_fs,
                "window_end_seconds": (self._next_start + self.window_samples) / self.source_fs,
                "state": state, "probability_abnormal": result.probability_abnormal,
                "smoothed_probability": smoothed, "signal_quality": result.signal_quality,
            })
            self._processed_windows += 1
            self._next_start += self.stride_samples
            drop_until = self._next_start
            drop = drop_until - self._buffer_start
            if drop > 0:
                self._buffer = self._buffer[drop:]
                self._buffer_start = drop_until
        return outputs

    def finalize(self):
        """Close an active abnormal event at the end of the observed stream."""
        end_seconds = (self._buffer_start + len(self._buffer)) / self.source_fs
        self._close_event(end_seconds)
        self._current_state = None
        return self.events

    def summary(self):
        duration_hours = (self._buffer_start + len(self._buffer)) / self.source_fs / 3600.0
        abnormal = [event for event in self._events if event.state == "POTENTIALLY_ABNORMAL"]
        return {
            "processed_windows": self._processed_windows,
            "events": len(abnormal),
            "false_alarms_per_hour": len(abnormal) / max(duration_hours, 1 / 3600),
            "unreliable_periods": sum(event.state == "UNRELIABLE" for event in self._events),
            "state_flap_count": self._flaps,
        }
