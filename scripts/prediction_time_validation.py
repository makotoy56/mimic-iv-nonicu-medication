"""Time-anchored internal prediction evaluation; export aggregates only."""
from pathlib import Path
import hashlib
import json
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
import statsmodels.api as sm

ROOT=Path(__file__).resolve().parents[1]
SQL_PATH=Path('sql/05_prediction_time_inputs.sql')
LIMIT=10*1024**3
BOOTSTRAPS=500
SPLIT_SEED=42
BOOTSTRAP_SEED=20261118
WARD_UNITS=['Cardiac Surgery', 'Cardiology', 'Cardiology Surgery Intermediate', 'Hematology/Oncology', 'Hematology/Oncology Intermediate', 'Labor & Delivery', 'Med/Surg', 'Med/Surg/GYN', 'Med/Surg/Trauma', 'Medical/Surgical (Gynecology)', 'Medicine', 'Medicine/Cardiology', 'Medicine/Cardiology Intermediate', 'Neuro Intermediate', 'Neuro Stepdown', 'Neurology', 'Observation', 'Obstetrics (Postpartum & Antepartum)', 'Obstetrics Antepartum', 'Obstetrics Postpartum', 'Oncology', 'Psychiatry', 'Surgery', 'Surgery/Pancreatic/Biliary/Bariatric', 'Surgery/Trauma', 'Surgery/Vascular/Intermediate', 'Surgical Intermediate', 'Thoracic Surgery', 'Transplant', 'Vascular']
ICU_UNITS=['Cardiac Vascular Intensive Care Unit (CVICU)', 'Coronary Care Unit (CCU)', 'Intensive Care Unit (ICU)', 'Medical Intensive Care Unit (MICU)', 'Medical/Surgical Intensive Care Unit (MICU/SICU)', 'Neuro Surgical Intensive Care Unit (Neuro SICU)', 'Surgical Intensive Care Unit (SICU)', 'Trauma SICU (TSICU)']
MODELS=[('Admission: age/sex',0,False),('24h: age/sex',24,False),('24h: age/sex + verified RAAS record',24,True)]
DATE_COLUMNS=['admittime','dischtime','deathtime','first_icu_intime','last_qualifying_order_time','last_qualifying_start_time']


def input_sql(root=ROOT,project='mimic-iv-portfolio',dataset='nonicu_raas'):
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]',project):raise ValueError('Invalid project identifier')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,1023}',dataset):raise ValueError('Invalid dataset identifier')
    text=(Path(root)/SQL_PATH).read_text().strip().removesuffix(';')
    clean=re.sub(r'--[^\n]*','',text).strip()
    if not clean.upper().startswith('WITH ') or ';' in clean or re.search(r'\b(CREATE|DROP|ALTER|INSERT|UPDATE|DELETE|MERGE|EXPORT|CALL|EXECUTE|TRUNCATE)\b',clean,re.I):raise ValueError('Expected one read-only SELECT source')
    return text.replace('mimic-iv-portfolio.nonicu_raas.',f'{project}.{dataset}.')


def prepare_inputs(frame):
    required={'subject_id','hadm_id','age','gender','hospital_expire_flag','location_status_0h','location_status_24h','icu_unknown_intime','raas_recorded_by_24h','early_raas_records','raas_unverified_order_time_records','raas_late_order_records','raas_duplicate_poe_records',*DATE_COLUMNS}
    if required-set(frame):raise ValueError('Prediction input schema is incomplete')
    data=frame.copy()
    if data[['subject_id','hadm_id']].isna().any().any() or data.hadm_id.duplicated().any():raise ValueError('Prediction input admission grain is invalid')
    for col in DATE_COLUMNS:
        original=data[col];data[col]=pd.to_datetime(original,errors='coerce')
        if (original.notna()&data[col].isna()).any():raise ValueError('Invalid typed prediction timestamp')
    data['age']=pd.to_numeric(data.age,errors='coerce').astype(float)
    data['gender']=data.gender.astype(object).where(data.gender.notna(),np.nan)
    if data.age.isna().any() or data.age.lt(18).any():raise ValueError('Adult base age is invalid')
    if not data.raas_recorded_by_24h.isin([0,1]).all():raise ValueError('Invalid recorded-order indicator')
    positive=data.raas_recorded_by_24h.eq(1)
    bound=data.admittime+pd.Timedelta(hours=24)
    valid_order=(data.last_qualifying_order_time.notna()&data.last_qualifying_order_time.le(bound)
                 &data.last_qualifying_start_time.ge(data.admittime)&data.last_qualifying_start_time.lt(bound))
    if (positive&~valid_order).any():raise ValueError('Order feature crosses its information-time boundary')
    return data.sort_values(['subject_id','hadm_id'],kind='stable').reset_index(drop=True)


def eligibility(data,hours):
    if hours not in (0,24):raise ValueError('Prediction time must be 0 or 24 hours')
    point=data.admittime+pd.Timedelta(hours=hours)
    reason=pd.Series('included',index=data.index,dtype='object')
    def exclude(mask,label):reason.loc[reason.eq('included')&mask.fillna(False)]=label
    flag=data.hospital_expire_flag
    exclude(data.admittime.isna(),'missing_admittime')
    exclude(data.dischtime.isna(),'missing_dischtime')
    exclude(data.dischtime.lt(data.admittime),'discharge_before_admission')
    exclude(~flag.isin([0,1]),'invalid_or_missing_expire_flag')
    exclude(flag.eq(1)&data.deathtime.isna(),'death_flag_without_deathtime')
    exclude(flag.eq(0)&data.deathtime.notna(),'survival_flag_with_deathtime')
    exclude(data.deathtime.lt(data.admittime),'death_before_admission')
    exclude(data.deathtime.gt(data.dischtime),'death_after_discharge')
    exclude(data.dischtime.le(point),'discharge_at_or_before_prediction')
    exclude(flag.eq(1)&data.deathtime.le(point),'death_at_or_before_prediction')
    exclude(data.icu_unknown_intime.gt(0),'unknown_icu_entry_time')
    exclude(data.first_icu_intime.le(point),'icu_entry_at_or_before_prediction')
    location=data[f'location_status_{hours}h'].fillna('no_covering_location')
    for status in ['no_covering_location','unconfirmed_interval_end','unconfirmed_unit','overlapping_locations','not_target_ward']:
        exclude(location.eq(status),'location_'+status)
    exclude(~location.isin(['confirmed_non_icu_ward','no_covering_location','unconfirmed_interval_end','unconfirmed_unit','overlapping_locations','not_target_ward']),'location_unknown_status')
    return reason.eq('included'),reason


def classify_location(transfers,point):
    """Synthetic/reference reconstruction: entries <=t; half-open stay intervals.

    No unit entered after t is used to backfill t. Missing interval ends or
    overlapping distinct units are unconfirmed, never assigned a ward.
    """
    if transfers.empty:return 'no_covering_location'
    active=transfers.loc[transfers.eventtype.str.lower().isin(['ed','admit','transfer'])
                         &transfers.intime.le(point)&(transfers.outtime.gt(point)|transfers.outtime.isna())]
    if active.empty:return 'no_covering_location'
    if active.outtime.isna().any():return 'unconfirmed_interval_end'
    if active.careunit.isna().any() or active.careunit.astype(str).str.upper().eq('UNKNOWN').any():return 'unconfirmed_unit'
    units=active.careunit.unique()
    if len(units)>1:return 'overlapping_locations'
    return 'confirmed_non_icu_ward' if units[0] in WARD_UNITS else 'not_target_ward'


def eligible_sql_predicate(hours):
    if hours not in (0,24):raise ValueError('Invalid prediction time')
    point=f'DATETIME_ADD(admittime, INTERVAL {hours} HOUR)'
    return f'''admittime IS NOT NULL AND dischtime IS NOT NULL
AND dischtime > {point}
AND ((hospital_expire_flag = 0 AND deathtime IS NULL)
 OR (hospital_expire_flag = 1 AND deathtime > {point} AND deathtime <= dischtime))
AND icu_unknown_intime = 0
AND (first_icu_intime IS NULL OR first_icu_intime > {point})
AND location_status_{hours}h = 'confirmed_non_icu_ward'
'''


def read_inputs(root=ROOT,project='mimic-iv-portfolio',dataset='nonicu_raas'):
    from google.cloud import bigquery
    sql=input_sql(root,project,dataset)
    client=bigquery.Client(project=project)
    if client.get_dataset(f'{project}.{dataset}').location!='US':raise ValueError('Expected US source/destination location')
    dry=client.query(sql,location='US',job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False))
    if dry.total_bytes_processed>LIMIT:raise RuntimeError('Prediction input source scan exceeds 10 GiB')
    config=bigquery.QueryJobConfig(maximum_bytes_billed=LIMIT)
    job=client.query(sql,location='US',job_config=config)
    frame=job.result().to_dataframe(create_bqstorage_client=False)
    data=prepare_inputs(frame)
    # The SQL count uses independent typed predicates; no model rows leave memory.
    wrapped='WITH prediction_input AS (\n'+sql+'\n)\n'
    checks=[]
    for hours in [0,24]:
        q=wrapped+f'SELECT COUNT(*) AS admissions,COUNTIF(hospital_expire_flag=1) AS deaths FROM prediction_input WHERE '+eligible_sql_predicate(hours)
        count_job=client.query(q,location='US',job_config=config)
        row=next(iter(count_job.result()))
        mask,_=eligibility(data,hours)
        if int(row.admissions)!=int(mask.sum()) or int(row.deaths)!=int(data.loc[mask,'hospital_expire_flag'].sum()):raise AssertionError('Independent SQL/Python eligibility counts disagree')
        checks.append({'prediction_hours':hours,'admissions':int(row.admissions),'deaths':int(row.deaths),'job_id':count_job.job_id,'bytes_processed':count_job.total_bytes_processed})
    # Independently reconstruct actual transfer intervals for a deterministic sample.
    sample_sql=f"""SELECT b.subject_id,b.hadm_id,b.admittime,t.transfer_id,t.eventtype,t.careunit,t.intime,t.outtime
FROM `{project}.{dataset}.base_admissions` b
LEFT JOIN `physionet-data.mimiciv_3_1_hosp.transfers` t USING(subject_id,hadm_id)
WHERE MOD(ABS(FARM_FINGERPRINT(CAST(b.hadm_id AS STRING))),1000)=0"""
    sample_job=client.query(sample_sql,location='US',job_config=config)
    sample=sample_job.result().to_dataframe(create_bqstorage_client=False)
    for col in ['admittime','intime','outtime']:sample[col]=pd.to_datetime(sample[col])
    expected=data.set_index('hadm_id');mismatches=0;sample_admissions=0
    for hadm,group in sample.groupby('hadm_id'):
        sample_admissions+=1
        native=group.loc[group.transfer_id.notna()]
        for hours in [0,24]:
            status=classify_location(native,group.admittime.iloc[0]+pd.Timedelta(hours=hours))
            mismatches+=int(status!=expected.loc[hadm,f'location_status_{hours}h'])
    if not sample_admissions or mismatches:raise AssertionError('Native transfer interval reconstruction disagrees with SQL')
    location_check={'sample_admissions':sample_admissions,'prediction_points_checked':sample_admissions*2,
                    'mismatches':mismatches,'sampling':'deterministic admission hash modulo 1000 = 0',
                    'job_id':sample_job.job_id,'bytes_processed':sample_job.total_bytes_processed,'row_exports':False}
    metadata={'query_sha256':hashlib.sha256(sql.encode()).hexdigest(),'dry_run_bytes':dry.total_bytes_processed,
              'retrieval_job_id':job.job_id,'retrieval_bytes_processed':job.total_bytes_processed,'sql_python_eligibility_checks':checks,
              'native_transfer_reconstruction':location_check,'source':'MIMIC-IV v3.1 adult base, transfers, icustays, prescriptions, poe','rows_in_memory':len(data),'row_exports':False}
    return data,metadata


def make_model(verified_order=False):
    columns=[('age',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),['age']),
             ('gender',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Unknown')),('encode',OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=False))]),['gender'])]
    if verified_order:columns.append(('verified_raas','passthrough',['raas_recorded_by_24h']))
    return Pipeline([('prep',ColumnTransformer(columns,remainder='drop')),
                     ('logit',LogisticRegression(C=1.0,solver='lbfgs',max_iter=2000,class_weight=None))])


def independent_rank_metrics(y,p,weights=None):
    """Mann-Whitney ROC and threshold-group AP, independent of sklearn's curve routines."""
    y=np.asarray(y,dtype=int);p=np.asarray(p,dtype=float)
    w=np.ones(len(y)) if weights is None else np.asarray(weights,dtype=float)
    _,index=np.unique(p,return_inverse=True)
    positive=np.bincount(index,weights=w*y);negative=np.bincount(index,weights=w*(1-y),minlength=len(positive))
    if positive.sum()<=0 or negative.sum()<=0:raise ValueError('Both outcomes required')
    auc=np.dot(positive,np.cumsum(negative)-.5*negative)/(positive.sum()*negative.sum())
    tp=np.cumsum(positive[::-1]);total=tp+np.cumsum(negative[::-1])
    precision=np.divide(tp,total,out=np.zeros_like(tp),where=total>0)
    ap=np.dot(precision,positive[::-1])/positive.sum()
    return float(auc),float(ap)


def calibration_diagnostic(y,p):
    logit=np.log(np.clip(p,1e-12,1-1e-12)/(1-np.clip(p,1e-12,1-1e-12)))
    if np.ptp(logit)<1e-12:
        return {'calibration_intercept':None,'calibration_slope':None,'calibration_fit_converged':False,'calibration_warnings':'ConstantScores'}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        fit=sm.GLM(y,np.column_stack([np.ones(len(y)),logit]),family=sm.families.Binomial()).fit(maxiter=200,tol=1e-8)
    return {'calibration_intercept':float(fit.params[0]),'calibration_slope':float(fit.params[1]),
            'calibration_fit_converged':bool(fit.converged),'calibration_warnings':','.join(sorted({type(x.message).__name__ for x in caught}))}


def test_patient_bootstrap(y,p,groups,hours,n_boot=BOOTSTRAPS):
    _,codes=np.unique(groups,return_inverse=True);n_groups=int(codes.max()+1)
    rng=np.random.default_rng(BOOTSTRAP_SEED+hours)
    edges=np.unique(np.quantile(p,np.linspace(0,1,11)))
    bins=np.searchsorted(edges[1:-1],p,side='left');n_bins=int(bins.max()+1)
    rows=[];bin_rates=[];failed=0
    for _ in range(n_boot):
        frequency=np.bincount(rng.integers(n_groups,size=n_groups),minlength=n_groups)
        w=frequency[codes].astype(float)
        if np.dot(w,y)==0 or np.dot(w,1-y)==0:failed+=1;continue
        rows.append([roc_auc_score(y,p,sample_weight=w),average_precision_score(y,p,sample_weight=w),np.average((y-p)**2,weights=w)])
        totals=np.bincount(bins,weights=w,minlength=n_bins)
        events=np.bincount(bins,weights=w*y,minlength=n_bins)
        bin_rates.append(np.divide(events,totals,out=np.full(n_bins,np.nan),where=totals>0))
    available=len(rows)>=np.ceil(.95*n_boot)
    limits=np.quantile(np.asarray(rows),[.025,.975],axis=0) if available else np.full((2,3),np.nan)
    calibration=[]
    for k in range(n_bins):
        member=bins==k;rates=np.asarray(bin_rates)[:,k] if bin_rates else np.array([])
        finite=rates[np.isfinite(rates)]
        lo,hi=np.quantile(finite,[.025,.975]) if available and len(finite)>=np.ceil(.95*n_boot) else (np.nan,np.nan)
        calibration.append({'bin':k+1,'admissions':int(member.sum()),'deaths':int(y[member].sum()),
                            'mean_predicted_risk':float(p[member].mean()),'observed_risk':float(y[member].mean()),
                            'observed_CI_lower':float(lo),'observed_CI_upper':float(hi)})
    return limits,calibration,{'bootstrap_requested':n_boot,'bootstrap_successful':len(rows),'bootstrap_failed_one_class':failed,'interval_available':available,'bootstrap_seed':BOOTSTRAP_SEED+hours}


def evaluate(data,n_boot=BOOTSTRAPS,progress=None):
    data=prepare_inputs(data)
    split=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SPLIT_SEED).split(data,groups=data.subject_id))
    train_patients=np.unique(data.iloc[split[0]].subject_id);test_patients=np.unique(data.iloc[split[1]].subject_id)
    if len(np.intersect1d(train_patients,test_patients)):raise AssertionError('Patient overlap in master split')
    metrics=[];calibration=[];cohorts=[];exclusions=[]
    for hours in [0,24]:
        mask,reason=eligibility(data,hours);eligible=data.loc[mask]
        for name,indices in reason.groupby(reason).groups.items():
            rows=data.loc[indices];exclusions.append({'prediction_hours':hours,'reason':name,'admissions':len(rows),'flagged_deaths':int(rows.hospital_expire_flag.eq(1).sum())})
        train=eligible.loc[eligible.subject_id.isin(train_patients)];test=eligible.loc[eligible.subject_id.isin(test_patients)]
        if set(train.subject_id)&set(test.subject_id):raise AssertionError('Patient overlap in eligible split')
        followup_end=eligible.dischtime.where(eligible.hospital_expire_flag.eq(0),eligible.deathtime)
        later_icu=eligible.first_icu_intime.gt(eligible.admittime+pd.Timedelta(hours=hours))&eligible.first_icu_intime.le(followup_end)
        cohorts.append({'prediction_hours':hours,'base_admissions':len(data),'eligible_admissions':len(eligible),'eligible_patients':eligible.subject_id.nunique(),
                        'deaths':int(eligible.hospital_expire_flag.sum()),'train_admissions':len(train),'test_admissions':len(test),
                        'train_patients':train.subject_id.nunique(),'test_patients':test.subject_id.nunique(),'train_deaths':int(train.hospital_expire_flag.sum()),
                        'test_deaths':int(test.hospital_expire_flag.sum()),'overlapping_patients':0,'later_icu_admissions_retained':int(later_icu.sum()),
                        'deaths_at_or_before_24h_retained':int((eligible.hospital_expire_flag.eq(1)&eligible.deathtime.le(eligible.admittime+pd.Timedelta(hours=24))).sum()),
                        'verified_raas_admissions':int(eligible.raas_recorded_by_24h.sum()) if hours==24 else None,
                        'early_raas_record_admissions':int(eligible.early_raas_records.gt(0).sum()) if hours==24 else None,
                        'unverified_order_time_admissions':int(eligible.raas_unverified_order_time_records.gt(0).sum()) if hours==24 else None,
                        'late_order_time_admissions':int(eligible.raas_late_order_records.gt(0).sum()) if hours==24 else None})
        for name,point,verified in MODELS:
            if point!=hours:continue
            features=['age','gender']+(['raas_recorded_by_24h'] if verified else [])
            y_train=train.hospital_expire_flag.to_numpy(dtype=int);y_test=test.hospital_expire_flag.to_numpy(dtype=int)
            if len(np.unique(y_train))!=2 or len(np.unique(y_test))!=2:raise ValueError('Training and test labels must both contain both outcomes')
            model=make_model(verified)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always');model.fit(train[features],y_train)
            if any(type(x.message).__name__=='ConvergenceWarning' for x in caught):raise RuntimeError('Prediction model did not converge')
            p=model.predict_proba(test[features])[:,1]
            independent_auc,independent_ap=independent_rank_metrics(y_test,p)
            metric_error=max(abs(independent_auc-roc_auc_score(y_test,p)),abs(independent_ap-average_precision_score(y_test,p)))
            if metric_error>1e-12:raise AssertionError('Independent rank-metric check failed')
            limits,bins,bootstrap=test_patient_bootstrap(y_test,p,test.subject_id.to_numpy(),hours,n_boot)
            base_probability=float(y_train.mean())
            row={'model':name,'prediction_hours':hours,'features':','.join(features),'eligible_admissions':len(eligible),
                 'test_admissions':len(test),'test_patients':test.subject_id.nunique(),'test_deaths':int(y_test.sum()),'overlapping_patients':0,
                 'roc_auc':float(roc_auc_score(y_test,p)),'roc_auc_CI_lower':limits[0,0],'roc_auc_CI_upper':limits[1,0],
                 'pr_auc_average_precision':float(average_precision_score(y_test,p)),'pr_auc_CI_lower':limits[0,1],'pr_auc_CI_upper':limits[1,1],
                 'brier':float(np.mean((y_test-p)**2)),'brier_CI_lower':limits[0,2],'brier_CI_upper':limits[1,2],
                 'constant_train_prevalence_brier':float(np.mean((y_test-base_probability)**2)),
                 'mean_predicted_risk':float(p.mean()),'observed_test_risk':float(y_test.mean()),
                 'iterations':int(model.named_steps['logit'].n_iter_[0]),'converged':True,
                 'warnings':','.join(sorted({type(x.message).__name__ for x in caught})),
                 'independent_metric_check_passed':True,'independent_metric_max_error':float(metric_error),**bootstrap,**calibration_diagnostic(y_test,p)}
            metrics.append(row);calibration.extend([{'model':name,'prediction_hours':hours,**b} for b in bins])
            if progress:progress(name)
    quality={'base_admissions':len(data),'base_patients':data.subject_id.nunique(),'missing_recorded_gender':int(data.gender.isna().sum()),
             'early_raas_records':int(data.early_raas_records.sum()),
             'unverified_order_time_records':int(data.raas_unverified_order_time_records.sum()),
             'late_order_records_excluded_from_feature':int(data.raas_late_order_records.sum()),
             'duplicate_poe_link_records':int(data.raas_duplicate_poe_records.sum()),
             'icu_entries_after_discharge':int(data.first_icu_intime.gt(data.dischtime).sum()),
             'icu_entries_after_recorded_death':int((data.hospital_expire_flag.eq(1)&data.first_icu_intime.gt(data.deathtime)).sum()),'master_train_patients':len(train_patients),'master_test_patients':len(test_patients),
             'split_seed':SPLIT_SEED,'row_exports':False,'model_training_bootstrapped':False}
    return {'metrics':pd.DataFrame(metrics),'calibration':pd.DataFrame(calibration),'cohorts':pd.DataFrame(cohorts),'exclusions':pd.DataFrame(exclusions),'quality':quality}


def export_results(results,root=ROOT):
    root=Path(root);output=root/'python/outputs';output.mkdir(parents=True,exist_ok=True)
    for key in ['metrics','calibration','cohorts','exclusions']:
        frame=results[key]
        if {'subject_id','hadm_id','admittime','dischtime','deathtime'}.intersection(frame.columns):raise AssertionError('Attempted record export')
        frame.to_csv(output/f'prediction_time_{key}.csv',index=False)
    import matplotlib.pyplot as plt
    assets=root/'assets';assets.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(10,5),sharex=True,sharey=True)
    for ax,hours in zip(axes,[0,24]):
        groups=results['calibration'].loc[results['calibration'].prediction_hours.eq(hours)].groupby('model',sort=False)
        for model,rows in groups:
            x=rows.mean_predicted_risk.to_numpy()*100;y=rows.observed_risk.to_numpy()*100
            lo=rows.observed_CI_lower.to_numpy()*100;hi=rows.observed_CI_upper.to_numpy()*100
            augmented='verified RAAS' in model;color='#d97706' if augmented else '#2563eb'
            ax.vlines(x,lo,hi,color=color,alpha=.7)
            ax.plot(x,y,'s-' if augmented else 'o-',color=color,label='Age/sex + verified RAAS' if augmented else 'Age/sex')
        cohort=results['cohorts'].loc[results['cohorts'].prediction_hours.eq(hours)].iloc[0]
        time_label='Admission ward-confirmed subset' if hours==0 else '24-hour ward-confirmed cohort'
        ax.set_title(time_label+'\n'+f'Test deaths: {int(cohort.test_deaths):,}',fontsize=11)
        interval_ok=results['metrics'].loc[results['metrics'].prediction_hours.eq(hours),'interval_available'].all()
        if not interval_ok:ax.text(.03,.94,'Sparse events; intervals withheld',transform=ax.transAxes,va='top',fontsize=9,color='#9a3412')
        ax.set_xlabel('Mean predicted risk (%)');ax.grid(alpha=.2);ax.legend(fontsize=9)
    upper=results['calibration'].observed_CI_upper.dropna()
    limit=max(float(results['calibration'].mean_predicted_risk.max()),float(results['calibration'].observed_risk.max()),float(upper.max()) if len(upper) else 0)*105
    for ax in axes:ax.plot([0,limit],[0,limit],'--',color='#64748b');ax.set_xlim(0,limit);ax.set_ylim(0,limit)
    axes[0].set_ylabel('Observed in-hospital mortality (%)')
    fig.suptitle('Prediction-time models: patient-disjoint internal calibration')
    fig.text(.01,.01,'500 held-out-patient resamples; fixed trained models; separate time-specific populations; not external/prospective validation.',fontsize=9)
    fig.tight_layout(rect=[0,.07,1,.93]);fig.savefig(assets/'prediction_time_calibration.png',dpi=220);plt.close(fig)
