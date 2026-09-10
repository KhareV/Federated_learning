import numpy as np
import torch

from backend.ml.signal_processing.ppg_processor import PPGProcessor
from backend.ml.signal_processing.spo2_processor import SpO2Processor
from backend.ml.signal_quality.ppg_sqi import PPGSQICalculator
from models.multimodal_fusion import MultimodalFusionModel
from datasets.bidmc import BIDMCDataset


def test_ppg_processing_is_deterministic_and_extracts_heart_rate():
    fs = 50
    t = np.arange(500) / fs
    raw = np.sin(2 * np.pi * 1.2 * t)
    first = PPGProcessor().process(raw, fs)
    second = PPGProcessor().process(raw, fs)
    np.testing.assert_array_equal(first.filtered, second.filtered)
    assert first.heart_rate_bpm > 0
    assert first.quality_state in {"GOOD", "DEGRADED", "UNRELIABLE"}


def test_ppg_sparse_nans_are_interpolated_but_excessive_missingness_is_rejected():
    processor = PPGProcessor()
    t = np.arange(500) / 50
    raw = np.sin(2 * np.pi * 1.2 * t)
    raw[10:20] = np.nan
    assert processor.process(raw, 50).quality_state != "UNRELIABLE"
    raw[:450] = np.nan
    result = processor.process(raw, 50)
    assert result.quality_state == "UNRELIABLE"
    assert result.feature_values["reason"] == "excessive_nonfinite"


def test_spo2_does_not_fabricate_missing_values():
    result = SpO2Processor().process([np.nan, np.nan])
    assert result.valid is False
    assert result.quality_state == "UNRELIABLE"
    assert np.isnan(result.spo2)


def test_ppg_sqi_rejects_nonfinite_input():
    result = PPGSQICalculator().compute_ppg_sqi([np.nan], [np.nan], [], [])
    assert result.quality_label == "UNRELIABLE"
    assert result.overall_sqi == 0.0


def test_fusion_accepts_missing_ppg_with_mask():
    model = MultimodalFusionModel()
    output = model(
        torch.zeros(2, 2500), torch.zeros(2, 2500),
        torch.zeros(2, 4), torch.tensor([[1., 0., 1., 1.], [1., 1., 1., 1.]]),
    )
    assert output.shape == (2, 2)
    assert torch.isfinite(output).all()


def test_bidmc_loader_aligns_waveform_and_numeric_modalities():
    session = BIDMCDataset().load_session("bidmc01")
    assert session.sampling_rate == 125
    assert "ECG" in session.signals and "PPG" in session.signals
    assert "SpO2" in session.numerics
    window = next(BIDMCDataset().synchronized_windows("bidmc01"))
    assert window["availability_mask"]["ECG"] is True
    assert window["availability_mask"]["PPG"] is True
    assert window["label"] is None
