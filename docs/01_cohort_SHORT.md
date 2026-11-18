# 01 - Non-ICU Hospital Admission Cohort Construction (SHORT)


Full notebook:
[01- Non-ICU Hospital Admission Cohort Construction](../notebooks/01_cohort.ipynb)

## Overview

This notebook constructs the foundational adult, non-ICU hospital admission cohort used in the original association-analysis pipeline (02–04b).
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
   - The cohort is not restricted to one admission per patient, so a patient may contribute multiple admissions.
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
  Final non-ICU admission-level cohort for the original association analyses (02–04b); any ICU stay over the entire admission is excluded.

## Downstream Use

The `nonicu_admissions` table serves as the fixed cohort input for:
- Documented early inpatient RAAS prescription-exposure definition (02)
- Construction of the unified analysis dataset (02, followed by read-only validation in 03a)
- Baseline characteristic summaries (03b)
- Unadjusted outcome analyses (04a)
- Multivariable and adjusted outcome modeling (04b)

Notebooks 03a–04b read the constructed tables without rewriting them; 04b separately applies its documented landmark eligibility filters. The additional prediction-time branch in 04c starts from `base_admissions` and native location/order records, not `nonicu_admissions`. It defines eligibility at each prediction instant and retains later ICU transfers; see [04c SHORT](04c_prediction_time_evaluation_SHORT.md).

## Notes

- No exposure definitions or outcome modeling are performed in this notebook.
- All cohort construction steps are implemented entirely in SQL.
- This separation of cohort definition from modeling supports reproducibility, auditability, and clear data provenance.

## Current execution (2026-11-18)

This notebook was reexecuted successfully with a fresh repository kernel. The [current execution record](CLINICAL_REEXECUTION_615de01.md) covers 8 notebooks / 93 code cells with zero runtime error outputs, connected BigQuery checks and preserved original association estimates. Runtime success is distinct from the nonconverged MLE diagnostics in 04b.

---
## Next Step

Proceed to:
- [02 - Documented Early Inpatient RAAS Prescription-Exposure Definition (Non-ICU Admissions)](02_exposure_SHORT.md)

This next notebook/document briefly describes the next workflow step.
