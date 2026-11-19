# Connected clinical reexecution (2026-11-19)

All eight current notebooks (00–04c) were executed sequentially with fresh repository Python 3.12.13 kernels from 2026-11-19T09:25:32.965978+00:00 to 2026-11-19T09:56:32.577499+00:00 (UTC). **109/109 code cells completed with zero runtime error outputs**, and the executed notebooks were saved on the SSD. Normal execution used real authorized BigQuery inputs; it did not substitute synthetic/demo data or saved results.

The starting main was `859bca4070072cb5c74090c32e3325d530b7e4c0` with the pending real-data access guards. The machine-readable receipt records each executed notebook's semantic source hash and the SQL/helper hashes, so this run does not incorrectly attribute the uncommitted guards to the starting commit. No cohort, exposure, covariate, estimator or interval rule was changed during the run.

| Notebook | Code cells | Runtime errors | Seconds |
| --- | --- | --- | --- |
| 00_setup.ipynb | 7/7 | 0 | 4.08 |
| 01_cohort.ipynb | 19/19 | 0 | 379.15 |
| 02_exposure.ipynb | 12/12 | 0 | 163.19 |
| 03a_validate_input_tables.ipynb | 7/7 | 0 | 130.26 |
| 03b_describe_analysis_dataset.ipynb | 14/14 | 0 | 124.29 |
| 04a_unadjusted_outcomes.ipynb | 14/14 | 0 | 109.34 |
| 04b_multivariable_outcomes.ipynb | 26/26 | 0 | 825.92 |
| 04c_prediction_time_evaluation.ipynb | 10/10 | 0 | 122.38 |

## Reproduced results and numerical limits

The main cohort remains **460,786 admissions / 191,775 patients / 2,326 deaths**. The corrected 24-hour association cohort remains **342,519 admissions / 1,769 deaths**. All 14 non-MLE aggregate CSVs agree with the pre-run exports within 1e-7 absolute / 1e-6 relative tolerance, including text/category columns. The two separated-MLE diagnostic exports are compared and retained but are excluded from this stable-estimate claim. Runtime completion does not establish statistical convergence: all five unpenalized MLE fits remain nonconverged audit outputs. All five Firth point fits passed their numerical checks; their patient-cluster bootstrap sets and the risk bootstrap each accepted 500/500 draws. The reference admission-row bootstrap completed 200/200 draws; its plot and unordered-row comparator may vary with retrieval order.

| Firth model | Admissions / deaths | OR | Patient-cluster 95% interval |
| --- | --- | --- | --- |
| Primary cohort | 460,786 / 2,326 | 0.318889 | 0.266741–0.380005 |
| Original condition | 460,350 / 1,890 | 0.362477 | 0.302618–0.425612 |
| Original condition + proxy | 460,350 / 1,890 | 0.387862 | 0.323408–0.456335 |
| 24h landmark | 342,519 / 1,769 | 0.356387 | 0.292353–0.422734 |
| 24h landmark + proxy | 342,519 / 1,769 | 0.381595 | 0.314534–0.453328 |

The retrospective patient-disjoint holdout remains 92,477 admissions / 468 deaths, with zero patient overlap, ROC AUC 0.860635 and PR AUC/AP 0.117607. It uses the first-day prescription records and is not an admission-time or 24-hour prediction evaluation.

The separate time-anchored branch again produced admission and 24-hour ward-confirmed cohorts of **719** and **336,372** admissions. Their test sets contain **3** and **698** deaths. All three prediction fits converged, with zero patient overlap. Admission intervals remain withheld (467/500 usable draws, below the prespecified 475 threshold); both 24-hour models accepted 500/500 draws. SQL/Python eligible-admission/death counts and native-transfer reconstruction agree. Later ICU transfers remain followed. The existing post-QA chronology sensitivity was also rerun with its unchanged master patient allocation; primary results were not replaced. See [prediction validation](PREDICTION_TIME_VALIDATION.md) and the newly generated aggregate prediction receipts. The historical 29-case BigQuery boundary exercise is not claimed as freshly rerun here.

## Connected BigQuery checks

The normal 00–02 construction steps rebuilt the five authorized tables. Actual metadata confirms the analysis table still has 25 columns, including admission/discharge/death DATETIME fields and the INTEGER mortality flag. Independent aggregate SQL confirmed unique admissions, no missing identifiers, consistent exposure flags, zero entire-stay ICU matches and the corrected 24-hour count. The rebuild helper separately passed its read-only full-pipeline dry run (921,440,830 bytes), and the aggregate validation checklist passed.

| Table | Rows | Columns | Expiration UTC |
| --- | --- | --- | --- |
| base_admissions | 546,028 | 19 | 2027-01-18T09:25:42.529000+00:00 |
| base_admissions_racegrp | 546,028 | 21 | 2027-01-18T09:27:48.782000+00:00 |
| nonicu_admissions | 460,786 | 21 | 2027-01-18T09:29:55.844000+00:00 |
| exposure_raas_early | 460,786 | 6 | 2027-01-18T09:32:01.789000+00:00 |
| analysis_dataset | 460,786 | 25 | 2027-01-18T09:32:33.650000+00:00 |

The dataset retains its 60-day lifetime. Billing, access permissions and existing processing limits were not changed. Prediction reads remain read-only, dry-run first and capped at 10 GiB/query.

## Preservation and release scope

Executed notebook sources match the pre-run backup; fresh numbered displays identify live execution and are generated from the current Python objects. Saved local outputs and sequential execution counts are retained. Git's clean filter removes outputs/counts from public notebook blobs. The 21 pre-existing private historical artifacts retain their sizes and modification times; SAS was neither run nor restored. Historical receipts remain unchanged. Only aggregate exports, curated figures, source code and verification evidence are public; no patient rows, individual scores or credentials are exported.

Clinical execution, offline regression tests, Quarto generation, Git push and live deployment are separate checks. This receipt establishes the connected execution above and the local release checks below; push and live deployment are reported separately. No external/prospective clinical validation is claimed.

Machine-readable evidence: [clinical_reexecution_20261119.json](../python/outputs/clinical_reexecution_20261119.json). Previous [615de01 execution evidence](CLINICAL_REEXECUTION_615de01.md) remains historical.

## Local release checks

All 12 existing offline test scripts passed with network and ADC access blocked, including the new access-failure tests, 24-hour boundaries, Firth/patient validation, prediction-time location/chronology and report checks. Quarto rendered successfully, its post-render check validated 23 local resources, and all 10 tracked canonical/public image pairs agree byte-for-byte. These checks do not replace the connected clinical execution recorded above, and they do not by themselves establish successful GitHub push or Pages deployment.
