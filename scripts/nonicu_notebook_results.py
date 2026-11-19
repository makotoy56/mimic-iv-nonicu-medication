"""Runtime-only presentation of aggregate Non-ICU notebook results.

No warehouse clients, clinical fits, patient exports, or cached result files are
used here. The notebook supplies objects from its current execution. The replay
entry point is explicitly labeled and is only for saved-output presentation QA.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from IPython.display import Markdown, HTML, display
from IPython.utils.capture import capture_output
from real_data_access import real_data_errors

SPEC_PATH = Path(__file__).with_name('nonicu_result_specs.json')
FORBIDDEN = {'subject_id','hadm_id','stay_id','transfer_id','poe_id',
             'admittime','dischtime','deathtime','predicted_probability'}

@dataclass
class ResultPayload:
    tables: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    image: object = None

@dataclass
class MimeBundle:
    data: dict
    metadata: dict = field(default_factory=dict)

    def _repr_mimebundle_(self,include=None,exclude=None):
        return self.data,self.metadata

def _frame(value):
    if isinstance(value,pd.Series):
        return value.rename(value.name or 'value').to_frame()
    if not isinstance(value,pd.DataFrame):
        raise TypeError('Presentation requires an explicit aggregate DataFrame or Series')
    return value.copy()

def schema_table(frame):
    """Describe columns, never display admission-level rows."""
    result=pd.DataFrame({'column':frame.columns.astype(str),
                         'non_null':frame.notna().sum().to_numpy(),
                         'dtype':frame.dtypes.astype(str).to_numpy()})
    result.attrs.update(rows=len(frame),columns=len(frame.columns),schema_summary=True)
    return result

def _number(value,digits=6):
    if pd.isna(value):return 'not available'
    if isinstance(value,(bool,np.bool_)):return str(bool(value))
    if isinstance(value,(int,np.integer)):return f'{int(value):,}'
    if isinstance(value,(float,np.floating)):
        return f'{value:,.0f}' if float(value).is_integer() else f'{value:.{digits}g}'
    return str(value)

def _pct(value):return 'not available' if pd.isna(value) else f'{100*float(value):.4f}%'

def _bool(value):
    if pd.isna(value):return False
    if isinstance(value,str):return value.strip().lower()=='true'
    return bool(value)

def _row_summary(frame,fields=None):
    fields=fields or [x for x in ['n','n_admissions','deaths','n_events','OR',
        'CI_lower','CI_upper','converged','inference_valid','bootstrap_successful',
        'bootstrap_requested','roc_auc','pr_auc','average_precision','ame'] if x in frame]
    if not fields:fields=list(frame.columns[:6])
    messages=[]
    for index,row in frame.head(5).iterrows():
        name=row.get('model',row.get('metric',row.get('validation',row.get('prediction_hours',index))))
        values='; '.join(f'{key}={_number(row[key])}' for key in fields)
        messages.append(f'{name}: {values}')
    suffix=f' Only the first {len(messages)} aggregate rows are summarized.' if len(frame)>len(messages) else ''
    return ' '.join(messages)+suffix

def _mortality(frame):
    messages=[]
    for index,row in frame.iterrows():
        group=row.get('exposure_group',row.get('exposure',index))
        n=row.get('n_admissions',row.get('n'))
        deaths=row.get('n_events',row.get('deaths'))
        rate=row.get('mortality_rate',row.get('mortality_proportion',deaths/n if n else np.nan))
        messages.append(f'{group}: {_number(deaths)} deaths / {_number(n)} admissions ({_pct(rate)}).')
    return ' '.join(messages)

def summarize(label,payload):
    """All result values come from this payload, never narrative constants."""
    frames=payload.tables;stats=payload.stats;first=frames[0] if frames else None
    if first is not None and first.attrs.get('schema_summary'):
        return f'Loaded {_number(first.attrs["rows"])} admissions and {_number(first.attrs["columns"])} columns. Non-null counts and types are shown above.'
    if label=='Table 01.4':
        row=first.iloc[0];return (f'Adult base: {_number(row.n_base)} admissions; ICU-associated exclusions: '
          f'{_number(row.n_excluded_icu)}; retained Non-ICU admissions: {_number(row.n_nonicu)} '
          f'({_pct(row.n_nonicu/row.n_base) if row.n_base else "not available"}).')
    if label=='Table 01.8':
        row=first.iloc[0];return f'Median age is {_number(row["median"])} years; interquartile range {_number(row.q1)}–{_number(row.q3)} years.'
    if label in {'Table 01.9','Table 04a.2'}:
        if 'hospital_expire_flag' in first:
            counts=first.set_index('hospital_expire_flag')['n']
        else:counts=first.iloc[:,0]
        return f'Total: {_number(counts.sum())} admissions; recorded in-hospital deaths: {_number(counts.get(1,0))} ({_pct(counts.get(1,0)/counts.sum()) if counts.sum() else "not available"}).'
    if label=='Table 01.13':return _row_summary(first,list(first.columns))
    if label in {'Table 02.3','Table 02.4','Table 02.5','Table 02.7','Table 00.1'}:
        return _row_summary(first,list(first.columns))
    if label in {'Table 03b.2','Table 04a.3','Table 04b.2','Table 04b.4'}:
        return _row_summary(first,list(first.columns))
    if label in {'Table 04a.6','Table 04a.7','Table 04b.3','Figure 04a.1'}:
        return _mortality(first)
    if label in {'Table 04b.6','Table 04b.7'}:
        converged=_bool(stats.get('converged',False))
        message=_row_summary(first)
        return f'Ordinary-MLE convergence: {converged}. '+message+(' Nominal intervals and p-values are diagnostic only because this fit did not converge.' if not converged else ' Check all finite-inference and separation diagnostics before interpretation.')
    if label=='Table 04b.8':
        exclusions=frames[-1].set_index('reason')
        included=exclusions.loc['included'] if 'included' in exclusions.index else None
        retained=0 if included is None else included.admissions
        deaths=0 if included is None else included.flagged_deaths
        return (f'Corrected eligibility retains {_number(retained)} admissions / {_number(deaths)} deaths. '
                f'Exclusive reason counts, including retained admissions, sum to {_number(exclusions.admissions.sum())}. '
                'The separate issue table overlaps and must not be summed as exclusions.')
    if label in {'Table 04b.9','Table 04b.10'}:
        n_valid=int(first.inference_valid.map(_bool).sum())
        return f'{n_valid}/{len(first)} specifications pass the reported inference-validity flag. '+_row_summary(first)
    if label in {'Table 04b.11','Table 04b.12'}:
        row=first.iloc[0]
        if label.endswith('.11'):
            return f'Mean predicted risks: no qualifying record {_pct(row.risk_unexposed)}; qualifying record {_pct(row.risk_exposed)}. These are model scenarios, not observed group rates.'
        return f'Qualifying-record minus no-record AME: {100*float(row.ame):.4f} percentage points. This is an observational model contrast, not a causal risk reduction.'
    if label=='Table 04b.14':
        messages=[]
        for row in first.itertuples():
            unit='percentage points' if row.metric=='ame' else '%'
            interval=(f'{100*row.CI_lower:.4f} to {100*row.CI_upper:.4f}'
                      if _bool(row.interval_available) and np.isfinite([row.CI_lower,row.CI_upper]).all() else 'withheld')
            messages.append(f'{row.metric}: {100*row.estimate:.4f} {unit}; 95% interval {interval}; accepted {int(row.bootstrap_successful)}/{int(row.bootstrap_requested)} draws.')
        return ' '.join(messages)
    if label in {'Table 04b.13','Table 04b.15'}:
        message=_row_summary(first,['train_admissions','test_admissions','test_deaths','overlapping_patients','roc_auc','pr_auc'] if label.endswith('.15') else None)
        if 'bootstrap_requested' in first:
            withheld=first.loc[~first.interval_available.map(_bool)] if 'interval_available' in first else first.iloc[0:0]
            message+=f' Intervals withheld for {len(withheld)}/{len(first)} rows.'
        return message
    if label=='Table 04c.1':return _row_summary(first,['prediction_hours','admissions','deaths','bytes_processed'])
    if label=='Table 04c.2':
        return _row_summary(first,['eligible_admissions','deaths','test_admissions','test_deaths',
            'overlapping_patients','later_icu_admissions_retained'])
    if label in {'Table 04c.3','Figure 04c.1'}:
        metrics=stats['metrics'];messages=[]
        for row in metrics.itertuples():
            requested=int(row.bootstrap_requested);successful=int(row.bootstrap_successful)
            threshold=math.ceil(.95*requested)
            interval='intervals available' if _bool(row.interval_available) else f'intervals withheld ({successful}/{requested} usable draws; required {threshold}/{requested})'
            messages.append(f'{row.model}: {int(row.test_admissions):,} test admissions / {int(row.test_deaths):,} deaths; ROC AUC {row.roc_auc:.6f}; AP {row.pr_auc_average_precision:.6f}; {interval}.')
        if label.startswith('Figure'):
            sparse=metrics.loc[~metrics.interval_available.map(_bool)]
            if len(sparse):messages.append('Sparse-event panels cannot establish reliable model quality from the line shape. Zero observed mortality in a bin does not mean zero true risk.')
            messages.append('The panels use different eligible populations and do not establish improvement from waiting 24 hours.')
        return ' '.join(messages)
    if label in {'Figure 04b.1','Figure 04b.4','Figure 04b.D1','Figure 04b.D2'}:
        accepted=pd.Series(True,index=first.index)
        for flag in ['inference_valid','interval_available']:
            if flag in first:accepted &= first[flag].map(_bool)
        message=_row_summary(first.loc[accepted],['OR','CI_lower','CI_upper','n','deaths'])
        return message+f' Estimates/intervals withheld for {int((~accepted).sum())}/{len(first)} displayed specifications.'
    if label=='Figure 04b.2':
        ages=np.asarray(stats['ages']);return f'The two model scenarios are evaluated at {len(ages)} ages, from {_number(ages.min())} to {_number(ages.max())} years, holding other covariates at the same typical profile.'
    if label in {'Figure 04b.3','Figure 04b.5'}:
        ages=np.asarray(stats['ages']);values=np.asarray(stats['risk_difference'])
        return (f'Across ages {_number(ages.min())}–{_number(ages.max())}, the qualifying-record minus no-record '
                f'predicted risk difference ranges from {100*values.min():.4f} to {100*values.max():.4f} percentage points. '
                f'Uncertainty method: {stats["uncertainty_method"]}. '
                +('Intervals are withheld.' if stats.get('interval_available') is False else ''))
    if label=='Figure 03b.1':return _row_summary(first,['n','age_mean','los_median'])
    return f'{len(first):,} aggregate rows are displayed. '+_row_summary(first)

def _forest(frame,title):
    import matplotlib.pyplot as plt
    names=['Primary cohort','24h landmark','24h landmark + proxy']
    data=frame.set_index('model').loc[names]
    fig,ax=plt.subplots(figsize=(9,4));positions=np.arange(len(data))
    finite=np.isfinite(data[['OR','CI_lower','CI_upper']].astype(float)).all(axis=1)
    if 'interval_available' in data:finite &= data.interval_available.map(_bool)
    if 'inference_valid' in data:finite &= data.inference_valid.map(_bool)
    valid=data.loc[finite];pos=positions[finite.to_numpy()]
    if len(valid):ax.errorbar(valid.OR,pos,xerr=[valid.OR-valid.CI_lower,valid.CI_upper-valid.OR],fmt='o',capsize=5,color='#2563eb')
    for index in positions[~finite.to_numpy()]:ax.text(.5,index,'Interval withheld',ha='center')
    ax.axvline(1,color='#64748b',linestyle='--');ax.set_xscale('log')
    ax.set_xlim(min(.2,float(valid.CI_lower.min())*.9) if len(valid) else .2,
                max(1.2,float(valid.CI_upper.max())*1.1) if len(valid) else 1.4)
    ax.set_yticks(positions,[f'{name}\nN={int(row.n):,}; deaths={int(row.deaths):,}' for name,row in data.iterrows()]);ax.invert_yaxis()
    ax.set_xlabel('Early prescription-record OR (log scale)');ax.set_title(title)
    fig.tight_layout();return fig

def _age_figure(frame):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,5));ax.plot(frame.age,100*frame.risk_difference,label='Qualifying record − no record')
    if np.isfinite(frame[['CI_lower','CI_upper']]).all().all():ax.fill_between(frame.age,100*frame.CI_lower,100*frame.CI_upper,alpha=.25,label='95% patient-cluster interval')
    else:ax.text(.03,.05,'Intervals withheld',transform=ax.transAxes)
    ax.axhline(0,linestyle='--',color='#64748b');ax.set_xlabel('Age (years)');ax.set_ylabel('Predicted risk difference (percentage points)')
    ax.set_title('Age-specific contrast at a typical covariate profile');ax.legend();fig.tight_layout();return fig

def calibration_figure(results):
    """Draw directly from this execution's aggregate bins, never a PNG path."""
    import matplotlib.pyplot as plt
    bins=results['calibration'];metrics=results['metrics'];cohorts=results['cohorts']
    fig,axes=plt.subplots(1,2,figsize=(10,5),sharex=True,sharey=True)
    upper=[]
    for ax,hours in zip(axes,[0,24]):
        for model,rows in bins.loc[bins.prediction_hours.eq(hours)].groupby('model',sort=False):
            metric=metrics.loc[metrics.model.eq(model)].iloc[0]
            x=rows.mean_predicted_risk.to_numpy()*100;y=rows.observed_risk.to_numpy()*100
            augmented='verified RAAS' in model;color='#d97706' if augmented else '#2563eb'
            if _bool(metric.interval_available):
                ax.vlines(x,100*rows.observed_CI_lower,100*rows.observed_CI_upper,color=color,alpha=.7)
                upper.extend(rows.observed_CI_upper.dropna().tolist())
            ax.plot(x,y,'s-' if augmented else 'o-',color=color,label='Age/sex + verified RAAS' if augmented else 'Age/sex')
        row=cohorts.loc[cohorts.prediction_hours.eq(hours)].iloc[0]
        ax.set_title(('Admission ward-confirmed subset' if hours==0 else '24-hour ward-confirmed cohort')+f'\nTest deaths: {int(row.test_deaths):,}')
        if not metrics.loc[metrics.prediction_hours.eq(hours),'interval_available'].map(_bool).all():
            ax.text(.03,.94,'Intervals withheld',transform=ax.transAxes,color='#9a3412',va='top')
        ax.set_xlabel('Mean predicted risk (%)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    limit=max(float(bins.mean_predicted_risk.max()),float(bins.observed_risk.max()),max(upper,default=0))*105
    for ax in axes:ax.plot([0,limit],[0,limit],'--',color='#64748b');ax.set_xlim(0,limit);ax.set_ylim(0,limit)
    axes[0].set_ylabel('Observed in-hospital mortality (%)')
    fig.suptitle('Prediction-time models: patient-disjoint internal calibration')
    requested='/'.join(map(str,sorted(set(metrics.bootstrap_requested.astype(int)))))
    fig.text(.01,.01,f'{requested} requested held-out-patient draws; fixed trained models; separate risk sets; not external/prospective validation.',fontsize=8)
    fig.tight_layout(rect=[0,.07,1,.93]);return fig

def prediction_metric_tables(metrics):
    discrimination=['model','test_admissions','test_deaths','roc_auc','roc_auc_CI_lower',
        'roc_auc_CI_upper','pr_auc_average_precision','pr_auc_CI_lower','pr_auc_CI_upper',
        'brier','interval_available']
    calibration=['model','mean_predicted_risk','observed_test_risk','calibration_intercept',
        'calibration_slope','calibration_fit_converged','iterations','bootstrap_requested',
        'bootstrap_successful','interval_available']
    return [metrics[discrimination].copy(),metrics[calibration].copy()]

def live_payload(label,ns,captured,previous_figure=None):
    """Select explicit aggregate objects; never dump the execution namespace."""
    last=ns.get('_notebook_result_value');stats={};tables=[];image=None
    schema_names={'Table 01.1':'df_base','Table 01.2':'df_base_race',
      'Table 01.3':'df_nonicu','Table 02.1':'df_expo','Table 02.2':'df',
      'Table 03a.1':'df_nonicu','Table 03a.2':'df_expo','Table 03b.1':'df','Table 04a.1':'df','Table 04b.1':'df'}
    if label=='Table 00.1':tables=[_frame(ns['df'])]
    elif label in schema_names:
        tables=[schema_table(ns[schema_names[label]])]
        if last is not None:tables.append(_frame(last))
    elif label=='Table 03b.2':
        df=ns['df'];tables=[pd.DataFrame([{'admissions':len(df),'unique_admissions':df.hadm_id.nunique(),
            'early_record_prevalence':ns['prev'],'any_consistency':ns['raas_any_definition_check'].mean(),
            'both_consistency':ns['raas_both_definition_check'].mean()}])]
    elif label=='Table 04a.3':
        df=ns['df'];tables=[pd.DataFrame([{'admissions':len(df),'mortality_percent':100*df.hospital_expire_flag.mean(),'median_age':df.age.median()}])]
    elif label=='Table 04b.2':tables=[pd.DataFrame([{'admissions':len(ns['X']),'features':ns['X'].shape[1],'outcome_rate':ns['y'].mean()}])]
    elif label=='Table 04b.4':tables=[pd.DataFrame([{'roc_auc':ns['auc'],'average_precision':ns['ap'],'observed_mortality':ns['y'].mean(),'mean_predicted_risk':np.mean(ns['risk_prob'])}])]
    elif label in {'Table 04b.6','Table 04b.7'}:
        tables=[_frame(last)];stats={'converged':bool(ns['model'].mle_retvals.get('converged',False))}
    elif label=='Table 04b.8':tables=[ns['landmark_diagnostics'],ns['landmark_exclusions']]
    elif label=='Table 04b.9':tables=[ns['landmark_model_comparison'],ns['compare_or']]
    elif label=='Table 04b.10':tables=[ns['firth_compare_raw']]
    elif label in {'Table 04b.11','Table 04b.12'}:tables=[pd.DataFrame([{'risk_unexposed':ns['p0_mean'],'risk_exposed':ns['p1_mean'],'ame':ns['ame']}])]
    elif label=='Table 04b.13':tables=[ns['firth_patient_ci'].merge(ns['firth_compare_raw'][['model','OR']],on='model',validate='one_to_one')]
    elif label=='Table 04b.14':tables=[ns['risk_patient_ci']]
    elif label=='Table 04b.15':tables=[ns['patient_split_validation']]
    elif label=='Table 04c.1':tables=[pd.DataFrame(ns['query_checks']['sql_python_eligibility_checks'])[['prediction_hours','admissions','deaths','bytes_processed']]]
    elif label in {'Table 04c.2','Table 04c.3','Figure 04c.1'}:
        result=ns['prediction_results'];stats={'metrics':result['metrics']}
        if label.endswith('.2'):tables=[result['cohorts'],result['exclusions']]
        elif label.startswith('Table'):tables=prediction_metric_tables(result['metrics'])
        else:image=calibration_figure(result)
    elif label in {'Figure 03b.1','Figure 04a.1'}:
        tables=[ns['summary'] if label.startswith('Figure 03b') else ns['python_unadjusted_outcomes']]
    elif label in {'Figure 04b.1','Figure 04b.4'}:
        points=ns['firth_compare_raw'].copy()
        if label.endswith('.4'):
            points=points.drop(columns=['CI_lower','CI_upper']).merge(ns['firth_patient_ci'][['model','CI_lower','CI_upper','interval_available']],on='model',validate='one_to_one')
        points=points.loc[points.model.isin(['Primary cohort','24h landmark','24h landmark + proxy'])]
        tables=[points];image=_forest(points,'Firth: 95% '+('profile-likelihood' if label.endswith('.1') else 'patient-cluster bootstrap')+' intervals')
    elif label=='Figure 04b.2':stats={'ages':ns['age_grid']}
    elif label=='Figure 04b.3':stats={'ages':ns['age_grid'],'risk_difference':ns['rd_line'],'uncertainty_method':f'{len(ns["rd_boot"])} admission-row bootstrap draws (historical method)'}
    elif label=='Figure 04b.5':
        age=ns['age_patient_ci'];stats={'ages':age.age.to_numpy(),'risk_difference':age.risk_difference.to_numpy(),'uncertainty_method':'patient-cluster bootstrap','interval_available':bool(np.isfinite(age[['CI_lower','CI_upper']]).all().all())};image=_age_figure(age)
    elif label.startswith('Table'):tables=[_frame(last)]
    if label.startswith('Figure') and image is None:
        images=[out for out in captured.outputs if 'image/png' in out.data or 'image/svg+xml' in out.data]
        if images:image=images[-1]
        elif ns.get('fig') is not None and ns['fig'] is not previous_figure:image=ns['fig']
        else:raise ValueError(f'{label}: this execution produced no figure')
    return ResultPayload([_frame(f) for f in tables],stats,image)

class NotebookResults:
    def __init__(self,context,emit=None,mode='live'):
        self.context=context;self.emit=emit or display;self.mode=mode
        self.specs=json.loads(SPEC_PATH.read_text())

    def source(self,text):
        project=self.context.get('PROJECT_ID');dataset=self.context.get('DATASET',self.context.get('DATASET_ID'))
        if project and dataset:text=text.replace('nonicu_raas.',f'{project}.{dataset}.')
        return text

    def overview(self,labels):
        """Present source references and execution mode once for the notebook."""
        import re
        grouped={};exports={}
        for label in dict.fromkeys(labels):
            reference=self.source(self.specs[label]['source'])
            reference=reference.replace('in this cell','in the corresponding analysis cell')
            reference=reference.replace("this cell's", "the corresponding analysis cell's")
            grouped.setdefault(reference,[]).append(label)
            for caption,target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',self.specs[label].get('exports','')):
                exports.setdefault(target,caption)
        if self.mode=='live':
            mode=('**Execution mode: live notebook execution.** Each numbered result '
                  'is generated from objects produced when its analysis cell finishes. '
                  'This header alone does not certify that later cells have completed.')
        else:
            mode=('**Execution mode of saved outputs: presentation replay.** '
                  'The numbered displays were refreshed from previously saved aggregate '
                  'tables and figure outputs; no clinical query or model fit was rerun. '
                  'Their execution counts are blank. A fresh Run All replaces these '
                  'saved displays with results from that execution.')
        references='\n'.join(f'- **{", ".join(names)}:** {reference}'
                             for reference,names in grouped.items())
        text=('## Data sources and execution mode\n\n'+mode+'\n\n'
              'Source tables and queries are specified in the analysis code. '
              'The first expandable index describes calculation inputs by result. '
              'During live execution, calculation and display share current in-memory '
              'aggregate objects. The separate CSV/JSON list contains saved aggregates '
              'and verification files, rather than original MIMIC-IV source tables.\n\n'
              '<details>\n<summary>Calculation inputs and source definitions</summary>\n\n'
              +references+'\n\n</details>')
        if exports:
            text+=('\n\n<details><summary>Saved aggregates and verification files (CSV/JSON)</summary>'
                   '<p>These files store aggregate results, diagnostics or execution records '
                   'for checking and reuse; they are not the original MIMIC-IV source tables. '
                   'During live notebook execution, displays use in-memory results. '
                   'Saved-output replay and validation workflows may read these files.</p><ul>'+
                   ''.join('<li><a href="'+escape(target,quote=True)+'">'+escape(caption)+'</a></li>' for target,caption in exports.items())+
                   '</ul></details>')
        self.emit(Markdown(text))

    def render(self,label,payload,diagnostics=''):
        spec=self.specs[label]
        safe_tables=[]
        for frame in payload.tables:
            if FORBIDDEN.intersection(map(str,frame.columns)) or FORBIDDEN.intersection(map(str,frame.index.names)):
                raise ValueError('Record-level identifiers/timestamps are forbidden in displayed result tables')
            frame=frame.copy()
            if 'interval_available' in frame:
                unavailable=~frame.interval_available.map(_bool)
                bounds=[c for c in frame if c in {'CI_lower','CI_upper'} or '_CI_lower' in c or '_CI_upper' in c]
                frame.loc[unavailable,bounds]=np.nan
            safe_tables.append(frame)
        payload=ResultPayload(safe_tables,payload.stats,payload.image)
        self.emit(Markdown(f'### {label} — {spec["title"]}'))
        if label.startswith('Table'):
            for index,frame in enumerate(payload.tables):
                if len(payload.tables)>1:self.emit(Markdown(f'**{chr(97+index)}. Aggregate output**'))
                shown=frame.copy()
                if label=='Table 04b.14':
                    shown[['estimate','CI_lower','CI_upper']]*=100
                    shown['unit']=np.where(shown.metric.eq('ame'),'percentage points','%')
                self.emit(shown)
        elif payload.image is not None:
            if hasattr(payload.image,'data') and isinstance(payload.image.data,dict):
                self.emit(MimeBundle(payload.image.data,getattr(payload.image,'metadata',{})))
            else:self.emit(payload.image)
        else:raise ValueError(f'{label}: missing figure; refusing stale-image fallback')
        summary=summarize(label,payload)
        self.emit(Markdown(f'**How to read**\n\n{spec["read"]}\n\n**What the results show**\n\n{summary}\n\n**Interpretation limits**\n\n{spec["limit"]}'))
        if diagnostics.strip():self.emit(HTML('<details><summary>Execution diagnostics</summary><pre>'+escape(diagnostics)+'</pre></details>'))

    @contextmanager
    def capture(self,labels,namespace):
        labels=[labels] if isinstance(labels,str) else labels
        previous_figure=namespace.get('fig')
        namespace['_notebook_result_value']=None
        with real_data_errors('notebook result input/calculation'):
            with capture_output(stdout=True,stderr=True,display=True) as captured:
                yield
        # Exceptions leave before this point: never publish a previous result.
        for index,label in enumerate(labels):
            payload=live_payload(label,namespace,captured,previous_figure)
            self.render(label,payload,(captured.stdout+captured.stderr) if index==len(labels)-1 else '')
            if payload.image is not None and hasattr(payload.image,'savefig'):
                import matplotlib.pyplot as plt
                plt.close(payload.image)

    @contextmanager
    def diagnostic(self,label,namespace):
        previous=namespace.get('fig')
        with capture_output(stdout=True,stderr=True,display=True) as captured:
            yield
        images=[o for o in captured.outputs if 'image/png' in o.data or 'image/svg+xml' in o.data]
        current=namespace.get('fig')
        if images or (current is not None and current is not previous):
            frame=namespace['or_ci'].loc[['exposure']] if label.endswith('D1') else namespace['compare_raw']
            self.render(label,ResultPayload([frame],image=images[-1] if images else current),captured.stdout+captured.stderr)
        else:
            self.emit(Markdown(f'**{label}: not produced.** This execution did not pass the existing plot-export gate; no historical image is substituted.'))
            if captured.stdout or captured.stderr:self.emit(HTML('<details><summary>Execution diagnostics</summary><pre>'+escape(captured.stdout+captured.stderr)+'</pre></details>'))
