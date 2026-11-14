"""Read-only monitoring explanation. The model never supplies clinical state."""
import json,re,unicodedata
import httpx
from .knowledge_v08 import terms,INJECTION
from .local_assistant import evidence_blocks
from .conversational import DENIED,validate_generated

ACTION=re.compile(r'diagn[oó]sticame|diagnose me|confirma.{0,25}diagn[oó]stico|que dosis|cu[aá]nta insulina|how (?:do i|to).{0,20}(?:treat|dose)|prescribe|administ(?:ra|er)|ignore|ignora|reveal.{0,20}(?:token|secret)',re.I)

def monitoring_blocks(run,previous=None):
    english=False;blocks=[]
    def add(category,text,**ref):
        blocks.append({'id':'M'+str(len(blocks)+1),'kind':'ENGINE','category':category,'text':text,
          'reference':{'run_id':run['id'],'as_of':run['as_of'],'output_hash':run['output_hash'],**ref}})
    add('LIMITATION','Monitorización experimental / Experimental monitoring. Cambios numéricos no equivalen a empeoramiento clínico / numeric changes are not clinical worsening. No diagnóstico firmado, no tratamiento autorizado. / No signed diagnosis or treatment authorization.')
    for d in run['domains']:
        add('DATA_SUFFICIENCY',f"{d['domain']}: indicadores faltantes / missing indicators: {', '.join(d['missing_indicators']) or 'ninguno / none'}. Fase / phase: {d['phase']}; gravedad / gravity: {d['gravity']}.",domain=d['domain'],source_ids=d['source_ids'])
        add('LIMITATION',f"{d['domain']}: limitaciones / limitations: {', '.join(d['limitations'])}.",domain=d['domain'],source_ids=d['source_ids'])
        for i in d['indicators']:
            if i['latest_measurement_id'] is None:continue
            add('DESCRIPTIVE',f"{i['variable']}: estado / state {i['state']}; valor / value {i['value']} {i['unit']}. Calidad / quality: {json.dumps(i['quality_issues'],ensure_ascii=False)}.",variable=i['variable'],measurement_id=i['latest_measurement_id'],source_ids=i['source_ids'])
            if i['baseline_comparison']:
                b=i['baseline_comparison'];add('BASELINE',f"{i['variable']}: baseline {b['baseline_value']} {i['unit']}; cambio absoluto / absolute change {b['absolute_change']}; retención / retention {b['retention_percent']}%. Descriptivo, no diagnóstico / descriptive, not diagnosis.",variable=i['variable'],baseline_id=b['baseline_id'],source_ids=i['source_ids'])
            if i['trend']:add('TREND',f"{i['variable']}: pendiente / slope {i['trend']['slope_per_day']} {i['unit']}/day; EWMA/CUSUM por observación / per observation; {i['trend']['status']}. No umbral clínico / no clinical threshold.",variable=i['variable'],source_ids=i['source_ids'])
        if d.get('accumulated_dose'):
            dose=d['accumulated_dose'];add('RADIATION',f"Radiación / radiation: {dose['state']}; dosis efectiva registrada / recorded effective dose {dose['effective_dose_mSv']} mSv; cobertura / coverage {dose['coverage_seconds']} seconds. Solo intervalos registrados, no dosis de vida ni diagnóstico / recorded intervals only, not lifetime dose or diagnosis.",source_ids=d['source_ids'])
    for e in run['events']:
        add('ALERT',f"Evento o alerta / alert event {e['key']}: {e['state']}; prioridad / priority {e['urgency']}; nueva notificación / notify {e['notify']}; motivo / reason {e['reason']}; clase / kind {e['kind']}. No diagnóstico / not a diagnosis.",event_id=e['id'],source_ids=e['source_ids'])
    add('FOLLOWUP',f"Episodios / episodes: {json.dumps(run['episode_ids'])}; planes nuevos / new followups: {', '.join(run['followup_ids']) or 'ninguno / none'}. Sin cierre ni recuperación automática / no automatic closure or recovery.")
    if previous:
        old={i['variable']:i for d in previous['domains'] for i in d['indicators']}
        changes=[{'variable':i['variable'],'previous':old.get(i['variable'],{}).get('value'),'current':i['value'],'previous_state':old.get(i['variable'],{}).get('state'),'current_state':i['state']} for d in run['domains'] for i in d['indicators'] if any(i.get(k)!=old.get(i['variable'],{}).get(k) for k in ('value','state'))]
        for change in changes:add('CHANGE','Cambio desde revisión anterior / change since previous review: '+json.dumps(change,ensure_ascii=False),previous_run_id=previous['id'])
        if not changes:add('CHANGE','Sin cambios de valores/estados de indicadores / no changes in indicator values or states.',previous_run_id=previous['id'])
    else:add('CHANGE','No hay ciclo anterior para comparar / no previous cycle available.')
    return blocks

def answer_monitoring(reader,inference,run_id,question,history=(),library=None):
    run=reader.get('/monitoring/cycles/'+run_id)
    previous=reader.get('/monitoring/cycles/'+run['previous_run_id']) if run.get('previous_run_id') else None
    if previous and (previous['subject_id'],previous['mission_id'])!=(run['subject_id'],run['mission_id']):raise ValueError('PREVIOUS_RUN_SCOPE_MISMATCH')
    blocks=monitoring_blocks(run,previous)
    for ev in run['clinical_evaluations'].values():
        for b in evidence_blocks(ev,reader):
            b={**b,'id':'C-'+str(len(blocks)+1),'category':'CLINICAL_CRITERIA' if b['kind']=='ENGINE' else 'IMPLEMENTED_CRITERION'};blocks.append(b)
    query=terms(question);focus=set()
    if 'missing' in query or 'quality' in query:focus={'DATA_SUFFICIENCY','DESCRIPTIVE','CLINICAL_CRITERIA'}
    elif 'alert' in query:focus={'ALERT','CLINICAL_CRITERIA'}
    elif 'baseline' in query or 'cardiovascular' in query:focus={'BASELINE','TREND','CHANGE'}
    elif 'trend' in query:focus={'CHANGE','BASELINE','TREND'}
    elif 'microgravity' in query:focus={'LIMITATION'}
    elif 'radiation' in query:focus={'RADIATION'}
    elif 'protocol' in query or 'hypoglycemia' in query:focus={'CLINICAL_CRITERIA','FOLLOWUP','LIMITATION'}
    ranked=sorted(blocks,key=lambda b:(b['category'] not in focus,-len(query&terms(b['text'])),b['id']))
    # A compound request must retain a representative of each requested dimension.
    matched=[b for b in ranked if b['category'] in focus or query&terms(b['text'])]
    representatives=[next((b for b in matched if b['category']==category),None) for category in sorted(focus)]
    representatives=[b for b in representatives if b is not None]
    relevant=(representatives+[b for b in matched if b not in representatives])[:10]
    # Always preserve the distinction between monitoring and diagnosis, independently of generation.
    selected=[blocks[0]]+[b for b in relevant if b['id']!=blocks[0]['id']]
    documents,issues=library.search(question,3 if getattr(inference,'mode','FULL')=='FULL' else 1) if library else ([],['DOCUMENT_LIBRARY_NOT_CONFIGURED'])
    from .local_assistant import tokens
    lexical=tokens(question)
    tests_query=bool(lexical & {'test','prueba'})
    documents_query=bool(lexical & {'document','documento','fuente','source','referencia','reference'})
    if tests_query:
        recommendations=[b for b in blocks if b['kind']=='ENGINE' and (b['text'].startswith('Prueba recomendada') or ': suficiencia de datos.' in b['text'])]
        if recommendations:
            relevant=recommendations;selected=[blocks[0]]+recommendations
    if documents_query:
        # Existing implemented criteria are documentary context, never patient decisions.
        criteria_documents=[b for b in blocks if b['kind']=='DOCUMENT']
        if library and not documents and run['clinical_evaluations']:
            documents,issues=library.search(' '.join(run['clinical_evaluations']),3 if getattr(inference,'mode','FULL')=='FULL' else 1)
        documents=criteria_documents+documents
    documents=[b for b in documents if not INJECTION.search(b['text'])]
    result={'status':'EXTRACTIVE_ONLY','run_id':run_id,'evaluation_id':None,'as_of':run['as_of'],'mode':getattr(inference,'mode','FULL'),
      'message':'Resultados del motor separados de documentación y texto generado. / Engine results are separate from documents and generated text.',
      'answer':selected,'retrieved':selected+documents,'generated':[],'documents':documents,'document_issues':issues,
      'sources':[b['reference'] for b in documents],'inference_attempted':False,'inference_executed':False,
      'clinical_execution':'BLOCKED','authority':'DETERMINISTIC_ENGINE_ONLY','clinical_validation':False,
      'limitations':['DOCUMENTS_DO_NOT_OVERRIDE_ENGINE','SEMANTIC_VERIFICATION_IS_NOT_CLINICAL_VALIDATION','UNKNOWN_UNDETECTED_ERRORS_REQUIRE_INDEPENDENT_REVIEW']}
    from .assistant_safety import request_guard
    guard=request_guard(question,run['subject_id'],run['mission_id'])
    result['context']={'subject_id':run['subject_id'],'mission_id':run['mission_id'],'target_id':run_id}
    if guard:
        result.update(status=guard,message='Solicitud no sustentada, accion no permitida o contexto incompatible; no se genera una respuesta clinica.');return result
    normalized=''.join(c for c in unicodedata.normalize('NFKD',question) if not unicodedata.combining(c))
    # Reading a recorded radiation dose is not a request to prescribe a dose.
    action_text=normalized
    if re.search(r'\bdosis de radiacion (?:esta registrada|registrada|acumulada|medida)\b',normalized,re.I):
        action_text=re.sub(r'\bque dosis\b','cantidad registrada',normalized,flags=re.I)
    if DENIED.search(normalized) or ACTION.search(action_text):
        result.update(status='REFUSED_ACTION',message='No puedo diagnosticar, prescribir, cambiar resultados ni revelar credenciales. / I cannot diagnose, prescribe, change results or disclose credentials.');return result
    if documents_query and documents:
        result.update(status='DOCUMENT_EXCERPTS_ONLY',message='Documentación recuperada y criterios implementados; no es generación ni una decisión clínica. / Retrieved documentation and implemented criteria; no generated explanation or clinical decision.')
        return result
    if tests_query and relevant:
        result.update(status='DETERMINISTIC_TEST_RECOMMENDATIONS',consistency_policy='EXISTING_ENGINE_TESTS_ONLY',message='Pruebas y suficiencia tomadas del resultado registrado; no son órdenes autorizadas. / Tests and data sufficiency from the stored engine result; not authorized orders.')
        return result
    if not relevant:
        result.update(status='INSUFFICIENT_INFORMATION',message='No hay evidencia pertinente del sujeto para responder. / No relevant subject evidence is available.');return result
    if query&{'missing','quality'}:
        result.update(status='DETERMINISTIC_DATA_SUFFICIENCY',consistency_policy='ENGINE_DATA_REQUIREMENTS_ONLY');return result
    if result['mode']=='CRITICAL':return result
    if not inference.status()['available']:return result
    # Patient-specific explanations cite ENGINE facts; retrieved documents remain independently visible.
    # This avoids letting a guideline or an injected excerpt override a stored patient result.
    context=[b for b in selected if b['kind']=='ENGINE']
    if not hasattr(inference,'explain'):return result
    result['inference_attempted']=True
    try:
        response=inference.explain(question,context,history)
        generated=validate_generated({'sentences':[{'text':g['text'],'evidence_ids':g['evidence_ids']} for g in response.get('generated',[])]},context)
        # Descriptive values cannot acquire unsupported clinical direction or diagnoses in prose.
        if any(re.search(r'\b(normal|normales|normalidad|empeor\w*|mejor\w*|worsen\w*|improv\w*|confirma\w*|confirm\w*|descarta\w*|cured|cancer)\b',g['text'],re.I) for g in generated):raise ValueError('UNSUPPORTED_CLINICAL_INTERPRETATION')
        result.update(response);result['generated']=generated
        result['answer']=selected # deterministic fallback is retained even for an empty generation
    except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError,MemoryError) as exc:
        from .inference_failures import failure_trace
        result['failure_trace']=failure_trace(exc)
        result.update(status='EXTRACTIVE_FALLBACK',generated=[],failure_type=type(exc).__name__,message='Explicación rechazada o fallida; se muestran resultados exactos del motor. / Generation rejected or failed; exact engine results retained.')
    return result
