# 04b: Multivariable Outcomes Analysis (Short Summary)

## Purpose
This notebook evaluates the association between early in-hospital exposure to renin–angiotensin–aldosterone system (RAAS) inhibitors and in-hospital mortality among adult non-ICU hospital admissions.

The goal is not causal inference, but to demonstrate how multivariable regression results can be translated into clinically interpretable, risk-based effect measures using real-world hospital data.

## Data and Study Population
The analysis uses the finalized admission-level analysis dataset derived from MIMIC-IV v3.1, restricted to adult, non-ICU hospital admissions (one row per admission).

Early RAAS exposure is defined as any ACE inhibitor or ARB initiated within 24 hours of hospital admission.
The primary outcome is in-hospital mortality, defined by the hospital expiration flag.

## Methods
A multivariable logistic regression model was fitted, adjusting for:
- Age
- Sex
- Race group
- Admission type
- Insurance category
- Calendar period of admission

Categorical variables were one-hot encoded with explicit handling of missing values.
Model performance was evaluated using ROC AUC and precision–recall AUC.

To improve interpretability beyond odds ratios, results were summarized using:
- Average marginal effects (AME)
- Adjusted predicted risks
- Age-specific adjusted risk differences

Statistical uncertainty for marginal effects was quantified using nonparametric bootstrap resampling, repeating the full modeling pipeline for each resample.

## Key Results
Early RAAS exposure was consistently associated with lower in-hospital mortality after multivariable adjustment.

- The adjusted odds ratio for early RAAS exposure indicated substantially lower odds of mortality.
- On the absolute risk scale, early RAAS exposure was associated with an average reduction of approximately 0.38 percentage points in predicted in-hospital mortality.
- Adjusted predicted mortality increased with age in both exposure groups, but the absolute risk difference associated with RAAS exposure widened among older patients.
- Bootstrap confidence intervals for age-specific risk differences remained below zero across most of the adult age range.

## Interpretation
These findings demonstrate how marginal effects and risk differences can complement odds ratios by providing clinically interpretable estimates on the absolute risk scale.

While the observational design precludes causal conclusions, the consistency of results across multiple effect measures supports the robustness of the observed association.
This notebook illustrates a transparent and reproducible approach to multivariable outcome modeling and uncertainty quantification in large clinical datasets.