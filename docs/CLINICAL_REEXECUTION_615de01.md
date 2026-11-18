# Clinical reexecution of 615de01 and additional prediction evaluation

The original seven-notebook workflow was reexecuted sequentially with fresh repository Python kernels from 2026-11-18T10:13:14.208427+00:00 to 2026-11-18T10:42:31.884642+00:00 (UTC). Notebook 04c was then separately executed under its ward-confirmed protocol amendment. All eight notebooks / 93 code cells completed with zero runtime error outputs and were saved locally. Git strips outputs/counts; public evidence consists of model-level aggregates.

| Notebook | Code cells | Runtime errors | Seconds |
| --- | --- | --- | --- |
| 00_setup.ipynb | 5/5 | 0 | 4.21 |
| 01_cohort.ipynb | 17/17 | 0 | 402.27 |
| 02_exposure.ipynb | 10/10 | 0 | 159.21 |
| 03a_validate_input_tables.ipynb | 5/5 | 0 | 132.80 |
| 03b_describe_analysis_dataset.ipynb | 12/12 | 0 | 126.58 |
| 04a_unadjusted_outcomes.ipynb | 12/12 | 0 | 110.82 |
| 04b_multivariable_outcomes.ipynb | 24/24 | 0 | 820.88 |
| 04c_prediction_time_evaluation.ipynb | 8/8 | 0 | 129.36 |

## Original analysis preserved

Original notebook semantic sources, six original SQL files and Firth/patient helpers match baseline `615de01`. All tracked original aggregate CSVs except separated MLE diagnostics match the baseline numerically (within 1e-7 absolute / 1e-6 relative tolerance, including text/category columns). Main estimates and patient-cluster uncertainty are preserved: 460,786 admissions / 2,326 deaths overall, corrected 24h cohort 342,519 / 1,769, and patient-disjoint retrospective ROC AUC 0.860635 / PR AUC 0.117607. The legacy unordered-row split and reference 200-draw admission bootstrap can vary with retrieval order; their rerun values are recorded in the receipt. Its reference plot was regenerated and both asset copies synchronized.

Runtime completion does not resolve separation: the primary and four unpenalized MLE fits remain nonconverged audit outputs, with unstable nuisance coefficients. All five Firth point fits passed their numerical checks. Each patient-cluster Firth fit set and the risk bootstrap accepted 500/500 draws. All 200 reference admission-bootstrap fits completed.

## Connected BigQuery verification

The unchanged construction notebooks rebuilt the five authorized tables. The separate rebuild helper passed a connected dry run (921,440,830 bytes) without execute mode; the aggregate validation checklist also ran. The actual 25-column analysis schema retains admission/discharge/death DATETIME fields and the INTEGER mortality flag. Unique admissions, no missing identifiers, consistent exposure flags and zero ICU matches were confirmed. The dataset still uses 60-day expiry; billing was not changed.

| Table | Rows | Expiration UTC |
| --- | --- | --- |
| base_admissions | 546,028 | 2027-01-17T10:13:24.573000+00:00 |
| base_admissions_racegrp | 546,028 | 2027-01-17T10:15:36.572000+00:00 |
| nonicu_admissions | 460,786 | 2027-01-17T10:17:51.975000+00:00 |
| exposure_raas_early | 460,786 | 2027-01-17T10:20:05.828000+00:00 |
| analysis_dataset | 460,786 | 2027-01-17T10:20:36.400000+00:00 |

The independent connected landmark SQL matches 342,519 admissions / 1,769 deaths. New prediction queries are read-only, dry-run first and capped at 10 GiB/query; they do not create or alter analysis tables. Prediction-time cohorts, location checks, fit status, calibration and chronology sensitivity are documented in [prediction validation](PREDICTION_TIME_VALIDATION.md).

## Preservation and presentation

The clean baseline working tree was recorded before execution. The 23 pre-existing private historical artifacts retain identical bytes and update times; SAS was not run or restored to public scope. No raw rows or credentials are exported. The historical 8063e91 JSON receipt remains unchanged. Its [execution note](PYTHON_WORKFLOW_VALIDATION.md) now links to this later record.

Quarto generation, resource/aggregate consistency checks, deployment and live visual inspection are distinct release checks. A public HTTPS visual inspection of baseline 615de01 confirmed the relevant inference/discrimination/risk sections; the prior file:// restriction was not bypassed. Release status for the updated page must be confirmed after publication.

Machine-readable evidence: `python/outputs/clinical_reexecution_615de01.json` and `prediction_time_execution.json`. No prospective/external clinical validation is claimed.
