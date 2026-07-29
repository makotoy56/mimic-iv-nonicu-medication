# 03b - Describe Analysis Dataset (Baseline Characteristics)


Full notebook:
[03b. Baseline Characteristics by Early RAAS Exposure](../notebooks/03b_describe_analysis_dataset.ipynb)

## Overview

This notebook summarizes baseline characteristics of the non-ICU hospital admission cohort stratified by documented early inpatient RAAS prescription exposure.

The primary objective is to describe cohort composition, assess baseline differences between exposure groups, and generate Table 1–style descriptive summaries to inform downstream adjusted outcome analyses.

No outcome models or causal inference are performed in this notebook.

## Data Source

- MIMIC-IV v3.1 (BigQuery public dataset)
- Project: mimic-iv-portfolio
- Input table:
  - nonicu_raas.analysis_dataset  
    (constructed in 03a via SQL-based preprocessing)

Each row represents a unique non-ICU hospital admission.

## Cohort Description

- Total admissions: 460,786
- Each row corresponds to a unique hospital admission (one-to-one with hadm_id)
- Patients may contribute multiple qualifying admissions.
- Adult patients only (age ≥ 18 years)
- Non-ICU hospital admissions only

Documented early inpatient RAAS prescription exposure was observed in 12.33% of admissions (n = 56,825).

## Exposure Definition

Documented early inpatient RAAS prescription exposure was defined from prescription records with start times within 24 hours for:
- ACE inhibitors, or
- Angiotensin receptor blockers (ARBs)

A binary indicator (raas_any_early) was used as the primary exposure variable.

The prescription-based definition does not confirm administration or measure outpatient chronic use, adherence, dose, treatment indication, or duration.

Exposure groups were labeled for descriptive clarity as:
- Documented early RAAS prescription exposure
- No documented early RAAS prescription exposure

Internal consistency checks confirmed perfect agreement between composite exposure indicators and their component definitions.

## Baseline Continuous Characteristics

Baseline continuous variables were summarized by exposure group using both:
- Mean (standard deviation)
- Median [interquartile range]

Key findings:
- Admissions with documented early RAAS prescription exposure involved substantially older patients than admissions without documented exposure
  (mean age 68.6 vs. 56.6 years; median 69 vs. 58 years).
- Hospital length of stay was slightly longer among admissions with documented early prescription exposure
  (median 2.75 vs. 2.33 days).

These summaries indicate marked baseline age differences between exposure groups.

## Baseline Categorical Characteristics

Categorical variables were summarized as counts and percentages within each exposure group, including:
- Sex
- Admission type
- Calendar period (anchor year group)

Notable patterns included:
- A higher proportion of males among admissions with documented early prescription exposure.
- Substantial differences in admission type, with documented early prescription exposure more common among emergency-related admissions.
- Broadly similar calendar-period distributions, with modest differences across eras.

Percentage-point differences were reported to aid interpretation.

## Summary Interpretation

Baseline characteristics differed systematically between documented early inpatient RAAS prescription-exposure groups, particularly with respect to age, sex distribution, and admission pathway.

These unadjusted differences suggest substantial confounding by baseline risk and clinical context, underscoring the need for multivariable adjustment in downstream outcome analyses.

## Outputs and Downstream Use

This notebook produces descriptive baseline summaries used as inputs for subsequent analyses, including:

- Table 1–style continuous-variable summaries
- Group-level baseline summary statistics
- Categorical distribution tables for exploratory assessment

These outputs support interpretation of adjusted outcome models and marginal effect estimates in downstream notebooks (04a, 04b).

---
## Next Step

Proceed to:
- [04a - Unadjusted Outcomes Overview (Non-ICU Admissions)](04a_unadjusted_outcomes_SHORT.md)

This next notebook/document briefly describes the next workflow step.
