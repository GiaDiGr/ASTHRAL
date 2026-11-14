"""Local API. No write access to rules, evidence, authorization or audit."""
import os, json, hmac, sqlite3
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .security import authenticate, authorized_request, rag_projection, audit_identity
from . import models as m
from .store import Store
from .registry import Registry
from .service import Engine
from .quality import Inconclusive

def create_app(root=None, db_path=None, tokens=None):
    root=Path(root or os.environ.get('VIGILE_CORPUS',Path(__file__).resolve().parents[2]))
    db_path=db_path or os.environ.get('VIGILE_DB',root/'engine/data/vigile.sqlite3')
    token_file=Path(os.environ.get('VIGILE_TOKEN_FILE',root/'engine/data/tokens.json'))
    explicit_tokens=dict(tokens) if tokens is not None else None
    def token_mapping():
        if explicit_tokens is not None: return explicit_tokens
        if 'VIGILE_TOKENS' in os.environ: return json.loads(os.environ['VIGILE_TOKENS'])
        return json.loads(token_file.read_text(encoding='utf-8')) if token_file.exists() else {}
    store=Store(db_path); engine=Engine(Registry(root),store)
    @asynccontextmanager
    async def lifespan(app):
        yield
        store.close()
    app=FastAPI(title='VIGILE Health Intelligence Engine',version='0.9.0',docs_url=None,redoc_url=None,
                openapi_url=None,lifespan=lifespan)
    app.state.engine=engine

    @app.middleware('http')
    async def auth(request: Request, call_next):
        if request.url.path=='/health':
            response=await call_next(request)
            response.headers['Cache-Control']='no-store'
            return response
        header=request.headers.get('authorization','')
        token=header[7:] if header.startswith('Bearer ') else ''
        try: principal=authenticate(token,token_mapping())
        except (ValueError,TypeError,OSError): principal=None
        if not principal:
            store.audit('AUTHENTICATION_DENIED','anonymous',{'method':request.method})
            return JSONResponse({'detail':'UNAUTHORIZED'},status_code=401,headers={'Cache-Control':'no-store'})
        request.state.actor=principal.role
        request.state.principal=principal
        identity_token=audit_identity.set(principal.id)
        try:
            data=dict(request.query_params)
            if request.method not in ('GET','HEAD'):
                # Bounded streaming consumption, not merely a trusted Content-Length.
                body=bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body)>1048576:
                        return JSONResponse({'detail':'PAYLOAD_TOO_LARGE'},status_code=413)
                request._body=bytes(body)
                if body:
                    try: data=json.loads(body)
                    except ValueError: return JSONResponse({'detail':'INVALID_JSON'},status_code=422)
                    if not isinstance(data,dict): return JSONResponse({'detail':'OBJECT_REQUIRED'},status_code=422)
            try: allowed=authorized_request(engine,principal,request.url.path,request.method,data)
            except (KeyError,ValueError,TypeError,AttributeError,sqlite3.ProgrammingError): allowed=False
            if not allowed:
                store.audit('ACCESS_DENIED',principal.role,{'method':request.method})
                return JSONResponse({'detail':'BLOCKED_NO_AUTHORIZATION'},status_code=403,headers={'Cache-Control':'no-store'})
            response=await call_next(request)
            response.headers['Cache-Control']='no-store'
            response.headers['X-Content-Type-Options']='nosniff'
            return response
        finally:
            audit_identity.reset(identity_token)

    def require(*roles):
        def check(request:Request):
            actor=request.state.actor
            if actor not in roles:
                store.audit('ROLE_DENIED',actor,{'method':request.method})
                raise HTTPException(403,'BLOCKED_NO_AUTHORIZATION')
            return actor
        return check
    write=Depends(require('operator','researcher','clinician'))
    research=Depends(require('researcher','clinician'))
    medical=Depends(require('clinician'))

    @app.exception_handler(RequestValidationError)
    async def invalid_payload(request,exc):
        return JSONResponse({'detail':[{'loc':list(e['loc']),'type':e['type']} for e in exc.errors()]},status_code=422)

    @app.get('/rag/findings/{identifier}')
    def rag_finding(identifier:str): return rag_projection(store.get('finding',identifier))

    @app.exception_handler(KeyError)
    async def missing(request,exc): return JSONResponse({'detail':'REFERENCE_NOT_FOUND'},status_code=404)
    @app.exception_handler(ValueError)
    async def invalid(request,exc): return JSONResponse({'detail':str(exc)},status_code=422)
    @app.exception_handler(sqlite3.IntegrityError)
    async def conflict(request,exc): return JSONResponse({'detail':'IMMUTABLE_RECORD_CONFLICT'},status_code=409)

    @app.get('/health')
    def health(): return {'status':'ok','mode':'RESEARCH_ONLY','clinical_execution':'BLOCKED','version':'0.9.0'}
    @app.get('/openapi.json')
    def openapi(): return app.openapi()
    @app.get('/catalog/{kind}')
    def catalog(kind:str): return engine.registry.list(kind)
    @app.get('/conditions/{identifier}')
    def condition(identifier:str): return engine.registry.get('conditions',identifier)
    @app.get('/evidence/{identifier}')
    def evidence(identifier:str): return engine.registry.get('sources',identifier)
    @app.get('/rules')
    def rules(): return engine.registry.rule_status()
    @app.get('/evidence-issues')
    def issues(): return engine.registry.issues
    @app.get('/audit/verify')
    def verify(actor=Depends(require('researcher','clinician'))): return {'valid':store.verify()}
    @app.post('/missions',status_code=201)
    def mission(body:m.MissionContext,actor=research): return engine.register('mission',body,actor)
    @app.post('/profiles',status_code=201)
    def profile(body:m.AstronautProfile,actor=write): return engine.register('profile',body,actor)
    @app.post('/devices',status_code=201)
    def device(body:m.Device,actor=research): return engine.register('device',body,actor)
    @app.post('/measurements',status_code=201)
    def measurement(body:m.Measurement,actor=write): return engine.ingest(body,actor)
    @app.get('/profiles')
    def profiles(request:Request,mission_id:str):
        return [p for p in store.all('profile') if p['mission_id']==mission_id and request.state.principal.allows(p['id'],mission_id)]
    @app.get('/profiles/{identifier}')
    def profile_record(identifier:str): return store.get('profile',identifier)
    @app.get('/baselines')
    def baselines(subject_id:str,mission_id:str):
        return [b for b in store.all('baseline') if (b['subject_id'],b['mission_id'])==(subject_id,mission_id)]
    @app.get('/baselines/{identifier}/status')
    def baseline_availability(identifier:str,as_of:m.AwareDatetime):
        b=store.get('baseline',identifier)
        try:
            engine.baseline_status(identifier,as_of)
            state='AVAILABLE_FOR_RESEARCH'
        except Inconclusive as exc: state=str(exc)
        return {'baseline':b,'as_of':as_of.isoformat(),'availability':state,'clinical_execution':'BLOCKED'}
    @app.get('/trends')
    def trends(subject_id:str,mission_id:str):
        return [b for b in store.all('trend') if (b['subject_id'],b['mission_id'])==(subject_id,mission_id)]
    @app.get('/rag/findings')
    def rag_findings(subject_id:str,mission_id:str,limit:int=100):
        if not 1<=limit<=1000: raise HTTPException(422,'Limit must be 1..1000')
        return [rag_projection(f) for f in store.all('finding') if (f['subject_id'],f['mission_id'])==(subject_id,mission_id)][-limit:]
    @app.get('/measurements')
    def query_measurements(subject_id:str, mission_id:str, variable:str|None=None, limit:int=100):
        if not 1<=limit<=1000: raise HTTPException(422,'Limit must be 1..1000')
        rows=[r for r in store.all('measurement') if r['measurement']['subject_id']==subject_id and r['measurement']['mission_id']==mission_id and (variable is None or r['measurement']['variable']==variable)]
        return sorted(rows,key=lambda r:(r['measurement']['timestamp'],r['measurement']['id']))[-limit:]
    @app.get('/findings')
    def query_findings(subject_id:str,mission_id:str):
        return [r for r in store.all('finding') if r['subject_id']==subject_id and r['mission_id']==mission_id]
    @app.get('/episodes')
    def query_episodes(subject_id:str,mission_id:str):
        return [engine.episode(r['id']) for r in store.all('episode') if r['subject_id']==subject_id and r['mission_id']==mission_id]
    @app.get('/research-records/{kind}/{identifier}')
    def research_record(kind:str,identifier:str):
        if kind not in ('baseline','trend','followup','followup_review','multisystem','clinical_note','quality_report','resource_assessment','baseline_withdrawal'):
            raise HTTPException(404,'Record type not exposed')
        return store.get(kind,identifier)
    @app.get('/measurements/{identifier}')
    def read_measurement(identifier:str): return store.get('measurement',identifier)
    @app.post('/baselines',status_code=201)
    def baseline(body:m.BaselineRequest,actor=research): return engine.build_baseline(body,actor)
    @app.post('/trends',status_code=201)
    def trend(body:m.TrendRequest,actor=research): return engine.trend(body,actor)
    @app.post('/evaluations')
    def evaluate(body:m.EvaluationRequest,actor=research): return engine.evaluate(body,actor)
    @app.get('/findings/{identifier}')
    def finding(identifier:str): return store.get('finding',identifier)
    @app.get('/findings/{identifier}/explanation')
    def explanation(identifier:str): return engine.reproduce(identifier)
    @app.post('/episodes',status_code=201)
    def episode(body:m.EpisodeRequest,actor=research): return engine.open_episode(body,actor)
    @app.get('/episodes/{identifier}')
    def read_episode(identifier:str): return engine.episode(identifier)
    @app.get('/episodes/{identifier}/pathway')
    def pathway(identifier:str): return engine.pathway(identifier)
    @app.post('/episodes/{identifier}/transitions')
    def transition(identifier:str,body:m.TransitionRequest,actor=research): return engine.transition(identifier,body,actor)
    @app.post('/clinical-notes')
    def note(body:m.ClinicalNote,actor=medical): return engine.note(body,actor)
    @app.post('/action-requests')
    def action(body:m.ActionRequest,actor=write): return engine.action(body,actor)
    @app.post('/followups')
    def followup(body:m.FollowUpPlan,actor=medical): return engine.followup(body,actor)
    @app.post('/followups/reviews')
    def review(body:m.FollowUpReview,actor=medical): return engine.review_followup(body,actor)
    @app.post('/multisystem')
    def multisystem(body:m.MultisystemRequest,actor=research): return engine.multisystem(body,actor)
    @app.post('/baselines/withdrawals',status_code=201)
    def withdraw(body:m.BaselineWithdrawal,actor=research): return engine.withdraw_baseline(body,actor)
    @app.post('/quality/assessments',status_code=201)
    def quality(body:m.QualityRequest,actor=research): return engine.quality_report(body,actor)
    @app.post('/evidence/revisions',status_code=201)
    def revision(body:m.EvidenceRevision,actor=research): return engine.register_evidence_revision(body,actor)
    @app.get('/evidence/rules/{identifier}')
    def rule_evidence(identifier:str): return engine.evidence_for_rule(identifier)
    @app.get('/capabilities/coverage')
    def coverage(): return engine.clinical_coverage()
    @app.post('/episodes/{identifier}/findings')
    def attach(identifier:str,body:m.EpisodeAttachment,actor=research): return engine.attach_findings(identifier,body,actor)
    @app.get('/followups/{identifier}/status')
    def followup_state(identifier:str,as_of:m.AwareDatetime): return engine.followup_status(identifier,as_of)
    @app.post('/resources/assessments',status_code=201)
    def resource(body:m.ResourceAssessment,actor=research): return engine.assess_resources(body,actor)
    @app.get('/audit/checkpoint')
    def checkpoint(actor=Depends(require('researcher','clinician'))): return store.checkpoint()
    from .clinical_api import install_clinical_routes
    install_clinical_routes(app,engine,research)
    from .monitoring import install_monitoring_routes
    install_monitoring_routes(app,engine,research)
    from .dashboard_api import install_dashboard_routes
    install_dashboard_routes(app,engine)
    from fastapi.openapi.utils import get_openapi
    def secured_openapi():
        if app.openapi_schema is None:
            schema=get_openapi(title=app.title,version=app.version,routes=app.routes)
            schema.setdefault('components',{}).setdefault('securitySchemes',{})['BearerAuth']={
                'type':'http','scheme':'bearer','description':'Server-owned identity, role and subject/mission scope. Reader cannot write.'}
            for path,operations in schema['paths'].items():
                for method,operation in operations.items():
                    if isinstance(operation,dict) and method in ('get','post','put','patch','delete','head'):
                        operation['security']=[] if path=='/health' else [{'BearerAuth':[]}]
            app.openapi_schema=schema
        return app.openapi_schema
    app.openapi=secured_openapi
    return app
