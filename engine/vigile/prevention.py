"""Validated, explicitly self-reported prevention and recovery journal entries."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import json
import hashlib
from pathlib import Path

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


@lru_cache(maxsize=3)
def _food_catalog(catalog_id=None):
    requested = catalog_id or "USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT_V2"
    if requested not in {"USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT", "USDA_FDC_FOUNDATION_FOODS_2026_10_ASTHRAL_COMPACT_V2"}:
        raise ValueError("NUTRITION_CATALOG_VERSION_UNSUPPORTED")
    filename = "foods-v1.json" if requested.endswith("_COMPACT") else "foods.json"
    candidates = [Path(__file__).resolve().parents[2] / "web-local" / "src" / "nutrition" / filename,
                  Path(__file__).resolve().parents[1] / "web-local" / "src" / "nutrition" / filename,
                  Path("/app/web-local/src/nutrition") / filename]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise ValueError("NUTRITION_CATALOG_UNAVAILABLE")
    try:
        content = path.read_bytes()
        expected = path.with_suffix(path.suffix + ".sha256").read_text(encoding="ascii").strip()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("NUTRITION_CATALOG_HASH_MISMATCH")
        data = json.loads(content)
    except (OSError, json.JSONDecodeError):
        raise ValueError("NUTRITION_CATALOG_UNAVAILABLE") from None
    if data.get("catalog_id") != requested:
        raise ValueError("NUTRITION_CATALOG_VERSION_UNSUPPORTED")
    data["_verified_content_sha256"] = expected
    return data, {str(row["fdc_id"]): row for row in data.get("foods", [])}


def _pose_summary(raw):
    """Validate an untrusted client report; this engine does not attest inference."""
    if not isinstance(raw, dict):
        raise ValueError("INVALID_POSE_SUMMARY")
    model = raw.get("model")
    expected = "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a"
    if not isinstance(model, dict) or model.get("model_sha256") != expected or model.get("runtime") != "0.10.21":
        raise ValueError("UNSUPPORTED_POSE_MODEL")
    source_hash = raw.get("source_sha256")
    source_kind = raw.get("source", "USER_SELECTED_VIDEO_UNVERIFIED")
    if source_kind not in {"USER_SELECTED_VIDEO_UNVERIFIED", "USER_CAMERA_UNVERIFIED"}:
        raise ValueError("INVALID_POSE_SOURCE_KIND")
    if source_kind == "USER_CAMERA_UNVERIFIED" and source_hash is not None:
        raise ValueError("CAMERA_SOURCE_FILE_HASH_MUST_BE_UNKNOWN")
    if source_kind != "USER_CAMERA_UNVERIFIED" and (not isinstance(source_hash, str) or len(source_hash) != 64 or any(c not in "0123456789abcdef" for c in source_hash)):
        raise ValueError("INVALID_POSE_SOURCE_HASH")
    if raw.get("projection") != "IMAGE_PLANE_2D" or raw.get("joint") not in {"left_elbow", "right_elbow", "left_knee", "right_knee"}:
        raise ValueError("INVALID_POSE_PROJECTION_OR_JOINT")
    counts = {key: _number(raw.get(key), key, 0, 180, integral=True) for key in ("frames", "valid_angle_frames", "missing_angle_frames")}
    if counts["frames"] < 1 or counts["valid_angle_frames"] + counts["missing_angle_frames"] != counts["frames"]:
        raise ValueError("INCONSISTENT_POSE_FRAME_COUNTS")
    minimum = _number(raw.get("angle_min_degrees"), "angle_min_degrees", 0, 180, optional=True)
    maximum = _number(raw.get("angle_max_degrees"), "angle_max_degrees", 0, 180, optional=True)
    if counts["valid_angle_frames"] == 0:
        if minimum is not None or maximum is not None:
            raise ValueError("POSE_ANGLE_WITHOUT_VALID_FRAMES")
    elif minimum is None or maximum is None or minimum > maximum:
        raise ValueError("INVALID_POSE_ANGLE_RANGE")
    limits = raw.get("cycle_limits")
    observed = _number(raw.get("observed_complete_cycles"), "observed_complete_cycles", 0, 1000, integral=True, optional=True)
    cycles = _number(raw.get("cycles"), "cycles", 0, 1000, integral=True, optional=True)
    if limits is not None:
        if not isinstance(limits, dict): raise ValueError("INVALID_POSE_CYCLE_LIMITS")
        limits = {key: _number(limits.get(key), "cycle_" + key, 0, 180) for key in ("low", "high")}
        if limits["low"] >= limits["high"]: raise ValueError("INVALID_POSE_CYCLE_LIMITS")
    if (not counts["valid_angle_frames"] or limits is None) and (cycles is not None or observed is not None):
        raise ValueError("POSE_CYCLES_WITHOUT_ELIGIBLE_TRACKING")
    if counts["missing_angle_frames"] and cycles is not None:
        raise ValueError("POSE_COMPLETE_COUNT_WITH_TRACKING_GAPS")
    if observed is not None and observed > max(0, (counts["valid_angle_frames"] - 1) // 2):
        raise ValueError("POSE_CYCLES_EXCEED_VALID_SAMPLE_BOUND")
    if cycles is not None and cycles != observed:
        raise ValueError("POSE_CYCLE_COUNT_DISAGREEMENT")
    state = "DISABLED" if limits is None else "INSUFFICIENT_TRACKING" if not counts["valid_angle_frames"] else "PARTIAL_TRACKING" if counts["missing_angle_frames"] else "MODEL_ESTIMATE"
    return {"source": "CLIENT_REPORTED_POSE_ESTIMATE", "source_sha256": source_hash, "source_kind": source_kind,
            "capture_started_at": _time(raw["capture_started_at"]) if source_kind == "USER_CAMERA_UNVERIFIED" and raw.get("capture_started_at") else None,
            "model_sha256": expected, "runtime": "0.10.21", "projection": "IMAGE_PLANE_2D", "joint": raw["joint"],
            "analyzed_at": _time(raw.get("analyzed_at")), "source_recorded_at": None,
            **counts, "angle_min_degrees": minimum, "angle_max_degrees": maximum,
            "cycles": cycles, "observed_complete_cycles": observed, "cycle_limits": limits, "cycle_status": state,
            "runtime_execution_verified": False, "subject_identity_verified": False,
            "temporal_correspondence_verified": False, "sensor_verified": False,
            "clinical_interpretation": "NOT_PROVIDED", "clinical_execution": "BLOCKED"}


def _training_session(raw, occurred_at):
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("INVALID_TRAINING_SESSION")
    session_id = raw.get("session_id")
    title = raw.get("title")
    kind = raw.get("workout_type")
    state = raw.get("status")
    started = _time(raw.get("started_at"))
    ended = _time(raw.get("updated_at", occurred_at))
    if not isinstance(session_id, str) or not 1 <= len(session_id) <= 100:
        raise ValueError("INVALID_TRAINING_SESSION_ID")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError("INVALID_TRAINING_SESSION_TITLE")
    if kind not in {"RESISTANCE", "AEROBIC", "MOBILITY", "BALANCE"}:
        raise ValueError("INVALID_TRAINING_SESSION_TYPE")
    if state not in {"IN_PROGRESS", "PAUSED", "STOPPED", "COMPLETED"}:
        raise ValueError("INVALID_TRAINING_SESSION_STATUS")
    if datetime.fromisoformat(ended) < datetime.fromisoformat(started):
        raise ValueError("TRAINING_SESSION_TIME_ORDER")
    activities = raw.get("activities")
    if not isinstance(activities, list) or len(activities) > 20:
        raise ValueError("INVALID_TRAINING_ACTIVITIES")
    normalized = []
    for activity in activities:
        if not isinstance(activity, dict):
            raise ValueError("INVALID_TRAINING_ACTIVITY")
        activity_id = activity.get("exercise_id")
        if not isinstance(activity_id, str) or not 1 <= len(activity_id) <= 80:
            raise ValueError("INVALID_TRAINING_EXERCISE_ID")
        normalized.append({
            "exercise_id": activity_id,
            "sets_completed": _number(activity.get("sets_completed", 0), "sets_completed", 0, 30, integral=True),
            "repetitions": _number(activity.get("repetitions", 0), "repetitions", 0, 1000, integral=True),
            "duration_seconds": _number(activity.get("duration_seconds", 0), "duration_seconds", 0, 86400, integral=True),
            "workload_note": str(activity.get("workload_note", ""))[:80],
        })
    plan_id = raw.get("plan_id")
    if plan_id is not None and (not isinstance(plan_id, str) or len(plan_id) > 100):
        raise ValueError("INVALID_TRAINING_PLAN_ID")
    segment_started = raw.get("segment_started_at")
    current_index = _number(raw.get("current_activity_index", 0), "current_activity_index", 0, 20, integral=True)
    result = {"session_id": session_id, "plan_id": plan_id, "title": title.strip(), "workout_type": kind, "status": state,
            "started_at": started, "updated_at": ended,
            "segment_started_at": _time(segment_started) if segment_started else None,
            "current_activity_index": current_index,
            "elapsed_seconds": _number(raw.get("elapsed_seconds", 0), "elapsed_seconds", 0, 86400, integral=True),
            "activities": normalized, "guidance_scope": "GENERIC_EDUCATIONAL_EXAMPLE_NOT_PERSONALIZED_OR_MISSION_PRESCRIPTION"}
    if raw.get("motion_summary") is not None:
        result["motion_summary"] = _pose_summary(raw["motion_summary"])
    return result


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
    synthetic = raw.get("synthetic_fixture", False)
    if type(synthetic) is not bool:
        raise ValueError("INVALID_SYNTHETIC_FIXTURE_FLAG")
    output = {"subject_id": subject_id, "entry_type": kind, "occurred_at": _time(raw.get("occurred_at")),
              "label": label.strip(), "note": note.strip(), "source": "SYNTHETIC_FIXTURE" if synthetic else "SELF_REPORTED",
              "synthetic_data": synthetic, "sensor_verified": False,
              "clinical_interpretation": "NOT_PROVIDED", "clinical_execution": "BLOCKED"}
    if kind == "EXERCISE_SESSION":
        output["duration_minutes"] = _number(raw.get("duration_minutes"), "duration_minutes", 1, 1440, integral=True)
        output["perceived_exertion_0_10"] = _number(raw.get("perceived_exertion_0_10"), "perceived_exertion_0_10", 0, 10, optional=True)
        workout_type = raw.get("workout_type", "USER_REPORTED")
        output["workout_type"] = workout_type if isinstance(workout_type, str) and workout_type in {"USER_REPORTED", "RESISTANCE", "AEROBIC", "MOBILITY", "BALANCE", "OTHER"} else "OTHER"
        if raw.get("training_session") is not None:
            output["training_session"] = _training_session(raw["training_session"], output["occurred_at"])
    elif kind == "HYDRATION":
        output["amount_ml"] = _number(raw.get("amount_ml"), "amount_ml", 1, 100000)
        output["amount_source"] = "USER_ENTERED_NO_COMPOSITION_OR_CLINICAL_TARGET"
    elif kind == "SLEEP":
        output["duration_minutes"] = _number(raw.get("duration_minutes"), "duration_minutes", 1, 1440, integral=True)
        output["subjective_quality_1_5"] = _number(raw.get("subjective_quality_1_5"), "subjective_quality_1_5", 1, 5, integral=True, optional=True)
        output["fatigue_rating_0_10"] = _number(raw.get("fatigue_rating_0_10"), "fatigue_rating_0_10", 0, 10, integral=True, optional=True)
        if raw.get("sleep_start") is not None or raw.get("sleep_end") is not None:
            start, end = _time(raw.get("sleep_start")), _time(raw.get("sleep_end"))
            elapsed = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 60
            if elapsed <= 0 or elapsed > 1440 or round(elapsed) != output["duration_minutes"]:
                raise ValueError("SLEEP_INTERVAL_DURATION_MISMATCH")
            output["sleep_start"], output["sleep_end"] = start, end
    elif kind == "WELLBEING":
        output["mood_rating_1_5"] = _number(raw.get("mood_rating_1_5"), "mood_rating_1_5", 1, 5, integral=True, optional=True)
        output["stress_rating_1_5"] = _number(raw.get("stress_rating_1_5"), "stress_rating_1_5", 1, 5, integral=True, optional=True)
        if output["mood_rating_1_5"] is None and output["stress_rating_1_5"] is None and not output["note"]:
            raise ValueError("WELLBEING_ENTRY_EMPTY")
        output["interpretation"] = "VOLUNTARY_SELF_RATING_NO_SCREENING_OR_DIAGNOSIS"
    elif kind == "MEAL_NOTE":
        if raw.get("food_id") is not None:
            food_id = str(raw.get("food_id"))
            catalog_id = raw.get("nutrition_catalog_id")
            if catalog_id is not None and not isinstance(catalog_id, str):
                raise ValueError("NUTRITION_CATALOG_VERSION_UNSUPPORTED")
            data, foods = _food_catalog(catalog_id)
            food = foods.get(food_id)
            if food is None:
                raise ValueError("UNKNOWN_USDA_FDC_FOOD_ID")
            quantity_g = _number(raw.get("quantity_g"), "quantity_g", 0.1, 5000)
            scale = quantity_g / 100
            energy_basis = raw.get("energy_basis", "DECLARED_1008")
            if not isinstance(energy_basis, str) or energy_basis not in {"DECLARED_1008", "ATWATER_GENERAL_2047", "ATWATER_SPECIFIC_2048"}:
                raise ValueError("INVALID_USDA_ENERGY_BASIS")
            references = food.get("energy_references_kcal_per_100g", {"DECLARED_1008": food["per_100g"].get("energy_kcal"), "ATWATER_GENERAL_2047": None, "ATWATER_SPECIFIC_2048": None})
            composition = {**food["per_100g"], "energy_kcal": references[energy_basis]}
            output.update({"food_id": food_id, "food_name": food["description"], "quantity_g": quantity_g,
                           "nutrient_estimate": {key: None if value is None else round(value * scale, 3)
                                                  for key, value in composition.items()},
                           "energy_reference_estimates_kcal": {key: None if value is None else round(value * scale, 3) for key, value in references.items()},
                           "nutrition_reference": {"catalog_id": data["catalog_id"], "catalog_content_sha256": data["_verified_content_sha256"], "energy_basis": energy_basis, "source_url": data["source_url"],
                                                   "source_archive_sha256": data["source_archive_sha256"],
                                                   "basis": "USDA composition per 100 g scaled by user-entered portion; estimate, not measurement"}})
            if not output["label"]:
                output["label"] = food["description"]
        if not output["label"] and not output["note"]:
            raise ValueError("MEAL_NOTE_EMPTY")
    return output
