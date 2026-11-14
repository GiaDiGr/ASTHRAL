"""Synthetic software regression cases, not clinical validation."""
from datetime import timedelta
from itertools import product
import copy
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from test_clinical import clinical,req,result
from vigile.clinical_simulator import observation,AS_OF
from vigile.clinical_logic import tree,leaf,requirements
from vigile.clinical_engine import normalize
from vigile.clinical_contracts import ClinicalEvaluationResponse
from vigile.api import create_app
from vigile.models import MissionContext,AstronautProfile
from conftest import ROOT

STATES=['TRUE','FALSE','UNKNOWN','INVALID']
def truth_and(a,b):
    if 'FALSE' in (a,b): return 'FALSE'
    if 'INVALID' in (a,b): return 'INVALID'
    if 'UNKNOWN' in (a,b): return 'UNKNOWN'
    return 'TRUE'
def truth_or(a,b):
    if 'TRUE' in (a,b): return 'TRUE'
    if 'INVALID' in (a,b): return 'INVALID'
    if 'UNKNOWN' in (a,b): return 'UNKNOWN'
    return 'FALSE'

@pytest.mark.parametrize('states',list(product(STATES,repeat=3)))
def test_nested_four_state_truth_and_requirements(states):
    v={f:True if s=='TRUE' else False for f,s in zip('abc',states) if s in ('TRUE','FALSE')}
    invalid={f:['SYNTHETIC_INVALID'] for f,s in zip('abc',states) if s=='INVALID'}
    n=tree({'all_of':[{'any_of':[leaf('a'),leaf('b')]},leaf('c')]},v,invalid)
    assert n['truth_state']==truth_and(truth_or(*states[:2]),states[2])
    info=requirements(n)
    if n['truth_state'] in ('TRUE','FALSE'):
        assert not info['missing_required'] and not info['invalid_required']
    assert len(n['children'][0]['children'])==2

def test_offset_history_order_and_aki_derivation(clinical):
    r=req('AKI')
    obs=[observation('serum_creatinine_mg_dl',1.3,identifier='current-new',timestamp='2026-10-16T07:00:00-05:00'),
         observation('serum_creatinine_mg_dl',1.1,identifier='current-old',timestamp='2026-10-16T11:00:00Z'),
         observation('baseline_creatinine_mg_dl',1,identifier='baseline',timestamp='2026-10-15T12:00:00Z')]
    r=r.model_copy(update={'observations':obs})
    values,_,history=normalize(r,[o.model_dump(mode='json') for o in obs])
    assert history['serum_creatinine_mg_dl'][-1]['id']=='current-new'
    assert values['serum_creatinine_delta_mg_dl_48h']==.3
    assert result(clinical,r)['diagnostic_status']=='CRITERIA_MET'

@pytest.mark.parametrize('bad', [{'quality':'INVALID'},{'quality':'UNKNOWN'},{'quality':'NOT_MEASURED','value':None},{'unit':'mmHg'}])
def test_latest_unusable_value_has_no_silent_fallback(clinical,bad):
    r=req('DKA',{'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22})
    old=r.observations[-1].model_copy(update={'id':'old-ph','timestamp':AS_OF-timedelta(hours=1)})
    r=r.model_copy(update={'observations':r.observations[:-1]+[old,r.observations[-1].model_copy(update=bad)]})
    out=result(clinical,r)
    assert out['diagnostic_status']!='CRITERIA_MET'
    assert any(i['reason']=='LATEST_OBSERVATION_UNAVAILABLE_NO_FALLBACK' for i in out['data_issues'])

def test_negative_dm_test_does_not_close_unknown_alternatives(clinical):
    out=result(clinical,req('DM',{'fasting_plasma_glucose_mg_dl':90,'fasting_hours':8}))
    assert out['diagnostic_status']=='INSUFFICIENT_DATA'
    assert out['evaluation_tree']['truth_state']=='UNKNOWN'
    assert 'a1c_percent' in out['missing_required']

def test_dm_trace_records_confirmation_collections(clinical):
    out=result(clinical,req('DM',{'fasting_plasma_glucose_mg_dl':126,'fasting_hours':8,'a1c_percent':6.5,'assay_quality.a1c_valid':True}))
    assert out['diagnostic_status']=='CRITERIA_MET'
    assert len(out['evaluation_tree']['confirmation_evidence'])==2
    assert out['evaluation_tree']['operator']=='ADA_CONFIRMATION'

def test_reversed_bp_pair_cannot_derive_drop(clinical):
    r=req('ORTHOSTATIC_HYPOTENSION',{'baseline_sbp_mm_hg':120,'upright_sbp_mm_hg':90,'upright_window_minutes':3,'sustained_reduction':True})
    r=r.model_copy(update={'observations':[o.model_copy(update={'timestamp':AS_OF-timedelta(minutes=1)}) if o.concept=='upright_sbp_mm_hg' else o for o in r.observations]})
    out=result(clinical,r)
    assert out['diagnostic_status']!='CRITERIA_MET'
    assert 'delta_sbp_mm_hg' in out['invalid_required']

def test_high_creatinine_without_acute_change_does_not_upstage_oliguria(clinical):
    out=result(clinical,req('AKI',{'serum_creatinine_mg_dl':4,'urine_output_ml_kg_h':.4,'urine_output_duration_h':6,'body_mass_known':True,'urine_collection_reliable':True}))
    assert out['diagnostic_status']=='CRITERIA_MET'
    assert out['metadata']['aki_stage']==1
    assert out['metadata']['aki_stage_is_minimum_supported']

@pytest.mark.parametrize('hours,creatinine,expected',[(48,1.3,True),(48.0001,1.3,False),(168,1.5,True),(168.0001,1.5,False)])
def test_aki_exact_time_boundaries(clinical,hours,creatinine,expected):
    r=req('AKI',{'serum_creatinine_mg_dl':creatinine})
    baseline=observation('baseline_creatinine_mg_dl',1,timestamp=(AS_OF-timedelta(hours=hours)).isoformat())
    out=result(clinical,r.model_copy(update={'observations':r.observations+[baseline]}))
    assert (out['diagnostic_status']=='CRITERIA_MET')==expected

@pytest.mark.parametrize('ph,bicarb,expected',[(7.3,18,'CRITERIA_NOT_MET'),(7.299,18,'CRITERIA_MET'),(7.3,17.999,'CRITERIA_MET')])
def test_dka_acidosis_exact_boundary(clinical,ph,bicarb,expected):
    out=result(clinical,req('DKA',{'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':3,'venous_pH':ph,'bicarbonate_mmol_l':bicarb}))
    assert out['diagnostic_status']==expected
    assert not out['protocol']['automatic_execution']

@pytest.mark.parametrize('upright,expected',[(140,False),(139.999,True)])
def test_anaphylaxis_strict_percent_boundary(clinical,upright,expected):
    out=result(clinical,req('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'baseline_sbp_mm_hg':200,'adult_sbp_mm_hg':upright}))
    assert (out['diagnostic_status']=='CRITERIA_MET')==expected

@pytest.mark.parametrize('systolic,expected',[(90,False),(89.999,True)])
def test_anaphylaxis_strict_absolute_boundary(clinical,systolic,expected):
    out=result(clinical,req('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'adult_sbp_mm_hg':systolic}))
    assert (out['diagnostic_status']=='CRITERIA_MET')==expected

@pytest.mark.parametrize('delta,window,months,expected',[(30,10,3,True),(29.999,10,3,False),(30,10.001,3,False),(30,10,2.999,False)])
def test_pots_exact_boundaries(clinical,delta,window,months,expected):
    out=result(clinical,req('POTS',{'delta_hr_bpm':delta,'sustained_hr_rise':True,'upright_window_minutes':window,'orthostatic_hypotension_present':False,'orthostatic_symptoms_frequent':True,'symptoms_improve_supine':True,'symptom_duration_months':months,'alternative_cause_present':False}))
    assert (out['diagnostic_status']=='CRITERIA_MET')==expected

def test_simultaneous_conditions_remain_independent(clinical):
    r=req('DKA',{'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22,'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'laryngeal_involvement':True})
    r=r.model_copy(update={'condition_id':None,'presentation_id':'PRES-DIZZINESS-TACHYCARDIA'})
    out=clinical.evaluate(r,'researcher')
    for c in ['DKA','ANAPHYLAXIS']: assert out['results'][c]['diagnostic_status']=='CRITERIA_MET'
    assert out['urgency']=='EMERGENCY'
    assert out['results']['DKA']['required_for_protocol_safety']==['potassium_mmol_l']
    assert clinical.replay(out['id'])['matches'] and clinical.store.verify()

def test_replay_detects_changed_stored_output(clinical,monkeypatch):
    out=clinical.evaluate(req(),'researcher');record=clinical.store.get('clinical_evaluation',out['id'])
    altered=copy.deepcopy(record);altered['urgency']='EMERGENCY'
    original=clinical.store.get
    monkeypatch.setattr(clinical.store,'get',lambda kind,id:altered if kind=='clinical_evaluation' else original(kind,id))
    with pytest.raises(ValueError,match='REPLAY_STORED_OUTPUT_HASH_MISMATCH'): clinical.replay(out['id'])

def test_ambiguous_route_rejected():
    with pytest.raises(ValidationError,match='AMBIGUOUS_ROUTE'): req(presentation_id='PRES-DIZZINESS-TACHYCARDIA')

def test_response_round_trip_and_legacy_omission(clinical):
    out=clinical.evaluate(req('DKA',{'known_diabetes':True,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22}),'researcher')
    assert ClinicalEvaluationResponse.model_validate(out).model_dump(mode='json',exclude_unset=True)==out
    legacy=copy.deepcopy(out)
    for key in ['missing_required','optional_not_measured','invalid_required','invalid_fields','required_for_protocol_safety','data_requirement_version','missing_requirement_semantics']:
        legacy['results']['DKA'].pop(key)
    assert ClinicalEvaluationResponse.model_validate(legacy).model_dump(mode='json',exclude_unset=True)==legacy

def test_openapi_response_contract_and_reader_access(tmp_path):
    tokens={'w'*32:'researcher','r'*32:'reader'}
    # Exercise exactly the existing token format and HTTP authentication path.
    tokens={token:{'id':role,'role':role,'subject_ids':['*'],'mission_ids':['*']} for token,role in tokens.items()}
    with TestClient(create_app(ROOT,tmp_path/'audit.db',tokens=tokens)) as client:
        wh={'Authorization':'Bearer '+'w'*32};rh={'Authorization':'Bearer '+'r'*32}
        engine=client.app.state.engine
        engine.register('mission',MissionContext(id='clinical-earth',phase='PRE_MISSION',gravity='EARTH',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=True),'researcher')
        engine.register('profile',AstronautProfile(id='clinical-crew',mission_id='clinical-earth',synthetic=True),'researcher')
        response=client.post('/clinical/evaluations',json=req().model_dump(mode='json'),headers=wh)
        assert response.status_code==201,response.text
        data=response.json();url='/clinical/evaluations/'+data['id']
        assert client.get(url,headers=rh).json()==data
        assert client.get(url+'/replay',headers=rh).json()['matches']
        assert client.post('/clinical/evaluations',json=req().model_dump(mode='json'),headers=rh).status_code==403
        schema=client.app.openapi()
        assert schema['paths']['/clinical/evaluations']['post']['responses']['201']['content']['application/json']['schema']['$ref'].endswith('ClinicalEvaluationResponse')
        assert 'optional_not_measured' in schema['components']['schemas']['ClinicalResultResponse']['properties']

def test_bound_stale_measurement_is_invalid(clinical):
    from conftest import add,NOW
    from vigile.clinical_models import MeasurementBinding
    add(clinical.engine,'old-glucose','plasma_glucose_mg_dl',200,'mg/dL',method='VENOUS_PLASMA')
    r=req('DKA',{'beta_hydroxybutyrate_mmol_l':4,'venous_pH':7.2}).model_copy(update={
        'subject_id':'crew','mission_id':'mission','window_start':NOW-timedelta(days=1),
        'measurement_bindings':[MeasurementBinding(measurement_id='old-glucose',concept='plasma_glucose_mg_dl',sample_id='old')]})
    out=clinical.evaluate(r,'researcher');record=clinical.store.get('clinical_evaluation',out['id'])
    assert record['snapshot']['measurement_records'][0]['quality_reason']=='STALE'
    assert out['results']['DKA']['diagnostic_status']!='CRITERIA_MET'
    assert 'plasma_glucose_mg_dl' in out['results']['DKA']['invalid_required']

def test_bound_historical_baseline_is_explicit_exception(clinical):
    from conftest import add
    from vigile.clinical_models import MeasurementBinding
    from vigile.models import Device
    d=Device(id='short-age',variable='serum_creatinine_mg_dl',unit='mg/dL',calibration_id='cal-short',calibrated_at=AS_OF-timedelta(days=10),valid_until=AS_OF+timedelta(days=1),technical_min=0,technical_max=20,max_age_seconds=60,policy_reference='SYNTHETIC_NOT_CLINICAL',synthetic=True,conflict_tolerance=.1,alignment_seconds=1)
    clinical.engine.register('device',d,'researcher')
    add(clinical.engine,'prior-creatinine','serum_creatinine_mg_dl',1,'mg/dL',device_id=d.id,calibration_id=d.calibration_id,method='SERUM_LAB',timestamp=AS_OF-timedelta(days=1))
    r=req('AKI',{'serum_creatinine_mg_dl':1.3}).model_copy(update={'subject_id':'crew','mission_id':'mission','measurement_bindings':[MeasurementBinding(measurement_id='prior-creatinine',concept='baseline_creatinine_mg_dl',sample_id='baseline')]})
    out=clinical.evaluate(r,'researcher')
    assert out['results']['AKI']['diagnostic_status']=='CRITERIA_MET'
    assert clinical.replay(out['id'])['matches']


def test_orthostatic_pressure_cannot_diagnose_anaphylaxis(clinical):
    out=result(clinical,req('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'known_or_highly_probable_allergen':True,'baseline_sbp_mm_hg':200,'upright_sbp_mm_hg':100}))
    assert out['diagnostic_status']!='CRITERIA_MET'
    assert 'sbp_drop_percent' in out['missing_required']

def test_invalid_fasting_context_cannot_be_reused_for_confirmation(clinical):
    prior=AS_OF-timedelta(days=1)
    obs=[observation('fasting_plasma_glucose_mg_dl',130,sample='first',timestamp=prior),
         observation('fasting_hours',8,sample='first',timestamp=prior),
         observation('fasting_hours',None,sample='first',timestamp=prior+timedelta(minutes=1),identifier='invalid-fasting',quality='INVALID'),
         observation('fasting_plasma_glucose_mg_dl',130,sample='second'),
         observation('fasting_hours',8,sample='second')]
    out=result(clinical,req('DM').model_copy(update={'observations':obs}))
    assert out['diagnostic_status']!='CRITERIA_MET'
    assert out['confirmation_status']=='REQUIRED'
    first=next(n for n in out['evaluation_tree']['children'] if n.get('sample_id')=='first')
    assert first['truth_state']=='INVALID'
    assert 'invalid-fasting' in first['context_observation_ids']


def test_conflicting_historical_sample_cannot_confirm_diabetes(clinical):
    prior=AS_OF-timedelta(days=1)
    obs=[observation('fasting_plasma_glucose_mg_dl',130,sample='first',timestamp=prior),
         observation('fasting_plasma_glucose_mg_dl',80,sample='first',timestamp=prior,identifier='conflict-first'),
         observation('fasting_hours',8,sample='first',timestamp=prior),
         observation('fasting_plasma_glucose_mg_dl',130,sample='second'),observation('fasting_hours',8,sample='second')]
    out=result(clinical,req('DM').model_copy(update={'observations':obs}))
    assert out['diagnostic_status']!='CRITERIA_MET'
    assert all(n['truth_state']=='INVALID' for n in out['evaluation_tree']['children'] if n.get('sample_id')=='first')

def test_random_glucose_and_symptoms_need_collection_context(clinical):
    obs=[observation('random_plasma_glucose_mg_dl',240,sample='prior',timestamp=AS_OF-timedelta(days=1)),observation('classic_hyperglycemia_symptoms',True,sample='now')]
    out=result(clinical,req('DM').model_copy(update={'observations':obs}))
    assert out['diagnostic_status']!='CRITERIA_MET'
    assert 'classic_hyperglycemia_symptoms' in out['missing_required']
