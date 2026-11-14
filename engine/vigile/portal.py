"""Local reader BFF: bounded sessions, explicit runtime observation and scoped evidence."""
from pathlib import Path
import json,time,secrets,hmac,threading,math,sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import FileResponse,JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import Field,model_validator
from typing import Literal
import httpx
from .conversational import ConversationalInference
from .offline_library import OfflineLibrary
from .models import Model,Id
from .local_assistant import ReaderClient,OllamaInference,answer
from .local_protection import read_secret
from .portal_sessions import Sessions
from .hybrid_retrieval import HybridRetrieval,Topic
from .english import english_result
from .skinguard import SkinGuardService,SkinGuardRequest,SkinGuardInputError
from .computer_vision import ComputerVisionService,ComputerVisionError,OCTRequest,VideoRequest

class Login(Model):code:str=Field(pattern=r'^[A-Za-z0-9_-]{24,200}$')
class Question(Model):
 evaluation_id:Id|None=None
 monitoring_id:Id|None=None
 question:str=Field(min_length=3,max_length=1200)
 documentary:bool=False
 history_context_id:Id|None=None
 history:list[str]=Field(default_factory=list,max_length=3)
 language:Literal['en','es']='en'
 public_topic:Topic|None=None
 @model_validator(mode='after')
 def target(self):
  if (self.evaluation_id is None)==(self.monitoring_id is None):raise ValueError('EXACTLY_ONE_EVIDENCE_TARGET_REQUIRED')
  return self
class OperationMode(Model):mode:Literal['FULL','LOW_POWER','CRITICAL']

HEADERS={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Permissions-Policy':'camera=(self), microphone=(), geolocation=()', 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}

def create_portal(config,reader=None,inference=None,clock=time.monotonic,voice=None):
 config=dict(config);assets=Path(__file__).with_name('web')
 if config.get('voice_enabled') and not config.get('structured_explanations'):raise ValueError('VOICE_REQUIRES_STRUCTURED_EXPLANATIONS')
 reader=reader or ReaderClient(config['backend_url'],read_secret(config['reader_token_file']))
 inference=inference or (ConversationalInference(config.get('model_url','http://127.0.0.1:8891'),config.get('model'),config.get('mode','FULL'),config['inference_provider'],config.get('runtime_key_file')) if config.get('inference_provider') else OllamaInference(config.get('model_url','http://127.0.0.1:8891'),config.get('model')))
 inference.structured_explanations=bool(config.get('structured_explanations',False))
 skinguard=SkinGuardService()
 computer_vision=ComputerVisionService()
 hybrid=HybridRetrieval(config.get('online_retrieval'),lambda:getattr(inference,'mode','CRITICAL'),config.get('public_science_cache'));library=OfflineLibrary(config.get('library_manifest'));code=read_secret(config['access_code_file'])
 if len(code)<24:raise ValueError('ACCESS_CODE_TOO_SHORT')
 sessions=Sessions(config.get('session_idle_seconds',900),config.get('session_absolute_seconds',28800),clock);attempts=[];lock=threading.Lock();inference_lock=threading.Lock()
 @asynccontextmanager
 async def lifespan(app):
  yield
  reader.close()
  if getattr(app.state,'voice',None):app.state.voice.close()
  computer_vision.close()
 app=FastAPI(title='ASTHRAL Local Reader Portal',version='1.1.0',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
 app.state.sessions=sessions;app.state.inference=inference;app.state.hybrid=hybrid;app.state.skinguard=skinguard;app.state.computer_vision=computer_vision
 from .voice_api import install_voice
 attach_speech=install_voice(app,config,reader,inference,voice,clock)
 headers=dict(HEADERS)
 if config.get('voice_enabled'):
  headers['Permissions-Policy']='camera=(self), microphone=(self), geolocation=()'
 app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1'])
 def error(code,status):return JSONResponse({'detail':code},status,headers=headers)
 @app.middleware('http')
 async def secure(request,call_next):
  path=request.url.path;origin=request.headers.get('origin');base=str(request.base_url).rstrip('/')
  if request.method not in ('GET','POST'):return error('READ_ONLY_PORTAL',403)
  if request.method=='POST' and origin!=base:return error('ORIGIN_REQUIRED',403)
  if path.startswith('/api/') and origin and origin!=base:return error('ORIGIN_REJECTED',403)
  if path.startswith('/api/') and request.headers.get('sec-fetch-site')=='cross-site':return error('CROSS_SITE_REQUEST_REJECTED',403)
  vision_paths=path.startswith('/api/computer-vision/') and path.endswith('/analyze')
  if (path in ('/api/voice/transcribe','/api/skinguard/analyze') or vision_paths) and not sessions.get(request.cookies.get('vigile_session',''),False):return error('SESSION_EXPIRED_OR_REQUIRED',401)
  if request.method=='POST':
   body=bytearray()
   async for chunk in request.stream():
    body.extend(chunk)
    limit=15_728_640 if path=='/api/skinguard/analyze' or vision_paths else 1_820_000 if path=='/api/voice/transcribe' else 16384
    if len(body)>limit:return error('PAYLOAD_TOO_LARGE',413)
   request._body=bytes(body)
  if path.startswith('/api/') and path!='/api/login':
   token=request.cookies.get('vigile_session','');session=sessions.get(token,touch=path not in ('/api/status','/api/session','/api/runtime'))
   if not session:return error('SESSION_EXPIRED_OR_REQUIRED',401)
   if not sessions.admit(token,path in ('/api/assistant','/api/voice/transcribe','/api/voice/synthesize','/api/skinguard/analyze') or vision_paths):
    response=error('RETRY_LATER',429);response.headers['Retry-After']='60';return response
  response=await call_next(request);response.headers.update(headers);return response
 @app.exception_handler(RuntimeError)
 async def backend_failure(request,exc):
  if str(exc).startswith('HTTP_403 '):return error('ACCESS_DENIED',403)
  if str(exc).startswith('HTTP_404 '):return error('RESULT_NOT_FOUND',404)
  return error('BACKEND_UNAVAILABLE_OR_ACCESS_DENIED',502)
 @app.exception_handler(httpx.HTTPError)
 async def transport_failure(request,exc):return error('LOCAL_SERVICE_UNAVAILABLE',502)
 @app.exception_handler(sqlite3.Error)
 async def db_failure(request,exc):return error('STORAGE_UNAVAILABLE',503)
 @app.exception_handler(ValueError)
 async def invalid(request,exc):return error('INVALID_LOCAL_RESPONSE',422)
 @app.exception_handler(RequestValidationError)
 async def invalid_input(request,exc):return error('INVALID_REQUEST',422)
 def cookie(response,token,request):
  response.set_cookie('vigile_session',token,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=max(1,math.ceil((sessions.get(token,False) or {}).get('absolute_until',clock())-clock())),path='/')
  return response
 @app.post('/api/login')
 def login(body:Login,request:Request):
  with lock:
   now=clock();attempts[:]=[t for t in attempts if now-t<60]
   if len(attempts)>=10:raise HTTPException(429,'RETRY_LATER',headers={'Retry-After':'60'})
   attempts.append(now)
  if not hmac.compare_digest(body.code,code):raise HTTPException(401,'INVALID_ACCESS_CODE')
  if reader.get('/dashboard/identity')['role']!='reader':raise HTTPException(503,'READER_CREDENTIAL_REQUIRED')
  return cookie(JSONResponse({'authenticated':True,'idle_seconds':sessions.idle,'absolute_seconds':sessions.absolute}),sessions.create(),request)
 @app.post('/api/logout')
 def logout(request:Request):
  sessions.revoke(request.cookies.get('vigile_session',''));r=JSONResponse({'authenticated':False});r.delete_cookie('vigile_session',path='/');return r
 @app.get('/api/session')
 def session_info(request:Request):
  row=sessions.get(request.cookies.get('vigile_session',''),False)
  if not row:raise HTTPException(401,'SESSION_EXPIRED')
  return {'idle_seconds_remaining':max(0,math.ceil(row['idle_until']-clock())),'absolute_seconds_remaining':max(0,math.ceil(row['absolute_until']-clock())),'renewal':'EXPLICIT_ROTATING_COOKIE','secure_transport':request.url.scheme=='https'}
 @app.post('/api/session/renew')
 def renew(request:Request):
  if reader.get('/dashboard/identity')['role']!='reader':raise HTTPException(503,'READER_CREDENTIAL_REQUIRED')
  token=sessions.renew(request.cookies.get('vigile_session',''))
  if not token:raise HTTPException(401,'SESSION_EXPIRED')
  return cookie(JSONResponse({'renewed':True,'absolute_lifetime_extended':False}),token,request)
 def runtime_observation():
  if getattr(inference,'provider',None)!='ollama':return {'state':'NOT_SUPPORTED','loaded':None}
  try:
   with httpx.Client(trust_env=False,follow_redirects=False,timeout=1.5) as c:
    r=c.get(inference.url+'/api/ps');r.raise_for_status();model=next((m for m in r.json().get('models',[]) if m.get('name')==inference.model),None)
   return {'state':'OBSERVED','loaded':model is not None,'size_vram_bytes':model.get('size_vram') if model else 0,'context_tokens':model.get('context_length') if model else None,'observed_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'inference_requested':False}
  except (httpx.HTTPError,ValueError,TypeError,KeyError):return {'state':'UNAVAILABLE','loaded':None,'inference_requested':False}
 @app.get('/api/runtime')
 def runtime():return runtime_observation()
 @app.get('/api/status')
 def status():
  try:
   identity=reader.get('/dashboard/identity');backend='CONNECTED' if identity['role']=='reader' else 'ACCESS_DENIED'
  except (httpx.HTTPError,RuntimeError,ValueError):backend='UNAVAILABLE_OR_ACCESS_DENIED'
  return {'backend':backend,'portal':'CONNECTED','network':'LOOPBACK_PORTAL_OPTIONAL_PUBLIC_SCIENTIFIC_EGRESS','scientific_retrieval':hybrid.status(),'process_isolation':'SAME_USER_NOT_ISOLATED','assistant':inference.status(),'assistant_busy':inference_lock.locked(),'runtime':runtime_observation() if getattr(inference,'mode',None)!='CRITICAL' else {'state':'NOT_INSPECTED_IN_CRITICAL','loaded':None,'note':'NO_INFERENCE_DOES_NOT_MEAN_MEMORY_RELEASED'},'clinical_execution':'BLOCKED','version':'1.1.0'}
 @app.get('/api/skinguard/status')
 def skinguard_status():return skinguard.status()
 @app.post('/api/skinguard/analyze')
 def skinguard_analyze(body:SkinGuardRequest):
  try:return skinguard.analyze(body)
  except SkinGuardInputError as exc:raise HTTPException(exc.status_code,exc.code)
 @app.get('/api/computer-vision/status')
 def computer_vision_status():return computer_vision.get_model_status()
 @app.post('/api/computer-vision/ocular/analyze')
 def ocularvision_analyze(body:OCTRequest):
  try:return computer_vision.analyze_oct(body)
  except ComputerVisionError as exc:raise HTTPException(exc.status_code,exc.code)
 @app.post('/api/computer-vision/echo/analyze')
 def echovision_analyze(body:VideoRequest):
  try:return computer_vision.analyze_echo(body)
  except ComputerVisionError as exc:raise HTTPException(exc.status_code,exc.code)
 @app.post('/api/computer-vision/motion/analyze')
 def motionguard_analyze(body:VideoRequest):
  try:return computer_vision.analyze_motion(body)
  except ComputerVisionError as exc:raise HTTPException(exc.status_code,exc.code)
 @app.post('/api/mode')
 def mode(body:OperationMode):
  if not hasattr(inference,'set_mode'):raise HTTPException(409,'CONFIGURABLE_INFERENCE_REQUIRED')
  if not inference_lock.acquire(blocking=False):raise HTTPException(429,'ASSISTANT_BUSY')
  try:
   inference.set_mode(body.mode);hybrid.mode_changed();return {'mode':body.mode,'clinical_rules_changed':False,'runtime_memory_note':'No inference does not imply allocated memory was released; inspection and release are explicit operations.'}
  finally:inference_lock.release()
 @app.get('/api/subjects')
 def subjects():return reader.get('/dashboard/subjects')
 @app.get('/api/dashboard/{subject_id}')
 def dashboard(subject_id:Id,mission_id:Id,frame_id:Id|None=None):return reader.get('/dashboard/subjects/'+subject_id+'?mission_id='+mission_id+('&frame_id='+frame_id if frame_id else ''))
 @app.get('/api/frames/{subject_id}')
 def frames(subject_id:Id,mission_id:Id):return reader.get('/dashboard/frames/'+subject_id+'?mission_id='+mission_id)
 @app.get('/api/source/{source_id}')
 def source(source_id:Id):return reader.get('/clinical/sources/'+source_id)
 @app.get('/api/protocol/{protocol_id}')
 def protocol(protocol_id:Id):return reader.get('/clinical/protocols/'+protocol_id)
 @app.get('/api/replay/{kind}/{identifier}')
 def replay(kind:Literal['monitoring','clinical'],identifier:Id):
  return reader.get(('/monitoring/cycles/' if kind=='monitoring' else '/clinical/evaluations/')+identifier+'/replay')
 @app.get('/api/document/{fragment_id}')
 def document(fragment_id:Id):
  from .portal_documents import exact_fragment
  return exact_fragment(library,fragment_id)
 @app.post('/api/assistant')
 def chat(body:Question,request:Request):
  if not inference_lock.acquire(blocking=False):raise HTTPException(429,'ASSISTANT_BUSY')
  try:
   body=body.model_copy(update={'language':'en'});response_start=time.perf_counter()
   before_calls=getattr(inference,'model_http_calls',None)
   if any(len(q)>1200 for q in body.history):raise HTTPException(422,'HISTORY_TOO_LARGE')
   history=body.history if body.history_context_id==(body.monitoring_id or body.evaluation_id) else []
   if body.monitoring_id:
    from .longitudinal_assistant import answer_monitoring
    result=answer_monitoring(reader,inference,body.monitoring_id,body.question,history,library,body.language)
   else:result=answer(reader,inference,body.evaluation_id,body.question,history,library)
   if body.documentary:
    from .documentary import explain_documents
    result['documentary_explanation']=explain_documents(inference,library,body.question,result.get('answer',[]))
   result['history_used']=bool(history)
   after_calls=getattr(inference,'model_http_calls',None)
   result['inference_trace']={'model_requests_attempted':after_calls-before_calls if isinstance(before_calls,int) and isinstance(after_calls,int) else None,'explanation_accepted':bool(result.get('generated')),'request_attempt_is_not_completed_inference':True,'legacy_inference_executed_is_not_a_runtime_counter':True}
   result=english_result(result);result=attach_speech(result,body,request)
   result.setdefault('timings',{})['server_response_seconds']=time.perf_counter()-response_start
  finally:inference_lock.release()
  result['supplementary_science']=hybrid.retrieve(body.public_topic)
  return result
 @app.get('/')
 def index():return FileResponse(assets/'index.html')
 @app.get('/assets/{name}')
 def asset(name:str):
  if name not in ('app.js','style.css','voice-controller.js','recorder-worklet.js','management.js','translations.js','skinguard.js','computer-vision.js','astronaut-earth-login.png'):raise HTTPException(404)
  return FileResponse(assets/name)
 return app

def main():
 import argparse,uvicorn
 p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=Path);p.add_argument('--port',type=int,default=8766);args=p.parse_args()
 uvicorn.run(create_portal(json.loads(args.config.read_text(encoding='utf8'))),host='127.0.0.1',port=args.port,access_log=False)
if __name__=='__main__':main()
