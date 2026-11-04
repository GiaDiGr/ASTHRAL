"""Synthetic local end-to-end demo: HTTP contracts, SQLite and replay, no network."""
from tempfile import TemporaryDirectory
from datetime import datetime,timezone,timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from .api import create_app
from .store import Store

def run(root):
    token='demo-research-token-not-for-deployment'
    now=datetime.now(timezone.utc).replace(microsecond=0)
    with TemporaryDirectory() as temp:
        database=Path(temp)/'demo.sqlite3'
        with TestClient(create_app(root,database,{token:'researcher'})) as c:
            c.headers['Authorization']='Bearer '+token
            def post(url,body):
                response=c.post(url,json=body)
                response.raise_for_status()
                return response.json()
            post('/missions',dict(id='demo',phase='IN_MISSION',gravity='MICROGRAVITY',environment='HABITABLE_VOLUME',mode='NOMINAL',microgravity_eva_planned_or_required=True,synthetic=True))
            post('/profiles',dict(id='crew',mission_id='demo',synthetic=True))
            post('/devices',dict(id='ergometer',variable='physiology.vo2max',unit='mL/min/kg',calibration_id='cal-demo',calibrated_at=(now-timedelta(days=1)).isoformat(),valid_until=(now+timedelta(days=1)).isoformat(),technical_min=0,technical_max=100,max_age_seconds=3600,policy_reference='SYNTHETIC_DEMO_ONLY',synthetic=True))
            post('/measurements',dict(id='vo2',subject_id='crew',mission_id='demo',variable='physiology.vo2max',value=32.8,unit='mL/min/kg',timestamp=now.isoformat(),device_id='ergometer',calibration_id='cal-demo',method='DIRECT',protocol='demo-protocol',phase='IN_MISSION',reported_quality='ACCEPTABLE',synthetic=True,provenance='SYNTHETIC_DEMO'))
            finding=post('/evaluations',dict(rule_id='VIGILE-AER-001',subject_id='crew',mission_id='demo',as_of=now.isoformat(),bindings={'vo2max_relative':'vo2'},mode='SIMULATION'))
            assert finding['result']=='REQUIREMENT_NOT_MET' and finding['diagnosis'] is None
            post('/episodes',dict(id='episode',subject_id='crew',mission_id='demo',condition_id='C001',finding_ids=[finding['id']]))
            action=post('/action-requests',dict(episode_id='episode',action='treatment'))
            replay=c.get('/findings/'+finding['id']+'/explanation').json()
            spec=c.get('/openapi.json').json()
            (root/'docs/openapi.json').write_text(__import__('json').dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
        s=Store(database)
        persisted=s.get('finding',finding['id']);audit=s.verify();s.close()
        assert persisted==finding and audit and replay['verified'] and not action['executed']
        return {'simulation_result':finding['result'],'diagnosis':None,'action':action,
                'replay_verified':replay['verified'],'persisted_after_reopen':True,'audit_valid':audit,
                'synthetic':True,'clinical_validation':False}
