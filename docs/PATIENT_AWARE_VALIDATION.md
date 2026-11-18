# Patient-aware validation (2026-11-17)

## Scope and unchanged specifications

The unit remains the hospital admission, with repeated admissions from the same patient. All full-data Firth point fits, covariates, corrected/original landmark rules, 0–<24-hour prescription exposure and entire-stay non-ICU definition are unchanged. The historical primary MLE is separated/nonconverged; its nominal inference is diagnostic only. These are added uncertainty and discrimination validations, not a replacement primary analysis.

## Prespecified patient-cluster procedure

500 patient samples are drawn with replacement separately within each eligible cohort, carrying every eligible admission of each selected patient with the same multiplicity. Ordinary/proxy models within a cohort share patient draws. Seeds are 42 for the primary cohort, 43 for the original condition and 44 for the corrected condition. Inputs are deterministically ordered by subject/admission IDs in process memory; identifiers are never exported. Frequency compression of identical design/outcome rows is exact and is not subsampling.

Each resample uses normal observed-level dummy encoding: a category absent from the draw contributes no dummy, as in fitting explicitly expanded resampled rows. No observed category or adjustment variable is pooled or dropped. This policy was established in numerical preflight before the final 500-draw run. Synthetic tests compare it with explicit expanded-data fitting, and the observed-level counts below make it auditable.

Each Firth refit uses the same Jeffreys-penalized objective. Bootstrap Newton settings are max_iter 300, gtol 1e-6 and xtol 1e-7. If Newton flags nonconvergence, an independent score is checked and, when needed, the same objective is optimized with analytic-gradient BFGS (maximum 200 iterations, gtol 1e-6). Acceptance requires finite coefficients, no objective decrease beyond 1e-7 and maximum absolute independent adjusted score below 1e-5. This is numerical recovery, not a change of estimator or a claim that the original Newton run converged. Full-data profile fits retain their original stricter settings.

Failed draws are counted and are not replaced. Publication requires at least 475/500 accepted refits per model. The 95% intervals are the 2.5th/97.5th percentiles of accepted coefficient draws, exponentiated for ORs (NumPy linear percentiles). With 500 draws, percentile endpoints have Monte Carlo error; numerical success is not a coverage guarantee.

| Firth sensitivity model | Admissions | Patients | Deaths | OR | 95% patient-cluster CI | Accepted / requested |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Primary cohort | 460,786 | 191,775 | 2,326 | 0.319 | 0.267–0.380 | 500/500 |
| Original condition | 460,350 | 191,591 | 1,890 | 0.362 | 0.303–0.426 | 500/500 |
| Original condition + proxy | 460,350 | 191,591 | 1,890 | 0.388 | 0.323–0.456 | 500/500 |
| 24h landmark | 342,519 | 153,041 | 1,769 | 0.356 | 0.292–0.423 | 500/500 |
| 24h landmark + proxy | 342,519 | 153,041 | 1,769 | 0.382 | 0.315–0.453 | 500/500 |

| Model | Accepted / requested | Newton-warning fits independently recovered | Draws missing a nuisance level | Maximum absent levels | Failed fits |
| --- | ---: | ---: | ---: | ---: | --- |
| Primary cohort | 500/500 | 5 | 0 | 0 | {} |
| Original condition | 500/500 | 1 | 0 | 0 | {} |
| Original condition + proxy | 500/500 | 22 | 188 | 1 | {} |
| 24h landmark | 500/500 | 7 | 0 | 0 | {} |
| 24h landmark + proxy | 500/500 | 5 | 173 | 1 | {} |

The separate unweighted L2 risk model is refitted on the primary patient draws. Both StandardScaler and LogisticRegression receive the patient-frequency weights; this matches explicit row replication. AME and average predicted risks are weighted over each resampled admission distribution. Age contrasts use the resampled mean nuisance-covariate profile, not marginal standardization. No exposure-by-age interaction is fitted. All 500/500 risk refits passed, with no failed risk draws.

| Unweighted L2 risk estimand | Estimate | 95% patient-cluster CI |
| --- | ---: | --- |
| Mean predicted risk: no exposure | 0.5733 % | 0.5487 to 0.5991 % |
| Mean predicted risk: exposure | 0.1936 % | 0.1596 to 0.2239 % |
| Average marginal effect (difference) | -0.3797 percentage points | -0.4201 to -0.3407 percentage points |

Historical 200-replicate admission-row bootstrap intervals applied only to the age curve; they did not supply an AME CI. New patient-cluster figures use new filenames, retaining historical images and original profile intervals for audit.

## Patient-disjoint discrimination

The patient-disjoint holdout is an internal evaluation of retrospective discrimination on the full admission cohort. It uses prescription records from 0–<24 hours while including deaths within 24 hours, and applies no 24-hour survival/continued-hospitalization eligibility filter. There is no fixed clinical prediction time or prospective prediction horizon: ROC AUC 0.860635 and PR AUC 0.117607 do not describe admission-time or 24-hour prognostic performance. Patient separation and train-only preprocessing address patient overlap and preprocessing leakage, not temporal feature availability. The 24-hour landmark association analyses separately require confirmed survival and continued hospitalization strictly beyond 24 hours and evaluate subsequent in-hospital death; they use a different eligible cohort.

The same class-balanced L2 logistic classifier family, C=1, lbfgs, max_iter=2000, age and categorical covariates is evaluated with an 80/20 patient GroupShuffleSplit, seed 42. Scaler and OneHotEncoder(drop='first', handle_unknown='ignore') are fitted using training data only. Test patients are disjoint; patients are never features. No threshold is tuned on the holdout. The new admission-random reference uses stratification and the same seed on deterministic input order.

| Validation | Train / test admissions | Test deaths | Overlapping patients | ROC AUC | PR AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Admission-random reference | 368,628 / 92,158 | 465 | 42,796 | 0.857576 | 0.106915 |
| Patient-disjoint holdout | 368,309 / 92,477 | 468 | 0 | 0.860635 | 0.117607 |

Train/test patient counts for the patient-disjoint holdout are 153,420/38,355. Both fits completed without convergence warnings (59/73 iterations, in table order). The initial 2026-11-17 validation note reports unordered-row AUC 0.854487/PR AUC 0.115764. The separate 2026-11-18 full-run JSON receipt records 0.859852/0.116565 (rounded 0.8599/0.1166). The exact row partitions of these unordered runs were not exported, so neither is the deterministic reference or a current patient-disjoint metric. See [metric provenance](AUDIT_CORRECTIONS_20261118.md#discrimination-metric-provenance). Single-holdout metrics have sampling variation and different test case mixes, so the observed difference is not evidence that group splitting improves prediction. This is internal, not external, validation.

## Reproduction and checks

Run the patient-aware cells in `notebooks/04b_multivariable_outcomes.ipynb` using the repository `.venv`. `scripts/patient_validation.py` and `scripts/firth_point_fallback.py` implement the calculation. Aggregate evidence is in `python/outputs/firth_patient_bootstrap.csv`, `risk_patient_bootstrap.csv`, `age_risk_patient_bootstrap.csv` and `patient_split_validation.csv`.

Synthetic tests verify common weights for a patient's admissions, deterministic patient-disjoint splitting, weighted versus expanded risk/AME calculations, observed-level Firth encoding versus explicit resampled data, same-objective fallback versus an analytic/library Firth result, and its score against numerical differentiation. Existing landmark boundary and Firth/profile tests also pass.

```bash
.venv/bin/python scripts/test_landmark_sensitivity.py
.venv/bin/python scripts/test_firth_sensitivity.py
.venv/bin/python scripts/test_patient_validation.py
.venv/bin/python scripts/test_report_publication.py
.venv/bin/python scripts/test_report_consistency.py
quarto render reports/nonicu_raas_mortality_report.qmd
.venv/bin/python scripts/check_public_report.py  # after Pages deployment
```

Quarto post-render copies referenced canonical images into `docs/assets/` and rejects broken local resources. Live checks compare the deployed HTML bytes and fetch every same-site linked resource. The legacy MLE CSV is regenerated during full workflow runs and remains explicitly diagnostic; local working changes are backed up before rerunning. Nonconverged MLE diagnostics do not validate Firth or bootstrap inference. The current public workflow and execution evidence are linked from [reproducible scope](REPRODUCIBLE_SCOPE.md).

Firth and patient resampling do not remove unmeasured confounding, timing/eligibility selection or selection from excluding any ICU stay during the entire admission. The primary cohort still includes observation/day-case categories and its original timestamp inconsistencies; the landmark rules explicitly exclude inconsistent eligibility records. No patient-level data, identifiers, credentials or compressed covariate patterns are saved or published.

SciPy is explicitly listed as a direct dependency for the analytic-gradient fallback. Updating the dependency metadata changed no locked package version; the computation used the existing SciPy 1.17.1.


## Separate admission/24-hour prediction evaluation

Notebook 04c adds an independently defined ward-confirmed prediction-time branch from adult base admissions. It retains later ICU transfers and follows subsequent in-hospital death to discharge, with age/sex primary features and a time-verified RAAS-record companion at 24h. The original association cohort/estimates and 04b retrospective discrimination are unchanged. See [protocol](PREDICTION_TIME_PROTOCOL.md) and [real-data results, calibration, exclusions and limits](PREDICTION_TIME_VALIDATION.md).
