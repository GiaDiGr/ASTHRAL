from pathlib import Path
import sys,json,httpx,time,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));F=R/'engine/data/asthral-release';D=R/'docs/asthral'
from vigile.local_protection import read_secret
base='http://127.0.0.1:8922';origin={'Origin':base};rows=[]
with httpx.Client(trust_env=False,timeout=90) as c:
 page=c.get(base+'/');page.raise_for_status();assert '<html lang="en">' in page.text and 'VIGILE' not in page.text
 c.post(base+'/api/login',json={'code':read_secret(F/'portal-access.txt')},headers=origin).raise_for_status()
 status=c.get(base+'/api/status');status.raise_for_status();assert status.json()['scientific_retrieval']['network_permitted']
 def ask(label,payload):
  start=time.perf_counter();response=c.post(base+'/api/assistant',json=payload,headers=origin);response.raise_for_status();a=response.json();assert a['assistant_identity']=='ASTHRAL' and a['language']=='en'
  row={'case':label,'status':a['status'],'latency_seconds':time.perf_counter()-start,'generated_sentences':len(a.get('generated',[])),'model_requests':a['inference_trace']['model_requests_attempted'],'science_status':a['supplementary_science']['status'],'science_delivery':a['supplementary_science']['delivery'],'references':a['supplementary_science']['documents'],'message':a['message']};rows.append(row);return a
 a=ask('local_personal_baseline',{'monitoring_id':'mission-crew-A-cycle-35','question':'What changed from my personal baseline?','language':'en'})
 data=ask('DKA_missingness_with_public_science',{'monitoring_id':'mission-crew-B-cycle-18','question':'Which data are missing?','public_topic':'hyperglycemic_consensus','language':'en'})
 assert data['supplementary_science']['status']=='REMOTE_OPTIONAL'
 assert any('optional' in b['text'].lower() or 'alternatives' in b['text'].lower() for b in data['answer'])
 for mode in ['LOW_POWER','CRITICAL']:
  c.post(base+'/api/mode',json={'mode':mode},headers=origin).raise_for_status()
  result=ask(mode,{'monitoring_id':'mission-crew-B-cycle-18','question':'Which criteria are met?','public_topic':'radiation','language':'en'})
  assert result['supplementary_science']['status']=='LOCAL_ONLY' and not result['supplementary_science']['documents']
 c.post(base+'/api/mode',json={'mode':'FULL'},headers=origin).raise_for_status()
 c.post(base+'/api/logout',json={},headers=origin).raise_for_status()
report={'real_loopback_HTTP':True,'English_UI_and_ASTHRAL_identity':True,'model':'vigile-qwen3-4b:latest','model_configuration_changed':False,'status_before':{'assistant':status.json()['assistant'],'scientific_retrieval':status.json()['scientific_retrieval']},'cases':rows,'credentials_omitted':True,'physical_microphone':False,'visual_acceptance':'PENDING_COMPUTER_USE_URL_POLICY_STOP','no_Internet_disconnection_claim':True}
(D/'http-assistant-smoke.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps([{k:r[k] for k in ['case','status','generated_sentences','model_requests','science_status','science_delivery']} for r in rows]))