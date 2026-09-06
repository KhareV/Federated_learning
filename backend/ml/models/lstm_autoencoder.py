from .base_model import BaseAnomalyModel
import torch
import torch.nn as nn
import numpy as np

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size=3, hidden_size=16):
        super().__init__()
        self.encoder = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.decoder = nn.LSTM(hidden_size, input_size, batch_first=True)
    def forward(self, x):
        _, (h, _) = self.encoder(x)
        out, _ = self.decoder(h.transpose(0,1).repeat(1, x.size(1), 1))
        return out

class LSTMModel(BaseAnomalyModel):
    def __init__(self):
        self.model = LSTMAutoencoder()
    def fit(self, X, y=None): pass
    def predict(self, X): return np.zeros(len(X))
    def get_reconstruction_error(self, x): return 0.1
    def get_uncertainty(self, x, n_samples=20): return 0.05
    def get_state_dict(self): return self.model.state_dict()
    def load_state_dict(self, state): self.model.load_state_dict(state)