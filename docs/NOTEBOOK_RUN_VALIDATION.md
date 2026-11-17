# Complete notebook execution validation

Executed from 2026-11-17T15:57:44.899157+00:00 to 2026-11-17T16:29:41.738430+00:00 (UTC).

All eight notebooks were executed sequentially, top-to-bottom, using a new repository Python 3.12.13 kernel for each notebook. All 100 code cells completed with zero runtime error outputs. Local notebooks were saved with their outputs; Git retains the existing output-stripping policy. The JSON receipt records source hashes and actual model/validation status.

| Notebook | Completed code cells | Runtime errors | Seconds |
| --- | ---: | ---: | ---: |
| `00_setup.ipynb` | 5/5 | 0 | 4.0 |
| `01_cohort.ipynb` | 17/17 | 0 | 417.9 |
| `02_exposure.ipynb` | 10/10 | 0 | 173.6 |
| `03a_validate_input_tables.ipynb` | 5/5 | 0 | 135.2 |
| `03b_describe_analysis_dataset.ipynb` | 12/12 | 0 | 138.1 |
| `04a_unadjusted_outcomes.ipynb` | 12/12 | 0 | 122.9 |
| `04b_multivariable_outcomes.ipynb` | 24/24 | 0 | 922.4 |
| `05_sas_python_validation.ipynb` | 15/15 | 0 | 1.8 |

## Rebuilt tables and source integrity

Notebook 01 rebuilt the three cohort tables; notebook 02 rebuilt the exposure and analysis tables using the unchanged SQL. The sandbox dataset default remains 60 days and billing was not changed. These are reconstructions from source, not a frozen historical snapshot.

| Table | Rows | Current expiration (UTC) |
| --- | ---: | --- |
| `base_admissions` | 546,028 | 2027-01-16T15:57:54.766000+00:00 |
| `base_admissions_racegrp` | 546,028 | 2027-01-16T16:00:07.591000+00:00 |
| `nonicu_admissions` | 460,786 | 2027-01-16T16:02:35.107000+00:00 |
| `exposure_raas_early` | 460,786 | 2027-01-16T16:04:52.978000+00:00 |
| `analysis_dataset` | 460,786 | 2027-01-16T16:05:25.421000+00:00 |

The analysis table retains `admittime`, `dischtime`, `deathtime` (DATETIME) and `hospital_expire_flag` (INTEGER). Aggregate checks confirmed 460,786 unique admissions from 191,775 patients, no missing admission/patient identifiers, consistent exposure flags and zero ICU matches. The exposure remains prescription start at 0–<24 hours; ICU use is excluded over the entire admission. Adjustment variables were unchanged.

## Numerical and statistical status

Runtime completion is separate from statistical convergence. The historical unpenalized primary and four sensitivity MLE fits remain separated/nonconverged diagnostic outputs. Their nominal intervals and p-values are not validated inference. All five supplementary Firth fits passed convergence, rank/profile and independent adjusted-score checks. Patient-cluster refits and the patient-disjoint holdout were rerun in this complete notebook execution.

The historical admission-row split returned ROC AUC 0.852419 and PR AUC 0.104964 on this run. It depends on BigQuery row order. The patient-disjoint validation is sorted deterministically; different case mixes do not demonstrate improved model performance.

The unweighted risk model returned AME -0.379727 percentage points. All 200/200 admission-bootstrap refits completed. Patient-cluster success counts and current OR/risk intervals are in [patient-aware validation](PATIENT_AWARE_VALIDATION.md) and the aggregate CSVs.

Notebook 05 reran comparisons against existing SAS-generated aggregate CSVs; it did not launch SAS. Unadjusted summaries matched. Flagged logistic comparisons were limited to the already documented separated intercept/admission-type terms. There were no unexpected term failures.

## Saved artifacts and publication

[Machine-readable execution receipt and source hashes](https://github.com/makotoy56/mimic-iv-nonicu-medication/blob/main/python/outputs/notebook_execution_validation.json) contain notebook-level execution/source checks, table metadata and model-level aggregates only. Existing local working changes were backed up before generated outputs were overwritten. No patient rows, identifiers or credentials were added to Git.

Canonical notebook figures are synchronized to `docs/assets/`. The Quarto report is rendered again, and aggregate-consistency/local-resource checks run before publication. After deployment, live checks compare HTML bytes and fetch every same-site linked resource.

Notebook stderr recorded the optional BigQuery Storage-module warning; reads used the REST fallback and completed successfully. Statistical convergence warnings are accounted for separately above. No authentication, billing or API-enablement settings were changed.
