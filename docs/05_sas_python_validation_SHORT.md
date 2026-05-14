# 05 - SAS-Python Reproducibility Validation


Full notebook:
[05. SAS-Python Cross-Platform Validation](../notebooks/05_sas_python_validation.ipynb)

## Overview

This notebook compares selected aggregate outputs generated independently in Python and SAS for the non-ICU RAAS medication analysis.

It is a reproducibility validation step only. It does not define a new cohort, construct a new exposure, fit a new primary clinical model, or change the interpretation of the clinical analysis.

## Files Compared

Unadjusted outcomes:

- Python output: `python/outputs/python_unadjusted_outcomes.csv`
- SAS output: `sas/outputs/sas_unadjusted_outcomes.csv`
- SAS program: `sas/programs/03_unadjusted_analysis.sas`

Multivariable logistic parameters:

- Python output: `python/outputs/python_logistic_parameters.csv`
- SAS output: `sas/outputs/sas_logistic_parameters.csv`
- SAS program: `sas/programs/04_multivariable_logistic.sas`

## Validation Purpose

The notebook checks whether key aggregate statistics align across platforms, including:

- Unadjusted counts and mortality proportions
- Crude odds and crude odds ratios
- Logistic regression coefficients
- Odds ratios and confidence intervals
- p-values where available

## Interpretation

The primary clinical analysis remains the multivariable logistic regression and absolute risk estimation in `04b_multivariable_outcomes.ipynb`.

SAS-Python comparison supports reproducibility of selected exported outputs. Any sparse-category discrepancies are treated as validation diagnostics, not as new clinical findings.

## Data Protection

Only aggregate outputs are tracked in the repository. Patient-level data, local SAS input extracts, credentials, logs, and local data files are excluded by `.gitignore`.

---
## Next Step

Proceed to:
- [Repository README](../README.md)

This next notebook/document briefly describes the next workflow step.
