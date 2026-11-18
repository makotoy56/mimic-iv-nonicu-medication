# Setup And Reproducibility

This repository is a portfolio-focused analysis project, not a packaged production application. The setup below is intended to make notebook review and selective reruns reproducible without tracking patient-level data or local credentials.

## Python Environment

The repository uses uv with Python 3.12. The project metadata is stored in `pyproject.toml`, the resolved dependency set is stored in `uv.lock`, and `.python-version` pins the local interpreter preference to Python 3.12.

```bash
uv sync
uv run python -m ipykernel install --user --name mimic-iv-nonicu-medication-py312 --display-name "Python (MIMIC non-ICU .venv)"
```

Select this repository’s `.venv/bin/python` in VS Code. A shared `mimic-portfolio` registration may point to an older environment; the optional registration above uses a project-specific name. A repository-local `.venv/` is ignored by git and may be created by `uv sync`; do not commit virtual environment contents. Existing local virtual environments do not need to be deleted for this workflow.

To add or update Python dependencies, use `uv add` from the repository root so `pyproject.toml` and `uv.lock` stay in sync.

## Data And Credential Expectations

The repository does not include MIMIC-IV tables, local extracts, credentials or patient-level data. Full notebook execution requires:

- PhysioNet/MIMIC-IV access and compliance with the MIMIC data use agreement.
- Google Cloud authentication with BigQuery access to the configured MIMIC-IV project/dataset.

The tracked CSV files under `python/outputs/` are aggregate validation artifacts only.

## Notebook Execution

Run in order: 00 → 01 → 02 → 03a → 03b → 04a → 04b, using the repository `.venv` and a fresh kernel for each notebook.

1. `00_setup.ipynb` validates the interpreter, existing ADC and source access.
2. `01_cohort.ipynb` through `03b_describe_analysis_dataset.ipynb` build and inspect the analysis tables.
3. `04a_unadjusted_outcomes.ipynb` and `04b_multivariable_outcomes.ipynb` generate aggregate analyses and figures.

A complete Run All rerun rebuilds five derived tables and overwrites aggregate CSVs and figures. Back up local working changes first and close notebook editors before an external execution to avoid save conflicts. Selective reruns require the upstream tables or exports. See the [complete execution record](PYTHON_WORKFLOW_VALIDATION.md).

## Figure Refresh Workflow

README figures are exported to stable paths under `assets/` by the analysis notebooks. See [Figure reproducibility](FIGURE_REPRODUCIBILITY.md) for the current figure-to-notebook mapping.

Regenerating a figure should be intentional: rerun the exporting notebook, confirm the visual and aggregate outputs still match the expected interpretation, then commit the refreshed asset with the notebook change.

## Notebook Hygiene

To keep diffs reviewable:

- Keep concise summary tables when they help portfolio readability.
- Avoid committing large embedded image outputs when the same figure is exported under `assets/`.
- Retain local executed outputs; the Git clean filter strips outputs and execution counts from staged notebook contents.
- Do not commit local warnings, credentials, patient-level extracts, or local analysis logs.

Local saved notebooks retain executed outputs and figures. The Git clean filter strips outputs and execution counts from committed notebooks; aggregate CSVs, curated figures and execution evidence remain reviewable.

## BigQuery sandbox table expiration and reconstruction

The existing project uses the free BigQuery sandbox, which enforces automatic table expiration after 60 days. Disabling expiration requires leaving sandbox mode; billing settings are not changed by this repository. See [Google's sandbox documentation](https://docs.cloud.google.com/bigquery/docs/sandbox).

If the notebook reports that `nonicu_raas.analysis_dataset` does not exist, recreate missing tables from the unchanged public SQL. This helper verifies the full source query with a dry run, keeps existing tables, and creates only missing tables with an explicit 60-day expiration. It never replaces existing tables or prints patient rows.

```bash
# Read-only validation of source access and estimated scan volume
.venv/bin/python scripts/rebuild_analysis_tables.py

# Create missing tables only, retaining sandbox expiration
.venv/bin/python scripts/rebuild_analysis_tables.py --execute
```

This restores five derived tables from authorized MIMIC-IV v3.1 sources. It is reconstruction from source, not recovery of an old deleted table snapshot. Review aggregate cohort checks and model convergence after reconstruction; successful table creation alone does not validate statistical inference. The 2026-11-17 reconstruction and rerun results are recorded in [landmark validation](24H_LANDMARK_VALIDATION.md).

## Supplementary Firth sensitivity analysis

`firthmodels==0.8.2` is pinned in both dependency specifications and the uv lock. Existing locked package versions are unchanged. Run `uv sync` after updating the repository, then run the added Firth cells in notebook 04b after the cohort/model comparison section. The original MLE and sklearn prediction/risk models remain available.

```bash
.venv/bin/python scripts/test_firth_sensitivity.py
```

See [Firth validation](FIRTH_SENSITIVITY_VALIDATION.md) for the estimator change, profile interval checks, separation certificate and real-data aggregate results.

## Publication checks and patient-aware validation

In VS Code, select the Python interpreter in this repository's `.venv/`; an older globally registered kernel may point to another environment. The patient-aware section of notebook 04b runs 500 prespecified patient-cluster bootstrap replicates, reports failed/recovered fits, and evaluates a patient-disjoint holdout. It may take several minutes and does not export patient rows or identifiers. See [patient-aware validation](PATIENT_AWARE_VALIDATION.md).

```bash
.venv/bin/python scripts/test_patient_validation.py
.venv/bin/python scripts/test_report_publication.py
quarto render reports/nonicu_raas_mortality_report.qmd
```

The post-render helper synchronizes referenced aggregate figures from `assets/` to the GitHub Pages publication directory `docs/assets/`, then checks local links/resources. A missing figure or relative validation link fails the render instead of publishing a silently broken page. Canonical assets are generated by the notebooks; `docs/assets/` contains publication copies. Inspect the deployed report after pushing.

After rendering, run `.venv/bin/python scripts/test_report_consistency.py` to compare current report/narrative values with aggregate CSVs and verify synchronized images. After deployment, run `.venv/bin/python scripts/check_public_report.py` to check live HTML bytes and linked same-site resources.
