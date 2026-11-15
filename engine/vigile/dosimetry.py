"""Conservative unit handling for personal radiation records.

This module stores observations and computes only same-quantity unit conversions,
counter deltas, and explicitly requested dose-rate trapezoids. It does not assess
health risk, establish effective dose from a personal dosimeter, or authorize action.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import math

UNITS = {
    "ABSORBED_DOSE": {"Gy": Decimal("1"), "mGy": Decimal("0.001"), "uGy": Decimal("0.000001"), "rad": Decimal("0.01")},
    "CUMULATIVE_ABSORBED_DOSE": {"Gy": Decimal("1"), "mGy": Decimal("0.001"), "uGy": Decimal("0.000001"), "rad": Decimal("0.01")},
    "ABSORBED_DOSE_RATE": {"Gy/h": Decimal("1"), "mGy/h": Decimal("0.001"), "uGy/h": Decimal("0.000001"), "rad/h": Decimal("0.01")},
    "DOSE_EQUIVALENT": {"Sv": Decimal("1"), "mSv": Decimal("0.001"), "uSv": Decimal("0.000001"), "rem": Decimal("0.01")},
    "DOSE_EQUIVALENT_RATE": {"Sv/h": Decimal("1"), "mSv/h": Decimal("0.001"), "uSv/h": Decimal("0.000001"), "rem/h": Decimal("0.01")},
    "EFFECTIVE_DOSE": {"Sv": Decimal("1"), "mSv": Decimal("0.001"), "uSv": Decimal("0.000001"), "rem": Decimal("0.01")},
}
MODES = {"MEASURED", "MODELLED", "SYNTHETIC"}
QUALITIES = {"VALID", "UNKNOWN", "INVALID"}
MAX_NOTE = 1200


def _text(value, name, maximum=160):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError("INVALID_" + name.upper())
    return value.strip()


def _decimal(value, name):
    if isinstance(value, bool):
        raise ValueError("INVALID_" + name.upper())
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("INVALID_" + name.upper()) from None
    if not result.is_finite() or result < 0:
        raise ValueError("INVALID_" + name.upper())
    return result


def normalize_record(raw, subject_id):
    if not isinstance(raw, dict):
        raise ValueError("RADIATION_RECORD_OBJECT_REQUIRED")
    kind = raw.get("quantity_kind")
    if not isinstance(kind, str) or kind not in UNITS:
        raise ValueError("UNSUPPORTED_RADIATION_QUANTITY")
    unit = raw.get("unit")
    if not isinstance(unit, str) or unit not in UNITS[kind]:
        raise ValueError("RADIATION_UNIT_KIND_MISMATCH")
    value = _decimal(raw.get("value"), "value")
    mode = raw.get("mode")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError("INVALID_RADIATION_MODE")
    quality = raw.get("quality", "UNKNOWN")
    if not isinstance(quality, str) or quality not in QUALITIES:
        raise ValueError("INVALID_RADIATION_QUALITY")
    try:
        timestamp = datetime.fromisoformat(str(raw.get("timestamp", "")).replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("INVALID_RADIATION_TIMESTAMP") from None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("RADIATION_TIMESTAMP_REQUIRES_TIMEZONE")
    segment = _text(raw.get("mission_segment"), "mission_segment")
    location = _text(raw.get("location"), "location")
    source = _text(raw.get("source"), "source", 240)
    instrument = raw.get("instrument_id")
    if instrument is not None:
        instrument = _text(instrument, "instrument_id")
    model = raw.get("model")
    if mode == "MODELLED":
        if not isinstance(model, dict):
            raise ValueError("MODEL_PROVENANCE_REQUIRED")
        model = {"name": _text(model.get("name"), "model_name"), "version": _text(model.get("version"), "model_version")}
    else:
        model = None
    uncertainty = raw.get("uncertainty")
    if uncertainty is not None:
        if not isinstance(uncertainty, dict) or uncertainty.get("unit") != unit:
            raise ValueError("UNCERTAINTY_MUST_USE_RECORDED_QUANTITY_UNIT")
        uncertainty = {"value": float(_decimal(uncertainty.get("value"), "uncertainty")), "unit": unit}
    note = raw.get("note", "")
    if not isinstance(note, str) or len(note) > MAX_NOTE:
        raise ValueError("RADIATION_NOTE_BOUNDS")
    return {
        "subject_id": subject_id,
        "quantity_kind": kind,
        "value": float(value),
        "unit": unit,
        "canonical_value": float(value * UNITS[kind][unit]),
        "canonical_unit": "Gy" if kind in {"ABSORBED_DOSE", "CUMULATIVE_ABSORBED_DOSE"} else "Gy/h" if kind == "ABSORBED_DOSE_RATE" else "Sv/h" if kind == "DOSE_EQUIVALENT_RATE" else "Sv",
        "timestamp": timestamp.isoformat(),
        "mode": mode,
        "quality": quality,
        "mission_segment": segment,
        "location": location,
        "instrument_id": instrument,
        "source": source,
        "model": model,
        "uncertainty": uncertainty,
        "note": note.strip(),
        "sensor_verified": False,
        "clinical_interpretation": "NOT_PROVIDED",
    }


def integrate_rate(records, max_gap_seconds):
    """Integrate adjacent valid readings only; linear-between-samples is explicit."""
    if isinstance(max_gap_seconds, bool) or not isinstance(max_gap_seconds, (int, float)) or not math.isfinite(max_gap_seconds) or max_gap_seconds <= 0:
        raise ValueError("EXPLICIT_POSITIVE_MAX_GAP_REQUIRED")
    if not records:
        return {"intervals": [], "gaps": [], "total": None, "status": "INSUFFICIENT_DATA"}
    kinds = {r["quantity_kind"] for r in records}
    if len(kinds) != 1 or next(iter(kinds)) not in {"ABSORBED_DOSE_RATE", "DOSE_EQUIVALENT_RATE"}:
        raise ValueError("RATE_INTEGRATION_REQUIRES_ONE_RATE_QUANTITY")
    kind = next(iter(kinds))
    rate_dimension = kind
    rows = sorted(records, key=lambda r: datetime.fromisoformat(r["timestamp"]))
    seen = set()
    for row in rows:
        if row["quantity_kind"] != rate_dimension or row["mode"] == "SYNTHETIC" or row["quality"] != "VALID":
            continue
        marker = (row.get("instrument_id"), row["mission_segment"], row["location"], row["timestamp"])
        if marker in seen:
            raise ValueError("DUPLICATE_RATE_OBSERVATION")
        seen.add(marker)
    intervals, gaps = [], []
    for left, right in zip(rows, rows[1:]):
        a = datetime.fromisoformat(left["timestamp"])
        b = datetime.fromisoformat(right["timestamp"])
        seconds = (b - a).total_seconds()
        compatible = (left.get("instrument_id") and left.get("instrument_id") == right.get("instrument_id")
                      and left.get("mission_segment") == right.get("mission_segment")
                      and left.get("location") == right.get("location")
                      and left.get("quantity_kind") == right.get("quantity_kind")
                      and left.get("mode") == right.get("mode") == "MEASURED"
                      and left.get("quality") == right.get("quality") == "VALID")
        if seconds <= 0:
            gaps.append({"from": left["timestamp"], "to": right["timestamp"], "reason": "DUPLICATE_OR_REVERSED_TIME"})
        elif not compatible:
            gaps.append({"from": left["timestamp"], "to": right["timestamp"], "reason": "SOURCE_CONTEXT_OR_QUALITY_CHANGED"})
        elif seconds > max_gap_seconds:
            gaps.append({"from": left["timestamp"], "to": right["timestamp"], "reason": "INTERVAL_EXCEEDS_USER_MAX_GAP"})
        else:
            amount = (Decimal(str(left["canonical_value"])) + Decimal(str(right["canonical_value"]))) * Decimal(str(seconds)) / Decimal("7200")
            unit = "Gy" if kind == "ABSORBED_DOSE_RATE" else "Sv"
            intervals.append({"from": left["timestamp"], "to": right["timestamp"], "seconds": seconds, "value": float(amount), "unit": unit,
                              "method": "TRAPEZOID_LINEAR_INTERPOLATION_ASSUMED"})
    if not intervals:
        return {"intervals": [], "gaps": gaps, "total": None, "status": "NO_CONTIGUOUS_VALID_INTERVAL"}
    unit = intervals[0]["unit"]
    total = sum((Decimal(str(row["value"])) for row in intervals), Decimal("0"))
    return {"intervals": intervals, "gaps": gaps, "total": {"value": float(total), "unit": unit},
            "status": "PARTIAL_INTERVAL_SUM_WITH_GAPS" if gaps else "INTEGRATED_VALID_INTERVALS"}


def cumulative_counter_segments(records):
    rows = [r for r in records if r["quantity_kind"] == "CUMULATIVE_ABSORBED_DOSE" and r["mode"] == "MEASURED" and r["quality"] == "VALID"]
    rows.sort(key=lambda r: (r.get("instrument_id") or "", r["mission_segment"], datetime.fromisoformat(r["timestamp"])))
    deltas, resets, duplicates = [], [], []
    seen = set()
    previous = {}
    for row in rows:
        key = (row.get("instrument_id"), row["mission_segment"], row["location"])
        marker = (key, row["timestamp"])
        if marker in seen:
            duplicates.append({"id": row.get("id"), "timestamp": row["timestamp"]})
            continue
        seen.add(marker)
        value = Decimal(str(row["canonical_value"]))
        old = previous.get(key)
        if old and datetime.fromisoformat(row["timestamp"]) > datetime.fromisoformat(old["timestamp"]):
            before = Decimal(str(old["canonical_value"]))
            if value < before:
                resets.append({"instrument_id": key[0], "mission_segment": key[1], "from": old["timestamp"], "to": row["timestamp"], "reason": "COUNTER_RESET_OR_ROLLOVER_NO_DELTA_ASSIGNED"})
            else:
                deltas.append({"instrument_id": key[0], "mission_segment": key[1], "from": old["timestamp"], "to": row["timestamp"], "value": float(value-before), "unit": "Gy"})
        previous[key] = row
    return {"interval_deltas": deltas, "resets": resets, "duplicates": duplicates,
            "status": "REVIEW_COUNTER_RESETS" if resets else "VALID_INTERVAL_DELTAS" if deltas else "INSUFFICIENT_DATA"}
