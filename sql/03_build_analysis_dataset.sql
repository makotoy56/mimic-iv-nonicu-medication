-- 03_build_analysis_dataset.sql
-- Build the final analytic dataset (HADM-level).

CREATE OR REPLACE TABLE `mimic-iv-portfolio.nonicu_raas.analysis_dataset` AS
WITH cohort AS (
  SELECT *
  FROM `mimic-iv-portfolio.nonicu_raas.nonicu_admissions`
),
expo AS (
  SELECT *
  FROM `mimic-iv-portfolio.nonicu_raas.exposure_raas_early`
)

SELECT
  c.*,
  COALESCE(e.acei_early, 0) AS acei_early,
  COALESCE(e.arb_early, 0) AS arb_early,
  COALESCE(e.raas_both_early, 0) AS raas_both_early,
  COALESCE(e.raas_any_early, 0) AS raas_any_early
FROM cohort AS c
LEFT JOIN expo AS e
  USING (subject_id, hadm_id);