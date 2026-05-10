# Setup And Reproducibility

This repository is a portfolio-focused analysis project, not a packaged production application. The setup below is intended to make notebook review and selective reruns reproducible without tracking patient-level data or local credentials.

## Python Environment

The notebooks were developed with Python 3.10 in a local virtual environment. A repository-local `.venv/` works, and a shared parent environment such as `../.venv/` is also fine when working across related portfolio projects.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --user --name mimic-portfolio --display-name "Python (mimic-portfolio)"
```

The notebook metadata points to the `mimic-portfolio` kernel name. If you use a shared parent environment, run the same `ipykernel install` command from that activated environment.

## Data And Credential Expectations

The repository does not include MIMIC-IV tables, local extracts, credentials, SAS input files, or patient-level data. Full notebook execution requires:

- PhysioNet/MIMIC-IV access and compliance with the MIMIC data use agreement.
- Google Cloud authentication with BigQuery access to the configured MIMIC-IV project/dataset.
- Local SAS configuration if regenerating the SAS comparison outputs.

The tracked CSV files under `python/outputs/` and `sas/outputs/` are aggregate validation artifacts only.

## Notebook Execution

The notebooks are ordered by analysis stage:

1. `01_cohort.ipynb` through `03b_describe_analysis_dataset.ipynb` build and inspect the analysis dataset.
2. `04a_unadjusted_outcomes.ipynb` and `04b_multivariable_outcomes.ipynb` generate the primary Python outputs and README figures.
3. `05_sas_python_validation.ipynb` compares exported aggregate Python and SAS outputs.

Most notebooks depend on upstream tables or exported artifacts. Rerun them selectively rather than treating the repository as a single push-button pipeline.

## Figure Refresh Workflow

README figures are exported to stable paths under `assets/` by the analysis notebooks. See [Figure reproducibility](FIGURE_REPRODUCIBILITY.md) for the current figure-to-notebook mapping.

Regenerating a figure should be intentional: rerun the exporting notebook, confirm the visual and aggregate outputs still match the expected interpretation, then commit the refreshed asset with the notebook change.

## Notebook Hygiene

To keep diffs reviewable:

- Keep concise summary tables when they help portfolio readability.
- Avoid committing large embedded image outputs when the same figure is exported under `assets/`.
- Clear execution counts before committing notebooks.
- Do not commit local warnings, credentials, patient-level extracts, or SAS logs.

The current notebooks preserve summary-level outputs but avoid large embedded figure blobs and execution-count churn.
