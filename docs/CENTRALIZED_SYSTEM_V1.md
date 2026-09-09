# CENTRALIZED_SYSTEM_V1

This is the locked centralized software-only milestone. The authoritative
artifact inventory and SHA-256 checksums are in
`artifacts/CENTRALIZED_SYSTEM_V1/LOCK_MANIFEST.json`.

The release includes the frozen contracts, registered dataset manifests,
patient-level PTB-XL splits, train-only preprocessing statistics, ECG
`MODEL_V1`, calibration and threshold, streaming inference, backend API,
SvelteKit frontend, and phase evidence reports.

Reproducibility starts with:

```text
python3 -m pytest -q
python3 scripts/run_demo.py --duration-seconds 10 --seed 91
cd frontend && npm run check && npm run build
```

The canonical output is `NORMAL_MONITORED_PATTERN`,
`POTENTIALLY_ABNORMAL`, or `UNRELIABLE_SIGNAL`. It is not a diagnosis and
must not be presented as one. Multimodal supervised improvement is not claimed
because the supplied BIDMC data does not provide compatible labels.

Hardware integration, wearable-domain validation, federated learning, secure
aggregation, differential privacy, edge optimization, and QAPFL claims are
explicitly deferred and are not dependencies of this lock.
