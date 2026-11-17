# Documented Early Inpatient RAAS Prescription Exposure and In-Hospital Mortality in Non-ICU Admissions

*A reproducible MIMIC-IV clinical analytics portfolio project*

Makoto Yoshida, PhD<br>
Clinical Data Analytics Portfolio<br>
LinkedIn: https://www.linkedin.com/in/makoto-yoshida/

## Overview

This repository presents an EHR-based retrospective cohort study using MIMIC-IV v3.1. It evaluates whether documented inpatient renin-angiotensin-aldosterone system (RAAS) prescription exposure within the first 24 hours of admission is associated with in-hospital mortality among adult non-ICU hospital admissions.

The primary clinical analysis is multivariable logistic regression with absolute risk estimation using average marginal effects. Findings are interpreted as hypothesis-generating associations, not causal effects.

The analytic unit is the hospital admission (`hadm_id`). The cohort is not restricted to one admission per patient, so a patient may contribute multiple qualifying admissions.

## Portfolio Report

For a portfolio-style clinical analytics report presenting the study background, methods, results, interpretation, limitations, and reproducibility workflow:

➡️ [View the Quarto HTML report](https://makotoy56.github.io/mimic-iv-nonicu-medication/reports/nonicu_raas_mortality_report.html)

This README provides the repository overview and technical navigation.

## Reviewer Path

For a quick review:

1. Read the Study Snapshot and Key Findings.
2. Review the representative figures, including the 24-hour landmark sensitivity analysis.
3. Open the Quarto report for methods, results, and interpretation.
4. Inspect the cohort-construction and modeling notebooks for implementation details.

## What This Demonstrates

- Real-world evidence workflow using hospital EHR data
- Reproducible cohort, exposure, covariate, and outcome construction in BigQuery SQL
- Transparent documented inpatient prescription-exposure definition using ACE inhibitor and ARB records with start times within 24 hours of admission
- Multivariable logistic regression with odds ratios, adjusted risks, and average marginal effects
- Cross-platform validation of selected unadjusted and logistic model outputs
- Clear separation between clinical analysis, validation artifacts, and compliance-safe repository contents

## Workflow

![Analysis workflow](assets/workflow_diagram.svg)

For the detailed source-table-to-analysis-dataset lineage, see the [Quarto HTML report section on source tables and project-created analysis tables](https://makotoy56.github.io/mimic-iv-nonicu-medication/reports/nonicu_raas_mortality_report.html#source-tables-to-analysis-dataset).

## Why This Project Matters

This project shows how clinical analytics teams can move from raw EHR tables to an auditable real-world evidence workflow. It emphasizes transparent cohort, exposure, covariate, and outcome definitions; multivariable regression; and absolute risk interpretation for findings that need to be understandable beyond a purely statistical audience.

For clinical analytics, RWE, HEOR, and outcomes research teams, the portfolio value is the operational workflow: defensible data definitions, documented modeling choices, reproducible notebooks, and SAS/Python output checks. Limitations, including residual confounding and non-causal interpretation, are documented in the [discussion](docs/DISCUSSION_AND_LIMITATIONS.md).

## Key Findings

**Inference status:** Historical unpenalized primary/sensitivity fits have separation and remain nonconverged audit outputs. Supplementary Firth fits all converged. Current intervals below resample patients to account for repeated admissions; the original profile intervals are retained separately. Discrimination and absolute risks use separate L2 models.

- The analytic cohort included 460,786 adult non-ICU hospital admissions.
- Documented inpatient RAAS prescription exposure within 24 hours occurred in 56,825 admissions, or 12.33% of the cohort.
- Crude in-hospital mortality was lower among admissions with documented early RAAS prescription exposure than among admissions without it.
- The Firth sensitivity fit on the primary cohort returned OR 0.319 (95% patient-cluster CI 0.267–0.380). The original unpenalized primary output remains historical and nonconverged.
- The unweighted L2 risk model produced AME -0.3797 percentage points (95% patient-cluster CI -0.4201 to -0.3407).
- Age-specific predictions at a typical mean covariate profile showed larger absolute contrasts at older ages; no exposure-by-age interaction was fitted.
- The corrected 24-hour cohort contains 342,519 admissions and 1,769 deaths. Its Firth ordinary/proxy ORs were 0.356 (95% patient-cluster CI 0.292–0.423) and 0.382 (0.315–0.453); both fits converged.

**Reviewer interpretation:** The OR of approximately 0.32 and the model-predicted mortality difference are observational associations, not evidence that RAAS inhibitors caused lower mortality. Treatment eligibility, confounding by indication, early clinical stability, clinician prescribing behavior, and unmeasured clinical severity may affect the estimates. The landmark analyses address one timing-related bias concern but do not establish causality.

See [Results summary](docs/RESULTS_SUMMARY.md) and [Discussion and limitations](docs/DISCUSSION_AND_LIMITATIONS.md) for interpretation details.

## Results Visualizations

The README uses three figures to keep the result flow concise: observed outcome contrast, adjusted absolute-risk interpretation, and the 24-hour landmark sensitivity context. Technical validation remains in the reproducibility documentation rather than the main visual narrative.

### Crude Outcome Comparison

Observed in-hospital mortality was lower among admissions with documented early inpatient RAAS prescription exposure than among admissions without documented exposure.

<img src="assets/unadjusted_mortality_by_raas.png" alt="Unadjusted in-hospital mortality by documented early inpatient RAAS prescription exposure" width="760">

### Adjusted Absolute Risk Interpretation

The unweighted L2 model contrasts exposure scenarios at a typical mean covariate profile. The intervals below resample entire patients; age-varying absolute contrasts are not a formal interaction test.

<img src="assets/absolute_risk_difference_patient_bootstrap.png" alt="Age-specific typical-profile risk differences with 95 percent patient-cluster bootstrap intervals" width="760">

### 24-Hour Landmark Sensitivity Analysis

**Patient-aware update (2026-11-17):** Current uncertainty summaries use 500 prespecified patient-cluster bootstrap draws, carrying all eligible admissions per sampled patient. Firth point estimates and all exposure/cohort/adjustment definitions are unchanged. Historical admission-independent profile intervals remain available separately. See [patient-aware validation](docs/PATIENT_AWARE_VALIDATION.md).

The full-data Firth point fits passed convergence, rank, profile-bound and independent adjusted-score checks. The new figure uses patient-cluster percentile intervals; [original profile figure](assets/firth_landmark_sensitivity.png) and [Firth numerical validation](docs/FIRTH_SENSITIVITY_VALIDATION.md) remain available.

The corrected rule requires confirmed survival and continued hospitalization beyond 24 hours, removing 117,637 early live discharges plus separately counted inconsistent records. The figure below explicitly uses the supplementary Firth estimator. Historical unpenalized OR assets are retained unchanged for audit.

<img src="assets/firth_landmark_patient_bootstrap.png" alt="Supplementary Firth odds ratios with 95 percent patient-cluster bootstrap intervals" width="760">

### Patient-Disjoint Discrimination

| Validation | Train / test admissions | Test deaths | Overlapping patients | ROC AUC | PR AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Admission-random reference | 368,628 / 92,158 | 465 | 42,796 | 0.857576 | 0.106915 |
| Patient-disjoint holdout | 368,309 / 92,477 | 468 | 0 | 0.860635 | 0.117607 |

The additional patient-disjoint holdout has zero train/test patient overlap. Scaling and categorical encoding are fitted on training data only. These are single splits with different case mixes, so their metric difference is not evidence of improved model performance. See [patient-aware validation](docs/PATIENT_AWARE_VALIDATION.md).

## Study Snapshot

| Area | Details |
| --- | --- |
| Data | MIMIC-IV v3.1 hospital admissions |
| Design | Retrospective observational cohort study |
| Population | Adult hospital admissions, including observation categories, excluding any ICU stay |
| Analytic unit | Hospital admission (`hadm_id`); patients may contribute multiple admissions |
| Exposure | Documented inpatient ACE inhibitor or ARB prescription with recorded start time from admission through less than 24 hours |
| Primary outcome | In-hospital mortality |
| Original primary model | Unpenalized multivariable logistic regression; nonconverged audit output |
| Supplementary OR estimator | Firth logistic regression; patient-cluster bootstrap intervals |
| Absolute risk estimand | Adjusted predicted risks and average marginal effects |
| Validation | Patient-cluster uncertainty and patient-disjoint holdout; historical SAS-Python aggregate agreement |
| Tools | BigQuery SQL, Python, Jupyter, SAS |

Exposure is based on inpatient prescription records. It does not confirm medication administration and does not directly capture outpatient chronic use, adherence, dose, treatment indication, or duration.

## Explore The Project

- [00 setup and source-access checks](notebooks/00_setup.ipynb)
- [01 cohort construction](notebooks/01_cohort.ipynb) and [short notes](docs/01_cohort_SHORT.md)
- [02 exposure definition](notebooks/02_exposure.ipynb) and [short notes](docs/02_exposure_SHORT.md)
- [03a input table validation](notebooks/03a_validate_input_tables.ipynb) and [short notes](docs/03a_validate_input_tables_SHORT.md)
- [03b analysis dataset description](notebooks/03b_describe_analysis_dataset.ipynb) and [short notes](docs/03b_describe_analysis_dataset_SHORT.md)
- [04a unadjusted outcomes](notebooks/04a_unadjusted_outcomes.ipynb) and [short notes](docs/04a_unadjusted_outcomes_SHORT.md)
- [04b multivariable outcomes](notebooks/04b_multivariable_outcomes.ipynb) and [short notes](docs/04b_multivariable_outcomes_SHORT.md)
- [05 SAS-Python reproducibility validation](notebooks/05_sas_python_validation.ipynb) and [short notes](docs/05_sas_python_validation_SHORT.md)
- [SAS programs](sas/programs/) and [SAS workflow notes](sas/README.md)
- [BigQuery SQL](sql/) and [infrastructure sanity check](scripts/validation_checklist.py)

## Detailed Documentation

- [Study background](docs/STUDY_BACKGROUND.md): RAAS biology, hospital medicine rationale, and prior literature
- [Methods overview](docs/METHODS_OVERVIEW.md): design, cohort, exposure, outcome, covariates, and modeling plan
- [Results summary](docs/RESULTS_SUMMARY.md): concise findings without causal strengthening
- [Discussion and limitations](docs/DISCUSSION_AND_LIMITATIONS.md): interpretation, residual confounding, and generalizability
- [Setup and reproducibility](docs/SETUP.md): Python environment, notebook execution expectations, and hygiene guidance
- [Validation notes](docs/VALIDATION_NOTES.md): Python/SAS validation scope and discrepancy notes
- [Figure reproducibility](docs/FIGURE_REPRODUCIBILITY.md): README figure export locations and refresh workflow

## Reproducibility And Validation

The workflow uses version-controlled notebooks, SQL scripts, SAS programs, and aggregate validation CSVs. No patient-level data are included in this repository. See [Setup and reproducibility](docs/SETUP.md) for the uv-managed Python environment and notebook hygiene workflow.

For complete environment and reproducibility details, see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

The latest [complete 00–05 execution record](docs/NOTEBOOK_RUN_VALIDATION.md) confirms eight sequential fresh-kernel runs and zero runtime error outputs. Statistical convergence and SAS discrepancy checks are recorded separately; the historical MLE remains nonconverged.

Validation scope:

- `04b_multivariable_outcomes.ipynb` contains the primary clinical analysis: multivariable logistic regression and absolute risk estimation.
- `05_sas_python_validation.ipynb` compares exported Python and SAS outputs; it is reproducibility validation, not a new clinical analysis.
- SAS programs under `sas/programs/` generate comparison outputs under `sas/outputs/`.
- Python validation artifacts are stored under `python/outputs/`.
- `scripts/validation_checklist.py` performs lightweight BigQuery table-existence checks only; it does not validate table contents or statistical results.

MIMIC-IV/PhysioNet access, Google Cloud authentication, BigQuery access, and local SAS paths are configured outside the repository.

## Project Structure

```text
mimic-iv-nonicu-medication/
|-- assets/           # Portfolio visuals
|-- docs/             # Study background, methods, results, limitations, validation notes
|-- notebooks/        # Stepwise analysis and validation notebooks
|-- pyproject.toml    # uv project dependency metadata
|-- python/outputs/   # Aggregate Python validation CSVs
|-- sas/              # SAS workflow notes, programs, and aggregate validation outputs
|-- scripts/          # Validation utilities
|-- sql/              # BigQuery SQL for cohort/exposure construction
|-- uv.lock           # uv-resolved dependency lockfile
`-- README.md
```

## Data Source And Compliance

This project uses MIMIC-IV v3.1, maintained by the MIT Laboratory for Computational Physiology and made available via PhysioNet.

Johnson A., Bulgarelli L., Pollard T., Gow B., Moody B., Horng S., Celi L.A., & Mark R. (2024). *MIMIC-IV (version 3.1)*. PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/kpb9-mt58.

Access was granted after required training and approval under the PhysioNet data use agreement. This repository contains no patient-level data.
