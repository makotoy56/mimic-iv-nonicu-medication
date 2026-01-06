# 03a - Validation of Analysis Input Tables (SHORT)

## Overview

This notebook performs structural validation and basic descriptive checks of the intermediate tables used to construct the final admission-level analysis dataset.
It serves as a quality-control step prior to baseline description and outcome modeling.

No cohort construction, exposure definition, or data modification is performed in this notebook.
All tables are loaded in read-only mode from BigQuery.

## Purpose

The objectives of this notebook are to:

- Verify one-to-one correspondence between rows and hospital admissions (HADM-level)
- Confirm alignment between the non-ICU cohort table and the early RAAS exposure table
- Check data types, missingness, and internal consistency of exposure indicators
- Ensure the analysis dataset is structurally sound before downstream modeling

## Input Tables

The following pre-materialized BigQuery tables are loaded:

- **nonicu_admissions**  
  Admission-level non-ICU cohort table created upstream via ICU exclusion.

- **exposure_raas_early**  
  Admission-level early RAAS inhibitor exposure table encoding ACEi, ARB, and composite exposure indicators.

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

This step ensures that all downstream analyses operate on a consistent, verified analytic dataset.