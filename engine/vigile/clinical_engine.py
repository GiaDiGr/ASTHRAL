"""Clinical research layer composed over the existing Engine/Store, never an executor."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from .clinical_models import ClinicalRequest,ClinicalObservation,ClinicalEvaluationResult,ClinicalMetadata
from .clinical_knowledge import ClinicalKnowledge
from .clinical_logic import tree,fields,has_positive,leaf,number,requirements
from .store import digest

UNITS={
 'capillary_glucose_mg_dl':'mg/dL',
 'a1c_percent':'%','fasting_plasma_glucose_mg_dl':'mg/dL','random_plasma_glucose_mg_dl':'mg/dL',
 'plasma_glucose_mg_dl':'mg/dL','ogtt_2h_plasma_glucose_mg_dl':'mg/dL',
 'cgm_interstitial_glucose':'mg/dL','fasting_hours':'h','ogtt_glucose_load_g':'g',
 'beta_hydroxybutyrate_mmol_l':'mmol/L','urine_ketones_plus':'+','venous_pH':'pH',
 'bicarbonate_mmol_l':'mmol/L','potassium_mmol_l':'mmol/L',
 'baseline_sbp_mm_hg':'mmHg','upright_sbp_mm_hg':'mmHg','baseline_dbp_mm_hg':'mmHg','upright_dbp_mm_hg':'mmHg',
 'adult_sbp_mm_hg':'mmHg','upright_window_minutes':'min','delta_hr_bpm':'bpm','symptom_duration_months':'month',
 'serum_creatinine_mg_dl':'mg/dL','baseline_creatinine_mg_dl':'mg/dL',
 'urine_output_ml_kg_h':'mL/kg/h','urine_output_duration_h':'h','anuria_duration_h':'h'}
BOOLS=set('assay_quality.a1c_valid ogtt_2h_timing_valid classic_hyperglycemia_symptoms hyperglycemic_crisis known_diabetes orthostatic_hypotension_present orthostatic_symptoms_frequent symptoms_improve_supine alternative_cause_present acute_onset_minutes_to_hours skin_or_mucosal_involvement respiratory_compromise reduced_bp_or_end_organ_symptoms severe_gi_symptoms known_or_highly_probable_allergen bronchospasm laryngeal_involvement sustained_reduction sustained_hr_rise urine_collection_reliable body_mass_known rrt_initiated dizziness tachycardia postural_trigger irregular_pulse nausea vomiting dehydration recent_blood_loss anemia fever infection pain hyperthyroidism pheochromocytoma cardioactive_or_sympathomimetic_drug severe_deconditioning common_inhalant_trigger food_inhalation_without_ingestion'.split())
BOOLS.update({'altered_mental_or_physical_status','assistance_required_for_hypoglycemia','hypoglycemia_event_clinically_attributed','insulin_or_secretagogue_exposure','recent_reduced_intake','recent_exercise'})
PROTOCOL={'HYPOGLYCEMIA':'PROT-HYPO-REVIEW-2026','DM':'PROT-DM-CONFIRMATION','DKA':'PROT-DKA-ADULT-2024','ORTHOSTATIC_HYPOTENSION':'PROT-OH-POTS-INITIAL','POTS':'PROT-OH-POTS-INITIAL','AKI':'PROT-AKI-INITIAL','ANAPHYLAXIS':'PROT-ANAPH-IM-EPI'}
TEST_FIELDS={
 'HYPOGLYCEMIA':{'TEST-HYPO-GLUCOSE':['plasma_glucose_mg_dl','capillary_glucose_mg_dl'],'TEST-HYPO-CONTEXT':['known_diabetes','altered_mental_or_physical_status','assistance_required_for_hypoglycemia','hypoglycemia_event_clinically_attributed']},
 'DM':{'TEST-PLASMA-GLUCOSE':['fasting_plasma_glucose_mg_dl','random_plasma_glucose_mg_dl']},
 'DKA':{'TEST-PLASMA-GLUCOSE':['plasma_glucose_mg_dl','known_diabetes'],'TEST-BETA-OHB':['beta_hydroxybutyrate_mmol_l','urine_ketones_plus'],'TEST-VENOUS-PH-BICARB':['venous_pH','bicarbonate_mmol_l']},
 'AKI':{'TEST-SERUM-CREATININE':['serum_creatinine_delta_mg_dl_48h','serum_creatinine_ratio_to_baseline_7d'],'TEST-URINE-OUTPUT':['urine_output_ml_kg_h']},
 'POTS':{'TEST-ORTHOSTATIC-BP-HR':['sustained_delta_hr_bpm','orthostatic_hypotension_present'],'TEST-POTS-EXCLUSIONS':['alternative_cause_present']},
 'ORTHOSTATIC_HYPOTENSION':{'TEST-ORTHOSTATIC-BP-HR':['delta_sbp_mm_hg','delta_dbp_mm_hg','sustained_reduction']},
 'ANAPHYLAXIS':{'TEST-ANAPH-CLINICAL':['acute_onset_minutes_to_hours','respiratory_compromise'],'TEST-BP':['adult_sbp_mm_hg']}}

def normalize(request,observations):
    values={}; groups={}; issues=[]; histories={}; unavailable={}
    for raw in observations:
        o=ClinicalObservation.model_validate(raw); reason=None; value=o.value
        if o.concept not in UNITS and o.concept not in BOOLS: reason='UNSUPPORTED_CONCEPT'
        elif o.quality!='VALID': reason='QUALITY_'+o.quality
        elif value is None: reason='QUALITY_NOT_MEASURED'
        elif o.timestamp>request.as_of: reason='FUTURE_OBSERVATION'
        elif o.timestamp<request.window_start and o.concept!='baseline_creatinine_mg_dl': reason='OUTSIDE_DECLARED_WINDOW'
        elif o.concept=='baseline_creatinine_mg_dl' and (request.as_of-o.timestamp).total_seconds()>7*86400: reason='BASELINE_OUTSIDE_7_DAYS'
        elif o.concept in BOOLS:
            if type(value)!=bool or o.unit!='1': reason='BOOLEAN_OR_UNIT_INVALID'
        elif not number(value): reason='NUMERIC_REQUIRED'
        elif o.unit!=UNITS[o.concept]:
            if 'glucose' in o.concept and o.concept!='ogtt_glucose_load_g' and o.unit=='mmol/L': value=float(Decimal(str(value))*18)
            else: reason='INCOMPATIBLE_UNIT'
        if not reason and o.concept in UNITS:
            if value<0 and o.concept!='delta_hr_bpm': reason='NEGATIVE_QUANTITY'
            if o.concept=='venous_pH' and not 0<=value<=14: reason='INVALID_PH_SCALE'
            if 'plasma_glucose' in o.concept and o.method!='VENOUS_PLASMA': reason='DIAGNOSTIC_PLASMA_METHOD_REQUIRED'
            if o.concept=='capillary_glucose_mg_dl' and o.method!='VALIDATED_BLOOD_GLUCOSE_METER': reason='VALIDATED_CAPILLARY_METHOD_REQUIRED'
            if o.concept=='a1c_percent' and o.method!='NGSP_DCCT': reason='A1C_ASSAY_REQUIRED'
            if 'creatinine' in o.concept and o.method!='SERUM_LAB': reason='SERUM_METHOD_REQUIRED'
            if o.concept=='venous_pH' and o.method!='VENOUS_BLOOD_GAS': reason='VENOUS_METHOD_REQUIRED'
        if reason:
            issues.append({'observation_id':o.id,'concept':o.concept,'reason':reason})
            # A newer unusable observation must not silently resurrect an old value.
            unavailable.setdefault(o.concept,[]).append((o.timestamp,reason))
            histories.setdefault('__unavailable__',[]).append({**raw,'_invalid_reason':reason})
            continue
        entry={**raw,'value':value}; histories.setdefault(o.concept,[]).append(entry)
        groups.setdefault(o.concept,[]).append((o.timestamp,o.sample_id,value,o.id))
    for concept,entries in groups.items():
        latest=max(e[0] for e in entries); current=[e for e in entries if e[0]==latest]
        if len({str(e[2]) for e in current})>1:
            issues.append({'concept':concept,'reason':'CONFLICTING_DATA'}); continue
        if any(t>=latest for t,_ in unavailable.get(concept,[])):
            issues.append({'concept':concept,'reason':'LATEST_OBSERVATION_UNAVAILABLE_NO_FALLBACK'})
            continue
        values[concept]=current[0][2]
    for concept,history in histories.items(): history.sort(key=lambda o:(datetime.fromisoformat(o['timestamp']),o['id']))
    if values.get('bronchospasm') is True:
        if values.get('respiratory_compromise') is False: issues.append({'concept':'respiratory_compromise','reason':'CONFLICTING_DATA'})
        else: values['respiratory_compromise']=True
    # Never accept caller-provided derived deltas or impute missing baselines.
    for component in ('sbp','dbp'):
        b=values.get('baseline_'+component+'_mm_hg'); u=values.get('upright_'+component+'_mm_hg')
        if b is not None and u is not None:
            baseline=histories['baseline_'+component+'_mm_hg'][-1]
            upright=histories['upright_'+component+'_mm_hg'][-1]
            if datetime.fromisoformat(baseline['timestamp'])>datetime.fromisoformat(upright['timestamp']):
                issues.append({'concept':'delta_'+component+'_mm_hg','reason':'BASELINE_AFTER_UPRIGHT'})
                continue
            values['delta_'+component+'_mm_hg']=float(Decimal(str(u))-Decimal(str(b)))
    # WAO compares current systolic pressure with baseline, not an orthostatic maneuver.
    b=values.get('baseline_sbp_mm_hg'); current_bp=values.get('adult_sbp_mm_hg')
    if b is not None and current_bp is not None:
        baseline=histories['baseline_sbp_mm_hg'][-1]; current=histories['adult_sbp_mm_hg'][-1]
        if b<=0 or datetime.fromisoformat(baseline['timestamp'])>datetime.fromisoformat(current['timestamp']):
            issues.append({'concept':'sbp_drop_percent','reason':'INVALID_BP_BASELINE'})
        else: values['sbp_drop_percent']=float((Decimal(str(b))-Decimal(str(current_bp)))/Decimal(str(b))*100)
    if values.get('sustained_hr_rise') is True and 'delta_hr_bpm' in values: values['sustained_delta_hr_bpm']=values['delta_hr_bpm']
    if any(values.get(c) is True for c in ('dehydration','recent_blood_loss','anemia','fever','infection','pain','hyperthyroidism','pheochromocytoma','cardioactive_or_sympathomimetic_drug','severe_deconditioning')): values['alternative_cause_present']=True
    if values.get('body_mass_known') is not True or values.get('urine_collection_reliable') is not True:
        if 'urine_output_ml_kg_h' in values: issues.append({'concept':'urine_output_ml_kg_h','reason':'MASS_AND_COLLECTION_VALIDATION_REQUIRED'})
        values.pop('urine_output_ml_kg_h',None); values.pop('anuria_duration_h',None)
    currents=histories.get('serum_creatinine_mg_dl',[]); bases=histories.get('baseline_creatinine_mg_dl',[])
    if currents and bases and 'serum_creatinine_mg_dl' in values and 'baseline_creatinine_mg_dl' in values:
        current=currents[-1]; baseline=bases[-1]
        elapsed=(datetime.fromisoformat(current['timestamp'])-datetime.fromisoformat(baseline['timestamp'])).total_seconds()
        b=Decimal(str(baseline['value'])); c=Decimal(str(current['value']))
        if 0<elapsed<=7*86400 and b>0:
            values['serum_creatinine_ratio_to_baseline_7d']=float(c/b)
            if elapsed<=48*3600: values['serum_creatinine_delta_mg_dl_48h']=float(c-b)
        else: issues.append({'concept':'baseline_creatinine_mg_dl','reason':'BASELINE_NOT_PRIOR_OR_OUTSIDE_WINDOW'})
    return values,issues,histories

def dm_confirmation(criterion,values,histories,invalid=None):
    paths=criterion['logic']['qualifying_paths']
    evaluations=[]; positives=[]; negatives=[]
    for path in paths:
        concept=path['all_of'][0]['field']
        for observation in histories.get(concept,[]):
            sample_values=dict(values); sample_invalid=dict(invalid or {}); context_ids=[]
            same_collection=[o for o in histories.get(concept,[]) if o['sample_id']==observation['sample_id'] and datetime.fromisoformat(o['timestamp'])==datetime.fromisoformat(observation['timestamp'])]
            if len({str(o['value']) for o in same_collection})>1: sample_invalid[concept]=['CONFLICTING_DATA']
            # Fasting/load/assay attestations must belong to this exact collection.
            for contextual in ('fasting_hours','ogtt_glucose_load_g','assay_quality.a1c_valid','ogtt_2h_timing_valid','classic_hyperglycemia_symptoms','hyperglycemic_crisis'):
                candidates=[o for o in histories.get(contextual,[])+[o for o in histories.get('__unavailable__',[]) if o['concept']==contextual] if o['sample_id']==observation['sample_id']]
                sample_values[contextual]=None
                if candidates:
                    latest=max(datetime.fromisoformat(o['timestamp']) for o in candidates)
                    selected=[o for o in candidates if datetime.fromisoformat(o['timestamp'])==latest]
                    context_ids.extend(o['id'] for o in selected)
                    failures=[o['_invalid_reason'] for o in selected if '_invalid_reason' in o]
                    if failures:
                        if any(reason not in ('QUALITY_UNKNOWN','QUALITY_NOT_MEASURED') for reason in failures): sample_invalid[contextual]=failures
                    elif len({str(o['value']) for o in selected})>1: sample_invalid[contextual]=['CONFLICTING_DATA']
                    else: sample_values[contextual]=selected[0]['value']
            sample_values[concept]=observation['value']
            checked_path={'all_of':[path,leaf('ogtt_2h_timing_valid')]} if path['id']=='OGTT' else path
            result=tree(checked_path,sample_values,sample_invalid,path='root/'+path['id']+'/'+observation['id'])
            result.update(path_id=path['id'],sample_id=observation['sample_id'],context_observation_ids=sorted(context_ids)); evaluations.append(result)
            if result['state'] is True: positives.append((path['id'],observation['sample_id'],observation['timestamp']))
            elif result['state'] is False: negatives.append(path['id'])
    # Keep unmeasured alternative paths in the trace, including their context.
    for path in paths:
        if not any(n.get('path_id')==path['id'] for n in evaluations):
            checked={'all_of':[path,leaf('ogtt_2h_timing_valid')]} if path['id']=='OGTT' else path
            absent=tree(checked,values,invalid,path='root/'+path['id'])
            absent['path_id']=path['id'];evaluations.append(absent)
    root={'operator':'ADA_CONFIRMATION','state':None,'path':'root','logic_version':'four-state-1',
          'confirmation_rule':'TWO_DISTINCT_TESTS_OR_REPEAT_SEPARATE_COLLECTIONS_OR_UNEQUIVOCAL_RANDOM',
          'children':evaluations or [tree(p,values,invalid) for p in paths]}
    root['confirmation_evidence']=[{'path_id':p,'sample_id':s,'timestamp':t} for p,s,t in sorted(set(positives))]
    if any(p[0]=='RANDOM_SYMPTOMATIC' for p in positives):
        root['state']=True
        return 'CRITERIA_MET','NOT_REQUIRED',root
    # Two distinct tests same sample or repeated tests distinct samples; duplicate IDs never count.
    unique=set(positives)
    confirmed=any(a[0]!=b[0] or (a[1]!=b[1] and datetime.fromisoformat(a[2])!=datetime.fromisoformat(b[2])) for a in unique for b in unique)
    if confirmed:
        root['state']=True
        return 'CRITERIA_MET','SATISFIED',root
    if unique and negatives: return 'CONFLICTING_EVIDENCE','REQUIRED',root
    if unique: return 'SUSPECTED','REQUIRED',root
    if evaluations and all(n['truth_state']=='FALSE' for n in evaluations):
        root['state']=False
        return 'CRITERIA_NOT_MET','NOT_APPLICABLE',root
    return 'INSUFFICIENT_DATA','REQUIRED',root

def protocol_eligibility(condition,status,values,resources,knowledge):
    pid=PROTOCOL[condition]; p=knowledge.protocols[pid]; reasons=[]
    indication=status=='CRITERIA_MET' or (condition=='DM' and status=='SUSPECTED')
    if status in ('CRITERIA_NOT_MET','NOT_APPLICABLE'): reasons.append('NOT_INDICATED')
    elif not indication: reasons.append('BLOCKED_MISSING_DATA')
    if condition=='DKA':
        potassium=values.get('potassium_mmol_l')
        if potassium is None: reasons.append('BLOCKED_MISSING_DATA:POTASSIUM')
        elif potassium<=3.5: reasons.append('BLOCKED_CONTRAINDICATION:POTASSIUM_NOT_ABOVE_3_5')
    required=p.get('required_resources',[])
    if condition=='ANAPHYLAXIS': required=['epinephrine_inventory','verified_drug_concentration','IM_delivery_capability']
    missing=[name for name in required if resources.get(name) is not True]
    if missing: reasons.append('BLOCKED_RESOURCE')
    # No verified mission authorization provider exists. Unconditionally fail closed.
    reasons.append('BLOCKED_AUTHORIZATION')
    priority=['NOT_INDICATED','BLOCKED_CONTRAINDICATION','BLOCKED_MISSING_DATA','BLOCKED_RESOURCE','BLOCKED_AUTHORIZATION']
    selected=next(state for state in priority if any(r.startswith(state) for r in reasons))
    return {'protocol_id':pid,'indication_supported':indication,'status':selected,'block_reasons':reasons,
            'required_for_protocol_safety':['potassium_mmol_l'] if condition=='DKA' and values.get('potassium_mmol_l') is None else [],
            'missing_resources':missing,'authorization':'NO_VERIFIED_MISSION_POLICY','automatic_execution':False}

def evaluate_condition(condition,request,mission,values,issues,histories,knowledge):
    c=knowledge.criteria[condition]; logic=c['logic']; metadata=ClinicalMetadata().model_dump(); limits=['RESEARCH_ONLY','TERRESTRIAL_CRITERIA_NOT_SPACE_VALIDATION','CRITERIA_NOT_MET_DOES_NOT_EXCLUDE_DISEASE','MANUAL_OBSERVATIONS_USE_DECLARED_WINDOW_NOT_VALIDATED_FRESHNESS','MEASUREMENT_CONTEXT_ATTESTED_NOT_INDEPENDENTLY_VERIFIED','URGENCY_RESEARCH_POLICY_NOT_VALIDATED_TRIAGE']
    derivations={'delta_sbp_mm_hg':['baseline_sbp_mm_hg','upright_sbp_mm_hg'],
      'delta_dbp_mm_hg':['baseline_dbp_mm_hg','upright_dbp_mm_hg'],'sbp_drop_percent':['baseline_sbp_mm_hg','adult_sbp_mm_hg'],
      'serum_creatinine_delta_mg_dl_48h':['baseline_creatinine_mg_dl','serum_creatinine_mg_dl'],
      'serum_creatinine_ratio_to_baseline_7d':['baseline_creatinine_mg_dl','serum_creatinine_mg_dl'],
      'sustained_delta_hr_bpm':['delta_hr_bpm','sustained_hr_rise']}
    metadata['derivation_inputs']={name:[o['id'] for concept in concepts for o in histories.get(concept,[]) if datetime.fromisoformat(o['timestamp'])==max(datetime.fromisoformat(h['timestamp']) for h in histories[concept])] for name,concepts in derivations.items() if name in values}
    if condition=='ORTHOSTATIC_HYPOTENSION':
        logic={'all_of':[logic,leaf('upright_window_minutes',3,'<='),leaf('sustained_reduction')]}
    if condition=='ANAPHYLAXIS':
        # WAO's second bronchospasm pathway excludes common inhalant triggers.
        import copy
        logic=copy.deepcopy(logic)
        branch=logic['any_of'][1]['all_of'][2]['any_of']
        branch[:]=[{'all_of':[n,leaf('common_inhalant_trigger',False),leaf('food_inhalation_without_ingestion',False)]} if n.get('field')=='bronchospasm' else n for n in branch]
    # Quality failures are distinct from absent observations. Valid alternatives may
    # still settle an OR; an unusable decisive path may never settle it as true.
    invalid={}
    for issue in issues:
        concept=issue['concept']
        if issue['reason'] not in ('QUALITY_NOT_MEASURED','QUALITY_UNKNOWN','LATEST_OBSERVATION_UNAVAILABLE_NO_FALLBACK') and (concept not in values or issue['reason']=='CONFLICTING_DATA'):
            invalid.setdefault(concept,[]).append(issue['reason'])
    for name,inputs in derivations.items():
        if name not in values:
            reasons=[reason for concept in inputs for reason in invalid.get(concept,[])]
            if reasons: invalid[name]=['DERIVATION_INPUT_INVALID']+reasons
    evaluated=tree(logic,values,invalid) if condition!='DM' else None
    if condition=='DM': status,confirmation,evaluated=dm_confirmation(c,values,histories,invalid)
    else:
        state=evaluated['state']
        status='CRITERIA_MET' if state is True else 'CRITERIA_NOT_MET' if state is False else 'INSUFFICIENT_DATA'
        support=has_positive(evaluated)
        if condition=='ORTHOSTATIC_HYPOTENSION': support=has_positive(tree(c['logic'],values))
        elif condition=='POTS': support=values.get('delta_hr_bpm',0)>=30 and values.get('orthostatic_symptoms_frequent') is True
        elif condition=='AKI': support=values.get('urine_output_ml_kg_h',999)<.5
        elif condition=='ANAPHYLAXIS': support=any(values.get(f) is True for f in ('skin_or_mucosal_involvement','known_or_highly_probable_allergen','respiratory_compromise'))
        if state is None and support: status='SUSPECTED'
        confirmation='SATISFIED' if state is True else 'NOT_APPLICABLE' if state is False else 'REQUIRED'
        if condition=='ANAPHYLAXIS': confirmation='NOT_REQUIRED' if state is True else 'NOT_APPLICABLE' if state is False else 'PENDING'
    if condition=='DM':
        evaluated['truth_state']='TRUE' if evaluated['state'] is True else 'FALSE' if evaluated['state'] is False else 'INVALID' if any(n.get('truth_state')=='INVALID' for n in evaluated['children']) else 'UNKNOWN'
    requirement_info=requirements(evaluated)
    if any('CONFLICTING_DATA' in invalid.get(f,[]) for f in requirement_info['invalid_required']):
        status='CONFLICTING_EVIDENCE'; confirmation='REQUIRED' 
    urgency='PROMPT' if status in ('INSUFFICIENT_DATA','SUSPECTED','CONFLICTING_EVIDENCE') else 'ROUTINE'
    if condition=='DM' and status=='SUSPECTED': urgency='ROUTINE'
    if condition=='DM' and confirmation=='NOT_REQUIRED': urgency='PROMPT'
    if condition=='DKA':
        urgency='EMERGENCY' if status=='CRITERIA_MET' else 'URGENT' if status=='SUSPECTED' else urgency
        resolution=tree(c['resolution'],values,invalid)
        metadata['resolution_status']='MET' if resolution['state'] is True else 'NOT_MET' if resolution['state'] is False else 'UNKNOWN'
    if condition=='ANAPHYLAXIS':
        danger=any(values.get(f) is True for f in ('respiratory_compromise','bronchospasm','laryngeal_involvement','reduced_bp_or_end_organ_symptoms')) or (values.get('adult_sbp_mm_hg',999)<90)
        if status=='CRITERIA_MET' or (values.get('known_or_highly_probable_allergen') is True and danger): urgency='EMERGENCY'
        elif status!='INSUFFICIENT_DATA': urgency='PROMPT'
    if condition=='ORTHOSTATIC_HYPOTENSION' and status=='CRITERIA_MET': urgency='PROMPT'
    if condition=='POTS' and values.get('alternative_cause_present') is True: urgency='PROMPT'
    if condition=='AKI' and status=='CRITERIA_MET':
        urgency='URGENT'; stage=1
        ratio=values.get('serum_creatinine_ratio_to_baseline_7d',0); uo=values.get('urine_output_ml_kg_h',999); hours=values.get('urine_output_duration_h',0)
        if ratio>=2 or (uo<.5 and hours>=12): stage=2
        if ratio>=3 or (values.get('serum_creatinine_mg_dl',0)>=4 and (ratio>=1.5 or values.get('serum_creatinine_delta_mg_dl_48h',0)>=.3)) or values.get('rrt_initiated') is True or (uo<.3 and hours>=24) or values.get('anuria_duration_h',0)>=12: stage=3
        metadata['aki_stage']=stage; metadata['aki_stage_is_minimum_supported']=True
    if condition=='HYPOGLYCEMIA':
        glucose=[values[f] for f in ('plasma_glucose_mg_dl','capillary_glucose_mg_dl') if f in values and f not in invalid]
        severe=all(values.get(f) is True and f not in invalid for f in ('altered_mental_or_physical_status','assistance_required_for_hypoglycemia','hypoglycemia_event_clinically_attributed'))
        level=3 if severe else 2 if glucose and min(glucose)<54 else 1 if glucose and min(glucose)<70 else None
        urgency='EMERGENCY' if severe else 'URGENT' if level else urgency
        if status=='CRITERIA_MET': metadata['hypoglycemia_level_minimum_supported']=level
        if values.get('known_diabetes') is False:
            status='NOT_APPLICABLE'; confirmation='NOT_APPLICABLE'
        limits+=['RESTRICTED_TO_KNOWN_DIABETES','HYPOGLYCEMIA_CLASSIFICATION_NOT_ETIOLOGY','LEVEL_3_REQUIRES_CLINICAL_ATTRIBUTION','CGM_ALONE_NOT_USED','REEVALUATE_WITH_NEW_BLOOD_GLUCOSE_NO_AUTOMATIC_RECOVERY']
    if request.population=='UNKNOWN' or (condition=='DM' and request.population!='NONPREGNANT_ADULT'):
        status='INSUFFICIENT_DATA'; confirmation='REQUIRED'; limits.append('POPULATION_NOT_ESTABLISHED')
    if condition=='POTS' and (request.age_years is None or request.age_years<20):
        status='INSUFFICIENT_DATA' if request.age_years is None else 'NOT_APPLICABLE'
        confirmation='REQUIRED' if request.age_years is None else 'NOT_APPLICABLE'
        limits.append('ADULT_20_PLUS_PATH_ONLY_12_TO_19_THRESHOLD_NOT_IMPLEMENTED')
    if any(not knowledge.usable(s) for s in c['source_ids']):
        status='INSUFFICIENT_DATA'; confirmation='UNAVAILABLE'; limits.append('SOURCE_NOT_USABLE')
    space=c.get('space_applicability','REQUIRES_SPACE_SPECIFIC_VALIDATION')
    if condition in ('POTS','ORTHOSTATIC_HYPOTENSION'):
        if mission['gravity']=='MICROGRAVITY': status='NOT_APPLICABLE'; confirmation='NOT_APPLICABLE'; space='NOT_APPLICABLE'; urgency='ROUTINE'; limits.append('STANDARD_UPRIGHT_TEST_UNSUPPORTED_IN_FREE_MICROGRAVITY')
        elif mission['gravity']=='PARTIAL': status='INSUFFICIENT_DATA'; confirmation='UNAVAILABLE'; limits.append('PARTIAL_GRAVITY_VALIDATION_REQUIRED')
        else: space='APPLICABLE_WITH_LIMITATIONS'
    if status!='CRITERIA_MET': metadata['aki_stage']=None; metadata['aki_stage_is_minimum_supported']=False
    if status!='CRITERIA_MET': metadata['hypoglycemia_level_minimum_supported']=None
    protocol=protocol_eligibility(condition,status,values,request.resources,knowledge)
    return ClinicalEvaluationResult(condition_id=condition,diagnostic_status=status,urgency=urgency,confirmation_status=confirmation,
      protocol_status=protocol['status'],criterion_id=c['criterion_id'],criterion_version=c['version'],source_ids=c['source_ids'],
      source_statuses={s:knowledge.source_status(s) for s in c['source_ids']},evaluation_tree=evaluated,
      missing_fields=fields(evaluated),**requirement_info,required_for_protocol_safety=protocol['required_for_protocol_safety'],data_issues=issues,space_applicability=space,limitations=limits,protocol=protocol,metadata=metadata).model_dump(mode='json')

class ClinicalService:
    def __init__(self,engine,knowledge=None): self.engine=engine; self.store=engine.store; self.knowledge=knowledge or ClinicalKnowledge()
    def snapshot(self,request):
        from .mission_context import mission_at
        profile=self.store.get('profile',request.subject_id); mission=mission_at(self.store,request.mission_id,request.as_of)
        if profile['mission_id']!=request.mission_id: raise ValueError('CLINICAL_SCOPE_MISMATCH')
        observations=[o.model_dump(mode='json') for o in request.observations]; bindings=[]
        for binding in request.measurement_bindings:
            raw=self.engine.measurement(binding.measurement_id)
            if (raw.subject_id,raw.mission_id)!=(request.subject_id,request.mission_id): raise ValueError('CLINICAL_MEASUREMENT_SCOPE_MISMATCH')
            if raw.variable!=binding.concept and not (raw.variable=='serum_creatinine_mg_dl' and binding.concept=='baseline_creatinine_mg_dl'): raise ValueError('MEASUREMENT_CONCEPT_MISMATCH')
            quality='VALID'; reason=None
            from .quality import Inconclusive
            try: self.engine.checked(raw.id,request.as_of,historical=(binding.concept=='baseline_creatinine_mg_dl'))
            except Inconclusive as exc: quality='INVALID'; reason=str(exc)
            observations.append(ClinicalObservation(id=raw.id,concept=binding.concept,value=raw.value,unit=raw.unit,
              timestamp=raw.timestamp,quality=quality,method=raw.method,sample_id=binding.sample_id,provenance=raw.provenance).model_dump(mode='json'))
            bindings.append({'measurement':raw.model_dump(mode='json'),'device':self.store.get('device',raw.device_id),'quality_reason':reason})
        if len({o['id'] for o in observations})!=len(observations): raise ValueError('DUPLICATE_OBSERVATION_ID')
        snapshot={'request':request.model_dump(mode='json'),'observations':observations,'profile':profile,'mission':mission,'measurement_records':bindings}
        if request.resource_policy=='MISSION_INVENTORY' and not (profile['synthetic'] and mission['synthetic']):raise ValueError('SYNTHETIC_INVENTORY_CONTEXT_REQUIRED')
        if profile['synthetic'] and mission['synthetic']:
            from .management import inventory_snapshot
            snapshot['resource_snapshot']=inventory_snapshot(self.store,request.mission_id,request.as_of,request.resource_policy,request.resources)
        return snapshot
    def compute(self,snapshot):
        from .clinical_differential import differential
        request=ClinicalRequest.model_validate(snapshot['request'])
        if snapshot.get('resource_snapshot',{}).get('policy')=='MISSION_INVENTORY':
            from .management import resolved_flags
            request=request.model_copy(update={'resources':resolved_flags(snapshot['resource_snapshot'],self.knowledge)})
        values,issues,histories=normalize(request,snapshot['observations'])
        routes=[request.condition_id] if request.condition_id else list(self.knowledge.criteria)
        if 'POTS' in routes:
            oh=evaluate_condition('ORTHOSTATIC_HYPOTENSION',request,snapshot['mission'],values,issues,histories,self.knowledge)
            if oh['diagnostic_status']=='CRITERIA_MET':
                values['orthostatic_hypotension_present']=True
                issues=issues+[{'concept':'orthostatic_hypotension_present','reason':'DERIVED_OH_CRITERIA_EXCLUDE_POTS'}]
        results={c:evaluate_condition(c,request,snapshot['mission'],values,issues,histories,self.knowledge) for c in routes}
        ranked,tests=differential(request,results,values,self.knowledge)
        urgency_order=['ROUTINE','PROMPT','URGENT','EMERGENCY']
        urgency=max([r['urgency'] for r in results.values()]+[r['urgency'] for r in ranked],key=urgency_order.index)
        presentation_protocol=None
        if request.presentation_id=='PRES-DIZZINESS-TACHYCARDIA':
            indicated=values.get('dizziness') is True and values.get('tachycardia') is True
            presentation_protocol={'protocol_id':'PROT-DIZZINESS-TACHY-TRIAGE','indication_supported':indicated,
              'status':'BLOCKED_AUTHORIZATION' if indicated else 'BLOCKED_MISSING_DATA',
              'block_reasons':(['BLOCKED_MISSING_DATA'] if not indicated else [])+['BLOCKED_AUTHORIZATION'],
              'authorization':'NO_VERIFIED_MISSION_POLICY','automatic_execution':False}
        output={'results':results,'differential':ranked,'next_tests':tests,'urgency':urgency,'treatment_status':'NOT_STARTED','presentation_protocol':presentation_protocol}
        if 'resource_snapshot' in snapshot:
            from .management import management_view
            output['management']=management_view(snapshot,output,self.knowledge)
        return output
    def evaluate(self,request,actor,parent_id=None,identifier=None):
        with self.store.transaction():
            return self._evaluate_frozen(request,actor,parent_id,identifier)
    def _evaluate_frozen(self,request,actor,parent_id=None,identifier=None):
        if parent_id:
            parent=self.store.get('clinical_evaluation',parent_id)
            if (parent['subject_id'],parent['mission_id'])!=(request.subject_id,request.mission_id): raise ValueError('REEVALUATION_SCOPE_MISMATCH')
            prior=parent['snapshot']['request']
            if (prior['condition_id'],prior['presentation_id'])!=(request.condition_id,request.presentation_id): raise ValueError('REEVALUATION_ROUTE_MISMATCH')
            if request.as_of<datetime.fromisoformat(parent['snapshot']['request']['as_of']): raise ValueError('REEVALUATION_TIME_REVERSED')
        snapshot=self.snapshot(request); result=self.compute(snapshot); identifier=identifier or 'ce-'+uuid4().hex
        record={'id':identifier,'subject_id':request.subject_id,'mission_id':request.mission_id,'parent_id':parent_id,
         **result,'snapshot':snapshot,'input_hash':digest(snapshot),'knowledge_hash':self.knowledge.hash,
         'knowledge_version':self.knowledge.manifest['version'],'implementation_hash':self.engine.implementation_hash,'output_hash':digest(result)}
        self.store.put('clinical_evaluation',identifier,record,actor)
        return self.projection(record)
    def projection(self,record): return {k:v for k,v in record.items() if k not in ('snapshot','subject_id','mission_id')}
    def replay(self,identifier):
        r=self.store.get('clinical_evaluation',identifier)
        if r['knowledge_hash']!=self.knowledge.hash or r['implementation_hash']!=self.engine.implementation_hash: raise ValueError('REPLAY_VERSION_MISMATCH')
        if digest(r['snapshot'])!=r['input_hash']: raise ValueError('REPLAY_INPUT_HASH_MISMATCH')
        stored_output={k:r[k] for k in ('results','differential','next_tests','urgency','treatment_status','presentation_protocol')}
        if 'management' in r:stored_output['management']=r['management']
        if digest(stored_output)!=r['output_hash']: raise ValueError('REPLAY_STORED_OUTPUT_HASH_MISMATCH')
        output=self.compute(r['snapshot'])
        return {'id':identifier,'matches':digest(output)==r['output_hash'],'input_hash':r['input_hash'],'knowledge_hash':self.knowledge.hash}
