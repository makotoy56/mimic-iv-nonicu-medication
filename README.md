# Association of Early RAAS Inhibitor Exposure with In-Hospital Mortality
*A Non-ICU Hospital Cohort Study Using MIMIC-IV*

## 🔍 Start Here (Analysis Entry Points)

➡️ **Cohort construction**: [01_cohort.ipynb](notebooks/01_cohort.ipynb) <br>
➡️ **Exposure definition**: [02_exposure.ipynb](notebooks/02_exposure.ipynb)<br>
➡️ **Validate input tables**: [03a_validate_input_tables.ipynb](notebooks/03a_validate_input_tables.ipynb)<br>
➡️ **Describe analysis dataset**: [03b_describe_analysis_dataset.ipynb](notebooks/03b_describe_analysis_dataset.ipynb)<br>
➡️ **Unadjusted Outcomes Overview**: [04a_unadjusted_outcomes.ipynb](notebooks/04a_unadjusted_outcomes.ipynb)<br>
➡️ **Multivariable outcomes**: [04b_multivariable_outcomes.ipynb](notebooks/04b_multivariable_outcomes.ipynb)<br>

📁 **SQL pipelines (BigQuery)**: [sql/](sql/)  
📁 **Stepwise short documentation**: [docs/](docs/)

---

## Technical Snapshot

- **Data**: MIMIC-IV v3.1 (PhysioNet), non-ICU hospital admissions
- **Cohort**: Adult inpatient admissions excluding ICU stays
- **Exposure**: Early RAAS inhibitor use (ACE inhibitors / ARBs within 24 hours of admission)
- **Outcome**: In-hospital mortality
- **Methods**:
  - BigQuery SQL for cohort construction and exposure definition
  - Multivariable logistic regression
  - Absolute risk estimation via average marginal effects
  - Age-stratified risk difference analyses
- **Tools**: BigQuery, Python (pandas, statsmodels), Jupyter

---

## Project Snapshot

- **Population**: Adult non-ICU hospital admissions (MIMIC-IV v3.1)
- **Design**: Retrospective observational cohort study
- **Analysis**: Multivariable logistic regression
- **Key Focus**: Comparison of relative (odds ratios) and absolute (risk differences) effect measures, with emphasis on age-specific absolute risk
- **Key Finding**: Early RAAS inhibitor exposure was associated with a lower adjusted probability of in-hospital mortality, with larger absolute risk reductions among older patients
- **Interpretation**: Observational association; hypothesis-generating

---

## Introduction

Hospitalized patients outside the intensive care unit (ICU) represent a broad and clinically heterogeneous population, ranging from low-acuity admissions to patients at substantial risk of clinical deterioration. Even among non-ICU admissions, in-hospital mortality remains a meaningful outcome influenced by age, comorbidities, and pre-existing medication use. Identifying potentially modifiable factors associated with mortality in this setting is therefore of interest for both clinical epidemiology
and real-world evidence research.

Renin–angiotensin–aldosterone system (RAAS) inhibitors, including angiotensin-converting enzyme inhibitors (ACE inhibitors; ACEi) and angiotensin II receptor blockers (ARBs), are among the most commonly prescribed medications worldwide. While primarily indicated
for cardiovascular and metabolic conditions, these agents also interact with biological pathways related to inflammation, endothelial function, and organ injury, suggesting potential relevance beyond their traditional therapeutic targets [1].

Observational studies in hospitalized populations have reported associations between baseline or early RAAS inhibitor exposure and clinical outcomes in systemic illness, including pneumonia-related outcomes and viral respiratory infections [1–3]. However,
much of this evidence has focused on specific disease contexts or selected patient groups, and comparatively less is known about the association between RAAS inhibitor exposure and outcomes in general, non-ICU hospitalized cohorts.

This portfolio project evaluates the association between early RAAS inhibitor exposure and in-hospital mortality among adult, non-ICU hospital admissions using a reproducible electronic health record (EHR)–based analytic pipeline applied to the MIMIC-IV database.

---

## Background and Rationale

### RAAS inhibition and systemic illness

Beyond blood pressure control, RAAS inhibitors influence multiple physiological processes relevant to acute illness, including vascular tone, inflammatory signaling, and tissue perfusion. Prior population-based and hospital-based observational studies
have suggested that RAAS inhibitor exposure may be associated with improved outcomes in systemic infections and respiratory illnesses, including pneumonia and COVID-19 [1–3].

During the COVID-19 pandemic, large observational studies demonstrated that RAAS inhibitors were not associated with increased risk of infection or adverse outcomes, supporting the clinical safety of continued RAAS inhibitor use during acute illness [2,3]. These findings have reinforced interest in understanding the broader role of RAAS inhibition in hospitalized populations beyond disease-specific contexts.

However, existing studies have primarily focused on ICU populations, specific diagnoses, or pandemic-related cohorts. Comparatively less attention has been paid to general, non-ICU hospital admissions, despite their clinical heterogeneity and
substantial contribution to overall inpatient mortality. Given the high prevalence of RAAS inhibitor use and the size of non-ICU populations, this setting provides an important opportunity to examine associations on both relative and absolute risk
scales in a real-world context.

---

## Study Objective

The primary objective of this analysis is to evaluate whether early RAAS inhibitor exposure is associated with differences in in-hospital mortality among adult, non-ICU hospital admissions.

Secondary objectives include:
- Estimation of absolute risk differences using average marginal effects
- Evaluation of age-specific risk differences
- Comparison of relative (odds ratio) and absolute (risk difference) effect measures within a unified modeling framework

---

## Research Question

Among adult, non-ICU hospital admissions in MIMIC-IV, is early exposure to RAAS inhibitors associated with differences in in-hospital mortality after multivariable adjustment?

---

## Project Structure
````text
mimic-iv-nonicu-medication-private/
├── notebooks/        # Stepwise analysis notebooks (00–04b)
│   ├── 00_setup.ipynb
│   ├── 01_cohort.ipynb
│   ├── 02_exposure.ipynb
│   ├── 03a_validate_input_tables.ipynb
│   ├── 03b_describe_analysis_dataset.ipynb
│   ├── 04a_unadjusted_outcomes.ipynb
│   └── 04b_multivariable_outcomes.ipynb
│
├── sql/              # Reproducible BigQuery SQL pipelines
│   ├── 01_build_base_hosp_admissions.sql
│   ├── 01_collapse_race_categories.sql
│   ├── 02_exclude_icu_admissions.sql
│   ├── 03_build_analysis_dataset.sql
│   ├── 03_define_exposure_raas_early.sql
│   └── 04_check_raas_drugs.sql
│
├── docs/             # Lightweight documentation (SHORT summaries)
│   ├── 01_cohort_SHORT.md
│   ├── 02_exposure_SHORT.md
│   ├── 03a_validate_input_tables_SHORT.md
│   ├── 03b_describe_analysis_dataset_SHORT.md
│   ├── 04a_unadjusted_outcomes_SHORT.md
│   └── 04b_multivariable_outcomes_SHORT.md
│
├── data/             # Local analysis artifacts (minimal / excluded)
│   ├── interim/
│   └── processed/
│
├── .github/          # Repository configuration
├── .gitignore
└── README.md

````

---

## Methods Overview

Cohort construction, exposure definition, baseline covariate assembly, and outcome derivation were implemented using a combination of SQL (BigQuery-compatible) and Python-based processing.

Core cohort tables were generated entirely via SQL to ensure reproducibility and transparency, while downstream validation, modeling, and visualization were performed in structured Python notebooks.

Modeling strategies and estimands were defined prior to outcome modeling and applied consistently across analyses.

---

## Exposure Definition

Early RAAS inhibitor exposure was defined using inpatient medication prescription records from the MIMIC-IV prescriptions table.

Patients were classified as RAAS inhibitor exposed if they had at least one prescription for an angiotensin-converting enzyme inhibitor (ACE inhibitor) or angiotensin II receptor blocker (ARB) with a documented medication start time occurring on or after hospital admission and within the first 24 hours of admission. All other patients were classified as not exposed to RAAS inhibitors.

To preserve temporal ordering and reduce the risk of reverse causation, exposure ascertainment was restricted to this early-in-admission window, prior to the occurrence of in-hospital mortality or other downstream clinical events.

RAAS inhibitor exposure was further categorized as:
- ACE inhibitor exposure only
- ARB exposure only
- Exposure to either ACE inhibitors or ARBs

Sensitivity analyses and subgroup definitions, including alternative exposure specifications, are documented in the corresponding analysis notebooks.

---

## Modeling and Validation

Primary analyses used multivariable logistic regression to estimate the association between early RAAS exposure and in-hospital mortality.

In addition to odds ratios, absolute risk measures were emphasized through:

- Adjusted predicted mortality risks
- Average marginal effects (risk differences)
- Age-specific risk difference estimation with bootstrap-based confidence intervals

Model performance was evaluated using ROC AUC and precision–recall AUC, and internal consistency checks were conducted throughout the analytic pipeline.

---

## Results

### Cohort characteristics

The final analytic cohort consisted of adult, non-ICU hospital admissions derived from MIMIC-IV. Patients receiving early RAAS inhibitors differed from unexposed patients in baseline characteristics, reflecting the underlying burden of cardiovascular comorbidity. These differences were addressed through multivariable adjustment.

### Association between RAAS exposure and in-hospital mortality

After multivariable adjustment, early RAAS exposure was associated with a lower estimated probability of in-hospital mortality. This association was observed consistently across relative (odds ratio) and absolute (risk difference) effect measures.

### Absolute risk and age-specific effects

Although the baseline mortality rate was low in this non-ICU population, the estimated absolute risk reduction associated with early RAAS exposure was clinically interpretable and increased with age. Age-specific analyses demonstrated widening absolute risk differences among older patients.


## Interpretation and Limitations

This analysis is observational and does not establish causality. Despite careful temporal ordering and multivariable adjustment, residual confounding by indication and unmeasured clinical severity may remain.

Accordingly, the results should be interpreted as evidence of association rather than causal effect. The primary value of this work lies in its transparent, reproducible analytic design and its demonstration of complementary use of relative and absolute risk measures in large EHR-based cohorts.


## Data Source and Compliance

This project uses data from the Medical Information Mart for Intensive Care IV (MIMIC-IV) database (version 3.1), maintained by the MIT Laboratory for Computational Physiology and distributed via PhysioNet.

Required citation:
Johnson A., Bulgarelli L., Pollard T., Gow B., Moody B., Horng S., Celi L.A., & Mark R. (2024).
MIMIC-IV (version 3.1). PhysioNet. RRID:SCR_007345.
https://doi.org/10.13026/kpb9-mt58

This repository contains no patient-level data. All analyses were conducted within approved MIMIC-IV environments, and only code and aggregate descriptions are shared.

## References

1. Mortensen EM, et al.  
   Population-Based Study of Statins, Angiotensin II Receptor Blockers, and Angiotensin-Converting Enzyme Inhibitors on Pneumonia-Related Outcomes.  
   *Clinical Infectious Diseases*. 2012.

2. Mancia G, et al.  
   Renin–Angiotensin–Aldosterone System Blockers and the Risk of Covid-19.  
   *New England Journal of Medicine*. 2020.

3. Reynolds HR, et al.  
   Renin–Angiotensin–Aldosterone System Inhibitors and Risk of Covid-19.  
   *New England Journal of Medicine*. 2020.