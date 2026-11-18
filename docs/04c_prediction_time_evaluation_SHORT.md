# 04c - Separate Prediction-Time Evaluation (SHORT)

Full notebook: [04c. Prediction-time evaluation](../notebooks/04c_prediction_time_evaluation.ipynb)

## Purpose and outcome

This additional analysis evaluates internal prediction at hospital admission and admission + 24 hours. The outcome is death **strictly after the prediction instant through recorded hospital discharge**, with a variable hospital-stay horizon. It is separate from 04b's association analyses and retrospective discrimination (ROC AUC 0.860635 / PR AUC 0.117607).

## Eligibility and information available

- Start from adult `base_admissions` with native `transfers`, `icustays`, `prescriptions` and `poe`; do not reuse the entire-stay ICU-excluded association cohort.
- At each point require confirmed survival, continued hospitalization, a single confirmed target-ward interval and no ICU entry up to that point. General/specialty, intermediate/stepdown and hospital observation wards are included. ED/ED observation, PACU, nursery and unknown/ambiguous locations are excluded. Exact-boundary deaths/discharges/ICU entries are excluded; later ICU transfers remain followed. A later ward entry cannot fill an unknown earlier location.
- Missing/inconsistent timing or outcome records are excluded with explicit reasons, never assigned survival silently. See [full exclusion counts](PREDICTION_TIME_VALIDATION.md#data-and-independent-checks).
- Primary predictors are reconstructed age and recorded sex. The 24h companion adds a 0–<24h RAAS prescription record only if its linked POE order time is no later than 24h. This differs from the association exposure; zero is no confirmed available qualifying record, not proven absence of prescribing. Neither definition establishes administration. Original record-entry/version history is unavailable; demographic availability is assumed.

## Cohorts

| Time | Eligible admissions / deaths | Test admissions / deaths | Later ICU admissions retained |
| --- | ---: | ---: | ---: |
| Admission | 719 / 11 | 163 / 3 | 258 |
| 24 hours | 336,372 / 3,457 | 67,641 / 698 | 15,329 |

Admission-time results apply only to the ward-confirmed subset. Only 719 admissions / 11 deaths were eligible, including 3 test deaths; reliable admission-time performance is not established. The cohort was not broadened after viewing outcomes.

## Methods and results

Three unweighted L2 logistic models (C=1, lbfgs, max_iter=2000) use training-only imputation/scaling/encoding. One 80/20 patient allocation (seed 42), fixed before time-specific filters, keeps all admissions of each patient together. Train/test patient overlap is zero; all three fits converged. No holdout-driven tuning or recalibration was performed.

| Model | ROC AUC (95% CI) | PR AUC / AP (95% CI) | Brier |
| --- | --- | --- | --- |
| Admission: age/sex | 0.548958 (CI withheld) | 0.030599 (CI withheld) | 0.018112 |
| 24h: age/sex | 0.686252 (0.668263–0.700923) | 0.021281 (0.018373–0.026761) | 0.010167 |
| 24h: age/sex + verified RAAS record | 0.699762 (0.681841–0.714670) | 0.022521 (0.019358–0.028395) | 0.010162 |

Each 24h model accepted 500/500 held-out-patient bootstrap draws. Admission had 33 one-class draws, leaving 467/500 below the prespecified 95% threshold: all its bootstrap intervals are withheld. Available intervals condition on the trained model and exclude training-sample uncertainty. Calibration is diagnosed, not used to recalibrate the model; see [calibration and chronology sensitivity](PREDICTION_TIME_VALIDATION.md).

The two times have different risk sets; their AUC difference does not show model improvement. The RAAS companion is a feature comparison, not a treatment effect. These limited-feature retrospective internal evaluations are not prospective, external or deployment validation.

## Execution and outputs

Notebook 04c completed 8/8 code cells without runtime error and saved aggregate `prediction_time_*.csv/json` plus the calibration figure. SQL/Python eligibility counts matched at both times. Independent native-transfer reconstruction matched all 1,184 sampled prediction points; 29 BigQuery boundary cases and 16 synthetic transfer cases passed. Only aggregate outputs are public. The initial protocol was amended during cohort review to require confirmed ward location before these revised fits; see the [protocol](PREDICTION_TIME_PROTOCOL.md) and [current execution record](CLINICAL_REEXECUTION_615de01.md).

Next: [Quarto report — prediction-time evaluation](https://makotoy56.github.io/mimic-iv-nonicu-medication/reports/nonicu_raas_mortality_report.html#prediction-time-evaluation).
