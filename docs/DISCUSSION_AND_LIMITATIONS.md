# Discussion And Limitations

## Interpretation

Early RAAS inhibitor exposure was associated with lower in-hospital mortality in this adult non-ICU MIMIC-IV cohort after multivariable adjustment. The association was present on both the relative scale, using odds ratios, and the absolute scale, using predicted risks and average marginal effects.

The absolute-risk framing is important because the baseline event rate in this non-ICU cohort is low. A percentage-point risk difference is more directly interpretable for clinical analytics and outcomes research audiences than an odds ratio alone.

## Observational Design

This study is observational and hypothesis-generating. It cannot establish that early RAAS inhibitor exposure causes lower mortality.

Although exposure ascertainment is restricted to the first 24 hours after admission and models adjust for measured demographic and admission-related variables, residual confounding may remain. Potential sources include:

- Confounding by indication
- Differences in chronic outpatient medication history
- Comorbidity burden not fully represented in the primary model
- Acute physiologic severity and laboratory findings
- Clinician prescribing behavior
- Medication discontinuation, dose, duration, and adherence
- Selection effects related to early survival and treatment eligibility

## Exposure Limitations

The exposure definition uses inpatient prescription records. It does not directly measure outpatient chronic RAAS inhibitor use, medication adherence before admission, inpatient administration confirmation, dose intensity, or duration of therapy.

Restricting exposure to the first 24 hours improves temporal clarity but does not fully eliminate immortal-time bias or reverse-causation concerns.

## Outcome And Generalizability

The outcome is in-hospital mortality. The analysis does not evaluate post-discharge mortality, readmission, adverse events, renal outcomes, or disease-specific endpoints.

MIMIC-IV reflects care delivered within its source health system and time period. Findings may not generalize to all hospitals, geographic regions, prescribing practices, or patient populations.

## Practical Value

The main value of the project is methodological and operational: it demonstrates a reproducible EHR-based clinical analytics workflow with transparent definitions, multivariable modeling, absolute risk interpretation, and SAS/Python validation. The results should be treated as association evidence that could motivate more rigorous causal designs or prospective clinical questions.
