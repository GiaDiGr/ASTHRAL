"""Report-fixture adapter. Synthetic transport scaffolding is never clinical evidence."""
from datetime import datetime,timedelta,timezone
from .clinical_engine import UNITS,BOOLS
from .clinical_models import ClinicalObservation,ClinicalRequest
from .clinical_knowledge import ClinicalKnowledge

AS_OF=datetime(2026,10,16,12,tzinfo=timezone.utc)
def observation(concept,value,*,timestamp=AS_OF,sample='collection',identifier=None,unit=None,method=None,quality='VALID'):
    if method is None:
        method='VENOUS_PLASMA' if 'plasma_glucose' in concept else 'SERUM_LAB' if 'creatinine' in concept else 'VENOUS_BLOOD_GAS' if concept=='venous_pH' else 'NGSP_DCCT' if concept=='a1c_percent' else 'SYNTHETIC_OBSERVATION'
    return ClinicalObservation(id=identifier or concept.replace('.','-')+'-'+sample,concept=concept,value=value,
        timestamp=timestamp,sample_id=sample,unit=unit or UNITS.get(concept,'1'),method=method,quality=quality,provenance='SYNTHETIC_REPORT_ADAPTER_NOT_CLINICAL_VALIDATION')

def report_case(case,subject_id='clinical-crew',mission_id='clinical-earth'):
    inputs=case['inputs']; observations=[]; resources={}
    def add(c,v,**kw):
        if v is not None: observations.append(observation(c,v,**kw))
    aliases={'classic_symptoms':'classic_hyperglycemia_symptoms','baseline_sbp':'baseline_sbp_mm_hg','standing_sbp':'upright_sbp_mm_hg',
      'standing_time_min':'upright_window_minutes','orthostatic_hypotension':'orthostatic_hypotension_present',
      'orthostatic_symptoms':'orthostatic_symptoms_frequent','improve_supine':'symptoms_improve_supine','duration_months':'symptom_duration_months',
      'alternative_cause':'alternative_cause_present','creatinine_current_mg_dl':'serum_creatinine_mg_dl','duration_h':'urine_output_duration_h',
      'acute':'acute_onset_minutes_to_hours','skin_mucosal':'skin_or_mucosal_involvement','known_allergen':'known_or_highly_probable_allergen',
      'probable_allergen':'known_or_highly_probable_allergen','adult_sbp':'adult_sbp_mm_hg','respiratory':'respiratory_compromise',
      'hypotension':'reduced_bp_or_end_organ_symptoms','severe_gi':'severe_gi_symptoms','repetitive_vomiting':'severe_gi_symptoms',
      'postural':'postural_trigger','postural_relation':'postural_trigger','postural_delta_hr':'delta_hr_bpm',
      'vomiting_last_24h':'vomiting','persistent_tachycardia':'tachycardia','dyspnea':'respiratory_compromise'}
    for k,v in inputs.items():
        concept=aliases.get(k,k)
        if concept in UNITS or concept in BOOLS:
            if isinstance(v,dict): add(concept,v.get('value'),unit=v.get('unit'),quality='VALID' if v.get('valid',True) else 'INVALID')
            else: add(concept,v)
    for n,test in enumerate(inputs.get('fpg',[])):
        when=AS_OF-timedelta(days=len(inputs['fpg'])-n-1); sample='fpg-'+str(n)
        add('fasting_plasma_glucose_mg_dl',test['value'],unit=test['unit'],timestamp=when,sample=sample,quality='VALID' if test['valid'] else 'INVALID')
        add('fasting_hours',test['fasting_h'],timestamp=when,sample=sample)
    if 'random_plasma_glucose' in inputs:
        test=inputs['random_plasma_glucose'];add('random_plasma_glucose_mg_dl',test['value'],unit=test['unit'],quality='VALID' if test['valid'] else 'INVALID')
    for key,prefix in [('baseline_bp','baseline'),('bp_at_2min','upright'),('standing_bp','upright')]:
        if inputs.get(key):
            sbp,dbp=map(float,inputs[key].split('/'));add(prefix+'_sbp_mm_hg',sbp);add(prefix+'_dbp_mm_hg',dbp)
    if inputs.get('bp_at_2min'): add('upright_window_minutes',2)
    if inputs.get('within_10_min') is True: add('upright_window_minutes',10)
    if inputs.get('creatinine_baseline_mg_dl') is not None:
        elapsed=inputs.get('elapsed_h',inputs.get('elapsed_days',0)*24)
        add('baseline_creatinine_mg_dl',inputs['creatinine_baseline_mg_dl'],timestamp=AS_OF-timedelta(hours=elapsed),sample='prior')
    if 'symptom_duration_days' in inputs:
        # No invented month conversion: a one-day history cannot meet three months.
        if inputs['symptom_duration_days']==1: add('symptom_duration_months',0)
    if 'epinephrine_inventory_verified' in inputs: resources['epinephrine_inventory']=inputs['epinephrine_inventory_verified']
    route=case['route']; condition=None; presentation=None
    if route=='DM_DKA': condition='DKA' if case['id'] in ('DM-05','DM-06') else 'DM'
    elif route=='OH_POTS': condition='POTS' if case['id'] in ('ORTHO-04','ORTHO-05') else 'ORTHOSTATIC_HYPOTENSION'
    elif route=='AKI': condition='AKI'
    elif case['id'].startswith('ANAPH'): condition='ANAPHYLAXIS'
    else: presentation='PRES-DIZZINESS-TACHYCARDIA'
    # Explicit synthetic-only demographics and timestamps supply transport requirements,
    # never absent clinical findings (sustained fall, collection reliability, acute onset).
    return ClinicalRequest(subject_id=subject_id,mission_id=mission_id,condition_id=condition,presentation_id=presentation,
      population='NONPREGNANT_ADULT',age_years=30,as_of=AS_OF,window_start=AS_OF-timedelta(days=7),observations=observations,resources=resources)
