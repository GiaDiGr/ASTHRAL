import base64,json,hashlib
from io import BytesIO
from pathlib import Path
import pytest,httpx
from PIL import Image
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

def test_skinguard_authenticated_local_intake_has_no_fake_results(services):
    _,portal,_,config=services
    assert portal.get('/api/skinguard/status').status_code==401
    login(portal,config)
    status=portal.get('/api/skinguard/status')
    assert status.status_code==200 and status.json()['state']=='MODEL_NOT_CONFIGURED'
    assert portal.get('/assets/skinguard.js').status_code==200
    stream=BytesIO();Image.new('RGB',(100,80),'white').save(stream,format='PNG')
    encoded=base64.b64encode(stream.getvalue()).decode('ascii')
    response=portal.post('/api/skinguard/analyze',headers={'Origin':'http://127.0.0.1:8766'},json={
        'image_data':'data:image/png;base64,'+encoded,
        'capture_date':'2026-11-14','body_site':'left forearm','uv_context':'UNKNOWN'
    })
    assert response.status_code==200,response.text
    result=response.json()
    assert result['analysis_performed'] is False
    assert result['detections']==[] and result['diagnosis'] is None
    assert result['radiation_causation'] is None
    assert 'image_data' not in result and encoded not in response.text

def test_skinguard_requires_same_origin(services):
    _,portal,_,config=services;login(portal,config)
    response=portal.post('/api/skinguard/analyze',headers={'Origin':'https://evil.example'},json={})
    assert response.status_code==403 and response.json()['detail']=='ORIGIN_REQUIRED'

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

def test_computer_vision_uses_existing_authenticated_portal(services):
    _,portal,_,config=services
    assert portal.get('/api/computer-vision/status').status_code==401
    assert portal.get('/assets/computer-vision.js').status_code==200
    assert portal.get('/assets/astronaut-earth-login.png').status_code==200
    assert portal.get('/assets/astronaut-earth-login.png').headers['content-type']=='image/png'
    login_css=portal.get('/assets/style.css').text
    assert 'rgba(255,255,255,.26)' in login_css and 'background-color:rgba(255,255,255,.92)' in login_css
    page=portal.get('/').text
    assert 'Computer Vision / Image Analysis' in page
    assert all(f'data-view="{name}"' in page for name in ('skinguard','ocularvision','echovision','motionguard'))
    vision_group=page[page.index('Computer Vision / Image Analysis'):]
    assert [vision_group.index(f'data-view="{name}"') for name in ('skinguard','ocularvision','echovision','motionguard')] == sorted(vision_group.index(f'data-view="{name}"') for name in ('skinguard','ocularvision','echovision','motionguard'))
    login(portal,config)
    status=portal.get('/api/computer-vision/status')
    assert status.status_code==200,status.text
    assert set(status.json()['modules'])=={'skinguard','ocularvision','echovision','motionguard'}
    echo=status.json()['modules']['echovision']
    assert echo['state']=='LICENSE_REVIEW_REQUIRED' and echo['execution_enabled'] is False and echo['analysis_available'] is False
    assert portal.get('/api/skinguard/status').json()['state']=='MODEL_NOT_CONFIGURED'
    headers={'Origin':'http://127.0.0.1:8766'}
    corrupt='data:image/png;base64,'+base64.b64encode(b'x'*100).decode('ascii')
    bad=portal.post('/api/computer-vision/ocular/analyze',headers=headers,json={'image_data':corrupt})
    assert bad.status_code==422 and bad.json()['detail']=='INVALID_OR_CORRUPT_OCT_IMAGE'
    medium=portal.post('/api/computer-vision/ocular/analyze',headers=headers,json={'image_data':'x'*20_000})
    assert medium.status_code==422 and medium.json()['detail']=='INVALID_REQUEST'
    not_a4c=portal.post('/api/computer-vision/echo/analyze',headers=headers,json={
        'video_data':'data:video/mp4;base64,'+base64.b64encode(b'x'*100).decode('ascii'),'filename':'not-a-scan.mp4','confirm_a4c':False
    })
    assert not_a4c.status_code==503 and not_a4c.json()['detail']=='ECHONET_PERMISSION_NOT_VERIFIED'
    policy=portal.get('/').headers['content-security-policy']
    assert 'media-src \'self\' blob:' in policy and 'camera=(self)' in portal.get('/').headers['permissions-policy']
