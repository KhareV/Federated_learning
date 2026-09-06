from .base_model import BaseAnomalyModel
import xgboost as xgb

class XGBModel(BaseAnomalyModel):
    def __init__(self):
        self.model = xgb.XGBClassifier()
    def fit(self, X, y=None):
        if y is not None:
            self.model.fit(X, y)
        return self
    def predict(self, X):
        return self.model.predict(X)
    def get_feature_importance(self):
        return self.model.feature_importances_
    @property
    def model_name(self): return "XGBoost" 