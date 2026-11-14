"""Thin browser adapter around byte-identical reference clinical modules."""
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import base64
import json
from uuid import uuid4
from vigile.store import Store, digest
from vigile.clinical_engine import ClinicalService
from vigile.clinical_models import ClinicalRequest
from vigile.models import MissionContext, AstronautProfile
from vigile.clinical_simulator import observation
from vigile.algorithms import trends
from vigile.clinical_knowledge import ClinicalKnowledge

store = Store(':memory:')
service = ClinicalService(SimpleNamespace(store=store))
owner = None
biomedical = None

def differences(expected, actual, path='root'):
    if isinstance(expected, dict) and isinstance(actual, dict):
        return [item for key in sorted(expected.keys() | actual.keys()) for item in differences(expected.get(key),actual.get(key),path+'.'+key)]
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected)!=len(actual):return [{'path':path,'expected_length':len(expected),'actual_length':len(actual)}]
        return [item for i,(left,right) in enumerate(zip(expected,actual)) for item in differences(left,right,path+f'[{i}]')]
    if expected != actual or type(expected) != type(actual):
        return [{'path':path,'expected':expected,'actual':actual,'types':[type(expected).__name__,type(actual).__name__]}]
    return []

def monitoring_facts(run):
    from vigile.structured_facts import facts_for
    blocks=[]
    for domain in run['domains']:
        for indicator in domain['indicators']:
            if indicator['value'] is not None:
                blocks.append({'id':'M'+str(len(blocks)+1),'kind':'ENGINE','text':json.dumps(indicator),'reference':{'variable':indicator['variable'],'run_id':run['id']}})
    return facts_for(run,blocks,'en')

def dispatch(action, data):
    global store, service, owner, biomedical
    if action == 'init_profile':
        biomedical=None
        owner=None
        store.close()
        store=Store(':memory:')
        service=ClinicalService(SimpleNamespace(store=store))
        requested_owner = data['id']
        if data.get('database'):
            store.db.deserialize(base64.b64decode(data['database'], validate=True))
            if store.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or not store.verify():
                raise ValueError('LOCAL_DATABASE_INTEGRITY_FAILED')
            if store.db.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise ValueError('LOCAL_DATABASE_VERSION_UNSUPPORTED')
            for kind in ('browser_evaluation','voice_observation','research_stats','finding','monitoring_run','monitoring_event','episode','baseline','trend','clinical_evaluation','management_record'):
                if any(row.get('subject_id')!=requested_owner for row in store.all(kind)):
                    raise ValueError('PRIVATE_RECORD_SCOPE_MISMATCH')
            for row in store.all('measurement'):
                if row['measurement']['subject_id']!=requested_owner:raise ValueError('MEASUREMENT_SCOPE_MISMATCH')
            profiles = store.all('profile')
            if len(profiles) != 1 or profiles[0]['id'] != requested_owner:
                raise ValueError('PROFILE_BINDING_MISMATCH')
        else:
            mission=MissionContext(id='browser-mission',phase='IN_MISSION',gravity='EARTH',
                                   environment='HABITABLE_CABIN',mode='NOMINAL',synthetic=True)
            store.put('mission',mission.id,mission.model_dump(mode='json'))
            profile=AstronautProfile(id=requested_owner,mission_id=mission.id,synthetic=True)
            store.put('profile',requested_owner,profile.model_dump(mode='json'))
        owner=requested_owner
        return {'database_version':1,'audit_valid':store.verify(),'sqlite_version':__import__('sqlite3').sqlite_version}
    if action == 'parity':
        cases=data['cases']; failures=[]
        for case in cases:
            snapshot=json.loads(case['snapshot_json'])
            expected=json.loads(case['expected_json'])
            result=service.compute(snapshot)
            if digest(result) != digest(expected):
                failures.append({'id':case['id'],'expected_hash':digest(expected),'actual_hash':digest(result),'differences':differences(expected,result)[:12]})
        return {'total':len(cases),'matched':len(cases)-len(failures),'failures':failures,
                'runtime':'PYODIDE_REAL_COMPUTATION','knowledge_hash':service.knowledge.hash}
    if action == 'clinical_schema':
        from vigile.clinical_engine import UNITS,BOOLS,TEST_FIELDS,evaluate_condition
        import ast,inspect,hashlib
        from pathlib import Path
        definitions=[node for node in ast.walk(ast.parse(inspect.getsource(evaluate_condition))) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='derivations' for target in node.targets)]
        if len(definitions)!=1:raise ValueError('REFERENCE_INPUT_METADATA_LAYOUT_CHANGED')
        derivation_inputs=ast.literal_eval(definitions[0].value)
        source=Path(inspect.getsourcefile(evaluate_condition)).read_bytes()
        return {'criteria':service.knowledge.criteria,'presentations':service.knowledge.presentations,'units':UNITS,'booleans':sorted(BOOLS),'sources':service.knowledge.sources,'derivation_inputs':derivation_inputs,'input_metadata_source':{'module':'vigile.clinical_engine','sha256':hashlib.sha256(source).hexdigest(),'method':'REFERENCE_AST_LITERAL_METADATA_NOT_CLINICAL_COMPUTATION'}}
    if action == 'verify_corpus':
        from vigile.knowledge_v08 import verified_blocks
        from pathlib import Path
        blocks,issues,_=verified_blocks(data['corpus'],Path('/app'))
        from vigile.english import english_text
        blocks=[{**b,'display_text':english_text(b['text']),'english_generation_eligible':english_text(b['text'])==b['text']} for b in blocks]
        return {'blocks':blocks,'issues':issues}
    if action == 'search':
        from vigile.knowledge_v08 import search
        from pathlib import Path
        blocks,issues=search(data['corpus'],data['question'],data.get('limit',3),root=Path('/app'))
        from vigile.english import english_text
        blocks=[{**b,'display_text':english_text(b['text']),'english_generation_eligible':english_text(b['text'])==b['text']} for b in blocks]
        return {'blocks':blocks,'issues':issues,'algorithm':'REFERENCE_BM25'}
    if not owner:
        raise ValueError('LOCAL_PROFILE_LOCKED')
    from browser_monitoring import ACTIONS,LocalBiomedical
    if action in ACTIONS:
        if biomedical is None:biomedical=LocalBiomedical(store,owner)
        return biomedical.dispatch(action,data)
    if action == 'assistant_context':
        from vigile.assistant_safety import request_guard
        guard=request_guard(data['question'],owner,'browser-mission')
        if guard:return {'state':guard,'blocks':[]}
        from vigile.structured_facts import facts_for,explain
        numeric=None;runs=store.all('monitoring_run')
        if runs:
            run=runs[-1];facts=monitoring_facts(run)
            if facts:
                class ContextPrepared(Exception):pass
                class PromptRecorder:
                    def _complete(self,messages,schema,max_tokens):
                        self.prompt={'messages':messages,'schema':schema,'max_tokens':max_tokens}
                        raise ContextPrepared()
                recorder=PromptRecorder()
                try:explain(recorder,data['question'],facts,'en')
                except ContextPrepared:pass
                numeric={'facts':[fact.model_dump(mode='json') for fact in facts[:5]],'prompt':recorder.prompt,'as_of':run['as_of'],'mode':'CONTEXT_PREPARATION_ONLY_NO_INFERENCE_EXECUTED'}
        rows=store.all('browser_evaluation')
        if not rows:return {'state':'AUTHORIZED_LOCAL_CONTEXT' if numeric else 'NO_RECORDED_ASSESSMENT','blocks':[],'numeric':numeric}
        row=rows[-1]
        from browser_assistant_reference import evidence_blocks
        from vigile.english import english_result
        class Reader:
            def get(self,path):
                if path.startswith('/clinical/criteria/'):
                    return next(c for c in service.knowledge.criteria.values() if c['criterion_id']==path.rsplit('/',1)[1])
                raise ValueError('UNSUPPORTED_READ_ONLY_CONTEXT_REFERENCE')
        blocks=evidence_blocks({**row['output'],'id':row['id'],'input_hash':row['input_hash']},Reader())
        rendered=english_result({'retrieved':blocks})['retrieved']
        return {'state':'AUTHORIZED_LOCAL_CONTEXT','blocks':rendered[:8],'numeric':numeric}
    if action == 'validate_numeric_assistant':
        from vigile.structured_facts import Fact,validate_realization
        facts=[Fact.model_validate(fact) for fact in data['facts']]
        if any(fact.subject_id!=owner for fact in facts):raise ValueError('FACT_SCOPE_MISMATCH')
        for fact in facts:
            source=store.get('monitoring_run',fact.target_id)
            expected={item.id:item.model_dump(mode='json') for item in monitoring_facts(source)}
            if fact.id not in expected or digest(fact.model_dump(mode='json'))!=digest(expected[fact.id]):raise ValueError('FACT_DOES_NOT_MATCH_STORED_REFERENCE')
        return {'sentences':validate_realization(data['generated'],facts,'en'),'authority':'DESCRIPTIVE_NUMERIC_REALIZATION_ONLY'}
    if action == 'validate_assistant':
        from browser_assistant_reference import validate_generated
        from vigile.assistant_safety import clinical_claim_guard
        sentences=validate_generated(data['generated'],data['blocks'])
        for sentence in sentences:
            support=' '.join(b['text'] for b in data['blocks'] if b['id'] in sentence['evidence_ids'])
            clinical_claim_guard(sentence['text'],support)
            cited=[block for block in data['blocks'] if block['id'] in sentence['evidence_ids']]
            if any(block.get('kind')=='ENGINE' for block in cited):
                from vigile.assistant_safety import normalize
                import re
                compact=lambda text:re.sub(r'[^a-z0-9]+',' ',normalize(text)).strip()
                if compact(sentence['text']) not in compact(support):raise ValueError('ENGINE_EXPLANATION_REQUIRES_VERBATIM_SUPPORT')
            elif __import__('re').search(r'\b(?:your|you|patient)\b',sentence['text'],__import__('re').I):raise ValueError('DOCUMENT_CANNOT_ESTABLISH_PERSONAL_MEASUREMENTS')
        return {'sentences':sentences,'authority':'EXPLANATION_ONLY_NO_WRITE_OR_CLINICAL_AUTHORITY'}
    if action == 'statistics':
        from vigile.models import Measurement,Device
        from vigile.quality import assess
        from vigile.algorithms import baseline,trends
        sample=data['sample'];request=sample['request']
        if len({(row['measurement']['subject_id'],row['measurement']['mission_id']) for row in sample['snapshots']})!=1:
            raise ValueError('MIXED_STATISTICAL_INPUT_SCOPES')
        measurements=[]
        for row in sample['snapshots']:
            measurement=Measurement.model_validate({**row['measurement'],'subject_id':owner,'mission_id':'browser-mission'})
            quality=assess(measurement,Device.model_validate(row['device']),datetime.fromisoformat(request['as_of']),historical=True)
            if quality!='VALID':raise ValueError('STATISTICS_INCONCLUSIVE_'+quality)
            measurements.append(measurement)
        if sample['kind']=='baseline':output=baseline(measurements,request['minimum_observations'])
        elif sample['kind']=='trend':output=trends(measurements,request['ewma_lambda'],request['cusum_target'],request['cusum_allowance'],request['ewma_initial'],request['cusum_decision_limit'])
        else:raise ValueError('UNSUPPORTED_STATISTICAL_OPERATION')
        expected=json.loads(sample['expected_json'])
        record={'id':'statistics-'+uuid4().hex,'subject_id':owner,'source':'SYNTHETIC_STATISTICAL_FIXTURE',
                'kind':sample['kind'],'output':output,'output_hash':digest(output),'reference_matches':not differences(expected,output),
                'diagnosis':None,'execution':'BLOCKED'}
        store.put('research_stats',record['id'],record,'local_profile')
        return record
    if action == 'evaluate':
        snapshot=data['snapshot']
        request=ClinicalRequest.model_validate({**snapshot['request'],'subject_id':owner,'mission_id':'browser-mission'})
        if request.measurement_bindings:
            if biomedical is None:biomedical=LocalBiomedical(store,owner)
            service=ClinicalService(biomedical.engine)
        mission=MissionContext.model_validate({**snapshot['mission'],'id':'browser-mission','synthetic':True})
        # Same scope and inventory-snapshot path as the reference implementation.
        store.db.execute('BEGIN')
        try:
            frozen=service.snapshot(request)
            if not data.get('use_registered_context',False):frozen['mission']=mission.model_dump(mode='json')
            output=service.compute(frozen)
            record={'id':'web-eval-'+uuid4().hex,'subject_id':owner,'mission_id':'browser-mission',
                    'snapshot':frozen,'output':output,'input_hash':digest(frozen),'output_hash':digest(output),
                    'knowledge_hash':service.knowledge.hash,'source':'REFERENCE_PYTHON_IN_WASM'}
            store.insert_record('browser_evaluation',record['id'],record,'local_profile')
            store.db.execute('COMMIT')
        except Exception:
            store.db.execute('ROLLBACK')
            raise
        return record
    if action == 'history':
        return {'evaluations':store.all('browser_evaluation'),'observations':store.all('voice_observation'),'statistics':store.all('research_stats'),
                'audit_valid':store.verify(),'checkpoint':store.checkpoint()}
    if action == 'parse_observation':
        from health_voice_parser import parse
        return {'observation':parse(data['text'])}
    if action == 'voice_policy':
        from health_voice_parser import parse
        parsed=parse(data['text']);words=data.get('words') or []
        confidences=[w.get('conf') for w in words]
        confidence=min(confidences) if confidences and all(type(c) in (int,float) and 0<=c<=1 for c in confidences) else None
        eligible=bool(data.get('auto_save') is True and data.get('finalization')=='EXPLICIT_WORKER_FINAL_RESULT'
            and parsed and parsed.get('explicit') and parsed.get('structured')
            and parsed.get('kind') in ('sleep_duration','exercise_duration')
            and parsed.get('time_reference')=='PAST_24_HOURS' and confidence is not None and confidence>=.95
            and ' '.join(w.get('word','') for w in words)==data['text'])
        return {'eligible':eligible,'observation':parsed,'confidence':confidence,'policy':'ORIGINAL_V120_DURATION_ONLY_WITH_EXPLICIT_BROWSER_FINALIZATION'}
    if action == 'save_observation':
        if data.get('source') != 'SELF_REPORTED_VOICE' and data.get('source') != 'SELF_REPORTED_TYPED':
            raise ValueError('SELF_REPORTED_SOURCE_REQUIRED')
        if not isinstance(data.get('text'),str) or not 1<=len(data['text'])<=1200:raise ValueError('OBSERVATION_TEXT_BOUNDS')
        from health_voice_parser import parse
        data={**data,'observation':parse(data['text'])}
        if data.get('validation')=='AUTOMATIC_SELF_REPORT' and not dispatch('voice_policy',data)['eligible']:raise ValueError('AUTOMATIC_VOICE_POLICY_REJECTED')
        record={**data,'id':'voice-'+uuid4().hex,'subject_id':owner,'sensor_verified':False,
                'submitted_at':datetime.now(timezone.utc).isoformat(),'clinical_execution':'BLOCKED'}
        store.put('voice_observation',record['id'],record,'local_profile')
        return record
    if action == 'serialize':
        return base64.b64encode(store.db.serialize()).decode()
    raise ValueError('UNSUPPORTED_BROWSER_ACTION')
