import pytest
from pathlib import Path
import vigile.prevention as prevention
from vigile.prevention import normalize_entry


def entry(entry_type, **updates):
    row={"entry_type":entry_type,"occurred_at":"2026-11-15T10:00:00Z","label":"","note":""}
    row.update(updates)
    return normalize_entry(row,"synthetic-crew")


def test_exercise_is_user_reported_and_not_a_prescription():
    row=entry("EXERCISE_SESSION",label="Resistance session",duration_minutes=35,perceived_exertion_0_10=6,workout_type="RESISTANCE")
    assert row["source"]=="SELF_REPORTED"
    assert row["sensor_verified"] is False
    assert row["clinical_execution"]=="BLOCKED"


def test_sleep_quality_is_a_subjective_rating():
    row=entry("SLEEP",duration_minutes=420,subjective_quality_1_5=4,fatigue_rating_0_10=6)
    assert row["subjective_quality_1_5"]==4
    assert row["fatigue_rating_0_10"]==6
    assert "device" not in str(row).lower()


def test_hydration_and_meal_note_do_not_infer_nutrition_content():
    hydration=entry("HYDRATION",amount_ml=500)
    meal=entry("MEAL_NOTE",label="Breakfast",note="User-entered meal note")
    assert hydration["amount_source"].startswith("USER_ENTERED")
    assert "calories" not in meal and "protein" not in meal


def test_usda_foundation_food_meal_estimate_uses_local_food_id_and_preserves_provenance():
    row=entry("MEAL_NOTE",occurred_at="2026-11-15T10:00:00Z",food_id="1105073",quantity_g=150)
    assert row["food_name"]=="Bananas, overripe, raw"
    assert row["nutrient_estimate"]["energy_kcal"]==127.5
    assert row["nutrient_estimate"]["protein_g"]==1.095
    assert row["nutrition_reference"]["catalog_id"]=="USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT_V2"
    assert len(row["nutrition_reference"]["source_archive_sha256"])==64
    with pytest.raises(ValueError,match="UNKNOWN_USDA_FDC_FOOD_ID"):
        entry("MEAL_NOTE",food_id="not-in-catalog",quantity_g=100)


def test_pyodide_package_layout_can_resolve_the_bundled_catalog(tmp_path,monkeypatch):
    app=tmp_path/'app';(app/'vigile').mkdir(parents=True);nutrition=app/'web-local'/'src'/'nutrition';nutrition.mkdir(parents=True)
    source=Path(__file__).resolve().parents[2]/'web-local'/'src'/'nutrition'
    for name in ('foods.json','foods.json.sha256'):(nutrition/name).write_bytes((source/name).read_bytes())
    monkeypatch.setattr(prevention,'__file__',str(app/'vigile'/'prevention.py'))
    prevention._food_catalog.cache_clear()
    try:
        row=entry('MEAL_NOTE',food_id='1105073',quantity_g=100)
        assert row['nutrient_estimate']['energy_kcal']==85.0
    finally:
        prevention._food_catalog.cache_clear()


def test_missing_usda_nutrient_stays_unknown_in_estimate():
    row=entry("MEAL_NOTE",food_id="2768188",quantity_g=100)
    assert row["nutrient_estimate"]["energy_kcal"] is None


def test_guided_exercise_state_is_auditable_self_report_not_an_intensity_prescription():
    session={"session_id":"session-1","title":"Mobility example","workout_type":"MOBILITY","status":"PAUSED",
        "started_at":"2026-11-15T10:00:00Z","updated_at":"2026-11-15T10:02:00Z","elapsed_seconds":120,
        "activities":[{"exercise_id":"shoulder-range","sets_completed":1,"repetitions":5,"duration_seconds":0,"workload_note":"bodyweight"}]}
    row=entry("EXERCISE_SESSION",occurred_at="2026-11-15T10:02:00Z",duration_minutes=2,workout_type="MOBILITY",training_session=session)
    assert row["training_session"]["status"]=="PAUSED"
    assert row["training_session"]["activities"][0]["repetitions"]==5
    assert "NOT_PERSONALIZED" in row["training_session"]["guidance_scope"]
    session["workout_type"]="UNAPPROVED_CLINICAL_PLAN"
    with pytest.raises(ValueError,match="INVALID_TRAINING_SESSION_TYPE"):
        entry("EXERCISE_SESSION",occurred_at="2026-11-15T10:02:00Z",duration_minutes=2,training_session=session)


def test_sleep_interval_is_timezone_aware_and_matches_recorded_duration():
    row=entry("SLEEP",occurred_at="2026-11-16T06:00:00Z",duration_minutes=450,
        sleep_start="2026-11-15T22:30:00Z",sleep_end="2026-11-16T06:00:00Z")
    assert row["sleep_start"].endswith("+00:00")
    with pytest.raises(ValueError,match="SLEEP_INTERVAL_DURATION_MISMATCH"):
        entry("SLEEP",occurred_at="2026-11-16T06:00:00Z",duration_minutes=400,
            sleep_start="2026-11-15T22:30:00Z",sleep_end="2026-11-16T06:00:00Z")


def test_wellbeing_is_voluntary_self_rating_without_diagnosis():
    row=entry("WELLBEING",mood_rating_1_5=2,stress_rating_1_5=3)
    assert row["interpretation"]=="VOLUNTARY_SELF_RATING_NO_SCREENING_OR_DIAGNOSIS"


def test_synthetic_demo_entries_have_distinct_provenance():
    row=entry("SLEEP",duration_minutes=405,synthetic_fixture=True)
    assert row["source"]=="SYNTHETIC_FIXTURE" and row["synthetic_data"] is True
    assert row["clinical_execution"]=="BLOCKED"
    with pytest.raises(ValueError,match="INVALID_SYNTHETIC_FIXTURE_FLAG"):
        entry("SLEEP",duration_minutes=405,synthetic_fixture="true")


def test_out_of_range_or_empty_records_are_rejected():
    with pytest.raises(ValueError):entry("SLEEP",duration_minutes=2000)
    with pytest.raises(ValueError,match="WELLBEING_ENTRY_EMPTY"):entry("WELLBEING")
    with pytest.raises(ValueError,match="REQUIRES_TIMEZONE"):entry("SLEEP",duration_minutes=360,occurred_at="2026-11-15T10:00")
    with pytest.raises(ValueError,match="UNSUPPORTED_PREVENTION_ENTRY"):
        entry([],duration_minutes=20)

def pose_summary(**updates):
    data={"model":{"runtime":"0.10.21","model_sha256":"59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a"},"source_sha256":"a"*64,"projection":"IMAGE_PLANE_2D","joint":"left_elbow","frames":10,"valid_angle_frames":8,"missing_angle_frames":2,"angle_min_degrees":50,"angle_max_degrees":160,"cycle_limits":{"low":70,"high":150},"cycles":None,"observed_complete_cycles":1,"analyzed_at":"2026-11-15T10:00:00Z"}
    data.update(updates);return data


def test_pose_summary_is_untrusted_and_never_converts_missing_tracking_to_zero():
    row=prevention._pose_summary(pose_summary(runtime_execution_verified=True,sensor_verified=True,clinical_execution="AUTHORIZED"))
    assert row["cycles"] is None and row["observed_complete_cycles"]==1
    assert row["cycle_status"]=="PARTIAL_TRACKING" and row["runtime_execution_verified"] is False
    assert row["sensor_verified"] is False and row["clinical_execution"]=="BLOCKED"
    missing=prevention._pose_summary(pose_summary(valid_angle_frames=0,missing_angle_frames=10,angle_min_degrees=None,angle_max_degrees=None,observed_complete_cycles=None))
    assert missing["cycle_status"]=="INSUFFICIENT_TRACKING" and missing["cycles"] is None
    assert missing["source_recorded_at"] is None and missing["temporal_correspondence_verified"] is False


@pytest.mark.parametrize("updates",[{"cycles":0},{"valid_angle_frames":9},{"observed_complete_cycles":5},{"source_sha256":"forged"},{"model":{"runtime":"0.10.21","model_sha256":"bad"}},{"angle_min_degrees":float('nan')},{"analyzed_at":"2026-11-15T10:00:00"}])
def test_pose_summary_rejects_contradictory_or_invalid_claims(updates):
    with pytest.raises(ValueError):prevention._pose_summary(pose_summary(**updates))

def test_pose_summary_camera_does_not_invent_a_source_file_hash_or_recording_time():
    result=prevention._pose_summary(pose_summary(source="USER_CAMERA_UNVERIFIED",source_sha256=None,capture_started_at="2026-11-15T10:00:00Z"))
    assert result["source_kind"]=="USER_CAMERA_UNVERIFIED" and result["source_sha256"] is None
    assert result["source_recorded_at"] is None and result["runtime_execution_verified"] is False
    with pytest.raises(ValueError,match="CAMERA_SOURCE_FILE_HASH"):
        prevention._pose_summary(pose_summary(source="USER_CAMERA_UNVERIFIED"))


def test_motion_summary_is_attached_without_replacing_manual_activity_counts():
    session={"session_id":"synthetic-motion-session","title":"Synthetic software test","workout_type":"RESISTANCE","status":"PAUSED","started_at":"2026-11-15T09:00:00Z","updated_at":"2026-11-15T10:00:00Z","elapsed_seconds":60,"activities":[{"exercise_id":"manual-example","sets_completed":2,"repetitions":8,"duration_seconds":60}],"motion_summary":pose_summary()}
    result=entry("EXERCISE_SESSION",duration_minutes=1,training_session=session,synthetic_fixture=True)
    assert result["training_session"]["activities"][0]["repetitions"]==8
    assert result["training_session"]["motion_summary"]["cycles"] is None
    assert result["training_session"]["motion_summary"]["source"]=="CLIENT_REPORTED_POSE_ESTIMATE"
    assert result["clinical_execution"]=="BLOCKED" and result["synthetic_data"] is True

def test_energy_reference_alternatives_are_named_source_values_not_imputed_energy():
    legacy=entry("MEAL_NOTE",food_id="2262074",quantity_g=10)
    assert legacy["nutrient_estimate"]["energy_kcal"] is None
    assert legacy["energy_reference_estimates_kcal"]["ATWATER_GENERAL_2047"]==64.5
    general=entry("MEAL_NOTE",food_id="2262074",quantity_g=10,energy_basis="ATWATER_GENERAL_2047")
    specific=entry("MEAL_NOTE",food_id="2262074",quantity_g=10,energy_basis="ATWATER_SPECIFIC_2048")
    assert general["nutrient_estimate"]["energy_kcal"]==64.5 and specific["nutrient_estimate"]["energy_kcal"]==60.3
    assert general["nutrition_reference"]["energy_basis"]=="ATWATER_GENERAL_2047"
    assert len(general["nutrition_reference"]["catalog_content_sha256"])==64
    with pytest.raises(ValueError,match="INVALID_USDA_ENERGY_BASIS"):
        entry("MEAL_NOTE",food_id="2262074",quantity_g=10,energy_basis="GUESS_FROM_MACROS")


def test_original_food_catalog_remains_available_by_explicit_version():
    row=entry("MEAL_NOTE",food_id="1105073",quantity_g=100,nutrition_catalog_id="USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT")
    assert row["nutrient_estimate"]["energy_kcal"]==85
    assert row["nutrition_reference"]["catalog_content_sha256"]=="a09e222154963247cbb4f24b0a643385a6f2c5fac26d4aa0956dab34d1d6ad17"


def test_nutrition_builder_refuses_an_unpinned_source_archive(tmp_path):
    import importlib.util
    source=Path(__file__).resolve().parents[2]/"tools/build_nutrition_catalog.py"
    spec=importlib.util.spec_from_file_location("nutrition_builder_test",source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    fake=tmp_path/"unverified.zip";fake.write_bytes(b"not the official USDA archive")
    with pytest.raises(ValueError,match="USDA_SOURCE_ARCHIVE_HASH_MISMATCH"):
        module.build(fake,tmp_path/"foods.json")
    assert not (tmp_path/"foods.json").exists()


@pytest.mark.parametrize("field,error",[("nutrition_catalog_id","NUTRITION_CATALOG_VERSION_UNSUPPORTED"),("energy_basis","INVALID_USDA_ENERGY_BASIS")])
def test_malformed_nutrition_reference_selector_is_a_validation_error(field,error):
    with pytest.raises(ValueError,match=error):entry("MEAL_NOTE",food_id="1105073",quantity_g=100,**{field:[]})
