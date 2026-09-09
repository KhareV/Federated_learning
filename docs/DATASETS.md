# NHM Dataset Inventory

The supplied raw datasets are kept immutable under `data/raw/` and are not
part of source control.

| Dataset | Directory | Version | Role |
|---|---|---:|---|
| PTB-XL | `data/raw/ptbxl` | 1.0.1 | Centralized ECG development |
| MIT-BIH Arrhythmia | `data/raw/mitbih` | 1.0.0 | External ECG validation |
| MIT-BIH Noise Stress Test | `data/raw/mitbih_noise_stress` | 1.0.0 | ECG noise robustness |
| BIDMC PPG and Respiration | `data/raw/bidmc` | 1.0.0 | Multimodal alignment and quality |

Run the read-only structural validation with:

```bash
python scripts/validate_datasets.py
```

The command writes a small inventory to
`data/manifests/dataset_inventory.json`. It verifies PTB-XL metadata/WFDB
parity, complete MIT-BIH annotation pairs, configured noise SNR coverage, and
BIDMC WFDB/CSV availability. It does not alter any raw file.

Raw data is deliberately excluded from Git. Keep dataset licenses and source
identifiers alongside any published experiment manifest.

