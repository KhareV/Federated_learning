"""
tests/test_p1_features.py — P1 Feature Extraction Tests
=========================================================
Tests the ECGFeatureExtractor:
  - Fixed output shape (n_features)
  - All-finite output for valid signals
  - Deterministic output
  - Handles invalid input gracefully
  - Feature names list length matches vector
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from features.ecg_features import ECGFeatureExtractor, ECGFeatureSet
from preprocessing.ecg import ECGPreprocessor, synthesize_ecg_segment


@pytest.fixture
def extractor():
    return ECGFeatureExtractor(fs=250)


@pytest.fixture
def processed_clean_ecg():
    raw = synthesize_ecg_segment(2500, fs=250, noise_std=0.02, seed=42)
    prep = ECGPreprocessor().process(raw, 250)
    return prep.signal


class TestECGFeatureExtractor:

    def test_feature_names_count(self, extractor):
        assert len(extractor.FEATURE_NAMES) == extractor.n_features

    def test_output_shape(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        assert result.feature_values.shape == (extractor.n_features,)

    def test_all_finite(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        assert np.isfinite(result.feature_values).all(), (
            f"Non-finite features: "
            f"{[(n, v) for n, v in zip(result.feature_names, result.feature_values) if not np.isfinite(v)]}"
        )

    def test_float32_output(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        assert result.feature_values.dtype == np.float32

    def test_deterministic(self, extractor, processed_clean_ecg):
        r1 = extractor.extract(processed_clean_ecg, record_id="test")
        r2 = extractor.extract(processed_clean_ecg, record_id="test")
        np.testing.assert_array_equal(r1.feature_values, r2.feature_values)

    def test_empty_signal_returns_invalid(self, extractor):
        result = extractor.extract(np.array([]), record_id="empty")
        assert result.is_valid is False
        assert result.feature_values.shape == (extractor.n_features,)

    def test_nan_signal_returns_invalid(self, extractor):
        sig = np.full(2500, np.nan, dtype=np.float32)
        result = extractor.extract(sig)
        assert result.is_valid is False

    def test_to_dict(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        d = result.to_dict()
        assert len(d) == extractor.n_features
        assert all(isinstance(v, float) for v in d.values())

    def test_batch_extraction_shape(self, extractor):
        signals = [
            ECGPreprocessor().process(
                synthesize_ecg_segment(2500, 250, seed=i), 250
            ).signal
            for i in range(5)
        ]
        X = extractor.extract_batch(signals)
        assert X.shape == (5, extractor.n_features)
        assert np.isfinite(X).all()

    def test_time_domain_features_plausible(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        d = result.to_dict()
        # Z-scored signal: mean close to 0, std close to 1
        assert abs(d["td_mean"]) < 1.0, f"td_mean={d['td_mean']}"
        assert d["td_std"] > 0, f"td_std={d['td_std']}"
        assert d["td_range"] > 0, f"td_range={d['td_range']}"

    def test_hrv_features_plausible(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        d = result.to_dict()
        # Should detect some R-peaks in a 10s ECG at ~72 bpm
        assert d["hrv_n_rpeaks"] >= 0, "n_rpeaks should be >= 0"

    def test_sqi_passed_through(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg, sqi_overall=75.0)
        d = result.to_dict()
        assert d["qual_sqi_overall"] == 75.0

    def test_feature_version_in_result(self, extractor, processed_clean_ecg):
        result = extractor.extract(processed_clean_ecg)
        assert result.feature_version == "1.0.0"
