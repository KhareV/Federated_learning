# Deferred Components

The following source trees are retained as future-work scaffolding only. They
are not imported by `backend.main`, exposed by the active API, linked from the
active monitor navigation, or evidence for the centralized release:

- `backend/federated/` and `backend/services/fl_service.py`: federated learning,
  privacy, and client orchestration.
- `backend/ml/personalization/`: personal baseline research.
- `backend/ml/models/`: legacy anomaly-model abstractions.
- `backend/experiments/`: legacy experiment placeholders.
- `backend/simulator/`: synthetic signal generation for tests and demos.
- legacy API modules for alerts, devices, experiments, baselines, signals, and
  federated status.

The active centralized surface is deliberately restricted to the routers
imported by `backend.main`: system health/model status, monitoring sessions and
chunks, central inference, evidence reports, and WebSocket broadcast.

Deferred modules must not be imported into an active router or presented as a
working feature until they have an implementation, contract tests, real-data
evidence, and an updated scope decision.
