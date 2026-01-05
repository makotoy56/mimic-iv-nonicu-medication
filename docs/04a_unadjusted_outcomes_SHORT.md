# 04a. Unadjusted Outcomes Overview (Non-ICU Admissions)

## Overview

This notebook presents unadjusted, descriptive summaries of in-hospital outcomes by early RAAS inhibitor exposure among non-ICU adult hospital admissions.

The purpose of this step is to characterize crude outcome patterns prior to any multivariable adjustment, providing baseline context for subsequent adjusted analyses.

All results in this notebook are descriptive only and are not interpreted causally.

## Data Source and Study Population

- Data source: **MIMIC-IV v3.1** (BigQuery public dataset)
- Project: `mimic-iv-portfolio`
- Input table: `nonicu_raas.analysis_dataset`  
  (constructed in `03_build_analysis_dataset.sql`)

The study population includes adult (≥18 years) non-ICU hospital admissions.
Each hospital admission is treated as an independent observation.

## Exposure and Outcome Definitions

- **Exposure**: Early RAAS inhibitor use, defined as administration of any ACE inhibitor or ARB during the early phase of hospitalization (`raas_any_early`, binary).
- **Outcome**: In-hospital mortality, defined using the hospital expiration flag (`hospital_expire_flag`).

## Descriptive Analyses

Unadjusted summaries were computed separately for admissions with and without early RAAS inhibitor exposure, including:

- Number of admissions per exposure group
- Number of in-hospital deaths
- Crude in-hospital mortality rates
- Unadjusted length of stay summaries

No regression modeling or covariate adjustment was performed in this notebook.

## Key Unadjusted Findings

- Early RAAS inhibitor exposure occurred in approximately 12% of non-ICU admissions.
- The overall in-hospital mortality rate in the cohort was approximately 0.5%.
- Crude in-hospital mortality was lower among admissions with early RAAS exposure compared with those without exposure.
- Admissions with early RAAS exposure had a slightly longer unadjusted hospital length of stay.

## Interpretation Fra# 04a. Unadjusted Outcomes Overview (Non-ICU Admissions)

## Overview

This notebook presents unadjusted, descriptive summaries of in-hospital outcomes by early RAAS inhibitor exposure among non-ICU adult hospital admissions.

The purpose of this step is to characterize crude outcome patterns prior to any multivariable adjustment, providing baseline context for subsequent adjusted analyses.

All results in this notebook are descriptive only and are not interpreted causally.

## Data Source and Study Population

- Data source: **MIMIC-IV v3.1** (BigQuery public dataset)
- Project: `mimic-iv-portfolio`
- Input table: `nonicu_raas.analysis_dataset`  
  (constructed in `03_build_analysis_dataset.sql`)

The study population includes adult (≥18 years) non-ICU hospital admissions.
Each hospital admission is treated as an independent observation.

## Exposure and Outcome Definitions

- **Exposure**: Early RAAS inhibitor use, defined as administration of any ACE inhibitor or ARB during the early phase of hospitalization (`raas_any_early`, binary).
- **Outcome**: In-hospital mortality, defined using the hospital expiration flag (`hospital_expire_flag`).

## Descriptive Analyses

Unadjusted summaries were computed separately for admissions with and without early RAAS inhibitor exposure, including:

- Number of admissions per exposure group
- Number of in-hospital deaths
- Crude in-hospital mortality rates
- Unadjusted length of stay summaries

No regression modeling or covariate adjustment was performed in this notebook.

## Key Unadjusted Findings

- Early RAAS inhibitor exposure occurred in approximately 12% of non-ICU admissions.
- The overall in-hospital mortality rate in the cohort was approximately 0.5%.
- Crude in-hospital mortality was lower among admissions with early RAAS exposure compared with those without exposure.
- Admissions with early RAAS exposure had a slightly longer unadjusted hospital length of stay.

## Interpretation Framework

All findings presented in this notebook represent **unadjusted comparisons**.

Observed differences in outcomes may reflect confounding by age, admission characteristics, baseline clinical severity, or other unmeasured factors.
Accordingly, these results should not be interpreted as evidence of a causal or protective effect of early RAAS inhibitor use.

The primary role of this analysis is to establish descriptive context and motivate the need for multivariable adjustment.
Adjusted outcome modeling and absolute effect estimation are presented in the subsequent multivariable analysis notebook (04b).

## Output and Downstream Use

This notebook does not generate new tables.
Its outputs are descriptive summaries and figures used for exploratory interpretation and documentation.

Results from this notebook inform the interpretation of adjusted analyses but are not used directly for modeling.mework

All findings presented in this notebook represent **unadjusted comparisons**.

Observed differences in outcomes may reflect confounding by age, admission characteristics, baseline clinical severity, or other unmeasured factors.
Accordingly, these results should not be interpreted as evidence of a causal or protective effect of early RAAS inhibitor use.

The primary role of this analysis is to establish descriptive context and motivate the need for multivariable adjustment.
Adjusted outcome modeling and absolute effect estimation are presented in the subsequent multivariable analysis notebook (04b).

## Output and Downstream Use

This notebook does not generate new tables.
Its outputs are descriptive summaries and figures used for exploratory interpretation and documentation.

Results from this notebook inform the interpretation of adjusted analyses but are not used directly for modeling.