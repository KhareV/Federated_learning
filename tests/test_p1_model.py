"""
tests/test_p1_model.py — P1 CNN Model Tests
=============================================
Tests the ECGCNN1D model:
  - Forward pass shape
  - Checkpoint save/load
  - Config serialization
  - ECGWindowDataset
  - predict_proba output range [0, 1]
  - Deterministic (no dropout in eval mode)
"""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
import torch
from models.ecg_cnn import ECGCNN1D, ECGCNNConfig, ECGWindowDataset


@pytest.fixture
def default_config():
    return ECGCNNConfig(input_length=2500)


@pytest.fixture
def model(default_config):
    m = ECGCNN1D(config=default_config)
    m.eval()
    return m


@pytest.fixture
def batch():
    """Batch of 4 synthetic ECG windows."""
    return torch.randn(4, 1, 2500)


class TestECGCNNConfig:

    def test_default_values(self):
        cfg = ECGCNNConfig()
        assert cfg.n_classes == 2
        assert cfg.input_channels == 1
        assert len(cfg.conv_channels) == 4
        assert len(cfg.kernel_sizes) == 4
        assert len(cfg.pool_sizes) == 4

    def test_to_from_dict(self):
        cfg = ECGCNNConfig(dropout=0.3, fc_hidden=64)
        d = cfg.to_dict()
        cfg2 = ECGCNNConfig.from_dict(d)
        assert cfg2.dropout == cfg.dropout
        assert cfg2.fc_hidden == cfg.fc_hidden

    def test_model_version_set(self):
        cfg = ECGCNNConfig(model_version="MODEL_V1")
        assert cfg.model_version == "MODEL_V1"


class TestECGCNN1D:

    def test_forward_output_shape(self, model, batch):
        with torch.no_grad():
            out = model(batch)
        assert out.shape == (4, 2)

    def test_forward_is_finite(self, model, batch):
        with torch.no_grad():
            out = model(batch)
        assert torch.isfinite(out).all()

    def test_predict_proba_range(self, model, batch):
        probs = model.predict_proba(batch)
        assert probs.shape == (4, 2)
        assert (probs >= 0).all()
        assert (probs <= 1).all()
        # Probabilities should sum to ~1
        row_sums = probs.sum(dim=-1)
        assert torch.allclose(row_sums, torch.ones(4), atol=1e-5)

    def test_eval_is_deterministic(self, model, batch):
        model.eval()
        with torch.no_grad():
            out1 = model(batch)
            out2 = model(batch)
        assert torch.allclose(out1, out2)

    def test_parameter_count_positive(self, model):
        assert model.count_parameters() > 0

    def test_checkpoint_save_load(self, model):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = Path(tmpdir) / "test.pt"
            model.save_checkpoint(
                str(ckpt_path), epoch=5,
                metrics={"val_f1": 0.85}
            )
            assert ckpt_path.exists()

            loaded_model, checkpoint = ECGCNN1D.load_checkpoint(str(ckpt_path))
            assert checkpoint["epoch"] == 5
            assert checkpoint["metrics"]["val_f1"] == 0.85

            # Outputs should match
            batch = torch.randn(2, 1, 2500)
            model.eval()
            loaded_model.eval()
            with torch.no_grad():
                out1 = model(batch)
                out2 = loaded_model(batch)
            assert torch.allclose(out1, out2, atol=1e-6)

    def test_single_sample_inference(self, model):
        x = torch.randn(1, 1, 2500)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (1, 2)


class TestECGWindowDataset:

    def test_len(self):
        signals = np.random.randn(10, 2500).astype(np.float32)
        labels = np.random.randint(0, 2, 10)
        ds = ECGWindowDataset(signals, labels)
        assert len(ds) == 10

    def test_item_shapes(self):
        signals = np.random.randn(5, 2500).astype(np.float32)
        labels = np.array([0, 1, 0, 1, 0])
        ds = ECGWindowDataset(signals, labels)
        x, y = ds[0]
        assert x.shape == (1, 2500)  # (channel, samples)
        assert y.dtype == torch.long
        assert y.item() in (0, 1)

    def test_labels_preserved(self):
        signals = np.random.randn(5, 2500).astype(np.float32)
        labels = np.array([1, 0, 1, 0, 1])
        ds = ECGWindowDataset(signals, labels)
        for i, (_, y) in enumerate(ds):
            assert y.item() == labels[i]

    def test_augmentation_adds_noise(self):
        signals = np.ones((3, 2500), dtype=np.float32)
        labels = np.zeros(3)
        ds_aug = ECGWindowDataset(signals, labels, augment=True)
        x, _ = ds_aug[0]
        # With augmentation, signal should not be exactly 1.0 everywhere
        # (very unlikely to be unchanged)
        assert not torch.all(x == 1.0)
