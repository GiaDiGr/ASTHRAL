"""Ordinal differential only; incomplete external branches cannot diagnose."""
from .clinical_engine import TEST_FIELDS

def differential(request,results,v,knowledge):
    definitions=[]
    if request.presentation_id:
        definitions=list(knowledge.presentations[request.presentation_id]['hypotheses'])
        # Explicit cross-presentation routing, not new criteria.
        if request.presentation_id=='PRES-DIZZINESS-TACHYCARDIA':
            definitions += [{'id':'AKI','time_critical':False},{'id':'HYPOVOLEMIA','time_critical':False,'criteria_implemented_here':False}]
    else: definitions=[{'id':request.condition_id,'time_critical':request.condition_id in ('DKA','ANAPHYLAXIS','HYPOGLYCEMIA')}]
    if request.presentation_id=='PRES-DIZZINESS-TACHYCARDIA': definitions.append({'id':'HYPOGLYCEMIA','time_critical':True})
    supports={
      'HYPOGLYCEMIA':(['LOW_MEASURED_BLOOD_GLUCOSE'] if any(f in v and v[f]<70 for f in ('plasma_glucose_mg_dl','capillary_glucose_mg_dl')) else []),
      'ANAPHYLAXIS':[f for f in ('known_or_highly_probable_allergen','bronchospasm','laryngeal_involvement','skin_or_mucosal_involvement') if v.get(f) is True],
      'DKA':[f for f in ('known_diabetes','nausea','dehydration') if v.get(f) is True]+(['plasma_glucose_mg_dl'] if v.get('plasma_glucose_mg_dl',0)>=200 else []),
      'POTS':[f for f in ('postural_trigger','orthostatic_symptoms_frequent') if v.get(f) is True],
      'ORTHOSTATIC_HYPOTENSION':['postural_trigger'] if v.get('postural_trigger') is True else [],
      'HYPOVOLEMIA':[f for f in ('dehydration','recent_blood_loss') if v.get(f) is True],
      'EXTERNAL_ARRHYTHMIA_PATHWAY':['irregular_pulse'] if v.get('irregular_pulse') is True else []}
    rows=[]
    for definition in definitions:
        condition={'DIABETES':'DM'}.get(definition['id'],definition['id']); result=results.get(condition)
        support=supports.get(condition,[]); contradictions=[]; status=result['diagnostic_status'] if result else 'NOT_EVALUATED'
        if condition=='POTS':
            contradictions=[f for f in ('dehydration','anemia','infection','severe_deconditioning','orthostatic_hypotension_present','alternative_cause_present') if v.get(f) is True]
            if results.get('ORTHOSTATIC_HYPOTENSION',{}).get('diagnostic_status')=='CRITERIA_MET': contradictions.append('ORTHOSTATIC_HYPOTENSION')
        critical=definition.get('time_critical',False)
        if contradictions or status=='CRITERIA_NOT_MET': tier='CONTRADICTED'
        elif status=='CRITERIA_MET': tier='TIME_CRITICAL_CRITERIA_MET' if critical else 'CRITERIA_MET'
        elif critical and support and (not result or result['urgency'] in ('URGENT','EMERGENCY')): tier='TIME_CRITICAL_SUSPECTED'
        elif condition=='HYPOVOLEMIA' and support: tier='HIGH_PRIORITY_UNRESOLVED'
        elif support or status=='SUSPECTED': tier='COMPATIBLE'
        else: tier='NOT_EVALUABLE'
        rows.append({'condition_id':condition,'reported_condition_id':definition['id'],'tier':tier,'diagnostic_status':status,
          'support':support,'contradictions':contradictions,'criteria_implemented':condition in knowledge.criteria,
          'source_ids':result['source_ids'] if result else [],'external_evaluation_required':condition not in knowledge.criteria,
          'urgency':result['urgency'] if result else 'URGENT' if critical and support else 'PROMPT'})
    order=knowledge.documents['differential_rules']['ranking']; rows.sort(key=lambda r:(order.index(r['tier']),r['condition_id']))
    tests={}
    for row in rows:
        condition=row['condition_id']; result=results.get(condition)
        if row['tier']=='CONTRADICTED': continue
        if request.presentation_id and row['tier']=='NOT_EVALUABLE': continue
        if result and result['diagnostic_status'] in ('CRITERIA_MET','NOT_APPLICABLE'): continue
        candidates=TEST_FIELDS.get(condition,{})
        if condition=='EXTERNAL_ARRHYTHMIA_PATHWAY' and row['support']: candidates={'TEST-ECG':[]}
        for test,concepts in candidates.items():
            unresolved=set(result['missing_required']+result['invalid_required']) if result else set()
            if concepts and not (set(concepts)&unresolved) and not (condition=='DM' and result['confirmation_status']=='REQUIRED'): continue
            if test not in knowledge.tests: continue
            item=tests.setdefault(test,{'test_id':test,'reasons':[],'urgency':row['urgency'],
               'availability':request.resources.get(test),'risk':'NOT_SPECIFIED_IN_REPORT','cost':'NOT_SPECIFIED_IN_REPORT','execution_authorized':False})
            item['reasons'].append({'condition_id':condition,'reason':'CONFIRMATION_OR_MISSING_DISCRIMINATING_DATA','concepts':concepts,'unresolved_candidates':sorted(set(concepts)&unresolved),'purpose':'DIAGNOSTIC_RESOLUTION','alternatives_follow_evaluation_tree':True})
            ranks=['EMERGENCY','URGENT','PROMPT','ROUTINE']
            if ranks.index(row['urgency'])<ranks.index(item['urgency']): item['urgency']=row['urgency']
    tests=sorted(tests.values(),key=lambda t:(['EMERGENCY','URGENT','PROMPT','ROUTINE'].index(t['urgency']),t['availability'] is not True,t['test_id']))
    dka=results.get('DKA')
    if dka and dka['diagnostic_status'] in ('CRITERIA_MET','SUSPECTED') and v.get('potassium_mmol_l') is None:
        tests.insert(0,{'test_id':None,'action':'OBTAIN_POTASSIUM_SAFETY_DATA','catalogue_status':'TEST_ID_NOT_DEFINED_IN_REPORT',
          'reasons':[{'condition_id':'DKA','reason':'PROTOCOL_REQUIRES_POTASSIUM','purpose':'PROTOCOL_SAFETY','source_ids':dka['source_ids']}],
          'urgency':dka['urgency'],'availability':request.resources.get('potassium_measurement'),'risk':'NOT_SPECIFIED_IN_REPORT',
          'cost':'NOT_SPECIFIED_IN_REPORT','execution_authorized':False})
    hypo=results.get('HYPOGLYCEMIA')
    if hypo and hypo['metadata'].get('hypoglycemia_level_minimum_supported'):
        tests.append({'test_id':'TEST-HYPO-RECHECK','reasons':[{'condition_id':'HYPOGLYCEMIA','reason':'REPEAT_BLOOD_GLUCOSE_AND_REVIEW_CAUSE_TIMING_REQUIRES_PROTOCOL','purpose':'DIAGNOSTIC_RESOLUTION','source_ids':hypo['source_ids']}], 'urgency':hypo['urgency'],'availability':request.resources.get('TEST-HYPO-RECHECK'),'risk':'CONTEXT_REQUIRED','cost':'NOT_SPECIFIED','execution_authorized':False})
        for concept,name in [('insulin_or_secretagogue_exposure','MEDICATION_ASSOCIATED_HYPOGLYCEMIA'),('recent_reduced_intake','REDUCED_INTAKE_ASSOCIATED'),('recent_exercise','EXERCISE_ASSOCIATED')]:
            if v.get(concept) is True:
                rows.append({'condition_id':name,'reported_condition_id':name,'tier':'COMPATIBLE','diagnostic_status':'NOT_EVALUATED','support':[concept],'contradictions':[],'criteria_implemented':False,'source_ids':hypo['source_ids'],'external_evaluation_required':True,'urgency':hypo['urgency']})
    return rows,tests
