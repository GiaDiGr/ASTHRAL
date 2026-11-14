"""Loopback integration checks against the prepared release; preserve all histories."""
from pathlib import Path
import sys,json,time,httpx,concurrent.futures
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/v09/live-checks.json');args=parser.parse_args()
if args.output.exists():raise ValueError('OUTPUT_EXISTS_PRESERVE_REFERENCE_RESULTS')

from vigile.integration import deny_external_network
from vigile.store import Store,digest
from vigile.local_assistant import ReaderClient
from vigile.longitudinal_assistant import answer_monitoring
from vigile.conversational import ConversationalInference
from vigile.offline_library import OfflineLibrary
deny_external_network();folder=ROOT/'engine/data/portal-v090-release';docs=ROOT/'docs/v09'
def snapshot():
 s=Store(folder/'vigile.sqlite3')
 try:assert s.verify();return digest([dict(r) for r in s.db.execute('SELECT kind,id,payload FROM records ORDER BY seq')])
 finally:s.close()
before=snapshot();cycles=[];report={'clinical_validation':False,'network':'LOOPBACK_ONLY_ENFORCED'}
with httpx.Client(base_url='http://127.0.0.1:8895',trust_env=False,timeout=30,headers={'Authorization':'Bearer '+(folder/'reader-token.txt').read_text().strip()}) as c:
 assert c.get('/health').json()['version']=='0.9.0'
 for letter in 'ABC':
  r=c.get('/monitoring/cycles',params={'subject_id':'v07-crew-'+letter,'mission_id':'v07-mission-'+letter});r.raise_for_status();cycles+=r.json()
 for run in cycles:
  r=c.get('/monitoring/cycles/'+run['id']+'/replay');r.raise_for_status();assert r.json()['matches']
  for ev in run['clinical_evaluations'].values():assert c.get('/clinical/evaluations/'+ev['id']+'/replay').json()['matches']
 assert c.post('/monitoring/cycles',json={}).status_code==403
 assert c.get('/monitoring/cycles',params={'subject_id':'outside','mission_id':'v07-mission-A'}).status_code==403
 (docs/'backend-openapi.json').write_text(json.dumps(c.get('/openapi.json').json(),indent=2),encoding='utf8')
old=json.loads((ROOT/'engine/data/portal-v080-final/monitoring-report.json').read_text())
def vectors(rows):
 return {r['id']:{k:{condition:{f:result.get(f) for f in ('diagnostic_status','urgency','confirmation_status','protocol_status','treatment_status')} for condition,result in ev['results'].items()} for k,ev in r['clinical_evaluations'].items()} for r in rows}
assert vectors(old['outputs'])==vectors(cycles)
report.update(cycle_replays=len(cycles),clinical_replays=sum(len(r['clinical_evaluations']) for r in cycles),clinical_vectors_match_v08=True,reader_write_denied=True,scope_enforced=True)
with httpx.Client(base_url='http://127.0.0.1:8896',trust_env=False,timeout=90,headers={'Origin':'http://127.0.0.1:8896'}) as c:
 c.post('/api/login',json={'code':(folder/'portal-access.txt').read_text().strip()}).raise_for_status();modes=[]
 try:
  for mode in ('FULL','LOW_POWER','CRITICAL','FULL'):
   c.post('/api/mode',json={'mode':mode}).raise_for_status();out=c.post('/api/assistant',json={'monitoring_id':'C-cycle-28','question':'What data are missing or invalid?'});out.raise_for_status();out=out.json()
   assert out['status']=='DETERMINISTIC_DATA_SUFFICIENCY' and not out['inference_attempted']
   assert out['context']['subject_id']=='v07-crew-C';modes.append({'mode':mode,'response':out})
  report['mode_transitions']=modes
  payload={'monitoring_id':'A-cycle-14','question':'Explain baseline change','history':['Crew B is recovered'],'history_context_id':'B-cycle-0'}
  def query(i):
   r=c.post('/api/assistant',json=payload);return {'status':r.status_code,'response':r.json()}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
   futures=[ex.submit(query,i) for i in range(3)];time.sleep(.1)
   health=c.get('http://127.0.0.1:8895/health');assert health.status_code==200
   concurrent=[f.result() for f in futures]
  assert sum(r['status']==200 for r in concurrent)>=1 and any(r['status']==429 for r in concurrent)
  assert all(not r['response'].get('history_used') for r in concurrent if r['status']==200)
  report['concurrent_portal']=concurrent;report['backend_available_during_llm']=True
  r=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','question':'How are baselines selected and validated?','documentary':True});r.raise_for_status();report['documentary']=r.json();assert 'documentary_explanation' in r.json()
 finally:c.post('/api/mode',json={'mode':'FULL'}).raise_for_status()
 report['status']=c.get('/api/status').json()
reader=ReaderClient('http://127.0.0.1:8895',(folder/'reader-token.txt').read_text().strip())
try:
 unavailable=ConversationalInference('http://127.0.0.1:18899','vigile-qwen3-4b:latest','FULL','ollama')
 result=answer_monitoring(reader,unavailable,'A-cycle-14','Explain baseline change',library=OfflineLibrary(None));assert not result['inference_attempted'] and result['answer'];report['unavailable_runtime_and_library']=result
finally:reader.close()
assert snapshot()==before;report['records_hash_unchanged']=before;report['audit_valid']=True
args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('mode_transitions','concurrent_portal','documentary','status','unavailable_runtime_and_library')},indent=2))
