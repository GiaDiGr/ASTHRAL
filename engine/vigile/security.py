"""Server-owned identities, explicit scope, expiration and minimized RAG output."""
import hashlib, hmac
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Literal
from pydantic import AwareDatetime, Field
from .models import Model, Id

audit_identity=ContextVar('vigile_audit_identity',default=None)

class Principal(Model):
    id: Id
    role: Literal['reader','operator','researcher','clinician']
    subject_ids: list[str] = Field(default_factory=list)
    mission_ids: list[str] = Field(default_factory=list)
    expires_at: AwareDatetime | None = None
    disabled: bool = False

    def allows(self, subject_id=None, mission_id=None):
        return (subject_id is None or '*' in self.subject_ids or subject_id in self.subject_ids) and (mission_id is None or '*' in self.mission_ids or mission_id in self.mission_ids)

def authenticate(token, mapping):
    if not isinstance(mapping,dict) or not token or not 24<=len(token)<=4096: return None
    hashed=hashlib.sha256(token.encode('utf-8')).hexdigest()
    for key, descriptor in mapping.items():
        expected=key[7:] if key.startswith('sha256:') else hashlib.sha256(key.encode('utf-8')).hexdigest()
        if not hmac.compare_digest(hashed,expected): continue
        if isinstance(descriptor,str):
            descriptor={'id':'legacy-'+expected[:16],'role':descriptor,
                'subject_ids':[] if descriptor=='reader' else ['*'],
                'mission_ids':[] if descriptor=='reader' else ['*']}
        principal=Principal.model_validate(descriptor)
        if principal.disabled or (principal.expires_at and principal.expires_at<=datetime.now(timezone.utc)): return None
        return principal
    return None

def record_scopes(engine, kind, identifier):
    store=engine.store
    if kind=='episode': record=engine.episode(identifier)
    else: record=store.get(kind,identifier)
    if kind=='measurement': record=record['measurement']
    if 'subject_id' in record and 'mission_id' in record:
        return [(record['subject_id'],record['mission_id'])]
    if kind=='mission': return [(None,record['id'])]
    if kind=='profile': return [(record['id'],record['mission_id'])]
    if 'episode_id' in record: return record_scopes(engine,'episode',record['episode_id'])
    if 'plan_id' in record: return record_scopes(engine,'followup',record['plan_id'])
    if 'baseline_id' in record: return record_scopes(engine,'baseline',record['baseline_id'])
    if 'measurement_ids' in record.get('request',{}):
        return [scope for mid in record['request']['measurement_ids'] for scope in record_scopes(engine,'measurement',mid)]
    if 'input_ids' in record:
        return [scope for mid in record['input_ids'] for scope in record_scopes(engine,'measurement',mid)]
    if 'request' in record and 'finding_ids' in record['request']:
        return [scope for fid in record['request']['finding_ids'] for scope in record_scopes(engine,'finding',fid)]
    raise ValueError('RECORD_SCOPE_UNAVAILABLE')

def authorized_request(engine, principal, path, method, data):
    """Scopes are a server property. Client role/authorization fields never confer access."""
    segments=path.strip('/').split('/')
    if len(segments)==3 and segments[0]=='missions' and segments[2]=='medical-inventory':
        return principal.allows(None,segments[1]) and (method in ('GET','HEAD') or method=='POST' and principal.role in ('researcher','clinician') and data.get('mission_id')==segments[1])
    if segments==['clinical','management-records'] and method=='POST':
        if principal.role not in ('operator','researcher','clinician'):return False
        scopes=record_scopes(engine,'episode',data['episode_id'])+record_scopes(engine,'clinical_evaluation',data['evaluation_id'])
        for mid in data.get('measurement_ids',[]):scopes.extend(record_scopes(engine,'measurement',mid))
        if data.get('followup_plan_id'):scopes.extend(record_scopes(engine,'followup',data['followup_plan_id']))
        return all(principal.allows(s,m) for s,m in scopes)
    if len(segments)==3 and segments[0]=='missions' and segments[2]=='contexts':
        return method=='POST' and principal.role in ('researcher','clinician') and principal.allows(None,segments[1]) and data.get('mission_id')==segments[1]
    if segments[0]=='dashboard':
        if method not in ('GET','HEAD'): return False
        if path in ('/dashboard/subjects','/dashboard/identity'): return True
        if len(segments)==3 and segments[1] in ('subjects','frames') and data.get('mission_id'):
            if data.get('frame_id'):
                frame=engine.store.get('mission_frame',data['frame_id'])
                if frame['scope']!={'subject_id':segments[2],'mission_id':data['mission_id']}:return False
            return principal.allows(segments[2],data['mission_id'])
        return False
    if segments[0]=='monitoring':
        read=method in ('GET','HEAD')
        if principal.role=='reader' and not read:return False
        if read and path=='/monitoring/domains':return True
        scopes=[]
        if len(segments)>2 and segments[1]=='cycles':scopes.extend(record_scopes(engine,'monitoring_run',segments[2]))
        if data.get('subject_id') and data.get('mission_id'):scopes.append((data['subject_id'],data['mission_id']))
        if not read:
            if not isinstance(data.get('baseline_ids',[]),list):return False
            for identifier in data.get('baseline_ids',[]):scopes.extend(record_scopes(engine,'baseline',identifier))
            if data.get('previous_run_id'):scopes.extend(record_scopes(engine,'monitoring_run',data['previous_run_id']))
        return bool(scopes) and all(principal.allows(s,m) for s,m in scopes)
    # CLINICAL_SCOPED_ACCESS: deny reader mutation before wildcard logic.
    if segments[0]=='clinical':
        read=method in ('GET','HEAD')
        if principal.role=='reader' and not read: return False
        if read and len(segments)>1 and segments[1] in ('conditions','criteria','protocols','sources','knowledge'):
            return True
        scopes=[]
        if len(segments)>2 and segments[1]=='evaluations':
            scopes.extend(record_scopes(engine,'clinical_evaluation',segments[2]))
        if data.get('evaluation_id'):
            scopes.extend(record_scopes(engine,'clinical_evaluation',data['evaluation_id']))
        if not read and data.get('subject_id') and data.get('mission_id'):
            scopes.append((data['subject_id'],data['mission_id']))
        bindings=data.get('measurement_bindings',[])
        if not isinstance(bindings,list): return False
        for binding in bindings:
            if not isinstance(binding,dict): return False
            scopes.extend(record_scopes(engine,'measurement',binding['measurement_id']))
        return bool(scopes) and all(principal.allows(s,m) for s,m in scopes)
    knowledge=segments[0] in {'catalog','conditions','evidence','rules','evidence-issues','capabilities','openapi.json','integration'}
    if principal.role=='reader':
        if method not in ('GET','HEAD'): return False
        if knowledge: return True
        if segments[:2]!=['rag','findings'] or len(segments) not in (2,3): return False
    if knowledge and method in ('GET','HEAD'): return True
    if principal.subject_ids==['*'] and principal.mission_ids==['*'] and principal.role!='reader': return True
    scopes=[]
    if path.startswith('/rag/findings/'):
        scopes=record_scopes(engine,'finding',segments[-1])
    elif segments[0]=='profiles' and len(segments)==2:
        scopes=record_scopes(engine,'profile',segments[1])
    elif path=='/profiles' and method=='GET' and data.get('mission_id'):
        scopes=[(None,data['mission_id'])]
    elif segments[0] in ('measurements','findings','episodes','baselines') and len(segments)>=2:
        scopes=record_scopes(engine,{'measurements':'measurement','findings':'finding','episodes':'episode','baselines':'baseline'}[segments[0]],segments[1])
    elif segments[0]=='followups' and len(segments)==3 and segments[2]=='status':
        scopes=record_scopes(engine,'followup',segments[1])
    elif segments[0]=='research-records' and len(segments)==3:
        scopes=record_scopes(engine,segments[1],segments[2])
    elif path=='/profiles' and method=='POST': scopes=[(data.get('id'),data.get('mission_id'))]
    elif path=='/missions' and method=='POST': scopes=[(None,data.get('id'))]
    elif data.get('subject_id') and data.get('mission_id'): scopes=[(data['subject_id'],data['mission_id'])]
    elif data.get('episode_id'): scopes=record_scopes(engine,'episode',data['episode_id'])
    elif data.get('plan_id'): scopes=record_scopes(engine,'followup',data['plan_id'])
    elif data.get('baseline_id'): scopes=record_scopes(engine,'baseline',data['baseline_id'])
    elif data.get('measurement_ids'):
        scopes=[scope for mid in data['measurement_ids'] for scope in record_scopes(engine,'measurement',mid)]
    elif data.get('finding_ids'):
        scopes=[scope for fid in data['finding_ids'] for scope in record_scopes(engine,'finding',fid)]
    else: return False
    if not isinstance(data.get('bindings',{}),dict): return False
    for field in ('finding_ids','measurement_ids','co2_measurement_ids'):
        if not isinstance(data.get(field,[]),list): return False
    # Every referenced object must be authorized, including attachments to an existing episode.
    for fid in data.get('finding_ids',[]): scopes.extend(record_scopes(engine,'finding',fid))
    for mid in data.get('measurement_ids',[])+data.get('co2_measurement_ids',[]):
        scopes.extend(record_scopes(engine,'measurement',mid))
    for binding in data.get('bindings',{}).values():
        for identifier in (binding.values() if isinstance(binding,dict) else [binding]):
            try: scopes.extend(record_scopes(engine,'measurement',identifier))
            except KeyError: scopes.extend(record_scopes(engine,'baseline',identifier))
    for field in ('baseline_id','supersedes'):
        if data.get(field) and not knowledge: scopes.extend(record_scopes(engine,'baseline',data[field]))
    return bool(scopes) and all(principal.allows(s,m) for s,m in scopes)

def rag_projection(finding):
    allowed=('id','kind','result','reason','status','authorization','condition_ids','rule_id','timestamp','diagnosis')
    out={k:finding[k] for k in allowed if k in finding}
    bundle=finding.get('bundle',{})
    out['source_locators']=bundle.get('rule',{}).get('source_locators',[])
    out['rule_version']=bundle.get('rule',{}).get('rule_version')
    out['limitations']=['RESEARCH_ONLY','NO_DIAGNOSIS','NO_TREATMENT_AUTHORIZATION']
    # Deliberately no raw measurements, note text, subject, device, profile or replay bundle.
    return out
