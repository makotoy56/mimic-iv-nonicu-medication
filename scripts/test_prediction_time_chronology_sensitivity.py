"""Synthetic check of the post-QA filter and unchanged master patient allocation."""
from pathlib import Path
import contextlib,io,sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
with contextlib.redirect_stdout(io.StringIO()):
    import test_prediction_time_validation as fixtures
from prediction_time_chronology_sensitivity import sensitivity,uncertain_chronology

data=fixtures.frame.copy(deep=True)
original=fixtures.results['metrics'].copy(deep=True)
data.loc[[0,4],'first_icu_intime']=fixtures.hour(60)
assert int(uncertain_chronology(data).sum())==2
metrics,quality=sensitivity(data,original)
assert quality['base_uncertain_icu_chronology_admissions']==2
assert quality['master_patient_split_unchanged'] and quality['point_estimates_only']
assert metrics.excluded_uncertain_icu_admissions.eq(2).all()
assert metrics.eligible_admissions.eq(len(data)-2).all()
assert metrics.overlapping_patients.eq(0).all() and metrics.bootstrap_requested.eq(0).all()
pd.testing.assert_frame_equal(original,fixtures.results['metrics'])
assert data.loc[[0,4],'first_icu_intime'].eq(fixtures.hour(60)).all()
print('PASS: impossible future ICU chronology excluded only in the sensitivity; original metrics/data untouched; full-base patient split preserved')
