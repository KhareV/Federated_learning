# Canonical Label Schema

## Objective
Establish a single, canonical binary classification target for the P1 Model (MODEL_V1).

## Canonical Classes and Output States

| Class | Integer | Description |
|-------|---------|-------------|
| **NORMAL_MONITORED_PATTERN** | `0` | Normal monitored pattern under the documented dataset mapping. |
| **POTENTIALLY_ABNORMAL** | `1` | Pattern mapped as abnormal by the pre-registered dataset rules. |
| **UNRELIABLE_SIGNAL** | `null` | Signal quality is insufficient for a trustworthy monitored-pattern output. |

`UNRELIABLE_SIGNAL` is an inference/state outcome, not a third supervised
physiology class. It must not be silently converted to class `1`.

## Dataset Mappings

### PTB-XL
PTB-XL provides diagnostic statements mapped to 5 "superclasses". We map these superclasses to the canonical binary label.

| PTB-XL Superclass | Meaning | Canonical Label |
|-------------------|---------|-----------------|
| `NORM` | Normal ECG | **NORMAL_MONITORED_PATTERN** |
| `MI` | Myocardial Infarction | **POTENTIALLY_ABNORMAL** |
| `STTC` | ST/T Change | **POTENTIALLY_ABNORMAL** |
| `CD` | Conduction Disturbance | **POTENTIALLY_ABNORMAL** |
| `HYP` | Hypertrophy | **POTENTIALLY_ABNORMAL** |

### MIT-BIH Arrhythmia
MIT-BIH provides beat-level annotations. A 10-second window is labeled based on the **majority vote** of the valid beats within that window. 

| MIT-BIH Symbol (Subset) | Meaning | Canonical Label |
|-------------------------|---------|-----------------|
| `N` | Normal beat | **NORMAL_MONITORED_PATTERN** |
| `V`, `E`, `F` | Ventricular ectopic beats | **POTENTIALLY_ABNORMAL** |
| `A`, `a`, `J`, `S` | Supraventricular ectopic | **POTENTIALLY_ABNORMAL** |
| `L`, `R`, `B` | Bundle branch blocks | **POTENTIALLY_ABNORMAL** |
| `/`, `~`, `+`, `Q`, `?` | Paced, artifact, rhythm change | *EXCLUDED* |

*Note: Windows containing only EXCLUDED beats, or an exact tie between
`NORMAL_MONITORED_PATTERN`/`POTENTIALLY_ABNORMAL`, are dropped from the
evaluation set.*

## Why Binary?
- **Research focus:** The primary goal is centralized software validation and
  data-quality evaluation, not advancing multi-class taxonomy.
- **Hardware constraint:** Wearables (AD8232) are often single-lead (Lead I), which limits the ability to distinguish complex multi-class pathologies that typically require 12-lead setups (like PTB-XL). Binary "Normal vs. Abnormal" is realistic for a single-lead wearable.
