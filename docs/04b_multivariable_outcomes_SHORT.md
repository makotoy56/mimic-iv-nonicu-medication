# 04b - Multivariable Outcomes Analysis (Short Summary)


Full notebook:
[04b. Multivariable Logistic Regression](../notebooks/04b_multivariable_outcomes.ipynb)

## Purpose
This notebook evaluates the association between documented early inpatient renin–angiotensin–aldosterone system (RAAS) prescription exposure and in-hospital mortality among adult non-ICU hospital admissions.

The goal is not causal inference, but to demonstrate how multivariable regression results can be translated into clinically interpretable, risk-based effect measures using real-world hospital data.

## Data and Study Population
The analysis uses the finalized admission-level analysis dataset derived from MIMIC-IV v3.1, restricted to adult, non-ICU hospital admissions (one row per `hadm_id`). Patients may contribute multiple qualifying admissions.

Documented early inpatient RAAS prescription exposure is defined as any ACE inhibitor or ARB prescription record with `starttime` from admission through less than 24 hours. The definition does not confirm administration, adherence, outpatient chronic use, or treatment duration.
The primary outcome is in-hospital mortality, defined by the hospital expiration flag.

## Methods
A multivariable logistic regression model was fitted, adjusting for:
- Age
- Sex
- Race group
- Admission type
- Insurance category
- Calendar period of admission

Categorical variables were one-hot encoded with explicit handling of missing values.
Model performance was evaluated using ROC AUC and precision–recall AUC.

### Feature Construction (Model Inputs)
The modeling matrix is defined explicitly as:
- `exposure` (binary early RAAS indicator)
- `num_vars = ["age"]`
- `cat_vars = ["gender", "race_group", "admission_type", "insurance", "anchor_year_group"]`

Categorical variables are one-hot encoded and concatenated with `exposure` and `num_vars`, yielding `feature_cols` (e.g., `gender_*`, `race_group_*`, `admission_type_*`, `insurance_*`, `anchor_year_group_*`).

Outcome handling is separated from features: `hospital_expire_flag` is used only to construct `outcome` and is not included in `feature_cols`.

**Recommended guard (leakage prevention)**  
Add a simple assert before modeling to block post-outcome columns:
```python
forbidden_cols = {"hosp_los", "dischtime", "deathtime", "hospital_expire_flag", "outcome"}
assert forbidden_cols.isdisjoint(feature_cols)
```

To improve interpretability beyond odds ratios, results were summarized using:
- Average marginal effects (AME)
- Adjusted predicted risks
- Age-specific adjusted risk differences

Statistical uncertainty for marginal effects was quantified using nonparametric bootstrap resampling, repeating the full modeling pipeline for each resample.

The 24-hour landmark analysis was added as a bias-reduction sensitivity analysis by restricting to admissions with survival beyond 24 hours (or no recorded death) and re-estimating the model with the same covariates and exposure definition.
The primary and landmark exposure OR/95% CI are reported side-by-side in the notebook comparison table; interpret any attenuation or shift in magnitude from that table.
As an added proxy for baseline severity, admission source (`admission_location`) was included in a 24-hour landmark refit.
In this run, the exposure OR attenuated toward the null from the primary model (0.32) to the 24-hour landmark model (0.36), and further with the proxy model (0.39). Directional consistency does not establish causality.

## Key Results
Documented early inpatient RAAS prescription exposure was consistently associated with lower in-hospital mortality after multivariable adjustment.

- The adjusted odds ratio for documented early inpatient RAAS prescription exposure was 0.32 (95% CI 0.27-0.38).
- On the absolute risk scale, the fitted model produced an average adjusted predicted mortality difference of approximately -0.38 percentage points between the documented-exposure and no-exposure scenarios.
- Adjusted predicted mortality increased with age in both exposure groups, but the difference in adjusted predicted risk widened among older patients.
- Bootstrap confidence intervals for age-specific risk differences remained below zero across most of the adult age range.

## Interpretation
These findings demonstrate how marginal effects and risk differences can complement odds ratios by providing clinically interpretable estimates on the absolute risk scale.

The observational design precludes causal conclusions. Directional consistency across the primary and landmark models supports reporting the association as a sensitivity finding, but treatment eligibility, confounding by indication, early clinical stability, clinician prescribing behavior, and unmeasured severity may still affect the estimates.
This notebook illustrates a transparent and reproducible approach to multivariable outcome modeling and uncertainty quantification in large clinical datasets.

---
## Next Step

Proceed to:
- [05 - SAS-Python Reproducibility Validation](05_sas_python_validation_SHORT.md)

This next notebook/document briefly describes the next workflow step.
