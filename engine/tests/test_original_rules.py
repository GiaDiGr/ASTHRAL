import pytest
from vigile.rules import calculate
from conftest import ROOT
import json

RULES=json.loads((ROOT/'02_REGLAS_ORIGINALES_15/REGLAS_15_ORIGINALES.json').read_bytes())
CASES=[(r,t) for r in RULES for t in r['test_cases']]

@pytest.mark.parametrize('rule,case',CASES,ids=[t['id'] for r,t in CASES])
def test_every_original_embedded_case(rule,case):
    # Explicit supplemental context missing from terse original test fixtures.
    ctx={'mission_phase':'PRE_MISSION' if rule['rule_id']=='VIGILE-MUS-001' else 'IN_MISSION',
      'environment':'HABITABLE_VOLUME','mode':'NOMINAL',
      'radiation_context':'DESIGN_REFERENCE_SOLAR_PARTICLE_EVENT',
      'nuclear_technology_emitting_ionizing_radiation_present':True,'beyond_low_earth_orbit':True}
    actual=calculate(rule,case['inputs'],ctx)
    mapping={'PASS':'REQUIREMENT_MET','FAIL_REQUIREMENT':'REQUIREMENT_NOT_MET'}
    assert actual['result']==mapping.get(case['expected'],case['expected']),actual
    assert actual['diagnosis'] is None

@pytest.mark.parametrize('rule',RULES,ids=[r['rule_id'] for r in RULES])
def test_empty_inputs_never_pass(rule):
    assert calculate(rule,{}, {})['result'] not in ('REQUIREMENT_MET','REQUIREMENT_NOT_MET')
