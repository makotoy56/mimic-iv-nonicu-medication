# Results Summary

## Cohort And Exposure

The final analytic cohort included 460,786 adult non-ICU hospital admissions. Early RAAS inhibitor exposure was observed in 56,825 admissions, corresponding to 12.33% of the cohort.

Patients in the early RAAS exposure group differed systematically from unexposed patients at baseline. In particular, RAAS-exposed admissions were older on average, and exposure groups differed by sex distribution and admission context. These differences support the need for multivariable adjustment.

## Unadjusted Outcomes

The overall in-hospital mortality rate was approximately 0.5%. In unadjusted summaries:

- No early RAAS exposure: 2,177 deaths among 403,961 admissions; mortality proportion 0.00539
- Early RAAS exposure: 149 deaths among 56,825 admissions; mortality proportion 0.00262
- Crude odds ratio for early RAAS exposure versus no early RAAS exposure: approximately 0.49

These unadjusted comparisons are descriptive only and should not be interpreted causally.

## Multivariable Logistic Regression

After adjustment for age, gender, race group, admission type, insurance category, and calendar period, early RAAS exposure was associated with lower odds of in-hospital mortality.

The primary model estimated:

- Exposure coefficient: -1.146
- Adjusted odds ratio: 0.32
- 95% confidence interval: 0.27-0.38
- p-value: approximately 6.42e-41

The notebook also reports sensitivity analyses:

- Primary model exposure OR: 0.32 (95% CI 0.27-0.38)
- 24-hour landmark exposure OR: 0.36 (95% CI 0.30-0.43)
- 24-hour landmark plus proxy exposure OR: 0.39 (95% CI 0.32-0.46)

## Absolute Risk Interpretation

On the absolute risk scale, early RAAS exposure was associated with an average reduction of approximately 0.38 percentage points in predicted in-hospital mortality.

Age-specific adjusted analyses suggested that the absolute risk difference associated with early RAAS exposure widened among older patients. This supports reporting both relative measures, such as odds ratios, and absolute measures, such as predicted risks and marginal effects.

## Interpretation Boundary

These results describe an observational association. They do not prove that RAAS inhibitors reduce mortality. Residual confounding by indication, comorbidity burden, acute severity, outpatient medication history, and prescribing behavior may remain.
