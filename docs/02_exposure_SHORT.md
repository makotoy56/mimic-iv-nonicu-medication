# 02 – Early RAAS Exposure Definition (Non-ICU Admissions)

## Overview

This notebook defines early renin–angiotensin–aldosterone system (RAAS) inhibitor exposure for non-ICU adult hospital admissions using MIMIC-IV v3.1 data.

Using SQL-based preprocessing in BigQuery, medication prescription records are linked to hospital admissions to identify early exposure to angiotensin-converting enzyme inhibitors (ACE inhibitors) and angiotensin receptor blockers (ARBs) within a fixed time window after admission.

The resulting exposure indicators are constructed at the hospital admission (HADM) level and serve as fixed inputs for downstream descriptive analyses and multivariable outcome modeling.

## Purpose

The purpose of this notebook is to construct early RAAS inhibitor exposure variables for the finalized non-ICU admission cohort.

Specifically, this notebook:

- Defines early RAAS exposure based on medication prescriptions initiated within 24 hours after hospital admission  
- Constructs binary admission-level indicators for:
  - Early ACE inhibitor use  
  - Early ARB use  
  - Concurrent early use of both drug classes  
  - Composite early RAAS exposure (any ACEi or ARB)  
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

Early RAAS inhibitor exposure is defined as any ACE inhibitor or ARB prescription with a recorded start time occurring within **24 hours after hospital admission time**.

Exposure is operationalized using prescription start timestamps relative to admission time, without conditioning on duration or dose.

The following binary indicators are constructed at the admission level:

- `acei_early`: early ACE inhibitor exposure  
- `arb_early`: early ARB exposure  
- `raas_both_early`: concurrent early ACE inhibitor and ARB exposure  
- `raas_any_early`: any early RAAS inhibitor exposure  

## Outputs

Execution of the SQL scripts in this notebook materializes the following tables in  
`mimic-iv-portfolio.nonicu_raas`:

- **exposure_raas_early**  
  An admission-level table encoding early RAAS inhibitor exposure indicators (`acei_early`, `arb_early`, `raas_both_early`, `raas_any_early`).

- **analysis_dataset**  
  A unified analytic dataset created by left-joining the non-ICU admission cohort with early RAAS exposure indicators on `(subject_id, hadm_id)`.  
  All admissions are retained, with non-exposed admissions explicitly coded as zero.

These tables are constructed entirely via SQL and treated as finalized exposure-definition outputs.

## Sanity Checks

The following internal checks are performed to validate exposure construction:

- Distribution of early RAAS exposure indicators  
- Logical consistency between component indicators and composite variables  
- Verification that exposure tables and cohort tables contain identical admission counts  

These checks confirm complete alignment between the non-ICU cohort and exposure tables, with no loss of admissions during construction.

## Downstream Use

The `analysis_dataset` table produced in this notebook serves as the sole input for subsequent analyses, including:

- Baseline characteristic summaries (03b)  
- Unadjusted outcome analyses (04a)  
- Multivariable and adjusted outcome modeling (04b)  

Downstream notebooks load these tables in read-only mode and do not modify exposure definitions or cohort inclusion criteria, ensuring reproducibility and transparent data provenance.