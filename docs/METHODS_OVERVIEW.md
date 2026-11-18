# Methods Overview

## Design

This project is a retrospective observational cohort study using MIMIC-IV v3.1 hospital data. The unit of analysis is the hospital admission (`hadm_id`): each row represents one adult non-ICU hospital admission. The cohort is not restricted to one admission per patient, so patients may contribute multiple qualifying admissions.

Cohort construction, exposure definition, baseline covariate assembly, and outcome derivation are implemented with BigQuery-compatible SQL and structured Python notebooks. The public workflow is limited to BigQuery and Python.

## Cohort Definition

The cohort includes adult hospital admissions (including observation categories) from MIMIC-IV after excluding admissions associated with at least one ICU stay. The fixed non-ICU cohort is constructed upstream before exposure definition or outcome modeling.

The final analytic cohort contains 460,786 adult non-ICU hospital admissions.

## Exposure Definition

Documented early inpatient RAAS prescription exposure is defined using records from the MIMIC-IV `prescriptions` table.

Admissions are classified as exposed if they have at least one ACE inhibitor or ARB prescription record with `starttime` on or after hospital admission and before 24 hours after admission. Admissions without such a record are classified as unexposed.

The 0 to <24 hour window is an operational analytic definition, not a biological threshold or guideline-based treatment window.

Both-class flags only indicate records from both classes in the same early window; they do not establish overlapping treatment or co-administration. This prescription-based definition does not confirm medication administration and does not measure outpatient chronic use, adherence, dose, treatment indication, or duration.

The exposure table includes:

- `acei_early`: early ACE inhibitor exposure
- `arb_early`: early ARB exposure
- `raas_both_early`: both ACE inhibitor and ARB prescription-record flags in the same 0–<24-hour window
- `raas_any_early`: any documented early RAAS prescription exposure

The primary exposure variable is `raas_any_early`.

## Analysis Dataset Construction

`nonicu_raas.analysis_dataset` is an admission-level table built by left-joining `nonicu_raas.nonicu_admissions` to `nonicu_raas.exposure_raas_early` on `subject_id` and `hadm_id`. Missing exposure flags are handled with `COALESCE` so unexposed admissions remain in the analysis dataset.

## Outcome

The primary outcome is in-hospital mortality, defined using `hospital_expire_flag`.

## Covariates

The primary multivariable logistic regression adjusts for:

- Age
- Gender
- Race group
- Admission type
- Insurance category
- Calendar period of admission (`anchor_year_group`)

Categorical variables are one-hot encoded with explicit handling of missing values. Outcome variables and post-outcome fields are kept out of the feature matrix.

## Primary Analysis

| Component | Estimator / data | Interpretation and uncertainty |
| --- | --- | --- |
| Historical primary OR output | Unpenalized statsmodels Logit, full cohort | Separated/nonconverged; diagnostic archive only |
| Supplementary adjusted ORs | Firth/Jeffreys logistic regression, same covariates and cohort variants | Profile intervals assume admission independence; additional patient-cluster intervals resample entire patients |
| Discrimination | Class-balanced L2 sklearn logistic regression, training data only | Patient-disjoint holdout ROC/PR AUC; admission-row split retained as reference |
| Average risks / AME / age contrasts | Unweighted L2 sklearn logistic regression, full cohort | AME averages observed covariates; age curves use a typical mean profile; patient-cluster bootstrap intervals |

The main-effects model has no exposure-by-age interaction. Age-varying absolute contrasts should not be called a formal test of interaction or effect heterogeneity.

The primary clinical analysis is multivariable logistic regression estimating the association between documented early inpatient RAAS prescription exposure and in-hospital mortality. Results are summarized using:

- Logistic regression coefficients
- Odds ratios and confidence intervals
- Adjusted predicted mortality risks
- Average marginal effects
- Age-specific adjusted risk differences

Historical admission-level bootstrap intervals apply only to age-specific typical-profile contrasts. The additional patient-cluster bootstrap supplies AME/predicted-risk and Firth OR intervals. Age curves fix other covariates at means; they are not marginal standardization or a formal exposure-by-age interaction test.

## Sensitivity And Bias Checks

The multivariable notebook includes a 24-hour landmark bias-reduction sensitivity analysis. The corrected rule requires valid admission/discharge times, discharge strictly after admission + 24 hours, and consistent survival/death records. Live discharges require a zero expiration flag and no death time; hospital deaths require a death time strictly after the landmark and no later than discharge. Death or discharge exactly at 24 hours, unknown hospital-death timing, and inconsistent records are excluded with reason counts before the same core model is refitted. An additional landmark model includes admission source as a proxy for baseline severity.

These sensitivity analyses do not establish causality or remove all potential bias. Residual confounding by indication, treatment eligibility, early clinical stability, comorbidity burden, acute severity, prescribing behavior, and unmeasured clinical context may remain.

Historical models/profile intervals treat admissions as independent. Added patient-cluster bootstrap intervals resample patients with all eligible admissions. Added discrimination validation holds entire patients out; these are separate corrections for inference and train/test overlap.

## Validation Workflow

The patient-disjoint holdout is an internal evaluation of retrospective discrimination on the full admission cohort. It uses prescription records from 0–<24 hours while including deaths within 24 hours, and applies no 24-hour survival/continued-hospitalization eligibility filter. There is no fixed clinical prediction time or prospective prediction horizon: ROC AUC 0.860635 and PR AUC 0.117607 do not describe admission-time or 24-hour prognostic performance. Patient separation and train-only preprocessing address patient overlap and preprocessing leakage, not temporal feature availability. The 24-hour landmark association analyses separately require confirmed survival and continued hospitalization strictly beyond 24 hours and evaluate subsequent in-hospital death; they use a different eligible cohort.

Python validation covers boundary conditions, numerical fit checks, patient-cluster uncertainty and patient-disjoint prediction evaluation. Runtime success does not establish model convergence or causal validity.

See [reproducible scope](REPRODUCIBLE_SCOPE.md) and [current execution evidence](PYTHON_WORKFLOW_VALIDATION.md).

**Patient-aware update (2026-11-17):** Current uncertainty summaries use 500 prespecified patient-cluster bootstrap draws, carrying all eligible admissions per sampled patient. Firth point estimates and all exposure/cohort/adjustment definitions are unchanged. Historical admission-independent profile intervals remain available separately. See [patient-aware validation](PATIENT_AWARE_VALIDATION.md).

The supplementary Firth estimator uses a Jeffreys-information penalty and 95% penalized profile-likelihood intervals. All original adjustment categories are retained, including the zero-event admission-type category. Age centering/scaling is an invertible numerical transformation; exact frequency compression of duplicate design/outcome rows does not remove admissions. The original unpenalized primary fit and separate sklearn risk model are preserved.


## Separate admission/24-hour prediction evaluation

Notebook 04c adds an independently defined ward-confirmed prediction-time branch from adult base admissions. It retains later ICU transfers and follows subsequent in-hospital death to discharge, with age/sex primary features and a time-verified RAAS-record companion at 24h. The original association cohort/estimates and 04b retrospective discrimination are unchanged. See [protocol](PREDICTION_TIME_PROTOCOL.md) and [real-data results, calibration, exclusions and limits](PREDICTION_TIME_VALIDATION.md).
