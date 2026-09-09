import pytest
from fastapi.testclient import TestClient

from backend.main import app


def test_websocket_live_handshake_and_disconnect():
	with TestClient(app) as client:
		with client.websocket_connect("/ws/live/phase9-client") as websocket:
			assert websocket.receive_json() == {"type": "connected", "client_id": "phase9-client", "source": "LIVE"}


@pytest.mark.asyncio
async def test_replay_script_is_deterministic():
	from scripts.run_demo import run

	first = await run(10, 91)
	second = await run(10, 91)
	assert first["model_version"] == "MODEL_V1"
	assert first["windows"] == second["windows"] == 1
	assert first["stream"] == second["stream"]
	assert first["persisted_predictions"] == second["persisted_predictions"] == 1
