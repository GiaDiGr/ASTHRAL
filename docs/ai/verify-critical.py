from pathlib import Path
import sys,json,hashlib,zipfile,xml.etree.ElementTree as ET
root=Path(r'C:\Users\Gianni\Desktop\Vigile');sys.path.insert(0,str(root/'engine'));stage=Path(__file__).parent;docs=root/'docs/ai'
import httpx
from vigile.store import Store,digest
folder=root/'engine/data/portal-v06-final'
def snapshot():
 s=Store(folder/'vigile.sqlite3');h=digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')]);assert s.verify();s.close();return h
before=snapshot()
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,headers={'Origin':'http://127.0.0.1:8896'},timeout=20) as c:
 r=c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text()});r.raise_for_status()
 c.post('/api/mode',json={'mode':'CRITICAL'}).raise_for_status()
 data=c.get('/api/dashboard/clinical-crew?mission_id=clinical-earth').json();rows=[]
 for e in data['evaluations']:
  r=c.post('/api/assistant',json={'evaluation_id':e['id'],'question':'¿Qué datos faltan?'});r.raise_for_status();reply=r.json()
  assert reply['status']=='EXTRACTIVE_ONLY' and not reply['inference_executed'];rows.append({'evaluation_id':e['id'],'status':reply['status']})
 doc=c.post('/api/assistant',json={'evaluation_id':data['evaluations'][0]['id'],'question':'¿Qué dice la investigación sobre diabetes y glucosa?'}).json()
 assert any(b['kind']=='DOCUMENT' for b in doc['retrieved'])
 assert c.post('/api/mode',json={'mode':'CLINICIAN'}).status_code==422
 assert c.post('/api/mode',json={'mode':'FULL'},headers={'Origin':'https://external.example'}).status_code==403
with httpx.Client(base_url='http://127.0.0.1:8895',trust_env=False,headers={'Authorization':'Bearer '+(folder/'reader-token.txt').read_text()}) as c:
 for e in data['evaluations']:assert c.get('/clinical/evaluations/'+e['id']+'/replay').json()['matches']
 assert c.post('/clinical/evaluations',json={}).status_code==403
 assert c.get('/dashboard/subjects/other?mission_id=clinical-earth').status_code==403
 (docs/'openapi-v06.json').write_text(json.dumps(c.get('/openapi.json').json(),indent=2),encoding='utf-8')
assert before==snapshot()
originals=json.loads((root/'docs/INITIAL_INVENTORY.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((root/o['path']).read_bytes()).hexdigest()==o['sha256'] for o in originals)
with zipfile.ZipFile(stage/'releases/vigile-v05-before-ai.zip') as z:
 clinical=[n for n in z.namelist() if n.startswith('vigile/clinical_')]
 assert all(z.read(n)==(root/'engine'/n).read_bytes() for n in clinical)
report={'tests':ET.parse(docs/'tests-v06.xml').getroot().find('testsuite').attrib,'original_files_unchanged':len(originals),'clinical_modules_and_knowledge_unchanged':len(clinical),'critical_queries':rows,'documentary_retrieval':True,'replays_match':True,'reader_write_denied':True,'wrong_scope_denied':True,'mode_csrf_denied':True,'records_unchanged':True,'runtime_executable_available':(root/'engine/local_ai/llama-b11721/llama-server.exe').exists(),'clinical_validation':False}
(docs/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
config=json.loads((folder/'portal-config.json').read_text());config['mode']='CRITICAL';(folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
