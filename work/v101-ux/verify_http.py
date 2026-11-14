from pathlib import Path
import sys,json,httpx,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'));D=R/'docs/v101-ux';F=R/'engine/data/mission-v101-astronaut'
from vigile.local_protection import read_secret
base='http://127.0.0.1:8912';backend='http://127.0.0.1:8911';checks=[]
with httpx.Client(trust_env=False,timeout=30) as c:
 health=c.get(backend+'/health');health.raise_for_status();assert health.json()['clinical_execution']=='BLOCKED'
 c.post(base+'/api/login',json={'code':read_secret(F/'portal-access.txt')},headers={'Origin':base}).raise_for_status()
 for asset,needle in [('app.js','Unidades heterogéneas'),('management.js','renderAstronautGuidance'),('style.css','.journey-links')]:
  response=c.get(base+'/assets/'+asset);response.raise_for_status();assert needle in response.text
 page=c.get(base+'/');page.raise_for_status();assert 'id="journey"' in page.text
 for sid,day in [('A','35'),('A','21'),('B','18'),('B','18p1'),('B','47')]:
  subject='mission-crew-'+sid;frame='frame-'+subject+'-cycle-'+day
  response=c.get(base+'/api/dashboard/'+subject,params={'mission_id':'mission-v011','frame_id':frame});response.raise_for_status();data=response.json()
  assert data['profile']['id']==subject and all(r['measurement']['subject_id']==subject for r in data['measurements'])
  current=data['monitoring'][-1];assert current['id']==subject+'-cycle-'+day
  if sid=='B' and day in ('18','18p1'):
   e=current['clinical_evaluations']['DKA'];assert e['urgency']=='EMERGENCY' and e['treatment_status']=='NOT_STARTED';assert e['management']['DKA']['clinical_execution']=='BLOCKED'
  checks.append({'subject':subject,'frame':frame,'cycle':current['id'],'clinical_execution':data['clinical_execution'],'http_status':200})
 bad=c.get(base+'/api/dashboard/mission-crew-A',params={'mission_id':'mission-v011','frame_id':'frame-mission-crew-B-cycle-18'});assert bad.status_code==403
 denied=c.post(backend+'/monitoring/cycles',headers={'Authorization':'Bearer '+read_secret(F/'reader-token.txt')},json={});assert denied.status_code==403
 origin=c.post(base+'/api/mode',headers={'Origin':'https://untrusted.invalid'},json={'mode':'FULL'});assert origin.status_code==403
 c.post(base+'/api/logout',headers={'Origin':base}).raise_for_status()
a=json.loads((R/'engine/data/mission-v100-r2/mission-report.json').read_text(encoding='utf8'));b=json.loads((F/'mission-report.json').read_text(encoding='utf8'))
normalized=[{k:v for k,v in row.items() if k!='resource_policy'} for row in b['requests']]
assert normalized==a['requests'] and a['semantic_hash']==b['semantic_hash']
result={'date':'2026-11-02','loopback_HTTP':True,'portal':base,'backend':backend,'checks':checks,'cross_astronaut_frame_status':403,'reader_write_status':403,'cross_origin_status':403,'new_assets_served':True,'credentials_omitted':True,'real_browser_visual_QA':'PENDING_KERNEL_ASSETS_OS_ERROR_3','original_mission_semantic_hash':a['semantic_hash'],'new_mission_semantic_hash':b['semantic_hash'],'requests_equal_after_removing_only_v101_resource_policy_default':True,'new_default_resource_policy':list({row['resource_policy'] for row in b['requests']}),'inference_requested_by_this_check':False}
(D/'http-and-invariance.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))