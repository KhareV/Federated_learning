# P1 Label Schema

## Objective
Establish a single, canonical binary classification target for the P1 Model (MODEL_V1).

## Canonical Classes

| Class | Integer | Description |
|-------|---------|-------------|
| **NORMAL** | `0` | Normal sinus rhythm, healthy control, or beats classified as 'N' (Normal). |
| **ABNORMAL** | `1` | Any pathological condition, arrhythmia, myocardial infarction, bundle branch block, or ectopic beat. |

## Dataset Mappings

### PTB-XL
PTB-XL provides diagnostic statements mapped to 5 "superclasses". We map these superclasses to the canonical binary label.

| PTB-XL Superclass | Meaning | Canonical Label |
|-------------------|---------|-----------------|
| `NORM` | Normal ECG | **NORMAL** |
| `MI` | Myocardial Infarction | **ABNORMAL** |
| `STTC` | ST/T Change | **ABNORMAL** |
| `CD` | Conduction Disturbance | **ABNORMAL** |
| `HYP` | Hypertrophy | **ABNORMAL** |

### MIT-BIH Arrhythmia
MIT-BIH provides beat-level annotations. A 10-second window is labeled based on the **majority vote** of the valid beats within that window. 

| MIT-BIH Symbol (Subset) | Meaning | Canonical Label |
|-------------------------|---------|-----------------|
| `N` | Normal beat | **NORMAL** |
| `V`, `E`, `F` | Ventricular ectopic beats | **ABNORMAL** |
| `A`, `a`, `J`, `S` | Supraventricular ectopic | **ABNORMAL** |
| `L`, `R`, `B` | Bundle branch blocks | **ABNORMAL** |
| `/`, `~`, `+`, `Q`, `?` | Paced, artifact, rhythm change | *EXCLUDED* |

*Note: Windows containing only EXCLUDED beats, or an exact tie between NORMAL/ABNORMAL, are dropped from the evaluation set.*

## Why Binary?
- **Research focus:** The primary goal of P3 is federated learning and data quality evaluation, not advancing multi-class taxonomy.
- **Hardware constraint:** Wearables (AD8232) are often single-lead (Lead I), which limits the ability to distinguish complex multi-class pathologies that typically require 12-lead setups (like PTB-XL). Binary "Normal vs. Abnormal" is realistic for a single-lead wearable.
