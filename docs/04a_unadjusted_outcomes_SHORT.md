# 04a - Unadjusted Outcomes Overview (Non-ICU Admissions)


Full notebook:
[04a. Unadjusted Outcomes Overview](../notebooks/04a_unadjusted_outcomes.ipynb)

## Overview

This notebook presents unadjusted, descriptive summaries of in-hospital outcomes by documented early inpatient RAAS prescription exposure among non-ICU adult hospital admissions.

The purpose of this step is to characterize crude outcome patterns prior to any multivariable adjustment, providing baseline context for subsequent adjusted analyses.

All results in this notebook are descriptive only and are not interpreted causally.

## Data Source and Study Population

- Data source: **MIMIC-IV v3.1** (BigQuery public dataset)
- Project: `mimic-iv-portfolio`
- Input table: `nonicu_raas.analysis_dataset`  
  (constructed in `03_build_analysis_dataset.sql`)

The study population includes adult (≥18 years) non-ICU hospital admissions.
Each hospital admission is an analysis observation. Patients may contribute multiple qualifying admissions. This descriptive notebook does not model within-patient correlation; 04b separately uses patient-cluster uncertainty and patient-disjoint retrospective discrimination.

## Exposure and Outcome Definitions

- **Exposure**: Documented early inpatient RAAS prescription exposure, defined from ACE inhibitor or ARB prescription records with start times from admission through less than 24 hours (`raas_any_early`, binary). This does not confirm administration.
- **Outcome**: In-hospital mortality, defined using the hospital expiration flag (`hospital_expire_flag`).

## Descriptive Analyses

Unadjusted summaries were computed separately for admissions with and without documented early inpatient RAAS prescription exposure, including:

- Number of admissions per exposure group
- Number of in-hospital deaths
- Crude in-hospital mortality rates
- Unadjusted length of stay summaries

No regression modeling or covariate adjustment was performed in this notebook.

## Key Unadjusted Findings

- Documented early inpatient RAAS prescription exposure occurred in approximately 12% of non-ICU admissions.
- The overall in-hospital mortality rate in the cohort was approximately 0.5%.
- Crude in-hospital mortality was lower among admissions with documented early prescription exposure compared with those without documented exposure.
- Admissions with documented early prescription exposure had a slightly longer unadjusted hospital length of stay.

## Interpretation Framework

All findings presented in this notebook represent **unadjusted comparisons**.

Observed differences in outcomes may reflect confounding by age, admission characteristics, baseline clinical severity, or other unmeasured factors.
Accordingly, these results should not be interpreted as evidence of a causal or protective effect of RAAS treatment.

The primary role of this analysis is to establish descriptive context and motivate the need for multivariable adjustment.
Adjusted outcome modeling and absolute effect estimation are presented in the subsequent multivariable analysis notebook (04b).

## Output and Downstream Use

This notebook does not create new BigQuery tables. It exports the current aggregate summary to `python/outputs/unadjusted_outcomes.csv` and generates descriptive figures for interpretation and documentation.

Results from this notebook inform the original association analyses. Their entire-stay non-ICU cohort differs from the additional ward-confirmed prediction-time cohorts in [04c SHORT](04c_prediction_time_evaluation_SHORT.md).

## Current execution (2026-11-18)

This notebook was reexecuted successfully with a fresh repository kernel on 2026-11-19. The [current execution record](CLINICAL_REEXECUTION_20261119.md) covers all 8 notebooks / 109 code cells with zero runtime error outputs, live Python-generated displays, connected BigQuery checks and preserved association estimates. Runtime success is distinct from the nonconverged MLE diagnostics in 04b.

---
## Next Step

Proceed to:
- [04b - Multivariable Outcomes Analysis (Short Summary)](04b_multivariable_outcomes_SHORT.md)

This next notebook/document briefly describes the next workflow step.
