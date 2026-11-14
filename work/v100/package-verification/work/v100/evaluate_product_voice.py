from pathlib import Path
import sys,json,time,secrets,base64,socket,os,copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from fastapi.testclient import TestClient
from vigile.api import create_app
from vigile.portal import create_portal
from vigile.mission_review import ASGIReader
from vigile.local_protection import read_secret
from vigile.conversational import ConversationalInference
from vigile.voice import LocalVoice
from vigile.integration import deny_external_network
from vigile.space_compute import telemetry
folder=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();output.mkdir(exist_ok=False)
config=json.loads((folder/'portal-config.json').read_text());mapping=json.loads(read_secret(folder/'server-tokens.json'));token=read_secret(folder/'reader-token.txt');code=read_secret(folder/'portal-access.txt')
refs=json.loads((ROOT/'docs/v100/voice-benchmark/references.json').read_text(encoding='utf8'))
scenarios=[('A','en',9,'mission-crew-A-cycle-35','FULL',False),('B','en',10,'mission-crew-B-cycle-18','FULL',False),('C','en',11,'mission-crew-B-cycle-18','FULL',False),('D','es',11,'mission-crew-B-cycle-18p1','FULL',False),('A-es','es',9,'mission-crew-A-cycle-35','FULL',False),('LOW','en',9,'mission-crew-A-cycle-35','LOW_POWER',False),('CRITICAL','en',9,'mission-crew-A-cycle-35','CRITICAL',False),('OUTAGE','en',9,'mission-crew-A-cycle-35','FULL',True),('RESTORED','en',9,'mission-crew-A-cycle-35','FULL',False)]
report={'synthetic_reference_audio':True,'microphone_capture':'NOT_A_PHYSICAL_MICROPHONE_TEST','reference_correction':'Explicit reference review in this synthetic harness; runtime never auto-corrects or auto-submits','external_network_guard':'Python sockets allow loopback only; not an OS firewall','rows':[],'before':telemetry([os.getpid()]),'clinical_validation':False}
deny_external_network();voice=LocalVoice()
with TestClient(create_app(ROOT,folder/'vigile.sqlite3',mapping)) as backend:
 engine=backend.app.state.engine;original={r['id']:r['output_hash'] for r in engine.store.all('monitoring_run')}
 for label,lang,index,target,mode,outage in scenarios:
  blocked=socket.socket();blocked.bind(('127.0.0.1',0));port=blocked.getsockname()[1]
  model=ConversationalInference('http://127.0.0.1:'+str(port) if outage else config['model_url'],config['model'],mode,config['inference_provider'])
  raw_calls=[];complete=model._complete
  def traced(*args):
   value=complete(*args);raw_calls.append({'output':value[0],'metrics':value[1]});return value
  model._complete=traced;case_config=dict(config);case_config.update(voice_enabled=True,structured_explanations=True)
  # New session per independent scenario; production rate limits remain unchanged.
  with TestClient(create_portal(case_config,ASGIReader(backend,token),model,voice=voice),base_url='http://127.0.0.1:8898') as portal:
   h={'Origin':'http://127.0.0.1:8898'};login=portal.post('/api/login',headers=h,json={'code':code});assert login.status_code==200
   raw=(ROOT/('docs/v100/voice-benchmark/'+lang+'-'+str(index)+'.wav')).read_bytes();start=time.perf_counter()
   transcription=portal.post('/api/voice/transcribe',headers=h,json={'monitoring_id':target,'language':lang,'audio_base64':base64.b64encode(raw).decode()});transcription.raise_for_status();transcript=transcription.json()
   reference=refs[lang][index];answer=portal.post('/api/assistant',headers=h,json={'monitoring_id':target,'language':lang,'question':reference});answer.raise_for_status();reply=answer.json();speech=reply['speech']
   synthesized=portal.post('/api/voice/synthesize',headers=h,json={'response_id':speech['response_id'],'target_id':target,'rate':0});synthesized.raise_for_status();(output/(label+'.wav')).write_bytes(synthesized.content)
   safe_reply=copy.deepcopy(reply);safe_reply['speech'].pop('response_id',None);safe_reply['speech']['response_id_omitted']=True
   row={'scenario':label,'mode':mode,'language':lang,'reference_question':reference,'recognized_text':transcript['text'],'submitted_text_after_reference_review':reference,'transcription':transcript,'answer':safe_reply,'raw_model_calls':raw_calls,'synthesis_seconds':float(synthesized.headers['x-synthesis-seconds']),'wav_bytes':len(synthesized.content),'from_end_of_reference_capture_to_wave_ready_seconds':time.perf_counter()-start,'human_review_delay':'NOT_MEASURED_IN_SYNTHETIC_HARNESS','playback_device_latency':'NOT_MEASURED_BY_ASGI_TEST','clinical_hashes_unchanged':original=={r['id']:r['output_hash'] for r in engine.store.all('monitoring_run')},'metrics':telemetry([os.getpid()])}
   if mode=='CRITICAL' or outage:assert model.model_http_calls==0
   assert row['clinical_hashes_unchanged'];report['rows'].append(row);(output/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');print(label,reply['status'],len(reply.get('generated',[])),round(row['from_end_of_reference_capture_to_wave_ready_seconds'],2),flush=True)
  blocked.close()
 report['audit_valid']=engine.store.verify();assert report['audit_valid']
 records=engine.store.all('monitoring_run');matching=all(r['implementation_hash']==engine.implementation_hash for r in records)
 report['monitoring_replays']=[backend.app.state.monitoring.replay(r['id']) for r in records] if matching else 'DEVELOPMENT_VERSION_MISMATCH_NOT_REPLAYED'
 report['clinical_replays']=[backend.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')] if matching else 'DEVELOPMENT_VERSION_MISMATCH_NOT_REPLAYED'
report['after']=telemetry([os.getpid()]);(output/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')