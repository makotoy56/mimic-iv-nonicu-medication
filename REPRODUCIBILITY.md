# Reproducibility and Analytical Environment

## Project Purpose

This project is a retrospective observational MIMIC-IV clinical analytics workflow evaluating whether documented inpatient RAAS prescription exposure within 24 hours of admission is associated with in-hospital mortality among adult non-ICU hospital admissions.

The analytical purpose is to demonstrate reproducible EHR cohort construction, documented inpatient prescription-exposure classification, multivariable logistic regression, absolute risk interpretation, sensitivity analysis, Python numerical validation, and Quarto-based clinical reporting. The findings are hypothesis-generating associations and are not causal treatment-effect estimates.

## Data Source

The analysis uses MIMIC-IV v3.1 hospital admission data distributed through PhysioNet and accessed through BigQuery.

Patient-level MIMIC-IV source tables, patient-level derived analysis datasets, credentials and local BigQuery configuration are not included in this repository. Reproduction requires independent PhysioNet/MIMIC approval, Google Cloud authentication and BigQuery access.

## Analytical Workflow

The patient-disjoint holdout is an internal evaluation of retrospective discrimination on the full admission cohort. It uses prescription records from 0–<24 hours while including deaths within 24 hours, and applies no 24-hour survival/continued-hospitalization eligibility filter. There is no fixed clinical prediction time or prospective prediction horizon: ROC AUC 0.860635 and PR AUC 0.117607 do not describe admission-time or 24-hour prognostic performance. Patient separation and train-only preprocessing address patient overlap and preprocessing leakage, not temporal feature availability. The 24-hour landmark association analyses separately require confirmed survival and continued hospitalization strictly beyond 24 hours and evaluate subsequent in-hospital death; they use a different eligible cohort.

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
7. **Additional prediction-time evaluation**: notebook 04c defines ward-confirmed admission/24h risk sets, retains later ICU transfers and evaluates subsequent in-hospital death through discharge. See the separate [protocol and results](docs/PREDICTION_TIME_VALIDATION.md).
8. **Validation**: synthetic boundary tests, Firth numerical checks, patient-cluster bootstrap diagnostics and internal retrospective discrimination evaluation are implemented in Python. See [current execution evidence](docs/CLINICAL_REEXECUTION_20261119.md).
9. **Reporting**: the narrative clinical report is authored in Quarto and rendered to `docs/reports/`.
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

## Replace the author-specific BigQuery destination before running

The checked-in examples use the author's project `mimic-iv-portfolio` and destination dataset `nonicu_raas`; they do not configure a new user's project automatically. Do not run the construction notebooks against those defaults. Choose your own writable project and dataset, create the dataset in **US**, and configure your own authorized ADC/source access. Retain the sandbox's 60-day expiration where applicable. No credentials belong in source control.

Make these coordinated replacements in a private working copy before any connected run:

| Source | Required replacement |
| --- | --- |
| All seven `sql/*.sql` files | Replace every destination prefix `mimic-iv-portfolio.nonicu_raas` with `YOUR_PROJECT.YOUR_DATASET`, including intermediate-table reads and the drug-check query. |
| All eight notebooks 00–04c | Set `PROJECT_ID` to `YOUR_PROJECT`. Set `DATASET_ID` in 00 and `DATASET` in 01–04c to `YOUR_DATASET`; keep `LOCATION = "US"` in 00. Derived `TABLE_*` strings then follow those constants. |
| `scripts/rebuild_analysis_tables.py` | Set its fully qualified `DATASET` to `YOUR_PROJECT.YOUR_DATASET` **and** its `bigquery.Client(project=...)` to `YOUR_PROJECT`. Its exact CREATE-header check must agree with the edited SQL prefix. |
| Additional prediction helpers | Notebook 04c passes its `PROJECT_ID`/`DATASET` through `real_data_access.read_prediction_inputs` to the verified loader; no default edits are needed for that route. For direct guarded use pass `project=YOUR_PROJECT, dataset=YOUR_DATASET`. The optional chronology sensitivity CLI accepts `--project YOUR_PROJECT --dataset YOUR_DATASET`. Native MIMIC source prefixes stay unchanged. |
| Optional `scripts/validation_checklist.py` | Set `PROJECT_ID` and `DATASET`; table references, including the landmark prevalence query, follow `TABLES`. |

Keep the authorized source references `physionet-data.mimiciv_3_1_hosp` and `physionet-data.mimiciv_3_1_icu` unchanged unless deliberately using an equivalent licensed source. Do not replace `physionet-data` with the destination project. Retain table names, joins, cohort/exposure predicates and US location. Update explanatory author-project labels in notebook markdown separately if desired; those labels do not configure execution.

Review executable cells, SQL and both helper scripts for remaining author-specific destination literals; use notebook source/JSON-aware editing rather than replacing saved outputs. `scripts/test_audit_corrections.py` tests this replacement recipe on temporary source copies without credentials, a client connection or data queries. Passing it does not prove IAM, source access or BigQuery SQL execution.

Only after reviewing the replacements, use the rebuild helper without `--execute` for a connected dry run. Its `--execute` mode creates missing tables only. By contrast, notebooks 01–02 run `CREATE OR REPLACE` and overwrite their configured destination tables. Confirm that destination is your own before a complete rerun.

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
   - `notebooks/04c_prediction_time_evaluation.ipynb` (separate ward-confirmed admission/24h predictions; read the protocol first)
5. Render the Quarto report from the repository root:

   ```bash
   quarto render reports/nonicu_raas_mortality_report.qmd
   ```

6. Review the rendered report at `docs/reports/nonicu_raas_mortality_report.html`.

The independent-admission profile intervals and nonconverged Python MLE diagnostics are distinct from the added patient-cluster bootstrap intervals. Patient-disjoint discrimination and bootstrap details are documented in [patient-aware validation](docs/PATIENT_AWARE_VALIDATION.md). Quarto post-render now synchronizes referenced canonical images from `assets/` to `docs/assets/` and rejects missing local resources.

After rendering, run `.venv/bin/python scripts/test_report_consistency.py` to compare current report/narrative values with aggregate CSVs and verify synchronized images. After deployment, run `.venv/bin/python scripts/check_public_report.py` to check live HTML bytes and linked same-site resources.

## Complete workflow verification

The [current clinical reexecution record](docs/CLINICAL_REEXECUTION_20261119.md) documents the 2026-11-19 sequential fresh-kernel Run All of 00–04c (8 notebooks / 109 code cells, zero runtime error outputs). It includes the live Python-generated displays and real-data access guards. Connected BigQuery checks and stable aggregate comparisons passed; MLE remains separated/nonconverged. Historical [615de01 execution evidence](docs/CLINICAL_REEXECUTION_615de01.md), [8063e91 execution evidence](docs/PYTHON_WORKFLOW_VALIDATION.md) and [offline correction scope](docs/AUDIT_CORRECTIONS_20261118.md) retain their recorded scope.

## Additional time-anchored prediction branch

Notebook 04c uses read-only `sql/05_prediction_time_inputs.sql` from the adult base and native `transfers`, `icustays`, `prescriptions` and `poe`. It requires confirmed ward occupancy at the point and no prior ICU entry, retains later ICU transfers and follows subsequent in-hospital death through discharge. It does not use the original entire-stay non-ICU analysis table as its risk set. See [protocol](docs/PREDICTION_TIME_PROTOCOL.md) and [real-data validation](docs/PREDICTION_TIME_VALIDATION.md). Admission results apply only to ward-confirmed admissions. Configure the notebook constants before running; reads are dry-run first and capped at 10 GiB/query. Only aggregate CSV/JSON and a calibration figure are saved. The optional post-QA point-estimate sensitivity is:

```bash
.venv/bin/python scripts/prediction_time_chronology_sensitivity.py --project YOUR_PROJECT --dataset YOUR_DATASET
```

Synthetic checks require no data access:

```bash
.venv/bin/python scripts/test_prediction_time_validation.py
.venv/bin/python scripts/test_prediction_time_location.py
.venv/bin/python scripts/test_prediction_time_chronology_sensitivity.py
.venv/bin/python scripts/test_prediction_time_report.py
```

The additional forecast metrics cannot reuse 04b retrospective AUCs. Their intervals resample held-out patients conditional on fixed trained models. Predictors are limited to age/sex and a separately defined time-verified RAAS record in the companion model. This is retrospective internal evaluation, not prospective/external validation or a causal RAAS effect.

## Python-generated notebook results

All public notebooks 00–04c now initialize `NotebookResults` from `scripts/nonicu_notebook_results.py`. Numbered titles, tables/figures, reading guidance, computed summaries and interpretation limits are emitted by Python from the current execution's aggregate objects. Source references and execution mode are generated once near the beginning of each notebook, after the destination settings. The shared header includes an expandable source index keyed by result number; individual figure/table captions do not repeat it. `scripts/nonicu_result_specs.json` contains captions and methodological guidance, not stored clinical estimates. Destination table labels follow the notebook's `PROJECT_ID` and `DATASET`/`DATASET_ID`.

The original 93 analytical code cells retain their cohort/exposure/model statements. Eight presentation setup cells and eight shared-provenance cells bring the current total to 109 code cells. Presentation wrappers capture the existing outputs without introducing data queries or model fits. Existing model and CSV exports remain in their original analysis cells. Firth and patient-cluster displays use current fitted aggregate rows; the calibration display is drawn directly from current aggregate bins. No old PNG is substituted if an execution fails or does not produce a figure.

The earlier presentation-only review regenerated displays from saved aggregates with cleared execution counts and labeled them **presentation replay**. The 2026-11-19 connected Run All replaced those local replay outputs with live results, sequential execution counts and freshly calculated summaries/figures, including both original age-risk plots. Each saved header now identifies **live notebook execution**. The receipt above records that successful clinical run; historical replay and execution receipts retain their original scope.

Run each notebook from a fresh repository Python 3.12 kernel in the documented order, after configuring your own authorized BigQuery destination. Run All still executes the original construction queries, fitting and resampling; 01–02 retain their `CREATE OR REPLACE` behavior. Successful execution replaces the replay outputs with current results and recalculates their numerical summaries. Fits that fail, intervals that are withheld, and missing outputs are reported explicitly rather than filled from old results.

The following checks use synthetic aggregates and local source files only; they do not authenticate, query BigQuery or refit clinical models:

```bash
uv run python scripts/test_notebook_results.py
uv run python scripts/test_audit_corrections.py
uv run python scripts/test_report_consistency.py
uv run python scripts/test_prediction_time_report.py
```


### Calculation inputs versus saved aggregates and verification files

The shared header separates **Calculation inputs and source definitions** from **Saved aggregates and verification files (CSV/JSON)**. The latter links identify saved aggregate results, diagnostics and execution/checking records, not original MIMIC-IV source tables. `nonicu_result_specs.json` keeps current Python calculation inputs in `source`, and saved CSV/JSON result and verification references separately in `exports`. The two indexes do not imply the same data-flow role.

For example, Table 04b.13 joins the in-memory `firth_patient_ci` and `firth_compare_raw` objects directly. `firth_patient_bootstrap.csv` and `firth_model_comparison.csv` are saved copies, not files reloaded to produce that display. The same distinction applies to other affected result definitions. Separate report/validation workflows may legitimately read those exports.

The earlier source-label clarification changed only explanatory metadata and saved shared-header text; it did not execute clinical queries, fits or bootstraps. The subsequent 2026-11-19 connected Run All separately verified the complete live workflow, as recorded above. Synthetic presentation checks still forbid network access and CSV reading.

## Real-data execution and access failures

Normal execution of notebooks 00–04c uses real MIMIC-IV/BigQuery inputs. There is no automatic switch to synthetic/demo data or saved aggregate files when access fails. Configure `PROJECT_ID` and `DATASET`/`DATASET_ID` and the matching SQL destination prefixes first. Missing or placeholder settings stop before authentication. The checked-in author settings are examples for other users; they do not grant access.

The notebook/CLI access boundaries report a safe cause and **Next** action for missing/expired ADC, rejected permissions, missing resources, location, service and processing-limit errors. They do not print SDK request details or credentials. Configure ADC outside the notebook with `gcloud auth application-default login`, use your approved PhysioNet account and authorized BigQuery project, then start a fresh repository Python kernel. If source access or job/destination permissions are denied, resolve them with the project administrator. Missing derived tables may have reached the sandbox's 60-day expiration; follow the documented construction/rebuild procedure explicitly. Error handling never starts a rebuild itself.

Notebook 00 retains its existing dataset setup behavior, and 01–02 retain their explicit construction queries. The prediction and rebuild processing caps, dry runs, US-location checks, missing-only rebuild, 60-day lifetime and aggregate-only exports are unchanged. A failed input step stops before fitting or result export. Saved notebook presentation-replay outputs remain available for review and do not prove that a new run succeeded.

Notebook 04c and the chronology-sensitivity CLI use `real_data_access.read_prediction_inputs`, an error-guidance adapter around the unchanged verified `prediction_time_validation.read_inputs` loader. Direct low-level loader calls remain real-only and raise on failure; use the adapter for the same actionable guidance. Historical execution receipts and source hashes remain unchanged. Separate numerical optimizer recovery in the Firth code is not a switch of datasets.

Explicit synthetic tests and saved-aggregate review/validation workflows remain separate. `validation_checklist.py --step forbidden` is a static feature-list check and needs no ADC or BigQuery client. The new access tests mock failures and block network/credential access:

```bash
.venv/bin/python scripts/test_real_data_access.py
```

These tests are offline access/presentation checks. The separate [2026-11-19 connected execution](docs/CLINICAL_REEXECUTION_20261119.md) verified actual access, live tables, all 109 notebook code cells and the existing aggregate-validation/chronology CLI paths. A passing historical run does not guarantee future IAM or table availability.
