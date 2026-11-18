"""Post-QA sensitivity: exclude uncertain ICU chronology, preserve master split.

Primary prespecified results are not overwritten. This is a point-estimate
sensitivity only, not a second bootstrap or a feature/model-selection exercise.
"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.model_selection import GroupShuffleSplit
from prediction_time_validation import read_inputs,prepare_inputs,eligibility,make_model,MODELS,SPLIT_SEED,independent_rank_metrics,ROOT


def uncertain_chronology(data):
    return data.first_icu_intime.gt(data.dischtime)|(data.hospital_expire_flag.eq(1)&data.first_icu_intime.gt(data.deathtime))


def sensitivity(data,primary_metrics):
    data=prepare_inputs(data);uncertain=uncertain_chronology(data)
    train_index,test_index=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SPLIT_SEED).split(data,groups=data.subject_id))
    train_patients=np.unique(data.iloc[train_index].subject_id);test_patients=np.unique(data.iloc[test_index].subject_id)
    rows=[]
    for name,hours,verified in MODELS:
        original,_=eligibility(data,hours);mask=original&~uncertain
        eligible=data.loc[mask];train=eligible.loc[eligible.subject_id.isin(train_patients)];test=eligible.loc[eligible.subject_id.isin(test_patients)]
        if set(train.subject_id)&set(test.subject_id):raise AssertionError('Patient overlap in chronology sensitivity')
        features=['age','gender']+(['raas_recorded_by_24h'] if verified else [])
        y=train.hospital_expire_flag.to_numpy(dtype=int);z=test.hospital_expire_flag.to_numpy(dtype=int)
        model=make_model(verified)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(train[features],y)
        if any(type(x.message).__name__=='ConvergenceWarning' for x in caught):raise RuntimeError('Sensitivity fit did not converge')
        p=model.predict_proba(test[features])[:,1];auc=float(roc_auc_score(z,p));ap=float(average_precision_score(z,p))
        np.testing.assert_allclose(independent_rank_metrics(z,p),[auc,ap],atol=1e-12)
        original_row=primary_metrics.loc[primary_metrics.model.eq(name)].iloc[0]
        rows.append({'model':name,'prediction_hours':hours,'eligible_admissions':len(eligible),'excluded_uncertain_icu_admissions':int((original&uncertain).sum()),
                     'test_admissions':len(test),'test_deaths':int(z.sum()),'overlapping_patients':0,'roc_auc':auc,'pr_auc_average_precision':ap,
                     'brier':float(np.mean((z-p)**2)),'roc_auc_difference_from_prespecified':auc-float(original_row.roc_auc),
                     'pr_auc_difference_from_prespecified':ap-float(original_row.pr_auc_average_precision),
                     'converged':True,'iterations':int(model.named_steps['logit'].n_iter_[0]),'bootstrap_requested':0})
    return pd.DataFrame(rows),{'base_uncertain_icu_chronology_admissions':int(uncertain.sum()),
                              'master_patient_split_unchanged':True,'post_QA_not_prespecified_primary':True,'point_estimates_only':True}


if __name__=='__main__':
    from datetime import datetime,timezone
    from google.cloud import bigquery
    from prediction_time_validation import input_sql,eligible_sql_predicate,LIMIT
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='mimic-iv-portfolio');parser.add_argument('--dataset',default='nonicu_raas')
    args=parser.parse_args()
    started=datetime.now(timezone.utc).isoformat()
    data,queries=read_inputs(project=args.project,dataset=args.dataset)
    primary=pd.read_csv(ROOT/'python/outputs/prediction_time_metrics.csv')
    metrics,checks=sensitivity(data,primary)
    client=bigquery.Client(project=args.project);jobs=[]
    for hours in [0,24]:
        sql='WITH input AS (\n'+input_sql(project=args.project,dataset=args.dataset)+'\n) SELECT COUNT(*) AS n FROM input WHERE ('+eligible_sql_predicate(hours)+''')
AND NOT COALESCE(first_icu_intime > dischtime OR (hospital_expire_flag=1 AND first_icu_intime > deathtime),FALSE)'''
        job=client.query(sql,location='US',job_config=bigquery.QueryJobConfig(maximum_bytes_billed=LIMIT));row=next(iter(job.result()))
        expected=int(metrics.loc[metrics.prediction_hours.eq(hours),'eligible_admissions'].iloc[0])
        if int(row.n)!=expected:raise AssertionError('Chronology-sensitivity SQL/Python count mismatch')
        jobs.append({'prediction_hours':hours,'admissions':expected,'job_id':job.job_id,'bytes_processed':job.total_bytes_processed})
    metrics.to_csv(ROOT/'python/outputs/prediction_time_chronology_sensitivity.csv',index=False)
    receipt={'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'queries':queries,'independent_sql_counts':jobs,
             'quality':checks,'models':json.loads(metrics.to_json(orient='records')),'row_exports':False}
    (ROOT/'python/outputs/prediction_time_chronology_sensitivity.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print('PASS: post-QA chronology sensitivity complete; same master patient allocation; aggregate-only results saved; primary results untouched')
