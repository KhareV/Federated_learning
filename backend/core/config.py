from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here"
    database_url: str = "sqlite+aiosqlite:///./health_monitor.db"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: List[str] = ["http://localhost:5173","http://localhost:3000"]
    log_level: str = "INFO"
    
    anomaly_threshold: float = 0.5
    sqi_threshold: float = 60.0
    confidence_min_sqi: float = 40.0
    sampling_rate_ecg: int = 250
    sampling_rate_ppg: int = 50
    
    fl_rounds: int = 10
    fl_local_epochs: int = 5
    fl_learning_rate: float = 0.001
    fl_min_clients: int = 3
    fl_personalization_alpha: float = 0.3
    
    qapfl_alpha: float = 0.35
    qapfl_beta: float = 0.25
    qapfl_gamma: float = 0.30
    qapfl_delta: float = 0.10
    
    num_simulated_clients: int = 8
    sim_sampling_interval: float = 0.04
    
    class Config:
        env_file = ".env"

settings = Settings()