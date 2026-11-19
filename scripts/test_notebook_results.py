"""Offline result-generation tests: synthetic aggregates only, no credentials."""
from pathlib import Path
from types import SimpleNamespace
import ast
import contextlib
import json
import socket
import sys

import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nonicu_notebook_results import NotebookResults,ResultPayload,live_payload,summarize,calibration_figure

def forbidden(*args,**kwargs):
    raise AssertionError('Network/credential access is forbidden in presentation tests')
socket.create_connection=forbidden
pd.read_csv=forbidden

# Saved CSVs must be output references, not the inputs used by the renderer.
roles=[]
role_view=NotebookResults({},emit=roles.append)
role_view.overview(['Table 04b.10','Table 04b.13','Figure 04b.4'])
role_header=roles[0].data
assert 'Saved aggregates and verification files (CSV/JSON)' in role_header
assert 'not the original MIMIC-IV source tables' in role_header
assert 'During live notebook execution, displays use in-memory results.' in role_header
assert 'Saved-output replay and validation workflows may read these files.' in role_header
assert 'Calculation inputs and source definitions' in role_header
assert role_header.count('href="../python/outputs/firth_patient_bootstrap.csv"')==1
assert role_header.count('href="../python/outputs/firth_model_comparison.csv"')==1
assert 'firth_patient_ci' in role_view.specs['Table 04b.13']['source']
assert '.csv' not in role_view.specs['Table 04b.13']['source']
assert 'firth_patient_bootstrap.csv' in role_view.specs['Table 04b.13']['exports']
print('PASS: saved CSV destinations are distinct from in-memory calculation/display inputs')

# Counts and percentages must follow the supplied result, not saved examples.
selection=pd.DataFrame([dict(n_base=40,n_adult_admissions=40,n_excluded_icu=10,n_nonicu=30)])
first=summarize('Table 01.4',ResultPayload([selection]))
selection.loc[0,['n_base','n_adult_admissions','n_excluded_icu','n_nonicu']]=[20,20,15,5]
second=summarize('Table 01.4',ResultPayload([selection]))
assert first!=second and '75.0000%' in first and '25.0000%' in second
assert '460,786' not in second
print('PASS: changed cohort counts update the computed summary and denominator')

or_table=pd.DataFrame([dict(OR=.7,CI_lower=.4,CI_upper=1.2,p_value=.2)],index=['exposure'])
failed=summarize('Table 04b.6',ResultPayload([or_table],{'converged':False}))
passed=summarize('Table 04b.6',ResultPayload([or_table],{'converged':True}))
assert 'did not converge' in failed and 'did not converge' not in passed
assert 'diagnostic only' in failed
print('PASS: convergence status changes interpretation; nominal significance is not inferred')

risk=pd.DataFrame([dict(metric='ame',estimate=-.02,CI_lower=np.nan,CI_upper=np.nan,
    bootstrap_requested=20,bootstrap_successful=15,interval_available=False)])
message=summarize('Table 04b.14',ResultPayload([risk]))
assert '-2.0000 percentage points' in message and 'withheld' in message and '15/20' in message
assert '0.0000 to 0.0000' not in message
print('PASS: AME uses percentage points and missing intervals remain withheld')

metrics=pd.DataFrame([
 dict(model='Admission: age/sex',prediction_hours=0,test_admissions=19,test_deaths=2,
      roc_auc=.6,pr_auc_average_precision=.2,bootstrap_requested=20,
      bootstrap_successful=18,interval_available=False),
 dict(model='24h: age/sex',prediction_hours=24,test_admissions=31,test_deaths=4,
      roc_auc=.7,pr_auc_average_precision=.3,bootstrap_requested=20,
      bootstrap_successful=20,interval_available=True)])
message=summarize('Figure 04c.1',ResultPayload(stats={'metrics':metrics}))
assert '19 test admissions / 2 deaths' in message and 'required 19/20' in message
assert '163' not in message and '698' not in message
changed=metrics.copy();changed.loc[0,['test_admissions','test_deaths','bootstrap_successful','interval_available']]=[29,6,20,True]
new=summarize('Figure 04c.1',ResultPayload(stats={'metrics':changed}))
assert '29 test admissions / 6 deaths' in new and 'intervals withheld' not in new
print('PASS: prediction sample sizes, deaths and prespecified interval gate are data-driven')

events=[];view=NotebookResults({'PROJECT_ID':'replication-project','DATASET':'replica'},emit=events.append)
with view.capture('Table 00.1',{'df':pd.DataFrame({'icu_stays':[12]})}):
    print('Synthetic aggregate check')
assert any('icu_stays=12' in getattr(item,'data','') for item in events if isinstance(getattr(item,'data',None),str))
assert 'replication-project.replica.analysis_dataset' in view.source('`nonicu_raas.analysis_dataset`')
assert 'physionet-data' in view.source('`physionet-data.mimiciv_3_1_hosp.admissions`')
print('PASS: actual capture emits a current result and source destinations follow notebook settings')

events.clear()
view.overview(['Table 01.1','Table 01.1','Table 00.1'])
assert len(events)==1
header=events[0].data
assert '## Data sources and execution mode' in header
assert header.count('**Table 01.1:**')==1
assert 'replication-project.replica.base_admissions' in header
assert 'Execution mode: live notebook execution' in header
assert '<details>' in header and 'in the corresponding analysis cell' in header
events.clear()
replay=NotebookResults({},emit=events.append,mode='saved-replay')
replay.overview(['Table 00.1'])
replay.render('Table 00.1',ResultPayload([pd.DataFrame({'icu_stays':[12]})]))
texts=[item.data for item in events if isinstance(getattr(item,'data',None),str)]
assert sum('Execution mode of saved outputs' in item for item in texts)==1
assert 'no clinical query or model fit was rerun' in texts[0]
assert texts[1]=='### Table 00.1 — '+replay.specs['Table 00.1']['title']
assert all('**Data source**' not in item for item in texts)
assert all('presentation replay' not in item.lower() for item in texts[1:])
assert any('icu_stays=12' in item for item in texts)
print('PASS: sources and mode appear once in the shared header; result titles and computed values remain')

events.clear()
try:
    with view.capture('Table 00.1',{'df':pd.DataFrame({'icu_stays':[99]})}):
        raise RuntimeError('Synthetic failure')
except RuntimeError:pass
else:raise AssertionError('Result failure was swallowed')
assert not events
try:view.render('Table 00.1',ResultPayload([pd.DataFrame({'hadm_id':[1]})]))
except ValueError:pass
else:raise AssertionError('Record-level identifier table was displayed')
assert not events
print('PASS: failures cannot reuse old results; record-level tables fail before display')

# A figure left in the kernel from an earlier cell is not a new result.
events.clear()
try:
    with view.capture('Figure 04b.2',{'fig':object(),'age_grid':np.arange(18,20)}):
        pass
except ValueError:pass
else:raise AssertionError('An unchanged figure from an earlier cell was reused')
assert not events
print('PASS: figure presentation rejects an unchanged figure from a previous cell')

bins=pd.DataFrame([
 dict(model='Admission: age/sex',prediction_hours=0,mean_predicted_risk=.1,
      observed_risk=.2,observed_CI_lower=.1,observed_CI_upper=.3),
 dict(model='24h: age/sex',prediction_hours=24,mean_predicted_risk=.1,
      observed_risk=.15,observed_CI_lower=.1,observed_CI_upper=.2)])
cohorts=pd.DataFrame([dict(prediction_hours=0,test_deaths=2),dict(prediction_hours=24,test_deaths=4)])
figure=calibration_figure({'metrics':metrics,'calibration':bins,'cohorts':cohorts})
assert '2' in figure.axes[0].get_title() and '4' in figure.axes[1].get_title()
# Invalid-gate bounds exist intentionally in synthetic bins; they must not draw.
assert not figure.axes[0].collections and figure.axes[1].collections
import matplotlib.pyplot as plt
plt.close(figure)
print('PASS: calibration is drawn from aggregate bins and respects interval eligibility')

# Source coverage is checked when this file lives in the repository. No notebook
# or BigQuery client is executed by this structural check.
if (ROOT/'notebooks').is_dir():
    labels=set();setup_count=0;overview_count=0
    for path in (ROOT/'notebooks').glob('*.ipynb'):
        if path.name.startswith('05'):continue
        nb=json.loads(path.read_text());notebook_labels=set();overview_labels=None;notebook_setup=0
        for cell in nb['cells']:
            source=''.join(cell['source'])
            if cell['cell_type']=='markdown':
                assert '<!-- nonicu-result-guide:' not in source
                assert not any(line.startswith('|') for line in source.splitlines())
                assert '![' not in source
            if cell['cell_type']!='code':continue
            tree=ast.parse(source)
            # nbstripout renumbers cell IDs when committing. Identify setup by
            # its executable assignment so both local and published files pass.
            for statement in tree.body:
                if (isinstance(statement,ast.Assign)
                        and any(isinstance(target,ast.Name) and target.id=='notebook_results' for target in statement.targets)
                        and isinstance(statement.value,ast.Call)
                        and isinstance(statement.value.func,ast.Name)
                        and statement.value.func.id=='NotebookResults'):
                    setup_count+=1;notebook_setup+=1
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='notebook_results' and node.func.attr in {'capture','diagnostic'}:
                    value=ast.literal_eval(node.args[0]);items=[value] if isinstance(value,str) else value
                    labels.update(items);notebook_labels.update(items)
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='notebook_results' and node.func.attr=='overview':
                    assert overview_labels is None,'Duplicate notebook provenance header'
                    overview_labels=set(ast.literal_eval(node.args[0]));overview_count+=1
        assert notebook_setup==1,(path.name,notebook_setup)
        assert overview_labels==notebook_labels,path.name
    assert setup_count==8 and labels==set(view.specs),(setup_count,labels.symmetric_difference(view.specs))
    assert overview_count==8
    print('PASS: all eight notebooks have one complete provenance header; static result tables/images are absent')
