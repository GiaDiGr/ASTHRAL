from datetime import timedelta
import hashlib, sqlite3
import pytest
from fastapi.testclient import TestClient
from vigile import models as m
from vigile.api import create_app
from vigile.quality import Inconclusive, convert
from vigile.security import authenticate
from conftest import add, evaluate, NOW, ROOT

def baseline(e, **kw):
    for i,v in enumerate([10,12,14]):
        add(e,'b'+str(i),'physiology.strength',v,'N',phase='PRE_MISSION',timestamp=NOW-timedelta(days=6-i))
    return e.build_baseline(m.BaselineRequest(id='base',measurement_ids=['b2','b0','b1'],minimum_observations=3,protocol_reference='SYNTHETIC',as_of=NOW-timedelta(days=3),**kw),'researcher')

def test_baseline_order_and_expiry(engine):
    b=baseline(engine,valid_until=NOW)
    assert b['value']==12 and b['mad']==2 and b['input_ids']==['b0','b1','b2']
    assert b['version']==1 and b['snapshots'] and b['implementation_hash']
    engine.baseline_status('base',NOW)
    with pytest.raises(Inconclusive,match='EXPIRED'): engine.baseline_status('base',NOW+timedelta(seconds=1))

def test_baseline_withdrawal_temporal(engine):
    baseline(engine)
    engine.withdraw_baseline(m.BaselineWithdrawal(baseline_id='base',effective_at=NOW,reason='SYNTHETIC correction'),'researcher')
    engine.baseline_status('base',NOW-timedelta(seconds=1))
    with pytest.raises(Inconclusive,match='WITHDRAWN'): engine.baseline_status('base',NOW)

def test_baseline_revision(engine):
    baseline(engine)
    request=m.BaselineRequest(id='base2',measurement_ids=['b0','b1','b2'],minimum_observations=3,protocol_reference='SYNTHETIC',as_of=NOW,supersedes='base')
    assert engine.build_baseline(request,'researcher')['version']==2
    assert engine.store.get('baseline','base')['version']==1
    with pytest.raises(ValueError,match='REVISION_TIME'): engine.build_baseline(request.model_copy(update={'id':'base3','as_of':NOW-timedelta(days=3)}),'researcher')

def trend_request(**kw):
    return m.TrendRequest(measurement_ids=['t0','t1'],as_of=NOW,ewma_lambda=.5,cusum_target=12,cusum_allowance=0,**kw)

def test_reference_trends(engine):
    baseline(engine)
    add(engine,'t0','physiology.strength',14,'N',timestamp=NOW-timedelta(days=1))
    add(engine,'t1','physiology.strength',16,'N')
    out=engine.trend(trend_request(baseline_id='base',ewma_initial=12,cusum_decision_limit=3,max_gap_seconds=86400),'researcher')
    assert out['slope_per_day']==2
    assert out['baseline_comparison']['z']==2
    assert out['baseline_comparison']['absolute_change']==4
    assert out['trace'][0]['ewma']==13
    assert out['trace'][-1]['statistical_signal'] is True
    assert out['diagnosis'] is None
    with pytest.raises(Inconclusive,match='TEMPORAL_GAP'): engine.trend(trend_request(max_gap_seconds=3600),'researcher')

def test_historical_conflicts_block_baseline(engine):
    add(engine,'a','physiology.strength',10,'N',phase='PRE_MISSION')
    add(engine,'b','physiology.strength',20,'N',phase='PRE_MISSION')
    req=m.BaselineRequest(id='base',measurement_ids=['a'],minimum_observations=1,protocol_reference='SYNTHETIC',as_of=NOW)
    with pytest.raises(Inconclusive,match='CONFLICTING_DATA'): engine.build_baseline(req,'researcher')

def test_quality_missing_and_no_imputation(engine):
    add(engine,'missing','physiology.strength',None,'N',reported_quality='NOT_MEASURED')
    out=engine.quality_report(m.QualityRequest(measurement_ids=['missing','absent'],as_of=NOW),'researcher')
    assert out['result']=='INCONCLUSIVE' and out['no_imputation']
    assert out['assessments'][1]['state']=='MISSING_REFERENCE'

@pytest.mark.parametrize('state',['normal','conflict','invalid','absent','operational'])
def test_full_replay(engine,state):
    if state!='absent': add(engine,'a','physiology.vo2max',32.8,'mL/min/kg',reported_quality='INVALID' if state=='invalid' else 'ACCEPTABLE')
    if state=='conflict': add(engine,'b','physiology.vo2max',50,'mL/min/kg')
    f=evaluate(engine,'AER-001',{'vo2max_relative':'a'},mode='OPERATIONAL' if state=='operational' else 'SIMULATION')
    before=engine.store.checkpoint()
    replay=engine.reproduce(f['id'])
    assert replay['verified'] and replay['replay_scope']=='FULL_INPUT_GATES_AND_COMPARATOR_REEXECUTED'
    assert engine.store.checkpoint()==before
    add(engine,'later','physiology.vo2max',60,'mL/min/kg')
    assert engine.reproduce(f['id'])['verified']

def test_coverage(engine):
    coverage=engine.clinical_coverage()
    assert len(coverage)==44
    assert all(len(c['stages'])==11 for c in coverage)
    assert all(s['clinical_execution']=='BLOCKED' for c in coverage for s in c['stages'])

def test_evidence_versions_do_not_enable_rules(engine):
    req=m.EvidenceRevision(source_id='S01',version='test-1',locator='SYNTHETIC',document_sha256='a'*64,status='REVIEWED_METADATA_ONLY',note='Synthetic metadata')
    first=engine.register_evidence_revision(req,'researcher')
    assert first['clinical_activation']=='BLOCKED'
    with pytest.raises(ValueError,match='ALREADY_EXISTS'): engine.register_evidence_revision(req,'researcher')
    assert engine.evidence_for_rule('VIGILE-AER-001')['clinical_activation']=='BLOCKED'

def test_stale_episode_and_note_transaction(engine):
    engine.open_episode(m.EpisodeRequest(id='ep',subject_id='crew',mission_id='mission',condition_id='C001'),'researcher')
    engine.transition('ep',m.TransitionRequest(target='ASSESSMENT',note='Synthetic',expected_state='MONITORING'),'researcher')
    with pytest.raises(ValueError,match='STALE'): engine.transition('ep',m.TransitionRequest(target='FOLLOW_UP',note='Synthetic',expected_state='MONITORING'),'clinician')
    req=m.ClinicalNote(id='note',episode_id='ep',observed_at=NOW,kind='OBSERVATION',text='SYNTHETIC_PRIVATE_TEXT')
    n=engine.note(req,'clinician'); assert engine.reproduce(n['finding_id'])['verified']
    checkpoint=engine.store.checkpoint()
    with pytest.raises(sqlite3.IntegrityError): engine.note(req.model_copy(update={'text':'OTHER_SYNTHETIC'}),'clinician')
    assert engine.store.checkpoint()==checkpoint and len(engine.store.all('finding'))==1

def test_followup_due(engine):
    engine.open_episode(m.EpisodeRequest(id='ep',subject_id='crew',mission_id='mission',condition_id='C001'),'researcher')
    engine.followup(m.FollowUpPlan(id='plan',episode_id='ep',due_at=NOW,goal_description='Synthetic',protocol_reference='Synthetic'),'clinician')
    assert engine.followup_status('plan',NOW)['status']=='SCHEDULED'
    assert engine.followup_status('plan',NOW+timedelta(days=1))['status']=='OVERDUE'

@pytest.mark.parametrize('interval,expected',[(30,'COMPATIBLE_WITH_DECLARED_POLICY'),(61,'POLICY_CONFLICT')])
def test_resource_contract(engine,interval,expected):
    add(engine,'a','physiology.strength',10,'N')
    out=engine.assess_resources(m.ResourceAssessment(mode='LOW_POWER',proposed_interval_seconds=interval,required_interval_seconds=60,policy_reference='SYNTHETIC',measurement_ids=['a'],as_of=NOW),'researcher')
    assert out['result']==expected and not out['rule_thresholds_changed'] and not out['measurements_resampled']

@pytest.mark.parametrize('unit',['ms','mV','mL/L','um','degC','cm/s','dBA'])
def test_additional_scalar_units(unit): assert convert(1,unit,unit)==1

TOKEN='synthetic-reader-credential-long-enough'
def principal(**kw): return dict(id='rag-client',role='reader',subject_ids=['crew'],mission_ids=['mission'],**kw)

def test_auth_hash_expiry_and_disabled():
    hashed='sha256:'+hashlib.sha256(TOKEN.encode()).hexdigest()
    assert authenticate(TOKEN,{hashed:principal()}).id=='rag-client'
    assert authenticate(TOKEN,{hashed:principal(disabled=True)}) is None
    assert authenticate(TOKEN,{hashed:principal(expires_at=NOW.isoformat())}) is None
    assert authenticate('short',{'short':'researcher'}) is None

def test_reader_scope_and_minimization(tmp_path):
    tokens={TOKEN:principal(),'different-subject-credential-long':dict(id='other',role='reader',subject_ids=['other'],mission_ids=['mission'])}
    app=create_app(ROOT,tmp_path/'api.sqlite',tokens)
    e=app.state.engine
    e.store.put('finding','f',dict(id='f',subject_id='crew',mission_id='mission',kind='HUMAN_REPORTED_FINDING',result='FINDING',condition_ids=['C001'],note_id='private',text='SYNTHETIC_SECRET'))
    with TestClient(app) as c:
        headers={'Authorization':'Bearer '+TOKEN}
        response=c.get('/rag/findings/f',headers=headers)
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert 'SYNTHETIC_SECRET' not in response.text and 'subject_id' not in response.text
        assert c.get('/findings/f',headers=headers).status_code==403
        assert c.get('/measurements?subject_id=crew&mission_id=mission',headers=headers).status_code==403
        assert c.get('/rag/findings/f',headers={'Authorization':'Bearer different-subject-credential-long'}).status_code==403
        assert c.post('/evidence/revisions',json={},headers=headers).status_code==403
        assert len(c.get('/capabilities/coverage',headers=headers).json())==44

def test_audit_detects_deleted_record(engine):
    engine.store.db.execute('DROP TRIGGER records_no_delete')
    engine.store.db.execute("DELETE FROM records WHERE kind='profile'")
    assert not engine.store.verify()

def test_new_api_contracts_and_validation(tmp_path):
    token='synthetic-researcher-token-long-enough'
    app=create_app(ROOT,tmp_path/'contracts.sqlite',{token:'researcher'})
    with TestClient(app) as c:
        headers={'Authorization':'Bearer '+token}
        assert c.post('/quality/assessments',headers=headers,json={'measurement_ids':['absent'],'as_of':NOW.isoformat()}).json()['result']=='INCONCLUSIVE'
        assert c.get('/evidence/rules/VIGILE-AER-001',headers=headers).json()['clinical_activation']=='BLOCKED'
        req=dict(source_id='S01',version='test',locator='Synthetic',document_sha256='a'*64,status='REVIEWED_METADATA_ONLY',note='Synthetic')
        assert c.post('/evidence/revisions',headers=headers,json=req).status_code==201
        assert c.post('/evidence/revisions',headers=headers,json=req).status_code==422
        response=c.post('/profiles',headers=headers,json={'id':'SECRET_SYNTHETIC_VALUE','bad':'SECRET_SYNTHETIC_VALUE'})
        assert response.status_code==422 and 'SECRET_SYNTHETIC_VALUE' not in response.text
        assert c.get('/audit/checkpoint',headers=headers).json()['sequence']>0
        spec=c.get('/openapi.json',headers=headers).json()
        assert spec['paths']['/evaluations']['post']['security']==[{'BearerAuth':[]}]
        assert spec['paths']['/health']['get']['security']==[]

def test_environment_credential_revocation(tmp_path,monkeypatch):
    import json
    monkeypatch.setenv('VIGILE_TOKENS',json.dumps({TOKEN:'reader'}))
    with TestClient(create_app(ROOT,tmp_path/'revoked.sqlite')) as c:
        headers={'Authorization':'Bearer '+TOKEN}
        assert c.get('/rules',headers=headers).status_code==200
        monkeypatch.setenv('VIGILE_TOKENS','{}')
        assert c.get('/rules',headers=headers).status_code==401

@pytest.mark.parametrize('interaction',['MSI05','MSI10'])
def test_unrepresented_multisystem_evidence_is_blocked(engine,interaction):
    out=engine.multisystem(m.MultisystemRequest(interaction_id=interaction,finding_ids=['a','b'],max_separation_seconds=60,policy_reference='Synthetic'),'researcher')
    assert out['result']=='INCONCLUSIVE' and out['clinical_execution']=='BLOCKED'

def test_resource_missing_quality_is_inconclusive(engine):
    out=engine.assess_resources(m.ResourceAssessment(mode='LOW_POWER',proposed_interval_seconds=30,required_interval_seconds=60,policy_reference='Synthetic',measurement_ids=['absent'],as_of=NOW),'researcher')
    assert out['result']=='INCONCLUSIVE'

def test_credential_provision_hashes_only(tmp_path):
    import json
    from vigile.credentials import provision
    provision(tmp_path)
    server=json.loads((tmp_path/'tokens.json').read_text())
    clients=json.loads((tmp_path/'client-credentials.json').read_text())
    assert all(k.startswith('sha256:') for k in server)
    assert all(token not in (tmp_path/'tokens.json').read_text() for token in clients)
    for token,role in clients.items(): assert authenticate(token,server).role==role
    provision(tmp_path)
    assert json.loads((tmp_path/'tokens.json').read_text())==server
