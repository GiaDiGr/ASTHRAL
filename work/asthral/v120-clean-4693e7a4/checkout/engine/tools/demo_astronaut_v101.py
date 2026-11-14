"""Unchanged seeded mission + v1.0.1 documentary management; no new clinical scenarios.
No Internet or inference is requested by preparation/verification. Serve is loopback only.
"""
from pathlib import Path
import argparse,json,sys
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))

def prepare(folder,backend_port=8911):
 from vigile.mission_demo import prepare as original_prepare
 summary=original_prepare(folder,seed=42,verify_replays=True)
 config_path=folder/'portal-config.json';config=json.loads(config_path.read_text(encoding='utf8'));config['backend_url']='http://127.0.0.1:'+str(backend_port)
 config_path.write_text(json.dumps(config,indent=2),encoding='utf8')
 print(json.dumps({k:summary[k] for k in ('cycles','request_hash','semantic_hash','audit_integrity','assistant')}))

def verify(folder,report_path):
 from vigile.api import create_app
 from vigile.local_protection import read_secret
 from vigile.store import digest
 from fastapi.testclient import TestClient
 tokens=json.loads(read_secret(folder/'server-tokens.json'));header={'Authorization':'Bearer '+read_secret(folder/'reader-token.txt')}
 with TestClient(create_app(ROOT,folder/'vigile.sqlite3',tokens)) as c:
  engine=c.app.state.engine;frames=engine.store.all('mission_frame');checks=[]
  for row in frames:
   sid=row['scope']['subject_id'];mid=row['scope']['mission_id'];response=c.get('/dashboard/subjects/'+sid,params={'mission_id':mid,'frame_id':row['index']['id']},headers=header);response.raise_for_status();data=response.json()
   assert data['profile']['id']==sid and data['profile']['mission_id']==mid
   assert all(m['measurement']['subject_id']==sid and m['measurement']['mission_id']==mid for m in data['measurements'])
   assert all(datetime.fromisoformat(e['as_of'])<=datetime.fromisoformat(data['historical_frame']['as_of']) for e in data['evaluations'])
   checks.append({'frame':row['index']['id'],'scope':row['scope'],'snapshot_hash':row['index']['snapshot_hash'],'matches':True})
  denied=c.post('/monitoring/cycles',json={},headers=header);assert denied.status_code==403
  wrong=c.get('/dashboard/subjects/mission-crew-A',params={'mission_id':'mission-v011','frame_id':'frame-mission-crew-B-cycle-18'},headers=header);assert wrong.status_code==403
  clinical=[c.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')];monitoring=[c.app.state.monitoring.replay(r['id']) for r in engine.store.all('monitoring_run')]
  assert all(r['matches'] for r in clinical+monitoring) and engine.store.verify()
  output={'format':'VIGILE_ASTRONAUT_UX_VERIFICATION_1','frames':checks,'reader_write_status':denied.status_code,'cross_astronaut_frame_status':wrong.status_code,'clinical_replays':clinical,'monitoring_replays':monitoring,'audit_valid':True,'clinical_execution':'BLOCKED','clinical_validation':False,'visual_QA':'PENDING_TOOL_INITIALIZATION_FAILURE','inference_requests':0,'source_of_data':'UNCHANGED_V011_SEED_42','implementation_hash':engine.implementation_hash}
 report_path.parent.mkdir(parents=True,exist_ok=True)
 with report_path.open('x',encoding='utf8') as f:json.dump(output,f,indent=2)
 print(json.dumps({'frames':len(checks),'clinical_replays':len(clinical),'monitoring_replays':len(monitoring),'all_match':True,'reader_write':403,'cross_astronaut_frame':403}))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','serve','verify']);p.add_argument('--output',type=Path,required=True);p.add_argument('--backend-port',type=int,default=8911);p.add_argument('--portal-port',type=int,default=8912);p.add_argument('--report',type=Path);a=p.parse_args();folder=a.output.resolve()
 if a.command=='prepare':prepare(folder,a.backend_port)
 elif a.command=='serve':
  from demo_management_v101 import serve
  serve(folder,a.backend_port,a.portal_port)
 else:
  if not a.report:p.error('--report requires a new report file')
  verify(folder,a.report)
if __name__=='__main__':main()