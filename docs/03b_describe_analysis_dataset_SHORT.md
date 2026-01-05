# 03b Describe Analysis Dataset (Baseline Characteristics)

## Overview

This notebook summarizes baseline characteristics of the non-ICU hospital admission cohort stratified by early RAAS inhibitor exposure.

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
- Adult patients only (age ≥ 18 years)
- Non-ICU hospital admissions only

Early RAAS inhibitor exposure was observed in 12.33% of admissions (n = 56,825).

## Exposure Definition

Early RAAS inhibitor exposure was defined as any early in-hospital administration of:
- ACE inhibitors, or
- Angiotensin receptor blockers (ARBs)

A binary indicator (raas_any_early) was used as the primary exposure variable.

Exposure groups were labeled for descriptive clarity as:
- RAAS early
- No RAAS early

Internal consistency checks confirmed perfect agreement between composite exposure indicators and their component definitions.

## Baseline Continuous Characteristics

Baseline continuous variables were summarized by exposure group using both:
- Mean (standard deviation)
- Median [interquartile range]

Key findings:
- Patients in the RAAS early group were substantially older than those without early RAAS exposure  
  (mean age 68.6 vs. 56.6 years; median 69 vs. 58 years).
- Hospital length of stay was slightly longer among RAAS-exposed admissions  
  (median 2.75 vs. 2.33 days).

These summaries indicate marked baseline age differences between exposure groups.

## Baseline Categorical Characteristics

Categorical variables were summarized as counts and percentages within each exposure group, including:
- Sex
- Admission type
- Calendar period (anchor year group)

Notable patterns included:
- A higher proportion of males in the RAAS early group.
- Substantial differences in admission type, with RAAS exposure more common among emergency-related admissions.
- Broadly similar calendar-period distributions, with modest differences across eras.

Percentage-point differences were reported to aid interpretation.

## Summary Interpretation

Baseline characteristics differed systematically between early RAAS exposure groups, particularly with respect to age, sex distribution, and admission pathway.

These unadjusted differences suggest substantial confounding by baseline risk and clinical context, underscoring the need for multivariable adjustment in downstream outcome analyses.

## Outputs and Downstream Use

This notebook produces descriptive baseline summaries used as inputs for subsequent analyses, including:

- Table 1–style continuous-variable summaries
- Group-level baseline summary statistics
- Categorical distribution tables for exploratory assessment

These outputs support interpretation of adjusted outcome models and marginal effect estimates in downstream notebooks (04a, 04b).