"""Check that published summaries agree with the actual aggregate evidence."""
from pathlib import Path
import csv,json,math,sys
from quarto_normalize_outputs import publish_report,ReportResources
ROOT=Path(__file__).resolve().parents[1]

def rows(name):
    with (ROOT/'python/outputs'/f'{name}.csv').open() as f:return list(csv.DictReader(f))

points={r['model']:r for r in rows('firth_model_comparison')}
boot=rows('firth_patient_bootstrap');risk=rows('risk_patient_bootstrap')
texts=[(ROOT/p).read_text() for p in ['README.md','docs/RESULTS_SUMMARY.md','docs/PATIENT_AWARE_VALIDATION.md','reports/nonicu_raas_mortality_report.qmd']]
notebook=json.loads((ROOT/'notebooks/04b_multivariable_outcomes.ipynb').read_text())
texts.append('\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='markdown'))
for row in boot:
    p=points[row['model']]
    assert int(row['n'])==int(p['n']) and int(row['deaths'])==int(p['deaths'])
    assert int(row['bootstrap_successful'])>=.95*int(row['bootstrap_requested'])
    assert int(row['bootstrap_requested'])==500
    assert row['interval_available']=='True'
    lower,upper=map(float,[row['CI_lower'],row['CI_upper']])
    assert math.isfinite(lower) and 0<lower<float(p['OR'])<upper
    line=f"| {row['model']} | {int(row['n']):,} | {int(row['patients']):,} | {int(row['deaths']):,} | {float(p['OR']):.3f} | {lower:.3f}–{upper:.3f} | {row['bootstrap_successful']}/500 |"
    for text in texts[1:]:assert line in text,('Missing/mismatched current table',row['model'])
ame=next(r for r in risk if r['metric']=='ame')
for text in texts:
    assert f"{100*float(ame['estimate']):.4f}" in text
    assert f"{100*float(ame['CI_lower']):.4f} to {100*float(ame['CI_upper']):.4f}" in text
split=next(r for r in rows('patient_split_validation') if r['validation']=='Patient-disjoint holdout')
assert split['overlapping_patients']=='0'
for text in texts:
    assert f"{float(split['roc_auc']):.6f}" in text and f"{float(split['pr_auc']):.6f}" in text
stats=publish_report(ROOT)
parser=ReportResources();parser.feed((ROOT/'docs/reports/nonicu_raas_mortality_report.html').read_text())
for name in ['firth_landmark_patient_bootstrap.png','absolute_risk_difference_patient_bootstrap.png','firth_landmark_sensitivity.png']:
    assert any(url.endswith('/'+name) for _,url in parser.resources)
    assert (ROOT/'assets'/name).read_bytes()==(ROOT/'docs/assets'/name).read_bytes()
print('PASS: five cohort/model summaries and AME/split metrics agree with aggregates; three Firth/risk assets are published consistently;',stats)
