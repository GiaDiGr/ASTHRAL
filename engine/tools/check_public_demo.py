"""Synthetic public demo admission and actual HTTPS workflow checks."""
from pathlib import Path
import argparse
import base64
import json
import ssl
import sys
import time
import httpx

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engine'))
from vigile.local_protection import read_secret
from vigile.mission_demo import SUBJECTS,MID
FOLDER=ROOT/'engine/data/cloudflare-public-demo'

def run(local=False, ai=False):
    origin='https://preflight-demo.trycloudflare.com' if local else (FOLDER/'public-origin.txt').read_text(encoding='utf8').strip()
    if local:
        (FOLDER/'public-origin.txt').write_text(origin)
    base='http://127.0.0.1:8952' if local else origin
    credentials=json.loads(read_secret(FOLDER/'demo-credentials.dpapi'))
    options=dict(base_url=base,verify=ssl.create_default_context(),trust_env=False,timeout=100,
                 headers={'Host':origin[8:]})
    def post(client,path,**body):
        return client.post('/api/'+path,json=body,headers={'Origin':origin})
    def sign_in(client,user):
        response=post(client,'login',username=user,password=credentials[user])
        assert response.status_code==200, ('LOGIN_FAILED',response.status_code)
        cookie=response.headers['set-cookie']
        assert all(value in cookie for value in ('Secure','HttpOnly','SameSite=strict'))
        if local:
            client.headers['Cookie']='vigile_session='+response.cookies['vigile_session']
        return response
    with httpx.Client(**options) as a,httpx.Client(**options) as b:
        assert a.get('/').status_code==200
        assert a.get('/api/subjects').status_code==401
        assert a.get('/api/status').status_code==401
        assert a.get('/docs').status_code==404
        assert a.get('/openapi.json').status_code==404
        assert post(a,'login',username='crew-alpha',password='invalid').status_code==401
        assert a.post('/api/login',json={'username':'crew-alpha','password':'invalid'},
                      headers={'Origin':'https://evil.invalid'}).status_code==403
        sign_in(a,'crew-alpha');sign_in(b,'crew-bravo')
        projections=[]
        for client,subject in zip((a,b),SUBJECTS):
            assert [row['id'] for row in client.get('/api/subjects').json()]==[subject]
            data=client.get('/api/dashboard/'+subject+'?mission_id='+MID).raise_for_status().json()
            assert data['profile']['id']==subject and data['profile']['synthetic']
            projections.append(data)
            frames=client.get('/api/frames/'+subject+'?mission_id='+MID).raise_for_status().json()
            assert frames
            historical=client.get('/api/dashboard/'+subject+'?mission_id='+MID+'&frame_id='+frames[-1]['id'])
            historical.raise_for_status()
            assert historical.json()['profile']['id']==subject
            assert client.get('/api/session').json()['secure_transport'] is True
        other=projections[1]
        eid=other['evaluations'][0]['id']
        for route in ('dashboard/'+SUBJECTS[1]+'?mission_id='+MID,
                      'frames/'+SUBJECTS[1]+'?mission_id='+MID,'replay/clinical/'+eid):
            denied=a.get('/api/'+route)
            assert denied.status_code==404,('FOREIGN_SCOPE',route,denied.status_code)
        assert post(a,'assistant',evaluation_id=eid,question='Explain my results').status_code==404
        for path in ('/.env','/personal.sqlite3','/vigile.sqlite3','/portal-config.json','/assets/../vigile.sqlite3',
                     '/admin','/api/register','/api/tags','/api/ps'):
            assert a.get(path).status_code==404,(path,a.get(path).status_code)
        assert post(a,'mode',mode='FULL').status_code==403
        assert a.get('/api/status').json()['clinical_execution']=='BLOCKED'
        for path in ('/','/assets/app.js','/api/subjects','/api/voice/health-history'):
            response=a.get(path)
            assert 'no-store' in response.headers['cache-control']
            assert not any(password in response.text for password in credentials.values())
        result={'transport':'LOOPBACK_HTTP_WITH_PUBLIC_HOST' if local else 'ACTUAL_CLOUDFLARE_HTTPS',
                'login':True,'secure_cookie':True,'csrf':True,'two_account_isolation':True,
                'dashboard_and_frames':True,'private_files_denied':True,'treatment_blocked':True}
        if ai:
            from vigile.voice import LocalVoice
            voice=LocalVoice()
            try:
                raw,_=voice.synthesize('My heart rate is eighty two beats per minute.','en')
            finally:
                voice.close()
            capture=post(a,'voice/health-capture',capture_id='public-sapi-'+str(time.time_ns()),
                         audio_base64=base64.b64encode(raw).decode()).raise_for_status().json()
            assert capture['status']=='DRAFT' and capture['observation']['values']==[82]
            saved=post(a,'voice/health-review',record_id=capture['record_id'],
                       transcript=capture['transcript']).raise_for_status().json()
            assert saved in a.get('/api/voice/health-history').json()
            assert saved not in b.get('/api/voice/health-history').json()
            assert post(b,'voice/health-delete',record_id=saved['record_id']).status_code==404
            reply=post(a,'assistant',monitoring_id='mission-crew-A-cycle-35',
                       question='Compare the recorded aerobic capacity and its baseline',
                       public_topic='cardiovascular').raise_for_status().json()
            result['assistant']={'status':reply['status'],'inference':reply.get('inference_trace'),
                                 'documentary':reply.get('documentary_explanation',{}).get('status'),
                                 'public_science':reply.get('supplementary_science',{}).get('status')}
            result['voice_sapi_vosk_over_transport']=True
            print(json.dumps(result),flush=True)
        assert post(a,'logout').status_code==200
        if local:a.headers.pop('Cookie',None)
        assert a.get('/api/subjects').status_code==401
        sign_in(a,'crew-alpha')
        assert a.get('/api/subjects').status_code==200
        result.update(logout=True,reconnection=True)
        (FOLDER/('preflight-results.json' if local else 'external-results.json')).write_text(json.dumps(result,indent=2))
        print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--local',action='store_true')
    parser.add_argument('--ai',action='store_true')
    args=parser.parse_args()
    run(args.local,args.ai)
