# External Gate Audit — Centralized ECG Candidates

The release gate for a centralized ECG candidate is AUROC >= 0.80,
sensitivity >= 0.70, and specificity >= 0.70 on MIT-BIH. MIT-BIH is
evaluation-only and is never used to tune the threshold or architecture.

The first audit corrected a contract defect: exact ties in MIT-BIH's
10-second majority-beat windows were previously labelled normal. Ties and
excluded-only windows are now omitted, as required by `LABEL_SCHEMA.md`.

All reported candidates were trained and selected using PTB-XL only. Their
MIT-BIH evaluations are frozen evidence, not a tuning loop.

| Candidate | PTB-XL test AUROC | MIT-BIH AUROC | MIT-BIH sensitivity | MIT-BIH specificity | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| MODEL_V1 | — | 0.7404 | 1.0000 | 0.0710 | Fail |
| MODEL_V2 | 0.8988 | 0.7614 | 0.9766 | 0.1620 | Fail |
| MODEL_V3 | 0.9038 | 0.7774 | 0.9968 | 0.1263 | Fail |

`MODEL_V3` includes record-level bootstrap intervals: AUROC 0.6427–0.8803,
sensitivity 0.9900–1.0000, and specificity 0.0467–0.2212. It therefore
remains **blocked** and is not a releasable centralized model.

The repeated high-sensitivity/very-low-specificity result confirms a material
comparability limitation: PTB-XL diagnostic superclasses and MIT-BIH
beat/rhythm annotations are distinct sources of ground truth. Further work
must not tune thresholds, architecture, preprocessing, or label rules on
MIT-BIH. A release requires a pre-registered semantically compatible target
and a newly trained PTB-XL-only candidate that clears the same frozen gate.
