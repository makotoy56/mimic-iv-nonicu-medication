"""Synthetic time/availability/split/metric checks; no credentials or MIMIC rows."""
from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score

sys.path.insert(0,str(Path(__file__).resolve().parent))
from prediction_time_validation import prepare_inputs,eligibility,eligible_sql_predicate,make_model,evaluate,export_results,test_patient_bootstrap,input_sql,independent_rank_metrics

BASE=pd.Timestamp('2020-01-01')
def hour(value):return pd.NaT if value is None else BASE+pd.Timedelta(hours=value)
def row(i=1,discharge=48,death=None,flag=0,icu=None,unknown=0):
    return dict(subject_id=i,hadm_id=i,admittime=BASE,dischtime=hour(discharge),deathtime=hour(death),hospital_expire_flag=flag,
                first_icu_intime=hour(icu),location_status_0h='confirmed_non_icu_ward',location_status_24h='confirmed_non_icu_ward',icu_unknown_intime=unknown,age=50.,gender='F',raas_recorded_by_24h=0,
                last_qualifying_order_time=pd.NaT,last_qualifying_start_time=pd.NaT,early_raas_records=0,
                raas_unverified_order_time_records=0,raas_late_order_records=0,raas_duplicate_poe_records=0)

cases=[(row(1),True,True),(row(2,death=12,flag=1),True,False),(row(3,death=24,flag=1),True,False),
       (row(4,death=24.000001,flag=1),True,True),(row(5,discharge=24),True,False),
       (row(6,discharge=24.000001),True,True),(row(7,icu=12),True,False),(row(8,icu=24),True,False),
       (row(9,icu=24.000001),True,True),(row(10,icu=0),False,False),(row(11,unknown=1),False,False),
       (row(12,flag=1),False,False),(row(13,flag=0,death=36),False,False),
       (row(14,discharge=None),False,False),(row(15,discharge=-1),False,False),
       (row(16,death=-1,flag=1),False,False),(row(17,death=49,flag=1),False,False),
       (row(18,flag=2),False,False),(row(19,discharge=0),False,False),(row(20,death=0,flag=1),False,False),(row(21,death=48,flag=1),True,True),
       (row(22,flag=None),False,False),(dict(row(23),admittime=pd.NaT),False,False)]
for key,status,e0,e24 in [('location_status_0h','no_covering_location',False,True),
                           ('location_status_24h','unconfirmed_interval_end',True,False),
                           ('location_status_24h','overlapping_locations',True,False),
                           ('location_status_0h','not_target_ward',False,True),
                           ('location_status_24h','unconfirmed_unit',True,False),
                           ('location_status_24h',None,True,False)]:
    record=row(len(cases)+1);record[key]=status;cases.append((record,e0,e24))
d=prepare_inputs(pd.DataFrame([x[0] for x in cases]))
for hours,column in [(0,1),(24,2)]:
    mask,_=eligibility(d,hours);assert mask.tolist()==[x[column] for x in cases]
    # Independent typed-predicate surrogate; the live run also checks actual BigQuery counts.
    point=f'DATETIME_ADD(admittime, INTERVAL {hours} HOUR)'
    predicate=eligible_sql_predicate(hours).replace(point,f"datetime(admittime,'+{hours} hours')")
    con=sqlite3.connect(':memory:');con.execute('CREATE TABLE records (idx INTEGER,admittime TEXT,dischtime TEXT,deathtime TEXT,hospital_expire_flag INTEGER,icu_unknown_intime INTEGER,first_icu_intime TEXT,location_status_0h TEXT,location_status_24h TEXT)')
    for i,r in enumerate([x[0] for x in cases]):
        time=lambda k:None if pd.isna(r[k]) else r[k].isoformat(sep=' ')
        con.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?)',[i,time('admittime'),time('dischtime'),time('deathtime'),r['hospital_expire_flag'],r['icu_unknown_intime'],time('first_icu_intime'),r['location_status_0h'],r['location_status_24h']])
    selected=[x[0] for x in con.execute('SELECT idx FROM records WHERE '+predicate+' ORDER BY idx')]
    assert selected==np.flatnonzero(mask).tolist();con.close()
assert eligibility(d,0)[0].iloc[6] and not eligibility(d,24)[0].iloc[6]
assert eligibility(d,24)[0].iloc[8]  # Later ICU is retained; no entire-stay selection.
print(f'PASS: {len(cases)} admission/24h boundary cases and independent SQL-predicate surrogate; later ICU retained, early deaths only excluded at 24h')

bad=d.copy();bad.loc[0,'raas_recorded_by_24h']=1
bad.loc[0,'last_qualifying_order_time']=hour(25);bad.loc[0,'last_qualifying_start_time']=hour(12)
try:prepare_inputs(bad)
except ValueError:pass
else:raise AssertionError('Future order time must fail closed')
bad.loc[0,'last_qualifying_order_time']=hour(24)
assert prepare_inputs(bad).raas_recorded_by_24h.iloc[0]==1
bad.loc[0,'last_qualifying_start_time']=hour(24)
try:prepare_inputs(bad)
except ValueError:pass
else:raise AssertionError('Prescription start at exactly 24h must fail the <24h feature window')
print('PASS: recorded order at the prediction instant is allowed; later registration and start exactly at 24h are rejected')

rng=np.random.default_rng(817);n=1200
frame=pd.DataFrame([row(i+1) for i in range(n)])
frame['subject_id']=np.repeat(np.arange(400),3)
frame['age']=rng.integers(18,90,n);frame['gender']=rng.choice(['F','M'],n)
frame['hospital_expire_flag']=rng.binomial(1,.18,n)
frame.loc[frame.hospital_expire_flag.eq(1),'deathtime']=hour(36)
positive=rng.random(n)<.2;frame.loc[positive,'raas_recorded_by_24h']=1
frame.loc[positive,'last_qualifying_order_time']=hour(12);frame.loc[positive,'last_qualifying_start_time']=hour(10)
frame.loc[positive,'early_raas_records']=1
results=evaluate(frame,n_boot=20)
assert len(results['metrics'])==3 and results['metrics'].overlapping_patients.eq(0).all()
assert results['metrics'].bootstrap_successful.eq(20).all()
for _,r in results['metrics'].iterrows():
    assert r.roc_auc_CI_lower<=r.roc_auc_CI_upper and r.pr_auc_CI_lower<=r.pr_auc_CI_upper
    assert abs(r.observed_test_risk-results['cohorts'].loc[results['cohorts'].prediction_hours.eq(r.prediction_hours),'test_deaths'].item()/r.test_admissions)<1e-12
future=frame.copy();future['first_icu_intime']=hour(30)
future_results=evaluate(future,n_boot=20)
np.testing.assert_allclose(results['metrics'].roc_auc,future_results['metrics'].roc_auc)
assert future_results['cohorts'].later_icu_admissions_retained.eq(n).all()
print('PASS: three synthetic fits, fixed patient-level split, held-out bootstrap and future-ICU invariance')

train=pd.DataFrame({'age':[40.,50.,60.,70.],'gender':['F','M','F','M'],'raas_recorded_by_24h':[0,1,0,1]})
model=make_model(True).fit(train,[0,0,1,1])
before=model.named_steps['prep'].named_transformers_['age'].named_steps['scale'].mean_.copy()
predict=train.copy();predict['age']=1000;predict['future_outcome']=1;model.predict_proba(predict)
np.testing.assert_array_equal(before,model.named_steps['prep'].named_transformers_['age'].named_steps['scale'].mean_)
assert set(model.feature_names_in_)==set(train.columns)
print('PASS: training-only age transformation is unchanged by extreme held-out ages or extra post-outcome columns')

with tempfile.TemporaryDirectory() as temp:
    export_results(results,temp)
    for p in (Path(temp)/'python/outputs').glob('*.csv'):
        columns=pd.read_csv(p).columns
        assert not {'subject_id','hadm_id','admittime','dischtime','deathtime'}.intersection(columns)
    assert (Path(temp)/'assets/prediction_time_calibration.png').is_file()
print('PASS: only aggregate tables and calibration figure are exported')

# Ties and patient-frequency weights: verify the independent rank implementation.
y=np.array([0,1,1,0]);p=np.array([.1,.3,.3,.7])
np.testing.assert_allclose(independent_rank_metrics(y,p),[.5,2/3],atol=1e-14)
y=rng.binomial(1,.3,300);p=np.round(rng.random(300),1);weights=rng.integers(0,5,300)
for w in [None,weights]:
    a,b=independent_rank_metrics(y,p,w)
    np.testing.assert_allclose([a,b],[roc_auc_score(y,p,sample_weight=w),average_precision_score(y,p,sample_weight=w)],atol=1e-14)
print('PASS: independent ROC/AP rank formulas agree with hand calculation and sklearn for ties/frequency weights')
