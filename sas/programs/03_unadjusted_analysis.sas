/* 03_unadjusted_analysis.sas */
/* Reproduce unadjusted outcome summaries for the non-ICU RAAS analytic dataset. */
options nodate nonumber;
ods noproctitle;
%let output_path=/home/u64438249/portfolio-non-ICU/output;
libname data "/home/u64438249/portfolio-non-ICU/data";

/* Match the validation-ready Python output column names and group definitions. */
proc sql;
	create table work.unadjusted_counts as select raas_any_early as exposure, case 
		when raas_any_early=0 then "No early RAAS inhibitor use" when 
		raas_any_early=1 then "Early RAAS inhibitor use" else "Missing" end as 
		exposure_group length=32, count(*) as n, sum(hospital_expire_flag) as deaths, 
		calculated n - calculated deaths as non_deaths, mean(hospital_expire_flag) as 
		mortality_proportion format=best16., case when calculated non_deaths > 0 then 
		calculated deaths / calculated non_deaths else .
end as crude_odds format=best16.
    from data.nonicu_analysis where raas_any_early in (0, 1) and 
		hospital_expire_flag in (0, 1) group by raas_any_early order by 
		raas_any_early;
	select crude_odds into :reference_odds trimmed from work.unadjusted_counts 
		where exposure=0;
	create table work.sas_unadjusted_outcomes as select exposure, exposure_group, 
		n, deaths, non_deaths, mortality_proportion, crude_odds, crude_odds / 
		&reference_odds as crude_or_vs_no_raas format=best16.
    from work.unadjusted_counts order by exposure;
quit;

proc export data=work.sas_unadjusted_outcomes 
		outfile="&output_path/sas_unadjusted_outcomes.csv" dbms=csv replace;
run;

ods pdf file="&output_path/03_unadjusted_analysis.pdf" style=journal 
	startpage=yes;
title1 "Non-ICU RAAS Medication Study Using MIMIC-IV";
footnote1 "Source: MIMIC-IV derived analytic dataset exported from BigQuery.";
footnote2 "Patient-level derived data are used only for local/SAS validation and are not shared publicly.";
title2 "Unadjusted In-Hospital Mortality by Early RAAS Exposure";

proc print data=work.sas_unadjusted_outcomes noobs label;
	var exposure exposure_group n deaths non_deaths mortality_proportion 
		crude_odds crude_or_vs_no_raas;
	label exposure="Exposure" exposure_group="Exposure Group" n="N" 
		deaths="Deaths" non_deaths="Non-Deaths" 
		mortality_proportion="Mortality Proportion" crude_odds="Crude Odds" 
		crude_or_vs_no_raas="Crude Odds Ratio vs No Early RAAS";
run;

title2 "PROC FREQ: Early RAAS Exposure by In-Hospital Mortality";

proc freq data=data.nonicu_analysis;
	tables raas_any_early * hospital_expire_flag / missing norow nocol nopercent;
run;

title2 "Unadjusted Logistic Regression: In-Hospital Mortality";
ods output ParameterEstimates=work.logistic_parameter_estimates 
	OddsRatios=work.logistic_odds_ratios;

proc logistic data=data.nonicu_analysis;
	model hospital_expire_flag(event='1')=raas_any_early;
run;

title2 "Crude Logistic Model Parameter Estimates";

proc print data=work.logistic_parameter_estimates noobs label;
run;

title2 "Crude Logistic Odds Ratio Estimates";

proc print data=work.logistic_odds_ratios noobs label;
run;

ods pdf close;
title;
footnote;
ods proctitle;