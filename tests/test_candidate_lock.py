import json

from scripts.lock_candidate import digest


def test_model_v2_candidate_lock_matches_artifacts():
    lock = json.load(open("artifacts/MODEL_V2_RESEARCH_CANDIDATE/LOCK_MANIFEST.json"))
    for item in lock["artifacts"].values():
        assert digest(__import__("pathlib").Path(item["path"])) == item["sha256"]
