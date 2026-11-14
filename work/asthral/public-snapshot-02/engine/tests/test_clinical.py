import copy,json
from datetime import timedelta
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from vigile.clinical_models import ClinicalRequest
from vigile.clinical_engine import ClinicalService
from vigile.clinical_knowledge import ClinicalKnowledge
from vigile.clinical_logic import tree,leaf
from vigile.clinical_simulator import observation,report_case,AS_OF
from vigile.models import MissionContext,AstronautProfile
from vigile.api import create_app
from conftest import ROOT,add,NOW

@pytest.fixture
def clinical(engine):
    engine.register('mission',MissionContext(id='clinical-earth',phase='PRE_MISSION',gravity='EARTH',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True),'researcher')
    engine.register('profile',AstronautProfile(id='clinical-crew',mission_id='clinical-earth',synthetic=True),'researcher')
    return ClinicalService(engine)

def req(condition='DKA',data=None,**kw):
    return ClinicalRequest(subject_id='clinical-crew',mission_id='clinical-earth',condition_id=condition,population='NONPREGNANT_ADULT',age_years=30,as_of=AS_OF,window_start=AS_OF-timedelta(days=7),observations=[observation(k,v) for k,v in (data or {}).items()],**kw)
def result(service,request): return service.evaluate(request,'researcher')['results'][request.condition_id]
CASES=ClinicalKnowledge().documents['synthetic_cases']['cases']
# Explicit reconciliation, NOT generated from actual outputs. See docs/clinical/DECISIONS.md.
EXPECTED={
 'DM-01':('DM','CRITERIA_MET','ROUTINE','SATISFIED','BLOCKED_AUTHORIZATION'),
 'DM-02':('DM','SUSPECTED','ROUTINE','REQUIRED','BLOCKED_AUTHORIZATION'),
 'DM-03':('DM','CRITERIA_MET','PROMPT','NOT_REQUIRED','BLOCKED_AUTHORIZATION'),
 'DM-04':('DM','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'DM-05':('DKA','CRITERIA_MET','EMERGENCY','SATISFIED','BLOCKED_MISSING_DATA'),
 'DM-06':('DKA','SUSPECTED','URGENT','REQUIRED','BLOCKED_MISSING_DATA'),
 'ORTHO-01':('ORTHOSTATIC_HYPOTENSION','SUSPECTED','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'ORTHO-02':('ORTHOSTATIC_HYPOTENSION','SUSPECTED','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'ORTHO-03':('ORTHOSTATIC_HYPOTENSION','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'ORTHO-04':('POTS','SUSPECTED','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'ORTHO-05':('POTS','CRITERIA_NOT_MET','PROMPT','NOT_APPLICABLE','NOT_INDICATED'),
 'ORTHO-06':('ORTHOSTATIC_HYPOTENSION','NOT_APPLICABLE','ROUTINE','NOT_APPLICABLE','NOT_INDICATED'),
 'AKI-01':('AKI','CRITERIA_MET','URGENT','SATISFIED','BLOCKED_AUTHORIZATION'),
 'AKI-02':('AKI','CRITERIA_MET','URGENT','SATISFIED','BLOCKED_AUTHORIZATION'),
 'AKI-03':('AKI','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'AKI-04':('AKI','CRITERIA_MET','URGENT','SATISFIED','BLOCKED_AUTHORIZATION'),
 'AKI-05':('AKI','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'AKI-06':('AKI','CRITERIA_MET','URGENT','SATISFIED','BLOCKED_AUTHORIZATION'),
 'ANAPH-01':('ANAPHYLAXIS','CRITERIA_MET','EMERGENCY','NOT_REQUIRED','BLOCKED_RESOURCE'),
 'ANAPH-02':('ANAPHYLAXIS','CRITERIA_MET','EMERGENCY','NOT_REQUIRED','BLOCKED_RESOURCE'),
 'ANAPH-03':('ANAPHYLAXIS','SUSPECTED','PROMPT','PENDING','BLOCKED_MISSING_DATA'),
 'ANAPH-04':('ANAPHYLAXIS','SUSPECTED','PROMPT','PENDING','BLOCKED_MISSING_DATA'),
 'ANAPH-05':('ANAPHYLAXIS','CRITERIA_MET','EMERGENCY','NOT_REQUIRED','BLOCKED_RESOURCE'),
 'ANAPH-06':('ANAPHYLAXIS','SUSPECTED','EMERGENCY','PENDING','BLOCKED_MISSING_DATA'),
 'DIFF-01':('ORTHOSTATIC_HYPOTENSION','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'DIFF-02':('POTS','CRITERIA_NOT_MET','PROMPT','NOT_APPLICABLE','NOT_INDICATED'),
 'DIFF-03':('ANAPHYLAXIS','SUSPECTED','EMERGENCY','PENDING','BLOCKED_MISSING_DATA'),
 'DIFF-04':('DKA','SUSPECTED','URGENT','REQUIRED','BLOCKED_MISSING_DATA'),
 'DIFF-05':('AKI','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA'),
 'DIFF-06':('POTS','INSUFFICIENT_DATA','PROMPT','REQUIRED','BLOCKED_MISSING_DATA')}

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_report_30_cases(clinical,case):
    request=report_case(case)
    if case['id'] in ('ORTHO-06','AKI-06'): request=request.model_copy(update={'subject_id':'crew','mission_id':'mission'})
    output=clinical.evaluate(request,'researcher'); condition,*expected=EXPECTED[case['id']]; actual=output['results'][condition]
    assert [actual[k] for k in ('diagnostic_status','urgency','confirmation_status','protocol_status')]==expected
    assert actual['treatment_status']=='NOT_STARTED'
    if 'stage' in case: assert actual['metadata']['aki_stage']==(None if case['id']=='AKI-03' else case['stage'])
    assert clinical.replay(output['id'])['matches']
    assert clinical.store.verify()
    if case['id']=='DIFF-06':
        assert output['differential'][0]['condition_id']=='EXTERNAL_ARRHYTHMIA_PATHWAY'
        assert [t['test_id'] for t in output['next_tests']]==['TEST-ECG']
    if case['id']=='DIFF-04': assert {'TEST-BETA-OHB','TEST-VENOUS-PH-BICARB'}<={t['test_id'] for t in output['next_tests']}
    if case['id']=='DIFF-02': assert output['differential'][0]['condition_id']=='HYPOVOLEMIA'

@pytest.mark.parametrize('values,expected',[({},None),({'x':False},False),({'x':True},True),({'x':1},None),({'x':'true'},None)])
def test_typed_three_value_logic(values,expected): assert tree(leaf('x'),values)['state'] is expected

@pytest.mark.parametrize('changes',[{'unit':'mmHg'},{'quality':'INVALID'},{'timestamp':AS_OF+timedelta(seconds=1)},{'timestamp':AS_OF-timedelta(days=8)},{'method':'CGM'},{'value':True}])
def test_invalid_data_cannot_diagnose(clinical,changes):
    r=req('DM',{'random_plasma_glucose_mg_dl':240,'classic_hyperglycemia_symptoms':True})
    r=r.model_copy(update={'observations':[r.observations[0].model_copy(update=changes),r.observations[1]]})
    assert result(clinical,r)['diagnostic_status']!='CRITERIA_MET'

def test_timestamp_timezone_required():
    with pytest.raises(ValidationError): observation('known_diabetes',True,timestamp='2026-10-16T12:00:00')

@pytest.mark.parametrize('potassium,expected',[(None,'BLOCKED_MISSING_DATA'),(3.4,'BLOCKED_CONTRAINDICATION'),(3.5,'BLOCKED_CONTRAINDICATION'),(3.6,'BLOCKED_AUTHORIZATION')])
def test_dka_safety_independent_urgency(clinical,potassium,expected):
    data={'known_diabetes':True,'plasma_glucose_mg_dl':180,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22}
    if potassium is not None: data['potassium_mmol_l']=potassium
    resources={name:True for name in clinical.knowledge.protocols['PROT-DKA-ADULT-2024']['required_resources']}
    r=result(clinical,req(data=data,resources=resources))
    assert (r['diagnostic_status'],r['urgency'],r['protocol_status'])==('CRITERIA_MET','EMERGENCY',expected)

def test_repeated_sample_not_confirmation(clinical):
    r=req('DM',{'fasting_plasma_glucose_mg_dl':130,'fasting_hours':8})
    duplicate=r.observations[0].model_copy(update={'id':'different-record-same-sample'})
    r=r.model_copy(update={'observations':r.observations+[duplicate]})
    assert result(clinical,r)['confirmation_status']=='REQUIRED'

def test_dm_discordant_tests(clinical):
    r=result(clinical,req('DM',{'fasting_plasma_glucose_mg_dl':130,'fasting_hours':8,'a1c_percent':5,'assay_quality.a1c_valid':True}))
    assert r['diagnostic_status']=='CONFLICTING_EVIDENCE'

def test_complete_oh_and_pots(clinical):
    oh=result(clinical,req('ORTHOSTATIC_HYPOTENSION',{'baseline_sbp_mm_hg':120,'upright_sbp_mm_hg':100,'upright_window_minutes':3,'sustained_reduction':True}))
    assert oh['diagnostic_status']=='CRITERIA_MET'
    data={'delta_hr_bpm':35,'sustained_hr_rise':True,'upright_window_minutes':10,'orthostatic_hypotension_present':False,'orthostatic_symptoms_frequent':True,'symptoms_improve_supine':True,'symptom_duration_months':4,'alternative_cause_present':False}
    assert result(clinical,req('POTS',data))['diagnostic_status']=='CRITERIA_MET'
    data['orthostatic_hypotension_present']=True
    assert result(clinical,req('POTS',data))['diagnostic_status']=='CRITERIA_NOT_MET'

@pytest.mark.parametrize('uo,hours,stage',[(.4,6,1),(.4,12,2),(.2,24,3),(.3,24,2)])
def test_aki_urine_staging(clinical,uo,hours,stage):
    r=result(clinical,req('AKI',{'urine_output_ml_kg_h':uo,'urine_output_duration_h':hours,'body_mass_known':True,'urine_collection_reliable':True}))
    assert r['metadata']['aki_stage']==stage

def test_aki_baseline_outside_window(clinical):
    r=req('AKI',{'serum_creatinine_mg_dl':2})
    r=r.model_copy(update={'observations':r.observations+[observation('baseline_creatinine_mg_dl',1,timestamp=AS_OF-timedelta(days=8))]})
    assert result(clinical,r)['diagnostic_status']=='INSUFFICIENT_DATA'

@pytest.mark.parametrize('verification',['DRAFT_NOT_FOR_PRODUCTION','RETRACTED','SUPERSEDED','UNVERIFIED'])
def test_noncurrent_sources_block_clinical_result(clinical,verification):
    clinical.knowledge.sources['SRC-DKA-2024']['verification']=verification
    r=result(clinical,req(data={'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4,'venous_pH':7.2}))
    assert r['diagnostic_status']=='INSUFFICIENT_DATA' and r['urgency']=='EMERGENCY'

def test_replay_and_immutable_reassessment(clinical):
    r=req(data={'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4})
    first=clinical.evaluate(r,'researcher'); original=clinical.store.get('clinical_evaluation',first['id'])
    second=clinical.evaluate(r.model_copy(update={'observations':r.observations+[observation('venous_pH',7.2)]}),'researcher',first['id'])
    assert second['parent_id']==first['id'] and second['results']['DKA']['diagnostic_status']=='CRITERIA_MET'
    assert clinical.store.get('clinical_evaluation',first['id'])==original
    assert clinical.replay(first['id'])['matches'] and clinical.replay(second['id'])['matches']
    clinical.knowledge.hash='tampered'
    with pytest.raises(ValueError,match='VERSION'): clinical.replay(first['id'])

def test_api_reader_scope_and_escalation(tmp_path):
    writer='w'*32; reader='r'*32; outsider='o'*32
    tokens={writer:{'id':'writer','role':'researcher','subject_ids':['*'],'mission_ids':['*']},reader:{'id':'rag','role':'reader','subject_ids':['clinical-crew'],'mission_ids':['clinical-earth']},outsider:{'id':'other','role':'reader','subject_ids':['other'],'mission_ids':['clinical-earth']}}
    with TestClient(create_app(ROOT,tmp_path/'clinical.sqlite3',tokens)) as client:
        wh={'Authorization':'Bearer '+writer};rh={'Authorization':'Bearer '+reader}
        assert client.post('/missions',headers=wh,json={'id':'clinical-earth','phase':'PRE_MISSION','gravity':'EARTH','environment':'HABITABLE_VOLUME','mode':'NOMINAL','synthetic':True}).status_code==201
        assert client.post('/profiles',headers=wh,json={'id':'clinical-crew','mission_id':'clinical-earth','synthetic':True}).status_code==201
        body=req(data={'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4,'venous_pH':7.2}).model_dump(mode='json')
        response=client.post('/clinical/evaluations',headers=wh,json=body);assert response.status_code==201,response.text
        identifier=response.json()['id'];url='/clinical/evaluations/'+identifier
        read=client.get(url,headers=rh);assert read.status_code==200 and 'snapshot' not in read.json()
        assert client.get(url,headers={'Authorization':'Bearer '+outsider}).status_code==403
        assert client.post(url+'/reassess',headers=rh,json=body).status_code==403
        assert client.post('/clinical/evaluations',headers=rh,json={**body,'role':'clinician'}).status_code==403
        assert client.post('/clinical/evaluations',headers=wh,json={**body,'mission_approved':True}).status_code==422
        assert client.get(url+'/replay',headers=rh).json()['matches']
        assert client.post('/clinical/protocols/PROT-DKA-ADULT-2024/eligibility',headers=wh,json={'evaluation_id':identifier}).status_code==200
        assert client.get('/clinical/knowledge/version',headers=rh).status_code==200
        assert client.get('/audit/verify',headers=wh).json()['valid']

def test_complete_api_demo(tmp_path):
    from vigile.clinical_demo import run
    report=run(ROOT,tmp_path/'demo')
    assert report['all_replays_match'] and report['reader_write_denied']
    assert report['clinical_validation'] is False
    transcript=json.loads((tmp_path/'demo/synthetic-http-transcript.json').read_text(encoding='utf-8'))
    assert any(t['path']=='/measurements' for t in transcript)
    assert any(t['path'].endswith('/reassess') for t in transcript)

def test_same_time_repeat_not_confirmation(clinical):
    r=req('DM',{'fasting_plasma_glucose_mg_dl':130,'fasting_hours':8})
    second=[o.model_copy(update={'id':o.id+'-2','sample_id':'different-sample'}) for o in r.observations]
    assert result(clinical,r.model_copy(update={'observations':r.observations+second}))['confirmation_status']=='REQUIRED'

def test_same_occasion_distinct_tests_confirm(clinical):
    r=result(clinical,req('DM',{'fasting_plasma_glucose_mg_dl':130,'fasting_hours':8,'a1c_percent':7,'assay_quality.a1c_valid':True}))
    assert r['diagnostic_status']=='CRITERIA_MET' and r['confirmation_status']=='SATISFIED'

def test_ogtt_requires_2h_attestation(clinical):
    r=req('DM',{'ogtt_2h_plasma_glucose_mg_dl':220,'ogtt_glucose_load_g':75})
    assert result(clinical,r)['diagnostic_status']!='CRITERIA_MET'

def test_anaphylaxis_second_path_bronchospasm_exclusions(clinical):
    r=req('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'bronchospasm':True,'skin_or_mucosal_involvement':False,'common_inhalant_trigger':False,'food_inhalation_without_ingestion':False})
    assert result(clinical,r)['diagnostic_status']=='CRITERIA_MET'
    r=r.model_copy(update={'observations':[o.model_copy(update={'value':True}) if o.concept=='common_inhalant_trigger' else o for o in r.observations]})
    assert result(clinical,r)['diagnostic_status']!='CRITERIA_MET'

def test_evaluated_oh_excludes_pots(clinical):
    data={'baseline_sbp_mm_hg':120,'upright_sbp_mm_hg':95,'upright_window_minutes':2,'sustained_reduction':True,
     'delta_hr_bpm':35,'sustained_hr_rise':True,'orthostatic_hypotension_present':False,'orthostatic_symptoms_frequent':True,
     'symptoms_improve_supine':True,'symptom_duration_months':4,'alternative_cause_present':False}
    assert result(clinical,req('POTS',data))['diagnostic_status']=='CRITERIA_NOT_MET'

def test_conflicting_data_not_normal(clinical):
    r=req('DM',{'random_plasma_glucose_mg_dl':240,'classic_hyperglycemia_symptoms':True})
    conflict=observation('random_plasma_glucose_mg_dl',80,identifier='other-device')
    r=r.model_copy(update={'observations':r.observations+[conflict]})
    assert result(clinical,r)['diagnostic_status']=='CONFLICTING_EVIDENCE'

def test_unit_conversion_is_analyte_specific(clinical):
    r=req('DM',{'random_plasma_glucose_mg_dl':12,'classic_hyperglycemia_symptoms':True})
    r=r.model_copy(update={'observations':[r.observations[0].model_copy(update={'unit':'mmol/L'}),r.observations[1]]})
    assert result(clinical,r)['diagnostic_status']=='CRITERIA_MET'
    bad=req('AKI',{'serum_creatinine_mg_dl':12})
    bad=bad.model_copy(update={'observations':[bad.observations[0].model_copy(update={'unit':'mmol/L'})]})
    assert result(clinical,bad)['data_issues'][0]['reason']=='INCOMPATIBLE_UNIT'

@pytest.mark.parametrize('value',[float('inf'),float('nan')])
def test_nonfinite_values_rejected(value):
    with pytest.raises(ValidationError): observation('plasma_glucose_mg_dl',value)

def test_missing_population_and_partial_gravity_block(clinical):
    r=req('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'laryngeal_involvement':True})
    out=result(clinical,r.model_copy(update={'population':'UNKNOWN'}))
    assert out['diagnostic_status']=='INSUFFICIENT_DATA' and out['urgency']=='EMERGENCY'
    clinical.engine.register('mission',MissionContext(id='partial',phase='IN_MISSION',gravity='PARTIAL',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True),'researcher')
    clinical.engine.register('profile',AstronautProfile(id='partial-crew',mission_id='partial',synthetic=True),'researcher')
    r=req('ORTHOSTATIC_HYPOTENSION',{'baseline_sbp_mm_hg':120,'upright_sbp_mm_hg':90,'upright_window_minutes':2,'sustained_reduction':True})
    out=result(clinical,r.model_copy(update={'subject_id':'partial-crew','mission_id':'partial'}))
    assert out['diagnostic_status']=='INSUFFICIENT_DATA' and out['confirmation_status']=='UNAVAILABLE'

def test_knowledge_tampering_rejected(tmp_path):
    import shutil
    source=ClinicalKnowledge().path; shutil.copytree(source,tmp_path/'knowledge')
    (tmp_path/'knowledge/diagnostic_criteria.json').write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='HASH_MISMATCH'): ClinicalKnowledge(tmp_path/'knowledge')

def test_measurement_reference_scope_enforced(clinical):
    add(clinical.engine,'foreign-measurement','plasma_glucose_mg_dl',250,'mg/dL',method='VENOUS_PLASMA')
    from vigile.clinical_models import MeasurementBinding
    r=req('DM',{'classic_hyperglycemia_symptoms':True}).model_copy(update={'measurement_bindings':[MeasurementBinding(measurement_id='foreign-measurement',concept='plasma_glucose_mg_dl',sample_id='a')]})
    with pytest.raises(ValueError,match='SCOPE_MISMATCH'): clinical.evaluate(r,'researcher')

def test_clinical_offline_no_network(clinical,monkeypatch):
    import socket
    def blocked(*args,**kwargs): raise AssertionError('NETWORK_FORBIDDEN')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    out=clinical.evaluate(req(data={'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4,'venous_pH':7.2}),'researcher')
    assert out['urgency']=='EMERGENCY' and clinical.replay(out['id'])['matches']

def test_reevaluation_cannot_change_route(clinical):
    first=clinical.evaluate(req(),'researcher')
    with pytest.raises(ValueError,match='ROUTE'): clinical.evaluate(req('AKI'),'researcher',first['id'])

def test_no_insulin_or_drug_execution_contract():
    raw=req().model_dump(mode='json')
    for field,value in [('mission_approved',True),('treatment_status','STARTED'),('initial_epinephrine_route','IV_BOLUS'),('role','clinician')]:
        with pytest.raises(ValidationError): ClinicalRequest.model_validate({**raw,field:value})

@pytest.mark.parametrize('age,status',[(None,'INSUFFICIENT_DATA'),(19,'NOT_APPLICABLE'),(20,'CRITERIA_MET')])
def test_pots_adolescent_threshold_not_misapplied(clinical,age,status):
    r=req('POTS',{'delta_hr_bpm':35,'sustained_hr_rise':True,'upright_window_minutes':10,'orthostatic_hypotension_present':False,
       'orthostatic_symptoms_frequent':True,'symptoms_improve_supine':True,'symptom_duration_months':4,'alternative_cause_present':False})
    assert result(clinical,r.model_copy(update={'age_years':age}))['diagnostic_status']==status
