# 01 - Non-ICU Hospital Admission Cohort Construction (SHORT)

## Overview

This notebook constructs the foundational adult, non-ICU hospital admission cohort used throughout the analysis pipeline.
The objective is to define a clean, admission-level cohort prior to any exposure or outcome modeling, ensuring a transparent and reproducible cohort selection process.

## Data Sources

- MIMIC-IV v3.1 (BigQuery public dataset)
  - hosp.admissions
  - hosp.patients
  - icu.icustays

## Cohort Construction Steps

1. **Base adult admissions**
   - All adult hospital admissions are extracted at the admission (HADM) level.
   - One row per hospital admission is retained.
   - Demographic variables, admission metadata, insurance type, approximate age at admission, and hospital length of stay are included.

2. **Race category collapsing**
   - Raw race labels are collapsed into predefined race groups (White, Black, Hispanic, Asian, Other).
   - This step ensures consistent and stable race categorization prior to cohort restriction and downstream modeling.

3. **Exclusion of ICU admissions**
   - Any hospital admission associated with at least one ICU stay is excluded.
   - The resulting cohort contains only non-ICU adult hospital admissions.

## Outputs

This notebook materializes the following tables in the `mimic-iv-portfolio.nonicu_raas` dataset:

- **base_admissions**  
  Adult hospital admissions table at the HADM level.

- **base_admissions_racegrp**  
  Intermediate table with collapsed race categories.

- **nonicu_admissions**  
  Final non-ICU admission-level cohort used for all downstream analyses.

## Downstream Use

The `nonicu_admissions` table serves as the fixed cohort input for:
- Early RAAS inhibitor exposure definition (02)
- Construction of the unified analysis dataset (03a)
- Baseline characteristic summaries (03b)
- Unadjusted outcome analyses (04a)
- Multivariable and adjusted outcome modeling (04b)

Downstream notebooks load these tables in read-only mode and do not modify cohort inclusion criteria.

## Notes

- No exposure definitions or outcome modeling are performed in this notebook.
- All cohort construction steps are implemented entirely in SQL.
- This separation of cohort definition from modeling supports reproducibility, auditability, and clear data provenance.