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

def differences(expected, actual, path='root'):
    if isinstance(expected, dict) and isinstance(actual, dict):
        return [item for key in sorted(expected.keys() | actual.keys()) for item in differences(expected.get(key),actual.get(key),path+'.'+key)]
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected)!=len(actual):return [{'path':path,'expected_length':len(expected),'actual_length':len(actual)}]
        return [item for i,(left,right) in enumerate(zip(expected,actual)) for item in differences(left,right,path+f'[{i}]')]
    if expected != actual or type(expected) != type(actual):
        return [{'path':path,'expected':expected,'actual':actual,'types':[type(expected).__name__,type(actual).__name__]}]
    return []

def dispatch(action, data):
    global store, service, owner
    if action == 'init_profile':
        store.close()
        store=Store(':memory:')
        service=ClinicalService(SimpleNamespace(store=store))
        owner = data['id']
        if data.get('database'):
            store.db.deserialize(base64.b64decode(data['database'], validate=True))
            if store.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or not store.verify():
                raise ValueError('LOCAL_DATABASE_INTEGRITY_FAILED')
            if store.db.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise ValueError('LOCAL_DATABASE_VERSION_UNSUPPORTED')
            for kind in ('browser_evaluation','voice_observation','research_stats'):
                if any(row.get('subject_id')!=owner for row in store.all(kind)):
                    raise ValueError('PRIVATE_RECORD_SCOPE_MISMATCH')
            profiles = store.all('profile')
            if len(profiles) != 1 or profiles[0]['id'] != owner:
                raise ValueError('PROFILE_BINDING_MISMATCH')
        else:
            mission=MissionContext(id='browser-mission',phase='IN_MISSION',gravity='EARTH',
                                   environment='HABITABLE_CABIN',mode='NOMINAL',synthetic=True)
            store.put('mission',mission.id,mission.model_dump(mode='json'))
            profile=AstronautProfile(id=owner,mission_id=mission.id,synthetic=True)
            store.put('profile',owner,profile.model_dump(mode='json'))
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
    if action == 'search':
        from vigile.knowledge_v08 import search
        from pathlib import Path
        blocks,issues=search(data['corpus'],data['question'],data.get('limit',3),root=Path('/app'))
        return {'blocks':blocks,'issues':issues,'algorithm':'REFERENCE_BM25'}
    if not owner:
        raise ValueError('LOCAL_PROFILE_LOCKED')
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
            raise ValueError('BROWSER_MEASUREMENT_BINDING_NOT_YET_PORTED')
        mission=MissionContext.model_validate({**snapshot['mission'],'id':'browser-mission','synthetic':True})
        # Same scope and inventory-snapshot path as the reference implementation.
        store.db.execute('BEGIN')
        try:
            frozen=service.snapshot(request)
            frozen['mission']=mission.model_dump(mode='json')
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
    if action == 'save_observation':
        if data.get('source') != 'SELF_REPORTED_VOICE' and data.get('source') != 'SELF_REPORTED_TYPED':
            raise ValueError('SELF_REPORTED_SOURCE_REQUIRED')
        record={**data,'id':'voice-'+uuid4().hex,'subject_id':owner,'sensor_verified':False,
                'submitted_at':datetime.now(timezone.utc).isoformat(),'clinical_execution':'BLOCKED'}
        store.put('voice_observation',record['id'],record,'local_profile')
        return record
    if action == 'serialize':
        return base64.b64encode(store.db.serialize()).decode()
    raise ValueError('UNSUPPORTED_BROWSER_ACTION')
