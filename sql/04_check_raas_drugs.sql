-- 04_define_exposure_raas_early.sql

-- Purpose:
-- Inspect actual drug names contributing to early RAAS exposure

WITH rx_24h AS (
  SELECT
    LOWER(r.drug) AS drug_lc
  FROM `mimic-iv-portfolio.nonicu_raas.nonicu_admissions` AS c
  JOIN `physionet-data.mimiciv_3_1_hosp.prescriptions` AS r
    ON c.subject_id = r.subject_id
   AND c.hadm_id   = r.hadm_id
  WHERE r.starttime >= c.admittime
    AND r.starttime < TIMESTAMP_ADD(c.admittime, INTERVAL 24 HOUR)
    AND r.drug IS NOT NULL
)

SELECT
  CASE
    WHEN REGEXP_CONTAINS(drug_lc,
      r'(lisinopril|enalapril|captopril|ramipril|benazepril|quinapril|fosinopril|perindopril|trandolapril|moexipril)'
    ) THEN 'ACEi'
    WHEN REGEXP_CONTAINS(drug_lc,
      r'(losartan|valsartan|candesartan|irbesartan|telmisartan|olmesartan|eprosartan|azilsartan|sacubitril)'
    ) THEN 'ARB'
    ELSE 'Other'
  END AS class,
  drug_lc,
  COUNT(*) AS n_rows
FROM rx_24h
GROUP BY class, drug_lc
HAVING class IN ('ACEi', 'ARB')
ORDER BY n_rows DESC;