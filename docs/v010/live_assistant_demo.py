"""Synthetic local demo; preserves engine results and restores FULL in finally.
Run only when no other operator is changing the portal's global mode.
"""
from pathlib import Path
import sys,json,httpx,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.local_protection import read_secret
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['FULL','LOW_POWER','CRITICAL'],default='LOW_POWER');a=p.parse_args();folder=ROOT/'engine/data/portal-v0100-integrated'
with httpx.Client(base_url='http://127.0.0.1:8896',headers={'Origin':'http://127.0.0.1:8896'},trust_env=False,timeout=90) as c:
 c.post('/api/login',json={'code':read_secret(folder/'portal-access.txt')}).raise_for_status()
 try:
  c.post('/api/mode',json={'mode':a.mode}).raise_for_status()
  response=c.post('/api/assistant',json={'monitoring_id':'A-cycle-14','history_context_id':'A-cycle-14','question':'How are baselines selected and validated?'});response.raise_for_status();answer=response.json()
  if a.mode=='CRITICAL':assert answer['inference_trace']['model_requests_attempted']==0
  report={'mode':a.mode,'assistant':answer,'runtime':c.get('/api/runtime').json(),'clinical_validation':False}
  (ROOT/('docs/v010/live-assistant-demo-'+a.mode+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
  print(json.dumps({'status':answer['status'],'inference_trace':answer['inference_trace'],'document_count':len(answer.get('documents',[])),'clinical_validation':False},indent=2))
 finally:
  restored=c.post('/api/mode',json={'mode':'FULL'});restored.raise_for_status();c.post('/api/logout',json={}).raise_for_status()
