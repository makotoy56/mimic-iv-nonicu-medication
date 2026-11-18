# Reproducible portfolio scope

The current portfolio covers BigQuery SQL and Python notebooks 00–04b. Reproduction requires authorized MIMIC-IV v3.1 access, source retrieval, cohort construction, model execution and result checks; rendering an existing report alone does not establish analysis reproduction.

| Step | Implementation | Evidence and limits |
| --- | --- | --- |
| Source access and construction | Notebook 00; notebooks 01–02 and `sql/` | Five derived BigQuery tables; each reproducer needs their own access. The free sandbox retains 60-day expiration. |
| Input and cohort checks | Notebooks 03a–03b | Admission counts, uniqueness, missingness and aggregate descriptions; no patient rows are published. |
| Outcome analysis | Notebooks 04a–04b | Current aggregate exports and figures; unpenalized MLE separation/nonconvergence remains explicit. |
| Supplementary inference | Firth and patient-validation Python helpers | Numerical checks and 500 patient-cluster draws; not independent clinical or causal validation. |
| Prediction evaluation | Patient-disjoint holdout in 04b | Train-only preprocessing and zero patient overlap; a single internal split is not external validation. |
| Report generation | Quarto and publication checks | Rebuilds the report and checks resources; distinct from model execution. |

SAS programs, exports, comparison notebook and historical comparison evidence are outside the current public workflow. They are retained unchanged in local storage and excluded from current Git tracking. SAS was not executed. Existing Git history is not rewritten; older commits may still contain previously public files.

The admission-to-<24-hour prescription definition, entire-admission ICU exclusion, 24-hour landmark eligibility, adjustment variables, Firth method, patient-cluster uncertainty and patient-disjoint evaluation are unchanged by this publication-scope update. Historical nonconverged OR figures are kept locally and excluded from the current public presentation.

[Current execution record](PYTHON_WORKFLOW_VALIDATION.md) · [Environment and reproduction](../REPRODUCIBILITY.md) · [Patient-aware methods](PATIENT_AWARE_VALIDATION.md)
