"""Patient-group validation and patient-cluster bootstrap; aggregate output only."""
import warnings
import json
import numpy as np
import pandas as pd
from firthmodels import FirthLogisticRegression
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from firth_sensitivity import model_inputs, adjusted_score, CATEGORIES
from firth_point_fallback import verified_point


def evaluate_patient_split(frame, seed=42):
    if 'hadm_id' in frame:
        frame=frame.sort_values(['subject_id','hadm_id'],kind='stable')
    encoded,y=model_inputs(frame)
    X=frame.loc[encoded.index,['age','exposure']+CATEGORIES].copy()
    X[CATEGORIES]=X[CATEGORIES].fillna('Unknown')
    groups=frame.loc[X.index,'subject_id'].to_numpy()
    if pd.isna(groups).any():
        raise ValueError('Missing patient identifiers prevent group validation')
    classifier=Pipeline([('prep',ColumnTransformer([('num',StandardScaler(),['age']),
                         ('cat',OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=False),CATEGORIES)],remainder='passthrough')),
                         ('logit',LogisticRegression(max_iter=2000,class_weight='balanced',solver='lbfgs',C=1.0))])
    indices=np.arange(len(y))
    row_split=train_test_split(indices,test_size=.2,random_state=seed,stratify=y)
    group_split=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=seed).split(X,y,groups))
    rows=[]
    for name,(train,test) in [('Admission-random reference',row_split),('Patient-disjoint holdout',group_split)]:
        model=clone(classifier)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(X.iloc[train],y[train])
        probabilities=model.predict_proba(X.iloc[test])[:,1]
        overlap=len(np.intersect1d(groups[train],groups[test]))
        if name=='Patient-disjoint holdout' and overlap:
            raise AssertionError('Patient overlap in group holdout')
        rows.append(dict(validation=name,seed=seed,train_admissions=len(train),test_admissions=len(test),
                         train_patients=len(np.unique(groups[train])),test_patients=len(np.unique(groups[test])),
                         overlapping_patients=overlap,test_deaths=int(y[test].sum()),
                         test_prevalence=float(y[test].mean()),roc_auc=float(roc_auc_score(y[test],probabilities)),
                         pr_auc=float(average_precision_score(y[test],probabilities)),
                         iterations=int(model.named_steps['logit'].n_iter_[0]),
                         warnings=', '.join(sorted({type(w.message).__name__ for w in caught}))))
    return pd.DataFrame(rows)


def prepare_scope(frame, proxy=False):
    X,y=model_inputs(frame,proxy)
    patient_ids=frame.loc[X.index,'subject_id'].to_numpy()
    if pd.isna(patient_ids).any():
        raise ValueError('Missing patient identifiers prevent cluster resampling')
    patients,codes=np.unique(patient_ids,return_inverse=True)
    unique,first,inverse=np.unique(np.column_stack([X.to_numpy(),y]),axis=0,return_index=True,return_inverse=True)
    columns=['exposure','age','outcome']+CATEGORIES+(['admission_location'] if proxy else [])
    raw_groups=frame.loc[X.index].iloc[first][columns].copy()
    return dict(X=X,y=y,patients=patients,codes=codes,proxy=proxy,raw_groups=raw_groups,
                compressed_X=unique[:,:-1],compressed_y=unique[:,-1].astype(int),inverse=inverse.reshape(-1))


def patient_weights(codes, n_patients, rng):
    """Sample patients uniformly with replacement, carrying ALL their admissions."""
    frequencies=np.bincount(rng.integers(n_patients,size=n_patients),minlength=n_patients)
    return frequencies[codes].astype(float)


def firth_bootstrap_point(prepared, weights, return_details=False):
    counts=np.bincount(prepared['inverse'],weights=weights,minlength=len(prepared['compressed_y']))
    active=counts>0
    # Re-encode only levels observed in this resample, as an explicit row bootstrap would.
    # No observed level or adjustment variable is pooled/dropped; full-data fits are unchanged.
    encoded,y=model_inputs(prepared['raw_groups'].iloc[np.flatnonzero(active)],prepared['proxy'])
    X=encoded.to_numpy();w=counts[active]
    # Reject any residual rank problem after ordinary observed-level encoding.
    if np.linalg.matrix_rank(np.column_stack([X,np.ones(len(X))]))!=X.shape[1]+1:
        raise ValueError('RankDeficientResample')
    model=FirthLogisticRegression(backend='numpy',max_iter=300,gtol=1e-6,xtol=1e-7)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');model.fit(X,y,sample_weight=w)
    recovered=0
    beta=np.r_[model.coef_,model.intercept_]
    if not model.converged_ or any(type(t.message).__name__=='ConvergenceWarning' for t in caught):
        beta,_=verified_point(X,y,w,beta)
        recovered=1
    score=adjusted_score(X,y,w,beta[:-1],beta[-1])
    if not np.isfinite(beta).all() or not np.isfinite(score) or score>=1e-5:
        raise ValueError('AdjustedScoreFailure')
    value=float(beta[0])
    omitted=max(0,prepared['X'].shape[1]-X.shape[1])
    return (value,omitted,recovered) if return_details else value



def make_risk_model():
    return Pipeline([('scaler',StandardScaler()),
                     ('logit',LogisticRegression(solver='lbfgs',max_iter=2000,class_weight=None))])


def risk_statistics(model,X,weights,age_grid):
    X0=X.copy();X1=X.copy();X0['exposure']=0;X1['exposure']=1
    p0=model.predict_proba(X0)[:,1];p1=model.predict_proba(X1)[:,1]
    p0_mean=float(np.average(p0,weights=weights));p1_mean=float(np.average(p1,weights=weights))
    base=np.average(X.to_numpy(),axis=0,weights=weights)
    grid0=pd.DataFrame(np.tile(base,(len(age_grid),1)),columns=X.columns)
    grid1=grid0.copy();grid0['exposure']=0;grid1['exposure']=1
    grid0['age']=age_grid;grid1['age']=age_grid
    rd=model.predict_proba(grid1)[:,1]-model.predict_proba(grid0)[:,1]
    return dict(ame=p1_mean-p0_mean,risk_unexposed=p0_mean,risk_exposed=p1_mean),rd


def cluster_bootstrap(scopes, n_boot=500, seed=42, progress=None):
    """Percentile CIs. Each scope resamples its own eligible patients.

    Ordinary/proxy fits within a scope share patient draws. Failures are counted;
    interval publication requires >=95% successful prespecified replicates.
    Unobserved categorical levels are re-encoded within each resample, without pooling observed levels.
    """
    prepared={name:prepare_scope(frame.sort_values(['subject_id','hadm_id'],kind='stable') if 'hadm_id' in frame else frame,proxy)
              for name,(frame,proxy) in scopes.items()}
    for name,p in prepared.items():
        base=name.removesuffix(' + proxy')
        if base!=name and not np.array_equal(p['codes'],prepared[base]['codes']):
            raise ValueError('Ordinary/proxy admissions are not aligned for shared patient draws')
    primary=prepared['Primary cohort']
    riskX=primary['X'].copy();riskX['age']=riskX['age']*10+60
    risk_y=primary['y'];age_grid=np.arange(18,95)
    risk=make_risk_model().fit(riskX,risk_y)
    risk_point,rd_point=risk_statistics(risk,riskX,np.ones(len(risk_y)),age_grid)
    generators={name:np.random.default_rng(seed+i) for i,name in enumerate(['Primary cohort','Original condition','24h landmark'])}
    coefficients={name:[] for name in scopes};failures={name:{} for name in scopes}
    risk_rows=[];risk_curves=[];risk_failures={}
    reencoded={name:0 for name in scopes};max_absent={name:0 for name in scopes};recovered_fits={name:0 for name in scopes}
    for b in range(n_boot):
        scope_weights={}
        for name,p in prepared.items():
            base=name.removesuffix(' + proxy')
            if base not in scope_weights:
                scope_weights[base]=patient_weights(p['codes'],len(p['patients']),generators[base])
            weights=scope_weights[base]
            try:
                value,omitted,recovered=firth_bootstrap_point(p,weights,return_details=True)
                coefficients[name].append(value)
                reencoded[name]+=int(omitted>0);max_absent[name]=max(max_absent[name],omitted);recovered_fits[name]+=recovered
            except (ValueError,np.linalg.LinAlgError) as exc:
                reason=str(exc) if str(exc) in ['RankDeficientResample','NonconvergedResample','AdjustedScoreFailure'] else type(exc).__name__
                failures[name][reason]=failures[name].get(reason,0)+1
        try:
            weights=scope_weights['Primary cohort']
            fitted=make_risk_model()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                fitted.fit(riskX,risk_y,scaler__sample_weight=weights,logit__sample_weight=weights)
            if any(type(t.message).__name__=='ConvergenceWarning' for t in caught):
                raise ValueError('NonconvergedResample')
            row,curve=risk_statistics(fitted,riskX,weights,age_grid)
            risk_rows.append(row);risk_curves.append(curve)
        except (ValueError,np.linalg.LinAlgError) as exc:
            reason=type(exc).__name__;risk_failures[reason]=risk_failures.get(reason,0)+1
        if progress and ((b+1)%10==0 or b+1==n_boot):
            progress(b+1,coefficients,failures,len(risk_rows),risk_failures)
    threshold=int(np.ceil(.95*n_boot))
    rows=[]
    for name,values in coefficients.items():
        p=prepared[name];valid=len(values)>=threshold
        ci=np.exp(np.percentile(values,[2.5,97.5])) if valid else [np.nan,np.nan]
        rows.append(dict(model=name,n=len(p['y']),patients=len(p['patients']),deaths=int(p['y'].sum()),
                         bootstrap_requested=n_boot,bootstrap_successful=len(values),master_seed=seed,
                         resample_seed=seed+['Primary cohort','Original condition','24h landmark'].index(name.removesuffix(' + proxy')),
                         CI_lower=float(ci[0]),CI_upper=float(ci[1]),ci_method='patient-cluster percentile bootstrap',
                         interval_available=valid,recovered_newton_fits=recovered_fits[name],resamples_with_unobserved_levels=reencoded[name],maximum_unobserved_levels=max_absent[name],failure_counts=json.dumps(failures[name],sort_keys=True)))
    risk_values=pd.DataFrame(risk_rows);risk_summary=[]
    risk_valid=len(risk_values)>=threshold
    for name,point in risk_point.items():
        ci=np.percentile(risk_values[name],[2.5,97.5]) if risk_valid else [np.nan,np.nan]
        risk_summary.append(dict(metric=name,estimate=point,CI_lower=float(ci[0]),CI_upper=float(ci[1]),
                                 bootstrap_requested=n_boot,bootstrap_successful=len(risk_rows),seed=seed,
                                 interval_available=risk_valid))
    bounds=np.percentile(np.asarray(risk_curves),[2.5,97.5],axis=0) if risk_valid else np.full((2,len(age_grid)),np.nan)
    age_summary=pd.DataFrame(dict(age=age_grid,risk_difference=rd_point,CI_lower=bounds[0],CI_upper=bounds[1]))
    return pd.DataFrame(rows),pd.DataFrame(risk_summary),age_summary


def export_patient_figures(points, bootstrap, age, assets_dir):
    """Publish patient-cluster intervals only when their predeclared gate passed."""
    from pathlib import Path
    import matplotlib.pyplot as plt
    assets_dir=Path(assets_dir)
    names=['Primary cohort','24h landmark','24h landmark + proxy']
    combined=points.set_index('model').loc[names,['OR','n','deaths']].join(
        bootstrap.set_index('model').loc[names,['CI_lower','CI_upper','interval_available','bootstrap_requested','bootstrap_successful']])
    if not combined.interval_available.all() or not np.isfinite(combined[['OR','CI_lower','CI_upper']]).all().all():
        raise ValueError('Patient-cluster interval checks failed; figures are not refreshed')
    assets_dir.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(9,4))
    positions=np.arange(3)
    ax.errorbar(combined.OR,positions,xerr=[combined.OR-combined.CI_lower,combined.CI_upper-combined.OR],
                fmt='o',capsize=5,color='#2563eb',elinewidth=2)
    ax.axvline(1,color='#64748b',linestyle='--',linewidth=1.2)
    labels=[f'{name}\nN={int(row.n):,}; deaths={int(row.deaths):,}' for name,row in zip(names,combined.itertuples())]
    ax.set_yticks(positions,labels);ax.invert_yaxis();ax.set_xscale('log')
    ax.set_xlim(min(.2,float(combined.CI_lower.min())*.9),max(1.2,float(combined.CI_upper.max())*1.1))
    ax.set_xlabel('Early prescription exposure OR (log scale)')
    ax.set_title('Firth sensitivity: 95% patient-cluster bootstrap intervals')
    ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    b=int(combined.bootstrap_requested.iloc[0])
    fig.text(.03,.02,f'{b} prespecified patient resamples; supplementary estimator; observational associations.',fontsize=9,color='#475569')
    fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(assets_dir/'firth_landmark_patient_bootstrap.png',dpi=200,bbox_inches='tight');plt.close(fig)
    if not np.isfinite(age[['risk_difference','CI_lower','CI_upper']]).all().all():
        raise ValueError('Patient-cluster age intervals unavailable')
    fig,ax=plt.subplots(figsize=(7,5))
    ax.plot(age.age,age.risk_difference*100,color='#2563eb',label='Exposure − no exposure')
    ax.fill_between(age.age,age.CI_lower*100,age.CI_upper*100,color='#93c5fd',alpha=.4,label='95% patient-cluster interval')
    ax.axhline(0,color='#64748b',linestyle='--',linewidth=1.2)
    ax.set_xlabel('Age');ax.set_ylabel('Predicted risk difference (percentage points)')
    ax.set_title('Age-specific risk contrast at a typical covariate profile')
    ax.spines[['top','right']].set_visible(False);ax.legend()
    fig.text(.03,.02,f'Unweighted L2 risk model; {b} patient resamples; no exposure-by-age interaction fitted.',fontsize=8,color='#475569')
    fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(assets_dir/'absolute_risk_difference_patient_bootstrap.png',dpi=200,bbox_inches='tight');plt.close(fig)
