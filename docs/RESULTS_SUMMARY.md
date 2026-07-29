# Results Summary

## Cohort And Exposure

The final analytic cohort included 460,786 adult non-ICU hospital admissions. Documented early inpatient RAAS prescription exposure was observed in 56,825 admissions, corresponding to 12.33% of the cohort. The analytic unit was the hospital admission (`hadm_id`), and patients could contribute multiple admissions.

Admissions with documented early inpatient RAAS prescription exposure differed systematically from admissions without documented exposure at baseline. In particular, documented-exposure admissions involved older patients on average, and exposure groups differed by sex distribution and admission context. These differences support the need for multivariable adjustment.

## Unadjusted Outcomes

The overall in-hospital mortality rate was approximately 0.5%. In unadjusted summaries:

- No documented early inpatient RAAS prescription exposure: 2,177 deaths among 403,961 admissions; mortality proportion 0.00539
- Documented early inpatient RAAS prescription exposure: 149 deaths among 56,825 admissions; mortality proportion 0.00262
- Crude odds ratio for documented early prescription exposure versus no documented exposure: approximately 0.49

These unadjusted comparisons are descriptive only and should not be interpreted causally.

## Multivariable Logistic Regression

After adjustment for age, gender, race group, admission type, insurance category, and calendar period, documented early inpatient RAAS prescription exposure was associated with lower odds of in-hospital mortality.

The primary model estimated:

- Exposure coefficient: -1.146
- Adjusted odds ratio: 0.32
- 95% confidence interval: 0.27-0.38
- p-value: approximately 6.42e-41

The notebook also reports a 24-hour landmark bias-reduction sensitivity analysis and an additional landmark model with an admission-source proxy:

- Primary model exposure OR: 0.32 (95% CI 0.27-0.38)
- 24-hour landmark exposure OR: 0.36 (95% CI 0.30-0.43)
- 24-hour landmark plus proxy exposure OR: 0.39 (95% CI 0.32-0.46)

The sensitivity estimates remained directionally consistent with the primary estimate. They address one timing-related bias concern but do not eliminate residual confounding or establish causality.

## Absolute Risk Interpretation

On the absolute risk scale, the fitted model produced an average adjusted predicted mortality difference of approximately -0.38 percentage points between the documented-exposure and no-exposure scenarios.

Age-specific adjusted analyses suggested that the difference in adjusted predicted risk widened among older patients. This supports reporting both relative measures, such as odds ratios, and absolute measures, such as predicted risks and marginal effects.

## Interpretation Boundary

These results describe an observational association. They do not prove that RAAS inhibitors caused lower mortality. Treatment eligibility, confounding by indication, early clinical stability, comorbidity burden, acute severity, outpatient medication history, prescribing behavior, and other unmeasured clinical factors may affect the estimates.
