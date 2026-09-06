from .base_model import BaseAnomalyModel
from sklearn.ensemble import IsolationForest
import numpy as np

class IFModel(BaseAnomalyModel):
    def __init__(self):
        self.model = IsolationForest()
    def fit(self, X, y=None):
        self.model.fit(X)
        return self
    def predict(self, X):
        preds = self.model.predict(X)
        return np.where(preds == -1, 1, 0)
    @property
    def model_name(self): return "IsolationForest" 