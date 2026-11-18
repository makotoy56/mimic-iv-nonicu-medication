"""Synthetic native-transfer boundaries; no credentials or patient records."""
from pathlib import Path
import sys,ast,re
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prediction_time_validation import classify_location,WARD_UNITS,ICU_UNITS,input_sql
T=pd.Timestamp('2020-01-01')
def frame(records):
 d=pd.DataFrame(records,columns=['intime','outtime','careunit','eventtype'])
 for col in ['intime','outtime']:d[col]=[pd.NaT if x is None else T+pd.Timedelta(hours=x) for x in d[col]]
 return d
def check(records,hours,expected):assert classify_location(frame(records),T+pd.Timedelta(hours=hours))==expected
ward='Medicine';icu=ICU_UNITS[0];ok='confirmed_non_icu_ward';no='no_covering_location'
check([(0,30,ward,'admit')],0,ok)
check([(0,24,ward,'admit')],24,no)
check([(0,24,ward,'admit'),(24,48,icu,'transfer')],24,'not_target_ward')
check([(0,24.000001,ward,'admit'),(24.000001,48,icu,'transfer')],24,ok)
check([(1,48,ward,'admit')],0,no) # Never backfill a later ward.
check([(-2,1,'Emergency Department','ed'),(1,48,ward,'transfer')],0,'not_target_ward')
check([(0,None,ward,'admit')],24,'unconfirmed_interval_end')
check([(0,48,None,'admit')],24,'unconfirmed_unit')
check([(0,48,'UNKNOWN','admit')],24,'unconfirmed_unit')
check([(0,48,ward,'admit'),(20,30,'Cardiology','transfer')],24,'overlapping_locations')
check([(0,48,ward,'admit'),(20,30,ward,'transfer')],24,ok)
check([],24,no)
check([(0,25,ward,'admit')],24,ok)
check([(0,1000,ward,'admit'),(1000,2000,icu,'transfer')],24,ok)
check([(0,48,'Observation','admit')],24,ok)
check([(0,48,'Emergency Department Observation','ed')],24,'not_target_ward')
sql=input_sql()
for cte,units in [('ward_units',WARD_UNITS),('icu_units',ICU_UNITS)]:
 match=re.search(cte+r' AS \(SELECT unit FROM UNNEST\((\[.*?\])\)',sql)
 assert ast.literal_eval(match.group(1))==units
print('PASS: 16 native-transfer interval cases, exact entry/exit, later ICU, unknown/overlapping location and SQL/Python ward mappings')
