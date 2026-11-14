from pathlib import Path
import sys,json,time,statistics,hashlib
root=Path(r'C:\Users\Gianni\Desktop\Vigile');sys.path.insert(0,str(root/'engine'))
import httpx
from vigile.store import Store
folder=root/'engine/data/portal-v05-final';docs=root/'docs/portal'
config=json.loads((folder/'portal-config.json').read_text());base='http://127.0.0.1:8876'
durations=[];checks=[]
with httpx.Client(base_url=base,trust_env=False,timeout=45) as client:
 def call(method,path,body=None):
  start=time.perf_counter();r=client.request(method,path,json=body,headers={'Origin':base} if method=='POST' else {});durations.append((time.perf_counter()-start)*1000);r.raise_for_status();return r.json()
 call('POST','/api/login',{'code':Path(config['access_code_file']).read_text()})
 status=call('GET','/api/status');assert status['assistant']['available'] is False
 assert len(call('GET','/api/subjects'))==1
 data=call('GET','/api/dashboard/clinical-crew?mission_id=clinical-earth')
 assert len(data['measurements'])==21 and len(data['baselines'])==1
 for e in data['evaluations']:
  reply=call('POST','/api/assistant',{'evaluation_id':e['id'],'question':'¿Qué datos faltan y qué pruebas se recomiendan?'})
  assert reply['status']=='UNAVAILABLE' and reply['sources'] and not reply['inference_executed']
  checks.append({'evaluation_id':e['id'],'condition':e['condition_id'],'presentation':e['presentation_id'],'urgency':e['urgency'],'assistant':reply['status']})
 assert call('GET','/api/protocol/PROT-DKA-ADULT-2024')['execution_enabled'] is False
 assert client.post('/api/assistant',json={}).status_code==403
 with httpx.Client(base_url=config['backend_url'],trust_env=False,headers={'Authorization':'Bearer '+Path(config['reader_token_file']).read_text()}) as backend:
  for e in data['evaluations']:assert backend.get('/clinical/evaluations/'+e['id']+'/replay').json()['matches']
  assert backend.post('/clinical/evaluations',json={'role':'clinician'}).status_code==403
  assert backend.get('/dashboard/subjects/unauthorized?mission_id=clinical-earth').status_code==403
  (docs/'openapi-v05.json').write_text(json.dumps(backend.get('/openapi.json').json(),ensure_ascii=False,indent=2),encoding='utf-8')
store=Store(folder/'vigile.sqlite3');assert store.verify();store.close()
report={'transport':'Real TCP HTTP loopback, HTTPX client to BFF to backend','requests_measured':len(durations),'latency_ms_median':statistics.median(durations),'latency_ms_max':max(durations),'scenarios':checks,'replays_match':True,'reader_write_denied':True,'scope_denied':True,'csrf_denied':True,'audit_valid':True,'real_llm_inference_executed':False,'clinical_validation':False,'sqlite_bytes':(folder/'vigile.sqlite3').stat().st_size}
(docs/'live-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
