"""Synthetic mission resources and documentary management. No treatment authority.
Reuses Store/protocols/episodes; never computes a dose or changes diagnostic criteria.
"""
from datetime import datetime
import math
from typing import Literal
from pydantic import AwareDatetime,Field,StrictBool,StrictInt,StrictFloat,model_validator,JsonValue
from .models import Model,Id
from .store import digest

class MedicalResource(Model):
    id:Id
    kind:Literal['MEDICATION','CONSUMABLE','EQUIPMENT','CAPABILITY']
    label:str=Field(min_length=1,max_length=200)
    quantity:StrictInt|StrictFloat|None=Field(default=None,ge=0)
    unit:str|None=Field(default=None,min_length=1,max_length=64)
    availability:Literal['UNKNOWN','AVAILABLE','UNAVAILABLE']='UNKNOWN'
    verification:Literal['UNVERIFIED','VERIFIED']='UNVERIFIED'
    verified_at:AwareDatetime|None=None
    expires_at:AwareDatetime|None=None
    storage_status:Literal['UNKNOWN','COMPLIANT','NONCOMPLIANT']='UNKNOWN'
    storage_conditions:str=Field(default='UNSPECIFIED',max_length=300)
    integrity_status:Literal['UNKNOWN','INTACT','COMPROMISED']='UNKNOWN'
    requires_cold_chain:StrictBool|None=None
    cold_chain_status:Literal['UNKNOWN','COMPLIANT','NONCOMPLIANT']='UNKNOWN'
    updated_at:AwareDatetime
    source:str=Field(min_length=1,max_length=300)
    responsible:str=Field(min_length=1,max_length=200)
    synthetic:Literal[True]=True
    @model_validator(mode='after')
    def coherent(self):
        if self.quantity is not None and (not math.isfinite(self.quantity) or not self.unit):raise ValueError('FINITE_QUANTITY_WITH_UNIT_REQUIRED')
        if self.verified_at and self.verified_at>self.updated_at:raise ValueError('VERIFICATION_AFTER_RESOURCE_UPDATE')
        return self

class InventoryVersion(Model):
    id:Id
    mission_id:Id
    version:StrictInt=Field(ge=1)
    supersedes:Id|None=None
    effective_at:AwareDatetime
    updated_at:AwareDatetime
    source:str=Field(min_length=1,max_length=300)
    responsible:str=Field(min_length=1,max_length=200)
    resources:list[MedicalResource]=Field(max_length=64)
    synthetic:Literal[True]=True
    @model_validator(mode='after')
    def coherent(self):
        if self.updated_at!=self.effective_at:raise ValueError('INVENTORY_UPDATE_MUST_EQUAL_EFFECTIVE_TIME')
        if len({r.id for r in self.resources})!=len(self.resources):raise ValueError('DUPLICATE_RESOURCE_ID')
        if any(r.updated_at>self.effective_at for r in self.resources):raise ValueError('FUTURE_RESOURCE_IN_VERSION')
        return self

class ResourceSnapshot(Model):
    policy:Literal['DECLARED_R2','MISSION_INVENTORY']
    mission_id:Id
    as_of:AwareDatetime
    inventory_id:Id|None=None
    inventory_version:int|None=None
    inventory_hash:str|None=None
    resources:list[MedicalResource]=Field(default_factory=list)
    declared_flags:dict[str,StrictBool]=Field(default_factory=dict)
    synthetic_only:Literal[True]=True

class InterventionDocument(Model):
    id:Id
    protocol_id:str
    title:str
    kind:Literal['DOCUMENTED_THERAPY','DOCUMENTED_REVIEW','CAPABILITY_REVIEW']
    documentation_status:Literal['DOCUMENTED']='DOCUMENTED'
    applicability_status:Literal['DOCUMENTED','CONDITIONALLY_APPLICABLE','NOT_APPLICABLE']
    documented_indication:JsonValue
    intervention_indication_decided:Literal[False]=False
    protocol_indication_supported:bool
    conditions:list[str]
    safety_restrictions:list[str]
    documented_precautions:list[dict[str,JsonValue]]
    monitoring:list[str]
    required_resources:list[str]
    resource_status:Literal['RESOURCE_AVAILABLE','RESOURCE_UNVERIFIED','RESOURCE_UNAVAILABLE']
    resource_checks:list[dict[str,JsonValue]]
    authorization:Literal['AUTHORIZATION_REQUIRED']='AUTHORIZATION_REQUIRED'
    authority_verification:Literal['NO_VERIFIED_MISSION_POLICY']='NO_VERIFIED_MISSION_POLICY'
    evidence:list[dict[str,JsonValue]]
    protocol_version:str
    space_applicability:str
    limitations:list[str]
    reference_only:dict[str,JsonValue]=Field(default_factory=dict)
    execution_enabled:Literal[False]=False
    dose_calculation_enabled:Literal[False]=False

class ManagementView(Model):
    version:Literal['1.0.1']='1.0.1'
    resource_snapshot:ResourceSnapshot
    interventions:list[InterventionDocument]
    urgent_suspicion_without_met_criteria:bool
    diagnostic_status:str
    urgency:str
    protocol_status:str
    clinical_execution:Literal['BLOCKED']='BLOCKED'
    limitations:list[str]

class ManagementRecord(Model):
    id:Id
    episode_id:Id
    evaluation_id:Id
    intervention_id:Id
    status:Literal['DOCUMENTED','PROPOSED','REVIEW_PENDING','HUMAN_REPORTED_PERFORMED','POST_INTERVENTION_OBSERVATION']
    occurred_at:AwareDatetime
    recorded_at:AwareDatetime
    source:str=Field(min_length=1,max_length=300)
    reported_authority:str=Field(min_length=1,max_length=300)
    note:str=Field(min_length=1,max_length=2000)
    followup_plan_id:Id|None=None
    measurement_ids:list[Id]=Field(default_factory=list,max_length=64)
    data_needed_for_reevaluation:list[str]=Field(default_factory=list,max_length=32)
    synthetic:Literal[True]=True
    @model_validator(mode='after')
    def coherent(self):
        if self.occurred_at>self.recorded_at:raise ValueError('RECORD_BEFORE_REPORTED_EVENT')
        if len(set(self.measurement_ids))!=len(self.measurement_ids):raise ValueError('DUPLICATE_MEASUREMENT')
        if any(len(x)>120 for x in self.data_needed_for_reevaluation):raise ValueError('REEVALUATION_LABEL_TOO_LONG')
        return self


def append_inventory(engine,version,actor):
    with engine.store.transaction():
        if not engine.store.get('mission',version.mission_id)['synthetic']:raise ValueError('SYNTHETIC_MISSION_REQUIRED')
        prior=[v for v in engine.store.all('medical_inventory') if v['mission_id']==version.mission_id]
        last=prior[-1] if prior else None
        if version.version!=(last['version']+1 if last else 1) or version.supersedes!=(last['id'] if last else None):raise ValueError('INVENTORY_LINEAGE_CONFLICT')
        if last and version.effective_at<=datetime.fromisoformat(last['effective_at']):raise ValueError('INVENTORY_TIME_MUST_ADVANCE')
        committed=[datetime.fromisoformat(r['as_of']) for r in engine.store.all('monitoring_run') if r['mission_id']==version.mission_id]
        committed += [datetime.fromisoformat(r['snapshot']['request']['as_of']) for r in engine.store.all('clinical_evaluation') if r['mission_id']==version.mission_id]
        if any(t>=version.effective_at for t in committed):raise ValueError('COMMITTED_RESOURCE_CONTEXT_CANNOT_BE_REWRITTEN')
        return engine.store.put('medical_inventory',version.id,version.model_dump(mode='json'),actor)


def inventory_snapshot(store,mission_id,as_of,policy='MISSION_INVENTORY',declared=None):
    if policy=='DECLARED_R2':return ResourceSnapshot(policy=policy,mission_id=mission_id,as_of=as_of,declared_flags=declared or {}).model_dump(mode='json')
    versions=[v for v in store.all('medical_inventory') if v['mission_id']==mission_id and datetime.fromisoformat(v['effective_at'])<=as_of]
    v=max(versions,key=lambda x:datetime.fromisoformat(x['effective_at'])) if versions else None
    return ResourceSnapshot(policy=policy,mission_id=mission_id,as_of=as_of,inventory_id=v['id'] if v else None,inventory_version=v['version'] if v else None,inventory_hash=digest(v) if v else None,resources=v['resources'] if v else []).model_dump(mode='json')


def resource_check(snapshot,identifier):
    if snapshot['policy']=='DECLARED_R2':
        value=snapshot.get('declared_flags',{}).get(identifier)
        return {'id':identifier,'status':'RESOURCE_UNAVAILABLE' if value is False else 'RESOURCE_UNVERIFIED','reason':'LEGACY_DECLARED_FALSE' if value is False else 'LEGACY_DECLARATION_NOT_INVENTORY_VERIFICATION' if value is True else 'NOT_DECLARED','declared_available':value}
    r=next((x for x in snapshot['resources'] if x['id']==identifier),None)
    if not r:return {'id':identifier,'status':'RESOURCE_UNVERIFIED','reason':'ABSENT_FROM_MISSION_MANIFEST'}
    if identifier in ('insulin_inventory','epinephrine_inventory') and r['kind']!='MEDICATION':return {'id':identifier,'status':'RESOURCE_UNVERIFIED','reason':'MEDICATION_KIND_REQUIRED'}
    at=datetime.fromisoformat(snapshot['as_of'])
    unavailable=r['availability']=='UNAVAILABLE' or r['integrity_status']=='COMPROMISED' or r['storage_status']=='NONCOMPLIANT' or (r.get('quantity') is not None and r['quantity']<=0) or (r.get('expires_at') is not None and datetime.fromisoformat(r['expires_at'])<=at) or (r['requires_cold_chain'] is True and r['cold_chain_status']=='NONCOMPLIANT')
    physical=r['kind']!='CAPABILITY'
    unknown=r['availability']!='AVAILABLE' or r['verification']!='VERIFIED' or not r.get('verified_at') or datetime.fromisoformat(r['verified_at'])>at or (physical and (r['integrity_status']!='INTACT' or r['storage_status']!='COMPLIANT')) or (r['kind'] in ('MEDICATION','CONSUMABLE') and (r.get('quantity') is None or not r.get('expires_at'))) or (r['kind']=='MEDICATION' and r['requires_cold_chain'] is None) or (r['requires_cold_chain'] is True and r['cold_chain_status']!='COMPLIANT')
    return {'id':identifier,'status':'RESOURCE_UNAVAILABLE' if unavailable else 'RESOURCE_UNVERIFIED' if unknown else 'RESOURCE_AVAILABLE','reason':'UNUSABLE_OR_EXPIRED_OR_EMPTY' if unavailable else 'VERIFICATION_OR_STORAGE_OR_INTEGRITY_UNKNOWN' if unknown else 'VERIFIED_SYNTHETIC_MANIFEST_RESOURCE','resource':r}


def resolved_flags(snapshot,knowledge):
    names={n for p in knowledge.protocols.values() for n in p.get('required_resources',[])}|set(knowledge.tests)|{'epinephrine_inventory','verified_drug_concentration','IM_delivery_capability'}
    checked={name:resource_check(snapshot,name)['status'] for name in names}
    return {name:state=='RESOURCE_AVAILABLE' for name,state in checked.items() if state!='RESOURCE_UNVERIFIED'}


def evidence(knowledge,ids):
    notes={'SRC-DKA-2024':'THERAPEUTIC_FULL_TEXT_NOT_REVERIFIED_HUMAN_REVIEW_REQUIRED','SRC-KDIGO-AKI-2012':'PINNED_SECTION_2_SUPPORTS_DEFINITION_NOT_FULL_THERAPEUTIC_GUIDELINE','SRC-ADA-HYPO-2026':'ORAL_MANAGEMENT_ROUTING_NOT_APPROVED_IN_PINNED_PROTOCOL','SRC-WAO-ANAPH-2020':'LOCAL_FULL_TEXT_AVAILABLE_INDEPENDENT_CLINICAL_REVIEW_PENDING'}
    return [{'source_id':sid,'source':knowledge.sources[sid],'source_status':knowledge.source_status(sid),'review_status':notes.get(sid,'PINNED_PREVIOUS_REFERENCE_NOT_REVALIDATED'),'knowledge_hash':knowledge.hash} for sid in ids]


def management_view(snapshot,result,knowledge):
    request=snapshot['request'];resources=snapshot['resource_snapshot'];views={}
    for condition,r in result['results'].items():
        p=knowledge.protocols[r['protocol']['protocol_id']];pid=p['protocol_id'];entries=[]
        if p.get('therapy'):
            for i,therapy in enumerate(p['therapy']):entries.append((pid+'.therapy.'+str(i),therapy['action'],'DOCUMENTED_THERAPY',therapy))
        else:
            for i,step in enumerate(p.get('steps',[p.get('purpose','DOCUMENTED_PROTOCOL_REVIEW')])):entries.append((pid+'.review.'+str(i),step,'DOCUMENTED_REVIEW',{}))
        for i,step in enumerate(p.get('additional_actions',[])):entries.append((pid+'.additional.'+str(i),step,'DOCUMENTED_REVIEW',{}))
        if condition=='DKA':entries.append((pid+'.fluid-review','IV_FLUID_CAPABILITY_REVIEW_NOT_FLUID_ORDER','CAPABILITY_REVIEW',{}))
        docs=[]
        for iid,title,kind,reference in entries:
            insulin=condition=='DKA' and 'INSULIN' in title
            required=p.get('required_resources',[])
            if condition=='DKA' and not insulin:required=['IV_access_capability','IV_fluid_capability']
            if condition=='ANAPHYLAXIS':required=['epinephrine_inventory','verified_drug_concentration','IM_delivery_capability'] if title=='EPINEPHRINE_IM' else []
            checks=[resource_check(resources,k) for k in required]
            state='RESOURCE_UNAVAILABLE' if any(c['status']=='RESOURCE_UNAVAILABLE' for c in checks) else 'RESOURCE_UNVERIFIED' if not checks or any(c['status']=='RESOURCE_UNVERIFIED' for c in checks) else 'RESOURCE_AVAILABLE'
            restrictions=[x for x in r['protocol']['block_reasons'] if insulin and ('POTASSIUM' in x)]
            conditions=['INTERVENTION_INDICATION_NOT_INDEPENDENTLY_DECIDED','HUMAN_PROTOCOL_REVIEW_REQUIRED']
            if reference.get('if'):conditions.append('DOCUMENTED_NOT_EXECUTED: '+reference['if'])
            if condition=='HYPOGLYCEMIA':
                # Assess declared oral-route context only; no new treatment is selected.
                candidates=[o for o in snapshot['observations'] if o['concept']=='can_swallow_safely']
                candidates=[o for o in candidates if datetime.fromisoformat(request['window_start'])<=datetime.fromisoformat(o['timestamp'])<=datetime.fromisoformat(request['as_of'])]
                latest=max((datetime.fromisoformat(o['timestamp']) for o in candidates),default=None)
                current=[o for o in candidates if datetime.fromisoformat(o['timestamp'])==latest]
                valid=[o['value'] for o in current if o['quality']=='VALID' and type(o['value']) is bool and o['unit']=='1']
                swallow=valid[0] if current and len(valid)==len(current) and len(set(valid))==1 else None
                conditions.append('ORAL_ROUTE_NOT_SUPPORTED_BY_DECLARED_SWALLOWING' if swallow is False else 'SWALLOWING_DECLARED_TRUE_NOT_A_TREATMENT_AUTHORIZATION' if swallow is True else 'SWALLOWING_ABILITY_UNKNOWN')
                conditions.append('NO_ORAL_GLUCOSE_OR_GLUCAGON_REGIMEN_ADDED_PENDING_APPROVED_SOURCE')
            precautions=[x for x in knowledge.documents['contraindications']['rules'] if x.get('protocol_id')==pid and (condition!='DKA' or insulin) and (condition!='ANAPHYLAXIS' or title=='EPINEPHRINE_IM')]
            docs.append(InterventionDocument(id=iid,protocol_id=pid,title=title,kind=kind,applicability_status='NOT_APPLICABLE' if r['diagnostic_status']=='NOT_APPLICABLE' else 'CONDITIONALLY_APPLICABLE' if r['protocol']['indication_supported'] else 'DOCUMENTED',documented_indication=p.get('trigger',['DOCUMENTARY_REVIEW_ONLY']),protocol_indication_supported=r['protocol']['indication_supported'],conditions=conditions,safety_restrictions=restrictions,documented_precautions=precautions,monitoring=p.get('monitoring',[]),required_resources=required,resource_status=state,resource_checks=checks,evidence=evidence(knowledge,p['source_ids']),protocol_version=knowledge.documents['treatment_protocols']['schema_version'],space_applicability=r['space_applicability'],limitations=['REFERENCE_ONLY_NOT_ADMINISTRATION_INSTRUCTION','NO_EXECUTABLE_DOSE_OR_SEQUENCE','MONITORING_TEXT_IS_NOT_A_SCHEDULE','MISSION_PROTOCOL_AND_HUMAN_REVIEW_REQUIRED','RESOURCE_AVAILABLE_NOT_QUANTITY_ADEQUACY','PRECAUTION_CLASSIFICATION_INCOMPLETE_REQUIRES_REVIEW'],reference_only=reference or {k:p[k] for k in ('rules','initial_IV_epinephrine_bolus','pharmacologic_automation','purpose') if k in p}).model_dump(mode='json'))
        views[condition]=ManagementView(resource_snapshot=resources,interventions=docs,urgent_suspicion_without_met_criteria=r['urgency']=='EMERGENCY' and r['diagnostic_status']!='CRITERIA_MET',diagnostic_status=r['diagnostic_status'],urgency=r['urgency'],protocol_status=r['protocol_status'],limitations=['PROTOCOL_INDICATION_IS_NOT_INTERVENTION_INDICATION','G05_AUTHORIZATION_REMAINS_BLOCKED','RESOURCE_AVAILABILITY_IS_NOT_AUTHORIZATION','NO_EFFICACY_OR_CLINICAL_VALIDATION']).model_dump(mode='json')
    return views


def append_management_record(engine,record,actor):
    with engine.store.transaction():
        ep=engine.episode(record.episode_id);ev=engine.store.get('clinical_evaluation',record.evaluation_id)
        if (ep['subject_id'],ep['mission_id'])!=(ev['subject_id'],ev['mission_id']):raise ValueError('MANAGEMENT_RECORD_SCOPE_MISMATCH')
        if ep['condition_id'] not in ev['results']:raise ValueError('MANAGEMENT_RECORD_CONDITION_MISMATCH')
        if not engine.store.get('profile',ep['subject_id'])['synthetic']:raise ValueError('SYNTHETIC_PROFILE_REQUIRED')
        if record.occurred_at<datetime.fromisoformat(ev['snapshot']['request']['as_of']):raise ValueError('MANAGEMENT_BEFORE_SOURCE_EVALUATION')
        ids={i['id'] for i in ev.get('management',{}).get(ep['condition_id'],{}).get('interventions',[])}
        if record.intervention_id not in ids:raise ValueError('INTERVENTION_NOT_IN_FROZEN_EVALUATION')
        if record.followup_plan_id and engine.store.get('followup',record.followup_plan_id)['episode_id']!=ep['id']:raise ValueError('FOLLOWUP_SCOPE_MISMATCH')
        for mid in record.measurement_ids:
            m=engine.measurement(mid)
            if (m.subject_id,m.mission_id)!=(ep['subject_id'],ep['mission_id']) or m.timestamp>record.recorded_at:raise ValueError('MANAGEMENT_MEASUREMENT_SCOPE_OR_TIME')
        payload={**record.model_dump(mode='json'),'subject_id':ep['subject_id'],'mission_id':ep['mission_id'],'authority_verification':'NOT_VERIFIED','execution_by_vigile':False,'authorization_by_vigile':False,'efficacy_verified':False,'semantic':'UNVERIFIED_HUMAN_REPORT_NOT_EXECUTION_OR_AUTHORIZATION'}
        return engine.store.put('management_record',record.id,payload,actor)


def countermeasure_documents(registry):
    # Exact pre-existing pathway text, no additional therapy, threshold or SANS action.
    return [{'condition_id':cid,'classification':'DOCUMENTARY_MISSION_PROTOCOL_REQUIRED','text':registry.get('conditions',cid)['clinical_pathway_profile_as_published'],'source_ids':registry.get('conditions',cid)['source_ids'],'documentary_coverage':registry.get('conditions',cid)['coverage_states'],'execution_enabled':False,'limitations':['NOT_A_PERSONAL_PRESCRIPTION','NO_ADHERENCE_OR_HARDWARE_ASSUMPTION','NO_NEW_PHARMACOLOGIC_RECOMMENDATION']} for cid in ('C001','C002','C003','C005','C012','C013','C014','C032')]


def install_management_routes(app,engine,research,write):
    @app.post('/missions/{mission_id}/medical-inventory',response_model=InventoryVersion,status_code=201)
    def put_inventory(mission_id:Id,body:InventoryVersion,actor=research):
        if body.mission_id!=mission_id:raise ValueError('INVENTORY_MISSION_MISMATCH')
        return append_inventory(engine,body,actor)
    @app.get('/missions/{mission_id}/medical-inventory',response_model=ResourceSnapshot)
    def get_inventory(mission_id:Id,as_of:AwareDatetime):
        engine.store.get('mission',mission_id)
        return inventory_snapshot(engine.store,mission_id,as_of)
    @app.get('/clinical/evaluations/{identifier}/management')
    def get_management(identifier:Id):
        r=engine.store.get('clinical_evaluation',identifier)
        return {'evaluation_id':identifier,'management':r.get('management'),'legacy_record': 'management' not in r,'clinical_execution':'BLOCKED'}
    @app.post('/clinical/management-records',status_code=201)
    def put_management(body:ManagementRecord,actor=write):return append_management_record(engine,body,actor)
    @app.get('/clinical/evaluations/{identifier}/management-records')
    def management_records(identifier:Id,as_of:AwareDatetime):
        engine.store.get('clinical_evaluation',identifier)
        return [r for r in engine.store.all('management_record') if r['evaluation_id']==identifier and datetime.fromisoformat(r['recorded_at'])<=as_of and datetime.fromisoformat(r['occurred_at'])<=as_of]