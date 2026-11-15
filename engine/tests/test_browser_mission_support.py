import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web-local'/'src'))
import browser_bridge as bridge


@pytest.fixture(autouse=True)
def fresh_profile():
    bridge.dispatch('init_profile',{'id':'crew-local-test'})
    yield
    bridge.store.close()


def test_prevention_and_radiation_records_share_profile_store_and_audit():
    entry=bridge.dispatch('prevention_add',{'entry_type':'SLEEP','occurred_at':'2026-11-15T03:00:00Z','duration_minutes':390,'subjective_quality_1_5':3})
    radiation=bridge.dispatch('radiation_add',{'quantity_kind':'ABSORBED_DOSE','value':2,'unit':'mGy','timestamp':'2026-11-15T10:00:00Z','mode':'MEASURED','quality':'UNKNOWN','mission_segment':'mission-1','location':'habitat-A','source':'MANUAL_SELF_REPORT'})
    report=bridge.dispatch('history',{})
    assert entry['source']=='SELF_REPORTED' and entry['subject_id']=='crew-local-test'
    assert radiation['sensor_verified'] is False and radiation['subject_id']=='crew-local-test'
    assert report['prevention_entries'][0]['id']==entry['id']
    assert report['radiation_records'][0]['id']==radiation['id']
    assert report['audit_valid'] is True


def test_radiation_duplicate_observation_is_rejected_and_counter_data_stays_separate():
    raw={'quantity_kind':'CUMULATIVE_ABSORBED_DOSE','value':1,'unit':'mGy','timestamp':'2026-11-15T10:00:00Z','mode':'MEASURED','quality':'VALID','mission_segment':'mission-1','location':'habitat-A','source':'MANUAL_SELF_REPORT','instrument_id':'D-1'}
    bridge.dispatch('radiation_add',raw)
    with pytest.raises(ValueError,match='DUPLICATE_RADIATION_OBSERVATION'):
        bridge.dispatch('radiation_add',raw)
    summary=bridge.dispatch('radiation_list',{})
    assert summary['counter_review']['status']=='INSUFFICIENT_DATA'


def test_dose_rate_calculation_filters_quantity_and_requires_explicit_gap():
    for value,time in [(1,'2026-11-15T10:00:00Z'),(3,'2026-11-15T11:00:00Z')]:
        bridge.dispatch('radiation_add',{'quantity_kind':'ABSORBED_DOSE_RATE','value':value,'unit':'mGy/h','timestamp':time,'mode':'MEASURED','quality':'VALID','mission_segment':'mission-1','location':'habitat-A','source':'MANUAL_SELF_REPORT','instrument_id':'D-1'})
    result=bridge.dispatch('radiation_integrate',{'quantity_kind':'ABSORBED_DOSE_RATE','max_gap_seconds':3600})
    assert result['total']['unit']=='Gy' and result['total']['value']==pytest.approx(.002)
    assert result['execution']=='BLOCKED' and result['clinical_interpretation']=='NOT_PROVIDED'
    with pytest.raises(ValueError,match='RATE_QUANTITY_REQUIRED'):
        bridge.dispatch('radiation_integrate',{'quantity_kind':'ABSORBED_DOSE','max_gap_seconds':3600})
    with pytest.raises(ValueError,match='RATE_QUANTITY_REQUIRED'):
        bridge.dispatch('radiation_integrate',{'quantity_kind':[],'max_gap_seconds':3600})


def test_new_records_are_rejected_when_restored_under_another_owner():
    bridge.dispatch('prevention_add',{'entry_type':'MEAL_NOTE','occurred_at':'2026-11-15T10:00:00Z','label':'Breakfast'})
    serialized=bridge.dispatch('serialize',{})
    with pytest.raises(ValueError,match='PRIVATE_RECORD_SCOPE_MISMATCH'):
        bridge.dispatch('init_profile',{'id':'different-owner','database':serialized})
