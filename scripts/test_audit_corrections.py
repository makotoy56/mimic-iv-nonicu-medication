"""Offline audit regressions: source, public aggregates and synthetic rows only."""
from pathlib import Path
import ast
import contextlib
import csv
import io
import json
import os
import socket
import sqlite3
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

def no_connection(*args,**kwargs):
    raise AssertionError('Network/credentials are forbidden in this offline test')
socket.create_connection=no_connection
import google.auth
google.auth.default=no_connection

def notebook(name):
    return json.loads((ROOT/'notebooks'/name).read_text())
def source(nb,needle):
    return next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code' and needle in ''.join(c['source']))
def load_source(path,text=None):
    ns={'__file__':str(path),'__name__':'offline_audit_module'}
    exec(compile(path.read_text() if text is None else text,str(path),'exec'),ns)
    return ns

a=notebook('04a_unadjusted_outcomes.ipynb');b=notebook('04b_multivariable_outcomes.ipynb')
df=pd.DataFrame({'subject_id':[10,10,20,30], 'raas_any_early':[0,0,1,1],
                 'hospital_expire_flag':[0,1,0,1], 'age':[40,40,60,70]})
ns={'df':df,'pd':pd};exec(source(a,'n_admissions=("raas_any_early"'),ns)
assert ns['tbl'].n_admissions.tolist()==[2,2]
assert df.groupby('raas_any_early').subject_id.nunique().tolist()==[1,2]
exec(source(b,'mortality_summary ='),ns)
assert ns['mortality_summary'].n_admissions.tolist()==[2,2]
with tempfile.TemporaryDirectory() as temporary:
    cwd=Path.cwd();work=Path(temporary)/'notebooks';work.mkdir()
    try:
        os.chdir(work)
        exec(source(a,'python_unadjusted_outcomes = tbl.reset_index()'),ns)
        exported=pd.read_csv(Path(temporary)/'python/outputs/unadjusted_outcomes.csv')
    finally:os.chdir(cwd)
public_header=next(csv.reader((ROOT/'python/outputs/unadjusted_outcomes.csv').open()))
assert exported.columns.tolist()==public_header and exported.n.tolist()==[2,2]
assert exported.deaths.tolist()==[1,1] and 'n_patients' not in exported
print('PASS: repeated patients count as admissions; 04a/04b labels agree and aggregate CSV schema is unchanged')

from patient_validation import evaluate_patient_split
rng=np.random.default_rng(91);n=600
frame=pd.DataFrame({'subject_id':np.repeat(np.arange(200),3),'hadm_id':np.arange(n),
                    'age':rng.integers(18,90,n),'exposure':rng.integers(0,2,n),
                    'outcome':rng.binomial(1,.25,n)})
for col in ['gender','race_group','admission_type','insurance','anchor_year_group']:
    frame[col]=rng.choice(['A','B'],n)
frame['admittime']=pd.Timestamp('2020-01-01')
frame['dischtime']=pd.Timestamp('2020-01-01 12:00')
frame['deathtime']=pd.NaT
frame.loc[frame.outcome.eq(1),'deathtime']=pd.Timestamp('2020-01-01 10:00')
frame['hospital_expire_flag']=frame.outcome
classification={'pd':pd};exec(source(b,'def classify_landmark(data):'),classification)
assert not classification['classify_landmark'](frame)[1].any()
result=evaluate_patient_split(frame)
assert (result.train_admissions+result.test_admissions).eq(n).all()
assert result.test_deaths.gt(0).all()
assert result.loc[result.validation.eq('Patient-disjoint holdout'),'overlapping_patients'].item()==0
print('PASS: full-cohort classifier retains synthetic early deaths/discharges; it is distinct from 24h landmark eligibility')

# Source-only destination replacement recipe; no BigQuery client is created.
old_project='mimic-iv-portfolio';old_dataset='nonicu_raas'
new_project='replication-test';new_dataset='replica'
def replace(text):return text.replace(old_project,new_project).replace(old_dataset,new_dataset)
for path in (ROOT/'notebooks').glob('*.ipynb'):
    if path.name.startswith('05'):continue  # private historical artifact, outside scope
    code='\n'.join(''.join(c['source']) for c in json.loads(path.read_text())['cells'] if c['cell_type']=='code')
    tree=ast.parse(replace(code))
    values={t.id:ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
            for t in node.targets if isinstance(t,ast.Name) and t.id in {'PROJECT_ID','DATASET','DATASET_ID'}}
    assert values['PROJECT_ID']==new_project
    assert values.get('DATASET',values.get('DATASET_ID'))==new_dataset
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);(root/'sql').mkdir()
    for path in (ROOT/'sql').glob('*.sql'):
        text=replace(path.read_text());(root/'sql'/path.name).write_text(text)
        assert text.count('physionet-data.')==path.read_text().count('physionet-data.')
    helper=ROOT/'scripts/rebuild_analysis_tables.py'
    rebuilt=load_source(helper,replace(helper.read_text()))
    steps=rebuilt['load_steps'](root)
    assert len(steps)==5 and rebuilt['DATASET']==new_project+'.'+new_dataset
    assert old_project not in rebuilt['dry_run_query'](steps)
    for table,sql,_ in steps:
        query=rebuilt['creation_query'](table,sql)
        assert f'CREATE TABLE `{new_project}.{new_dataset}.{table}`' in query
        assert 'INTERVAL 60 DAY' in query and 'CREATE OR REPLACE' not in query
print('PASS: documented destination changes cover seven notebooks, six SQL files and all five rebuild steps; source projects/expiration retained')

checker=ROOT/'scripts/validation_checklist.py';check=load_source(checker,replace(checker.read_text()))
class Client:
    def __init__(self):self.queries=[]
    def query(self,sql,**kwargs):self.queries.append(sql);return self
    def result(self,**kwargs):return [[.25]]
client=Client()
with contextlib.redirect_stdout(io.StringIO()):check['step_prevalence'](client,1)
assert len(client.queries)==2 and all(f'`{new_project}.{new_dataset}.analysis_dataset`' in q for q in client.queries)
cases_ast=ast.parse((ROOT/'scripts/test_landmark_sensitivity.py').read_text())
cases=ast.literal_eval(next(n.value for n in cases_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in n.targets)))
base=pd.Timestamp('2020-01-01')
def when(hours):return None if hours is None else base+pd.Timedelta(hours=hours)
records=[dict(admittime=when(a),dischtime=when(d),deathtime=when(e),hospital_expire_flag=f) for _,a,d,e,f,_ in cases]
eligible=classification['classify_landmark'](pd.DataFrame(records))[1]
predicate=client.queries[1].split('WHERE ',1)[1].replace('DATETIME_ADD(admittime, INTERVAL 24 HOUR)',"datetime(admittime, '+24 hours')")
connection=sqlite3.connect(':memory:')
connection.execute('CREATE TABLE records (idx INTEGER,admittime TEXT,dischtime TEXT,deathtime TEXT,hospital_expire_flag INTEGER)')
for i,row in enumerate(records):
    times=[None if row[k] is None else row[k].isoformat(sep=' ') for k in ['admittime','dischtime','deathtime']]
    connection.execute('INSERT INTO records VALUES (?,?,?,?,?)',[i,*times,row['hospital_expire_flag']])
selected=[r[0] for r in connection.execute('SELECT idx FROM records WHERE '+predicate+' ORDER BY idx')]
assert selected==np.flatnonzero(eligible).tolist()
connection.close()
print('PASS: auxiliary configured-table query matches existing 04b eligibility on 18 synthetic cases (SQLite predicate surrogate, not BigQuery execution)')

for path in ['README.md','REPRODUCIBILITY.md','reports/nonicu_raas_mortality_report.qmd','docs/PATIENT_AWARE_VALIDATION.md']:
    text=(ROOT/path).read_text()
    assert 'internal evaluation of retrospective discrimination' in text and 'no fixed clinical prediction time' in text
    assert '0.860635' in text and '0.117607' in text
markdown='\n'.join(''.join(c['source']) for c in b['cells'] if c['cell_type']=='markdown')
assert 'not temporal feature availability' in markdown and '0.859852/0.116565' in markdown
print('PASS: main narrative surfaces preserve AUCs and state the temporal interpretation boundary')
