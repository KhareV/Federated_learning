# NHM ML System Specification

## Objective

Build a reproducible centralized research system for non-invasive physiological
monitoring. Outputs signal a monitored physiological pattern and are not
clinical diagnoses.

## Primary task

Binary ECG rhythm/abnormality classification with an explicit unusable-signal
state at inference time.

## Modalities and roles

ECG is the primary supervised modality. PPG, HR, and SpO₂ provide contextual
and multimodal information. PTB-XL trains the ECG reference model, MIT-BIH is
external evaluation, Noise Stress Test measures robustness, and BIDMC supports
aligned multimodal development and quality analysis.

## Canonical processing

All sources enter the same versioned schema and processing contracts. ECG is
resampled to 250 Hz, filtered, normalized using training-only statistics,
windowed to 10 seconds with 5-second stride, quality-assessed, and passed to
the model.

## Centralized milestone

The milestone ends at `CENTRALIZED_SYSTEM_V1`: locked models, calibration,
threshold, inference service, backend API/database, SvelteKit frontend, replay
demo, tests, and evidence reports. Hardware and federated training are later
consumers of this locked interface.

