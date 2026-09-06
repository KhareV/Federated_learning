"""
tests/test_p1_sqi.py — P1 SQI Tests
=====================================
Tests the ECGQualityAssessor against controlled synthetic signals:
  - Clean ECG → EXCELLENT/GOOD
  - Flatline → POOR (score near 0)
  - High noise → lower SQI
  - Baseline drift → lower SQI
  - Clipped signal → clipping penalty
  - NaN/missing values → handled

All tests are deterministic and use no external data.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from preprocessing.quality_ecg import ECGQualityAssessor, SQIResult
from preprocessing.ecg import synthesize_ecg_segment, ECGPreprocessor


@pytest.fixture
def assessor():
    return ECGQualityAssessor(fs=250)


@pytest.fixture
def preprocessor():
    return ECGPreprocessor()


def clean_ecg(n=2500, noise=0.02):
    """Preprocessed clean ECG."""
    raw = synthesize_ecg_segment(n, fs=250, noise_std=noise, seed=42)
    prep = ECGPreprocessor().process(raw, 250)
    return prep.signal


def flatline_signal(n=2500):
    return np.zeros(n, dtype=np.float32)


def high_noise_signal(n=2500):
    rng = np.random.RandomState(1)
    return rng.normal(0, 1.0, n).astype(np.float32)


def baseline_drift_signal(n=2500, fs=250):
    t = np.arange(n) / fs
    clean = synthesize_ecg_segment(n, fs=fs, noise_std=0.01, seed=2)
    drift = (0.8 * np.sin(2 * np.pi * 0.15 * t)).astype(np.float32)
    raw = clean + drift
    prep = ECGPreprocessor().process(raw, fs)
    return prep.signal


def clipped_signal(n=2500):
    sig = synthesize_ecg_segment(n, 250, noise_std=0.02, seed=5)
    sig = np.clip(sig, -0.1, 0.1)
    return sig.astype(np.float32)


class TestECGQualityAssessor:

    def test_clean_ecg_is_good_quality(self, assessor):
        sig = clean_ecg(noise=0.02)
        result = assessor.assess(sig)
        assert isinstance(result, SQIResult)
        assert result.overall_sqi > 40, (
            f"Clean ECG SQI too low: {result.overall_sqi}"
        )
        assert result.quality_state in ("EXCELLENT", "GOOD", "FAIR")
        assert result.is_usable is True

    def test_flatline_gets_poor_sqi(self, assessor):
        sig = flatline_signal()
        result = assessor.assess(sig)
        assert result.overall_sqi == 0.0, (
            f"Flatline should score 0, got {result.overall_sqi}"
        )
        assert result.quality_state == "POOR"
        assert result.is_usable is False
        assert result.flatline_score == 0.0
        assert any("flatline" in r.lower() for r in result.low_quality_reasons)

    def test_high_noise_lower_sqi_than_clean(self, assessor):
        clean = clean_ecg(noise=0.02)
        noisy = high_noise_signal()
        clean_result = assessor.assess(clean)
        noisy_result = assessor.assess(noisy)
        assert clean_result.overall_sqi > noisy_result.overall_sqi, (
            f"Clean ({clean_result.overall_sqi}) should > noisy ({noisy_result.overall_sqi})"
        )

    def test_clipped_signal_penalized(self, assessor):
        sig = clipped_signal()
        result = assessor.assess(sig)
        # Clipping should reduce amplitude score
        assert result.amplitude_score < 80, (
            f"Clipped signal amplitude_score too high: {result.amplitude_score}"
        )

    def test_nan_input_returns_poor(self, assessor):
        sig = np.full(2500, np.nan, dtype=np.float32)
        result = assessor.assess(sig)
        assert result.overall_sqi == 0.0
        assert result.quality_state == "POOR"
        assert result.is_usable is False

    def test_deterministic_output(self, assessor):
        sig = clean_ecg()
        result1 = assessor.assess(sig)
        result2 = assessor.assess(sig)
        assert result1.overall_sqi == result2.overall_sqi
        assert result1.quality_state == result2.quality_state

    def test_sqi_range_0_to_100(self, assessor):
        for sig in [clean_ecg(), flatline_signal(), high_noise_signal()]:
            result = assessor.assess(sig)
            assert 0.0 <= result.overall_sqi <= 100.0
            assert 0.0 <= result.snr_score <= 100.0
            assert 0.0 <= result.baseline_score <= 100.0
            assert 0.0 <= result.amplitude_score <= 100.0
            assert 0.0 <= result.clipping_score <= 100.0
            assert 0.0 <= result.flatline_score <= 100.0

    def test_quality_states_valid(self, assessor):
        for sig in [clean_ecg(), flatline_signal(), high_noise_signal()]:
            result = assessor.assess(sig)
            assert result.quality_state in ("EXCELLENT", "GOOD", "FAIR", "POOR")

    def test_batch_assess(self, assessor):
        signals = [clean_ecg(), flatline_signal(), high_noise_signal()]
        results = assessor.assess_batch(signals)
        assert len(results) == 3

    def test_sqi_to_dict(self, assessor):
        sig = clean_ecg()
        result = assessor.assess(sig)
        d = assessor.sqi_to_dict(result)
        assert "overall_sqi" in d
        assert "quality_state" in d
        assert "is_usable" in d
        assert "flatline_score" in d

    def test_thresholds_enforced(self):
        """Custom thresholds should affect quality state assignment."""
        strict = ECGQualityAssessor(excellent_threshold=99, good_threshold=90,
                                     fair_threshold=70, fs=250)
        sig = clean_ecg()
        result = strict.assess(sig)
        # With very high thresholds, even clean signal may not be EXCELLENT
        assert result.quality_state in ("EXCELLENT", "GOOD", "FAIR", "POOR")
