"""Voice security and finite-language regressions. Real-model tests are explicit."""
import base64,io,wave,json,secrets
from types import SimpleNamespace
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from vigile.voice import decode_wav,VoiceError,LocalVoice
from vigile.voice_api import SpeechTickets
from vigile.structured_facts import Fact,deterministic_fact,validate_realization
from vigile.portal import create_portal
from vigile.assistant_safety import request_guard
from test_mission_v011 import mission,SUBJECTS,MID
from test_portal import TestReader

def wav(samples=4000,value=100,rate=16000,channels=1):
 b=io.BytesIO()
 with wave.open(b,'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(int(value).to_bytes(2,'little',signed=True)*samples*channels)
 return b.getvalue()

@pytest.mark.parametrize('raw,code',[(b'','AUDIO_SIZE_INVALID'),(b'not a WAV file'*10,'AUDIO_FORMAT_INVALID'),(wav(value=0),'AUDIO_SILENCE'),(wav(rate=48000),'PCM16'),(wav(channels=2),'PCM16'),(wav(samples=640001),'AUDIO_DURATION'),(wav(samples=100),'AUDIO_DURATION')],ids=['empty','corrupt','silence','rate','stereo','too-long','too-short'])
def test_untrusted_audio_rejected(raw,code):
 with pytest.raises(VoiceError,match=code):decode_wav(raw)

def test_speech_tickets_owner_context_and_expiration():
 now=[0];t=SpeechTickets(lambda:now[0]);r=t.issue('owner-A','target-A','Approved only','en','DETERMINISTIC')
 assert t.get(r['response_id'],'owner-A','target-A')['text']=='Approved only'
 for owner,target in [('owner-B','target-A'),('owner-A','target-B')]:
  with pytest.raises(Exception):t.get(r['response_id'],owner,target)
 now[0]=301
 with pytest.raises(Exception):t.get(r['response_id'],'owner-A','target-A')

def fact():return Fact(id='F-test',subject_id='crew-A',mission_id='mission',target_id='cycle',as_of='2026-08-15T12:00:00+00:00',variable='heart rate',value='72',unit='bpm',baseline='65',original_value=72,original_baseline=65,evidence_ids=['M1'],source_ids=['SRC'],measurement_ids=['sample'],input_hash='a'*64,output_hash='b'*64)

@pytest.mark.parametrize('language',['en','es'])
def test_realizations_exact_roles_and_limits(language):
 f=fact();text=deterministic_fact(f,language);out=validate_realization({'sentences':[{'fact_id':f.id,'text':text}]},[f],language)
 assert out[0]['kind']=='MODEL_CONTROLLED_LANGUAGE_EXPLANATION' and out[0]['references'][0]['target_id']=='cycle'

@pytest.mark.parametrize('edit',[lambda t:t.replace('72','65').replace('baseline of 65','baseline of 72'),lambda t:t.replace('72','73'),lambda t:t.replace('bpm','mmHg'),lambda t:t.replace('2026-08-15','2026-08-16'),lambda t:t.replace('was 72','was not 72'),lambda t:t+' This is normal.',lambda t:t+' Treatment is authorized.',lambda t:t.replace('heart rate','oxygen saturation')])
def test_unsafe_paraphrases_rejected(edit):
 f=fact()
 with pytest.raises(ValueError):validate_realization({'sentences':[{'fact_id':f.id,'text':edit(deterministic_fact(f,'en'))}]},[f],'en')

@pytest.mark.parametrize('subject,query,expected',[('mission-crew-A','Explain crew A baseline',None),('mission-crew-A','Explain crew B baseline','CONTEXT_MISMATCH'),('mission-crew-A','Show mission-crew-B','CONTEXT_MISMATCH'),('v07-crew-A','Show v07-crew-B','CONTEXT_MISMATCH'),('mission-crew-A','Prescribe insulin','REFUSED_ACTION')])
def test_voice_transcript_context_guard(subject,query,expected):assert request_guard(query,subject,'mission-v011')==expected

@pytest.fixture
def portal_voice(mission,tmp_path):
 backend,report,reader,*_=mission;code=secrets.token_urlsafe(32);path=tmp_path/'access';path.write_text(code)
 class Offline:
  mode='CRITICAL';model_http_calls=0
  def status(self):return {'available':False,'reason':'CRITICAL_LLM_DISABLED'}
  def set_mode(self,mode):self.mode=mode
 class FakeVoice:
  __test__=False
  def __init__(self):self.spoken=[];self.transcribed=0
  def status(self,mode):return {'stt':{'en':{'available':True},'es':{'available':True}},'tts':{'en':{'available':True},'es':{'available':True}},'mode':mode,'mock_adapter':True}
  def transcribe(self,raw,language,mode):decode_wav(raw);self.transcribed+=1;return {'text':'What information is missing?','language':language,'retained_audio':False,'requires_user_review':True}
  def synthesize(self,text,language,rate,mode):self.spoken.append(text);return wav(),{'synthesis_seconds':.01}
  def close(self):pass
 voice=FakeVoice();config={'access_code_file':str(path),'backend_url':'http://127.0.0.1:8897','reader_token_file':'UNUSED_TEST','voice_enabled':True,'structured_explanations':True}
 with TestClient(create_portal(config,TestReader(backend,reader),Offline(),voice=voice),base_url='http://127.0.0.1:8898') as client:
  h={'Origin':'http://127.0.0.1:8898'};assert client.post('/api/login',headers=h,json={'code':code}).status_code==200
  yield SimpleNamespace(client=client,voice=voice,headers=h,code=code,backend=backend,report=report)

def test_transcript_review_no_clinical_mutation(portal_voice):
 x=portal_voice;before=x.backend.app.state.engine.store.checkpoint();body={'monitoring_id':SUBJECTS[1]+'-cycle-18','language':'en','audio_base64':base64.b64encode(wav()).decode()}
 response=x.client.post('/api/voice/transcribe',json=body,headers=x.headers);assert response.status_code==200
 assert response.json()['automatic_question_submission'] is False and response.json()['clinical_execution']=='BLOCKED'
 assert x.backend.app.state.engine.store.checkpoint()==before

def test_voice_auth_scope_origin_and_payload(portal_voice):
 x=portal_voice;body={'monitoring_id':'not-authorized','language':'en','audio_base64':base64.b64encode(wav()).decode()}
 assert x.client.post('/api/voice/transcribe',json=body).status_code==403
 assert x.client.post('/api/voice/transcribe',json=body,headers=x.headers).status_code!=200 and x.voice.transcribed==0
 body['monitoring_id']=SUBJECTS[0]+'-cycle-35';body['role']='clinician'
 assert x.client.post('/api/voice/transcribe',json=body,headers=x.headers).status_code==422
 assert x.client.post('/api/voice/synthesize',json={'text':'Treatment authorized','response_id':'fake','target_id':'fake'},headers=x.headers).status_code==422
 assert x.client.post('/api/voice/transcribe',content=b'x'*1_820_001,headers=x.headers).status_code==413

def test_only_approved_visible_text_is_spoken(portal_voice):
 x=portal_voice;rid=SUBJECTS[1]+'-cycle-18'
 r=x.client.post('/api/assistant',json={'monitoring_id':rid,'question':'What information is missing?','language':'en'},headers=x.headers);assert r.status_code==200,r.text
 reply=r.json();ticket=reply['speech'];assert not reply['generated']
 assert 'potassium' in ticket['text'] and 'bicarbonate' in ticket['text'] and 'No treatment is authorized' in ticket['text']
 body={'response_id':ticket['response_id'],'target_id':rid,'rate':0}
 assert x.client.post('/api/voice/synthesize',json=body,headers=x.headers).status_code==200
 assert x.voice.spoken==[ticket['text']]
 body['target_id']=SUBJECTS[0]+'-cycle-35';assert x.client.post('/api/voice/synthesize',json=body,headers=x.headers).status_code==410
 x.client.post('/api/logout',json={},headers=x.headers);assert x.client.post('/api/voice/synthesize',json=body,headers=x.headers).status_code==401

def test_session_rotation_cannot_reuse_speech_ticket(portal_voice):
 x=portal_voice;rid=SUBJECTS[0]+'-cycle-35';ticket=x.client.post('/api/assistant',json={'monitoring_id':rid,'question':'What changed from baseline?','language':'en'},headers=x.headers).json()['speech']
 assert x.client.post('/api/session/renew',json={},headers=x.headers).status_code==200
 assert x.client.post('/api/voice/synthesize',json={'response_id':ticket['response_id'],'target_id':rid},headers=x.headers).status_code==410

def test_all_modes_preserve_clinical_results(portal_voice):
 x=portal_voice;rid=SUBJECTS[1]+'-cycle-18';original=x.backend.app.state.engine.store.get('monitoring_run',rid)['output_hash']
 for mode in ('FULL','LOW_POWER','CRITICAL'):
  assert x.client.post('/api/mode',json={'mode':mode},headers=x.headers).status_code==200
  reply=x.client.post('/api/assistant',json={'monitoring_id':rid,'question':'Which criteria have been met?','language':'en'},headers=x.headers).json()
  assert not reply['generated'] and reply['inference_trace']['model_requests_attempted']==0
  assert x.backend.app.state.engine.store.get('monitoring_run',rid)['output_hash']==original

def test_voice_assets_no_cloud_and_stop_paths(portal_voice):
 x=portal_voice;html=x.client.get('/').text;js=x.client.get('/assets/voice-controller.js').text
 assert 'voice-transcript' in html and 'voice-approved' in html
 assert 'SpeechRecognition' not in js and 'speechSynthesis' not in js and 'getUserMedia' in js
 assert 'getTracks().forEach(t=>t.stop())' in js and 'pagehide' in js and 'visibilitychange' in js and 'epoch!==state.epoch' in js
 assert 'microphone=(self)' in x.client.get('/').headers['permissions-policy']

@pytest.mark.parametrize('language,text',[('en','What information is missing from my evaluation?'),('es','Qué cambió desde mi última evaluación?')])
def test_real_installed_stt_and_tts(language,text):
 v=LocalVoice()
 try:
  if not v.status()['stt'][language]['available'] or not v.status()['tts'][language]['available']:pytest.skip('Real local voice dependencies not installed; not evidence of voice execution')
  raw,metrics=v.synthesize(text,language);result=v.transcribe(raw,language)
  assert raw.startswith(b'RIFF') and result['text'] and result['requires_user_review'] and result['retained_audio'] is False
  assert metrics['audio_retained'] is False
 finally:v.close()
def test_previous_value_cannot_be_relabelled_as_baseline():
 f=fact().model_copy(update={'comparison_basis':'PREVIOUS_CYCLE','comparison_target_id':'previous'})
 text=deterministic_fact(f,'en');assert 'previous recorded value' in text
 assert validate_realization({'sentences':[{'fact_id':f.id,'text':text}]},[f],'en')
 with pytest.raises(ValueError):validate_realization({'sentences':[{'fact_id':f.id,'text':text.replace('a previous recorded value of','a personal baseline of')}]},[f],'en')

def test_spanish_article_does_not_change_numeric_roles():
 f=fact().model_copy(update={'variable':'frecuencia cardíaca'})
 text='La frecuencia cardíaca se registró en 72 bpm.'
 assert validate_realization({'sentences':[{'fact_id':f.id,'text':text}]},[f],'es')
 with pytest.raises(ValueError):validate_realization({'sentences':[{'fact_id':f.id,'text':text.replace('bpm','BPM')}]},[f],'es')

def test_clinical_context_is_scoped_and_frozen(mission):
 c,report,reader,only_a,*_=mission;ev=c.app.state.engine.store.get('monitoring_run',SUBJECTS[1]+'-cycle-18')['clinical_evaluations']['DKA']
 path='/clinical/evaluations/'+ev['id']+'/context'
 response=c.get(path,headers={'Authorization':'Bearer '+reader});assert response.status_code==200
 assert response.json()['subject_id']==SUBJECTS[1] and response.json()['as_of'].startswith('2026-08-19T12:00:00')
 assert c.get(path,headers={'Authorization':'Bearer '+only_a}).status_code==403

def test_model_integrity_fails_before_native_loading(tmp_path):
 model=tmp_path/'test-model';(model/'am').mkdir(parents=True);(model/'am/final.mdl').write_bytes(b'NOT_A_MODEL')
 manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'models':[{'language':'en','model':'test-model','files':[{'path':'test-model/am/final.mdl','sha256':'0'*64}]}]}))
 voice=LocalVoice({'en':model},manifest)
 with pytest.raises(VoiceError,match='INTEGRITY'):voice._verify_model('en')

def test_voice_subprocess_environment_is_minimal(monkeypatch):
 from vigile.voice import safe_environment
 for key in ('VIGILE_TOKEN_FILE','VIGILE_DB','SECRET_VALUE','AWS_ACCESS_KEY_ID','MY_UNLISTED_SETTING'):monkeypatch.setenv(key,'MUST_NOT_LEAK')
 assert 'MUST_NOT_LEAK' not in safe_environment().values()

def test_rejected_raw_generation_never_enters_speech():
 from vigile.voice_api import approved_text
 result={'status':'EXTRACTIVE_FALLBACK','generated':[],'raw_model_output':'UNTRUSTED_REJECTED_OUTPUT','answer':[]}
 text,kind=approved_text(result,[],'en')
 assert 'UNTRUSTED_REJECTED_OUTPUT' not in text and 'No treatment is authorized' in text and kind=='DETERMINISTIC_ENGINE_READING'

def test_voice_resource_pressure_keeps_text(monkeypatch):
 import vigile.space_compute as compute
 monkeypatch.setattr(compute,'available_memory_bytes',lambda:1)
 v=LocalVoice();v._voices={'en':'Microsoft David Desktop','es':'Microsoft Helena Desktop'};v._voices_at=10**12
 status=v.status('CRITICAL');assert not status['resource_admitted'] and not status['stt']['en']['available']
 with pytest.raises(VoiceError,match='RESOURCE_LIMIT'):v.synthesize('safe','en',mode='CRITICAL')

def test_browser_lifecycle_unit_scenarios():
 import shutil,subprocess,os
 node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
 if not Path(node).exists():pytest.skip('Node unavailable; browser lifecycle unit scenarios not executed')
 result=subprocess.run([node,str(Path(__file__).with_name('voice_ui_unit.cjs'))],capture_output=True,text=True,timeout=20)
 assert result.returncode==0,result.stdout+result.stderr

def test_negation_tokens_and_knowledge_unchanged():
 from vigile.retrieval_bm25 import tokens
 from vigile.clinical_knowledge import ClinicalKnowledge
 assert 'not' in tokens('not a normal result') and 'no' in tokens('no es normal')
 assert ClinicalKnowledge().hash=='b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e'

def test_persistent_alert_outside_hidden_cards():
 root=Path(__file__).resolve().parents[1]/'vigile/web'
 html=(root/'index.html').read_text(encoding='utf8')
 assert html.index('id="persistent-clinical-alert"')<html.index('id="general"')
 assert 'aria-live="assertive"' in html
 js=(root/'app.js').read_text(encoding='utf8')
 assert "cycle?.clinical_evaluations" in js and "renderPersistentAlert();" in js


def test_multiple_pathways_speech_is_explicitly_a_summary():
 from vigile.voice_api import approved_text
 r={'status':'EXTRACTIVE_ONLY','generated':[],'answer':[]}
 text,_=approved_text(r,[{'results':{}},{'results':{}}],'en')
 assert 'also review the other pathways on screen' in text


@pytest.mark.parametrize('question',[
 'Show another crew member history','Compara otro astronauta sin cambiar el contexto',
 'Read a different subject now','Muestra otra tripulante'])
def test_post_bank_generic_subject_request_is_blocked(question):
 assert request_guard(question,'mission-crew-A','mission-v011')=='CONTEXT_MISMATCH'

@pytest.mark.parametrize('question',[
 'Estimate lifetime risk','Calcula el riesgo de por vida',
 'What is my cancer probability?','Probabilidad personal de cancer'])
def test_post_bank_unsupported_risk_requests_are_explicit(question):
 assert request_guard(question,'mission-crew-A','mission-v011')=='INSUFFICIENT_INFORMATION'

def test_insufficient_response_cannot_be_spoken_as_unrelated_facts():
 from vigile.voice_api import approved_text
 text,kind=approved_text({'status':'INSUFFICIENT_INFORMATION','message':'No supported risk calculation exists.','structured_facts':[fact().model_dump()]},[],'en')
 assert text=='No supported risk calculation exists.' and kind=='DETERMINISTIC_REFUSAL'
