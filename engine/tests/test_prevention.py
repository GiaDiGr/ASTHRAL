import pytest
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
    row=entry("SLEEP",duration_minutes=420,subjective_quality_1_5=4)
    assert row["subjective_quality_1_5"]==4
    assert "device" not in str(row).lower()


def test_hydration_and_meal_note_do_not_infer_nutrition_content():
    hydration=entry("HYDRATION",amount_ml=500)
    meal=entry("MEAL_NOTE",label="Breakfast",note="User-entered meal note")
    assert hydration["amount_source"].startswith("USER_ENTERED")
    assert "calories" not in meal and "protein" not in meal


def test_wellbeing_is_voluntary_self_rating_without_diagnosis():
    row=entry("WELLBEING",mood_rating_1_5=2,stress_rating_1_5=3)
    assert row["interpretation"]=="VOLUNTARY_SELF_RATING_NO_SCREENING_OR_DIAGNOSIS"


def test_out_of_range_or_empty_records_are_rejected():
    with pytest.raises(ValueError):entry("SLEEP",duration_minutes=2000)
    with pytest.raises(ValueError,match="WELLBEING_ENTRY_EMPTY"):entry("WELLBEING")
    with pytest.raises(ValueError,match="REQUIRES_TIMEZONE"):entry("SLEEP",duration_minutes=360,occurred_at="2026-11-15T10:00")
    with pytest.raises(ValueError,match="UNSUPPORTED_PREVENTION_ENTRY"):
        entry([],duration_minutes=20)
