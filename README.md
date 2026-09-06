# QAPFL Health Monitor Platform

## Non-Invasive Continuous Health Monitor with Federated Learning

**Quality-Aware Personalized Federated Learning (QAPFL) for Multimodal Wearable Health Monitoring**

> ⚠️ **MEDICAL DISCLAIMER**: This software is an engineering research prototype. It is NOT intended for medical diagnosis, treatment, or emergency decision-making. All outputs are research results only.

---

## Project Overview

This platform is a final-year engineering research prototype implementing:

- **Real-time physiological signal monitoring** (ECG, PPG, HR, SpO₂)
- **Signal Quality Index (SQI) assessment** with quality-aware confidence
- **Anomaly detection** using Isolation Forest, XGBoost, and LSTM Autoencoder
- **Personalized baseline learning** per user
- **Federated Learning** with FedAvg, Personalized FL, and the proposed **QAPFL**
- **Research experiment framework** (noise robustness, ablation study, model comparison)
- **Professional React dashboard** with 33+ pages

### Research Novelty: QAPFL

Standard FedAvg treats all clients equally. QAPFL weights each client's contribution by:

```
quality_score_i = α·SQI_i + β·data_quality_i + γ·local_F1_i + δ·(1-uncertainty_i)
weight_i        = softmax(quality_score_i)
```

Where α, β, γ, δ are configurable weights. Clients with poor signal quality, missing data, low local performance, or high uncertainty contribute less to the global model, making the system robust to noisy/unreliable clients.

---

## Project Structure

```
health-monitor-platform/
├── backend/
│   ├── api/routes/          # FastAPI routes (12 files, 50+ endpoints)
│   ├── core/                # Auth, config, logging, WebSocket
│   ├── db/                  # SQLAlchemy models (16 tables)
│   ├── experiments/         # Experiment runner, noise robustness, ablation
│   ├── federated/           # FL server, FedAvg, PersonalizedFL, QAPFL
│   ├── ml/                  # Signal processing, SQI, models, anomaly detection
│   │   ├── models/          # IsolationForest, XGBoost, LSTM Autoencoder
│   │   ├── personalization/ # Baseline learner, personal model manager
│   │   ├── signal_processing/ # ECG, PPG, SpO₂ processors
│   │   └── signal_quality/  # ECG SQI, PPG SQI, Quality Assessor
│   ├── services/            # Monitoring, FL, Report services
│   ├── simulator/           # 8 simulated clients with distinct profiles
│   └── main.py              # FastAPI application
├── frontend/
│   └── src/
│       ├── components/      # Layout, UI, Charts, Waveforms, FL components
│       ├── pages/           # 33+ dashboard pages
│       ├── services/        # API client, WebSocket service
│       └── stores/          # Zustand state management
├── tests/                   # Unit + integration tests
├── docs/                    # Architecture, QAPFL algorithm, ESP32 docs
├── scripts/                 # Seed database, run demo
└── docker/                  # Dockerfiles, nginx config
```

---

## Quick Start (Without Docker)

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### Backend Setup

```bash
# 1. Clone and navigate to project
cd health-monitor-platform

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env if needed (default settings work for development)

# 5. Seed database with demo data
python scripts/seed_database.py

# 6. Start backend
uvicorn backend.main:app --reload --port 8000
```

Backend will be available at:
- **API**: http://localhost:8000
- **Interactive docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Frontend Setup

```bash
# Open a new terminal, navigate to frontend
cd health-monitor-platform/frontend

# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

### Login

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Administrator | `admin` | `admin123` | Full access |
| Researcher | `researcher` | `research123` | AI, FL, experiments |
| User | `user` | `user123` | Personal health data |

---

## Docker Setup

```bash
# Build and start all services
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Running Tests

```bash
# From project root with venv activated
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_aggregation.py -v    # FL aggregation tests
python -m pytest tests/test_sqi.py -v            # Signal quality tests
python -m pytest tests/test_signal_processing.py -v
```

### Expected test output:
```
tests/test_aggregation.py::test_qapfl_weights_reflect_quality PASSED
tests/test_aggregation.py::test_weights_sum_to_one PASSED
tests/test_anomaly_detection.py::test_isolation_forest PASSED
tests/test_anomaly_detection.py::test_anomaly_classification PASSED
tests/test_api.py::test_get_system_health PASSED
tests/test_signal_processing.py::test_ecg_bandpass_filter PASSED
tests/test_signal_processing.py::test_r_peak_detection PASSED
tests/test_sqi.py::test_clean_ecg_high_sqi PASSED
tests/test_sqi.py::test_noisy_ecg_low_sqi PASSED
======================== 9 passed in ~2s ========================
```

---

## Demo Scenario

Follow these steps for the complete demonstration:

1. **Login** → admin/admin123
2. **Overview** → See real-time stat cards and trend charts
3. **Live Monitoring** → Start simulator, view scrolling ECG/PPG waveforms, live HR and SpO₂
4. **Signal Quality** → View ECG SQI, PPG SQI, quality timeline
5. **Introduce noise** → Increase noise level in simulator → watch SQI decrease
6. **Anomaly Detection** → Verify noisy data produces LOW_CONFIDENCE not HIGH_CONFIDENCE
7. **Inject anomaly** → Enable physiological anomaly → watch anomaly score rise
8. **Explainable AI** → View feature contributions (SHAP-like)
9. **Personalized Baseline** → View deviation from learned baseline
10. **FL Overview** → Start FL training (select QAPFL strategy)
11. **FL Clients** → See 8 clients with different signal qualities
12. **FL Aggregation** → Compare FedAvg (equal weights) vs QAPFL (quality-weighted)
13. **Robustness Testing** → Run noise robustness experiment → compare FedAvg vs QAPFL curves
14. **Ablation Study** → Run configurations A→E → see each QAPFL component's contribution
15. **Reports** → Generate and export research report

---

## Architecture

### Data Flow

```
ESP32 / Simulator
        │
        ▼ BLE Adapter (standardized SensorReading)
        │
        ▼ Signal Processing
        │  ├── ECG: bandpass → notch → R-peak detection → HRV metrics
        │  ├── PPG: bandpass → peak detection → pulse intervals
        │  └── SpO₂: smoothing → confidence estimation
        │
        ▼ Signal Quality Index (SQI)
        │  ├── ECG SQI: SNR + baseline stability + QRS reliability + amplitude consistency
        │  ├── PPG SQI: baseline stability + peak regularity + amplitude stability + perfusion
        │  └── Overall SQI: weighted combination → EXCELLENT/GOOD/FAIR/POOR label
        │
        ▼ Feature Extraction (24-dimensional feature vector)
        │
        ▼ Anomaly Detection
        │  ├── Model inference (IsolationForest / XGBoost / LSTM Autoencoder)
        │  ├── Confidence adjusted by SQI
        │  └── Classification: NORMAL / POSSIBLE / LOW_CONFIDENCE / HIGH_CONFIDENCE
        │
        ▼ Personalization
        │  ├── Baseline learner (rolling statistics)
        │  └── Personal model fine-tuning
        │
        ▼ Database (SQLAlchemy + SQLite)
        │
        ▼ FastAPI + WebSocket → React Dashboard
```

### Federated Learning Flow

```
8 Simulated Clients (different signal quality, dataset size, baselines)
        │
        ▼ Local training (5 epochs per client)
        │
        ▼ Quality metadata upload:
        │  ├── ECG SQI, PPG SQI
        │  ├── Usable sample fraction
        │  ├── Local accuracy, F1, loss
        │  └── MC Dropout uncertainty
        │
        ▼ QAPFL Aggregation Server
        │  ├── quality_score_i = α·SQI + β·data_quality + γ·F1 - δ·uncertainty
        │  ├── weight_i = softmax(quality_score_i)
        │  └── Global model = Σ weight_i × local_model_i
        │
        ▼ Personalization
        │  └── local_model_i = (1-α)·global + α·local (per client)
        │
        ▼ Global model distributed back to clients
```

---

## QAPFL Algorithm Details

See [`docs/qapfl_algorithm.md`](docs/qapfl_algorithm.md) for the complete mathematical formulation.

**Configurable weights** (via `.env` or Settings page):
```
QAPFL_ALPHA=0.35  # Signal quality weight
QAPFL_BETA=0.25   # Data quality weight
QAPFL_GAMMA=0.30  # Model performance weight
QAPFL_DELTA=0.10  # Uncertainty penalty weight
```

All weights must sum to 1.0. The server auto-normalizes if they don't.

---

## Simulated Clients

| Client | Description | ECG Noise | Missing Data | Dataset Size |
|--------|-------------|-----------|--------------|--------------|
| client_01 (Alice) | Clean data, stable | 5% | 1% | 5,000 |
| client_02 (Bob) | Moderate noise | 20% | 3% | 7,000 |
| client_03 (Carol) | High motion artifacts | 45% | 8% | 4,000 |
| client_04 (David) | Missing data segments | 12% | 20% | 3,500 |
| client_05 (Eve) | Resource limited | 18% | 5% | 2,000 |
| client_06 (Frank) | Elevated HR baseline | 15% | 4% | 6,000 |
| client_07 (Grace) | SpO₂ variability | 10% | 6% | 5,500 |
| client_08 (Henry) | Mixed quality | 30% | 12% | 4,500 |

---

## API Reference

Full OpenAPI documentation available at http://localhost:8000/docs

Key endpoints:

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Get JWT token |
| `GET /monitoring/live/{client_id}` | Latest sensor readings |
| `POST /monitoring/simulate/start` | Start client simulator |
| `GET /fl/status` | FL system status |
| `POST /fl/training/start` | Start FL training round |
| `GET /fl/aggregation/{round_id}` | Client weights + reasoning |
| `GET /fl/clients` | All client metrics |
| `POST /experiments/robustness/run` | Run noise robustness experiment |
| `POST /experiments/ablation/run` | Run ablation study |
| `WS /ws/live/{client_id}` | Real-time sensor data stream |
| `WS /ws/fl/progress` | FL training progress |

---

## ESP32 Integration

To use with real hardware (ESP32 + MAX30102 + AD8232):

1. Flash ESP32 with provided BLE firmware (see [`docs/esp32_integration.md`](docs/esp32_integration.md))
2. The BLE adapter automatically handles the packet format
3. Replace simulator calls with real BLE connection in `monitoring_service.py`

**BLE Packet Format:**
```
[0x55 0xAA]  Header (2 bytes)
[seq(4)]     Sequence number
[hr(2)]      Heart rate × 10 (e.g., 740 = 74.0 BPM)
[spo2(2)]    SpO₂ × 100 (e.g., 9820 = 98.20%)
[n_ecg(2)]   Number of ECG samples
[ecg×n(2n)]  ECG samples (int16, µV)
[n_ppg(2)]   Number of PPG samples  
[ppg×n(2n)]  PPG samples (int16)
[battery(1)] Battery % (0-100)
[chk(2)]     CRC16 checksum
```

---

## Research Experiments

### Available Experiments

| # | Name | Description |
|---|------|-------------|
| 1 | Centralized vs Federated | Compare centralized model vs FedAvg |
| 2 | FedAvg vs Personalized FL | Effect of personalization |
| 3 | FedAvg vs QAPFL | Main comparison: standard vs quality-aware |
| 4 | Noise Robustness | F1 vs noise level 0-50% |
| 5 | Missing Data Robustness | Performance vs missing data rate |
| 6 | Client Heterogeneity | Effect of varied client quality |
| 7 | Personalization Benefit | Improvement from local fine-tuning |
| 8 | Communication Cost | Accuracy vs communication budget |
| 9 | Resource Constraints | Performance under limited resources |
| 10 | Ablation Study | FedAvg → +personalization → +quality → QAPFL |

All experiment results are stored with:
- Experiment ID, configuration, random seed
- Per-round metrics
- Timestamp

**No results are fabricated** — all come from actual computation.

---

## Configuration

Key settings in `.env`:

```bash
# Anomaly Detection
ANOMALY_THRESHOLD=0.5        # Score threshold for anomaly classification
SQI_THRESHOLD=60.0           # Minimum SQI for high-confidence anomaly
CONFIDENCE_MIN_SQI=40.0      # Minimum SQI to report any confidence

# Federated Learning
FL_ROUNDS=10                 # Training rounds per experiment
FL_LOCAL_EPOCHS=5            # Local epochs per client per round
FL_LEARNING_RATE=0.001       # Local optimizer learning rate
FL_MIN_CLIENTS=3             # Minimum clients to start a round
FL_PERSONALIZATION_ALPHA=0.3 # Personalization mixing coefficient

# QAPFL Weights (must sum to 1.0)
QAPFL_ALPHA=0.35             # Signal quality weight
QAPFL_BETA=0.25              # Data quality weight
QAPFL_GAMMA=0.30             # Model performance weight
QAPFL_DELTA=0.10             # Uncertainty penalty weight
```

All parameters can also be changed via the Settings page in the dashboard.

---

## Limitations

1. **Synthetic data only**: All physiological data is mathematically generated. Results are for algorithm validation, not clinical performance claims.
2. **In-process FL simulation**: FL uses in-process simulation, not real network communication. Communication costs are estimated based on model size.
3. **LSTM Autoencoder**: The LSTM model uses simulated training due to synthetic data. In a real deployment, it would be trained on actual physiological recordings.
4. **No real cryptography**: FL updates use simulated transmission. Production would require TLS and optionally differential privacy.
5. **Not a medical device**: This system has NOT been validated for clinical use and must not be used for healthcare decisions.

---

## Development

```bash
# Run with auto-reload
uvicorn backend.main:app --reload --port 8000

# Run tests with coverage
pytest tests/ -v --cov=backend --cov-report=html

# Frontend with HMR
cd frontend && npm run dev

# Type check frontend
cd frontend && npm run build  # TypeScript compilation check
```

---

## Citation

If using this code for research:

```
Non-Invasive Continuous Health Monitor with Federated Learning:
Quality-Aware Personalized Federated Learning for Multimodal Wearable Health Monitoring.
Final Year Engineering Research Prototype, 2026.
```

---

## License

Research Prototype — Not for Clinical Use

This software is provided for academic research and educational purposes only.
