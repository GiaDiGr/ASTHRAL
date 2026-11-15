import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'web-local'/'src'))
import browser_bridge as bridge


def kss_payload(**updates):
    payload={'entry_type':'WELLBEING','occurred_at':'2026-11-15T10:00:00Z','label':'NeuroGuard KSS',
        'neuroguard':{'task':'KSS','score':4,'consent_given':True,
            'consent_version':'ASTHRAL_NEUROGUARD_CONSENT_1','consented_at':'2026-11-15T09:00:00Z',
            'task_context':'synthetic software test'}}
    payload.update(updates)
    return payload


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

def test_radiation_preview_validates_without_persistence_and_commit_rechecks_duplicates():
    raw={'quantity_kind':'ABSORBED_DOSE_RATE','value':1,'unit':'uGy/h','timestamp':'2026-11-15T10:00:00Z','mode':'SYNTHETIC','quality':'UNKNOWN','mission_segment':'demo','location':'fixture','source':'synthetic-fixture'}
    before=bridge.dispatch('serialize',{})
    preview=bridge.dispatch('radiation_preview',{'records':[raw]})
    assert preview['count']==1 and preview['persisted'] is False
    assert bridge.dispatch('serialize',{})==before
    bridge.dispatch('radiation_import',{'records':[raw]})
    with pytest.raises(ValueError,match='RADIATION_IMPORT_DUPLICATE_ROW_1'):
        bridge.dispatch('radiation_preview',{'records':[raw]})


def test_neuroguard_sleep_reference_is_resolved_from_same_profile_and_type():
    sleep=bridge.dispatch('prevention_add',{'entry_type':'SLEEP','occurred_at':'2026-11-15T06:00:00Z',
        'duration_minutes':420,'subjective_quality_1_5':4,'synthetic_fixture':True})
    payload={'entry_type':'WELLBEING','occurred_at':'2026-11-15T10:00:00Z','label':'NeuroGuard fatigue',
        'neuroguard':{'task':'FATIGUE_CHECK','mental_fatigue_0_10':3,'physical_fatigue_0_10':5,
            'linked_sleep_entry_id':sleep['id'],'consent_given':True,
            'consent_version':'ASTHRAL_NEUROGUARD_CONSENT_1','consented_at':'2026-11-15T09:00:00Z',
            'task_context':'synthetic software test'}}
    fatigue=bridge.dispatch('prevention_add',payload)
    assert fatigue['neuroguard']['linked_sleep_summary']=={'id':sleep['id'],'occurred_at':sleep['occurred_at'],
        'duration_minutes':420,'subjective_quality_1_5':4}
    with pytest.raises(ValueError,match='LINKED_SLEEP_ENTRY_NOT_FOUND_FOR_PROFILE'):
        bridge.dispatch('prevention_add',{**payload,'neuroguard':{**payload['neuroguard'],'linked_sleep_entry_id':'foreign-or-missing'}})
    bridge.store.put('prevention_entry','foreign-sleep',{'id':'foreign-sleep','subject_id':'another-crew',
        'entry_type':'SLEEP','duration_minutes':500},'test')
    with pytest.raises(ValueError,match='LINKED_SLEEP_ENTRY_NOT_FOUND_FOR_PROFILE'):
        bridge.dispatch('prevention_add',{**payload,'neuroguard':{**payload['neuroguard'],'linked_sleep_entry_id':'foreign-sleep'}})
    assert bridge.dispatch('history',{})['audit_valid'] is True


def test_neuroguard_delete_is_scoped_to_neuroguard_and_appends_valid_audit_event():
    sleep=bridge.dispatch('prevention_add',{'entry_type':'SLEEP','occurred_at':'2026-11-15T06:00:00Z','duration_minutes':420})
    ordinary=bridge.dispatch('prevention_add',{'entry_type':'WELLBEING','occurred_at':'2026-11-15T08:00:00Z',
        'mood_rating_1_5':3,'note':'legacy voluntary record'})
    session=bridge.dispatch('prevention_add',kss_payload())
    with pytest.raises(ValueError,match='ONLY_NEUROGUARD_SESSIONS_CAN_BE_DELETED_HERE'):
        bridge.dispatch('prevention_delete',{'id':sleep['id']})
    with pytest.raises(ValueError,match='ONLY_NEUROGUARD_SESSIONS_CAN_BE_DELETED_HERE'):
        bridge.dispatch('prevention_delete',{'id':ordinary['id']})
    result=bridge.dispatch('prevention_delete',{'id':session['id']})
    assert result=={'deleted_id':session['id'],'audit_valid':True}
    remaining=bridge.dispatch('prevention_list',{})['entries']
    assert {row['id'] for row in remaining}=={sleep['id'],ordinary['id']}
    assert bridge.store.verify() is True
    events=[__import__('json').loads(row['payload']) for row in bridge.store.db.execute('SELECT payload FROM audit')]
    assert events[-1]['event']=='DELETE_PREVENTION_ENTRY'
    assert events[-1]['data']['id']==session['id']
    with pytest.raises(KeyError):
        bridge.dispatch('prevention_delete',{'id':session['id']})


def test_completed_eva_handover_is_synthetic_audited_and_survives_profile_export():
    started='2026-11-15T10:00:00Z';ended='2026-11-15T10:00:12Z'
    payload={'id':'eva-demo-unique-001','mission_id':'demo-mission','eva_id':'demo-eva-001',
        'mode':'SIMULATION','scenario_id':'critical_training','started_at_utc':started,
        'ended_at_utc':ended,'final_state':'critical','training_condition':True,
        'report':{'report_type':'EVA Medical Handover Report','mode':'SIMULATION',
            'delivery_status':'PREPARED_LOCALLY_NOT_SENT','mission_id':'demo-mission','eva_id':'demo-eva-001',
            'scenario':{'id':'critical_training'},'training_condition':True,'final_state':'critical',
            'scenario_time_utc':started},
        'session':{'state':'completed','scenario_time_utc':started,'alerts':[],'log':[]}}
    saved=bridge.dispatch('eva_activity_add',payload)
    assert saved['stored'] is True and saved['audit_valid'] is True
    history=bridge.dispatch('history',{})
    assert history['eva_activities'][0]['subject_id']=='crew-local-test'
    assert history['eva_activities'][0]['mode']=='SIMULATION'
    assert history['audit_valid'] is True
    backup=bridge.dispatch('serialize',{})
    bridge.dispatch('init_profile',{'id':'crew-local-test','database':backup})
    assert bridge.dispatch('history',{})['eva_activities'][0]['eva_id']=='demo-eva-001'
    with pytest.raises(ValueError,match='PRIVATE_RECORD_SCOPE_MISMATCH'):
        bridge.dispatch('init_profile',{'id':'another-owner','database':bridge.dispatch('serialize',{})})


def test_eva_record_contract_rejects_live_data_and_unfinished_sessions():
    payload={'id':'eva-demo-unique-002','mission_id':'demo-mission','eva_id':'demo-eva-002',
        'mode':'SIMULATION','scenario_id':'nominal','started_at_utc':'2026-11-15T10:00:00Z',
        'ended_at_utc':'2026-11-15T10:00:01Z','final_state':'active','training_condition':False,
        'report':{'report_type':'EVA Medical Handover Report','mode':'LIVE',
            'delivery_status':'PREPARED_LOCALLY_NOT_SENT','mission_id':'demo-mission','eva_id':'demo-eva-002',
            'scenario':{'id':'nominal'},'training_condition':False,'final_state':'active','scenario_time_utc':'2026-11-15T10:00:00Z'},
        'session':{'state':'active','scenario_time_utc':'2026-11-15T10:00:00Z'}}
    with pytest.raises(ValueError,match='EVA_REPORT_MUST_BE_LOCAL_SIMULATION'):
        bridge.dispatch('eva_activity_add',payload)
    payload['report']['mode']='SIMULATION'
    with pytest.raises(ValueError,match='EVA_ACTIVITY_MUST_BE_COMPLETED_BEFORE_STORAGE'):
        bridge.dispatch('eva_activity_add',payload)
