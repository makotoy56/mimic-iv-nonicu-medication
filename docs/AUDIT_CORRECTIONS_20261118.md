# Offline interpretation and source corrections (2026-11-18)

**Later authorized work:** [Current real-data reexecution and added prediction-time evaluation](CLINICAL_REEXECUTION_615de01.md) supersedes the outstanding connected-run gaps. This historical note and its original receipt retain their original scope.

Audit baseline: `8063e9172346b9a6898f8746b1132a0f2d54d9ce`. These corrections use version-controlled source, previously published aggregate CSV/JSON evidence and synthetic data only. No BigQuery connection, patient-data retrieval, clinical model rerun or SAS execution was performed. The revised local Quarto HTML is a presentation rebuild, not a new clinical analysis. Publication/deployment was outside the original offline correction pass. Any subsequently authorized release does not constitute another clinical rerun.

## Retrospective discrimination and landmark association are different analyses

The full-cohort patient-disjoint classifier uses prescription records from 0–<24 hours and includes early hospital deaths. It does not condition on confirmed survival and continued hospitalization at 24 hours. It has no fixed clinical prediction time or prospective prediction horizon. Its ROC AUC **0.860635** and PR AUC **0.117607** describe internal retrospective discrimination, not prognosis available at admission or at 24 hours. Patient disjointness and train-only preprocessing address different problems from temporal feature availability. These scores are also not external validation, calibrated mortality risks or validation of the Firth OR/AME estimators.

The existing 24-hour landmark **association** analyses separately require confirmed survival and continued hospitalization strictly beyond 24 hours and evaluate subsequent in-hospital death. Their 342,519 admissions/1,769 deaths, Firth points/intervals and eligibility rules are unchanged. They do not supply the published classifier holdout metrics.

## Discrimination metric provenance

| Metrics (ROC AUC / PR AUC) | Source and interpretation |
| --- | --- |
| 0.860635 / 0.117607 | `python/outputs/patient_split_validation.csv`, patient-disjoint holdout. Deterministic patient/admission order; 368,309/92,477 train/test admissions; 468 test deaths; zero patient overlap. Current retrospective internal discrimination summary. |
| 0.857576 / 0.106915 | The same CSV, deterministic-order admission-random reference; 42,796 overlapping patients. Not the historical unordered split and not a prediction-time evaluation. |
| 0.859852 / 0.116565 (rounded 0.8599 / 0.1166) | `current_unordered_discrimination` in the preserved `python/outputs/python_workflow_execution.json`, full run from 2026-11-18 06:40:55 to 07:12:37 UTC at baseline 8063e91. Legacy admission-row split, with full-cohort category encoding before splitting; the scaler/classifier are fitted in training data. |
| 0.854487 / 0.115764 | Historical 2026-11-17 initial reconstruction/rerun as reported in `24H_LANDMARK_VALIDATION.md`. Legacy unordered admission-row split. The published note is the available provenance; no exact exported row-partition manifest was established in this offline review. |

The unordered splits depend on retrieval order even with the same random seed. Their exact test row sets cannot be reconstructed from the published aggregates alone. They are historical execution values, not interchangeable estimates of the patient-disjoint evaluation. Differences between holdouts with different case mixes do not establish improved performance.

## Source corrections

- Renamed descriptive `n_patients='count'` outputs to `n_admissions` in 04a/04b; these count admission rows, not unique patients. The 04a CSV continues to export the same `n` column. Changed code-cell outputs/execution counts were cleared; they were not repopulated with historical or synthetic clinical-looking results.
- Added coordinated destination replacement instructions for all six SQL files, seven notebooks, the rebuild helper and optional aggregate checker in [REPRODUCIBILITY.md](../REPRODUCIBILITY.md#replace-the-author-specific-bigquery-destination-before-running). The SQL definitions and operational defaults themselves were not changed.
- Removed claims of simultaneous exposure/administration from both-class prescription-record labels. Both flags can be set by records at different times in the early window; overlapping prescription intervals and actual administration are not required.
- The optional `validation_checklist.py` prevalence query still used the obsolete permissive landmark condition and a hard-coded table. It now follows its configured `TABLES` reference and the existing 04b survival/in-hospital eligibility rule. This changes the auxiliary check, not the analysis cohort/model. It has not been executed against BigQuery in this correction pass.
- README, methods/results/setup notes, notebook explanations and local Quarto output distinguish retrospective discrimination from the 24-hour association analysis. The original execution receipt is unchanged and applies to its executed baseline source hashes, not to the subsequently edited notebooks.

## Offline checks and limits

`scripts/test_audit_corrections.py` covers repeated-patient admission counts, unchanged aggregate export columns, the absence of a hidden 24-hour eligibility filter in the classifier, helper-query/04b agreement on synthetic time-boundary cases, and source destination replacement without contacting Google services. Existing landmark/Firth/patient and report publication/consistency tests are also used. No new clinical estimates or figures are calculated from real data.

The adjusted results, published aggregate CSV/JSON values, exposure window, entire-admission ICU exclusion, main model specification, patient resampling and landmark rules remain unchanged. A new complete clinical Run All and a connected BigQuery dry run/IAM/schema check are **not** claimed by these offline tests. At completion of the offline correction pass, the revised source and HTML were local only; subsequent publication is a separate release step and does not add connected-SQL or clinical-model validation.

## Alternatives requiring new analysis

An admission-time prognostic model would need predictors restricted to information available at admission, excluding future prescription records. A 24-hour prognostic model would need a prespecified time origin, confirmed survival/in-hospital eligibility at that time, a subsequent outcome horizon, and another patient-disjoint evaluation on that eligible cohort (with calibration assessed separately). Either changes the target task or cohort and requires authorized real-data reanalysis; the existing AUC/PR-AUC values cannot be reused as its performance estimates.

Offline validation completed successfully with `test_audit_corrections.py`, `test_landmark_sensitivity.py`, `test_firth_sensitivity.py`, `test_patient_validation.py`, `test_report_publication.py` and `test_report_consistency.py`. Local Quarto rendering passed its 22 resource checks. Source comparison confirmed unchanged SQL, modeling helpers, all aggregate CSV/JSON files and figures; only descriptive count labels and one diagnostic message changed in notebook code. The 23 preserved historical local artifacts retained identical bytes and update times. No files were staged or committed during that original offline correction pass.

A visual browser inspection of the rebuilt local HTML was not completed: the browser security policy rejected the `file://` URL. No alternative browser route was used. HTML text/anchors, local resources and aggregate consistency were checked statically; this is not a claim of visual inspection or live deployment verification.
