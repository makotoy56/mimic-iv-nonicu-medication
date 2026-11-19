# Prediction-time evaluation: real-data validation

The [2026-11-19 connected Run All](CLINICAL_REEXECUTION_20261119.md) reproduced the cohorts, metrics, interval-withholding rule, SQL/Python counts, native-transfer checks and chronology sensitivity below. The historical 29-case BigQuery boundary exercise was not repeated in that run.

This is an **additional** prediction-time analysis in notebook 04c, separate from 04b's original association cohorts and retrospective discrimination (ROC AUC 0.860635 / PR AUC 0.117607). The outcome is death strictly after the prediction instant through recorded hospital discharge, with a variable hospital-stay horizon.

At admission and at 24 hours, eligibility requires survival, continued hospitalization, a single confirmed non-ICU target-ward transfer interval, and no ICU entry up to that instant. General/specialty, intermediate/stepdown and hospital observation wards are included; ED/ED observation, PACU, nursery and unknown/ambiguous location are excluded. Later ICU transfers remain followed. No later ward entry backfills an unknown admission location. Admission-time results therefore apply to the ward-confirmed subset, not all admissions. This replaces neither the entire-stay ICU exclusion nor the numbers in the original association analyses.

The primary predictors are reconstructed age and recorded sex. A 24-hour companion adds a qualifying 0–<24h RAAS prescription record whose linked POE order time is no later than 24 hours; unverified or later order times cannot make the feature positive. This differs from the original association exposure. Records do not establish medication administration. Untimestamped demographics are assumed available at admission; original entry/version history is unavailable.

## Design and eligibility amendment

The initial no-prior-ICU design was fixed before its input/performance review. Cohort review then identified that absence of ICU records alone did not establish a target ward. The [documented protocol amendment](PREDICTION_TIME_PROTOCOL.md) added observed ward confirmation before the revised models were run; no features or estimators were tuned on holdout outcomes. Initial working outputs are retained privately and are not current public estimates. Source hashes and the pre-run amendment freeze are in the aggregate execution receipt.

## Cohorts

| Time | Eligible admissions / deaths | Train admissions | Test admissions / deaths | Later ICU admissions retained |
| --- | --- | --- | --- | --- |
| Admission | 719 / 11 | 556 | 163 / 3 | 258 |
| 24 hours | 336,372 / 3,457 | 268,731 | 67,641 / 698 | 15,329 |

The protocol used unweighted L2 logistic regression (C=1, lbfgs, max_iter=2000), with training-only imputation, scaling and categorical encoding. One 80/20 patient allocation (seed 42) was fixed on the adult base before time-specific eligibility filters; all admissions of each patient stay in one partition. No test-driven tuning or recalibration was performed. Each model fit converged, with zero patient overlap. Each 24-hour model had 500/500 successful held-out-patient resamples. Admission had only 3 test deaths: 33/500 resamples had one outcome class, leaving 467/500 below the prespecified 95% threshold; all admission bootstrap intervals are withheld. Its point metrics/calibration are sparse-event diagnostics and do not establish reliable admission-time performance. Available 95% percentile intervals condition on the fitted training model and exclude training-sample uncertainty. Calibration is diagnosed without changing predictions. PR AUC is average precision (AP).

The admission and 24-hour populations differ. Metric differences across times are not evidence of improvement. The companion is a feature comparison, not a treatment-effect estimate. These limited-feature retrospective internal models are not prospective, external or deployment validation.

## Discrimination and calibration

Admission ward confirmation is exceptionally sparse (719 admissions, 11 deaths overall; 163 test admissions, 3 deaths). Do not generalize its diagnostic point metrics to all admissions or claim successful admission-time validation. The cohort was not broadened after viewing these outcomes.

| Model | ROC AUC (95% CI) | PR AUC / AP (95% CI) | Brier |
| --- | --- | --- | --- |
| Admission: age/sex | 0.548958 (CI withheld) | 0.030599 (CI withheld) | 0.018112 |
| 24h: age/sex | 0.686252 (0.668263–0.700923) | 0.021281 (0.018373–0.026761) | 0.010167 |
| 24h: age/sex + verified RAAS record | 0.699762 (0.681841–0.714670) | 0.022521 (0.019358–0.028395) | 0.010162 |

| Model | Observed / mean predicted mortality | Calibration intercept / slope | Brier / constant-risk reference |
| --- | --- | --- | --- |
| Admission: age/sex | 1.840% / 1.406% | -4.2455 / -0.0621 | 0.018112 / 0.018082 |
| 24h: age/sex | 1.032% / 1.036% | 0.0879 / 1.0213 | 0.010167 / 0.010213 |
| 24h: age/sex + verified RAAS record | 1.032% / 1.039% | -0.0030 / 1.0008 | 0.010162 / 0.010213 |

Brier scores are mean squared probability error; the constant reference predicts the training event rate. Calibration intercept/slope are diagnostic holdout fits (ideal 0/1), not applied recalibrations. Bin-wise observed risks and patient-bootstrap intervals are in the aggregate calibration CSV and [figure](../assets/prediction_time_calibration.png). Discrimination alone does not imply accurate absolute risks.

## Reading the admission-time calibration plot

Each point groups admissions with similar predicted risks. The horizontal axis is their average predicted mortality; the vertical axis is their observed mortality. The dashed line marks agreement between prediction and observation.

- **Why the line is jagged:** only 3 of the 163 test admissions died. One death in a small group can raise its observed mortality by several percentage points, while groups with no observed deaths stay at 0%. The line is strongly affected by these few events, so its shape alone cannot establish whether the model predicts well.
- **What 0% means:** no deaths were observed in that group. It does not mean that the group's true mortality risk is zero.
- **Why intervals are missing:** with so few deaths, too few patient resamples produced usable estimates to meet the reporting rule set before evaluation. Confidence intervals were therefore withheld. More deaths would need to be observed for a reliable admission-time assessment.

These explanations describe the existing estimates; they do not change the model, cohorts, bootstrap reporting rule or figure.

## Data and independent checks

The adult source base contained 546,028 admissions from 223,452 patients. Each time-specific exclusion flow below sums to that base. Reasons are hierarchical: only the first applicable reason is counted; flagged-death counts are not validated outcome totals for excluded records. Missing/inconsistent outcome times are never silently assigned survival.

| Time (hours) | First applicable reason | Admissions | Flagged deaths |
| --- | --- | --- | --- |
| 0 | death_after_discharge | 659 | 659 |
| 0 | death_before_admission | 11 | 11 |
| 0 | death_flag_without_deathtime | 11 | 11 |
| 0 | discharge_at_or_before_prediction | 5 | 0 |
| 0 | discharge_before_admission | 175 | 101 |
| 0 | icu_entry_at_or_before_prediction | 482 | 12 |
| 0 | included | 719 | 11 |
| 0 | location_no_covering_location | 145,282 | 2,936 |
| 0 | location_not_target_ward | 398,684 | 8,060 |
| 24 | death_after_discharge | 659 | 659 |
| 24 | death_at_or_before_prediction | 1 | 1 |
| 24 | death_before_admission | 11 | 11 |
| 24 | death_flag_without_deathtime | 11 | 11 |
| 24 | discharge_at_or_before_prediction | 120,664 | 1,617 |
| 24 | discharge_before_admission | 175 | 101 |
| 24 | icu_entry_at_or_before_prediction | 69,767 | 5,857 |
| 24 | included | 336,372 | 3,457 |
| 24 | location_no_covering_location | 484 | 23 |
| 24 | location_not_target_ward | 17,676 | 60 |
| 24 | location_unconfirmed_interval_end | 68 | 3 |
| 24 | location_unconfirmed_unit | 140 | 1 |

SQL and Python eligible-admission/death counts agree at both times. Actual BigQuery DATETIME tests passed all 29 synthetic cases at both times, and 16 synthetic transfer-interval cases cover exact entry/exit boundaries, later ICU, uncertain units/ends, overlaps and future-location non-backfill. A deterministic actual-transfer sample covered 592 admissions / 1,184 prediction points with 0 SQL/Python location mismatches. Only aggregates and query metadata are exported. Independent Mann–Whitney ROC and threshold AP implementations agree with the fitted model metrics within 1e-12.

The full adult base had 73,980 early RAAS records: 495 lacked a verified linked POE time and 5,556 had order times after 24 hours. Duplicate POE links: 0. Zero feature values mean no confirmed qualifying record available by the point, not proven absence of prescribing. No future stop/status/discontinuation fields are predictors.

The combined ICU-entry evidence identified 122 admissions with first ICU time after discharge and 29 after recorded death; these counts may overlap. A separately labelled post-QA sensitivity excludes their union without changing the primary specification or master patient allocation. It reports point estimates only, without bootstrap intervals:

| Model | Uncertain chronology excluded | Test admissions / deaths | ROC AUC | PR AUC / AP |
| --- | --- | --- | --- | --- |
| Admission: age/sex | 0 | 163 / 3 | 0.548958 | 0.030599 |
| 24h: age/sex | 10 | 67,640 / 697 | 0.685826 | 0.021169 |
| 24h: age/sex + verified RAAS record | 10 | 67,640 / 697 | 0.699639 | 0.022503 |

This chronology sensitivity assesses source-timing uncertainty; it does not exclude clinically plausible later ICU transfers. See `python/outputs/prediction_time_chronology_sensitivity.json` for independent connected SQL counts. Future interval ends are used to reconstruct point occupancy, but their later values/destinations do not select the risk set. Historical event times do not prove when records were entered or revised.

## Evidence and limits

Sources: `sql/05_prediction_time_inputs.sql`, `scripts/prediction_time_validation.py`, notebook 04c, aggregate `prediction_time_*.csv/json`, and [current reexecution record](CLINICAL_REEXECUTION_20261119.md). Source references and operational-availability assumptions are in the [protocol](PREDICTION_TIME_PROTOCOL.md). One internal split, approximate reconstructed age, restricted ward coverage, limited predictors, uncertain timestamps/version history, variable follow-up and exclusion of indeterminate outcomes limit generalization. No patient records, identifiers or individual scores are published.
