# Validation Notes

## Scope

The SAS-Python validation workflow checks whether selected aggregate outputs can be reproduced across two analytic platforms. It is a reproducibility exercise, not a separate clinical analysis.

Primary clinical analysis:

- `notebooks/04b_multivariable_outcomes.ipynb`
- Multivariable logistic regression
- Adjusted predicted risks and average marginal effects

Validation notebook:

- `notebooks/05_sas_python_validation.ipynb`
- Compares exported CSV outputs from Python and SAS
- Does not fit a new primary clinical model or define a new estimand

## Files Compared

Unadjusted outcomes:

- Python: `python/outputs/python_unadjusted_outcomes.csv`
- SAS: `sas/outputs/sas_unadjusted_outcomes.csv`
- SAS program: `sas/programs/03_unadjusted_analysis.sas`

Multivariable logistic regression parameters:

- Python: `python/outputs/python_logistic_parameters.csv`
- SAS: `sas/outputs/sas_logistic_parameters.csv`
- SAS program: `sas/programs/04_multivariable_logistic.sas`

## Validation Framing

The repository tracks aggregate validation CSVs only. It does not track patient-level extracts, SAS input CSVs, SAS datasets, local logs, or sensitive credential files.

The validation notebook standardizes variable names and compares coefficients, confidence intervals, odds ratios, p-values, and unadjusted outcome summaries where those fields are available in both platforms.

## Known Discrepancy Notes

The multivariable model includes admission type categories with sparse cells and a rare outcome. These terms are sensitive to implementation details in logistic regression software, especially around intercept handling, reference categories, separation-like behavior, and convergence.

The exposure term is stable across the exported Python and SAS logistic outputs:

- Python exposure OR: 0.3178484462
- SAS exposure OR: 0.3178484462

Observed differences for some admission-type terms should be interpreted as validation diagnostics for sparse-category behavior, not as new clinical findings.

## Infrastructure Sanity Check

`scripts/validation_checklist.py` is separate from SAS-Python output validation. It checks whether expected BigQuery tables are visible in the configured dataset through `INFORMATION_SCHEMA` metadata.

It does not validate:

- Statistical results
- Table contents
- Data quality
- Model outputs
- SAS/Python agreement
