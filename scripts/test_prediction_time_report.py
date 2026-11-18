"""Offline consistency of published prediction-time aggregates and explanations."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from quarto_normalize_outputs import publish_report,ReportResources
R=Path(__file__).resolve().parents[1];out=R/'python/outputs'
metrics=pd.read_csv(out/'prediction_time_metrics.csv');cohorts=pd.read_csv(out/'prediction_time_cohorts.csv')
exclusions=pd.read_csv(out/'prediction_time_exclusions.csv');cal=pd.read_csv(out/'prediction_time_calibration.csv')
receipt=json.loads((out/'prediction_time_execution.json').read_text())
assert len(metrics)==3 and metrics.converged.all() and metrics.overlapping_patients.eq(0).all()
texts=[(R/p).read_text() for p in ['README.md','reports/nonicu_raas_mortality_report.qmd','docs/PREDICTION_TIME_VALIDATION.md']]
for x in metrics.itertuples():
 assert x.features in ['age,gender','age,gender,raas_recorded_by_24h']
 assert x.bootstrap_requested==500 and x.bootstrap_successful+x.bootstrap_failed_one_class==500
 assert bool(x.interval_available)==(x.bootstrap_successful>=475)
 for name in ['roc_auc','pr_auc_average_precision','brier']:
  assert all(f'{getattr(x,name):.6f}' in t for t in texts),(x.model,name)
 if x.interval_available:
  for name in ['roc_auc_CI_lower','roc_auc_CI_upper','pr_auc_CI_lower','pr_auc_CI_upper']:
   assert np.isfinite(getattr(x,name)) and all(f'{getattr(x,name):.6f}' in t for t in texts)
 else:
  assert x.prediction_hours==0
  assert all(pd.isna(getattr(x,k)) for k in ['roc_auc_CI_lower','roc_auc_CI_upper','pr_auc_CI_lower','pr_auc_CI_upper','brier_CI_lower','brier_CI_upper'])
  assert all('CI withheld' in t and '467/500' in t for t in texts)
 bins=cal.loc[cal.model.eq(x.model)]
 assert bins.admissions.sum()==x.test_admissions and bins.deaths.sum()==x.test_deaths
 assert bool(bins.observed_CI_lower.notna().all())==bool(x.interval_available)
for x in cohorts.itertuples():
 assert x.train_admissions+x.test_admissions==x.eligible_admissions and x.train_deaths+x.test_deaths==x.deaths
 assert x.overlapping_patients==0 and x.later_icu_admissions_retained>0
 flow=exclusions.loc[exclusions.prediction_hours.eq(x.prediction_hours)]
 assert flow.admissions.sum()==x.base_admissions
 assert flow.loc[flow.reason.eq('included'),'admissions'].item()==x.eligible_admissions
 query=next(y for y in receipt['queries']['sql_python_eligibility_checks'] if y['prediction_hours']==x.prediction_hours)
 assert (query['admissions'],query['deaths'])==(x.eligible_admissions,x.deaths)
 if x.prediction_hours==24:assert x.deaths_at_or_before_24h_retained==0
 for t in texts:assert f'{x.eligible_admissions:,}' in t
for name in ['metrics','cohorts','exclusions','calibration','chronology_sensitivity']:
 columns=set(pd.read_csv(out/f'prediction_time_{name}.csv').columns)
 assert not columns.intersection(['subject_id','hadm_id','transfer_id','poe_id','admittime','dischtime','deathtime','predicted_probability'])
for path,expected in receipt['source_sha256'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==expected,path
assert receipt['queries']['native_transfer_reconstruction']['mismatches']==0 and not receipt['row_exports']
assert receipt['queries']['dry_run_bytes']<=10*1024**3
publish_report(R)
assert (R/'assets/prediction_time_calibration.png').read_bytes()==(R/'docs/assets/prediction_time_calibration.png').read_bytes()
parser=ReportResources();parser.feed((R/'docs/reports/nonicu_raas_mortality_report.html').read_text())
assert 'prediction-time-evaluation' in parser.ids
assert any(url.endswith('/prediction_time_calibration.png') for _,url in parser.resources)
print('PASS: prediction metrics/interval withholding, cohort flows, aggregate-only exports, source hashes, connected-check evidence and published calibration figure agree')
