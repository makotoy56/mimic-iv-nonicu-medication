# Discussion And Limitations

## Interpretation

**Separation-robust supplement (2026-11-17):** The original unpenalized primary/sensitivity fits remain nonconverged and are retained for audit. An explicit Firth/Jeffreys-penalized sensitivity analysis, using the same admissions, exposure and adjustment variables, converged for all five comparisons. Its 95% intervals use penalized profile likelihood; numerical rank, profile bounds and independent adjusted-score checks passed. This changes the estimator, not the original primary fit or the separate prediction/risk model. See [Firth validation](FIRTH_SENSITIVITY_VALIDATION.md).

Documented early inpatient RAAS prescription exposure was associated with lower in-hospital mortality in this adult non-ICU MIMIC-IV cohort after multivariable adjustment. The association was present on both the relative scale, using odds ratios, and the absolute scale, using differences in model-predicted risk.

The absolute-risk framing is important because the baseline event rate in this non-ICU cohort is low. A percentage-point difference in adjusted predicted risk is more directly interpretable for clinical analytics and outcomes research audiences than an odds ratio alone.

The corrected landmark cohort requires confirmed survival and continued hospitalization beyond 24 hours and contains 342,519 admissions/1,769 deaths. The supplementary Firth ordinary/proxy ORs were 0.356/0.382, with 95% penalized profile intervals 0.296–0.425 and 0.317–0.455. These fits converged without removing adjustment categories. The estimator differs from the original MLE; it does not establish causality or correct repeated-admission dependence. Historical MLE OR assets are retained unchanged, and the new Firth figure is explicitly labeled.

## Observational Design

This study is observational and hypothesis-generating. It cannot establish that documented inpatient RAAS prescription exposure, or RAAS treatment itself, causes lower mortality.

Although exposure ascertainment is restricted to the first 24 hours after admission and models adjust for measured demographic and admission-related variables, residual confounding may remain. Potential sources include:

- Confounding by indication
- Differences in chronic outpatient medication history
- Comorbidity burden not fully represented in the primary model
- Acute physiologic severity and laboratory findings
- Clinician prescribing behavior
- Medication discontinuation, dose, duration, and adherence
- Selection effects related to early survival and treatment eligibility

## Exposure Limitations

The exposure definition uses inpatient prescription records with a recorded start time during the first 24 hours. It does not directly measure outpatient chronic RAAS inhibitor use, medication adherence before admission, confirmed inpatient administration, dose intensity, treatment indication, or duration of therapy.

Restricting exposure to the first 24 hours improves temporal clarity but does not fully eliminate immortal-time bias or reverse-causation concerns.

The analytic unit is the hospital admission (`hadm_id`), and patients may contribute multiple admissions. The models treat admissions as observations and do not account for within-patient correlation across repeat admissions.

## Outcome And Generalizability

The outcome is in-hospital mortality. The analysis does not evaluate post-discharge mortality, readmission, adverse events, renal outcomes, or disease-specific endpoints.

MIMIC-IV reflects care delivered within its source health system and time period. Findings may not generalize to all hospitals, geographic regions, prescribing practices, or patient populations.

## Practical Value

The main value of the project is methodological and operational: it demonstrates a reproducible EHR-based clinical analytics workflow with transparent definitions, multivariable modeling, absolute risk interpretation, and SAS/Python validation. The results should be treated as association evidence that could motivate more rigorous causal designs or prospective clinical questions.
