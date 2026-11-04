import json,sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from test_portal import dataset,services,login,TestReader,NoModel
from vigile.portal import create_portal
from vigile.api import create_app
from vigile.offline_library import OfflineLibrary
from vigile.portal_documents import exact_fragment
from conftest import ROOT

def test_rotating_cookie_and_idle_expiry(dataset):
 now=[0];config=json.loads((dataset/'portal-config.json').read_text());config.update(session_idle_seconds=5,session_absolute_seconds=12)
 mapping=json.loads((dataset/'server-tokens.json').read_text())
 with TestClient(create_app(ROOT,dataset/'vigile.sqlite3',mapping)) as backend:
  bridge=TestReader(backend,(dataset/'reader-token.txt').read_text())
  with TestClient(create_portal(config,bridge,NoModel(),clock=lambda:now[0]),base_url='http://127.0.0.1:8766') as client:
   login(client,config);first=client.cookies.get('vigile_session');now[0]=4
   assert client.get('/api/session').json()['idle_seconds_remaining']==1
   response=client.post('/api/session/renew',json={},headers={'Origin':'http://127.0.0.1:8766'});assert response.status_code==200
   assert client.cookies.get('vigile_session')!=first
   now[0]=9;assert client.get('/api/subjects').status_code==401

def test_rate_limit_and_no_secret_in_validation(services):
 _,portal,_,config=services;login(portal,config)
 for _ in range(120):assert portal.get('/api/session').status_code==200
 response=portal.get('/api/subjects');assert response.status_code==429 and response.headers['retry-after']=='60'
 assert 'no-store' in response.headers['cache-control']

def test_sqlite_failure_is_not_normal_or_secret(services):
 _,portal,bridge,config=services;login(portal,config)
 bridge.get=lambda _:(_ for _ in ()).throw(sqlite3.OperationalError('SECRET_PATH'))
 response=portal.get('/api/subjects');assert response.status_code==503
 assert response.json()=={'detail':'STORAGE_UNAVAILABLE'}

def test_status_backend_failure_degrades_explicitly(services):
 _,portal,bridge,config=services;login(portal,config)
 bridge.get=lambda _:(_ for _ in ()).throw(RuntimeError('SECRET'))
 state=portal.get('/api/status');assert state.status_code==200
 assert state.json()['backend']=='UNAVAILABLE_OR_ACCESS_DENIED' and 'SECRET' not in state.text

def test_scoped_replay_and_no_arbitrary_document_path(services):
 _,portal,_,config=services;login(portal,config)
 data=portal.get('/api/dashboard/clinical-crew?mission_id=clinical-earth').json()
 result=portal.get('/api/replay/clinical/'+data['evaluations'][0]['id']);assert result.status_code==200 and result.json()['matches']
 assert portal.get('/api/replay/clinical/unauthorized').status_code!=200
 assert portal.get('/api/document/server-tokens.json').status_code==404

def test_verified_exact_fragment_and_corrupt_manifest(tmp_path):
 manifest=ROOT/'engine/local_ai/library-v080.json';value=json.loads(manifest.read_text(encoding='utf8'));block=value['blocks'][0]
 actual=exact_fragment(OfflineLibrary(manifest),block['id']);assert actual['text']==block['text'] and actual['relevance']=='NOT_INDEPENDENTLY_VALIDATED'
 value['blocks'][0]['text']='tampered';bad=tmp_path/'library.json';bad.write_text(json.dumps(value),encoding='utf8')
 with pytest.raises(HTTPException) as error:exact_fragment(OfflineLibrary(bad),block['id'])
 assert error.value.status_code==503

def test_session_cross_origin_and_body_limit(services):
 _,portal,_,config=services;login(portal,config)
 assert portal.get('/api/subjects',headers={'Origin':'https://evil.example'}).status_code==403
 assert portal.get('/api/subjects',headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
 assert portal.post('/api/assistant',content=b'x'*16385,headers={'Origin':'http://127.0.0.1:8766'}).status_code==413


@pytest.mark.parametrize('upstream,expected',[(403,403),(404,404)])
def test_backend_denials_preserve_safe_http_semantics(services,upstream,expected):
 _,portal,bridge,config=services;login(portal,config)
 bridge.get=lambda _:(_ for _ in ()).throw(RuntimeError('HTTP_'+str(upstream)+' GET /SECRET_PATH'))
 response=portal.get('/api/subjects');assert response.status_code==expected and 'SECRET_PATH' not in response.text


def test_inference_trace_does_not_confuse_accepted_output_with_requests(services):
 _,portal,_,config=services;login(portal,config);portal.app.state.inference.model_http_calls=0
 data=portal.get('/api/dashboard/clinical-crew?mission_id=clinical-earth').json()
 reply=portal.post('/api/assistant',json={'evaluation_id':data['evaluations'][0]['id'],'question':'¿Qué datos faltan?'},headers={'Origin':'http://127.0.0.1:8766'})
 assert reply.status_code==200
 assert reply.json()['inference_trace']['model_requests_attempted']==0
 assert reply.json()['inference_trace']['explanation_accepted'] is False
