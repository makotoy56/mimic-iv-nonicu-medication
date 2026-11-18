-- Supplementary prediction-time evaluation; SELECT only, no main-table changes.
-- The risk set is defined at prediction time, not by future entire-stay ICU use.
-- RAAS features require both an early prescribed start and a linked POE time <=24h.
WITH base AS (
  SELECT subject_id, hadm_id, admittime, dischtime, deathtime,
         hospital_expire_flag, age, gender
  FROM `mimic-iv-portfolio.nonicu_raas.base_admissions`
),
ward_units AS (SELECT unit FROM UNNEST(['Cardiac Surgery', 'Cardiology', 'Cardiology Surgery Intermediate', 'Hematology/Oncology', 'Hematology/Oncology Intermediate', 'Labor & Delivery', 'Med/Surg', 'Med/Surg/GYN', 'Med/Surg/Trauma', 'Medical/Surgical (Gynecology)', 'Medicine', 'Medicine/Cardiology', 'Medicine/Cardiology Intermediate', 'Neuro Intermediate', 'Neuro Stepdown', 'Neurology', 'Observation', 'Obstetrics (Postpartum & Antepartum)', 'Obstetrics Antepartum', 'Obstetrics Postpartum', 'Oncology', 'Psychiatry', 'Surgery', 'Surgery/Pancreatic/Biliary/Bariatric', 'Surgery/Trauma', 'Surgery/Vascular/Intermediate', 'Surgical Intermediate', 'Thoracic Surgery', 'Transplant', 'Vascular']) AS unit),
icu_units AS (SELECT unit FROM UNNEST(['Cardiac Vascular Intensive Care Unit (CVICU)', 'Coronary Care Unit (CCU)', 'Intensive Care Unit (ICU)', 'Medical Intensive Care Unit (MICU)', 'Medical/Surgical Intensive Care Unit (MICU/SICU)', 'Neuro Surgical Intensive Care Unit (Neuro SICU)', 'Surgical Intensive Care Unit (SICU)', 'Trauma SICU (TSICU)']) AS unit),
icu AS (
  SELECT subject_id, hadm_id, MIN(intime) AS first_icu_intime,
         COUNTIF(intime IS NULL) AS icu_unknown_intime
  FROM `physionet-data.mimiciv_3_1_icu.icustays`
  GROUP BY subject_id, hadm_id
),
poe AS (
  SELECT subject_id, hadm_id, poe_id, MIN(ordertime) AS ordertime,
         COUNT(*) AS poe_rows
  FROM `physionet-data.mimiciv_3_1_hosp.poe`
  WHERE poe_id IS NOT NULL
  GROUP BY subject_id, hadm_id, poe_id
),
transfer_icu AS (
  SELECT subject_id,hadm_id,MIN(intime) AS first_transfer_icu_intime,
         COUNTIF(intime IS NULL) AS unknown_transfer_icu_intime
  FROM `physionet-data.mimiciv_3_1_hosp.transfers`
  WHERE careunit IN (SELECT unit FROM icu_units)
  GROUP BY subject_id,hadm_id
),
prediction_points AS (
  SELECT b.subject_id,b.hadm_id,hours,DATETIME_ADD(b.admittime,INTERVAL hours HOUR) AS prediction_time
  FROM base b CROSS JOIN UNNEST([0,24]) AS hours
),
location_candidates AS (
  SELECT p.subject_id,p.hadm_id,p.hours,
         COUNT(t.transfer_id) AS location_records,
         COUNTIF(t.outtime IS NULL AND t.transfer_id IS NOT NULL) AS missing_interval_end,
         COUNTIF((t.careunit IS NULL OR UPPER(t.careunit)='UNKNOWN') AND t.transfer_id IS NOT NULL) AS unknown_units,
         COUNT(DISTINCT t.careunit) AS distinct_units,
         MIN(t.careunit) AS single_unit
  FROM prediction_points p
  LEFT JOIN `physionet-data.mimiciv_3_1_hosp.transfers` t
    ON p.subject_id=t.subject_id AND p.hadm_id=t.hadm_id
   AND LOWER(t.eventtype) IN ('ed','admit','transfer')
   AND t.intime<=p.prediction_time
   AND (t.outtime>p.prediction_time OR t.outtime IS NULL)
  GROUP BY p.subject_id,p.hadm_id,p.hours
),
locations AS (
  SELECT *,CASE
    WHEN location_records=0 THEN 'no_covering_location'
    WHEN missing_interval_end>0 THEN 'unconfirmed_interval_end'
    WHEN unknown_units>0 OR distinct_units=0 THEN 'unconfirmed_unit'
    WHEN distinct_units>1 THEN 'overlapping_locations'
    WHEN single_unit IN (SELECT unit FROM ward_units) THEN 'confirmed_non_icu_ward'
    ELSE 'not_target_ward' END AS location_status
  FROM location_candidates
),
location_pivot AS (
  SELECT subject_id,hadm_id,
    MAX(IF(hours=0,location_status,NULL)) AS location_status_0h,
    MAX(IF(hours=24,location_status,NULL)) AS location_status_24h
  FROM locations GROUP BY subject_id,hadm_id
),
early_raas AS (
  SELECT b.subject_id, b.hadm_id, r.poe_id, r.starttime, p.ordertime, p.poe_rows,
         DATETIME_ADD(b.admittime, INTERVAL 24 HOUR) AS prediction_time_24h
  FROM base b
  JOIN `physionet-data.mimiciv_3_1_hosp.prescriptions` r
    ON b.subject_id = r.subject_id AND b.hadm_id = r.hadm_id
  LEFT JOIN poe p
    ON r.subject_id = p.subject_id AND r.hadm_id = p.hadm_id AND r.poe_id = p.poe_id
  WHERE r.starttime >= b.admittime
    AND r.starttime < DATETIME_ADD(b.admittime, INTERVAL 24 HOUR)
    AND REGEXP_CONTAINS(LOWER(r.drug),
      r'(lisinopril|enalapril|captopril|ramipril|benazepril|quinapril|fosinopril|perindopril|trandolapril|moexipril|losartan|valsartan|candesartan|irbesartan|telmisartan|olmesartan|eprosartan|azilsartan)')
),
rx AS (
  SELECT subject_id, hadm_id, COUNT(*) AS early_raas_records,
         COUNTIF(ordertime IS NULL) AS raas_unverified_order_time_records,
         COUNTIF(ordertime > prediction_time_24h) AS raas_late_order_records,
         COUNTIF(poe_rows > 1) AS raas_duplicate_poe_records,
         MAX(IF(ordertime <= prediction_time_24h, 1, 0)) AS raas_recorded_by_24h,
         MAX(IF(ordertime <= prediction_time_24h, ordertime, NULL)) AS last_qualifying_order_time,
         MAX(IF(ordertime <= prediction_time_24h, starttime, NULL)) AS last_qualifying_start_time
  FROM early_raas
  GROUP BY subject_id, hadm_id
)
SELECT b.*,
       (SELECT MIN(x) FROM UNNEST([i.first_icu_intime,ti.first_transfer_icu_intime]) x) AS first_icu_intime,
       i.first_icu_intime AS icustays_first_intime,ti.first_transfer_icu_intime,
       COALESCE(i.icu_unknown_intime, 0)+COALESCE(ti.unknown_transfer_icu_intime,0) AS icu_unknown_intime,
       l.location_status_0h,l.location_status_24h,
       COALESCE(r.early_raas_records, 0) AS early_raas_records,
       COALESCE(r.raas_unverified_order_time_records, 0) AS raas_unverified_order_time_records,
       COALESCE(r.raas_late_order_records, 0) AS raas_late_order_records,
       COALESCE(r.raas_duplicate_poe_records, 0) AS raas_duplicate_poe_records,
       COALESCE(r.raas_recorded_by_24h, 0) AS raas_recorded_by_24h,
       r.last_qualifying_order_time, r.last_qualifying_start_time
FROM base b
LEFT JOIN icu i ON b.subject_id = i.subject_id AND b.hadm_id = i.hadm_id
LEFT JOIN rx r ON b.subject_id = r.subject_id AND b.hadm_id = r.hadm_id

LEFT JOIN transfer_icu ti ON b.subject_id=ti.subject_id AND b.hadm_id=ti.hadm_id
LEFT JOIN location_pivot l ON b.subject_id=l.subject_id AND b.hadm_id=l.hadm_id
