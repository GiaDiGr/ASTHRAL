"""Validated, explicitly self-reported prevention and recovery journal entries."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

KINDS = {"EXERCISE_SESSION", "HYDRATION", "MEAL_NOTE", "SLEEP", "WELLBEING"}


def _time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("INVALID_OCCURRED_AT") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("OCCURRED_AT_REQUIRES_TIMEZONE")
    return parsed.isoformat()


def _number(value, name, minimum, maximum, integral=False, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, bool):
        raise ValueError("INVALID_" + name.upper())
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("INVALID_" + name.upper()) from None
    if not result.is_finite() or result < minimum or result > maximum or integral and result != result.to_integral_value():
        raise ValueError("OUT_OF_RANGE_" + name.upper())
    return int(result) if integral else float(result)


def normalize_entry(raw, subject_id):
    if not isinstance(raw, dict):
        raise ValueError("PREVENTION_ENTRY_OBJECT_REQUIRED")
    kind = raw.get("entry_type")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError("UNSUPPORTED_PREVENTION_ENTRY")
    label = raw.get("label", "")
    note = raw.get("note", "")
    if not isinstance(label, str) or len(label.strip()) > 120 or not isinstance(note, str) or len(note.strip()) > 1000:
        raise ValueError("PREVENTION_TEXT_BOUNDS")
    output = {"subject_id": subject_id, "entry_type": kind, "occurred_at": _time(raw.get("occurred_at")),
              "label": label.strip(), "note": note.strip(), "source": "SELF_REPORTED", "sensor_verified": False,
              "clinical_interpretation": "NOT_PROVIDED", "clinical_execution": "BLOCKED"}
    if kind == "EXERCISE_SESSION":
        output["duration_minutes"] = _number(raw.get("duration_minutes"), "duration_minutes", 1, 1440, integral=True)
        output["perceived_exertion_0_10"] = _number(raw.get("perceived_exertion_0_10"), "perceived_exertion_0_10", 0, 10, optional=True)
        workout_type = raw.get("workout_type", "USER_REPORTED")
        output["workout_type"] = workout_type if isinstance(workout_type, str) and workout_type in {"USER_REPORTED", "RESISTANCE", "AEROBIC", "MOBILITY", "BALANCE", "OTHER"} else "OTHER"
    elif kind == "HYDRATION":
        output["amount_ml"] = _number(raw.get("amount_ml"), "amount_ml", 1, 100000)
        output["amount_source"] = "USER_ENTERED_NO_COMPOSITION_OR_CLINICAL_TARGET"
    elif kind == "SLEEP":
        output["duration_minutes"] = _number(raw.get("duration_minutes"), "duration_minutes", 1, 1440, integral=True)
        output["subjective_quality_1_5"] = _number(raw.get("subjective_quality_1_5"), "subjective_quality_1_5", 1, 5, integral=True, optional=True)
    elif kind == "WELLBEING":
        output["mood_rating_1_5"] = _number(raw.get("mood_rating_1_5"), "mood_rating_1_5", 1, 5, integral=True, optional=True)
        output["stress_rating_1_5"] = _number(raw.get("stress_rating_1_5"), "stress_rating_1_5", 1, 5, integral=True, optional=True)
        if output["mood_rating_1_5"] is None and output["stress_rating_1_5"] is None and not output["note"]:
            raise ValueError("WELLBEING_ENTRY_EMPTY")
        output["interpretation"] = "VOLUNTARY_SELF_RATING_NO_SCREENING_OR_DIAGNOSIS"
    elif kind == "MEAL_NOTE" and not output["label"] and not output["note"]:
        raise ValueError("MEAL_NOTE_EMPTY")
    return output
