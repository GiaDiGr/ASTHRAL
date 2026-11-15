"""Public ingress regression. All account data is synthetic."""
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from vigile.public_origin import PublicOrigin

@pytest.fixture
def public(tmp_path):
    origin = tmp_path/'origin'
    origin.write_text('https://synthetic-demo.trycloudflare.com')
    app = FastAPI()
    @app.get('/')
    def index(request: Request):
        return {'scheme':request.url.scheme,'base':str(request.base_url),
                'headers':{k:v for k,v in request.headers.items() if 'forward' in k}}
    app.add_middleware(PublicOrigin,path=origin)
    with TestClient(app,client=('127.0.0.1',1234),base_url='http://synthetic-demo.trycloudflare.com') as client:
        yield client,origin,app

def test_scheme_comes_from_operator_origin_not_client_headers(public):
    client,_,_=public
    result=client.get('/',headers={'X-Forwarded-Proto':'http','X-Forwarded-Host':'evil.invalid',
                                   'Forwarded':'host=evil.invalid;proto=http','X-Forwarded-For':'10.0.0.1'})
    assert result.json()=={'scheme':'https','base':'https://synthetic-demo.trycloudflare.com/','headers':{}}
    assert 'no-store' in result.headers['cache-control']
    assert result.headers['strict-transport-security']=='max-age=86400'

@pytest.mark.parametrize('host',['evil.invalid','127.0.0.1','other.trycloudflare.com',
                                 'synthetic-demo.trycloudflare.com.evil.invalid','synthetic-demo.trycloudflare.com:80'])
def test_exact_hostname(public,host):
    assert public[0].get('/',headers={'Host':host}).status_code==400

def test_unknown_origin_closed(public):
    client,path,_=public
    path.unlink()
    assert client.get('/').status_code==503
    path.write_text('https://*.trycloudflare.com')
    assert client.get('/').status_code==503

def test_nonloopback_peer_rejected(public):
    _,_,app=public
    with TestClient(app,client=('198.51.100.10',1234),base_url='http://synthetic-demo.trycloudflare.com') as client:
        assert client.get('/').status_code==400

def test_duplicate_origin_rejected(public):
    assert public[0].get('/',headers=[('Origin','https://synthetic-demo.trycloudflare.com'),
                                     ('Origin','https://evil.invalid')]).status_code==400

# Real portal integration with synthetic scoped backend adapter from the existing account tests.
from test_personal_v120 import service, PASSWORD

def test_public_portal_cookies_csrf_private_routes_and_logout(service,tmp_path):
    accounts, factory, _ = service
    origin='https://synthetic-demo.trycloudflare.com'
    path=tmp_path/'origin'
    path.write_text(origin)
    app=factory().app
    app.user_middleware=[m for m in app.user_middleware if m.cls.__name__!='TrustedHostMiddleware']
    app.add_middleware(PublicOrigin,path=path)
    with TestClient(app,base_url=origin,client=('127.0.0.1',2000)) as client:
        assert client.get('/api/subjects').status_code==401
        assert client.get('/docs').status_code==404
        assert client.get('/openapi.json').status_code==404
        assert client.get('/api/status').status_code==401
        assert client.post('/api/login',json={'username':'alpha','password':PASSWORD},
                           headers={'Origin':'https://evil.invalid'}).status_code==403
        response=client.post('/api/login',json={'username':'alpha','password':PASSWORD},
                             headers={'Origin':origin,'X-Forwarded-Proto':'http'})
        assert response.status_code==200,response.text
        assert all(value in response.headers['set-cookie'] for value in ('Secure','HttpOnly','SameSite=strict'))
        assert client.get('/api/session').json()['secure_transport'] is True
        assert client.get('/api/subjects').json()==[{'id':'alpha','mission_id':'mission'}]
        assert client.get('/api/dashboard/bravo?mission_id=mission').status_code==404
        for route in ('/.env','/personal.sqlite3','/vigile.sqlite3','/portal-config.json','/api/tags','/admin','/api/register'):
            assert client.get(route).status_code==404,route
        assert client.post('/api/logout',json={},headers={'Origin':origin}).status_code==200
        assert client.get('/api/subjects').status_code==401

def test_public_login_rate_limit(service,tmp_path):
    _, factory, _ = service
    origin='https://synthetic-demo.trycloudflare.com'
    path=tmp_path/'origin'
    path.write_text(origin)
    app=factory().app
    app.user_middleware=[m for m in app.user_middleware if m.cls.__name__!='TrustedHostMiddleware']
    app.add_middleware(PublicOrigin,path=path)
    with TestClient(app,base_url=origin,client=('127.0.0.1',2000)) as client:
        for _ in range(10):
            assert client.post('/api/login',json={'username':'alpha','password':'incorrect'},
                               headers={'Origin':origin}).status_code==401
        assert client.post('/api/login',json={'username':'alpha','password':PASSWORD},
                           headers={'Origin':origin}).status_code==429
