"""Validated, explicitly self-reported prevention and recovery journal entries."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from itertools import combinations
import json
import hashlib
from pathlib import Path

KINDS = {"EXERCISE_SESSION", "HYDRATION", "MEAL_NOTE", "SLEEP", "WELLBEING"}
NEUROGUARD_TASKS = {
    "MOOD_CHECK", "KSS", "FATIGUE_CHECK", "STRESS_CHECK", "NASA_TLX_WEIGHTED",
    "PVT_B_BROWSER_RESEARCH", "SIMPLE_RT_BROWSER_RESEARCH",
    "WORKING_MEMORY_1BACK_BROWSER_RESEARCH", "INHIBITORY_GONOGO_BROWSER_RESEARCH",
}
TLX_DIMENSIONS = ("mental", "physical", "temporal", "performance", "effort", "frustration")
KSS_ANCHORS = {
    1: "EXTREMELY_ALERT", 2: "VERY_ALERT", 3: "ALERT", 4: "RATHER_ALERT",
    5: "NEITHER_ALERT_NOR_SLEEPY", 6: "SOME_SIGNS_OF_SLEEPINESS",
    7: "SLEEPY_NO_EFFORT_TO_KEEP_AWAKE", 8: "SLEEPY_SOME_EFFORT_TO_KEEP_AWAKE",
    9: "VERY_SLEEPY_GREAT_EFFORT_FIGHTING_SLEEP",
}


def _text(value, name, maximum=120, optional=True):
    if value is None and optional:
        return ""
    if not isinstance(value, str) or len(value.strip()) > maximum:
        raise ValueError("INVALID_" + name.upper())
    return value.strip()


def _normalize_neuroguard(raw):
    """Validate user-selected research/self-report records; never emits a diagnosis."""
    if not isinstance(raw, dict):
        raise ValueError("INVALID_NEUROGUARD_RECORD")
    task = raw.get("task")
    if not isinstance(task, str) or task not in NEUROGUARD_TASKS:
        raise ValueError("UNSUPPORTED_NEUROGUARD_TASK")
    if raw.get("consent_given") is not True or raw.get("consent_version") != "ASTHRAL_NEUROGUARD_CONSENT_1":
        raise ValueError("NEUROGUARD_EXPLICIT_CONSENT_REQUIRED")
    result = {
        "task": task,
        "schema_version": "NEUROGUARD_RECORD_1",
        "consent_given": True,
        "consent_version": "ASTHRAL_NEUROGUARD_CONSENT_1",
        "consented_at": _time(raw.get("consented_at")),
        "task_context": _text(raw.get("task_context"), "task_context"),
        "source": "VOLUNTARY_SELF_REPORT_OR_BROWSER_TASK",
        "clinical_interpretation": "NOT_PROVIDED",
        "clinical_execution": "BLOCKED",
    }

    if task == "MOOD_CHECK":
        values = ("mood_0_10", "energy_0_10", "tension_0_10", "wellbeing_0_10")
        result.update({name: _number(raw.get(name), name, 0, 10, integral=True) for name in values})
        result["scale"] = "ASTHRAL_EXPERIMENTAL_SELF_REPORT_0_10"
    elif task == "KSS":
        score = _number(raw.get("score"), "kss_score", 1, 9, integral=True)
        result.update({"score": score, "anchor": KSS_ANCHORS[score], "scale": "KSS_9_POINT",
                       "recall_period": "PREVIOUS_5_MINUTES"})
    elif task == "FATIGUE_CHECK":
        result.update({name: _number(raw.get(name), name, 0, 10, integral=True)
                       for name in ("mental_fatigue_0_10", "physical_fatigue_0_10")})
        result["scale"] = "ASTHRAL_EXPERIMENTAL_SELF_REPORT_0_10"
        sleep_id = raw.get("linked_sleep_entry_id")
        if sleep_id is not None:
            if not isinstance(sleep_id, str) or not 1 <= len(sleep_id) <= 100:
                raise ValueError("INVALID_LINKED_SLEEP_ENTRY_ID")
            result["linked_sleep_entry_id"] = sleep_id
    elif task == "STRESS_CHECK":
        result.update({"stress_0_10": _number(raw.get("stress_0_10"), "stress_0_10", 0, 10, integral=True),
                       "scale": "ASTHRAL_EXPERIMENTAL_SELF_REPORT_0_10"})
    elif task == "NASA_TLX_WEIGHTED":
        ratings = raw.get("ratings")
        choices = raw.get("pairwise_choices")
        if not isinstance(ratings, dict) or set(ratings) != set(TLX_DIMENSIONS):
            raise ValueError("INVALID_TLX_DIMENSIONS")
        clean_ratings = {key: _number(ratings[key], "tlx_rating", 0, 100, integral=True) for key in TLX_DIMENSIONS}
        if any(value % 5 for value in clean_ratings.values()):
            raise ValueError("INVALID_TLX_RATING_INCREMENT")
        valid_pairs = {frozenset(pair) for pair in combinations(TLX_DIMENSIONS, 2)}
        if not isinstance(choices, list) or len(choices) != 15:
            raise ValueError("INVALID_TLX_PAIRWISE_CHOICES")
        seen, weights, clean_choices = set(), {key: 0 for key in TLX_DIMENSIONS}, []
        for choice in choices:
            if not isinstance(choice, dict):
                raise ValueError("INVALID_TLX_PAIRWISE_CHOICE")
            left, right, selected = choice.get("factor_a"), choice.get("factor_b"), choice.get("selected")
            if not all(isinstance(value, str) for value in (left, right, selected)):
                raise ValueError("INVALID_TLX_PAIRWISE_CHOICE")
            pair = frozenset((left, right)) if left != right else frozenset()
            if pair not in valid_pairs or pair in seen or selected not in pair:
                raise ValueError("INVALID_TLX_PAIRWISE_CHOICE")
            seen.add(pair)
            weights[selected] += 1
            clean_choices.append({"factor_a": left, "factor_b": right, "selected": selected})
        if seen != valid_pairs or sum(weights.values()) != 15:
            raise ValueError("INVALID_TLX_PAIRWISE_CHOICES")
        weighted = sum(clean_ratings[key] * weights[key] for key in TLX_DIMENSIONS) / 15
        result.update({"ratings": clean_ratings, "pairwise_choices": clean_choices, "weights": weights,
                       "weighted_score": round(weighted, 2),
                       "unweighted_descriptive_mean": round(sum(clean_ratings.values()) / 6, 2),
                       "scoring": "NASA_TLX_ORIGINAL_15_PAIRWISE_WEIGHTED",
                       "scale": "NASA_TLX_0_100_INCREMENTS_OF_5"})
    elif task in {"PVT_B_BROWSER_RESEARCH", "SIMPLE_RT_BROWSER_RESEARCH"}:
        trials = raw.get("trials")
        maximum = 200 if task == "PVT_B_BROWSER_RESEARCH" else 30
        minimum = 1 if task == "PVT_B_BROWSER_RESEARCH" else 5
        if not isinstance(trials, list) or not minimum <= len(trials) <= maximum:
            raise ValueError("INVALID_NEUROGUARD_TRIALS")
        elapsed = _number(raw.get("total_elapsed_ms"), "task_elapsed_ms", 1, 210000 if task == "PVT_B_BROWSER_RESEARCH" else 1800000, integral=True)
        if task == "PVT_B_BROWSER_RESEARCH" and elapsed < 180000:
            raise ValueError("INCOMPLETE_PVT_B_DURATION")
        clean, previous_onset = [], -1
        valid_rts, false_starts, timeouts = [], 0, 0
        for row in trials:
            if not isinstance(row, dict):
                raise ValueError("INVALID_NEUROGUARD_TRIAL")
            onset = _number(row.get("stimulus_onset_ms"), "stimulus_onset_ms", 0, elapsed, integral=True)
            interval = _number(row.get("interval_ms"), "stimulus_interval_ms", 1000, 4000, integral=True)
            if onset <= previous_onset:
                raise ValueError("NON_MONOTONIC_NEUROGUARD_TRIALS")
            previous_onset = onset
            response = _number(row.get("response_ms"), "response_ms", 0, 30000, optional=True)
            timed_out = row.get("timed_out", False)
            if type(timed_out) is not bool or (timed_out != (response is None)):
                raise ValueError("INCONSISTENT_NEUROGUARD_RESPONSE")
            if timed_out:
                timeouts += 1
                outcome, effective_rt = "TIMEOUT_LAPSE_30000MS", 30000
            elif response < 100:
                false_starts += 1
                outcome, effective_rt = "FALSE_START_UNDER_100MS", None
            else:
                outcome, effective_rt = "RESPONSE", response
                valid_rts.append(response)
            if task == "SIMPLE_RT_BROWSER_RESEARCH" and not timed_out and response is not None and response < 100:
                # False starts are retained and explicitly marked, never silently discarded.
                pass
            clean.append({"stimulus_onset_ms": onset, "interval_ms": interval, "response_ms": response,
                          "timed_out": timed_out, "outcome": outcome, "effective_rt_ms": effective_rt})
        starts_without_stimulus = raw.get("false_start_events", [])
        if not isinstance(starts_without_stimulus, list) or len(starts_without_stimulus) > 1000:
            raise ValueError("INVALID_FALSE_START_EVENTS")
        false_start_events = []
        for event in starts_without_stimulus:
            if not isinstance(event, dict) or event.get("reason") != "NO_STIMULUS":
                raise ValueError("INVALID_FALSE_START_EVENT")
            event_time = _number(event.get("elapsed_ms"), "false_start_elapsed_ms", 0, elapsed, integral=True)
            false_start_events.append({"elapsed_ms": event_time, "reason": "NO_STIMULUS"})
        if not clean or clean[-1]["stimulus_onset_ms"] > elapsed:
            raise ValueError("INVALID_NEUROGUARD_TRIAL_TIMING")
        median = _median(valid_rts)
        mean = sum(valid_rts) / len(valid_rts) if valid_rts else None
        sd = (sum((x - mean) ** 2 for x in valid_rts) / len(valid_rts)) ** 0.5 if valid_rts else None
        is_pvt_b = task == "PVT_B_BROWSER_RESEARCH"
        result.update({"duration_ms": 180000 if task == "PVT_B_BROWSER_RESEARCH" else None,
                       "total_elapsed_ms": elapsed, "trials": clean,
                       "false_start_events": false_start_events, "valid_response_count": len(valid_rts),
                       "mean_rt_ms": round(mean, 2) if mean is not None else None,
                       "median_rt_ms": median, "sd_rt_ms": round(sd, 2) if sd is not None else None,
                       "lapses_355ms": sum(rt >= 355 for rt in valid_rts) + timeouts if is_pvt_b else None,
                       "lapses_500ms": sum(rt >= 500 for rt in valid_rts) + timeouts if is_pvt_b else None,
                       "anticipations": false_starts + len(false_start_events), "timeouts_30000ms": timeouts,
                       "timing_scope": "BROWSER_INPUT_TIMING_UNCALIBRATED_NOT_EQUIVALENT_TO_NASA_PVT_OR_RST",
                       "protocol_scope": "PVT_B_PARADIGM_INSPIRED_RESEARCH_ONLY" if task == "PVT_B_BROWSER_RESEARCH" else "UNVALIDATED_SIMPLE_RT_BROWSER_TASK"})
    elif task == "WORKING_MEMORY_1BACK_BROWSER_RESEARCH":
        trials = raw.get("trials")
        sequence = raw.get("sequence")
        if not isinstance(sequence, list) or len(sequence) != 20 or any(not isinstance(value, str) or value not in {"A", "B", "C", "D"} for value in sequence):
            raise ValueError("INVALID_1BACK_SEQUENCE")
        if not isinstance(trials, list) or len(trials) != 19:
            raise ValueError("INVALID_1BACK_TRIAL_COUNT")
        clean, correct, rts, previous = [], 0, [], -1
        for index, row in enumerate(trials, start=1):
            if not isinstance(row, dict) or row.get("response") is not None and (not isinstance(row.get("response"), str) or row["response"] not in {"SAME", "DIFFERENT"}):
                raise ValueError("INVALID_1BACK_TRIAL")
            onset = _number(row.get("stimulus_onset_ms"), "stimulus_onset_ms", 0, 1800000, integral=True)
            if onset <= previous:
                raise ValueError("NON_MONOTONIC_NEUROGUARD_TRIALS")
            previous = onset
            if type(row.get("index")) is not int or row.get("index") != index or row.get("stimulus") != sequence[index] or row.get("previous_stimulus") != sequence[index-1]:
                raise ValueError("INCONSISTENT_1BACK_SEQUENCE")
            correct_response = "SAME" if sequence[index] == sequence[index-1] else "DIFFERENT"
            rt = _number(row.get("response_ms"), "response_ms", 0, 30000, optional=True)
            if (row["response"] is None) != (rt is None):
                raise ValueError("INCONSISTENT_1BACK_RESPONSE")
            hit = row["response"] == correct_response
            correct += int(hit)
            if rt is not None:
                rts.append(rt)
            clean.append({"index": index, "stimulus": sequence[index], "previous_stimulus": sequence[index-1],
                          "stimulus_onset_ms": onset, "correct_response": correct_response,
                          "response": row["response"], "response_ms": rt, "correct": hit})
        result.update({"sequence": sequence, "trials": clean, "accuracy_fraction": round(correct / len(clean), 4),
                       "correct_responses": correct, "task_scope": "UNVALIDATED_1_BACK_PRACTICE_TASK",
                       "median_rt_ms": _median(rts)})
    elif task == "INHIBITORY_GONOGO_BROWSER_RESEARCH":
        trials = raw.get("trials")
        if not isinstance(trials, list) or len(trials) != 20:
            raise ValueError("INVALID_GONOGO_TRIAL_COUNT")
        clean, false_alarms, omissions, go_hits, rts, previous = [], 0, 0, 0, [], -1
        for row in trials:
            if not isinstance(row, dict) or type(row.get("no_go")) is not bool or type(row.get("responded")) is not bool:
                raise ValueError("INVALID_GONOGO_TRIAL")
            onset = _number(row.get("stimulus_onset_ms"), "stimulus_onset_ms", 0, 1800000, integral=True)
            if onset <= previous:
                raise ValueError("NON_MONOTONIC_NEUROGUARD_TRIALS")
            previous = onset
            rt = _number(row.get("response_ms"), "response_ms", 0, 30000, optional=True)
            if row["responded"] != (rt is not None):
                raise ValueError("INCONSISTENT_GONOGO_RESPONSE")
            if row["no_go"] and row["responded"]: false_alarms += 1
            if not row["no_go"] and not row["responded"]: omissions += 1
            if not row["no_go"] and row["responded"]: go_hits += 1
            if rt is not None: rts.append(rt)
            clean.append({"stimulus_onset_ms": onset, "no_go": row["no_go"], "responded": row["responded"], "response_ms": rt})
        result.update({"trials": clean, "false_alarms": false_alarms, "go_omissions": omissions,
                       "go_responses": go_hits, "no_go_trials": sum(row["no_go"] for row in clean),
                       "no_go_correct_rejections": sum(row["no_go"] and not row["responded"] for row in clean),
                       "median_rt_ms": _median(rts),
                       "task_scope": "UNVALIDATED_GONOGO_PRACTICE_TASK"})
    return result


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


def _median(values):
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


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
        output["interpretation"] = "VOLUNTARY_SELF_RATING_NO_SCREENING_OR_DIAGNOSIS"
        neuro = raw.get("neuroguard")
        if neuro is not None:
            output["neuroguard"] = _normalize_neuroguard(neuro)
        elif output["mood_rating_1_5"] is None and output["stress_rating_1_5"] is None and not output["note"]:
            raise ValueError("WELLBEING_ENTRY_EMPTY")
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
