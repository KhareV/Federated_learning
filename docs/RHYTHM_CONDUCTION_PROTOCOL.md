# Rhythm/Conduction External-Validation Protocol

This is a new, separately versioned supervised task. It does not amend or
retroactively reinterpret the broad-diagnostic candidates MODEL_V1–V3.

## PTB-XL development labels

- `NORMAL`: `NORM` has positive confidence and no positive rhythm/conduction
  statement.
- `ABNORMAL`: at least one positive statement among PVC, PAC, premature
  complexes, AFIB, atrial flutter, supraventricular arrhythmia/tachycardia,
  sinus rate/rhythm abnormalities, bigeminy/trigeminy, AV block, bundle-branch
  block, fascicular block, IVCD, or WPW.
- Excluded: records that match neither condition, including MI, ST-T, and
  hypertrophy-only records. A zero-confidence SCP code is not present.

## External role

MIT-BIH remains evaluation-only. Its pre-existing majority-vote window rule,
lead, quality gate, calibration procedure, threshold lock, and AUROC /
sensitivity / specificity release gate remain unchanged. No MIT-BIH metric is
used to choose an architecture, threshold, or label rule.

The target is justified from source label semantics before training: both
datasets now represent rhythm/conduction phenomena rather than broad PTB-XL
diagnostic superclasses versus beat annotations.
