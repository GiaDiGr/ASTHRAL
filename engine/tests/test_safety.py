from datetime import timedelta
from copy import deepcopy
import sqlite3
import pytest
from pydantic import ValidationError
from vigile.models import BaselineRequest, TrendRequest, EpisodeRequest, TransitionRequest, FollowUpPlan, FollowUpReview
from vigile.quality import convert,Inconclusive
from vigile.store import Store
from vigile.rules import calculate
from conftest import NOW,add,evaluate,co2

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-float('inf')])
def test_nonfinite_ingestion_rejected(engine,value):
    with pytest.raises(ValidationError): add(engine,'bad','physiology.vo2max',value,'mL/min/kg')

@pytest.mark.parametrize('source,target',[('mGy','mSv'),('mGy-Eq','mSv'),('mSv/day','mSv'),('kg','kgf')])
def test_unsafe_units(source,target):
    with pytest.raises(Inconclusive): convert(200,source,target)

def test_safe_conversion():
    assert convert(34500,'Pa','kPa')==34.5
    assert convert(.6,'Sv','mSv')==600

@pytest.mark.parametrize('change,reason',[
 ({'reported_quality':'UNKNOWN'},'UNKNOWN'),({'reported_quality':'INVALID'},'INVALID'),
 ({'value':None},'MISSING'),({'timestamp':NOW+timedelta(seconds=1)},'FUTURE_TIMESTAMP'),
 ({'timestamp':NOW-timedelta(days=11)},'STALE'),({'phase':'POST_MISSION'},'PHASE_MISMATCH'),
 ({'variable':'physiology.strength'},'VARIABLE_MISMATCH')])
def test_quality_fail_closed(engine,change,reason):
    args=dict(variable='physiology.vo2max',value=40,unit='mL/min/kg');args.update(change)
    add(engine,'x',**args)
    out=evaluate(engine,'AER-001',{'vo2max_relative':'x'})
    assert out['result']=='INCONCLUSIVE' and out['reason']==reason

def test_operational_and_client_spoof_blocked(engine):
    add(engine,'x','physiology.vo2max',40,'mL/min/kg')
    out=evaluate(engine,'AER-001',{'vo2max_relative':'x'},mode='OPERATIONAL')
    assert out['result']=='REQUIRES_VALIDATION'
    for context in ({'data_quality_status':'ACCEPTABLE'},{'measurement_method':'DIRECT'},{'vo2max_relative':'40'}):
        assert evaluate(engine,'AER-001',{'vo2max_relative':'x'},context)['result']=='INCONCLUSIVE'

def test_baseline_build_use_and_insufficiency(engine):
    for i,value in enumerate([40,45,50]):
        add(engine,f'b{i}','physiology.vo2max',value,'mL/min/kg',phase='PRE_MISSION',timestamp=NOW-timedelta(days=30-i),device_id='dev')
    req=BaselineRequest(id='baseline',measurement_ids=['b0','b1','b2'],minimum_observations=3,protocol_reference='TEST',as_of=NOW)
    b=engine.build_baseline(req,'researcher')
    assert b['value']==45 and b['mad']==5
    add(engine,'current','physiology.vo2max',36,'mL/min/kg')
    out=evaluate(engine,'AER-003',{'premission_aerobic_capacity':'baseline','current_aerobic_capacity':'current'})
    assert out['result']=='REQUIREMENT_MET'
    with pytest.raises(Inconclusive): engine.build_baseline(req.model_copy(update={'id':'bad','minimum_observations':4}),'researcher')

@pytest.mark.parametrize('field,value',[('site','OTHER'),('method','QCT'),('protocol','another')])
def test_dxa_and_protocol_mismatch(engine,field,value):
    add(engine,'b','physiology.bmd',1,'g/cm2',site='TOTAL_HIP',phase='PRE_MISSION',timestamp=NOW-timedelta(days=30))
    kw={'site':'TOTAL_HIP',field:value}
    add(engine,'c','physiology.bmd',.95,'g/cm2',**kw)
    out=evaluate(engine,'BONE-001',{'premission_bmd':{'TOTAL_HIP':'b'},'current_bmd':{'TOTAL_HIP':'c'}})
    assert out['result']=='INCONCLUSIVE'

def test_trends_are_research(engine):
    for i,value in enumerate([1,2,3]): add(engine,f't{i}','physiology.strength',value,'N',timestamp=NOW-timedelta(days=2-i),device_id='d')
    out=engine.trend(TrendRequest(measurement_ids=['t0','t1','t2'],as_of=NOW,ewma_lambda=.5,cusum_target=1,cusum_allowance=.1),'researcher')
    assert out['slope_per_day']==1 and out['slope_standard_error']==0
    assert out['status']=='RESEARCH_ONLY' and out['diagnosis'] is None

def test_reproduction_idempotence_and_immutability(engine):
    add(engine,'x','physiology.vo2max',32.8,'mL/min/kg')
    first=evaluate(engine,'AER-001',{'vo2max_relative':'x'})
    second=evaluate(engine,'AER-001',{'vo2max_relative':'x'})
    assert first==second and len(engine.store.all('finding'))==1
    assert engine.reproduce(first['id'])['verified']
    with pytest.raises(sqlite3.IntegrityError): engine.store.db.execute('DELETE FROM audit')
    with pytest.raises(sqlite3.IntegrityError): engine.store.db.execute("UPDATE records SET payload='{}'")
    assert engine.store.verify()

def test_sqlite_persists_after_reopen(tmp_path):
    path=tmp_path/'persistent.db'; s=Store(path);s.put('x','one',{'value':1});s.close()
    s=Store(path); assert s.get('x','one')=={'value':1}; assert s.verify();s.close()

def test_corpus_and_coverage(registry):
    assert len(registry.list('conditions'))==44
    assert all(len(c['coverage_states'])==11 for c in registry.list('conditions'))
    assert registry.get('sources','S27')['source']=='OSD-198'
    assert any(i['id']=='EVID-001' for i in registry.issues)
    rule=registry.rule('VIGILE-AER-001');rule['thresholds'].clear()
    assert registry.rule('VIGILE-AER-001')['thresholds']

def test_workflow_and_followup(engine):
    engine.open_episode(EpisodeRequest(id='ep',subject_id='crew',mission_id='mission',condition_id='C001'),'researcher')
    tr=lambda state: TransitionRequest(target=state,note='Human review documentation')
    assert engine.transition('ep',tr('AUTHORIZED_ACTION'),'clinician')['result']=='BLOCKED_NO_AUTHORIZATION'
    engine.transition('ep',tr('ASSESSMENT'),'researcher')
    assert engine.transition('ep',tr('RECOVERY'),'researcher')['result']=='BLOCKED_NO_AUTHORIZATION'
    engine.transition('ep',tr('RECOVERY'),'clinician')
    engine.followup(FollowUpPlan(id='follow',episode_id='ep',due_at=NOW+timedelta(days=1),goal_description='Reassess function',protocol_reference='HUMAN_PLAN'),'clinician')
    add(engine,'x','physiology.vo2max',40,'mL/min/kg')
    out=engine.review_followup(FollowUpReview(plan_id='follow',measurement_ids=['x'],note='Review pending'),'clinician')
    assert out['recovery_status']=='HUMAN_ASSESSMENT_REQUIRED'
    engine.transition('ep',tr('FOLLOW_UP'),'clinician');engine.transition('ep',tr('CLOSED'),'clinician')
    with pytest.raises(ValueError): engine.transition('ep',tr('ASSESSMENT'),'clinician')

def test_eva_context_not_interchangeable(engine):
    add(engine,'x','physiology.vo2max',35,'mL/min/kg')
    assert evaluate(engine,'AER-002',{'vo2max_relative':'x'})['result']=='NOT_APPLICABLE'

def test_calibration_expired(engine):
    m=add(engine,'x','physiology.vo2max',40,'mL/min/kg',timestamp=NOW-timedelta(days=1100))
    assert evaluate(engine,'AER-001',{'vo2max_relative':'x'})['reason']=='INVALID_CALIBRATION'

def test_unknown_profile_and_empty_nutrition_do_not_pass(registry):
    r=registry.rule('VIGILE-MUS-001');x=deepcopy(r['test_cases'][0]['inputs']);x['applicable_mission_profiles']=[]
    assert calculate(r,x,{'mission_phase':'PRE_MISSION'})['result']=='INCONCLUSIVE'
    r=registry.rule('VIGILE-NUT-001');x=deepcopy(r['test_cases'][0]['inputs']);x['calculated_requirements']={}
    assert calculate(r,x,{'mission_phase':'IN_MISSION'})['result']=='INCONCLUSIVE'
