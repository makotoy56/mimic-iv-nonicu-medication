from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from patient_validation import patient_weights,evaluate_patient_split,make_risk_model,risk_statistics,prepare_scope,firth_bootstrap_point

codes=np.array([0,0,1,1,1,2])
w=patient_weights(codes,3,np.random.default_rng(42))
assert w[0]==w[1] and w[2]==w[3]==w[4]
assert sum(w[[0,2,5]])==3
assert np.array_equal(w,patient_weights(codes,3,np.random.default_rng(42)))

rng=np.random.default_rng(72);n=2400
d=pd.DataFrame({'subject_id':np.repeat(np.arange(800),3),'age':rng.integers(18,95,n),
                'exposure':rng.integers(0,2,n),'outcome':rng.binomial(1,.15,n)})
for c in ['gender','race_group','insurance','anchor_year_group','admission_location']:
    d[c]=rng.choice(['A','B'],n)
d['admission_type']=rng.choice(['AMBULATORY OBSERVATION','EMERGENCY'],n)
d.loc[d.admission_type.eq('AMBULATORY OBSERVATION'),'outcome']=0
result=evaluate_patient_split(d)
assert result.loc[result.validation.eq('Patient-disjoint holdout'),'overlapping_patients'].item()==0
assert result.loc[result.validation.eq('Admission-random reference'),'overlapping_patients'].item()>0
print('PASS: all admissions of resampled patients share weights; deterministic group split has zero patient overlap')

# Frequency-weighted scaling/regularized fitting must match actual row replication.
X=d[['exposure','age']].astype(float);y=d.outcome.to_numpy()
weights=np.random.default_rng(8).integers(0,4,n).astype(float)
weighted=make_risk_model().fit(X,y,scaler__sample_weight=weights,logit__sample_weight=weights)
idx=np.repeat(np.arange(n),weights.astype(int))
expanded=make_risk_model().fit(X.iloc[idx],y[idx])
np.testing.assert_allclose(weighted.predict_proba(X),expanded.predict_proba(X),atol=2e-5)
point,curve=risk_statistics(weighted,X,weights,np.arange(18,95))
reference,_=risk_statistics(expanded,X.iloc[idx],np.ones(len(idx)),np.arange(18,95))
assert abs(point['ame']-reference['ame'])<2e-5
print('PASS: weighted scaler/risk refit and AME agree with explicit patient-frequency row replication')

prepared=prepare_scope(d)
coefficient=firth_bootstrap_point(prepared,patient_weights(prepared['codes'],len(prepared['patients']),np.random.default_rng(42)))
assert np.isfinite(coefficient)
print('PASS: one patient-cluster Firth refit passes independent adjusted-score validation')

# A patient draw may omit a rare nuisance level. Re-encoding must match an
# explicit replicated-data fit, without removing any observed category.
from firth_sensitivity import fit_firth
rare=d.copy();rare['admission_location']='COMMON'
rare.loc[:2,'admission_location']='RARE'
rare.loc[3:200,'admission_location']='OTHER'
prepared=prepare_scope(rare,True)
weights=np.ones(n);weights[:3]=0
coefficient,omitted,_=firth_bootstrap_point(prepared,weights,return_details=True)
expanded=rare.loc[weights>0].copy()
reference,row=fit_firth(expanded,'synthetic observed levels',True)
assert omitted==1
assert abs(coefficient-reference.coef_[0])<1e-5 and row['inference_valid']
print('PASS: absent-category resample encoding matches explicit observed-data Firth fit; category omission counted')

from firth_point_fallback import verified_point,objective_score
from firthmodels import FirthLogisticRegression
smallX=np.r_[np.zeros(12),np.ones(15)][:,None]
smallY=np.r_[np.zeros(12),np.ones(4),np.zeros(11)].astype(int)
reference=FirthLogisticRegression(max_iter=200,backend='numpy',gtol=1e-8,xtol=1e-8).fit(smallX,smallY)
beta,used=verified_point(smallX,smallY,np.ones(len(smallY)),np.zeros(2))
np.testing.assert_allclose(beta,np.r_[reference.coef_,reference.intercept_],atol=2e-5)
design=np.column_stack([smallX,np.ones(len(smallX))])
value,score=objective_score(beta,design,smallY,np.ones(len(smallY)))
h=1e-5
numeric=np.array([(objective_score(beta+np.eye(2)[j]*h,design,smallY,np.ones(len(smallY)))[0]-objective_score(beta-np.eye(2)[j]*h,design,smallY,np.ones(len(smallY)))[0])/(2*h) for j in range(2)])
np.testing.assert_allclose(score,numeric,atol=1e-6)
print('PASS: same-objective fallback matches library Firth; adjusted gradient matches numerical differentiation')
