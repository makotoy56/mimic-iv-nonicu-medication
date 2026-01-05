-- 01_build_base_hosp_admissions.sql
-- Build a base adult hospital-admission cohort (HADM-level) from MIMIC-IV v3.1
-- Includes demographics and an approximate age-at-admission based on anchor variables.

CREATE OR REPLACE TABLE `mimic-iv-portfolio.nonicu_raas.base_admissions` AS
WITH base_adm AS (
  SELECT
    a.subject_id,
    a.hadm_id,
    a.admittime,
    a.dischtime,
    a.deathtime,
    a.hospital_expire_flag,
    a.admission_type,
    a.admission_location,
    a.discharge_location,
    a.insurance,
    a.language,
    a.marital_status,
    a.race
  FROM `physionet-data.mimiciv_3_1_hosp.admissions` AS a
),

pt AS (
  SELECT
    p.subject_id,
    p.gender,
    p.anchor_age,
    p.anchor_year,
    p.anchor_year_group
  FROM `physionet-data.mimiciv_3_1_hosp.patients` AS p
),

with_demo AS (
  SELECT
    b.*,
    p.gender,
    p.anchor_age,
    p.anchor_year,
    p.anchor_year_group,

    -- Approximate age at admission:
    -- MIMIC-IV provides anchor_age at anchor_year (de-identified).
    -- A common approximation is: anchor_age + (admission_year - anchor_year).
    (p.anchor_age + (EXTRACT(YEAR FROM b.admittime) - p.anchor_year)) AS age_at_admit,

    -- Hospital length of stay (days)
    DATETIME_DIFF(b.dischtime, b.admittime, HOUR) / 24.0 AS hosp_los
  FROM base_adm AS b
  JOIN pt AS p
    ON b.subject_id = p.subject_id
)

SELECT
  subject_id,
  hadm_id,
  admittime,
  dischtime,
  deathtime,
  hospital_expire_flag,
  admission_type,
  admission_location,
  discharge_location,
  insurance,
  language,
  marital_status,
  race,
  gender,
  age_at_admit AS age,
  anchor_age,
  anchor_year,
  anchor_year_group,
  hosp_los
FROM with_demo
WHERE age_at_admit >= 18;