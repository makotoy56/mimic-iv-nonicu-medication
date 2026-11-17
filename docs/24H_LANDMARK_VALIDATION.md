# 24-hour landmark correction: validation and recalculation status

## Scope

The correction is confined to the 24-hour sensitivity analysis in `notebooks/04b_multivariable_outcomes.ipynb`. The primary models, documented prescription exposure at 0–<24 hours after admission, the exclusion of any ICU use over the entire admission, and the existing adjustment variables are unchanged. The additional model still adds only `admission_location`, filling its missing values with `Unknown` as before. Missing numeric covariates are dropped separately in each sensitivity-model specification.

Eligibility requires admission and discharge times, `dischtime > admittime + 24 hours`, and a consistent expiration flag and death time. Survivors require flag 0 with no recorded death time. Deaths require flag 1 with `admittime + 24 hours < deathtime <= dischtime`. Death and discharge exactly at the landmark are excluded. Missing or unparseable admission/discharge times, invalid flags, missing death times for hospital deaths, a survival flag with a recorded death time, and deaths outside the admission interval are explicitly excluded. A missing death time in an otherwise consistent live discharge is expected and does not itself cause exclusion.

The outcome is subsequent in-hospital mortality among these eligible admissions. This selected observational cohort does not resolve unmeasured confounding, repeated-admission dependence, or every timing-related bias.

## Diagnostics and model comparison

`classify_landmark` generates two aggregate tables:

- Overlapping diagnostic counts for the entire input and admissions retained by the original condition, including temporally valid early live discharges without a contradictory death record, unknown/inconsistent death timing, missing discharge times, and exact 24-hour boundaries.
- Mutually exclusive counts assigning the first applicable exclusion reason in the code's displayed order; these include an `included` row and sum to all input admissions. Recorded death flags and unknown/invalid expiration flags are counted separately. Diagnostics may overlap and must not be summed.

`landmark_model_comparison` reports the original and corrected conditions, each with and without the admission-source proxy. It reports eligible cohort size, model size after numerical-covariate exclusions, deaths, exposure OR/95% CI, convergence, iterations, warning categories and fit failures separately. An invalid/unknown outcome retained by the original condition is reported as a fit failure, rather than coded as survival or silently removed. The same unpenalized statsmodels Logit estimator, optimizer defaults and iteration limit are retained; a failed fit is reported rather than replaced by another estimator. The primary model is included in the separate presentation table without changing its fit.

Convergence failures and non-finite exposure intervals block the figure export. A finite exposure interval and optimizer convergence do not constitute a complete model adequacy assessment; inspect warning categories before interpreting results.

## Validation performed on 2026-11-17

The existing SSD repository was confirmed as `makotoy56/mimic-iv-nonicu-medication`, at baseline commit `7c5147d`, with a clean working tree before edits. A separate Documents/Codex copy with 12 pre-existing modified files was left untouched. The SSD repository's existing Python environment was used (Python 3.12.13, pandas 3.0.3, NumPy 2.4.6, statsmodels 0.14.6).

Run the synthetic checks from the repository root:

```bash
.venv/bin/python scripts/test_landmark_sensitivity.py
```

The test executes the actual classifier/refit functions extracted from the notebook. It covers early and exact-boundary live discharges/deaths, events just after 24 hours, death at discharge, missing/invalid timestamps and flags, inconsistent death records, non-default indices, timezone normalization, input immutability and missing required columns. Synthetic ordinary/proxy fits verify missing-numeric-covariate counts, OR interval ordering and convergence reporting. A singular fit verifies explicit failure reporting. Synthetic estimates are not clinical findings and are not exported.

The public SQL selects `admittime`, `dischtime`, `deathtime` and `hospital_expire_flag` into `base_admissions`; subsequent `b.*`/`c.*` selections preserve them through the non-ICU cohort and analysis table. The notebook still uses `SELECT *`, now preceded by an explicit check of required fields in the actual BigQuery schema.

**Real-data limitation:** existing authentication reached BigQuery, but `mimic-iv-portfolio.nonicu_raas.analysis_dataset` returned 404. Listing tables in the existing `nonicu_raas` dataset returned none. The two local CSVs under `data/interim` are aggregate baseline summaries and do not contain the required admission/death/discharge fields. Consequently the actual analysis-table schema, issue counts, eligible/model counts, deaths, corrected ORs/95% CIs and real-data convergence could not be verified. No source tables were recreated and no substitute patient dataset was used.

Existing numeric estimates (including landmark OR 0.36 and proxy OR 0.39), exported figures and rendered HTML have not been recalculated or overwritten. Related source summaries identify the landmark estimates as historical pending recalculation. Do not interpret these historical values as results of the corrected definition.

## Authorized local rerun when the analysis table is available

1. Restore the existing authorized analysis table through the established local workflow. Confirm all four landmark fields in the schema output, without displaying patient rows.
2. Run notebook loading/preparation and the existing primary statsmodels model, then the landmark classifier, diagnostics and comparison cells. Review missingness, exact boundaries, exclusive reasons and the original-versus-corrected cohort/model counts.
3. Review each ordinary/proxy model's deaths, convergence, warning categories and OR/95% CI. Do not silently change adjustment variables, missing-value rules or fitting algorithms to obtain convergence.
4. Only after real-data verification, export the corrected aggregate figure and synchronize the numerical summaries/report. Any existing rendered HTML remains historical until deliberately regenerated from validated source results.

Patient-level data, identifiers and credentials must remain within the authorized environment. The committed notebook/test changes contain code and synthetic inputs, not patient records or new clinical estimates.
