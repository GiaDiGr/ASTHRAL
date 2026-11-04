"""Synthetic v1.0.1 management regressions; no dose/authorization execution."""
from copy import deepcopy
from datetime import timedelta
import hashlib,json
from pathlib import Path
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from vigile.management import MedicalResource,InventoryVersion,ManagementRecord,append_inventory,inventory_snapshot,resource_check,append_management_record
from vigile.models import EpisodeRequest,FollowUpPlan,MissionContext,AstronautProfile
from vigile.clinical_models import ClinicalRequest
from vigile.clinical_engine import ClinicalService
from vigile.clinical_simulator import AS_OF,observation
from vigile.api import create_app
from test_clinical import clinical,req
from conftest import ROOT
T=AS_OF
DATA={'known_diabetes':True,'plasma_glucose_mg_dl':180,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22}

def resource(identifier='insulin_inventory',**kw):
 raw=dict(id=identifier,kind='MEDICATION' if identifier in ('insulin_inventory','epinephrine_inventory') else 'CAPABILITY',label='FICTIONAL_RESOURCE_NOT_NASA',quantity=2,unit='synthetic-unit',availability='AVAILABLE',verification='VERIFIED',verified_at=T-timedelta(hours=2),expires_at=T+timedelta(days=1),storage_status='COMPLIANT',integrity_status='INTACT',requires_cold_chain=False,updated_at=T-timedelta(hours=1),source='SYNTHETIC_TEST_MANIFEST',responsible='fictional-operator')
 raw.update(kw);return MedicalResource(**raw)
def version(resources,**kw):
 raw=dict(id='inventory-1',mission_id='clinical-earth',version=1,effective_at=T-timedelta(hours=1),updated_at=T-timedelta(hours=1),source='SYNTHETIC_TEST',responsible='fictional-operator',resources=resources);raw.update(kw);return InventoryVersion(**raw)
def populate(service,**changes):
 names=service.knowledge.protocols['PROT-DKA-ADULT-2024']['required_resources']
 rows=[resource(name,**changes.get(name,{})) for name in names];return append_inventory(service.engine,version(rows),'researcher')
def evaluate(service,data=None,condition='DKA',**kw):
 return service.evaluate(req(condition,DATA if data is None else data,**kw),'researcher')
def view(out,condition='DKA'):return out['management'][condition]
def checksnap(rows):return {'policy':'MISSION_INVENTORY','as_of':T.isoformat(),'resources':[r.model_dump(mode='json') for r in rows]}

@pytest.mark.parametrize('change,expected',[
 ({},'RESOURCE_AVAILABLE'),({'availability':'UNKNOWN'},'RESOURCE_UNVERIFIED'),({'availability':'UNAVAILABLE'},'RESOURCE_UNAVAILABLE'),({'verification':'UNVERIFIED'},'RESOURCE_UNVERIFIED'),({'verified_at':None},'RESOURCE_UNVERIFIED'),({'expires_at':None},'RESOURCE_UNVERIFIED'),({'expires_at':T},'RESOURCE_UNAVAILABLE'),({'quantity':0},'RESOURCE_UNAVAILABLE'),({'quantity':None},'RESOURCE_UNVERIFIED'),({'integrity_status':'UNKNOWN'},'RESOURCE_UNVERIFIED'),({'integrity_status':'COMPROMISED'},'RESOURCE_UNAVAILABLE'),({'storage_status':'UNKNOWN'},'RESOURCE_UNVERIFIED'),({'storage_status':'NONCOMPLIANT'},'RESOURCE_UNAVAILABLE'),({'requires_cold_chain':None},'RESOURCE_UNVERIFIED'),({'requires_cold_chain':True,'cold_chain_status':'UNKNOWN'},'RESOURCE_UNVERIFIED'),({'requires_cold_chain':True,'cold_chain_status':'NONCOMPLIANT'},'RESOURCE_UNAVAILABLE'),({'requires_cold_chain':True,'cold_chain_status':'COMPLIANT'},'RESOURCE_AVAILABLE'),({'kind':'CAPABILITY','expires_at':None},'RESOURCE_UNVERIFIED')],ids=lambda x:str(x) if isinstance(x,str) else None)
def test_resource_states(change,expected):assert resource_check(checksnap([resource(**change)]),'insulin_inventory')['status']==expected

def test_absent_and_legacy_declarations_are_not_verified():
 assert resource_check(checksnap([]),'insulin_inventory')['reason']=='ABSENT_FROM_MISSION_MANIFEST'
 s={'policy':'DECLARED_R2','declared_flags':{'a':True,'b':False}}
 assert resource_check(s,'a')['status']=='RESOURCE_UNVERIFIED' and resource_check(s,'b')['status']=='RESOURCE_UNAVAILABLE' and resource_check(s,'c')['reason']=='NOT_DECLARED'

@pytest.mark.parametrize('change',[{'quantity':float('nan')},{'quantity':True},{'quantity':-1},{'quantity':2,'unit':None},{'synthetic':False}])
def test_invalid_resource_contract(change):
 with pytest.raises(ValidationError):resource(**change)

def test_dka_intervention_specific_safety_and_diagnostic_invariance(clinical):
 populate(clinical);a=evaluate(clinical,resource_policy='MISSION_INVENTORY')
 r=a['results']['DKA'];assert r['diagnostic_status']=='CRITERIA_MET' and r['urgency']=='EMERGENCY' and not r['missing_required']
 rows=view(a)['interventions'];insulin=[r for r in rows if 'INSULIN' in r['title']];fluids=next(r for r in rows if r['kind']=='CAPABILITY_REVIEW')
 assert all('BLOCKED_MISSING_DATA:POTASSIUM' in r['safety_restrictions'] for r in insulin) and not fluids['safety_restrictions']
 assert all(r['resource_status']=='RESOURCE_AVAILABLE' and r['authorization']=='AUTHORIZATION_REQUIRED' and not r['execution_enabled'] and not r['intervention_indication_decided'] for r in rows)
 assert clinical.replay(a['id'])['matches']
 b=evaluate(clinical,{**DATA,'potassium_mmol_l':3.5},resource_policy='MISSION_INVENTORY')
 assert b['results']['DKA']['protocol_status']=='BLOCKED_CONTRAINDICATION'
 assert a['results']['DKA']['diagnostic_status']==b['results']['DKA']['diagnostic_status']
 c=evaluate(clinical,{**DATA,'potassium_mmol_l':4},resource_policy='MISSION_INVENTORY')
 assert c['results']['DKA']['protocol_status']=='BLOCKED_AUTHORIZATION'
 assert c['results']['DKA']['treatment_status']=='NOT_STARTED'

def test_inventory_absent_preserves_emergency(clinical):
 out=evaluate(clinical,resource_policy='MISSION_INVENTORY');assert out['urgency']=='EMERGENCY'
 assert view(out)['resource_snapshot']['inventory_id'] is None
 assert all(r['resource_status']=='RESOURCE_UNVERIFIED' for r in view(out)['interventions'])

def test_versioning_future_exclusion_and_frozen_replay(clinical):
 populate(clinical);out=evaluate(clinical,{**DATA,'potassium_mmol_l':4},resource_policy='MISSION_INVENTORY')
 changed=version([resource('insulin_inventory',availability='UNAVAILABLE')],id='inventory-2',version=2,supersedes='inventory-1',effective_at=T+timedelta(hours=2),updated_at=T+timedelta(hours=2))
 append_inventory(clinical.engine,changed,'researcher')
 assert inventory_snapshot(clinical.store,'clinical-earth',T)['inventory_version']==1
 assert inventory_snapshot(clinical.store,'clinical-earth',T+timedelta(hours=3))['inventory_version']==2
 assert view(out)['resource_snapshot']['inventory_version']==1 and clinical.replay(out['id'])['matches']
 later=clinical.evaluate(req(data={**DATA,'potassium_mmol_l':4},resource_policy='MISSION_INVENTORY').model_copy(update={'as_of':T+timedelta(hours=3)}),'researcher')
 assert later['results']['DKA']['protocol_status']=='BLOCKED_RESOURCE'
 assert view(later)['resource_snapshot']['inventory_version']==2
 with pytest.raises(ValueError,match='COMMITTED|TIME'):
  append_inventory(clinical.engine,changed.model_copy(update={'id':'bad','version':3,'supersedes':'inventory-2','effective_at':T,'updated_at':T}),'researcher')

def test_inventory_cannot_rewrite_committed_or_wrong_lineage(clinical):
 evaluate(clinical)
 with pytest.raises(ValueError,match='COMMITTED'):append_inventory(clinical.engine,version([]),'researcher')
 with pytest.raises(ValueError,match='LINEAGE'):append_inventory(clinical.engine,version([],version=2),'researcher')

def test_inventory_other_mission_not_used(clinical):
 populate(clinical)
 assert inventory_snapshot(clinical.store,'mission',T)['inventory_id'] is None
 with pytest.raises(ValidationError):req(data=DATA,resource_policy='MISSION_INVENTORY',resources={'insulin_inventory':True})

def test_anaphylaxis_suspected_emergency_is_not_confirmed(clinical):
 out=evaluate(clinical,{'known_or_highly_probable_allergen':True,'respiratory_compromise':True},'ANAPHYLAXIS',resource_policy='MISSION_INVENTORY')
 m=view(out,'ANAPHYLAXIS');assert m['urgency']=='EMERGENCY' and m['diagnostic_status']!='CRITERIA_MET' and m['urgent_suspicion_without_met_criteria']
 assert all(r['authorization']=='AUTHORIZATION_REQUIRED' for r in m['interventions'])

@pytest.mark.parametrize('swallow,quality,expected',[(False,'VALID','ORAL_ROUTE_NOT_SUPPORTED'),(True,'VALID','SWALLOWING_DECLARED_TRUE'),(None,'NOT_MEASURED','SWALLOWING_ABILITY_UNKNOWN'),(True,'INVALID','SWALLOWING_ABILITY_UNKNOWN')])
def test_hypo_oral_context_is_not_new_treatment(clinical,swallow,quality,expected):
 request=req('HYPOGLYCEMIA',{'known_diabetes':True,'plasma_glucose_mg_dl':60})
 request=request.model_copy(update={'observations':request.observations+[observation('can_swallow_safely',swallow,quality=quality)]})
 out=clinical.evaluate(request,'researcher');rows=view(out,'HYPOGLYCEMIA')['interventions']
 assert any(c.startswith(expected) for c in rows[0]['conditions'])
 assert all(r['kind']=='DOCUMENTED_REVIEW' and not r['execution_enabled'] for r in rows)

@pytest.mark.parametrize('condition',['POTS','ORTHOSTATIC_HYPOTENSION'])
def test_gravity_limits_preserved(clinical,condition):
 request=req(condition).model_copy(update={'subject_id':'crew','mission_id':'mission'})
 out=clinical.evaluate(request,'researcher');assert out['results'][condition]['diagnostic_status']=='NOT_APPLICABLE'
 assert all(i['applicability_status']=='NOT_APPLICABLE' for i in view(out,condition)['interventions'])

def test_legacy_flags_keep_meaning_no_inventory_override(clinical):
 resources={r:True for r in clinical.knowledge.protocols['PROT-DKA-ADULT-2024']['required_resources']}
 out=evaluate(clinical,{**DATA,'potassium_mmol_l':4},resources=resources)
 assert out['results']['DKA']['protocol_status']=='BLOCKED_AUTHORIZATION'
 assert view(out)['resource_snapshot']['policy']=='DECLARED_R2'
 assert all(i['resource_status']=='RESOURCE_UNVERIFIED' for i in view(out)['interventions'])
 assert clinical.replay(out['id'])['matches']

def record_setup(clinical):
 out=evaluate(clinical);clinical.engine.open_episode(EpisodeRequest(id='episode',subject_id='clinical-crew',mission_id='clinical-earth',condition_id='DKA'),'researcher')
 return out,ManagementRecord(id='reported-1',episode_id='episode',evaluation_id=out['id'],intervention_id=view(out)['interventions'][0]['id'],status='HUMAN_REPORTED_PERFORMED',occurred_at=T+timedelta(minutes=1),recorded_at=T+timedelta(minutes=2),source='SYNTHETIC_OPERATOR_REPORT',reported_authority='CLAIMED_NOT_VERIFIED',note='Fictional report; not evidence of administration by VIGILE')

def test_human_record_is_not_authorization_execution_or_efficacy(clinical):
 out,entry=record_setup(clinical);payload=append_management_record(clinical.engine,entry,'operator')
 assert not any(payload[k] for k in ('execution_by_vigile','authorization_by_vigile','efficacy_verified'))
 assert clinical.store.get('clinical_evaluation',out['id'])['treatment_status']=='NOT_STARTED' and clinical.replay(out['id'])['matches']
 with pytest.raises(ValidationError):ManagementRecord.model_validate({**entry.model_dump(mode='json'),'authority_verification':'VERIFIED'})
 with pytest.raises(ValueError,match='INTERVENTION'):append_management_record(clinical.engine,entry.model_copy(update={'id':'bad','intervention_id':'invented'}),'clinician')

@pytest.fixture
def api_context(tmp_path):
 mapping={'writer'*8:'researcher','reader'*8:{'id':'r','role':'reader','subject_ids':['a'],'mission_ids':['m']},'operator'*8:{'id':'o','role':'operator','subject_ids':['a'],'mission_ids':['m']},'outsider'*8:{'id':'x','role':'researcher','subject_ids':['b'],'mission_ids':['other']}}
 with TestClient(create_app(ROOT,tmp_path/'isolated.sqlite3',mapping)) as c:
  e=c.app.state.engine
  e.register('mission',MissionContext(id='m',phase='PRE_MISSION',gravity='EARTH',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True),'researcher')
  e.register('profile',AstronautProfile(id='a',mission_id='m',synthetic=True),'researcher')
  yield c,e

def test_api_inventory_permissions_and_scope(api_context):
 c,e=api_context;body=version([resource()]).model_copy(update={'mission_id':'m'}).model_dump(mode='json');path='/missions/m/medical-inventory'
 for token in ('reader','operator','outsider'):assert c.post(path,json=body,headers={'Authorization':'Bearer '+token*8}).status_code==403
 assert c.post(path,json=body,headers={'Authorization':'Bearer '+('writer'*8)}).status_code==201
 assert c.get(path,params={'as_of':T.isoformat()},headers={'Authorization':'Bearer '+('reader'*8)}).status_code==200
 assert c.get(path,params={'as_of':T.isoformat()},headers={'Authorization':'Bearer '+('outsider'*8)}).status_code==403

def test_api_records_scope_and_no_authority_escalation(api_context):
 c,e=api_context;request=req(data=DATA).model_copy(update={'subject_id':'a','mission_id':'m'})
 out=c.app.state.clinical.evaluate(request,'researcher');e.open_episode(EpisodeRequest(id='ep',subject_id='a',mission_id='m',condition_id='DKA'),'researcher')
 body=ManagementRecord(id='r1',episode_id='ep',evaluation_id=out['id'],intervention_id=view(out)['interventions'][0]['id'],status='REVIEW_PENDING',occurred_at=T,recorded_at=T,source='synthetic',reported_authority='none',note='synthetic').model_dump(mode='json')
 for token in ('reader','outsider'):assert c.post('/clinical/management-records',json=body,headers={'Authorization':'Bearer '+token*8}).status_code==403
 assert c.post('/clinical/management-records',json=body,headers={'Authorization':'Bearer '+('operator'*8)}).status_code==201
 assert c.get('/clinical/evaluations/'+out['id']+'/management',headers={'Authorization':'Bearer '+('reader'*8)}).status_code==200
 path='/clinical/evaluations/'+out['id']+'/management-records'
 assert c.get(path,params={'as_of':(T-timedelta(seconds=1)).isoformat()},headers={'Authorization':'Bearer '+('reader'*8)}).json()==[]
 assert len(c.get(path,params={'as_of':T.isoformat()},headers={'Authorization':'Bearer '+('reader'*8)}).json())==1
 assert c.get(path,params={'as_of':T.isoformat()},headers={'Authorization':'Bearer '+('outsider'*8)}).status_code==403
 assert e.store.verify()

def test_knowledge_not_modified_and_countermeasures_are_documentary(registry):
 from vigile.clinical_knowledge import ClinicalKnowledge
 from vigile.management import countermeasure_documents
 assert ClinicalKnowledge().hash=='b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e'
 rows=countermeasure_documents(registry);assert len(rows)==8 and all(not r['execution_enabled'] and r['condition_id']!='C009' for r in rows)

def test_management_compute_never_needs_network(clinical,monkeypatch):
 import socket
 monkeypatch.setattr(socket.socket,'connect',lambda *a:pytest.fail('No network permitted'))
 out=evaluate(clinical,resource_policy='MISSION_INVENTORY');assert clinical.replay(out['id'])['matches']

def test_monitoring_freezes_inventory_and_replays(clinical):
 from vigile.monitoring import MonitoringService
 from vigile.monitoring_models import MonitoringRequest
 populate(clinical)
 request=MonitoringRequest(id='inventory-monitoring',subject_id='clinical-crew',mission_id='clinical-earth',resource_policy='MISSION_INVENTORY',as_of=T,history_start=T-timedelta(days=1),clinical_window_start=T-timedelta(hours=2),clinical_context_id='synthetic-context',policy_reference='SYNTHETIC_ONLY',population='NONPREGNANT_ADULT',age_years=30,observations=[observation(k,v) for k,v in DATA.items()])
 service=MonitoringService(clinical.engine);out=service.run(request,'researcher')
 assert out['clinical_evaluations']['DKA']['management']['DKA']['resource_snapshot']['inventory_version']==1
 assert service.replay(out['id'])['matches']


def test_cross_astronaut_management_record_rejected(clinical):
 out,entry=record_setup(clinical)
 clinical.engine.register('profile',AstronautProfile(id='second',mission_id='clinical-earth',synthetic=True),'researcher')
 clinical.engine.open_episode(EpisodeRequest(id='other-episode',subject_id='second',mission_id='clinical-earth',condition_id='DKA'),'researcher')
 with pytest.raises(ValueError,match='SCOPE'):append_management_record(clinical.engine,entry.model_copy(update={'episode_id':'other-episode'}),'clinician')


def test_legacy_clinical_record_is_not_reinterpreted(api_context):
 c,e=api_context;out=c.app.state.clinical.evaluate(req(data=DATA).model_copy(update={'subject_id':'a','mission_id':'m'}),'researcher')
 raw=e.store.get('clinical_evaluation',out['id']);raw.pop('management');raw['snapshot'].pop('resource_snapshot');raw['id']='legacy-clinical';raw['implementation_hash']='archived-r2-required';e.store.put('clinical_evaluation','legacy-clinical',raw)
 h={'Authorization':'Bearer '+('reader'*8)}
 r=c.get('/clinical/evaluations/legacy-clinical',headers=h);assert r.status_code==200 and 'management' not in r.json()
 r=c.get('/clinical/evaluations/legacy-clinical/management',headers=h);assert r.json()['legacy_record'] and r.json()['management'] is None


def test_hypo_future_swallowing_data_not_used(clinical):
 request=req('HYPOGLYCEMIA',{'known_diabetes':True,'plasma_glucose_mg_dl':60})
 request=request.model_copy(update={'observations':request.observations+[observation('can_swallow_safely',True,timestamp=T+timedelta(hours=1))]})
 out=clinical.evaluate(request,'researcher');assert 'SWALLOWING_ABILITY_UNKNOWN' in view(out,'HYPOGLYCEMIA')['interventions'][0]['conditions']


def test_non_synthetic_inventory_and_context_rejected(clinical):
 e=clinical.engine;e.register('mission',MissionContext(id='real-context',phase='PRE_MISSION',gravity='EARTH',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=False),'researcher');e.register('profile',AstronautProfile(id='real-profile',mission_id='real-context',synthetic=False),'researcher')
 with pytest.raises(ValueError,match='SYNTHETIC'):append_inventory(e,version([]).model_copy(update={'mission_id':'real-context'}),'clinician')
 with pytest.raises(ValueError,match='SYNTHETIC'):clinical.evaluate(req(data=DATA,resource_policy='MISSION_INVENTORY').model_copy(update={'subject_id':'real-profile','mission_id':'real-context'}),'clinician')


def test_followup_and_measurement_scope_checked(clinical):
 out,entry=record_setup(clinical);e=clinical.engine
 e.register('profile',AstronautProfile(id='other',mission_id='clinical-earth',synthetic=True),'researcher');e.open_episode(EpisodeRequest(id='ep2',subject_id='other',mission_id='clinical-earth',condition_id='DKA'),'researcher')
 e.followup(FollowUpPlan(id='wrong-plan',episode_id='ep2',due_at=T,goal_description='synthetic',protocol_reference='synthetic'),'researcher')
 with pytest.raises(ValueError,match='FOLLOWUP_SCOPE'):append_management_record(e,entry.model_copy(update={'followup_plan_id':'wrong-plan'}),'operator')


def test_management_assets_read_only_and_server_document():
 root=Path(__file__).resolve().parents[1]/'vigile/web';js=(root/'management.js').read_text(encoding='utf8')
 assert "'/api/" not in js and 'fetch(' not in js and 'innerHTML' not in js
 assert 'selected?.management' in js and 'authority_verification' in js
 assert '/assets/management.js' in (root/'index.html').read_text(encoding='utf8')


def test_management_dom_renderer_with_synthetic_report():
 import shutil,subprocess
 report=Path(__file__).with_name('fixtures')/'management-v101-report.json'
 if not report.exists():pytest.skip('Explicit synthetic demo not prepared; renderer fixture unavailable')
 node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
 if not Path(node).exists():pytest.skip('Node unavailable; DOM simulation not executed')
 r=subprocess.run([node,str(Path(__file__).with_name('management_ui_unit.cjs'))],capture_output=True,text=True,timeout=20)
 assert r.returncode==0,r.stdout+r.stderr

def test_unknown_test_availability_is_null_not_unavailable(clinical):
 out=evaluate(clinical,{},'DM',resource_policy='MISSION_INVENTORY')
 assert out['next_tests'] and all(t['availability'] is None for t in out['next_tests'])


def test_criteria_not_met_does_not_decide_intervention_not_applicable(clinical):
 out=evaluate(clinical,{'known_diabetes':False,'plasma_glucose_mg_dl':100,'beta_hydroxybutyrate_mmol_l':0,'urine_ketones_plus':0,'venous_pH':7.4,'bicarbonate_mmol_l':24})
 assert out['results']['DKA']['diagnostic_status']=='CRITERIA_NOT_MET'
 assert all(i['applicability_status']=='DOCUMENTED' and not i['intervention_indication_decided'] for i in view(out)['interventions'])


def test_intervention_cannot_be_borrowed_from_other_route(clinical):
 request=req(data=DATA).model_copy(update={'condition_id':None,'presentation_id':'PRES-DIZZINESS-TACHYCARDIA'})
 out=clinical.evaluate(request,'researcher');clinical.engine.open_episode(EpisodeRequest(id='only-dka',subject_id='clinical-crew',mission_id='clinical-earth',condition_id='DKA'),'researcher')
 entry=ManagementRecord(id='wrong-route-report',episode_id='only-dka',evaluation_id=out['id'],intervention_id=view(out,'ANAPHYLAXIS')['interventions'][0]['id'],status='PROPOSED',occurred_at=T,recorded_at=T,source='synthetic',reported_authority='none',note='synthetic')
 with pytest.raises(ValueError,match='INTERVENTION'):append_management_record(clinical.engine,entry,'operator')


def test_resource_snapshot_and_evaluation_share_transaction(clinical,monkeypatch):
 populate(clinical);original=clinical.snapshot
 def snapshot(request):
  assert clinical.store.db.in_transaction,'Resource context and clinical persistence must be atomic'
  return original(request)
 monkeypatch.setattr(clinical,'snapshot',snapshot)
 out=evaluate(clinical,resource_policy='MISSION_INVENTORY');assert clinical.replay(out['id'])['matches']