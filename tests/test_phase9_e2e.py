import pytest
from fastapi.testclient import TestClient

from backend.main import app


def test_websocket_live_handshake_and_disconnect():
	with TestClient(app) as client:
		with client.websocket_connect("/ws/live/phase9-client") as websocket:
			assert websocket.receive_json() == {"type": "connected", "client_id": "phase9-client", "source": "LIVE"}


def test_stream_chunk_persists_and_broadcasts_inference():
	from preprocessing.ecg import synthesize_ecg_segment

	with TestClient(app) as client:
		session = client.post("/monitoring/sessions/start", json={"subject_id": "stream-subject", "device_id": "replay"}).json()
		with client.websocket_connect("/ws/live/stream-client") as websocket:
			assert websocket.receive_json()["type"] == "connected"
			response = client.post(f"/monitoring/sessions/{session['session_id']}/chunks", json={"samples": synthesize_ecg_segment(2500, seed=19).tolist(), "sampling_rate": 250, "source": "REPLAY"})
			assert response.status_code == 202
			assert len(response.json()["emitted_inferences"]) == 1
			message = websocket.receive_json()
			assert message["type"] == "inference"
			assert message["session_id"] == session["session_id"]
			history = client.get(f"/monitoring/sessions/{session['session_id']}/predictions")
			assert len(history.json()) == 1


@pytest.mark.asyncio
async def test_replay_script_is_deterministic():
	from scripts.run_demo import run

	first = await run(10, 91)
	second = await run(10, 91)
	assert first["model_version"] == "MODEL_V1"
	assert first["windows"] == second["windows"] == 1
	assert first["persisted_predictions"] == second["persisted_predictions"] == 1
