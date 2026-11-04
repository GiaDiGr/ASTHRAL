import pytest
from datetime import timedelta
from pydantic import ValidationError
from conftest import add,evaluate,NOW,ROOT
from vigile.models import Measurement,EvaluationRequest
from vigile.demo import run

@pytest.mark.parametrize('value',[True,False,'40'])
def test_measurement_coercion_forbidden(engine,value):
    with pytest.raises(ValidationError): add(engine,'bad','physiology.vo2max',value,'mL/min/kg')

def test_subject_mismatch_rejected(engine):
    from vigile.models import AstronautProfile
    engine.register('profile',AstronautProfile(id='other',mission_id='mission',synthetic=True),'researcher')
    add(engine,'x','physiology.vo2max',40,'mL/min/kg',subject_id='other')
    assert evaluate(engine,'AER-001',{'vo2max_relative':'x'})['reason']=='MEASUREMENT_SCOPE_MISMATCH'

def test_direct_co2_average_not_accepted(engine):
    add(engine,'fake','environment.ppco2',2,'mmHg',compartment='HAB1')
    assert evaluate(engine,'ENV-002',{'one_hour_average_ppco2':'fake'})['result']=='INCONCLUSIVE'

def test_point_sample_cannot_cover_hour(engine):
    add(engine,'point','environment.ppco2',2,'mmHg',timestamp=NOW-timedelta(hours=1),method='INTERVAL_MEAN',compartment='HAB1')
    assert evaluate(engine,'ENV-002',co2=['point'])['reason']=='INSUFFICIENT_TEMPORAL_COVERAGE'

def test_nutrition_matching_units_periods(engine):
    for id,var,value,unit in [('r','nutrition.energy',2500,'kcal'),('p','nutrition.energy',2500,'kcal')]:
        add(engine,id,var,value,unit,timestamp=NOW-timedelta(days=1),interval_end=NOW)
    context={'requirement_period':'MISSION_DEFINED_DAY','requirement_calculation_method_approved':True}
    out=evaluate(engine,'NUT-001',{'calculated_requirements':{'energy':'r'},'provided_amounts':{'energy':'p'}},context)
    assert out['result']=='REQUIREMENT_MET'

def test_synthetic_only_even_with_valid_inputs(engine):
    from vigile.models import AstronautProfile,MissionContext
    engine.register('mission',MissionContext(id='real',phase='IN_MISSION',gravity='MICROGRAVITY',environment='HABITABLE_VOLUME',mode='NOMINAL',synthetic=False),'researcher')
    engine.register('profile',AstronautProfile(id='realcrew',mission_id='real',synthetic=False),'researcher')
    out=engine.evaluate(EvaluationRequest(rule_id='VIGILE-AER-001',subject_id='realcrew',mission_id='real',as_of=NOW,mode='SIMULATION'),'researcher')
    assert out['reason']=='SYNTHETIC_SCOPE_REQUIRED'
