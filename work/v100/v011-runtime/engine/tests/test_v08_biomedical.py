from datetime import timedelta
import pytest
from vigile.monitoring import MonitoringService
from test_monitoring import request,obs
from conftest import add,NOW

def test_wrong_phase_not_current(engine):
    m=add(engine,'pre','physiology.heart_rate',70,'bpm',phase='PRE_MISSION')
    r=MonitoringService(engine).run(request(measurements=[m]),'researcher')
    i=next(i for i in r['domains'][0]['indicators'] if i['variable']==m.variable)
    assert i['state']=='CURRENT_MISSION_PHASE_MISMATCH' and i['value'] is None

def test_wrong_phase_cannot_trigger_hypoglycemia(engine):
    m=add(engine,'pre-glucose','plasma_glucose_mg_dl',50,'mg/dL',phase='PRE_MISSION',method='VENOUS_PLASMA')
    svc=MonitoringService(engine);r=svc.run(request(measurements=[m],observations=[obs('known_diabetes',True)]),'researcher')
    assert r['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']['diagnostic_status']!='CRITERIA_MET'
    assert svc.replay(r['id'])['matches']

def test_distinct_samples_not_collapsed(engine):
    a=add(engine,'g1','plasma_glucose_mg_dl',50,'mg/dL',method='VENOUS_PLASMA',timestamp=NOW-timedelta(minutes=2))
    b=add(engine,'g2','plasma_glucose_mg_dl',55,'mg/dL',method='VENOUS_PLASMA')
    r=MonitoringService(engine).run(request(measurements=[a,b]),'researcher')
    snap=engine.store.get('clinical_evaluation',r['clinical_evaluations']['HYPOGLYCEMIA']['id'])['snapshot']
    assert {o['sample_id'] for o in snap['observations']}=={'g1','g2'}

def test_explicit_sample_mapping_preserved(engine):
    m=add(engine,'g','plasma_glucose_mg_dl',50,'mg/dL',method='VENOUS_PLASMA')
    r=MonitoringService(engine).run(request(measurements=[m],sample_ids={'g':'actual-collection'}),'researcher')
    snap=engine.store.get('clinical_evaluation',r['clinical_evaluations']['HYPOGLYCEMIA']['id'])['snapshot']
    assert snap['observations'][0]['sample_id']=='actual-collection'

@pytest.mark.parametrize('order',[False,True])
def test_dose_coverage_gaps_and_order(engine,order):
    a=add(engine,'d1','radiation.interval_effective_dose',1,'mSv',device_id='dose',method='INTERVAL_TOTAL',timestamp=NOW-timedelta(days=3),interval_end=NOW-timedelta(days=2))
    b=add(engine,'d2','radiation.interval_effective_dose',2,'mSv',device_id='dose',method='INTERVAL_TOTAL',timestamp=NOW-timedelta(days=1),interval_end=NOW)
    r=MonitoringService(engine).run(request(history_start=NOW-timedelta(days=3),measurements=[b,a] if order else [a,b]),'researcher')
    dose=r['domains'][2]['accumulated_dose']
    assert dose['state']=='PARTIAL_WINDOW' and dose['effective_dose_mSv']==3
    assert dose['coverage_seconds']==2*86400

def test_duplicate_dose_no_double_count(engine):
    a=add(engine,'d1','radiation.interval_effective_dose',1,'mSv',device_id='dose',method='INTERVAL_TOTAL',timestamp=NOW-timedelta(days=1),interval_end=NOW)
    b=add(engine,'d2','radiation.interval_effective_dose',1,'mSv',device_id='dose',method='INTERVAL_TOTAL',timestamp=NOW-timedelta(days=1),interval_end=NOW)
    r=MonitoringService(engine).run(request(measurements=[a,b]),'researcher')
    assert r['domains'][2]['accumulated_dose']['effective_dose_mSv'] is None

def test_emergency_escalates_same_context(engine):
    svc=MonitoringService(engine);svc.run(request(observations=[obs('known_diabetes',True),obs('plasma_glucose_mg_dl',50)]),'researcher')
    r=svc.run(request(id='cycle2',previous_run_id='cycle1',observations=[obs(k,True) for k in ('altered_mental_or_physical_status','assistance_required_for_hypoglycemia','hypoglycemia_event_clinically_attributed')]),'researcher')
    e=next(e for e in r['events'] if e['key']=='clinical:HYPOGLYCEMIA')
    assert e['urgency']=='EMERGENCY' and e['notify']
    assert svc.replay(r['id'])['matches']
