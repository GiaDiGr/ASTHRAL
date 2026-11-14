"""Loopback frontend/BFF. Reader credential stays server-side; no generic proxy or writes."""
from pathlib import Path
import json,time,secrets,hmac,threading
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import FileResponse,JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import Field,model_validator
from typing import Literal
from .conversational import ConversationalInference
from .offline_library import OfflineLibrary
from .models import Model,Id
from .local_assistant import ReaderClient,OllamaInference,answer

class Login(Model): code:str=Field(min_length=24,max_length=200)
class Question(Model):
    evaluation_id:Id|None=None
    monitoring_id:Id|None=None
    question:str=Field(min_length=3,max_length=1200)
    documentary:bool=False
    history_context_id:Id|None=None
    history:list[str]=Field(default_factory=list,max_length=3)
    @model_validator(mode='after')
    def target(self):
        if (self.evaluation_id is None)==(self.monitoring_id is None):raise ValueError('EXACTLY_ONE_EVIDENCE_TARGET_REQUIRED')
        return self
class OperationMode(Model): mode:Literal['FULL','LOW_POWER','CRITICAL']

def create_portal(config,reader=None,inference=None):
    config=dict(config);assets=Path(__file__).with_name('web')
    reader=reader or ReaderClient(config['backend_url'],Path(config['reader_token_file']).read_text(encoding='utf-8').strip())
    inference=inference or (ConversationalInference(config.get('model_url','http://127.0.0.1:8890'),config.get('model'),config.get('mode','FULL'),config['inference_provider'],config.get('runtime_key_file')) if config.get('inference_provider') else OllamaInference(config.get('model_url','http://127.0.0.1:11434'),config.get('model')))
    library=OfflineLibrary(config.get('library_manifest'))
    code=Path(config['access_code_file']).read_text(encoding='utf-8').strip()
    if len(code)<24:raise ValueError('ACCESS_CODE_TOO_SHORT')
    sessions={};attempts=[];lock=threading.Lock();inference_lock=threading.Lock()
    @asynccontextmanager
    async def lifespan(app):
        yield
        reader.close()
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1'])
    @app.middleware('http')
    async def secure(request,call_next):
        path=request.url.path
        if request.method not in ('GET','POST'):return JSONResponse({'detail':'READ_ONLY_PORTAL'},403)
        if request.method=='POST':
            if request.headers.get('origin')!=str(request.base_url).rstrip('/'):return JSONResponse({'detail':'ORIGIN_REQUIRED'},403)
            body=bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body)>16384:return JSONResponse({'detail':'PAYLOAD_TOO_LARGE'},413)
            request._body=bytes(body)
        if path.startswith('/api/') and path!='/api/login':
            session=request.cookies.get('vigile_session','')
            with lock:valid=sessions.get(session,0)>time.monotonic()
            if not valid:return JSONResponse({'detail':'SESSION_REQUIRED'},401)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
          'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response
    @app.exception_handler(RuntimeError)
    async def backend_failure(request,exc):return JSONResponse({'detail':'BACKEND_UNAVAILABLE_OR_ACCESS_DENIED'},502)
    import httpx
    @app.exception_handler(httpx.HTTPError)
    async def transport_failure(request,exc):return JSONResponse({'detail':'LOCAL_SERVICE_UNAVAILABLE'},502)
    @app.exception_handler(ValueError)
    async def invalid(request,exc):return JSONResponse({'detail':'INVALID_LOCAL_RESPONSE'},422)
    from fastapi.exceptions import RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def invalid_input(request,exc):return JSONResponse({'detail':'INVALID_REQUEST'},422)
    @app.post('/api/login')
    def login(body:Login):
        with lock:
            now=time.monotonic();attempts[:]=[t for t in attempts if now-t<60]
            if len(attempts)>=10:raise HTTPException(429,'RETRY_LATER')
            attempts.append(now)
        if not hmac.compare_digest(body.code,code):raise HTTPException(401,'INVALID_ACCESS_CODE')
        if reader.get('/dashboard/identity')['role']!='reader':raise HTTPException(503,'READER_CREDENTIAL_REQUIRED')
        token=secrets.token_urlsafe(32)
        with lock:
            for key in list(sessions):
                if sessions[key]<=time.monotonic():sessions.pop(key)
            if len(sessions)>=128:raise HTTPException(429,'SESSION_LIMIT')
            sessions[token]=time.monotonic()+8*3600
        response=JSONResponse({'authenticated':True})
        response.set_cookie('vigile_session',token,httponly=True,samesite='strict',max_age=8*3600,path='/')
        return response
    @app.post('/api/logout')
    def logout(request:Request):
        with lock:sessions.pop(request.cookies.get('vigile_session',''),None)
        r=JSONResponse({'authenticated':False});r.delete_cookie('vigile_session');return r
    @app.get('/api/status')
    def status():
        identity=reader.get('/dashboard/identity')
        if identity['role']!='reader':raise HTTPException(503,'READER_CREDENTIAL_REQUIRED')
        return {'backend':'CONNECTED','network':'LOOPBACK_ONLY','assistant':inference.status(),'clinical_execution':'BLOCKED','version':'0.9.0'}
    @app.post('/api/mode')
    def operation_mode(body:OperationMode):
        if not hasattr(inference,'set_mode'):raise HTTPException(409,'CONFIGURABLE_INFERENCE_REQUIRED')
        if not inference_lock.acquire(blocking=False):raise HTTPException(429,'ASSISTANT_BUSY')
        try:
            inference.set_mode(body.mode)
            return {'mode':body.mode,'clinical_rules_changed':False,'runtime_memory_note':'CRITICAL skips inference; stop runtime separately to release allocated VRAM.'}
        finally:inference_lock.release()
    @app.get('/api/subjects')
    def subjects():return reader.get('/dashboard/subjects')
    @app.get('/api/dashboard/{subject_id}')
    def dashboard(subject_id:Id,mission_id:Id):return reader.get('/dashboard/subjects/'+subject_id+'?mission_id='+mission_id)
    @app.get('/api/source/{source_id}')
    def source(source_id:Id):return reader.get('/clinical/sources/'+source_id)
    @app.get('/api/protocol/{protocol_id}')
    def protocol(protocol_id:Id):return reader.get('/clinical/protocols/'+protocol_id)
    @app.post('/api/assistant')
    def chat(body:Question):
        if not inference_lock.acquire(blocking=False):raise HTTPException(429,'ASSISTANT_BUSY')
        try:
            if any(len(q)>1200 for q in body.history):raise HTTPException(422,'HISTORY_TOO_LARGE')
            scoped_history=body.history if body.history_context_id==(body.monitoring_id or body.evaluation_id) else []
            if body.monitoring_id:
                from .longitudinal_assistant import answer_monitoring
                result=answer_monitoring(reader,inference,body.monitoring_id,body.question,scoped_history,library)
            else:result=answer(reader,inference,body.evaluation_id,body.question,scoped_history,library)
            if body.documentary:
                from .documentary import explain_documents
                result['documentary_explanation']=explain_documents(inference,library,body.question,result.get('answer',[]))
            result['history_used']=bool(scoped_history)
            return result
        finally:inference_lock.release()
    @app.get('/')
    def index():return FileResponse(assets/'index.html')
    @app.get('/assets/{name}')
    def asset(name:str):
        if name not in ('app.js','style.css'):raise HTTPException(404)
        return FileResponse(assets/name)
    return app

def main():
    import argparse,uvicorn
    p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=Path);p.add_argument('--port',type=int,default=8766);args=p.parse_args()
    uvicorn.run(create_portal(json.loads(args.config.read_text(encoding='utf-8'))),host='127.0.0.1',port=args.port,access_log=False)
if __name__=='__main__':main()
