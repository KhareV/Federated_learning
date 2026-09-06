"""
models/__init__.py
P1 Models package.
"""
from models.ecg_cnn import ECGCNN1D, ECGCNNConfig

__all__ = ["ECGCNN1D", "ECGCNNConfig"]
