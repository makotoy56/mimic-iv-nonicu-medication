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

**Implemented guard (leakage prevention)**
The notebook blocks post-outcome columns from modeling features:
```python
forbidden_cols = {"hosp_los", "dischtime", "deathtime", "hospital_expire_flag", "outcome"}
assert forbidden_cols.isdisjoint(feature_cols)
```

To improve interpretability beyond odds ratios, results were summarized using:
- Average marginal effects (AME)
- Adjusted predicted risks
- Age-specific adjusted risk differences

The historical 200-replicate admission bootstrap computed intervals for age-specific typical-profile risk differences, not an AME interval. The added patient-cluster procedure separately computes intervals for AME, predicted risks, age contrasts and Firth ORs, with the full fitting procedure repeated and failures counted.

The corrected 24-hour landmark analysis requires confirmed survival and continued hospitalization strictly beyond admission + 24 hours. Death or discharge exactly at 24 hours is excluded. Missing/invalid admission or discharge times, missing death times in hospital deaths, contradictory death flags/times, and deaths outside the admission interval are excluded with explicit counts. A consistent live discharge may have no death time. Subsequent in-hospital mortality is modeled with the same covariates and the unchanged 0–<24-hour prescription exposure.

**Patient-aware update (2026-11-17):** Current uncertainty summaries use 500 prespecified patient-cluster bootstrap draws, carrying all eligible admissions per sampled patient. Firth point estimates and all exposure/cohort/adjustment definitions are unchanged. Historical admission-independent profile intervals remain available separately. See [patient-aware validation](PATIENT_AWARE_VALIDATION.md).

Original nonconverged MLE comparison tables are diagnostic only. Supplementary Firth comparison tables and patient-cluster intervals are reported separately.
As an added proxy for baseline severity, admission source (`admission_location`) was included in a 24-hour landmark refit.
The original unpenalized outputs remain nonconverged. In the additional Firth analysis, original-condition ordinary/proxy ORs were 0.362/0.388; corrected-condition ORs were 0.356/0.382. All five full-data Firth fits converged; historical profile intervals and added patient-cluster intervals are explicitly distinguished. The full table and independent numerical checks are in the Firth validation note.

## Key Results
Documented early inpatient RAAS prescription exposure was consistently associated with lower in-hospital mortality after multivariable adjustment.

- Supplementary Firth primary-cohort OR 0.319 (95% patient-cluster CI 0.267–0.380); historical unpenalized OR output is nonconverged.
- On the absolute risk scale, the fitted model produced an average adjusted predicted mortality difference of approximately -0.38 percentage points between the documented-exposure and no-exposure scenarios.
- Adjusted predicted mortality increased with age in both exposure groups, but the difference in adjusted predicted risk widened among older patients.
- Newly computed AME -0.3797 percentage points (95% patient-cluster CI -0.4201 to -0.3407); current age-contrast intervals also resample patients.

## Interpretation
These findings demonstrate how marginal effects and risk differences can complement odds ratios by providing clinically interpretable estimates on the absolute risk scale.

The observational design precludes causal conclusions. The added Firth sensitivity estimates address separation, while the original unpenalized outputs remain nonconverged; treatment eligibility, confounding by indication, early clinical stability, clinician prescribing behavior, and unmeasured severity may still affect the estimates.
This notebook illustrates a transparent and reproducible approach to multivariable outcome modeling and uncertainty quantification in large clinical datasets.

---
## Next Step

Proceed to:
- [Current Python workflow validation](PYTHON_WORKFLOW_VALIDATION.md)

This next notebook/document briefly describes the next workflow step.

| Validation | Train / test admissions | Test deaths | Overlapping patients | ROC AUC | PR AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Admission-random reference | 368,628 / 92,158 | 465 | 42,796 | 0.857576 | 0.106915 |
| Patient-disjoint holdout | 368,309 / 92,477 | 468 | 0 | 0.860635 | 0.117607 |

The single patient-disjoint holdout is internal validation; different split case mixes do not demonstrate performance improvement. The current figures and full fitting diagnostics are described in [patient-aware validation](PATIENT_AWARE_VALIDATION.md).
