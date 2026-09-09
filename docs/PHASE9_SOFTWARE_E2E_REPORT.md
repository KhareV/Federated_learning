# Phase 9 — Software-Only End-to-End Validation

## Delivered

- `scripts/run_demo.py` now runs a deterministic centralized replay through
  session creation, the locked streaming engine, `/inference` persistence,
  prediction history, and session closure.
- The replay uses the committed `MODEL_V1`, frozen preprocessing, and Phase 4
  temperature scaling artifacts. It does not require authentication, hardware,
  federated learning, or a separately running server.
- The WebSocket live route now keeps connections open, sends a deterministic
  connection envelope, and cleans up disconnected clients through the shared
  connection manager.
- Docker's backend health check now targets the real `/system/health` route.

## Verification

```text
python3 scripts/run_demo.py --duration-seconds 10 --seed 91
```

Result: `MODEL_V1`, one 10-second window, one persisted prediction, zero
false alarms, and a clean session close.

```text
python3 -m pytest -q
```

Result: **100 passed**. Phase 9 also includes explicit WebSocket handshake and
replay determinism tests. Frontend verification from `frontend/` remains green:
Svelte check reports 0 errors and the production build succeeds.

Docker/browser checks remain environment-dependent smoke checks; the API,
WebSocket, frontend build, and deterministic software path are validated
without claiming hardware or federated operation.
