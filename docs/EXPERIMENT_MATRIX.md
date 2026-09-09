# NHM Centralized Experiment Matrix

| ID | Experiment | Dataset | Purpose |
|---|---|---|---|
| C01 | Majority baseline | PTB-XL | Trivial control |
| C02 | Logistic Regression | PTB-XL | Handcrafted-feature baseline |
| C03 | Random Forest | PTB-XL | Tree baseline |
| C04 | ECG CNN | PTB-XL | Centralized neural model |
| C05 | Calibrated `MODEL_V1` | PTB-XL | Locked internal evaluation |
| C06 | External validation | MIT-BIH | Dataset transfer |
| C07 | Noise robustness | Noise Stress Test | SNR degradation |
| C08 | PPG/SpO₂ processing | BIDMC | Alignment and quality |
| C09 | Multimodal ablation | Compatible labelled data | Modality contribution |
| C10 | Missing-modality robustness | Multimodal data | Fallback/uncertainty behavior |
| C11 | Streaming evaluation | Deterministic replay | Event-level behavior |

Synthetic data is permitted only for tests, smoke runs, and UI replay where it
is explicitly labelled synthetic.

