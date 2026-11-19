# 03a - Validation of Analysis Input Tables (SHORT)


Full notebook:
[03a. Input Table Validation and Descriptive Summary](../notebooks/03a_validate_input_tables.ipynb)

## Overview

This notebook performs structural validation and basic descriptive checks of the intermediate tables used to construct the final admission-level analysis dataset.
It serves as a quality-control step prior to baseline description and outcome modeling.

No cohort construction, exposure definition, or data modification is performed in this notebook.
All tables are loaded in read-only mode from BigQuery.

## Purpose

The objectives of this notebook are to:

- Verify one-to-one correspondence between rows and hospital admissions (HADM-level)
- Confirm alignment between the non-ICU cohort table and the documented early inpatient RAAS prescription-exposure table
- Check data types, missingness, and internal consistency of exposure indicators
- Ensure the analysis dataset is structurally sound before downstream modeling

## Input Tables

The following pre-materialized BigQuery tables are loaded:

- **nonicu_admissions**  
  Admission-level non-ICU cohort table created upstream via ICU exclusion.

- **exposure_raas_early**  
  Admission-level table encoding documented early inpatient ACEi, ARB, and composite prescription-exposure indicators.

Both tables are expected to contain exactly one row per hospital admission, identified by `(subject_id, hadm_id)`.

## Validation Checks Performed

This notebook confirms that:

- Row counts match exactly between cohort and exposure tables
- All admissions in the cohort have corresponding exposure records
- Exposure indicators (`acei_early`, `arb_early`, `raas_any_early`, `raas_both_early`) are complete and internally consistent
- No unexpected missingness is present in key identifiers or exposure variables
- Demographic variables (including collapsed race groups) are populated as expected

## Outputs

No new tables are created.
The notebook produces only printed summaries and sanity-check outputs to document data integrity.

## Downstream Use

The validated tables serve as stable inputs for subsequent notebooks, including:

- Baseline descriptive summaries (03b)
- Unadjusted outcome analyses (04a)
- Multivariable and marginal-effect outcome modeling (04b)

These checks cover the original association branch (03b–04b). The analysis table was constructed upstream in notebook 02 via `sql/03_build_analysis_dataset.sql`; 03a is read-only. The separate 04c prediction branch performs its own time-specific eligibility and native-transfer checks; see [04c SHORT](04c_prediction_time_evaluation_SHORT.md).

## Current execution (2026-11-18)

This notebook was reexecuted successfully with a fresh repository kernel on 2026-11-19. The [current execution record](CLINICAL_REEXECUTION_20261119.md) covers all 8 notebooks / 109 code cells with zero runtime error outputs, live Python-generated displays, connected BigQuery checks and preserved association estimates. Runtime success is distinct from the nonconverged MLE diagnostics in 04b.

---
## Next Step

Proceed to:
- [03b - Describe Analysis Dataset (Baseline Characteristics)](03b_describe_analysis_dataset_SHORT.md)

This next notebook/document briefly describes the next workflow step.
