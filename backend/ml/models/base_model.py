from abc import ABC, abstractmethod
import numpy as np

class BaseAnomalyModel(ABC):
    @abstractmethod
    def fit(self, X, y=None): pass
    @abstractmethod
    def predict(self, X): pass
    def predict_proba(self, X): return np.zeros(len(X))
    def get_feature_importance(self): return None
    def save(self, path): pass
    def load(self, path): pass
    @property
    def model_name(self): return "BaseModel"
    def get_state_dict(self): return {}
    def load_state_dict(self, state): pass