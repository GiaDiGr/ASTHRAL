"""Authenticated voice endpoints and session-bound approved speech tickets.
Audio is untrusted; transcripts cannot submit questions or measurements by themselves.
"""
import base64,hashlib,secrets,time,threading
from typing import Literal
from fastapi import Request,HTTPException
from fastapi.responses import Response
from pydantic import Field,StrictInt,model_validator
from .models import Model,Id
from .voice import LocalVoice,VoiceError,MAX_WAV_BYTES

class AudioInput(Model):
    monitoring_id:Id|None=None
    evaluation_id:Id|None=None
    language:Literal['en','es']
    audio_base64:str=Field(min_length=1,max_length=1_800_100)
    @model_validator(mode='after')
    def target(self):
        if (self.monitoring_id is None)==(self.evaluation_id is None):raise ValueError('ONE_TARGET_REQUIRED')
        return self
class SpeechInput(Model):
    response_id:Id
    target_id:Id
    rate:StrictInt=Field(default=0,ge=-3,le=3)

class SpeechTickets:
    def __init__(self,clock=time.monotonic):self.rows={};self.lock=threading.Lock();self.clock=clock
    def issue(self,owner,target,text,language,kind):
        with self.lock:
            now=self.clock();self.rows={k:v for k,v in self.rows.items() if v['expires']>now}
            while len(self.rows)>=32:self.rows.pop(next(iter(self.rows)))
            token=secrets.token_hex(24);self.rows[token]={'owner':owner,'target':target,'text':text,'language':language,'expires':now+300}
        return {'response_id':token,'target_id':target,'text':text,'language':language,'kind':kind,'expires_seconds':300,'retained_audio':False,'requires_user_playback':True}
    def get(self,token,owner,target):
        with self.lock:
            row=self.rows.get(token)
            if not row or row['expires']<=self.clock() or row['owner']!=owner or row['target']!=target:raise HTTPException(410,'APPROVED_SPEECH_EXPIRED_OR_CONTEXT_MISMATCH')
            return dict(row)

def owner(request):return hashlib.sha256(request.cookies.get('vigile_session','').encode()).hexdigest()

def approved_text(result,evaluations,language,previous=()):
    # Only accepted generated output or authoritative engine facts enter the visible
    # speech envelope. Raw rejected output, user questions and documents never do.
    if result['status'] in ('REFUSED_ACTION','CONTEXT_MISMATCH','INSUFFICIENT_INFORMATION'):
        return result['message'][:1200],'DETERMINISTIC_REFUSAL'
    es=language=='es'
    parts=['Prototipo de investigación. Los criterios y su confirmación no constituyen un diagnóstico clínico firmado. Ningún tratamiento está autorizado. Los datos ausentes no son resultados normales.' if es else 'Research prototype. Criteria and confirmation states are not a signed clinical diagnosis. No treatment is authorized. Missing measurements are not normal results.']
    generated=result.get('generated',[])
    if result.get('explanation_context'):
        parts.append(('Ciclo registrado: ' if es else 'Recorded cycle: ')+result['explanation_context']['as_of']+'.')
    if generated:parts.extend(g['text'] for g in generated)
    else:
        from .structured_facts import Fact,deterministic_fact
        parts.append('Lectura determinista o extractiva. No hubo una explicación generada aceptada.' if es else 'Deterministic or extractive reading. No generated explanation was accepted.')
        for f in result.get('structured_facts',[])[:2]:parts.append(deterministic_fact(Fact.model_validate(f),language))
    names={'bicarbonate_mmol_l':('bicarbonate','bicarbonato'),'urine_ketones_plus':('urine ketones','cetonas urinarias'),'potassium_mmol_l':('potassium','potasio'),'beta_hydroxybutyrate_mmol_l':('beta hydroxybutyrate','beta hidroxibutirato'),'venous_pH':('venous pH','pH venoso')}
    state_labels={'CRITERIA_MET':('criteria met','criterios cumplidos'),'CRITERIA_NOT_MET':('criteria not met','criterios no cumplidos'),'INSUFFICIENT_DATA':('insufficient data','datos insuficientes'),'SUSPECTED':('suspected only','sólo sospecha'),'CONFLICTING_EVIDENCE':('conflicting evidence','evidencia contradictoria'),'NOT_APPLICABLE':('not applicable','no aplicable'),'EMERGENCY':('emergency','emergencia'),'URGENT':('urgent','urgente'),'PROMPT':('prompt review','evaluación pronta'),'ROUTINE':('routine','rutina'),'SATISFIED':('satisfied as a criteria state only','satisfecha sólo como estado de criterios'),'REQUIRED':('required','requerida'),'NOT_REQUIRED':('not required','no requerida'),'BLOCKED_MISSING_DATA':('blocked because data are missing','bloqueado por datos pendientes'),'BLOCKED_AUTHORIZATION':('blocked without verified authorization','bloqueado sin autorización verificada'),'BLOCKED_RESOURCE':('blocked because resources are missing','bloqueado por recursos pendientes'),'BLOCKED_CONTRAINDICATION':('blocked by safety restrictions','bloqueado por restricciones de seguridad'),'NOT_STARTED':('not started','no iniciado'),'PENDING':('pending','pendiente')}
    label=lambda code:state_labels.get(code,(code,code))[es]
    if len(evaluations)>1:parts.append('Resumen oral: hechos descriptivos y estados clínicos urgentes; revisa también las demás rutas en pantalla.' if es else 'Spoken summary: descriptive facts and urgent clinical states; also review the other pathways on screen.')
    for ev in evaluations:
        for condition,r in ev['results'].items():
            if len(evaluations)>1 and r['urgency'] not in ('URGENT','EMERGENCY'):continue
            # Codes remain literal, accompanied by readable labels. No inferred state.
            parts.append((f'{condition}. Estado de criterios: {label(r["diagnostic_status"]) }. Urgencia: {label(r["urgency"]) }. Confirmación de criterios: {label(r["confirmation_status"]) }. Protocolo: {label(r["protocol_status"]) }. Tratamiento: {label(r["treatment_status"]) }.' if es else f'{condition}. Criteria status: {label(r["diagnostic_status"]) }. Urgency: {label(r["urgency"]) }. Criteria confirmation: {label(r["confirmation_status"]) }. Protocol: {label(r["protocol_status"]) }. Treatment: {label(r["treatment_status"]) }.'))
            prior=next((old['results'].get(condition) for old in previous if condition in old['results']),None)
            if prior and prior.get('required_for_protocol_safety')!=r.get('required_for_protocol_safety'):
                old_fields=', '.join(names.get(f,(f,f))[es] for f in prior.get('required_for_protocol_safety',[])) or ('ninguno' if es else 'none')
                parts.append(('Pendientes de seguridad en la evaluación anterior: ' if es else 'Protocol safety data pending in the previous evaluation: ')+old_fields+'.')
                parts.append(('Los estados de criterios y autorización se informan por separado; nuevos datos no autorizan tratamiento.' if es else 'Criteria and authorization states remain separate; additional data do not authorize treatment.'))
            labels=[('missing_required','Pendientes para resolver criterios','Pending to resolve criteria'),('optional_not_measured','Alternativas no medidas que no bloquean','Unmeasured alternatives that do not block'),('invalid_required','Datos inválidos en ramas pendientes','Invalid data in unresolved branches'),('required_for_protocol_safety','Pendientes para seguridad del protocolo','Pending for protocol safety')]
            for key,span,en in labels:
                fields=r.get(key)
                if fields is None:continue
                values=', '.join(names.get(f,(f,f))[es] for f in fields) or ('ninguno' if es else 'none')
                parts.append((span if es else en)+': '+values+'.')
    if not generated and not result.get('structured_facts') and not evaluations:
        parts.extend(b['text'] for b in result.get('answer',[])[:2] if b.get('kind')=='ENGINE' and len(b['text'])<450)
    text=' '.join(parts)
    # Never truncate away a restriction to satisfy the audio bound.
    if len(text)>3500:raise VoiceError('APPROVED_SPEECH_TOO_LONG_USE_TEXT')
    return text,'ACCEPTED_GENERATION_AND_ENGINE_RESTRICTIONS' if generated else 'DETERMINISTIC_ENGINE_READING'

def install_voice(app,config,reader,inference,voice=None,clock=time.monotonic):
    enabled=bool(config.get('voice_enabled',False));voice=voice or (LocalVoice(config.get('stt_models')) if enabled else None)
    tickets=SpeechTickets(clock);app.state.voice=voice;app.state.speech_tickets=tickets
    def target(body):
        rid=body.monitoring_id or body.evaluation_id
        path=('/monitoring/cycles/' if body.monitoring_id else '/clinical/evaluations/')+rid
        return reader.get(path) # Existing reader role/scope verification, no write client.
    @app.exception_handler(VoiceError)
    async def voice_failure(request,exc):
        code=str(exc)
        permitted={'AUDIO_SIZE_INVALID','PCM16_MONO_16000_REQUIRED','AUDIO_DURATION_INVALID','AUDIO_TRUNCATED','AUDIO_FORMAT_INVALID','AUDIO_SILENCE_OR_TOO_QUIET','VOICE_BUSY','STT_UNAVAILABLE_OR_RESOURCE_LIMIT','NO_SPEECH_RECOGNIZED','TRANSCRIPT_TOO_LONG','STT_LOCAL_ENGINE_FAILED','STT_MODEL_INTEGRITY_FAILED','TTS_LOCAL_ENGINE_FAILED','TTS_LOCAL_ENGINE_UNAVAILABLE','TTS_UNAVAILABLE_OR_RESOURCE_LIMIT','TTS_INPUT_INVALID','TTS_INVALID_OUTPUT','APPROVED_SPEECH_TOO_LONG_USE_TEXT','LANGUAGE_NOT_SUPPORTED'}
        if code not in permitted:code='VOICE_LOCAL_FAILURE'
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail':code,'text_interface_available':True},status_code=429 if code=='VOICE_BUSY' else 503 if 'UNAVAILABLE' in code or 'FAILED' in code else 422)
    @app.get('/api/voice/status')
    def status():return voice.status(getattr(inference,'mode','FULL')) if voice else {'configured':False,'reason':'VOICE_NOT_CONFIGURED','stt':{},'tts':{},'text_interface_available':True}
    @app.post('/api/voice/transcribe')
    def transcribe(body:AudioInput):
        target(body)
        if not voice:raise HTTPException(503,'VOICE_NOT_CONFIGURED')
        try:raw=base64.b64decode(body.audio_base64,validate=True)
        except ValueError:raise VoiceError('AUDIO_FORMAT_INVALID') from None
        if len(raw)>MAX_WAV_BYTES:raise VoiceError('AUDIO_SIZE_INVALID')
        result=voice.transcribe(raw,body.language,getattr(inference,'mode','FULL'))
        return {**result,'target_id':body.monitoring_id or body.evaluation_id,'automatic_question_submission':False,'clinical_execution':'BLOCKED'}
    @app.post('/api/voice/synthesize')
    def synthesize(body:SpeechInput,request:Request):
        row=tickets.get(body.response_id,owner(request),body.target_id)
        if not voice:raise HTTPException(503,'VOICE_NOT_CONFIGURED')
        raw,metrics=voice.synthesize(row['text'],row['language'],body.rate,getattr(inference,'mode','FULL'))
        return Response(raw,media_type='audio/wav',headers={'Cache-Control':'no-store','X-Synthesis-Seconds':str(metrics['synthesis_seconds']),'X-Audio-Retention':'memory-only','X-Content-Type-Options':'nosniff'})
    def attach(result,body,request):
        if not enabled and voice is None:return result
        record=target(body)
        evaluations=list(record.get('clinical_evaluations',{}).values()) if body.monitoring_id else [record]
        context={k:record[k] for k in ('subject_id','mission_id','as_of') if k in record}
        previous=[]
        if body.monitoring_id and record.get('previous_run_id'):
            old=reader.get('/monitoring/cycles/'+record['previous_run_id']);previous=list(old.get('clinical_evaluations',{}).values())
        if body.evaluation_id:
            context=reader.get('/clinical/evaluations/'+body.evaluation_id+'/context')
            if record.get('parent_id'):previous=[reader.get('/clinical/evaluations/'+record['parent_id'])]
        result.setdefault('explanation_context',{**context,'target_id':body.monitoring_id or body.evaluation_id})
        try:
            text,kind=approved_text(result,evaluations,body.language,previous)
            result['speech']=tickets.issue(owner(request),body.monitoring_id or body.evaluation_id,text,body.language,kind)
        except VoiceError:result['speech']={'available':False,'reason':'APPROVED_SPEECH_TOO_LONG_USE_TEXT'}
        return result
    return attach