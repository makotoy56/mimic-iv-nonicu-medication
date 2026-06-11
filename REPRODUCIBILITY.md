# Reproducibility and Analytical Environment

## Project Purpose

This project is a retrospective observational MIMIC-IV clinical analytics workflow evaluating whether early inpatient RAAS inhibitor exposure is associated with in-hospital mortality among adult non-ICU hospital admissions.

The analytical purpose is to demonstrate reproducible EHR cohort construction, early medication exposure classification, multivariable logistic regression, absolute risk interpretation, sensitivity analysis, SAS/Python validation, and Quarto-based clinical reporting. The findings are hypothesis-generating associations and are not causal treatment-effect estimates.

## Data Source

The analysis uses MIMIC-IV v3.1 hospital admission data distributed through PhysioNet and accessed through BigQuery.

Patient-level MIMIC-IV source tables, patient-level derived analysis datasets, credentials, local SAS inputs, and local BigQuery configuration are not included in this repository. Reproduction requires independent PhysioNet/MIMIC approval, Google Cloud authentication, BigQuery access, and local SAS configuration if SAS validation is rerun.

## Analytical Workflow

The workflow is organized as an admission-level clinical analytics pipeline:

1. **Cohort construction**: adult hospital admissions are identified and ICU-associated admissions are excluded before exposure or outcome modeling.
   - `sql/01_build_base_hosp_admissions.sql`
   - `sql/01_collapse_race_categories.sql`
   - `sql/02_exclude_icu_admissions.sql`
   - `notebooks/01_cohort.ipynb`
2. **Exposure definition**: early ACE inhibitor or ARB exposure is defined from inpatient prescription orders started within 24 hours after hospital admission.
   - `sql/03_define_exposure_raas_early.sql`
   - `sql/04_check_raas_drugs.sql`
   - `notebooks/02_exposure.ipynb`
3. **Analysis dataset preparation**: the fixed non-ICU cohort, exposure flags, outcome, and covariates are assembled and checked.
   - `sql/03_build_analysis_dataset.sql`
   - `notebooks/03a_validate_input_tables.ipynb`
   - `notebooks/03b_describe_analysis_dataset.ipynb`
4. **Unadjusted analysis**: crude mortality proportions and unadjusted odds ratios are summarized.
   - `notebooks/04a_unadjusted_outcomes.ipynb`
5. **Primary statistical analysis**: multivariable logistic regression estimates adjusted odds ratios, adjusted predicted risks, and average marginal effects.
   - `notebooks/04b_multivariable_outcomes.ipynb`
6. **Sensitivity analysis**: 24-hour landmark and admission-source proxy sensitivity models are evaluated in the multivariable outcomes workflow.
   - `notebooks/04b_multivariable_outcomes.ipynb`
7. **Validation**: exported aggregate Python outputs are compared with SAS-generated outputs for selected unadjusted and logistic model results.
   - `notebooks/05_sas_python_validation.ipynb`
   - `sas/programs/01_import_cohort.sas`
   - `sas/programs/02_baseline_table.sas`
   - `sas/programs/03_unadjusted_analysis.sas`
   - `sas/programs/04_multivariable_logistic.sas`
8. **Reporting**: the narrative clinical report is authored in Quarto and rendered to `docs/reports/`.
   - `reports/nonicu_raas_mortality_report.qmd`
   - `_quarto.yml`
   - `docs/reports/nonicu_raas_mortality_report.html`

## Environment Summary

- **Python environment**: The repository now uses uv with Python 3.12, as documented in `docs/SETUP.md`. Project dependencies are specified in `pyproject.toml` and locked in `uv.lock`; they include pandas, NumPy, statsmodels, scikit-learn, matplotlib, and Google BigQuery client libraries.

- **SAS environment**: SAS® OnDemand for Academics was used for SAS validation workflows. The exact SAS maintenance release was not pinned in the repository.
- **Quarto version**: 1.9.38 detected locally with `quarto --version`. Quarto configuration is stored in `_quarto.yml`, including output to `docs/` and a post-render normalization script.
- **Version control**: Git/GitHub are used for code, documentation, SQL definitions, notebooks, SAS programs, aggregate validation outputs, curated figures, and rendered portfolio materials.

## Major Analytical Libraries

The project dependency metadata indicates use of:

- pandas
- NumPy
- matplotlib
- statsmodels
- scikit-learn
- google-cloud-bigquery
- google-auth
- db-dtypes
- pyarrow
- JupyterLab
- ipykernel

## AI-Assisted Development

This project was developed using an AI-assisted workflow that included ChatGPT and Codex. These tools were used for implementation support, debugging assistance, code review, documentation refinement, and workflow iteration. Final analytical decisions, statistical interpretation, quality control, and reporting remained under investigator review.

## Complete Dependency Specification

The project includes `pyproject.toml` and `uv.lock`. Direct dependencies retain the lower bounds from the original `requirements.txt`; the resolved transitive environment is captured in `uv.lock`.

```text
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
statsmodels>=0.14
scikit-learn>=1.3
google-cloud-bigquery[pandas]>=3.0
google-auth>=2.0
db-dtypes>=1.0
pyarrow>=12.0
jupyterlab>=4.0
ipykernel>=6.0
```

The project targets Python 3.12 with `requires-python = ">=3.12,<3.13"` and `.python-version`.

## Reproduction Steps

1. Obtain independent MIMIC-IV/PhysioNet approval and configure Google Cloud/BigQuery access for MIMIC-IV v3.1.
2. Install uv if it is not already available, then create or update the repository-local environment:

   ```bash
   uv sync
   ```

3. If needed, register the notebook kernel:

   ```bash
   uv run python -m ipykernel install --user --name mimic-portfolio --display-name "Python (mimic-portfolio)"
   ```

4. Run the notebooks in workflow order:
   - `notebooks/00_setup.ipynb`
   - `notebooks/01_cohort.ipynb`
   - `notebooks/02_exposure.ipynb`
   - `notebooks/03a_validate_input_tables.ipynb`
   - `notebooks/03b_describe_analysis_dataset.ipynb`
   - `notebooks/04a_unadjusted_outcomes.ipynb`
   - `notebooks/04b_multivariable_outcomes.ipynb`
   - `notebooks/05_sas_python_validation.ipynb`
5. If SAS validation is being reproduced, run the SAS programs in SAS® OnDemand for Academics or another compatible SAS environment, updating library paths as needed.
6. Render the Quarto report from the repository root:

   ```bash
   quarto render reports/nonicu_raas_mortality_report.qmd
   ```

7. Review the rendered report at `docs/reports/nonicu_raas_mortality_report.html`.
