/* 02_baseline_table.sas */
/* Generate baseline summary tables for the non-ICU RAAS analytic dataset. */

options nodate nonumber;
ods noproctitle;

%let output_path=/home/u64438249/portfolio-non-ICU/output;
libname data "/home/u64438249/portfolio-non-ICU/data";

/* Create report-only labels for categorical missingness without changing source data. */
data work.baseline_report;
    set data.nonicu_analysis;

    length insurance_display marital_status_display $64;

    if missing(insurance) then insurance_display = "Missing";
    else insurance_display = strip(insurance);

    if missing(marital_status) then marital_status_display = "Missing";
    else marital_status_display = strip(marital_status);

    label insurance_display = "Insurance"
          marital_status_display = "Marital Status";
run;

ods pdf file="&output_path/02_baseline_table.pdf" style=journal startpage=yes;

title1 "Non-ICU RAAS Medication Study Using MIMIC-IV";
footnote1 "Source: MIMIC-IV derived analytic dataset exported from BigQuery.";
footnote2 "Patient-level derived data are used only for local/SAS validation and are not shared publicly.";

title2 "Table 1A. Overall Summary of Continuous Variables";
proc means data=work.baseline_report n mean std median q1 q3 min max maxdec=2;
    var age hosp_los;
run;

title2 "Table 1B. Continuous Variables Stratified by In-Hospital Mortality";
proc means data=work.baseline_report n mean std median q1 q3 min max maxdec=2;
    class hospital_expire_flag;
    var age hosp_los;
run;

title2 "Table 1C. Overall Summary of Categorical Variables";
proc freq data=work.baseline_report;
    tables gender
           hospital_expire_flag
           raas_any_early
           acei_early
           arb_early
           race_group
           insurance_display
           marital_status_display / missing;
run;

title2 "Data Quality Check: Hospital Length of Stay";
proc sql;
    select count(*) as records label="Records" format=comma12.,
           sum(case when missing(hosp_los) then 1 else 0 end)
               as hosp_los_missing label="Missing hosp_los" format=comma12.,
           sum(case when hosp_los < 0 then 1 else 0 end)
               as hosp_los_negative label="hosp_los < 0" format=comma12.,
           min(hosp_los) as hosp_los_min label="Minimum hosp_los" format=8.2,
           max(hosp_los) as hosp_los_max label="Maximum hosp_los" format=8.2
    from work.baseline_report;
quit;

ods pdf close;

title;
footnote;
ods proctitle;
