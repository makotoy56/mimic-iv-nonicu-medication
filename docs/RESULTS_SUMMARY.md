# Results Summary

## Cohort and observed outcomes

The unchanged cohort contains 460,786 adult non-ICU hospital admissions from 191,775 patients, including observation/day-case admission categories. Exposure remains a documented inpatient ACE inhibitor or ARB prescription start at 0–<24 hours; ICU use is excluded over the entire admission.

There were 149 deaths among 56,825 exposed admissions and 2,177 deaths among 403,961 unexposed admissions (crude OR approximately 0.485). These are descriptive admission-level aggregates.

## Estimation and patient-aware uncertainty

Historical unpenalized primary/sensitivity fits have separation and failed convergence. Their nominal CI/p-values are retained as audit diagnostics, not validated inference. The supplementary Firth estimator retains the same covariates and cohorts. All full-data Firth fits converged in 13–15 iterations and passed independent numerical checks.

**Patient-aware update (2026-11-17):** Current uncertainty summaries use 500 prespecified patient-cluster bootstrap draws, carrying all eligible admissions per sampled patient. Firth point estimates and all exposure/cohort/adjustment definitions are unchanged. Historical admission-independent profile intervals remain available separately. See [patient-aware validation](PATIENT_AWARE_VALIDATION.md).

| Firth sensitivity model | Admissions | Patients | Deaths | OR | 95% patient-cluster CI | Accepted / requested |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Primary cohort | 460,786 | 191,775 | 2,326 | 0.319 | 0.267–0.380 | 500/500 |
| Original condition | 460,350 | 191,591 | 1,890 | 0.362 | 0.303–0.426 | 500/500 |
| Original condition + proxy | 460,350 | 191,591 | 1,890 | 0.388 | 0.323–0.456 | 500/500 |
| 24h landmark | 342,519 | 153,041 | 1,769 | 0.356 | 0.292–0.423 | 500/500 |
| 24h landmark + proxy | 342,519 | 153,041 | 1,769 | 0.382 | 0.315–0.453 | 500/500 |

The original condition erroneously retained 117,637 temporally valid live discharges at or before 24 hours. The corrected rule requires confirmed survival and continued hospitalization strictly beyond 24 hours and excludes missing/inconsistent eligibility information explicitly. Ordinary and admission-source proxy fits have identical admission counts in these data. Proxy adjustment adds only `admission_location`.

## Separate absolute-risk model

The unweighted L2 risk model is separate from the class-balanced discrimination model and the Firth OR estimator. Patient-cluster resampling refits its scaler and coefficients and averages over each resampled admission distribution.

| Unweighted L2 risk estimand | Estimate | 95% patient-cluster CI |
| --- | ---: | --- |
| Mean predicted risk: no exposure | 0.5733 % | 0.5487 to 0.5991 % |
| Mean predicted risk: exposure | 0.1936 % | 0.1596 to 0.2239 % |
| Average marginal effect (difference) | -0.3797 percentage points | -0.4201 to -0.3407 percentage points |

Age-specific contrasts fix other covariates at their mean profile. They are not marginal standardization, and no exposure-by-age interaction was fitted. Historical 200-replicate admission bootstraps supplied only age-contrast intervals; the AME interval above is newly computed from patient resamples.

## Patient-disjoint discrimination

| Validation | Train / test admissions | Test deaths | Overlapping patients | ROC AUC | PR AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Admission-random reference | 368,628 / 92,158 | 465 | 42,796 | 0.857576 | 0.106915 |
| Patient-disjoint holdout | 368,309 / 92,477 | 468 | 0 | 0.860635 | 0.117607 |

All transformations are fitted within training data. The row-split reference was recomputed on deterministic subject/admission order; it is distinct from the earlier unordered-row AUC 0.854487. The holdouts have different case mixes; no performance improvement or external validation is claimed.

## Interpretation boundary

These are observational associations. Firth addresses separation; patient-cluster resampling addresses repeated-admission dependence. Neither corrects unmeasured severity, treatment eligibility, prescribing behavior, entire-stay ICU selection, or other residual confounding. The 500-draw percentile limits have Monte Carlo error and are not proof of coverage. Nonconverged MLE diagnostics do not validate inference; current Firth/bootstrap checks are documented separately.
