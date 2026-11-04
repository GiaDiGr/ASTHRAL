from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest
from vigile.registry import Registry
from vigile.store import Store
from vigile.service import Engine
from vigile.models import MissionContext,AstronautProfile,Device,Measurement,EvaluationRequest

ROOT=Path(__file__).resolve().parents[2]
NOW=datetime(2026,1,2,12,tzinfo=timezone.utc)

@pytest.fixture(scope='session')
def registry(): return Registry(ROOT)

@pytest.fixture
def engine(registry,tmp_path):
    store=Store(tmp_path/'test.sqlite3'); e=Engine(registry,store)
    e.register('mission',MissionContext(id='mission',phase='IN_MISSION',gravity='MICROGRAVITY',
      environment='HABITABLE_VOLUME',mode='NOMINAL',microgravity_eva_planned_or_required=True,
      extraterrestrial_surface_eva_planned_or_required=False,exposure_context='INDEFINITE_CABIN',synthetic=True),'researcher')
    e.register('profile',AstronautProfile(id='crew',mission_id='mission',synthetic=True),'researcher')
    yield e
    store.close()

def add(e,identifier,variable,value,unit,**kwargs):
    d=kwargs.pop('device_id','dev-'+identifier)
    calibration=kwargs.pop('calibration_id','cal-'+d)
    method=kwargs.pop('method','DIRECT')
    try: e.store.get('device',d)
    except KeyError:
        e.register('device',Device(id=d,variable=variable,unit=unit,calibration_id=calibration,
          calibrated_at=NOW-timedelta(days=1000),valid_until=NOW+timedelta(days=1000),
          technical_min=0,technical_max=100000,max_age_seconds=86400*10,
          policy_reference='SYNTHETIC_FIXTURE_NOT_CLINICAL',synthetic=True,
          conflict_tolerance=0.1,alignment_seconds=1),'researcher')
    raw=dict(id=identifier,subject_id='crew',mission_id='mission',variable=variable,value=value,
      unit=unit,timestamp=NOW,device_id=d,calibration_id=calibration,method=method,
      protocol='protocol',reported_quality='ACCEPTABLE',synthetic=True,
      phase='IN_MISSION',provenance='SYNTHETIC_TEST')
    raw.update(kwargs)
    m=Measurement(**raw); e.ingest(m,'operator'); return m

def evaluate(e,rule,bindings=None,context=None,co2=None,mode='SIMULATION'):
    return e.evaluate(EvaluationRequest(rule_id='VIGILE-'+rule,subject_id='crew',mission_id='mission',
      as_of=NOW,bindings=bindings or {},context=context or {},co2_measurement_ids=co2 or [],mode=mode),'researcher')

def co2(e,value=3.01,gap=False):
    start=NOW-timedelta(minutes=20 if gap else 60)
    add(e,'co2','environment.ppco2',value,'mmHg',timestamp=start,interval_end=NOW,
        method='INTERVAL_MEAN',compartment='HAB1')
    return evaluate(e,'ENV-002',co2=['co2'])
