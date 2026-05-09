/* 04_multivariable_logistic.sas */
/* Reproduce the primary adjusted logistic model for the non-ICU RAAS analytic dataset. */

options nodate nonumber;
ods noproctitle;

%let output_path=/home/u64438249/portfolio-non-ICU/output;
libname data "/home/u64438249/portfolio-non-ICU/data";

/* Match the Python model matrix:
   exposure + age + one-hot categorical covariates with missing values as Unknown.
   Reference categories mirror pandas get_dummies(drop_first=True). */
data work.model_input;
    set data.nonicu_analysis;

    exposure = raas_any_early;

    length gender_model $16
           race_group_model $32
           admission_type_model $64
           insurance_model $32
           anchor_year_group_model $32;

    if missing(gender) then gender_model = "Unknown";
    else gender_model = strip(gender);

    if missing(race_group) then race_group_model = "Unknown";
    else race_group_model = strip(race_group);

    if missing(admission_type) then admission_type_model = "Unknown";
    else admission_type_model = strip(admission_type);

    if missing(insurance) then insurance_model = "Unknown";
    else insurance_model = strip(insurance);

    if missing(anchor_year_group) then anchor_year_group_model = "Unknown";
    else anchor_year_group_model = strip(anchor_year_group);

    label exposure = "Early RAAS inhibitor exposure"
          gender_model = "Gender"
          race_group_model = "Race Group"
          admission_type_model = "Admission Type"
          insurance_model = "Insurance"
          anchor_year_group_model = "Anchor Year Group";
run;

data work.model_specification;
    length role $24 variable $32 reference $64;

    role = "Outcome"; variable = "hospital_expire_flag"; reference = "Event = 1"; output;
    role = "Main exposure"; variable = "raas_any_early"; reference = "Modeled as exposure"; output;
    role = "Continuous covariate"; variable = "age"; reference = "Per one year"; output;
    role = "Class covariate"; variable = "gender"; reference = "F"; output;
    role = "Class covariate"; variable = "race_group"; reference = "Asian"; output;
    role = "Class covariate"; variable = "admission_type"; reference = "AMBULATORY OBSERVATION"; output;
    role = "Class covariate"; variable = "insurance"; reference = "Medicaid"; output;
    role = "Class covariate"; variable = "anchor_year_group"; reference = "2008 - 2010"; output;
run;

ods pdf file="&output_path/04_multivariable_logistic.pdf" style=journal startpage=yes;

title1 "Non-ICU RAAS Medication Study Using MIMIC-IV";
footnote1 "Source: MIMIC-IV derived analytic dataset exported from BigQuery.";
footnote2 "Patient-level derived data are used only for local/SAS validation and are not shared publicly.";

title2 "Primary Adjusted Logistic Regression Model Specification";
proc print data=work.model_specification noobs label;
    label role = "Role"
          variable = "Variable"
          reference = "Reference / Coding";
run;

title2 "Primary Adjusted Logistic Regression: In-Hospital Mortality";
ods output ParameterEstimates=work.parameter_estimates
           CLOddsWald=work.odds_ratios
           FitStatistics=work.fit_statistics;
proc logistic data=work.model_input;
    class gender_model(ref='F')
          race_group_model(ref='Asian')
          admission_type_model(ref='AMBULATORY OBSERVATION')
          insurance_model(ref='Medicaid')
          anchor_year_group_model(ref='2008 - 2010') / param=ref;
    model hospital_expire_flag(event='1') =
          exposure
          age
          gender_model
          race_group_model
          admission_type_model
          insurance_model
          anchor_year_group_model / clodds=wald;
run;

/* Validation-ready parameter output using Python-compatible term meanings. */
data work.sas_logistic_parameters;
    set work.parameter_estimates;

    length term class_value $128;

    if variable = "Intercept" then term = "const";
    else if variable = "exposure" then term = "exposure";
    else if variable = "age" then term = "age";
    else if variable = "gender_model" then term = cats("gender_", classval0);
    else if variable = "race_group_model" then term = cats("race_group_", classval0);
    else if variable = "admission_type_model" then term = cats("admission_type_", classval0);
    else if variable = "insurance_model" then term = cats("insurance_", classval0);
    else if variable = "anchor_year_group_model"
         or variable = "anchor_year_group_mo"
         or index(variable, "anchor_year_group") = 1 then do;
        class_value = strip(classval0);
        class_value = tranwrd(class_value, " - ", "_");
        class_value = compress(class_value, " ");
        term = cats("anchor_year_group_", class_value);
    end;
    else term = strip(variable);

    coefficient = estimate;
    std_error = stderr;
    coefficient_ci_lower = estimate - quantile("NORMAL", 0.975) * stderr;
    coefficient_ci_upper = estimate + quantile("NORMAL", 0.975) * stderr;
    odds_ratio = exp(coefficient);
    odds_ratio_ci_lower = exp(coefficient_ci_lower);
    odds_ratio_ci_upper = exp(coefficient_ci_upper);
    ci_lower = odds_ratio_ci_lower;
    ci_upper = odds_ratio_ci_upper;
    p_value = probchisq;

    keep term
         coefficient
         std_error
         coefficient_ci_lower
         coefficient_ci_upper
         odds_ratio
         odds_ratio_ci_lower
         odds_ratio_ci_upper
         ci_lower
         ci_upper
         p_value;

    label term = "Model Term"
          coefficient = "Log-Odds Coefficient"
          std_error = "Standard Error"
          coefficient_ci_lower = "Coefficient 95% CI Lower"
          coefficient_ci_upper = "Coefficient 95% CI Upper"
          odds_ratio = "Odds Ratio"
          odds_ratio_ci_lower = "Odds Ratio 95% CI Lower"
          odds_ratio_ci_upper = "Odds Ratio 95% CI Upper"
          ci_lower = "Odds Ratio 95% CI Lower"
          ci_upper = "Odds Ratio 95% CI Upper"
          p_value = "P-Value";
run;

proc export data=work.sas_logistic_parameters
    outfile="&output_path/sas_logistic_parameters.csv"
    dbms=csv
    replace;
run;

title2 "Validation-Ready Logistic Parameter Output";
proc print data=work.sas_logistic_parameters noobs label;
run;

title2 "PROC LOGISTIC Odds Ratio Estimates and Wald Confidence Intervals";
proc print data=work.odds_ratios noobs label;
run;

title2 "PROC LOGISTIC Fit Statistics";
proc print data=work.fit_statistics noobs label;
run;

ods pdf close;

title;
footnote;
ods proctitle;
