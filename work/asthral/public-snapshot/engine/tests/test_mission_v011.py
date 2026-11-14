"""Synthetic integration regressions; assertions are not clinical validation."""
import json,secrets,socket
from datetime import datetime,timedelta
from pathlib import Path
import pytest,httpx
from fastapi.testclient import TestClient
from vigile.api import create_app
from vigile.mission_demo import execute,SUBJECTS,MID,START
from vigile.mission_frames import read_frame,capture_frame
from vigile.mission_context import MissionContextVersion,append_context
from vigile.conversational import ConversationalInference,validate_generated
from vigile.inference_failures import failure_trace
from vigile.local_assistant import ReaderClient
from vigile.longitudinal_assistant import answer_monitoring
from vigile.portal import create_portal
from vigile.store import digest
from conftest import ROOT
from test_portal import TestReader

@pytest.fixture(scope='module')
def mission(tmp_path_factory):
    folder=tmp_path_factory.mktemp('mission-v011');db=folder/'mission.sqlite3'
    writer,operator,reader,only_a=[secrets.token_urlsafe(32) for _ in range(4)]
    scope={'subject_ids':list(SUBJECTS),'mission_ids':[MID]}
    tokens={writer:'researcher',operator:{'id':'acquisition','role':'operator',**scope},reader:{'id':'reader','role':'reader',**scope},
            only_a:{'id':'reader-A','role':'reader','subject_ids':[SUBJECTS[0]],'mission_ids':[MID]}}
    with TestClient(create_app(ROOT,db,tokens)) as client:
        report=execute(client,writer,operator,42,verify_replays=False)
        yield client,report,reader,only_a,operator,writer,db,folder

def frame(mission,sid,day):
    c=mission[0];rid=sid+'-cycle-'+str(day).replace('.','p')
    return read_frame(c.app.state.engine,'frame-'+rid,sid,MID)

def indicator(data,var):
    return next(i for d in data['monitoring'][-1]['domains'] for i in d['indicators'] if i['variable']==var)

def test_historical_receipt_scope_and_phase(mission):
    early=frame(mission,SUBJECTS[0],14);later=frame(mission,SUBJECTS[0],21)
    late_ids={r['measurement']['id'] for r in later['measurements'] if datetime.fromisoformat(r['measurement']['timestamp'])==START+timedelta(days=11)}
    assert late_ids and not late_ids&{r['measurement']['id'] for r in early['measurements']}
    assert all(datetime.fromisoformat(r['measurement']['timestamp'])<=datetime.fromisoformat(early['historical_frame']['as_of']) for r in early['measurements'])
    assert frame(mission,SUBJECTS[0],-3)['mission']['phase']=='PRE_MISSION'
    assert early['mission']['gravity']=='MICROGRAVITY'
    assert frame(mission,SUBJECTS[0],47)['mission']['phase']=='POST_MISSION'
    assert len(early['baselines'])==3 and not frame(mission,SUBJECTS[0],-3)['baselines']
    assert all(r['measurement']['subject_id']==SUBJECTS[0] for r in early['measurements'])

def test_deterioration_is_descriptive_not_diagnosis(mission):
    a=indicator(frame(mission,SUBJECTS[0],35),'physiology.vo2max')
    b=indicator(frame(mission,SUBJECTS[1],35),'physiology.vo2max')
    assert a['baseline_comparison']['retention_percent']<b['baseline_comparison']['retention_percent']
    assert a['trend']['slope_per_day']<0
    assert all(e['diagnosis'] is None for e in frame(mission,SUBJECTS[0],35)['monitoring'][-1]['events'])

def test_sensor_failures_never_normal(mission):
    missing=indicator(frame(mission,SUBJECTS[0],14),'sleep.duration');assert missing['value'] is None
    data=frame(mission,SUBJECTS[0],21)
    for var in ('physiology.strength','sleep.duration','physiology.heart_rate','physiology.spo2'):
        i=indicator(data,var);assert i['value'] is None and i['state']!='DESCRIPTIVE_AVAILABLE'
    assert indicator(data,'sleep.duration')['state']=='CURRENT_MISSION_PHASE_MISMATCH'
    assert indicator(data,'physiology.heart_rate')['state']=='CONFLICTING_DATA'
    assert any(e['state']=='LATE_ARRIVAL_REANALYZED_NOT_CURRENT' for e in data['monitoring'][-1]['events'])

def test_acute_alternatives_protocol_and_reevaluation(mission):
    first=frame(mission,SUBJECTS[1],18)['monitoring'][-1]['clinical_evaluations']['DKA']
    after=frame(mission,SUBJECTS[1],18.1)['monitoring'][-1]['clinical_evaluations']['DKA']
    assert after['parent_id']==first['id']
    a,b=first['results']['DKA'],after['results']['DKA']
    assert a['diagnostic_status']==b['diagnostic_status']=='CRITERIA_MET'
    assert not a['missing_required'] and not a['invalid_required']
    assert {'bicarbonate_mmol_l','urine_ketones_plus'}<=set(a['optional_not_measured'])
    assert 'potassium_mmol_l' in a['required_for_protocol_safety'] and 'potassium_mmol_l' not in b['required_for_protocol_safety']
    assert a['protocol_status'].startswith('BLOCKED') and b['protocol_status'].startswith('BLOCKED')
    assert b['treatment_status']=='NOT_STARTED'
    assert frame(mission,SUBJECTS[1],18)['episodes'] and frame(mission,SUBJECTS[1],18)['followups']

def test_frame_tamper_wrong_scope_and_back_capture(mission):
    engine=mission[0].app.state.engine
    with pytest.raises(ValueError,match='FRAME_SCOPE_MISMATCH'):read_frame(engine,'frame-'+SUBJECTS[0]+'-cycle-14',SUBJECTS[1],MID)
    with pytest.raises(ValueError,match='CURRENT_RECEIPT'):capture_frame(mission[0].app,'backdated',SUBJECTS[0]+'-cycle-14')
    frame_record=engine.store.get('mission_frame','frame-'+SUBJECTS[0]+'-cycle-14')
    assert digest(frame_record['snapshot'])==frame_record['index']['snapshot_hash']

def test_context_cannot_rewrite_committed_history(mission):
    engine=mission[0].app.state.engine;base=engine.store.get('mission',MID)
    req=MissionContextVersion(id='rewrite',mission_id=MID,effective_at=START+timedelta(days=45),context=base)
    with pytest.raises(ValueError,match='COMMITTED_CONTEXT'):append_context(engine,req,'researcher')

def test_reader_acquisition_scope_and_privilege_denial(mission):
    c,report,reader,only_a,operator,writer,*_=mission
    h={'Authorization':'Bearer '+only_a}
    assert c.get('/dashboard/frames/'+SUBJECTS[1]+'?mission_id='+MID,headers=h).status_code==403
    assert c.get('/dashboard/subjects/'+SUBJECTS[0]+'?mission_id=foreign',headers=h).status_code==403
    assert c.get('/dashboard/subjects/'+SUBJECTS[0]+'?mission_id='+MID+'&frame_id=frame-'+SUBJECTS[1]+'-cycle-18',headers=h).status_code==403
    for token in (reader,operator):
        h={'Authorization':'Bearer '+token}
        assert c.post('/missions/'+MID+'/contexts',headers=h,json={'role':'clinician','mission_id':MID}).status_code==403
        assert c.post('/monitoring/cycles',headers=h,json=report['requests'][0]).status_code==403
    assert c.get('/dashboard/frames/'+SUBJECTS[0]+'?mission_id='+MID,headers={'Authorization':'Bearer '+reader}).status_code==200

def test_replays_and_audit_after_persistence(mission):
    c,report,reader,_,_,_,db,_=mission
    assert c.app.state.engine.store.verify()
    for sid,day in ((SUBJECTS[0],21),(SUBJECTS[1],18.1),(SUBJECTS[0],47)):
        assert c.app.state.monitoring.replay(sid+'-cycle-'+str(day).replace('.','p'))['matches']
    with TestClient(create_app(ROOT,db,{reader:{'id':'reader','role':'reader','subject_ids':list(SUBJECTS),'mission_ids':[MID]}})) as restarted:
        r=restarted.get('/dashboard/subjects/'+SUBJECTS[1]+'?mission_id='+MID+'&frame_id=frame-'+SUBJECTS[1]+'-cycle-18',headers={'Authorization':'Bearer '+reader})
        assert r.status_code==200 and r.json()==frame(mission,SUBJECTS[1],18)

def test_full_mission_same_seed_reproduces_semantics_offline(mission,tmp_path,monkeypatch):
    writer,operator=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
    tokens={writer:'researcher',operator:{'id':'acquisition','role':'operator','subject_ids':list(SUBJECTS),'mission_ids':[MID]}}
    with TestClient(create_app(ROOT,tmp_path/'repeat.sqlite3',tokens)) as client:
        # Windows asyncio creates a loopback self-pipe before the application runs.
        # Block every connect during the complete mission, after initializing the harness.
        with monkeypatch.context() as isolated:
            isolated.setattr(socket.socket,'connect',lambda *a:(_ for _ in ()).throw(AssertionError('NETWORK_FORBIDDEN')))
            repeated=execute(client,writer,operator,42,verify_replays=False)
        assert repeated['request_hash']==mission[1]['request_hash']
        assert repeated['semantic_hash']==mission[1]['semantic_hash']
        assert repeated['assistant']['generation_attempts']==0

@pytest.mark.parametrize('exc,category',[(ValueError('CLINICAL_CLAIM_REQUIRES_EXACT_ENGINE_TEXT'),'SAFETY_REJECTION'),(ValueError('SEMANTIC_GROUNDING_REJECTED'),'VERIFIER_REJECTION'),(ValueError('LLM_BUSY'),'SATURATION'),(ValueError('TRUNCATED_MODEL_RESPONSE'),'MODEL_OUTPUT'),(ValueError('SECRET_TOKEN_PATH'),'UNCLASSIFIED'),(httpx.ReadTimeout('secret'),'TIMEOUT'),(httpx.ConnectError('secret'),'TRANSPORT')])
def test_failure_taxonomy_no_exception_leak(exc,category):
    trace=failure_trace(exc);assert trace['category']==category and 'secret' not in json.dumps(trace).lower()

def test_generation_guard_not_relaxed_and_stage_recorded():
    model=ConversationalInference('http://127.0.0.1:8891','test',provider='ollama')
    model._complete=lambda *a:({'sentences':[{'text':'A clinical diagnosis is confirmed.','evidence_ids':['M1']}]},{})
    with pytest.raises(ValueError) as caught:model.explain('baseline values',[{'id':'M1','text':'baseline values 50','kind':'ENGINE','reference':{}}])
    assert failure_trace(caught.value)['stage']=='DETERMINISTIC_VALIDATION'
    assert failure_trace(caught.value)['category']=='SAFETY_REJECTION'

def test_modes_and_outage_do_not_mutate_engine(mission,monkeypatch):
    c,report,reader,*_=mission;bridge=TestReader(c,reader);rid=SUBJECTS[0]+'-cycle-35'
    model=ConversationalInference('http://127.0.0.1:8891','test',provider='ollama')
    monkeypatch.setattr(model,'status',lambda:{'available':False,'reason':'CONTROLLED_UNAVAILABLE_NO_RUNTIME_STOPPED'})
    monkeypatch.setattr(socket.socket,'connect',lambda *a:(_ for _ in ()).throw(AssertionError('NETWORK_FORBIDDEN')))
    original=c.app.state.engine.store.get('monitoring_run',rid)['output_hash']
    for mode in ('FULL','LOW_POWER','CRITICAL','FULL'):
        model.set_mode(mode);reply=answer_monitoring(bridge,model,rid,'What changed from baseline?')
        assert reply['generated']==[] and not reply['inference_attempted']
        assert c.app.state.engine.store.get('monitoring_run',rid)['output_hash']==original
    assert model.model_http_calls==0 and c.app.state.engine.store.verify()

@pytest.mark.parametrize('question,status',[('What tests could resolve the uncertainty?','DETERMINISTIC_TEST_RECOMMENDATIONS'),('Which documents support this information?','DOCUMENT_EXCERPTS_ONLY')])
def test_generic_questions_retrieve_existing_tests_and_documents(mission,question,status):
    c,_,reader,*_=mission
    class NoInference:
        mode='FULL'
        def status(self):return {'available':False}
        def explain(self,*a):raise AssertionError('MUST_USE_RECORDED_RESULTS')
    reply=answer_monitoring(TestReader(c,reader),NoInference(),SUBJECTS[1]+'-cycle-18',question)
    assert reply['status']==status and not reply['generated'] and not reply['inference_attempted']
    if status=='DOCUMENT_EXCERPTS_ONLY':
        assert reply['documents'] and all(b['kind']=='DOCUMENT' for b in reply['documents'])
    else:
        assert any('POTASSIUM' in b['text'] for b in reply['answer'])
        assert not any('TEST-VENOUS-PH-BICARB' in b['text'] and b['text'].startswith('Prueba recomendada') for b in reply['answer'])

def test_portal_historical_contract_and_context_reset(mission):
    c,report,reader,_,_,_,_,folder=mission
    code=secrets.token_urlsafe(32);path=folder/'access.txt';path.write_text(code)
    class Offline:
        mode='CRITICAL'
        def status(self):return {'available':False,'reason':'TEST_OFFLINE'}
    cfg={'access_code_file':str(path),'backend_url':'http://127.0.0.1:8897','reader_token_file':'UNUSED_IN_TEST'}
    with TestClient(create_portal(cfg,TestReader(c,reader),Offline()),base_url='http://127.0.0.1:8898') as p:
        h={'Origin':'http://127.0.0.1:8898'}
        assert p.post('/api/login',json={'code':code},headers=h).status_code==200
        idx=p.get('/api/frames/'+SUBJECTS[1]+'?mission_id='+MID);assert idx.status_code==200
        fid='frame-'+SUBJECTS[1]+'-cycle-18'
        data=p.get('/api/dashboard/'+SUBJECTS[1]+'?mission_id='+MID+'&frame_id='+fid).json()
        rid=data['historical_frame']['monitoring_id']
        reply=p.post('/api/assistant',headers=h,json={'monitoring_id':rid,'question':'What information is missing?','history':['another context'],'history_context_id':'wrong'})
        assert reply.status_code==200 and not reply.json()['history_used'] and not reply.json()['generated']
        assert reply.json()['context']['target_id']==rid
        assert p.post('/api/mode',json={'mode':'FULL','role':'clinician'},headers=h).status_code==422
        js=p.get('/assets/app.js').text
        assert 'mission-frame' in js and 'generation!==loadGeneration' in js and 'missionFrames.find' in js
