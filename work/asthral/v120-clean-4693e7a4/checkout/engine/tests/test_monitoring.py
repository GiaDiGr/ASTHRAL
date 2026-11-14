from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from vigile.monitoring import MonitoringService
from vigile.monitoring_models import MonitoringRequest
from vigile.clinical_models import ClinicalRequest
from vigile.clinical_engine import ClinicalService
from vigile.clinical_simulator import observation
from vigile.models import BaselineRequest
from conftest import NOW,add

def request(**kw):
    return MonitoringRequest(**(dict(id='cycle1',subject_id='crew',mission_id='mission',as_of=NOW,
      history_start=NOW-timedelta(days=30),clinical_window_start=NOW-timedelta(hours=1),clinical_context_id='event1',
      policy_reference='SYNTHETIC_TEST_POLICY_NOT_CLINICAL',population='ADULT',age_years=30)|kw))

def obs(field,value,**kw):return observation(field,value,timestamp=NOW,**kw)

@pytest.mark.parametrize('value,level',[(70,None),(69.99,1),(54,1),(53.99,2),(0,2)])
def test_hypoglycemia_exact_boundaries(engine,value,level):
    r=ClinicalService(engine).evaluate(ClinicalRequest(subject_id='crew',mission_id='mission',condition_id='HYPOGLYCEMIA',population='ADULT',as_of=NOW,window_start=NOW-timedelta(hours=1),observations=[obs('known_diabetes',True),obs('plasma_glucose_mg_dl',value)]),'researcher')
    out=r['results']['HYPOGLYCEMIA']
    assert out['metadata']['hypoglycemia_level_minimum_supported']==level
    assert (out['diagnostic_status']=='CRITERIA_MET')==(level is not None)
    assert out['protocol_status'].startswith('BLOCKED')
    assert out['treatment_status']=='NOT_STARTED'
    assert ClinicalService(engine).replay(r['id'])['matches']

@pytest.mark.parametrize('extra,level',[(dict(known_diabetes=False),None),(dict(known_diabetes=None),None),(dict(altered_mental_or_physical_status=True,assistance_required_for_hypoglycemia=True,hypoglycemia_event_clinically_attributed=True),3)])
def test_hypoglycemia_context(engine,extra,level):
    observations=[obs(k,v) for k,v in (dict(known_diabetes=True,plasma_glucose_mg_dl=90)|extra).items()]
    result=MonitoringService(engine).run(request(observations=observations),'researcher')
    assert result['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']['metadata']['hypoglycemia_level_minimum_supported']==level
    assert MonitoringService(engine).replay(result['id'])['matches']

def test_empty_cycle_and_replay(engine):
    svc=MonitoringService(engine);r=svc.run(request(),'researcher')
    assert len(r['domains'])==6
    assert all(not d['available_indicators'] for d in r['domains'])
    assert svc.replay(r['id'])['matches']
    assert svc.run(request(),'researcher')==r
    with pytest.raises(ValueError,match='IDEMPOTENCY'):svc.run(request(policy_reference='changed'),'researcher')
    assert engine.store.verify()

def test_urgent_new_evidence_not_suppressed(engine):
    svc=MonitoringService(engine)
    one=svc.run(request(observations=[obs('known_diabetes',True),obs('plasma_glucose_mg_dl',50)]),'researcher')
    two=svc.run(request(id='cycle2',previous_run_id='cycle1'),'researcher')
    hypo=lambda r:next(e for e in r['events'] if e['key']=='clinical:HYPOGLYCEMIA')
    assert hypo(one)['notify'] and not hypo(two)['notify']
    three=svc.run(request(id='cycle3',previous_run_id='cycle2',as_of=NOW+timedelta(minutes=1),observations=[observation('plasma_glucose_mg_dl',49,timestamp=NOW+timedelta(minutes=1),identifier='new-glucose')]),'researcher')
    assert hypo(three)['notify'] and hypo(three)['reason']=='NEW_URGENT_EVIDENCE'
    assert len(engine.store.all('episode'))>=1
    for r in (one,two,three):assert svc.replay(r['id'])['matches']

def test_trend_baseline_and_quality(engine):
    ids=[add(engine,'base'+str(i),'physiology.vo2max',50,'mL/min/kg',timestamp=NOW-timedelta(days=10-i),phase='PRE_MISSION',device_id='vo2').id for i in range(3)]
    engine.build_baseline(BaselineRequest(id='personal',measurement_ids=ids,as_of=NOW-timedelta(days=7),minimum_observations=3,protocol_reference='SYNTHETIC_TEST'),'researcher')
    add(engine,'v1','physiology.vo2max',45,'mL/min/kg',timestamp=NOW-timedelta(days=2),device_id='vo2')
    add(engine,'v2','physiology.vo2max',40,'mL/min/kg',timestamp=NOW-timedelta(days=1),device_id='vo2')
    last=add(engine,'v3','physiology.vo2max',35,'mL/min/kg',device_id='vo2')
    svc=MonitoringService(engine);r=svc.run(request(measurements=[last],baseline_ids=['personal']),'researcher')
    indicator=r['domains'][0]['indicators'][0]
    assert indicator['baseline_comparison']['retention_percent']==70
    assert indicator['trend']['slope_per_day']==-5
    assert indicator['normative_finding_id']
    assert svc.replay(r['id'])['matches']
    bad=add(engine,'v4','physiology.vo2max',100,'mL/min/kg',device_id='vo2',timestamp=NOW+timedelta(minutes=1),reported_quality='INVALID')
    r2=svc.run(request(id='cycle2',previous_run_id='cycle1',as_of=NOW+timedelta(minutes=1),measurements=[bad],baseline_ids=['personal']),'researcher')
    assert r2['domains'][0]['indicators'][0]['value'] is None
    assert svc.replay(r2['id'])['matches']

def test_radiation_overlap_blocks_total(engine):
    a=add(engine,'dose1','radiation.interval_effective_dose',.1,'mSv',device_id='dosimeter',timestamp=NOW-timedelta(days=2),interval_end=NOW-timedelta(days=1),method='INTERVAL_TOTAL')
    b=add(engine,'dose2','radiation.interval_effective_dose',.2,'mSv',device_id='dosimeter',timestamp=NOW-timedelta(days=1),interval_end=NOW,method='INTERVAL_TOTAL')
    svc=MonitoringService(engine);r=svc.run(request(measurements=[a,b]),'researcher')
    assert r['domains'][2]['accumulated_dose']['effective_dose_mSv']==.3
    overlap=add(engine,'dose3','radiation.interval_effective_dose',.5,'mSv',device_id='dosimeter',timestamp=NOW-timedelta(hours=1),interval_end=NOW,method='INTERVAL_TOTAL')
    r=svc.run(request(id='cycle2',previous_run_id='cycle1',measurements=[overlap]),'researcher')
    assert r['domains'][2]['accumulated_dose']['effective_dose_mSv'] is None
    assert svc.replay(r['id'])['matches']

def test_predecessor_and_scope_rollback(engine):
    svc=MonitoringService(engine);svc.run(request(),'researcher')
    with pytest.raises(ValueError,match='PREDECESSOR'):svc.run(request(id='cycle2'),'researcher')
    assert len(engine.store.all('monitoring_run'))==1

def test_newer_missing_never_means_recovery(engine):
    svc=MonitoringService(engine);svc.run(request(observations=[obs('known_diabetes',True),obs('plasma_glucose_mg_dl',50)]),'researcher')
    out=svc.run(request(id='cycle2',previous_run_id='cycle1',as_of=NOW+timedelta(minutes=1),observations=[observation('plasma_glucose_mg_dl',None,timestamp=NOW+timedelta(minutes=1),identifier='missing',quality='NOT_MEASURED')]),'researcher')
    r=out['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert r['diagnostic_status'] not in ('CRITERIA_MET','CRITERIA_NOT_MET')
    assert all(engine.episode(e)['state']!='CLOSED' for e in out['episode_ids'].values())
    assert svc.replay(out['id'])['matches']

def test_monitoring_api_reader_scope_and_contract(tmp_path):
    from vigile.api import create_app
    from conftest import ROOT
    from vigile.store import digest
    tokens={'w'*32:'researcher','r'*32:{'id':'rag','role':'reader','subject_ids':['crew'],'mission_ids':['mission']},'x'*32:{'id':'other','role':'reader','subject_ids':['other'],'mission_ids':['mission']}}
    with TestClient(create_app(ROOT,tmp_path/'api.db',tokens=tokens)) as client:
        write={'Authorization':'Bearer '+'w'*32};read={'Authorization':'Bearer '+'r'*32};other={'Authorization':'Bearer '+'x'*32}
        assert client.post('/missions',headers=write,json={'id':'mission','phase':'IN_MISSION','gravity':'EARTH','environment':'HABITABLE_VOLUME','mode':'NOMINAL','synthetic':True}).status_code==201
        assert client.post('/profiles',headers=write,json={'id':'crew','mission_id':'mission','synthetic':True}).status_code==201
        body=request().model_dump(mode='json')
        assert client.post('/monitoring/cycles',headers=read,json=body).status_code==403
        response=client.post('/monitoring/cycles',headers=write,json=body)
        assert response.status_code==201,response.text
        payload=response.json();expected=payload.pop('output_hash');assert digest(payload)==expected
        assert client.get('/monitoring/cycles/cycle1',headers=other).status_code==403
        assert client.get('/monitoring/cycles/cycle1',headers=read).status_code==200
        assert client.get('/monitoring/cycles/cycle1/replay',headers=read).json()['matches']
        assert client.get('/monitoring/cycles?subject_id=crew&mission_id=mission',headers=read).status_code==200
        assert 'replay_records' not in client.get('/monitoring/cycles/cycle1',headers=read).json()
        schema=client.get('/openapi.json',headers=read).json()
        assert 'MonitoringResult' in schema['components']['schemas']
        assert client.get('/dashboard/subjects/crew?mission_id=mission',headers=read).json()['monitoring'][0]['id']=='cycle1'

@pytest.mark.parametrize('change',[{'quality':'INVALID'},{'method':'CGM'},{'unit':'mmHg'}])
def test_hypoglycemia_invalid_cannot_classify(engine,change):
    observations=[obs('known_diabetes',True),obs('capillary_glucose_mg_dl',50,method='VALIDATED_BLOOD_GLUCOSE_METER').model_copy(update=change)]
    r=MonitoringService(engine).run(request(observations=observations),'researcher')['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert r['diagnostic_status']!='CRITERIA_MET'
    assert 'capillary_glucose_mg_dl' in r['invalid_required']

def test_hypoglycemia_unknown_population_no_level(engine):
    r=MonitoringService(engine).run(request(population='UNKNOWN',observations=[obs('known_diabetes',True),obs('plasma_glucose_mg_dl',50)]),'researcher')['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert r['metadata']['hypoglycemia_level_minimum_supported'] is None
    assert r['urgency']=='URGENT'

def test_invalid_time_and_late_receipts(engine):
    svc=MonitoringService(engine);svc.run(request(),'researcher')
    late=add(engine,'late','sleep.duration',6,'h',timestamp=NOW-timedelta(days=2))
    future=add(engine,'future','sleep.duration',8,'h',timestamp=NOW+timedelta(days=2))
    r=svc.run(request(id='cycle2',previous_run_id='cycle1',measurements=[late,future]),'researcher')
    assert {'LATE_ARRIVAL_REANALYZED_NOT_CURRENT','FUTURE_TIMESTAMP'}<={e['state'] for e in r['events']}
    assert svc.replay(r['id'])['matches']

def test_all_three_scenarios(engine):
    from vigile.monitoring_demo import scenarios
    report=scenarios(engine)
    assert report['cycles']==15
    assert all(r['matches'] for r in report['replays'])

def test_atomic_rollback_after_new_measurement(engine):
    original=add(engine,'template','sleep.duration',7,'h')
    new=original.model_copy(update={'id':'not-persisted'})
    svc=MonitoringService(engine)
    with pytest.raises(KeyError):svc.run(request(measurements=[new],baseline_ids=['absent']),'researcher')
    with pytest.raises(KeyError):engine.measurement(new.id)
    assert not engine.store.all('monitoring_run')
    assert engine.store.verify()

def test_replay_tampered_output_blocked(engine,monkeypatch):
    svc=MonitoringService(engine);r=svc.run(request(),'researcher')
    stored=engine.store.get('monitoring_run',r['id']);stored['clinical_execution']='ALTERED'
    original=engine.store.get
    monkeypatch.setattr(engine.store,'get',lambda kind,identifier:stored if kind=='monitoring_run' and identifier==r['id'] else original(kind,identifier))
    with pytest.raises(ValueError,match='OUTPUT_HASH'):svc.replay(r['id'])

@pytest.mark.parametrize('unit,method,value',[('mg/dL','VALIDATED_BLOOD_GLUCOSE_METER',53),('mmol/L','VALIDATED_BLOOD_GLUCOSE_METER',2.9)])
def test_valid_capillary_alternative(engine,unit,method,value):
    r=MonitoringService(engine).run(request(observations=[obs('known_diabetes',True),obs('capillary_glucose_mg_dl',value,unit=unit,method=method)]),'researcher')['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert r['diagnostic_status']=='CRITERIA_MET'
    assert 'plasma_glucose_mg_dl' in r['optional_not_measured']
    assert not r['missing_required']

def test_stale_current_not_normal(engine):
    m=add(engine,'stale','physiology.spo2',99,'%',timestamp=NOW-timedelta(days=11))
    r=MonitoringService(engine).run(request(measurements=[m]),'researcher')
    indicator=next(i for d in r['domains'] for i in d['indicators'] if i['variable']=='physiology.spo2')
    assert indicator['state']=='STALE' and indicator['value'] is None

def test_radiation_context_mismatch_blocks_sum(engine):
    a=add(engine,'dose-a','radiation.interval_effective_dose',.1,'mSv',device_id='dose',timestamp=NOW-timedelta(days=2),interval_end=NOW-timedelta(days=1),method='INTERVAL_TOTAL')
    b=add(engine,'dose-b','radiation.interval_effective_dose',.2,'mSv',device_id='dose',timestamp=NOW-timedelta(days=1),interval_end=NOW,method='INTERVAL_TOTAL',protocol='different')
    r=MonitoringService(engine).run(request(measurements=[a,b]),'researcher')
    assert r['domains'][2]['accumulated_dose']['effective_dose_mSv'] is None

def test_unrelated_observation_does_not_repeat_urgent_event(engine):
    svc=MonitoringService(engine)
    svc.run(request(observations=[obs('known_diabetes',True),obs('plasma_glucose_mg_dl',50)]),'researcher')
    r=svc.run(request(id='cycle2',previous_run_id='cycle1',observations=[obs('recent_exercise',True)]),'researcher')
    assert not next(e for e in r['events'] if e['key']=='clinical:HYPOGLYCEMIA')['notify']

def test_all_hypoglycemia_alternatives_false(engine):
    data={'known_diabetes':True,'plasma_glucose_mg_dl':70,'capillary_glucose_mg_dl':70,'altered_mental_or_physical_status':False,'assistance_required_for_hypoglycemia':False,'hypoglycemia_event_clinically_attributed':False}
    observations=[obs(k,v,**({'method':'VALIDATED_BLOOD_GLUCOSE_METER'} if k=='capillary_glucose_mg_dl' else {})) for k,v in data.items()]
    r=MonitoringService(engine).run(request(observations=observations),'researcher')['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert r['diagnostic_status']=='CRITERIA_NOT_MET'
    assert r['metadata']['disease_excluded'] is False

def test_non_diabetic_low_glucose_retains_urgency_without_diagnosis(engine):
    r=MonitoringService(engine).run(request(observations=[obs('known_diabetes',False),obs('plasma_glucose_mg_dl',50)]),'researcher')['clinical_evaluations']['HYPOGLYCEMIA']['results']['HYPOGLYCEMIA']
    assert r['diagnostic_status']=='NOT_APPLICABLE' and r['urgency']=='URGENT'
    assert r['metadata']['hypoglycemia_level_minimum_supported'] is None
