# Firth sensitivity analysis: separation and validation

## What changed

The original unpenalized statsmodels primary/sensitivity fits are preserved exactly, including their failed convergence statuses and aggregate diagnostic CSV. The added analysis uses Firth's Jeffreys-information penalty on the same logistic design, with penalized profile-likelihood 95% intervals for exposure. This is an explicit supplementary estimator, not a silent repair or relabeling of maximum likelihood. The primary cohort, corrected landmark eligibility, 0–<24-hour prescription exposure, entire-stay non-ICU definition and adjustment categories remain unchanged. The existing separate sklearn prediction/risk models, marginal effects and bootstrap results are not replaced by Firth predictions.

The implementation uses pinned `firthmodels==0.8.2`, its NumPy backend, 200 maximum fitting iterations, gradient and coefficient tolerances 1e-7, and profile-bound tolerance 1e-7 with at most 100 iterations per bound. Profile bounds are computed only for exposure. Likelihood-ratio p-values are exported separately from the historical Wald p-values. The [logistf method documentation](https://cran.r-project.org/web/packages/logistf/logistf.pdf) describes the estimator/profile inference, and the [firthmodels source](https://github.com/jzluo/firthmodels) documents this implementation.

## Why more MLE iterations do not solve this design

The earlier full-cohort diagnostic found 7,170 ambulatory-observation admissions with zero deaths. For each of the five actual design matrices, a separating direction was verified directly: set the intercept direction to −1, all non-reference admission-type dummy directions to +1, and every other direction to 0. The linear predictor changes only for the zero-event reference category. Every signed margin `(2*y - 1) * X*direction` was nonnegative, with at least one strict margin. This certifies separation and the absence of a finite full-model MLE; it is more than an optimizer's iteration-limit warning. No category was pooled or removed to make the optimizer report success.

All five designs have full column rank, with 25 parameters including intercept in the ordinary models and 36 in the admission-source models. The Firth penalty provides finite estimates for these full-rank separated designs. The original MLE output remains marked nonconverged.

## Real-data results on 2026-11-17

All five Firth fits converged in 14–15 iterations. Exposure ORs/profile bounds were finite and ordered; no warnings were recorded. Independent adjusted-score maxima were between 1.2e-9 and 6.3e-9, below the validation threshold 1e-5. All model admission/death counts exactly match the corresponding earlier fits; no numeric-covariate exclusions occurred.

| Firth sensitivity model | Admissions | Deaths | OR | 95% penalized profile CI | Iterations |
| --- | ---: | ---: | ---: | --- | ---: |
| Primary cohort | 460,786 | 2,326 | 0.318889 | 0.268642–0.375587 | 14 |
| Original condition | 460,350 | 1,890 | 0.362477 | 0.303480–0.429390 | 13 |
| Original condition + proxy | 460,350 | 1,890 | 0.387862 | 0.324601–0.459674 | 15 |
| 24h landmark | 342,519 | 1,769 | 0.356387 | 0.296182–0.425005 | 14 |
| 24h landmark + proxy | 342,519 | 1,769 | 0.381595 | 0.317006–0.455270 | 14 |

The model-level numerical checks passed; this is not a general claim of model adequacy, causal identification or validated clinical prediction. Intervals still assume independent admissions and do not account for a patient's repeated admissions. Unmeasured severity, treatment eligibility and prescribing behavior remain limitations.

The new figure `assets/firth_landmark_sensitivity.png` is explicitly labeled as supplementary Firth inference and shows only these profile intervals. Original OR assets are retained unchanged for audit. The notebook adds new cells after the existing landmark export; every prior cell source is preserved.

## Local computation and checks

Identical design/outcome rows were combined with exact integer frequency weights in process memory. Their frequency sums were 460,786, 460,350 or 342,519 as appropriate, with no subsampling. The weighted likelihood and information matrix preserve the individual-admission calculation. No compressed covariate patterns or patient rows were saved. Age is centered at 60 and divided by 10, an invertible numerical transformation that preserves the exposure contrast and covariate set.

The independent score check uses `X' [w*(y-p) + h*(0.5-p)]`, with leverage `h` computed from the original weighted binomial information matrix. A fit is not eligible for the figure unless optimizer convergence, finite profile limits, interval ordering, finite LRT p-value and the independent score threshold pass.

Synthetic tests verify:

- Complete separation, quasi-complete separation and an overlapping 2×2 design against analytic Firth point estimates from the half-cell correction.
- Profile limits against independent scalar nuisance optimization and bracketed likelihood-ratio roots, with log-coefficient agreement within 3e-6.
- Frequency-compressed versus expanded data agreement for points and profile bounds.
- Full ordinary/proxy covariate fits, admission/death preservation, full-rank checks and separation certificates.
- Invariance of exposure OR/profile limits under age rescaling and categorical-reference reversal.

```bash
uv sync
.venv/bin/python scripts/test_landmark_sensitivity.py
.venv/bin/python scripts/test_firth_sensitivity.py
```

Adding the Firth dependency changed no existing locked package versions. Runtime validation used the existing Python 3.12.13 environment, NumPy 2.4.6, SciPy 1.17.1 and scikit-learn 1.9.0. Only the new pinned package was added. The aggregate outputs are in `python/outputs/firth_model_comparison.csv`; historical MLE outputs remain in `landmark_model_comparison.csv`. No SAS session was rerun; its existing MLE validation artifacts were preserved and do not independently validate Firth inference.
