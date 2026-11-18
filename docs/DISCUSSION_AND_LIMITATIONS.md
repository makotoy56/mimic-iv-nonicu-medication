# Discussion And Limitations

## Interpretation

**Patient-aware update (2026-11-17):** Current uncertainty summaries use 500 prespecified patient-cluster bootstrap draws, carrying all eligible admissions per sampled patient. Firth point estimates and all exposure/cohort/adjustment definitions are unchanged. Historical admission-independent profile intervals remain available separately. See [patient-aware validation](PATIENT_AWARE_VALIDATION.md).

Documented early inpatient RAAS prescription exposure was associated with lower in-hospital mortality in this adult non-ICU MIMIC-IV cohort after multivariable adjustment. The association was present on both the relative scale, using odds ratios, and the absolute scale, using differences in model-predicted risk.

The absolute-risk framing is important because the baseline event rate in this non-ICU cohort is low. A percentage-point difference in adjusted predicted risk is more directly interpretable for clinical analytics and outcomes research audiences than an odds ratio alone.

The corrected landmark cohort requires confirmed survival and continued hospitalization beyond 24 hours and contains 342,519 admissions/1,769 deaths. The supplementary Firth ordinary/proxy ORs were 0.356/0.382, with 95% patient-cluster intervals 0.292–0.423 and 0.315–0.453. These fits converged without removing adjustment categories. The estimator differs from the original MLE; the Firth estimator alone does not correct repeated-admission dependence, which is addressed separately by patient-cluster resampling. Neither establishes causality. Historical MLE OR assets are retained unchanged, and the new Firth figure is explicitly labeled.

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

The analytic unit is the hospital admission (`hadm_id`), and patients may contribute multiple admissions. Historical profile intervals treated admissions as independent. Added patient-cluster resampling carries all eligible admissions of each sampled patient and supplies current OR/risk/AME intervals. Added discrimination evaluation holds out entire patients. These procedures address dependence and train/test overlap separately, while leaving residual confounding unresolved.

## Outcome And Generalizability

The outcome is in-hospital mortality. The analysis does not evaluate post-discharge mortality, readmission, adverse events, renal outcomes, or disease-specific endpoints.

MIMIC-IV reflects care delivered within its source health system and time period. Findings may not generalize to all hospitals, geographic regions, prescribing practices, or patient populations.

## Practical Value

The main value of the project is methodological and operational: it demonstrates a reproducible EHR-based clinical analytics workflow with transparent definitions, multivariable modeling, absolute risk interpretation, and documented Python numerical checks. The results should be treated as association evidence that could motivate more rigorous causal designs or prospective clinical questions.

## Selection and temporal data quality

The cohort includes hospital observation/day-case admission categories; it is not a strict inpatient-only filter. Excluding ICU use over the entire stay conditions on post-admission events and may induce selection bias. Constructing that cohort before calculating the exposure flag does not make eligibility statistically independent of exposure or severity. The original primary cohort retains 96 admission/discharge timestamp inversions, while the corrected landmark analysis excludes inconsistent records. These choices and limitations are explicit; no cohort rule was silently changed.

Age-specific curves are main-effects model predictions at a typical mean covariate profile. Their absolute differences can vary with age without an exposure-by-age interaction; they are not formal evidence of effect modification.

The 500-draw percentile bootstrap intervals have Monte Carlo variability; passing the numerical fit checks does not demonstrate nominal coverage or model correctness. The patient-disjoint split is a single internal holdout, not external validation or evidence that model performance improved.

The patient-disjoint holdout is an internal evaluation of retrospective discrimination on the full admission cohort. It uses prescription records from 0–<24 hours while including deaths within 24 hours, and applies no 24-hour survival/continued-hospitalization eligibility filter. There is no fixed clinical prediction time or prospective prediction horizon: ROC AUC 0.860635 and PR AUC 0.117607 do not describe admission-time or 24-hour prognostic performance. Patient separation and train-only preprocessing address patient overlap and preprocessing leakage, not temporal feature availability. The 24-hour landmark association analyses separately require confirmed survival and continued hospitalization strictly beyond 24 hours and evaluate subsequent in-hospital death; they use a different eligible cohort.
