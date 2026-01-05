-- 01_collapse_race_categories.sql
-- Purpose:
-- Collapse race categories to reduce sparsity and avoid quasi-complete separation,
-- while preserving interpretability.

CREATE OR REPLACE TABLE `mimic-iv-portfolio.nonicu_raas.base_admissions_racegrp` AS
WITH src AS (
  SELECT
    *,
    UPPER(TRIM(race)) AS race_u
  FROM `mimic-iv-portfolio.nonicu_raas.base_admissions`
)
SELECT
  *,
  CASE
    WHEN race_u IS NULL OR race_u = '' THEN 'Unknown'

    WHEN STARTS_WITH(race_u, 'WHITE') THEN 'White'
    WHEN STARTS_WITH(race_u, 'BLACK') THEN 'Black'
    WHEN STARTS_WITH(race_u, 'ASIAN') THEN 'Asian'

    WHEN STARTS_WITH(race_u, 'HISPANIC') OR STARTS_WITH(race_u, 'LATINO') THEN 'Hispanic'

    ELSE 'Other'
  END AS race_group
FROM src;
