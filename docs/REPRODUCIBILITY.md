# NHM Reproducibility

Every run records an experiment ID, git revision, dataset versions, split
version, preprocessing version, model version, random seed, hyperparameters,
and output metrics. Raw data under `data/raw/` is immutable and excluded from
Git. Derived manifests, reports, checkpoints, and calibration artifacts are
versioned separately and never silently overwritten.

The dataset foundation can be verified with:

```bash
python scripts/validate_datasets.py
```

Phase 2 preprocessing verification is covered by:

```bash
python -m pytest -q tests/test_phase2_ecg_contract.py
```

Research preprocessing must fit with `ECGPreprocessor.fit()` on the training
partition, persist the resulting JSON with `save_normalization_stats()`, and
load it for validation, test, and inference with
`ECGPreprocessor.load_normalization_stats()`. Calling `transform()` without
frozen statistics is an error. The legacy `process()` fallback exists only for
existing smoke tests and is not valid for research results.
