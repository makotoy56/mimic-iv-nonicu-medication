-- 02_exclude_icu_admissions.sql
-- Exclude any hospital admissions (HADM) that had an ICU stay.
-- Result: non-ICU adult hospital admissions cohort (HADM-level).

CREATE OR REPLACE TABLE `mimic-iv-portfolio.nonicu_raas.nonicu_admissions` AS
WITH icu_hadm AS (
  SELECT DISTINCT
    subject_id,
    hadm_id
  FROM `physionet-data.mimiciv_3_1_icu.icustays`
),

base AS (
  SELECT *
  FROM `mimic-iv-portfolio.nonicu_raas.base_admissions_racegrp`
)

SELECT
  b.*
FROM base AS b
LEFT JOIN icu_hadm AS i
  ON b.subject_id = i.subject_id
 AND b.hadm_id   = i.hadm_id
WHERE i.hadm_id IS NULL;