"""Centralized late-fusion model with explicit missing-modality masks."""

import torch
import torch.nn as nn


class MultimodalFusionModel(nn.Module):
    """ECG/PPG encoders plus HR/SpO2 features and an availability mask."""

    def __init__(self, n_scalar_features=4, n_classes=2):
        super().__init__()
        self.ecg_encoder = self._encoder()
        self.ppg_encoder = self._encoder()
        self.fusion = nn.Sequential(
            nn.Linear(64 + 64 + n_scalar_features + 4, 64),
            nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, n_classes),
        )

    @staticmethod
    def _encoder():
        return nn.Sequential(
            nn.Conv1d(1, 16, 9, padding=4), nn.ReLU(), nn.MaxPool1d(4),
            nn.Conv1d(16, 32, 7, padding=3), nn.ReLU(), nn.MaxPool1d(4),
            nn.Conv1d(32, 64, 5, padding=2), nn.ReLU(), nn.AdaptiveAvgPool1d(1),
        )

    def forward(self, ecg, ppg, scalar_features, availability_mask):
        if ecg.ndim == 2: ecg = ecg.unsqueeze(1)
        if ppg.ndim == 2: ppg = ppg.unsqueeze(1)
        ecg_embedding = self.ecg_encoder(ecg).flatten(1)
        ppg_embedding = self.ppg_encoder(ppg).flatten(1)
        # Mask embeddings and scalar values so zeros cannot masquerade as data.
        ecg_embedding = ecg_embedding * availability_mask[:, 0:1]
        ppg_embedding = ppg_embedding * availability_mask[:, 1:2]
        return self.fusion(torch.cat((ecg_embedding, ppg_embedding, scalar_features, availability_mask), dim=1))
