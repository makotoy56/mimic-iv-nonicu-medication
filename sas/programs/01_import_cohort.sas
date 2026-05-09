/* 01_import.sas */
/* Import BigQuery-exported non-ICU analytic dataset */

options nodate nonumber;

%let input_path=/home/u64438249/portfolio-non-ICU/input;
%let output_path=/home/u64438249/portfolio-non-ICU/output;

libname data "/home/u64438249/portfolio-non-ICU/data";

ods pdf file="&output_path/01_import_results.pdf" style=journal startpage=yes;

title1 "Non-ICU RAAS Medication Study Using MIMIC-IV";
footnote1 "Source: MIMIC-IV derived analytic dataset exported from BigQuery.";
footnote2 "Patient-level derived data are used only for local/SAS validation and are not shared publicly.";

title2 "Step 1: Import Analytic Dataset from CSV";
proc import datafile="&input_path/nonicu_raas__analysis_dataset.csv"
    out=data.nonicu_analysis
    dbms=csv
    replace;
    guessingrows=max;
    getnames=yes;
run;

title2 "Step 2: Dataset Structure";
proc contents data=data.nonicu_analysis varnum;
run;

title2 "Step 3: First 10 Observations Without Patient Identifiers";
proc print data=data.nonicu_analysis(obs=10);
    var hadm_id hospital_expire_flag raas_any_early age gender race_group hosp_los;
run;

title2 "Step 4: Frequency Distribution of Key Variables";
proc freq data=data.nonicu_analysis;
    tables gender hospital_expire_flag raas_any_early acei_early arb_early / missing;
run;

title2 "Step 5: Summary Statistics for Continuous Variables";
proc means data=data.nonicu_analysis n mean std median min max;
    var age hosp_los;
run;

title;
footnote;

ods pdf close;