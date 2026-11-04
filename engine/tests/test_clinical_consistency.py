import copy,itertools,json
import pytest
from vigile.clinical_logic import tree,leaf,requirements
from vigile.clinical_simulator import observation
from vigile.local_assistant import answer,evidence_blocks
from vigile.conversational import ConversationalInference
from test_clinical import clinical,req,result
from test_portal import dataset,services

STATES=['TRUE','FALSE','UNKNOWN','INVALID']
@pytest.mark.parametrize('operator', ['all_of','any_of'])
@pytest.mark.parametrize('a,b',list(itertools.product(STATES,repeat=2)))
def test_four_state_truth_tables(operator,a,b):
    values={k:v=='TRUE' for k,v in [('a',a),('b',b)] if v in ('TRUE','FALSE')}
    invalid={k:['BAD_SENSOR'] for k,v in [('a',a),('b',b)] if v=='INVALID'}
    out=tree({operator:[leaf('a'),leaf('b')]},values,invalid)
    # Explicit expected algebra: determining evidence wins; otherwise preserve invalidity.
    expected_and=[['TRUE','FALSE','UNKNOWN','INVALID'],['FALSE']*4,
                  ['UNKNOWN','FALSE','UNKNOWN','INVALID'],['INVALID','FALSE','INVALID','INVALID']]
    expected_or=[['TRUE']*4,['TRUE','FALSE','UNKNOWN','INVALID'],
                 ['TRUE','UNKNOWN','UNKNOWN','INVALID'],['TRUE','INVALID','INVALID','INVALID']]
    assert out['truth_state']==(expected_and if operator=='all_of' else expected_or)[STATES.index(a)][STATES.index(b)]
    assert len(out['children'])==2 and [c['truth_state'] for c in out['children']]==[a,b]
    requirements(out)
    assert out['children'][0]['path']!=out['children'][1]['path']

@pytest.mark.parametrize('a,expected_missing,expected_optional',[(True,[],['b']),(False,['b'],[]),(None,['a','b'],[])])
def test_or_requirements(a,expected_missing,expected_optional):
    out=tree({'any_of':[leaf('a'),leaf('b')]},{} if a is None else {'a':a})
    r=requirements(out)
    assert r['missing_required']==expected_missing
    assert r['optional_not_measured']==expected_optional

def test_nested_false_branch_missing_is_not_needed_for_root():
    out=tree({'any_of':[{'all_of':[leaf('a'),leaf('b')]},leaf('c')]},{'a':False})
    r=requirements(out)
    assert r['missing_required']==['c'] and r['optional_not_measured']==['b']

DATA={'known_diabetes':True,'plasma_glucose_mg_dl':180,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22}

def test_reported_dka_case_independent_safety(clinical):
    out=clinical.evaluate(req(data=DATA),'researcher');r=out['results']['DKA']
    assert r['diagnostic_status']=='CRITERIA_MET' and r['evaluation_tree']['truth_state']=='TRUE'
    assert r['missing_required']==[] and r['invalid_required']==[]
    assert r['optional_not_measured']==['bicarbonate_mmol_l','urine_ketones_plus']
    assert r['required_for_protocol_safety']==['potassium_mmol_l']
    assert 'BLOCKED_MISSING_DATA:POTASSIUM' in r['protocol']['block_reasons']
    assert len(out['next_tests'])==1 and out['next_tests'][0]['action']=='OBTAIN_POTASSIUM_SAFETY_DATA'
    assert clinical.replay(out['id'])['matches'] and clinical.store.verify()

@pytest.mark.parametrize('value,state,missing',[(7.22,'TRUE',[]),(7.4,'UNKNOWN',['bicarbonate_mmol_l']),(None,'UNKNOWN',['bicarbonate_mmol_l','venous_pH'])])
def test_dka_acidosis_alternatives(clinical,value,state,missing):
    data=dict(DATA);data['venous_pH']=value
    if value is None:data.pop('venous_pH')
    out=clinical.evaluate(req(data=data),'researcher');r=out['results']['DKA']
    assert r['evaluation_tree']['truth_state']==state and r['missing_required']==missing
    ids={t['test_id'] for t in out['next_tests']}
    assert ('TEST-VENOUS-PH-BICARB' in ids)==bool(missing)

def test_false_acidosis_is_not_unknown(clinical):
    r=result(clinical,req(data={**DATA,'venous_pH':7.4,'bicarbonate_mmol_l':22}))
    assert r['evaluation_tree']['truth_state']=='FALSE' and r['diagnostic_status']=='CRITERIA_NOT_MET'
    assert r['missing_required']==[]

@pytest.mark.parametrize('quality',['INVALID','UNKNOWN','NOT_MEASURED'])
def test_quality_is_not_silent_absence(clinical,quality):
    request=req(data=DATA)
    request=request.model_copy(update={'observations':[o.model_copy(update={'quality':quality}) if o.concept=='venous_pH' else o for o in request.observations]})
    r=result(clinical,request)
    assert r['evaluation_tree']['truth_state']==('INVALID' if quality=='INVALID' else 'UNKNOWN')
    assert ('venous_pH' in r['invalid_required'])==(quality=='INVALID')
    assert r['diagnostic_status']!='CRITERIA_MET'

def test_invalid_alternative_does_not_erase_valid_or(clinical):
    request=req(data={**DATA,'bicarbonate_mmol_l':12})
    request=request.model_copy(update={'observations':[o.model_copy(update={'quality':'INVALID'}) if o.concept=='bicarbonate_mmol_l' else o for o in request.observations]})
    r=result(clinical,request)
    assert r['diagnostic_status']=='CRITERIA_MET' and r['invalid_required']==[]
    assert r['invalid_fields']==['bicarbonate_mmol_l']

@pytest.mark.parametrize('condition,data,optional',[
 ('ORTHOSTATIC_HYPOTENSION',{'baseline_sbp_mm_hg':120,'upright_sbp_mm_hg':95,'upright_window_minutes':2,'sustained_reduction':True},'delta_dbp_mm_hg'),
 ('ANAPHYLAXIS',{'acute_onset_minutes_to_hours':True,'skin_or_mucosal_involvement':True,'respiratory_compromise':True},'severe_gi_symptoms'),
 ('AKI',{'urine_output_ml_kg_h':.4,'urine_output_duration_h':7,'body_mass_known':True,'urine_collection_reliable':True},'serum_creatinine_ratio_to_baseline_7d'),
 ('DM',{'random_plasma_glucose_mg_dl':240,'classic_hyperglycemia_symptoms':True},'hyperglycemic_crisis')])
def test_other_clinical_or_routes(clinical,condition,data,optional):
    r=result(clinical,req(condition,data))
    assert r['diagnostic_status']=='CRITERIA_MET' and r['missing_required']==[]
    assert optional in r['optional_not_measured']

@pytest.mark.parametrize('mode',['FULL','LOW_POWER','CRITICAL'])
@pytest.mark.parametrize('question',['¿Qué datos faltan?','¿Necesito bicarbonato para evaluar DKA?','¿Son imprescindibles las cetonas urinarias?'])
def test_assistant_sufficiency_never_reinterprets_engine(services,mode,question):
    _,portal,reader,config=services
    evaluation=reader.get('/dashboard/subjects/clinical-crew?mission_id=clinical-earth')['evaluations'][0]
    class Model:
        def status(self):return {'available':True}
        def explain(self,*a):raise AssertionError('LLM MUST NOT REINTERPRET MISSINGNESS')
    model=Model();model.mode=mode
    reply=answer(reader,model,evaluation['id'],question)
    assert not reply['inference_executed'] and not reply['generated']
    assert reply['consistency_policy']=='ENGINE_DATA_REQUIREMENTS_ONLY'
    text=reply['answer'][0]['text']
    assert 'CRITERIA_MET' in text and 'Datos pendientes para resolver ramas indeterminadas: ninguno' in text
    assert 'potasio' in text and 'Alternativas no medidas' in text

def test_legacy_missing_fields_are_not_relabelled(services):
    _,_,reader,_=services
    ev=reader.get('/dashboard/subjects/clinical-crew?mission_id=clinical-earth')['evaluations'][0]
    ev=copy.deepcopy(ev)
    for r in ev['results'].values():r.pop('data_requirement_version')
    blocks=evidence_blocks(ev,reader)
    assert any('evaluación histórica' in b['text'] for b in blocks)
    assert not any(': datos faltantes ' in b['text'] for b in blocks)

def test_nonfinite_and_wrong_type_are_invalid():
    for value in (True, '3', float('nan'), float('inf')):
        assert tree(leaf('x',3,'>='),{'x':value})['truth_state']=='INVALID'

def test_wrong_units_remain_invalid_even_with_numeric_value(clinical):
    request=req(data=DATA)
    request=request.model_copy(update={'observations':[o.model_copy(update={'unit':'mmHg'}) if o.concept=='venous_pH' else o for o in request.observations]})
    r=result(clinical,request)
    assert r['evaluation_tree']['truth_state']=='INVALID' and 'venous_pH' in r['invalid_required']

def test_guard_rejects_optional_requirement_despite_model_approval():
    from vigile.conversational import validate_generated
    blocks=[{'id':'E1','text':'CRITERIA_MET. Alternativas no medidas: bicarbonato.', 'reference':{},
             'clinical_contract':{'diagnostic_status':'CRITERIA_MET','missing_required':[],
                                  'optional_not_measured':['bicarbonate_mmol_l'],'required_for_protocol_safety':['potassium_mmol_l']}}]
    for text in ('Falta bicarbonato para evaluar DKA.','Faltan datos para diagnosticar DKA.'):
        with pytest.raises(ValueError):
            validate_generated({'sentences':[{'text':text,'evidence_ids':['E1']}]},blocks)

def test_generic_context_keeps_global_state(services):
    _,_,reader,_=services
    ev=reader.get('/dashboard/subjects/clinical-crew?mission_id=clinical-earth')['evaluations'][0]
    class Inspect:
        mode='FULL'
        def status(self):return {'available':True}
        def explain(self,question,blocks,history):
            assert any(': diagnóstico CRITERIA_MET' in b['text'] for b in blocks)
            assert any(b.get('clinical_contract',{}).get('optional_not_measured') for b in blocks)
            return {'generated':[],'status':'INSUFFICIENT_INFORMATION','inference_executed':True}
    answer(reader,Inspect(),ev['id'],'Explica los criterios')
