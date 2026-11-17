"""Synthetic/analytic checks; no MIMIC records used."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar, brentq
from scipy.special import expit
from scipy.stats import chi2
from firthmodels import FirthLogisticRegression
from firth_sensitivity import frequency_compress, fit_firth, adjusted_score, model_inputs


def independent_profile(n0, y0, n1, y1):
    b0=np.log((y0+.5)/(n0-y0+.5))
    b1=np.log((y1+.5)/(n1-y1+.5))-b0
    def objective(a,b):
        eta=np.array([a,a+b]);successes=np.array([y0+.5,y1+.5]);totals=np.array([n0+1,n1+1])
        return float(successes@eta-totals@np.logaddexp(0,eta))
    top=objective(b0,b1)
    def target(b):
        profile=-minimize_scalar(lambda a:-objective(a,b),bounds=(-50,50),method='bounded',options={'xatol':1e-12}).fun
        return 2*(top-profile)-chi2.ppf(.95,1)
    return b1,np.array([brentq(target,b1-30,b1),brentq(target,b1,b1+30)])


for counts in [(3,0,3,3),(12,0,15,4),(10,3,10,5)]:
    n0,y0,n1,y1=counts
    X=np.r_[np.zeros(n0),np.ones(n1)][:,None]
    y=np.r_[np.ones(y0),np.zeros(n0-y0),np.ones(y1),np.zeros(n1-y1)].astype(int)
    fit=FirthLogisticRegression(backend='numpy',max_iter=200,gtol=1e-8,xtol=1e-8).fit(X,y)
    beta,interval=independent_profile(*counts)
    actual=fit.conf_int(method='pl',features=[0],max_iter=100,tol=1e-8)[0]
    np.testing.assert_allclose(fit.coef_[0],beta,atol=2e-7)
    np.testing.assert_allclose(actual,interval,atol=3e-6)
    assert fit.converged_ and adjusted_score(X,y,np.ones(len(y)),fit.coef_,fit.intercept_)<1e-6
    cx,cy,w=frequency_compress(X,y)
    weighted=FirthLogisticRegression(backend='numpy',max_iter=200,gtol=1e-8,xtol=1e-8).fit(cx,cy,sample_weight=w)
    np.testing.assert_allclose(weighted.coef_,fit.coef_,atol=2e-7)
    np.testing.assert_allclose(weighted.conf_int(method='pl',features=[0],max_iter=100,tol=1e-8)[0],actual,atol=3e-6)
print('PASS: separated, quasi-separated and nonseparated 2x2 analytic Firth ORs and independently profiled 95% CIs; exact frequency compression')

rng=np.random.default_rng(71);n=2400
d=pd.DataFrame({'exposure':rng.integers(0,2,n),'age':rng.integers(18,95,n),'outcome':rng.binomial(1,.15,n)})
for c in ['gender','race_group','insurance','anchor_year_group','admission_location']:
    d[c]=rng.choice(['A','B'],n)
d['admission_type']=rng.choice(['AMBULATORY OBSERVATION','EMERGENCY'],n)
d.loc[d.admission_type.eq('AMBULATORY OBSERVATION'),'outcome']=0
for proxy in [False,True]:
    fit,row=fit_firth(d,'synthetic',proxy)
    assert row['inference_valid'] and row['separation_certificate']
    assert row['n']==n and row['deaths']==d.outcome.sum()
print('PASS: full covariate ordinary/proxy fits preserve all admissions and certify separation with finite profile inference')

# Firth exposure inference is invariant to an affine age reparameterization and
# binary reference-category reversal, with the same adjustment information.
X, y = model_inputs(d, False)
a = FirthLogisticRegression(backend="numpy", max_iter=200, gtol=1e-7, xtol=1e-7).fit(X.to_numpy(), y)
transformed = X.to_numpy().copy()
transformed[:, 1] = transformed[:, 1] * 10 + 60
transformed[:, 2:] = 1 - transformed[:, 2:]
b = FirthLogisticRegression(backend="numpy", max_iter=200, gtol=1e-7, xtol=1e-7).fit(transformed, y)
assert a.converged_ and b.converged_
np.testing.assert_allclose(a.coef_[0], b.coef_[0], atol=2e-6)
np.testing.assert_allclose(a.conf_int(method="pl", features=[0], max_iter=100, tol=1e-7)[0],
                           b.conf_int(method="pl", features=[0], max_iter=100, tol=1e-7)[0], atol=2e-5)
print("PASS: exposure OR/profile interval invariant to age scaling and reference-category reversal")

from tempfile import TemporaryDirectory
from firth_sensitivity import export_firth_figure
with TemporaryDirectory() as tmp:
    target=Path(tmp)/"must_not_exist.png"
    assert export_firth_figure(pd.DataFrame({"inference_valid":[False]}),target) is None
    assert not target.exists()
print("PASS: failed Firth/profile checks cannot overwrite a figure")
