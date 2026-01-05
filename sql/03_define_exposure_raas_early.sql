-- 03_define_exposure_raas_early.sql
-- Non-ICU RAAS exposure using an early-in-admission proxy:
-- RAAS exposure = any ACEi/ARB prescription with starttime within 24 hours after admittime.

CREATE OR REPLACE TABLE `mimic-iv-portfolio.nonicu_raas.exposure_raas_early` AS
WITH cohort AS (
  SELECT
    subject_id,
    hadm_id,
    admittime
  FROM `mimic-iv-portfolio.nonicu_raas.nonicu_admissions`
  WHERE admittime IS NOT NULL
),

rx AS (
  SELECT
    subject_id,
    hadm_id,
    starttime,
    drug
  FROM `physionet-data.mimiciv_3_1_hosp.prescriptions`
  WHERE hadm_id IS NOT NULL
    AND starttime IS NOT NULL
    AND drug IS NOT NULL
),

rx_24h AS (
  SELECT
    c.subject_id,
    c.hadm_id,
    LOWER(r.drug) AS drug_lc
  FROM cohort AS c
  JOIN rx AS r
    ON c.subject_id = r.subject_id
   AND c.hadm_id   = r.hadm_id
  WHERE TIMESTAMP(r.starttime) >= TIMESTAMP(c.admittime)
    AND TIMESTAMP(r.starttime) < TIMESTAMP_ADD(TIMESTAMP(c.admittime), INTERVAL 24 HOUR)
),

flags AS (
  SELECT
    subject_id,
    hadm_id,
    MAX(CASE WHEN REGEXP_CONTAINS(drug_lc,
      r'(lisinopril|enalapril|captopril|ramipril|benazepril|quinapril|fosinopril|perindopril|trandolapril|moexipril)'
    ) THEN 1 ELSE 0 END) AS acei_early,
    MAX(CASE WHEN REGEXP_CONTAINS(drug_lc,
      r'(losartan|valsartan|candesartan|irbesartan|telmisartan|olmesartan|eprosartan|azilsartan)'
    ) THEN 1 ELSE 0 END) AS arb_early
  FROM rx_24h
  GROUP BY subject_id, hadm_id
)

SELECT
  c.subject_id,
  c.hadm_id,
  COALESCE(f.acei_early, 0) AS acei_early,
  COALESCE(f.arb_early, 0)  AS arb_early,
  CASE WHEN COALESCE(f.acei_early,0)=1 AND COALESCE(f.arb_early,0)=1 THEN 1 ELSE 0 END AS raas_both_early,
  CASE WHEN COALESCE(f.acei_early,0)=1 OR  COALESCE(f.arb_early,0)=1 THEN 1 ELSE 0 END AS raas_any_early
FROM cohort AS c
LEFT JOIN flags AS f
  ON c.subject_id = f.subject_id
 AND c.hadm_id   = f.hadm_id;