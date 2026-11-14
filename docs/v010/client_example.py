"""External local reader example; never prints token/cookie or requests write access."""
from pathlib import Path
import sys,json,httpx
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.local_protection import read_secret
folder=ROOT/'engine/data/portal-v0100-integrated'
with httpx.Client(base_url='http://127.0.0.1:8895',headers={'Authorization':'Bearer '+read_secret(folder/'reader-token.txt')},trust_env=False,timeout=30) as reader:
 health=reader.get('/health');health.raise_for_status();run=reader.get('/monitoring/cycles/A-cycle-14');run.raise_for_status()
 print(json.dumps({'health':health.json(),'monitoring_id':run.json()['id'],'output_hash':run.json()['output_hash']},indent=2))
with httpx.Client(base_url='http://127.0.0.1:8896',headers={'Origin':'http://127.0.0.1:8896'},trust_env=False,timeout=30) as portal:
 portal.post('/api/login',json={'code':read_secret(folder/'portal-access.txt')}).raise_for_status()
 response=portal.get('/api/dashboard/clinical-crew?mission_id=clinical-earth');response.raise_for_status();e=response.json()['evaluations'][0]
 question={'evaluation_id':e['id'],'question':'¿Qué datos faltan y qué pruebas se recomiendan?'}
 reply=portal.post('/api/assistant',json=question);reply.raise_for_status()
 examples={'dashboard_request':'GET /api/dashboard/clinical-crew?mission_id=clinical-earth','dashboard_response':response.json(),'assistant_request':question,'assistant_response':reply.json()}
 (ROOT/'docs/v010/api-examples.json').write_text(json.dumps(examples,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps({'clinical_urgency':e['urgency'],'assistant_status':reply.json()['status'],'inference_trace':reply.json().get('inference_trace')},indent=2))
 portal.post('/api/logout',json={}).raise_for_status()
