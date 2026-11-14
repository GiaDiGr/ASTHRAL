from pathlib import Path
import sys,json,httpx,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import read_secret
folder=R/'engine/data/mission-v100-r2';origin='http://127.0.0.1:8898'
with httpx.Client(trust_env=False,timeout=15) as c:
 health=c.get('http://127.0.0.1:8897/health');health.raise_for_status()
 token=read_secret(folder/'reader-token.txt');headers={'Authorization':'Bearer '+token}
 subjects=c.get('http://127.0.0.1:8897/dashboard/subjects',headers=headers);subjects.raise_for_status();assert len(subjects.json())==2
 denied=c.post('http://127.0.0.1:8897/measurements',headers=headers,json={});assert denied.status_code==403
 login=c.post(origin+'/api/login',headers={'Origin':origin},json={'code':read_secret(folder/'portal-access.txt')});login.raise_for_status()
 status=c.get(origin+'/api/status');status.raise_for_status();voice=c.get(origin+'/api/voice/status');voice.raise_for_status()
 refused_origin=c.post(origin+'/api/mode',headers={'Origin':'http://untrusted.invalid'},json={'mode':'CRITICAL'});assert refused_origin.status_code==403
 assert voice.json()['stt']['en']['available'] and voice.json()['stt']['es']['available'] and voice.json()['tts']['en']['available'] and voice.json()['tts']['es']['available']
 c.post(origin+'/api/logout',headers={'Origin':origin}).raise_for_status()
 report={'real_http_loopback':True,'health':health.json(),'scoped_subjects':len(subjects.json()),'reader_write_denied_status':denied.status_code,'origin_rejected_status':refused_origin.status_code,'portal_version':status.json()['version'],'voice_status':voice.json(),'credentials_cookies_omitted':True,'physical_microphone_test':False}
(R/'docs/v100/LIVE_HTTP_CHECK.json').write_text(json.dumps(report,indent=2),encoding='utf8')
f=json.loads((R/'docs/v100/CANDIDATE_R2_FREEZE.json').read_text(encoding='utf8'))
assert all(hashlib.sha256((R/rel).read_bytes()).hexdigest()==h for rel,h in f['files'].items())
print('LIVE HTTP: two scoped subjects; reader write denied 403; cross-origin rejected 403; EN/ES STT/TTS available; frozen code unchanged.')