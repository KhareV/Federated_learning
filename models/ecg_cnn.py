"""
models/ecg_cnn.py — 1D CNN for ECG Classification
===================================================
PyTorch 1D Convolutional Neural Network for binary ECG classification
(NORMAL vs ABNORMAL) from preprocessed 10-second windows at 250 Hz.

Input shape: (batch, 1, 2500) — 1 lead, 2500 samples
Output: (batch, 2) — logits for [NORMAL, ABNORMAL]

Architecture:
  Block 1: Conv1d(1→32, k=9, s=1) → BN → ReLU → MaxPool(4)
  Block 2: Conv1d(32→64, k=7, s=1) → BN → ReLU → MaxPool(4)
  Block 3: Conv1d(64→128, k=5, s=1) → BN → ReLU → MaxPool(4)
  Block 4: Conv1d(128→256, k=3, s=1) → BN → ReLU → MaxPool(4)
  Adaptive Average Pool → (batch, 256, 1)
  Flatten → FC(256→128) → Dropout(0.4) → ReLU → FC(128→2)

Design decisions:
  - Decreasing kernel sizes: large early kernels capture coarse morphology
    (P-wave, QRS, T-wave), smaller later kernels learn fine features.
  - BatchNorm: stabilizes training on multi-source data.
  - MaxPool: reduces temporal resolution while preserving QRS peaks.
  - Dropout(0.4): regularization for limited dataset sizes.
  - Configurable: all architecture parameters can be changed via ECGCNNConfig.

Model versioning:
  - MODEL_V1 checkpoint is frozen after model selection.
  - Architecture changes require MODEL_V2+.
"""

import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


# ─── Configuration ────────────────────────────────────────────────────────────

@dataclass
class ECGCNNConfig:
    """
    Fully configurable 1D CNN architecture specification.
    Storing this alongside the checkpoint ensures reproducibility.
    """
    input_channels: int = 1
    input_length: int = 2500       # samples (10s at 250 Hz)
    n_classes: int = 2
    conv_channels: List[int] = None    # per-block output channels
    kernel_sizes: List[int] = None     # per-block kernel sizes
    pool_sizes: List[int] = None       # per-block max-pool sizes
    fc_hidden: int = 128
    dropout: float = 0.4
    model_version: str = "MODEL_V1"
    preprocessing_version: str = "1.0.0"
    feature_version: str = "1.0.0"

    def __post_init__(self):
        if self.conv_channels is None:
            self.conv_channels = [32, 64, 128, 256]
        if self.kernel_sizes is None:
            self.kernel_sizes = [9, 7, 5, 3]
        if self.pool_sizes is None:
            self.pool_sizes = [4, 4, 4, 4]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ECGCNNConfig":
        return cls(**d)


# ─── Convolutional Block ──────────────────────────────────────────────────────

class ConvBlock1D(nn.Module):
    """Conv1d → BatchNorm → ReLU → MaxPool block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        pool_size: int,
    ):
        super().__init__()
        self.conv = nn.Conv1d(
            in_channels, out_channels,
            kernel_size=kernel_size,
            padding=kernel_size // 2,  # same-ish padding
            bias=False,
        )
        self.bn = nn.BatchNorm1d(out_channels)
        self.act = nn.ReLU(inplace=True)
        self.pool = nn.MaxPool1d(kernel_size=pool_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(self.act(self.bn(self.conv(x))))


# ─── 1D CNN Classifier ────────────────────────────────────────────────────────

class ECGCNN1D(nn.Module):
    """
    1D CNN ECG Classifier.

    Forward pass:
      x: (batch, 1, n_samples)
      → conv blocks
      → adaptive avg pool
      → flatten
      → FC layers
      → logits (batch, n_classes)

    To get probabilities: F.softmax(model(x), dim=-1)
    To get class: logits.argmax(dim=-1)
    """

    def __init__(self, config: Optional[ECGCNNConfig] = None):
        super().__init__()
        self.config = config or ECGCNNConfig()

        channels = [self.config.input_channels] + self.config.conv_channels
        self.blocks = nn.Sequential(*[
            ConvBlock1D(
                in_channels=channels[i],
                out_channels=channels[i + 1],
                kernel_size=self.config.kernel_sizes[i],
                pool_size=self.config.pool_sizes[i],
            )
            for i in range(len(self.config.conv_channels))
        ])

        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(self.config.conv_channels[-1], self.config.fc_hidden)
        self.dropout = nn.Dropout(self.config.dropout)
        self.fc2 = nn.Linear(self.config.fc_hidden, self.config.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        x : torch.Tensor of shape (batch, 1, n_samples)

        Returns
        -------
        logits : torch.Tensor of shape (batch, n_classes)
        """
        x = self.blocks(x)
        x = self.global_pool(x)
        x = self.flatten(x)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Return softmax probabilities (batch, n_classes)."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return F.softmax(logits, dim=-1)

    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    # ── Serialization ─────────────────────────────────────────────────────────

    def save_checkpoint(
        self,
        path: str,
        epoch: int,
        optimizer_state: Optional[dict] = None,
        metrics: Optional[dict] = None,
    ):
        """Save full checkpoint (model weights + config + metadata)."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "model_state_dict": self.state_dict(),
            "config": self.config.to_dict(),
            "epoch": epoch,
            "metrics": metrics or {},
            "optimizer_state_dict": optimizer_state,
            "pytorch_version": torch.__version__,
        }
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved: {path} (epoch {epoch})")

    @classmethod
    def load_checkpoint(cls, path: str, device: Optional[str] = None) -> Tuple["ECGCNN1D", dict]:
        """
        Load model from checkpoint.

        Returns
        -------
        (model, checkpoint_dict)
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        checkpoint = torch.load(path, map_location=device, weights_only=False)
        config = ECGCNNConfig.from_dict(checkpoint["config"])
        model = cls(config=config)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()
        logger.info(
            f"Loaded checkpoint: {path} "
            f"(epoch={checkpoint.get('epoch', '?')}, "
            f"metrics={checkpoint.get('metrics', {})})"
        )
        return model, checkpoint


# ─── Dataset Wrapper ──────────────────────────────────────────────────────────

class ECGWindowDataset(torch.utils.data.Dataset):
    """
    PyTorch Dataset wrapping ECG windows for training the 1D CNN.

    Parameters
    ----------
    signals : np.ndarray of shape (n_windows, n_samples)
    labels : np.ndarray of shape (n_windows,) — integer class labels
    augment : bool — apply light augmentation during training
    """

    def __init__(
        self,
        signals: np.ndarray,
        labels: np.ndarray,
        augment: bool = False,
        augment_noise_std: float = 0.02,
    ):
        assert len(signals) == len(labels), \
            f"signals ({len(signals)}) and labels ({len(labels)}) must match"
        self.signals = signals.astype(np.float32)
        self.labels = labels.astype(np.int64)
        self.augment = augment
        self.augment_noise_std = augment_noise_std

    def __len__(self) -> int:
        return len(self.signals)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        sig = self.signals[idx].copy()

        if self.augment:
            # Light Gaussian noise augmentation only
            sig += np.random.normal(0, self.augment_noise_std, sig.shape)
            sig = sig.astype(np.float32)

        # Shape: (1, n_samples) — single channel
        x = torch.tensor(sig, dtype=torch.float32).unsqueeze(0)
        y = torch.tensor(self.labels[idx], dtype=torch.long)
        return x, y
