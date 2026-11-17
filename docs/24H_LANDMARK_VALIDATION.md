# 24-hour landmark correction: real-data validation

## Reconstruction on 2026-11-17

All five derived tables were reconstructed from the existing MIMIC-IV v3.1 SQL. The project uses the free BigQuery sandbox: attempting to remove expiration failed because billing is not enabled. Following the user's choice, billing was left unchanged and the tables were set to expire within 60 days. The dataset default remains 60 days. See [Google's sandbox specification](https://docs.cloud.google.com/bigquery/docs/sandbox).

This is reconstruction from source, not recovery of a historical snapshot. Earlier tables may have expired; their exact deletion history has not been established.

| Derived table | Rows | Expiration (UTC) |
| --- | --- | --- |
| analysis_dataset | 460,786 | 2027-01-16T11:48:16.966000+00:00 |
| base_admissions | 546,028 | 2027-01-16T11:44:56.933000+00:00 |
| base_admissions_racegrp | 546,028 | 2027-01-16T11:48:01.543000+00:00 |
| exposure_raas_early | 460,786 | 2027-01-16T11:48:12.014000+00:00 |
| nonicu_admissions | 460,786 | 2027-01-16T11:48:07.270000+00:00 |

## Actual schema and cohort validation

The rebuilt analysis table has 25 columns. `admittime`, `dischtime` and `deathtime` are `DATETIME`; `hospital_expire_flag` is `INTEGER`. The SQL retains these fields through `b.*`/`c.*`; the notebook checks the actual schema before `SELECT *`.

There are 460,786 unique admission IDs and 191,775 distinct patients. Aggregate checks found no missing identifiers, invalid/missing adult age, invalid exposure flags, inconsistency between any-RAAS and ACEi/ARB flags, or matches to ICU stays over the entire admission. The earlier aggregate results were reproduced: 56,825 exposed admissions/149 deaths and 403,961 unexposed admissions/2,177 deaths.

The primary models, prescription exposure at 0–<24 hours, entire-stay non-ICU definition, and adjustment variables were retained. The proxy model still adds only `admission_location`, with missing values represented by `Unknown` as before.

## Eligibility and diagnostic counts

Eligibility requires valid admission/discharge times, discharge strictly after admission + 24 hours, and consistent expiration flags/death times. Survivors require flag 0 and no death time. Deaths require flag 1 and `admission + 24 hours < deathtime <= dischtime`. Death/discharge exactly at 24 hours and unknown/inconsistent eligibility information are excluded rather than coded as survival.

Early live-discharge diagnostics require valid temporal order and no contradictory death record. Diagnostic categories can overlap and must not be summed.

| Overlapping diagnostic | Entire input | Retained by original |
| --- | --- | --- |
| live_discharge_at_or_before_24h | 117,637 | 117,637 |
| live_discharge_exactly_24h | 120 | 120 |
| discharge_before_admission | 96 | 73 |
| death_after_discharge | 141 | 119 |
| death_before_admission | 10 | 0 |
| death_exactly_24h | 0 | 0 |
| missing_admittime | 0 | 0 |
| missing_dischtime | 0 | 0 |
| death_flag_without_deathtime | 2 | 2 |
| survival_flag_with_deathtime | 0 | 0 |
| invalid_or_missing_expire_flag | 0 | 0 |

The following first-applicable-reason counts are mutually exclusive, include eligible admissions, and sum to 460,786. Recorded deaths and invalid/unknown outcome flags are counted separately; there were zero invalid/unknown flags in this input.

| First applicable reason | Admissions | Recorded deaths | Retained by original |
| --- | --- | --- | --- |
| included | 342,519 | 1,769 | 342,519 |
| discharge_at_or_before_24h | 117,637 | 0 | 117,637 |
| discharge_before_admission | 96 | 23 | 73 |
| death_after_discharge | 122 | 122 | 119 |
| death_at_or_before_24h | 404 | 404 | 0 |
| death_before_admission | 6 | 6 | 0 |
| death_flag_without_deathtime | 2 | 2 | 2 |

The original condition retained 460,350 admissions/1,890 deaths; the correction retains 342,519 admissions/1,769 deaths, removing 117,831 admissions and 121 deaths. Independent BigQuery aggregate SQL exactly reproduced Python counts, including 48,416 exposed admissions/129 deaths and 294,103 unexposed admissions/1,640 deaths in the corrected cohort.

## Original MLE diagnostics: separation remains; supplementary remedy added

The unchanged unpenalized statsmodels Logit/default optimizer and 35-iteration limit were used. **None of the five fits converged. The nominal confidence intervals below are diagnostic outputs, not validated inference.** No covariate, category handling, penalty, optimizer or iteration-limit change was made to obtain a different result.

| Condition/model | Admissions | Deaths | OR output | Nominal 95% CI | Converged |
| --- | --- | --- | --- | --- | --- |
| Primary | 460,786 | 2,326 | 0.318 | 0.269–0.376 | No |
| Original condition | 460,350 | 1,890 | 0.361 | 0.304–0.430 | No |
| Original condition + proxy | 460,350 | 1,890 | 0.387 | 0.325–0.460 | No |
| 24h landmark | 342,519 | 1,769 | 0.355 | 0.296–0.425 | No |
| 24h landmark + proxy | 342,519 | 1,769 | 0.382 | 0.319–0.457 | No |

Ordinary/proxy specifications have identical model counts and dropped zero numeric-covariate-missing rows. All four sensitivity fits recorded `ConvergenceWarning` and 35 iterations. The unchanged primary cell suppresses warning messages, but its `mle_retvals['converged']` was explicitly checked and was false.

An aggregate check found 7,170 `AMBULATORY OBSERVATION` admissions with zero deaths, consistent with a separation problem in the unpenalized model. A subsequent explicit Firth sensitivity analysis retained every adjustment category and converged for all five comparisons. It changes the estimator while preserving the original primary specification/output; see [Firth validation](FIRTH_SENSITIVITY_VALIDATION.md). The original MLE remains separated and is not relabeled as converged. Existing OR figures remain historical and were not overwritten with unconverged results. A skipped export now allows later notebook prediction/bootstrap sections to continue.

## Full primary prediction/risk rerun

The existing separate sklearn discrimination and unweighted risk models were rerun. ROC AUC was 0.854487, PR AUC 0.115764, predicted mortality 0.573332% without exposure versus 0.193605% with exposure, and AME −0.379727 percentage points. These reproduce the earlier rounded summaries. The classification and full-cohort risk models used 55 and 13 iterations, respectively. All 200 bootstrap refits completed with the existing seed 42 and 200-replicate specification. These separate penalized prediction models do not repair the unpenalized OR fits. No SAS session was rerun and no SAS-generated artifacts were overwritten.

## Reproduction and evidence

```bash
# Synthetic boundary/model/failed-figure-export checks
.venv/bin/python scripts/test_landmark_sensitivity.py
# Read-only validation of reconstruction SQL and scan volume
.venv/bin/python scripts/rebuild_analysis_tables.py
# Recreate missing tables only, with 60-day sandbox expiration
.venv/bin/python scripts/rebuild_analysis_tables.py --execute
```

The helper never replaces an existing table, changes billing, or displays patient rows. The initial full-pipeline dry run estimated 921,440,830 bytes. The baseline SSD working tree was clean at commit `05c178b`; the separate Documents/Codex copy's 12 existing modifications were left untouched.

Aggregate-only evidence is saved under `python/outputs/landmark_diagnostics.csv`, `landmark_exclusions.csv`, `landmark_model_comparison.csv`, and `landmark_cohort_counts.csv`. Notebook functions were tested directly on synthetic boundary cases, missing/invalid times and flags, timezone/index behavior, ordinary/proxy refits, singular fits, invalid-outcome handling and figure-export skipping. Real-data selection was also checked independently in BigQuery SQL.

Patient records stayed in the authorized BigQuery project and local process memory. Only aggregate outputs are saved or published; notebook outputs and execution counts are stripped by the existing Git filter. No patient-level local extracts, identifiers or credentials are added to the repository.

## Subsequent patient-aware validation

The profile intervals and original row-split/bootstrap results above are historical comparisons. Additional patient-cluster intervals (500 prespecified draws), risk/AME intervals and a patient-disjoint holdout are documented in [patient-aware validation](PATIENT_AWARE_VALIDATION.md). Full-data Firth points and original primary/cohort/exposure specifications remain unchanged.
