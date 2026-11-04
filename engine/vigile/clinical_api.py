"""Routes inherit the existing authentication middleware and role dependencies."""
from fastapi import HTTPException
from pydantic import AwareDatetime
from .models import Model,Id
class ClinicalContext(Model):
    evaluation_id:Id
    subject_id:Id
    mission_id:Id
    as_of:AwareDatetime
    input_hash:str

from .clinical_models import ClinicalRequest,ProtocolEligibilityRequest
from .clinical_engine import ClinicalService
from .clinical_contracts import ClinicalEvaluationResponse, DifferentialRow, PendingTest, ClinicalReplayResponse, EligibilityResponse

def install_clinical_routes(app,engine,research):
    service=ClinicalService(engine); app.state.clinical=service; knowledge=service.knowledge
    @app.post('/clinical/evaluations',status_code=201,response_model=ClinicalEvaluationResponse,response_model_exclude_unset=True)
    def evaluate(body:ClinicalRequest,actor=research): return service.evaluate(body,actor)
    @app.post('/clinical/presentations/evaluate',status_code=201,response_model=ClinicalEvaluationResponse,response_model_exclude_unset=True)
    def presentation(body:ClinicalRequest,actor=research):
        if not body.presentation_id or body.condition_id: raise ValueError('PRESENTATION_ONLY_REQUIRED')
        return service.evaluate(body,actor)
    @app.get('/clinical/evaluations/{identifier}',response_model=ClinicalEvaluationResponse,response_model_exclude_unset=True)
    def result(identifier:str): return service.projection(engine.store.get('clinical_evaluation',identifier))
    @app.get('/clinical/evaluations/{identifier}/context',response_model=ClinicalContext)
    def evidence_context(identifier:str):
        r=engine.store.get('clinical_evaluation',identifier)
        return {'evaluation_id':identifier,'subject_id':r['subject_id'],'mission_id':r['mission_id'],'as_of':r['snapshot']['request']['as_of'],'input_hash':r['input_hash']}
    @app.get('/clinical/evaluations/{identifier}/differential',response_model=list[DifferentialRow],response_model_exclude_unset=True)
    def differential(identifier:str): return engine.store.get('clinical_evaluation',identifier)['differential']
    @app.get('/clinical/evaluations/{identifier}/next-tests',response_model=list[PendingTest],response_model_exclude_unset=True)
    def tests(identifier:str): return engine.store.get('clinical_evaluation',identifier)['next_tests']
    @app.get('/clinical/evaluations/{identifier}/replay',response_model=ClinicalReplayResponse,response_model_exclude_unset=True)
    def replay(identifier:str): return service.replay(identifier)
    @app.post('/clinical/evaluations/{identifier}/reassess',status_code=201,response_model=ClinicalEvaluationResponse,response_model_exclude_unset=True)
    def reassess(identifier:str,body:ClinicalRequest,actor=research): return service.evaluate(body,actor,identifier)
    @app.get('/clinical/conditions/{condition}/criteria')
    def criterion_for_condition(condition:str): return knowledge.criteria[condition]
    @app.get('/clinical/conditions/{condition}')
    def condition_record(condition:str):
        if condition not in knowledge.criteria: return {'condition_id':condition,'status':'EXTERNAL_PATHWAY_NOT_IMPLEMENTED'}
        return {'criterion':knowledge.criteria[condition],'clinical_validation':'NOT_VALIDATED'}
    @app.get('/clinical/criteria/{identifier}')
    def criterion(identifier:str):
        for c in knowledge.criteria.values():
            if c['criterion_id']==identifier: return c
        raise KeyError(identifier)
    @app.get('/clinical/protocols/{identifier}')
    def protocol(identifier:str): return {'document':knowledge.protocols[identifier],'execution_enabled':False}
    @app.post('/clinical/protocols/{identifier}/eligibility',response_model=EligibilityResponse,response_model_exclude_unset=True)
    def eligibility(identifier:str,body:ProtocolEligibilityRequest,actor=research):
        knowledge.protocols[identifier]
        record=engine.store.get('clinical_evaluation',body.evaluation_id)
        matches=[r['protocol'] for r in record['results'].values() if r['protocol']['protocol_id']==identifier]
        if record.get('presentation_protocol',{} ) and record['presentation_protocol']['protocol_id']==identifier: matches.append(record['presentation_protocol'])
        if not matches: raise ValueError('PROTOCOL_NOT_IN_EVALUATED_ROUTE')
        engine.store.audit('CLINICAL_ELIGIBILITY_READ',actor,{'evaluation_id':body.evaluation_id,'protocol_id':identifier})
        return {'evaluation_id':body.evaluation_id,'eligibility':matches,'new_authorization':False}
    @app.get('/clinical/sources/{identifier}')
    def source(identifier:str): return {'source':knowledge.sources[identifier],'source_status':knowledge.source_status(identifier)}
    @app.get('/clinical/knowledge/version')
    def version(): return {'manifest':knowledge.manifest,'knowledge_hash':knowledge.hash,'runtime_network_required':False,'clinical_execution':'BLOCKED'}
