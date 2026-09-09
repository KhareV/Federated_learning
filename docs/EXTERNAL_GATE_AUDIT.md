# External Gate Audit — Current MODEL_V1

The release gate for a centralized ECG candidate is AUROC >= 0.80,
sensitivity >= 0.70, and specificity >= 0.70 on MIT-BIH. MIT-BIH is
evaluation-only and is never used to tune the threshold or architecture.

The first audit corrected a contract defect: exact ties in MIT-BIH's
10-second majority-beat windows were previously labelled normal. Ties and
excluded-only windows are now omitted, as required by `LABEL_SCHEMA.md`.

With the corrected protocol, the existing PTB-XL-trained `MODEL_V1` evaluated
on 16,302 MIT-BIH windows has AUROC 0.7404, sensitivity 1.0000, and specificity
0.0710. It therefore **fails** the external gate and is not a releasable
centralized model.

This result also confirms a comparability limitation: PTB-XL diagnostic
superclasses and MIT-BIH beat/rhythm annotations are distinct sources of
ground truth. The next candidate must be developed using PTB-XL only and
evaluated once against the frozen MIT-BIH protocol; it must not be selected by
tuning to MIT-BIH.
