"""Run the deterministic centralized software-only replay."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from backend.db.database import create_all_tables
from backend.main import app
from preprocessing.ecg import synthesize_ecg_segment


async def run(duration_seconds: int, seed: int) -> dict:
	await create_all_tables()
	async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://demo") as client:
		response = await client.post("/monitoring/sessions/start", json={"subject_id": "replay-subject", "device_id": "software-replay"})
		response.raise_for_status()
		session_id = response.json()["session_id"]
		samples = synthesize_ecg_segment(duration_seconds * 250, seed=seed)
		records = []
		for start in range(0, len(samples), 625):
			chunk = await client.post(f"/monitoring/sessions/{session_id}/chunks", json={"samples": samples[start:start + 625].tolist(), "sampling_rate": 250, "source": "REPLAY"})
			chunk.raise_for_status()
			records.extend(chunk.json()["emitted_inferences"])
		await client.put(f"/monitoring/sessions/{session_id}/stop")
		history = await client.get(f"/monitoring/sessions/{session_id}/predictions")
		history.raise_for_status()
		return {"session_id": session_id, "model_version": records[0]["model_version"] if records else None, "windows": len(records), "persisted_predictions": len(history.json())}


def main() -> None:
	parser = argparse.ArgumentParser(description="Run the centralized deterministic replay")
	parser.add_argument("--duration-seconds", type=int, default=30)
	parser.add_argument("--seed", type=int, default=2025)
	args = parser.parse_args()
	if args.duration_seconds < 10:
		parser.error("--duration-seconds must be at least 10")
	print(json.dumps(asyncio.run(run(args.duration_seconds, args.seed)), indent=2))


if __name__ == "__main__":
	main()
