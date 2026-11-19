# 02 – Documented Early Inpatient RAAS Prescription-Exposure Definition (Non-ICU Admissions)


Full notebook:
[02. Build Non-ICU RAAS Early Exposure Tables](../notebooks/02_exposure.ipynb)

## Overview

This notebook defines documented early inpatient renin–angiotensin–aldosterone system (RAAS) prescription exposure for non-ICU adult hospital admissions using MIMIC-IV v3.1 data.

Using SQL-based preprocessing in BigQuery, inpatient prescription records are linked to hospital admissions to identify documented ACE inhibitor and angiotensin receptor blocker (ARB) prescription exposure within a fixed time window after admission.

The resulting exposure indicators are constructed at the hospital admission (HADM) level and serve as fixed inputs for downstream descriptive analyses and multivariable outcome modeling.

## Purpose

The purpose of this notebook is to construct documented early inpatient RAAS prescription-exposure variables for the finalized non-ICU admission cohort.

Specifically, this notebook:

- Defines documented early RAAS prescription exposure from records with `starttime` from hospital admission through less than 24 hours
- Constructs binary admission-level indicators for:
  - Documented early ACE inhibitor prescription exposure
  - Documented early ARB prescription exposure
  - Records from both drug classes in the same early window
  - Composite documented early RAAS prescription exposure (any ACEi or ARB)
- Materializes exposure tables in BigQuery for downstream analytic use  

This notebook performs **data construction and validation only** and does not conduct baseline summaries, outcome comparisons, or statistical modeling.

## Data Sources

**Primary datasets**

- MIMIC-IV v3.1 (BigQuery public dataset)  
- Project: `mimic-iv-portfolio`

**Source tables**

- `physionet-data.mimiciv_3_1_hosp.prescriptions`  
- `mimic-iv-portfolio.nonicu_raas.nonicu_admissions`  
  (constructed in 01 via ICU exclusion)

## Exposure Definition

Documented early inpatient RAAS prescription exposure is defined as any ACE inhibitor or ARB prescription record with `starttime` on or after hospital admission and before **24 hours after hospital admission time**.

Exposure is operationalized using prescription start timestamps relative to admission time. It does not confirm medication administration and does not measure outpatient chronic use, adherence, dose, treatment indication, or duration.

Both-class flags do not require overlapping prescriptions and do not establish simultaneous treatment, co-administration or actual administration.

The following binary indicators are constructed at the admission level:

- `acei_early`: early ACE inhibitor exposure  
- `arb_early`: early ARB exposure  
- `raas_both_early`: both ACE inhibitor and ARB prescription-record flags in the same 0–<24-hour window
- `raas_any_early`: any documented early RAAS prescription exposure

## Outputs

Execution of the SQL scripts in this notebook materializes the following tables in  
`mimic-iv-portfolio.nonicu_raas`:

- **exposure_raas_early**  
  An admission-level table encoding documented early inpatient RAAS prescription-exposure indicators (`acei_early`, `arb_early`, `raas_both_early`, `raas_any_early`).

- **analysis_dataset**  
  A unified analytic dataset created by left-joining the non-ICU admission cohort with documented early RAAS prescription-exposure indicators on `(subject_id, hadm_id)`.
  All admissions are retained, with non-exposed admissions explicitly coded as zero.

These tables are constructed entirely via SQL and treated as finalized exposure-definition outputs.

## Sanity Checks

The following internal checks are performed to validate exposure construction:

- Distribution of documented early RAAS prescription-exposure indicators
- Logical consistency between component indicators and composite variables  
- Verification that exposure tables and cohort tables contain identical admission counts  

These checks confirm complete alignment between the non-ICU cohort and exposure tables, with no loss of admissions during construction.

## Downstream Use

The `analysis_dataset` table produced in this notebook is the analysis input for the original association branch, including:

- Baseline characteristic summaries (03b)  
- Unadjusted outcome analyses (04a)  
- Multivariable and adjusted outcome modeling (04b)  

Downstream association notebooks read these tables without changing the exposure definition; 04b separately applies its documented landmark eligibility filters. The additional 04c prediction branch uses the adult base and native transfer/order records. Its 24h companion requires both an early prescription start and a linked POE order time by 24h, so it does not reuse this exposure flag as evidence of information available at prediction time. See [04c SHORT](04c_prediction_time_evaluation_SHORT.md).

## Current execution (2026-11-18)

This notebook was reexecuted successfully with a fresh repository kernel on 2026-11-19. The [current execution record](CLINICAL_REEXECUTION_20261119.md) covers all 8 notebooks / 109 code cells with zero runtime error outputs, live Python-generated displays, connected BigQuery checks and preserved association estimates. Runtime success is distinct from the nonconverged MLE diagnostics in 04b.

---
## Next Step

Proceed to:
- [03a - Validation of Analysis Input Tables (SHORT)](03a_validate_input_tables_SHORT.md)

This next notebook/document briefly describes the next workflow step.
