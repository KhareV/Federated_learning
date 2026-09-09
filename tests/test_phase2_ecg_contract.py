"""Phase 2 gates: frozen preprocessing lifecycle and canonical SQI state."""

import numpy as np
import pytest

from preprocessing.ecg import ECGPreprocessor, synthesize_ecg_segment
from preprocessing.quality_ecg import ECGQualityAssessor


def test_transform_requires_frozen_training_statistics():
    preprocessor = ECGPreprocessor()
    with pytest.raises(RuntimeError, match="fit on training data"):
        preprocessor.transform(np.ones(2500, dtype=np.float32), 250)


def test_fit_transform_uses_training_statistics(tmp_path):
    train = [synthesize_ecg_segment(2500, seed=i) for i in range(2)]
    preprocessor = ECGPreprocessor().fit(train, source_fs=250)
    assert preprocessor.is_fitted

    artifact = tmp_path / "preprocessing.json"
    preprocessor.save_normalization_stats(artifact)
    loaded = ECGPreprocessor.load_normalization_stats(artifact)

    expected = preprocessor.transform(train[0], 250).signal
    actual = loaded.transform(train[0], 250).signal
    np.testing.assert_array_equal(expected, actual)
    assert loaded.config_dict["normalization_fitted"] is True


def test_transform_does_not_refit_on_shifted_signal():
    train = [np.zeros(2500, dtype=np.float32), np.ones(2500, dtype=np.float32)]
    preprocessor = ECGPreprocessor().fit(train, source_fs=250)
    shifted = np.full(2500, 100.0, dtype=np.float32)
    result = preprocessor.transform(shifted, 250)
    assert result.normalization_mean == preprocessor.normalization_stats.mean
    assert result.normalization_std == preprocessor.normalization_stats.std


def test_sqi_exposes_canonical_unreliable_state():
    result = ECGQualityAssessor(fs=250).assess(np.zeros(2500, dtype=np.float32))
    assert result.canonical_state == "UNRELIABLE"
    assert result.is_usable is False
    assert ECGQualityAssessor(fs=250).sqi_to_dict(result)["canonical_state"] == "UNRELIABLE"
