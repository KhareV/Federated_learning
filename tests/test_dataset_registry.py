from pathlib import Path

from datasets.registry import inspect_dataset, load_registry


def test_registry_points_to_canonical_dataset_roots():
    root = Path(__file__).resolve().parents[1]
    registry = load_registry(project_root=root)
    assert registry["ptbxl"].root == (root / "data/raw/ptbxl").resolve()
    assert registry["mitbih"].root == (root / "data/raw/mitbih").resolve()
    assert registry["mitbih_noise_stress"].root == (root / "data/raw/mitbih_noise_stress").resolve()
    assert registry["bidmc"].root == (root / "data/raw/bidmc").resolve()


def test_supplied_datasets_have_valid_inventory():
    root = Path(__file__).resolve().parents[1]
    registry = load_registry(project_root=root)
    for name in ("ptbxl", "mitbih", "mitbih_noise_stress", "bidmc"):
        report = inspect_dataset(registry[name])
        assert report["status"] == "valid", report["errors"]

