# Methods Overview

## Design

This project is a retrospective observational cohort study using MIMIC-IV v3.1 hospital data. The unit of analysis is the hospital admission (`hadm_id`): each row represents one adult non-ICU hospital admission. The cohort is not restricted to one admission per patient, so patients may contribute multiple qualifying admissions.

Cohort construction, exposure definition, baseline covariate assembly, and outcome derivation are implemented with BigQuery-compatible SQL and structured Python notebooks. SAS programs reproduce selected aggregate outputs for validation.

## Cohort Definition

The cohort includes adult inpatient admissions from MIMIC-IV after excluding admissions associated with at least one ICU stay. The fixed non-ICU cohort is constructed upstream before exposure definition or outcome modeling.

The final analytic cohort contains 460,786 adult non-ICU hospital admissions.

## Exposure Definition

Documented early inpatient RAAS prescription exposure is defined using records from the MIMIC-IV `prescriptions` table.

Admissions are classified as exposed if they have at least one ACE inhibitor or ARB prescription record with `starttime` on or after hospital admission and before 24 hours after admission. Admissions without such a record are classified as unexposed.

The 0 to <24 hour window is an operational analytic definition, not a biological threshold or guideline-based treatment window.

This prescription-based definition does not confirm medication administration and does not measure outpatient chronic use, adherence, dose, treatment indication, or duration.

The exposure table includes:

- `acei_early`: early ACE inhibitor exposure
- `arb_early`: early ARB exposure
- `raas_both_early`: concurrent early ACE inhibitor and ARB exposure
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

The primary clinical analysis is multivariable logistic regression estimating the association between documented early inpatient RAAS prescription exposure and in-hospital mortality. Results are summarized using:

- Logistic regression coefficients
- Odds ratios and confidence intervals
- Adjusted predicted mortality risks
- Average marginal effects
- Age-specific adjusted risk differences

Bootstrap resampling is used in the notebook to quantify uncertainty for selected marginal-effect estimates.

## Sensitivity And Bias Checks

The multivariable notebook includes a 24-hour landmark bias-reduction sensitivity analysis. It restricts the cohort to admissions with no recorded death or with recorded death more than 24 hours after admission, then refits the same core model. An additional landmark model includes admission source as a proxy for baseline severity.

These sensitivity analyses do not establish causality or remove all potential bias. Residual confounding by indication, treatment eligibility, early clinical stability, comorbidity burden, acute severity, prescribing behavior, and unmeasured clinical context may remain.

The models treat admissions as observations and do not account for within-patient correlation across multiple qualifying admissions.

## Validation Workflow

The SAS-Python validation workflow compares exported aggregate outputs from Python notebooks and SAS programs. It is designed to check reproducibility of selected outputs, not to introduce a new clinical estimand.

See [Validation notes](VALIDATION_NOTES.md) for scope and discrepancy details.
