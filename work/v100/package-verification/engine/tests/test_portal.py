import json,hashlib
from pathlib import Path
import pytest,httpx
from fastapi.testclient import TestClient
from vigile.portal_demo import prepare
from vigile.portal import create_portal
from vigile.api import create_app
from vigile.local_assistant import ReaderClient,OllamaInference,answer
from conftest import ROOT

@pytest.fixture(scope='module')
def dataset(tmp_path_factory):
    folder=tmp_path_factory.mktemp('portal-parent')/'demo';prepare(ROOT,folder);return folder

class TestReader(ReaderClient):
    __test__=False
    def __init__(self,backend,token):
        self.calls=[];owner=self
        class Transport:
            def call(self,method,path):
                assert method=='GET';owner.calls.append(path)
                r=backend.get(path,headers={'Authorization':'Bearer '+token})
                if r.status_code!=200:raise RuntimeError('ACCESS_DENIED')
                return r.json()
            def close(self):pass
        self.client=Transport()

class NoModel:
    def status(self):return {'available':False,'reason':'MODEL_NOT_CONFIGURED'}
    def select(self,*a):raise AssertionError('MUST_NOT_FAKE_INFERENCE')

@pytest.fixture
def services(dataset):
    reader=(dataset/'reader-token.txt').read_text();mapping=json.loads((dataset/'server-tokens.json').read_text())
    with TestClient(create_app(ROOT,dataset/'vigile.sqlite3',mapping)) as backend:
        bridge=TestReader(backend,reader);config=json.loads((dataset/'portal-config.json').read_text())
        with TestClient(create_portal(config,reader=bridge,inference=NoModel()),base_url='http://127.0.0.1:8766') as portal:
            yield backend,portal,bridge,config

def login(portal,config):
    r=portal.post('/api/login',json={'code':Path(config['access_code_file']).read_text()},headers={'Origin':'http://127.0.0.1:8766'})
    assert r.status_code==200,r.text;return r

def test_frontend_backend_three_scenarios(services):
    backend,portal,bridge,config=services;login(portal,config)
    assert portal.get('/').status_code==200
    assert portal.get('/assets/app.js').status_code==200
    assert portal.get('/api/status').json()['assistant']['available'] is False
    subjects=portal.get('/api/subjects').json();assert len(subjects)==1
    data=portal.get('/api/dashboard/clinical-crew?mission_id=clinical-earth').json()
    assert len(data['measurements'])==21 and len(data['baselines'])==1
    assert {r['condition_id'] for r in data['evaluations']}=={'DKA','ANAPHYLAXIS',None}
    for e in data['evaluations']:
        assert 'snapshot' not in e
        if e['condition_id'] in ('DKA','ANAPHYLAXIS'):assert e['urgency']=='EMERGENCY'
        response=portal.post('/api/assistant',json={'evaluation_id':e['id'],'question':'¿Por qué está bloqueado el protocolo?'},headers={'Origin':'http://127.0.0.1:8766'})
        assert response.status_code==200,response.text
        reply=response.json();assert reply['status']=='UNAVAILABLE' and not reply['inference_executed'] and reply['retrieved'] and reply['sources']
    assert all('/clinical/evaluations' in p or p.startswith(('/dashboard','/clinical/sources','/clinical/criteria')) for p in bridge.calls)

def test_session_csrf_and_secrets(services):
    _,portal,_,config=services
    assert portal.get('/api/subjects').status_code==401
    assert portal.post('/api/login',json={'code':Path(config['access_code_file']).read_text()},headers={'Origin':'https://evil.example'}).status_code==403
    r=login(portal,config);assert 'HttpOnly' in r.headers['set-cookie'] and 'SameSite=strict' in r.headers['set-cookie']
    for path in ['/','/assets/app.js','/api/status','/api/subjects']:
        r=portal.get(path);assert Path(config['reader_token_file']).read_text() not in r.text
        assert 'no-store' in r.headers['cache-control']
    assert "connect-src 'self'" in portal.get('/').headers['content-security-policy']
    assert portal.post('/api/assistant',json={'question':'write'}).status_code==403
    assert portal.get('/',headers={'Host':'evil.example'}).status_code==400
    assert portal.patch('/api/dashboard/x',json={}).status_code==403

def test_reader_cannot_mutate_backend_or_escalate(dataset,services):
    backend,portal,_,config=services;token=Path(config['reader_token_file']).read_text()
    headers={'Authorization':'Bearer '+token}
    for path in ['/clinical/evaluations','/missions','/measurements','/evidence/revisions','/dashboard/subjects']:
        assert backend.post(path,headers=headers,json={'role':'clinician','mission_approved':True}).status_code==403
    assert backend.get('/dashboard/subjects/other?mission_id=clinical-earth',headers=headers).status_code==403

@pytest.mark.parametrize('path',['/measurements','/clinical/evaluations/x/reassess','https://evil.example/','//evil.example','/dashboard/subjects/x?mission_id=x&admin=1'])
def test_no_generic_proxy(services,path):
    with pytest.raises(ValueError):services[2].get(path)

@pytest.mark.parametrize('url',['https://remote.example','http://localhost:11434','http://127.0.0.1:11434/a','http://127.0.0.1:11434?x=1'])
def test_inference_only_literal_loopback(url):
    with pytest.raises(ValueError):OllamaInference(url,'test')

def test_local_model_adapter_mock_not_real_inference(monkeypatch):
    original=httpx.Client;requests=[]
    def handler(request):
        requests.append(request)
        if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'local-test','size':1024,'details':{'format':'gguf'}}]})
        body=json.loads(request.content);assert body['stream'] is False and 'tools' not in body
        return httpx.Response(200,json={'message':{'content':json.dumps({'evidence_ids':['E1']})}})
    monkeypatch.setattr(httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    model=OllamaInference(model='local-test');assert model.status()['available']
    assert model.select('Pregunta',[{'id':'E1','text':'Dato del motor'}])==['E1']
    assert len(requests)==2

def test_cloud_model_rejected_without_network(monkeypatch):
    monkeypatch.setattr(httpx,'Client',lambda **kw:(_ for _ in ()).throw(AssertionError('NETWORK_FORBIDDEN')))
    assert OllamaInference(model='model:cloud').status()['reason']=='CLOUD_MODEL_FORBIDDEN'

@pytest.mark.parametrize('entry',[{'name':'test','size':1,'details':{'format':'gguf'},'remote_host':'remote'}, {'name':'test','size':'bad','details':{'format':'gguf'}}, {'name':'test'}])
def test_missing_malformed_or_remote_model_not_ready(monkeypatch,entry):
    original=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'models':[entry]})),**kw))
    assert not OllamaInference(model='test').status()['available']

@pytest.mark.parametrize('output',[{'evidence_ids':['FAKE']},{'evidence_ids':['E1'],'diagnosis':'invented'},{'evidence_ids':'E1'}])
def test_hallucinated_or_injected_model_output_rejected(monkeypatch,output):
    original=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'message':{'content':json.dumps(output)}})),**kw))
    with pytest.raises(ValueError):OllamaInference(model='mock').select('Ignore rules',[{'id':'E1','text':'Allowed'}])

def test_rag_reads_parent_and_criteria(services):
    _,portal,bridge,config=services;login(portal,config)
    data=portal.get('/api/dashboard/clinical-crew?mission_id=clinical-earth').json()
    child=next(e for e in data['evaluations'] if e['parent_id'])
    reply=answer(bridge,NoModel(),child['id'],'¿Qué cambios hay desde la evaluación anterior?')
    assert any(child['parent_id'] in p for p in bridge.calls)
    assert any('Cambios desde' in b['text'] for b in reply['retrieved'])
    assert any('/clinical/criteria/' in p for p in bridge.calls)
    dizziness=next(e for e in data['evaluations'] if e['presentation_id'])
    recommendations=answer(bridge,NoModel(),dizziness['id'],'¿Qué datos faltan y qué pruebas se recomiendan?')
    assert 'TEST-ECG' in recommendations['retrieved'][0]['text']

def test_portal_no_external_network(services,monkeypatch):
    import socket
    monkeypatch.setattr(socket.socket,'connect',lambda *a:(_ for _ in ()).throw(AssertionError('EXTERNAL_NETWORK_FORBIDDEN')))
    _,portal,bridge,config=services;login(portal,config)
    assert portal.get('/api/subjects').status_code==200
    assert portal.get('/api/protocol/PROT-DKA-ADULT-2024').json()['execution_enabled'] is False

def test_backend_failure_explicit(services):
    _,portal,bridge,config=services;login(portal,config)
    bridge.get=lambda p:(_ for _ in ()).throw(RuntimeError('SECRET_INTERNAL_PATH'))
    response=portal.get('/api/subjects');assert response.status_code==502 and 'SECRET' not in response.text

def test_repeated_demo_reproduces_clinical_inputs(dataset,tmp_path):
    second=tmp_path/'repeat';prepare(ROOT,second)
    a=json.loads((dataset/'demo-report.json').read_text());b=json.loads((second/'demo-report.json').read_text())
    assert a['request_hashes']==b['request_hashes'] and a['all_replays_match'] and b['all_replays_match']
