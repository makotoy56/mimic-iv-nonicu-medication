# BigQuery/Python execution validation: baseline 8063e91

**Later authorized work:** [Current real-data reexecution and added prediction-time evaluation](CLINICAL_REEXECUTION_615de01.md) supersedes the outstanding connected-run gaps. This historical note and its original receipt retain their original scope.

This is the historical full-execution record for audit baseline `8063e91`. Subsequent [offline audit corrections](AUDIT_CORRECTIONS_20261118.md) changed source labels and interpretation without rerunning clinical models. The original JSON receipt and its source hashes are preserved as evidence of that executed snapshot, not a receipt for the edited source.

Executed from 2026-11-18T06:40:55.673645+00:00 to 2026-11-18T07:12:37.048956+00:00 (UTC).

All seven current public notebooks were executed sequentially from top to bottom with a fresh repository Python kernel for each. All 85 code cells completed with zero runtime error outputs. Local notebooks retain saved outputs; Git strips outputs and execution counts before publication. This record covers BigQuery and Python only.

| Notebook | Completed code cells | Runtime errors | Seconds |
| --- | ---: | ---: | ---: |
| `00_setup.ipynb` | 5/5 | 0 | 4.5 |
| `01_cohort.ipynb` | 17/17 | 0 | 377.2 |
| `02_exposure.ipynb` | 10/10 | 0 | 169.1 |
| `03a_validate_input_tables.ipynb` | 5/5 | 0 | 139.5 |
| `03b_describe_analysis_dataset.ipynb` | 12/12 | 0 | 146.9 |
| `04a_unadjusted_outcomes.ipynb` | 12/12 | 0 | 123.7 |
| `04b_multivariable_outcomes.ipynb` | 24/24 | 0 | 939.6 |

## Source reconstruction and schema

The unchanged SQL rebuilt five derived tables from authorized MIMIC-IV v3.1 sources. Dataset default expiration remains 60 days in the free sandbox; billing settings were not changed. This is reconstruction from source, not restoration of an old snapshot.

| Table | Rows | Current expiration (UTC) |
| --- | ---: | --- |
| `base_admissions` | 546,028 | 2027-01-17T06:41:05.889000+00:00 |
| `base_admissions_racegrp` | 546,028 | 2027-01-17T06:43:11.209000+00:00 |
| `nonicu_admissions` | 460,786 | 2027-01-17T06:45:16.477000+00:00 |
| `exposure_raas_early` | 460,786 | 2027-01-17T06:47:22.843000+00:00 |
| `analysis_dataset` | 460,786 | 2027-01-17T06:47:55.229000+00:00 |

The actual analysis schema retains `admittime`, `dischtime`, `deathtime` (DATETIME) and `hospital_expire_flag` (INTEGER). Aggregate checks confirm 460,786 unique admissions from 191,775 patients, no missing patient/admission identifiers, consistent exposure flags and zero ICU matches. No patient rows or identifiers are included in this evidence.

## Boundary and regression checks

The existing landmark, Firth and patient-validation tests passed. They cover 18 boundary/cohort cases, invalid time/schema handling, synthetic ordinary/proxy refits, analytic Firth examples, frequency compression, patient sampling weights, train/test patient separation, weighted risk refitting, absent categories and same-objective numerical recovery. Publication tests confirmed idempotent figure synchronization and rejection of missing resources, broken links and path traversal. These computational tests are distinct from clinical validity.

## Statistical status

Runtime completion is separate from convergence. The original unpenalized primary and four sensitivity models remain separated/nonconverged diagnostics; nominal confidence intervals and p-values are not validated inference. All five supplementary Firth point fits passed convergence, rank/profile and independent adjusted-score checks. All five sets of patient-cluster Firth refits and the risk-model bootstrap met the prespecified 95% successful-draw threshold. Actual accepted/recovered/failed counts remain in the current aggregate CSVs and machine-readable receipt.

The corrected 24-hour cohort contains 342,519 admissions and 1,769 deaths. The landmark definition, exposure timing, entire-stay ICU exclusion and adjustment variables are unchanged. The patient-disjoint holdout has zero patient overlap. The unweighted risk model returned AME -0.379727 percentage points.

The historical unordered admission split returned ROC AUC 0.859852 and PR AUC 0.116565. These reference metrics depend on retrieval order; the current patient-disjoint evaluation uses deterministic patient/admission ordering. The rounded values are 0.8599/0.1166; they are not the patient-disjoint metrics. These are retrospective discrimination checks without a fixed prediction time. Different case mixes do not establish improved prediction. All 200/200 reference admission-bootstrap refits completed.

The optional BigQuery Storage reader is absent; the client successfully used the REST endpoint. This informational warning does not indicate a failed query. Statistical nonconvergence above remains a separate limitation.

## Publication and preservation

[Machine-readable receipt and notebook source hashes](https://github.com/makotoy56/mimic-iv-nonicu-medication/blob/main/python/outputs/python_workflow_execution.json) record only execution metadata, table metadata and model-level aggregates. SQL and analysis helpers were unchanged; notebook code changes were limited to two current aggregate export filenames. Historical comparison assets and evidence were preserved locally with identical bytes and update times, and excluded from current public tracking. No external analysis-service upload or historical comparison execution was performed. Existing Git history was not rewritten.

Current Python exports include `unadjusted_outcomes.csv` and `mle_diagnostics.csv`; the latter is explicitly nonconverged diagnostic output. Prior interchange files are not inputs to this workflow. [Public scope and limits](REPRODUCIBLE_SCOPE.md) · [Patient-aware uncertainty and holdout](PATIENT_AWARE_VALIDATION.md).

Quarto is regenerated from the current source and aggregate figures. Local consistency/resource checks and post-deployment live checks are recorded separately from notebook execution.
