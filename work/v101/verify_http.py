from pathlib import Path
import sys,json,httpx
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
folder=R/'engine/data/mission-v101-final';base='http://127.0.0.1:8902'
with httpx.Client(trust_env=False,timeout=20) as c:
 r=c.get('http://127.0.0.1:8901/health');r.raise_for_status();assert r.json()['version']=='1.0.1'
 login=c.post(base+'/api/login',headers={'Origin':base},json={'code':read_secret(folder/'portal-access.txt')});login.raise_for_status()
 asset=c.get(base+'/assets/management.js');asset.raise_for_status();assert 'renderManagement101' in asset.text
 page=c.get(base+'/');page.raise_for_status();assert '/assets/management.js' in page.text
 data=c.get(base+'/api/dashboard/clinical-crew',params={'mission_id':'clinical-earth','frame_id':'v101-management-frame'});data.raise_for_status();data=data.json()
 current=next(e for e in data['evaluations'] if e['id']==data['monitoring'][-1]['clinical_evaluations']['DKA']['id'])
 assert current['management']['DKA']['resource_snapshot']['inventory_version']==4 and len(data['management_records'])==5
 assert data['clinical_execution']=='BLOCKED' and current['urgency']=='EMERGENCY'
 denied=c.post(base+'/api/mode',headers={'Origin':'http://untrusted.invalid'},json={'mode':'FULL'});assert denied.status_code==403
 c.post(base+'/api/logout',headers={'Origin':base}).raise_for_status()
 report={'real_loopback_http':True,'version':'1.0.1','reader_dashboard_and_management_asset':True,'frozen_frame':'v101-management-frame','inventory_version':4,'management_records':5,'urgency':current['urgency'],'clinical_execution':'BLOCKED','cross_origin_status':403,'credentials_and_cookies_omitted':True,'real_browser_visual_inspection':'UNAVAILABLE_CUA_KERNEL_ASSETS_PATH_ERROR','physical_voice_test':False}
(R/'docs/v101/http-integration.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))