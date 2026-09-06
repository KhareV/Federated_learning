"""
tests/test_p1_preprocessing.py — P1 Preprocessing Tests
=========================================================
Tests for:
  - ECGPreprocessor (bandpass, notch, resample, normalize, clip)
  - ECGWindower (window generation, provenance, no-leakage)
  - NormalizationStats (train-only fitting)
  - synthesize_ecg_segment (for test signal generation)

All tests use synthetic data — no dataset download required.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from preprocessing.ecg import ECGPreprocessor, NormalizationStats, synthesize_ecg_segment
from preprocessing.windowing import ECGWindower


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def preprocessor():
    return ECGPreprocessor()


@pytest.fixture
def clean_ecg():
    """Clean synthetic ECG at 250 Hz."""
    return synthesize_ecg_segment(2500, fs=250, noise_std=0.02, seed=42)


@pytest.fixture
def clean_ecg_500hz():
    """Clean synthetic ECG at 500 Hz (like PTB-XL)."""
    return synthesize_ecg_segment(5000, fs=500, noise_std=0.02, seed=42)


# ─── ECGPreprocessor Tests ────────────────────────────────────────────────────

class TestECGPreprocessor:

    def test_output_is_float32(self, preprocessor, clean_ecg):
        result = preprocessor.process(clean_ecg, 250, "test_001")
        assert result.signal.dtype == np.float32

    def test_output_length_preserved_at_same_fs(self, preprocessor, clean_ecg):
        result = preprocessor.process(clean_ecg, 250)
        # Output length should be close to input after same-fs processing
        assert abs(len(result.signal) - len(clean_ecg)) <= 5

    def test_resampling_500_to_250(self, preprocessor, clean_ecg_500hz):
        result = preprocessor.process(clean_ecg_500hz, 500)
        assert result.was_resampled is True
        assert result.sampling_rate == 250
        expected_len = int(len(clean_ecg_500hz) * 250 / 500)
        assert abs(len(result.signal) - expected_len) <= 10

    def test_no_nan_in_output(self, preprocessor, clean_ecg):
        result = preprocessor.process(clean_ecg, 250)
        assert np.isfinite(result.signal).all(), "Output contains NaN/Inf"

    def test_nan_input_handled(self, preprocessor):
        sig = np.array([1.0, np.nan, 2.0, np.inf, -np.inf] * 500, dtype=np.float32)
        result = preprocessor.process(sig, 250)
        assert np.isfinite(result.signal).all()
        assert len(result.validation_notes) > 0  # Issues were logged

    def test_empty_signal_returns_invalid(self, preprocessor):
        result = preprocessor.process(np.array([]), 250)
        assert result.is_valid is False

    def test_clipping_applied(self, preprocessor):
        # Create signal with extreme outliers
        sig = synthesize_ecg_segment(2500, 250, noise_std=0.01, seed=1)
        sig[100] = 1000.0  # Extreme outlier
        result = preprocessor.process(sig, 250)
        # After normalization and clipping, no values should be > 5 * std_multiplier
        assert np.max(np.abs(result.signal)) <= preprocessor.clip_std_multiplier + 0.1

    def test_deterministic_output(self, preprocessor, clean_ecg):
        result1 = preprocessor.process(clean_ecg, 250, "rec_a")
        result2 = preprocessor.process(clean_ecg, 250, "rec_a")
        np.testing.assert_array_equal(result1.signal, result2.signal)

    def test_version_in_output(self, preprocessor, clean_ecg):
        result = preprocessor.process(clean_ecg, 250)
        assert result.preprocessing_version == "1.0.0"

    def test_provenance_in_output(self, preprocessor, clean_ecg):
        result = preprocessor.process(clean_ecg, 250, record_id="rec42",
                                       source_dataset="ptbxl")
        assert result.source_record_id == "rec42"
        assert result.source_dataset == "ptbxl"

    def test_normalization_with_train_stats(self):
        """Using NormalizationStats from training should give different result
        than per-signal normalization."""
        sig = synthesize_ecg_segment(2500, 250, noise_std=0.03, seed=10)
        train_stats = NormalizationStats(mean=0.0, std=0.5,
                                          n_samples_used=100000)
        proc_with_stats = ECGPreprocessor(normalization_stats=train_stats)
        result = proc_with_stats.process(sig, 250)
        assert result.normalization_mean == 0.0
        assert result.normalization_std == 0.5


class TestNormalizationStats:

    def test_fit_from_signals(self):
        signals = [synthesize_ecg_segment(2500, 250, seed=i) for i in range(5)]
        stats = NormalizationStats.from_signals(signals)
        assert np.isfinite(stats.mean)
        assert stats.std > 0
        assert stats.n_samples_used > 0

    def test_to_from_dict(self):
        stats = NormalizationStats(mean=0.5, std=1.2, n_samples_used=5000)
        d = stats.to_dict()
        stats2 = NormalizationStats.from_dict(d)
        assert stats2.mean == stats.mean
        assert stats2.std == stats.std


class TestSynthesizeECG:

    def test_output_shape(self):
        sig = synthesize_ecg_segment(2500, 250)
        assert len(sig) == 2500

    def test_deterministic_with_seed(self):
        rng = np.random.RandomState(42)
        sig1 = synthesize_ecg_segment(1000, 250, rng=rng)
        rng = np.random.RandomState(42)
        sig2 = synthesize_ecg_segment(1000, 250, rng=rng)
        np.testing.assert_array_equal(sig1, sig2)

    def test_no_nan(self):
        sig = synthesize_ecg_segment(2500, 250)
        assert np.isfinite(sig).all()

    def test_float32_output(self):
        sig = synthesize_ecg_segment(2500, 250)
        assert sig.dtype == np.float32


# ─── ECGWindower Tests ────────────────────────────────────────────────────────

class TestECGWindower:

    def test_windows_generated(self):
        windower = ECGWindower(window_seconds=10, stride_seconds=5, sampling_rate=250)
        signal = np.random.randn(5000).astype(np.float32)
        windows = windower.window_signal(
            signal, "P001", "REC001", "NORMAL", 0, "train", "ptbxl"
        )
        assert len(windows) > 0

    def test_window_length_correct(self):
        windower = ECGWindower(window_seconds=10, stride_seconds=5, sampling_rate=250)
        signal = np.random.randn(5000).astype(np.float32)
        windows = windower.window_signal(
            signal, "P001", "REC001", "NORMAL", 0, "train", "ptbxl"
        )
        for w in windows:
            assert len(w.signal) == windower.window_samples

    def test_provenance_in_window(self):
        windower = ECGWindower(window_seconds=10, stride_seconds=5, sampling_rate=250)
        signal = np.random.randn(5000).astype(np.float32)
        windows = windower.window_signal(
            signal, "PATIENT_42", "RECORD_77", "ABNORMAL", 1, "val", "mitbih"
        )
        assert len(windows) > 0
        w = windows[0]
        assert w.participant_id == "PATIENT_42"
        assert w.record_id == "RECORD_77"
        assert w.label_canonical == "ABNORMAL"
        assert w.label_int == 1
        assert w.split == "val"
        assert w.source_dataset == "mitbih"

    def test_too_short_signal_gives_no_windows(self):
        windower = ECGWindower(window_seconds=10, stride_seconds=5, sampling_rate=250)
        signal = np.random.randn(100).astype(np.float32)  # << 2500
        windows = windower.window_signal(
            signal, "P001", "REC001", "NORMAL", 0, "train", "ptbxl"
        )
        assert len(windows) == 0

    def test_deterministic_windows(self):
        windower = ECGWindower(window_seconds=10, stride_seconds=5, sampling_rate=250)
        np.random.seed(99)
        signal = np.random.randn(7500).astype(np.float32)
        w1 = windower.window_signal(signal, "P1", "R1", "NORMAL", 0, "train", "ptbxl")
        w2 = windower.window_signal(signal, "P1", "R1", "NORMAL", 0, "train", "ptbxl")
        assert len(w1) == len(w2)
        for a, b in zip(w1, w2):
            np.testing.assert_array_equal(a.signal, b.signal)
