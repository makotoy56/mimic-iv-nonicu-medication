# Reproducibility and Analytical Environment

## Project Purpose

This project is a retrospective observational MIMIC-IV clinical analytics workflow evaluating whether documented inpatient RAAS prescription exposure within 24 hours of admission is associated with in-hospital mortality among adult non-ICU hospital admissions.

The analytical purpose is to demonstrate reproducible EHR cohort construction, documented inpatient prescription-exposure classification, multivariable logistic regression, absolute risk interpretation, sensitivity analysis, Python numerical validation, and Quarto-based clinical reporting. The findings are hypothesis-generating associations and are not causal treatment-effect estimates.

## Data Source

The analysis uses MIMIC-IV v3.1 hospital admission data distributed through PhysioNet and accessed through BigQuery.

Patient-level MIMIC-IV source tables, patient-level derived analysis datasets, credentials and local BigQuery configuration are not included in this repository. Reproduction requires independent PhysioNet/MIMIC approval, Google Cloud authentication and BigQuery access.

## Analytical Workflow

The workflow is organized as an admission-level clinical analytics pipeline. The analytic unit is the hospital admission (`hadm_id`), and the cohort is not restricted to one admission per patient.

1. **Cohort construction**: adult hospital admissions are identified and ICU-associated admissions are excluded before exposure or outcome modeling.
   - `sql/01_build_base_hosp_admissions.sql`
   - `sql/01_collapse_race_categories.sql`
   - `sql/02_exclude_icu_admissions.sql`
   - `notebooks/01_cohort.ipynb`
2. **Exposure definition**: documented early inpatient ACE inhibitor or ARB prescription exposure is defined from records with `starttime` from hospital admission through less than 24 hours. This definition does not confirm administration, adherence, outpatient chronic use, or treatment duration.
   - `sql/03_define_exposure_raas_early.sql`
   - `sql/04_check_raas_drugs.sql`
   - `notebooks/02_exposure.ipynb`
3. **Analysis dataset preparation**: the fixed non-ICU cohort, exposure flags, outcome, and covariates are assembled and checked.
   - `sql/03_build_analysis_dataset.sql`
   - `notebooks/03a_validate_input_tables.ipynb`
   - `notebooks/03b_describe_analysis_dataset.ipynb`
4. **Unadjusted analysis**: crude mortality proportions and unadjusted odds ratios are summarized.
   - `notebooks/04a_unadjusted_outcomes.ipynb`
5. **Statistical analysis**: historical unpenalized OR fits remain nonconverged audit diagnostics. Supplementary Firth fits provide finite adjusted ORs; a separate unweighted L2 model provides adjusted risks and average marginal effects.
   - `notebooks/04b_multivariable_outcomes.ipynb`
6. **Sensitivity analysis**: 24-hour landmark and admission-source proxy sensitivity models are evaluated in the multivariable outcomes workflow.
   - `notebooks/04b_multivariable_outcomes.ipynb`
7. **Validation**: synthetic boundary tests, Firth numerical checks, patient-cluster bootstrap diagnostics and patient-disjoint evaluation are implemented in Python. See [current execution evidence](docs/PYTHON_WORKFLOW_VALIDATION.md).
8. **Reporting**: the narrative clinical report is authored in Quarto and rendered to `docs/reports/`.
   - `reports/nonicu_raas_mortality_report.qmd`
   - `_quarto.yml`
   - `docs/reports/nonicu_raas_mortality_report.html`

## Environment Summary

- **Python environment**: The repository now uses uv with Python 3.12, as documented in `docs/SETUP.md`. Project dependencies are specified in `pyproject.toml` and locked in `uv.lock`; they include pandas, NumPy, statsmodels, firthmodels, scikit-learn, matplotlib, and Google BigQuery client libraries.

- **Quarto version**: 1.9.38 detected locally with `quarto --version`. Quarto configuration is stored in `_quarto.yml`, including output to `docs/` and a post-render normalization script.
- **Version control**: Git/GitHub are used for code, documentation, SQL definitions, notebooks, current aggregate Python outputs, curated figures, and rendered portfolio materials.

## Notebook Output Policy

Jupyter notebooks may be rerun locally during development, but notebook outputs, execution counts, generated cell IDs, and volatile notebook metadata are stripped before commit.

The repository uses `nbstripout` as a uv development dependency and a Git clean filter for `*.ipynb` files. After cloning or recreating the environment, install the local Git filter from the repository root:

```bash
uv sync
uv run nbstripout --install --attributes .gitattributes
git config filter.nbstripout.extrakeys 'metadata.kernelspec metadata.language_info.version cell.metadata.execution cell.metadata.vscode cell.metadata.notebookRunGroups'
uv run nbstripout --status
```

Before committing, verify that staged notebook blobs contain no outputs or execution counts. The clean filter applies to Git contents while local executed notebooks retain their saved results.

## Major Analytical Libraries

The project dependency metadata indicates use of:

- pandas
- NumPy
- matplotlib
- statsmodels
- firthmodels (pinned supplementary estimator)
- scikit-learn
- SciPy (same-objective numerical fallback)
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
firthmodels==0.8.2
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
statsmodels>=0.14
scikit-learn>=1.3
scipy>=1.10
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
   uv run python -m ipykernel install --user --name mimic-iv-nonicu-medication-py312 --display-name "Python (MIMIC non-ICU .venv)"
   ```

4. Select the repository `.venv` and run with a fresh kernel for each notebook:
   - `notebooks/00_setup.ipynb`
   - `notebooks/01_cohort.ipynb`
   - `notebooks/02_exposure.ipynb`
   - `notebooks/03a_validate_input_tables.ipynb`
   - `notebooks/03b_describe_analysis_dataset.ipynb`
   - `notebooks/04a_unadjusted_outcomes.ipynb`
   - `notebooks/04b_multivariable_outcomes.ipynb`
5. Render the Quarto report from the repository root:

   ```bash
   quarto render reports/nonicu_raas_mortality_report.qmd
   ```

6. Review the rendered report at `docs/reports/nonicu_raas_mortality_report.html`.

The independent-admission profile intervals and nonconverged Python MLE diagnostics are distinct from the added patient-cluster bootstrap intervals. Patient-disjoint discrimination and bootstrap details are documented in [patient-aware validation](docs/PATIENT_AWARE_VALIDATION.md). Quarto post-render now synchronizes referenced canonical images from `assets/` to `docs/assets/` and rejects missing local resources.

After rendering, run `.venv/bin/python scripts/test_report_consistency.py` to compare current report/narrative values with aggregate CSVs and verify synchronized images. After deployment, run `.venv/bin/python scripts/check_public_report.py` to check live HTML bytes and linked same-site resources.

## Complete workflow verification

The [current Python workflow record](docs/PYTHON_WORKFLOW_VALIDATION.md) and its aggregate JSON receipt document the seven sequential fresh-kernel runs, source hashes and statistical status. Runtime success is separate from MLE nonconvergence. The [reproducible scope](docs/REPRODUCIBLE_SCOPE.md) defines the current public workflow.
