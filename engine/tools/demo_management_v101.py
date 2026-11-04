"""Fresh synthetic therapeutic support demonstration. No NASA inventory or administration.
prepare refuses existing folders; serve starts only its own loopback children.
"""
from pathlib import Path
import argparse,json,sys,secrets,hashlib,os,subprocess,socket,time
from datetime import timedelta
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))

def prepare(folder,backend_port=8901):
 from fastapi.testclient import TestClient
 from vigile.api import create_app
 from vigile.clinical_demo import run
 from vigile.clinical_simulator import AS_OF,observation
 from vigile.clinical_models import ClinicalRequest
 from vigile.management import MedicalResource,InventoryVersion,ManagementRecord,append_inventory,append_management_record
 from vigile.models import EpisodeRequest,FollowUpPlan
 from vigile.monitoring_models import MonitoringRequest
 from vigile.local_protection import protect_secret,restrict_directory
 folder=folder.resolve();run(ROOT,folder) # Existing synthetic clinical demo, fresh folder.
 writer,reader,operator,code=[secrets.token_urlsafe(32) for _ in range(4)]
 scope={'subject_ids':['clinical-crew'],'mission_ids':['clinical-earth']}
 tokens={writer:'researcher',reader:{'id':'v101-reader','role':'reader',**scope},operator:{'id':'v101-operator','role':'operator',**scope}}
 report={'version':'1.0.1','synthetic':True,'clinical_validation':False,'clinical_execution':'BLOCKED','scenarios':[],'inventory_is_not_NASA':True}
 with TestClient(create_app(ROOT,folder/'vigile.sqlite3',tokens)) as client:
  service=client.app.state.clinical;engine=client.app.state.engine;T=AS_OF
  dka=json.loads((folder/'request-dka.json').read_text(encoding='utf8'))
  original=next(r for r in engine.store.all('clinical_evaluation') if r['snapshot']['request']['condition_id']=='DKA' and not r['parent_id'])
  def manifest(n,state='AVAILABLE',expired=False,unknown_monitor=False):
   at=T+timedelta(hours=(n-1)*2,minutes=1);names=service.knowledge.protocols['PROT-DKA-ADULT-2024']['required_resources'];rows=[]
   for name in names:
    med=name=='insulin_inventory'
    rows.append(MedicalResource(id=name,kind='MEDICATION' if med else 'CAPABILITY',label='FICTIONAL_TEST_RESOURCE_'+name,quantity=3,unit='fictional-item',availability='UNKNOWN' if unknown_monitor and name=='continuous_or_frequent_monitoring' else state if med else 'AVAILABLE',verification='VERIFIED',verified_at=at,expires_at=T+timedelta(hours=1) if expired and med else T+timedelta(days=30),storage_status='COMPLIANT',storage_conditions='FICTIONAL_ONLY_NOT_DRUG_STORAGE_ADVICE',integrity_status='INTACT',requires_cold_chain=False,updated_at=at,source='SYNTHETIC_NON_NASA_MANIFEST',responsible='FICTIONAL_INVENTORY_OPERATOR'))
   return InventoryVersion(id='v101-inventory-'+str(n),mission_id='clinical-earth',version=n,supersedes='v101-inventory-'+str(n-1) if n>1 else None,effective_at=at,updated_at=at,source='SYNTHETIC_NON_NASA_MANIFEST',responsible='FICTIONAL_RESEARCHER',resources=rows)
  last=None
  for n,label,expired,unknown,potassium in [(1,'DKA_NO_POTASSIUM',False,False,None),(2,'DKA_EXPIRED_RESOURCE',True,False,4),(3,'DKA_MONITORING_UNKNOWN',False,True,4),(4,'DKA_RESOURCES_AVAILABLE_AUTHORIZATION_STILL_BLOCKED',False,False,4)]:
   append_inventory(engine,manifest(n,expired=expired,unknown_monitor=unknown),'researcher')
   raw={**dka,'resource_policy':'MISSION_INVENTORY','as_of':(T+timedelta(hours=(n-1)*2+1)).isoformat()}
   if potassium is not None:raw['observations']=raw['observations']+[observation('potassium_mmol_l',potassium,timestamp=T+timedelta(hours=(n-1)*2+1),sample='potassium-'+str(n)).model_dump(mode='json')]
   out=service.evaluate(ClinicalRequest.model_validate(raw),'researcher',last['id'] if last else None);last=out
   assert out['results']['DKA']['diagnostic_status']==original['results']['DKA']['diagnostic_status']=='CRITERIA_MET'
   assert out['urgency']=='EMERGENCY' and out['treatment_status']=='NOT_STARTED'
   report['scenarios'].append({'label':label,'evaluation':out})
  request=ClinicalRequest(subject_id='clinical-crew',mission_id='clinical-earth',condition_id='ANAPHYLAXIS',population='NONPREGNANT_ADULT',as_of=T+timedelta(hours=7),window_start=T-timedelta(hours=1),resource_policy='MISSION_INVENTORY',observations=[observation('known_or_highly_probable_allergen',True),observation('respiratory_compromise',True)])
  ana=service.evaluate(request,'researcher');assert ana['urgency']=='EMERGENCY' and ana['results']['ANAPHYLAXIS']['diagnostic_status']!='CRITERIA_MET';report['scenarios'].append({'label':'ANAPHYLAXIS_URGENT_SUSPECTED_WITHOUT_RESOURCES','evaluation':ana})
  cycle=client.app.state.monitoring.run(MonitoringRequest(id='v101-management-cycle',subject_id='clinical-crew',mission_id='clinical-earth',as_of=T+timedelta(hours=8),history_start=T-timedelta(days=1),clinical_window_start=T-timedelta(hours=1),clinical_context_id='v101-dka',policy_reference='SYNTHETIC_THERAPEUTIC_SOFTWARE_DEMO',population='NONPREGNANT_ADULT',age_years=30,resource_policy='MISSION_INVENTORY',observations=[observation(k,v) for k,v in {'known_diabetes':True,'plasma_glucose_mg_dl':180,'beta_hydroxybutyrate_mmol_l':4.2,'venous_pH':7.22,'potassium_mmol_l':4}.items()]),'researcher')
  current=cycle['clinical_evaluations']['DKA'];episode=cycle['episode_ids']['DKA'];at=T+timedelta(hours=8);plan='v101-human-review-plan'
  engine.followup(FollowUpPlan(id=plan,episode_id=episode,due_at=at+timedelta(hours=1),goal_description='Synthetic human review of documented management and pending data; not a treatment order',protocol_reference='SYNTHETIC_ONLY'),'researcher')
  records=[]
  for n,status in enumerate(['DOCUMENTED','PROPOSED','REVIEW_PENDING','HUMAN_REPORTED_PERFORMED','POST_INTERVENTION_OBSERVATION']):
   row=ManagementRecord(id='v101-report-'+str(n),episode_id=episode,evaluation_id=current['id'],intervention_id=current['management']['DKA']['interventions'][0]['id'],status=status,occurred_at=at,recorded_at=at,source='FICTIONAL_OPERATOR_RECORD_NO_REAL_TREATMENT',reported_authority='CLAIMED_ONLY_NOT_VERIFIED',note='Synthetic demonstration: this declaration does not show administration by VIGILE, authorization or efficacy.',followup_plan_id=plan,data_needed_for_reevaluation=['HUMAN_PROTOCOL_REVIEW','FOLLOWUP_DATA_AS_AUTHORIZED'])
   response=client.post('/clinical/management-records',json=row.model_dump(mode='json'),headers={'Authorization':'Bearer '+operator});response.raise_for_status();records.append(response.json())
  from vigile.mission_frames import capture_frame
  report['frame']=capture_frame(client.app,'v101-management-frame',cycle['id'])
  report['monitoring']=cycle;report['management_records']=records
  report['clinical_replays']=[service.replay(r['id']) for r in engine.store.all('clinical_evaluation')]
  report['monitoring_replays']=[client.app.state.monitoring.replay(cycle['id'])]
  assert all(r['matches'] for r in report['clinical_replays']+report['monitoring_replays']) and engine.store.verify()
  report['audit_valid']=True
  (folder/'openapi.json').write_text(json.dumps(client.app.openapi(),indent=2),encoding='utf8')
 mapping={'sha256:'+hashlib.sha256(t.encode()).hexdigest():p for t,p in tokens.items() if t!=writer}
 protect_secret(json.dumps(mapping),folder/'server-tokens.json');protect_secret(reader,folder/'reader-token.txt');protect_secret(operator,folder/'operator-token.txt');protect_secret(code,folder/'portal-access.txt')
 config={'backend_url':'http://127.0.0.1:'+str(backend_port),'reader_token_file':str(folder/'reader-token.txt'),'access_code_file':str(folder/'portal-access.txt'),'mode':'FULL','model_url':'http://127.0.0.1:8891','model':'vigile-qwen3-4b:latest','inference_provider':'ollama','library_manifest':str(ROOT/'engine/local_ai/library-v080.json'),'voice_enabled':True,'structured_explanations':True}
 (folder/'portal-config.json').write_text(json.dumps(config,indent=2),encoding='utf8');restrict_directory(folder)
 (folder/'management-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps({'scenarios':len(report['scenarios']),'clinical_replays':len(report['clinical_replays']),'monitoring_replays':len(report['monitoring_replays']),'all_match':True,'therapeutic_execution':'BLOCKED','real_treatment_administered':False}))
 return report

def serve(folder,backend_port,portal_port):
 folder=folder.resolve()
 for port in (backend_port,portal_port):
  with socket.socket() as s:s.bind(('127.0.0.1',port))
 config=json.loads((folder/'portal-config.json').read_text());assert config['backend_url']=='http://127.0.0.1:'+str(backend_port)
 env={k:v for k,v in os.environ.items() if not k.startswith('VIGILE_')};backend={**env,'VIGILE_DB':str(folder/'vigile.sqlite3'),'VIGILE_TOKEN_FILE':str(folder/'server-tokens.json')}
 commands=[([sys.executable,'-m','uvicorn','vigile.api:create_app','--factory','--host','127.0.0.1','--port',str(backend_port),'--no-access-log'],backend),([sys.executable,'-m','vigile.portal','--config',str(folder/'portal-config.json'),'--port',str(portal_port)],env)]
 children=[]
 try:
  for cmd,childenv in commands:children.append(subprocess.Popen(cmd,cwd=ROOT/'engine',env=childenv,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
  print('VIGILE v1.0.1 synthetic demo: http://127.0.0.1:'+str(portal_port)+'; own child PIDs '+','.join(str(p.pid) for p in children),flush=True)
  while all(p.poll() is None for p in children):time.sleep(.5)
 finally:
  for p in children:
   if p.poll() is None:p.terminate()
  for p in children:p.wait(timeout=10)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','serve']);p.add_argument('--output',type=Path,required=True);p.add_argument('--backend-port',type=int,default=8901);p.add_argument('--portal-port',type=int,default=8902);a=p.parse_args()
 if a.command=='prepare':prepare(a.output,a.backend_port)
 else:serve(a.output,a.backend_port,a.portal_port)
if __name__=='__main__':main()