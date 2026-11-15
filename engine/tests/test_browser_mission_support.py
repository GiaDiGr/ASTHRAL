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


def test_radiation_csv_import_is_atomic_validated_and_audited():
    base={'quantity_kind':'ABSORBED_DOSE_RATE','value':1,'unit':'uGy/h','timestamp':'2026-11-15T10:00:00Z','mode':'SYNTHETIC','quality':'UNKNOWN','mission_segment':'demo','location':'fixture','source':'synthetic-fixture'}
    with pytest.raises(ValueError,match='RADIATION_IMPORT_DUPLICATE_ROW_2'):
        bridge.dispatch('radiation_import',{'records':[base,{**base,'value':2}]})
    assert bridge.dispatch('radiation_list',{})['records']==[]
    result=bridge.dispatch('radiation_import',{'records':[base,{**base,'timestamp':'2026-11-15T11:00:00Z'}]})
    assert result['count']==2 and result['atomic'] is True and result['audit_valid'] is True
    assert all(row['source_kind']=='FILE_IMPORT' and row['synthetic_data'] for row in result['records'])


def test_new_preventive_records_survive_encrypted_export_restore_with_owner_scope():
    exercise={'session_id':'session-roundtrip','plan_id':'mobility-basics','title':'Generic mobility example','workout_type':'MOBILITY','status':'PAUSED','started_at':'2026-11-15T10:00:00Z','updated_at':'2026-11-15T10:05:00Z','elapsed_seconds':300,'current_activity_index':1,'activities':[{'exercise_id':'ankle-circles','sets_completed':1,'repetitions':6,'duration_seconds':60,'workload_note':''}]}
    bridge.dispatch('prevention_add',{'entry_type':'EXERCISE_SESSION','occurred_at':'2026-11-15T10:05:00Z','label':'Generic mobility example','duration_minutes':5,'workout_type':'MOBILITY','training_session':exercise,'synthetic_fixture':True})
    bridge.dispatch('prevention_add',{'entry_type':'MEAL_NOTE','occurred_at':'2026-11-15T11:00:00Z','food_id':'1105073','quantity_g':100,'synthetic_fixture':True})
    bridge.dispatch('prevention_add',{'entry_type':'SLEEP','occurred_at':'2026-11-15T06:00:00Z','sleep_start':'2026-11-14T22:30:00Z','sleep_end':'2026-11-15T06:00:00Z','duration_minutes':450,'subjective_quality_1_5':4,'synthetic_fixture':True})
    encrypted_export=bridge.dispatch('serialize',{})
    bridge.dispatch('init_profile',{'id':'crew-local-test','database':encrypted_export})
    rows=bridge.dispatch('prevention_list',{})['entries']
    assert len(rows)==3 and all(row['synthetic_data'] for row in rows)
    session=next(row['training_session'] for row in rows if row['entry_type']=='EXERCISE_SESSION')
    assert session['current_activity_index']==1 and session['status']=='PAUSED'
    meal=next(row for row in rows if row['entry_type']=='MEAL_NOTE')
    assert meal['nutrient_estimate']['energy_kcal']==85.0
    assert bridge.dispatch('history',{})['audit_valid'] is True


def test_new_records_are_rejected_when_restored_under_another_owner():
    bridge.dispatch('prevention_add',{'entry_type':'MEAL_NOTE','occurred_at':'2026-11-15T10:00:00Z','label':'Breakfast'})
    serialized=bridge.dispatch('serialize',{})
    with pytest.raises(ValueError,match='PRIVATE_RECORD_SCOPE_MISMATCH'):
        bridge.dispatch('init_profile',{'id':'different-owner','database':serialized})
