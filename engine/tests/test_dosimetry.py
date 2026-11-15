import pytest
from vigile.dosimetry import cumulative_counter_segments, integrate_rate, normalize_record


def record(**updates):
    value={"quantity_kind":"ABSORBED_DOSE","value":3,"unit":"mGy","timestamp":"2026-11-15T10:00:00Z","mode":"MEASURED","quality":"VALID","mission_segment":"transit-1","location":"habitat-A","instrument_id":"manual-unit-1","source":"MANUAL_USER_REPORTED","note":""}
    value.update(updates)
    return normalize_record(value,"synthetic-crew")


def test_absorbed_dose_unit_conversion_stays_within_gy_family():
    row=record()
    assert row["canonical_value"]==pytest.approx(.003)
    assert row["canonical_unit"]=="Gy"
    assert row["sensor_verified"] is False


@pytest.mark.parametrize("kind,unit",[("ABSORBED_DOSE","mSv"),("DOSE_EQUIVALENT","mGy"),("ABSORBED_DOSE_RATE","mSv/h"),("DOSE_EQUIVALENT_RATE","mGy/h")])
def test_incompatible_radiation_unit_families_rejected(kind,unit):
    with pytest.raises(ValueError,match="RADIATION_UNIT_KIND_MISMATCH"):
        record(quantity_kind=kind,unit=unit)


def test_modelled_record_requires_model_name_and_version():
    with pytest.raises(ValueError,match="MODEL_PROVENANCE_REQUIRED"):
        record(mode="MODELLED")
    row=record(mode="MODELLED",model={"name":"synthetic transport model","version":"fixture-1"})
    assert row["model"]["version"]=="fixture-1"
    assert row["sensor_verified"] is False


def test_naive_timestamps_and_invalid_quality_are_not_accepted():
    with pytest.raises(ValueError,match="REQUIRES_TIMEZONE"):
        record(timestamp="2026-11-15T10:00")
    with pytest.raises(ValueError,match="INVALID_RADIATION_QUALITY"):
        record(quality="NORMAL")


def test_dose_rate_integration_needs_explicit_max_gap_and_labels_assumption():
    rows=[record(quantity_kind="ABSORBED_DOSE_RATE",value=1,unit="mGy/h",timestamp="2026-11-15T10:00:00Z"),
          record(quantity_kind="ABSORBED_DOSE_RATE",value=3,unit="mGy/h",timestamp="2026-11-15T11:00:00Z")]
    with pytest.raises(ValueError,match="EXPLICIT_POSITIVE_MAX_GAP_REQUIRED"):
        integrate_rate(rows,None)
    result=integrate_rate(rows,3600)
    assert result["total"]["unit"]=="Gy"
    assert result["total"]["value"]==pytest.approx(.002)
    assert result["intervals"][0]["method"]=="TRAPEZOID_LINEAR_INTERPOLATION_ASSUMED"


def test_rate_integration_reports_gaps_and_never_bridges_them():
    rows=[record(quantity_kind="ABSORBED_DOSE_RATE",value=1,unit="mGy/h",timestamp="2026-11-15T10:00:00Z"),
          record(quantity_kind="ABSORBED_DOSE_RATE",value=3,unit="mGy/h",timestamp="2026-11-15T12:00:00Z")]
    result=integrate_rate(rows,3600)
    assert result["total"] is None
    assert result["status"]=="NO_CONTIGUOUS_VALID_INTERVAL"
    assert result["gaps"][0]["reason"]=="INTERVAL_EXCEEDS_USER_MAX_GAP"


def test_rate_integration_does_not_mix_instruments_locations_or_synthetic_values():
    a=record(quantity_kind="DOSE_EQUIVALENT_RATE",value=1,unit="mSv/h",timestamp="2026-11-15T10:00:00Z",mode="MEASURED")
    b=record(quantity_kind="DOSE_EQUIVALENT_RATE",value=2,unit="mSv/h",timestamp="2026-11-15T10:30:00Z",instrument_id="different-unit")
    c=record(quantity_kind="DOSE_EQUIVALENT_RATE",value=99,unit="mSv/h",timestamp="2026-11-15T11:00:00Z",mode="SYNTHETIC")
    result=integrate_rate([a,b,c],7200)
    assert result["total"] is None
    assert len(result["gaps"])==2


def test_counter_reset_is_reported_without_assigning_negative_delta():
    rows=[record(quantity_kind="CUMULATIVE_ABSORBED_DOSE",value=4,unit="mGy",timestamp="2026-11-15T10:00:00Z"),
          record(quantity_kind="CUMULATIVE_ABSORBED_DOSE",value=1,unit="mGy",timestamp="2026-11-15T11:00:00Z")]
    result=cumulative_counter_segments(rows)
    assert result["interval_deltas"]==[]
    assert result["resets"][0]["reason"]=="COUNTER_RESET_OR_ROLLOVER_NO_DELTA_ASSIGNED"


def test_duplicate_rate_timestamp_is_rejected():
    a=record(quantity_kind="ABSORBED_DOSE_RATE",value=1,unit="mGy/h")
    b=record(quantity_kind="ABSORBED_DOSE_RATE",value=2,unit="mGy/h")
    with pytest.raises(ValueError,match="DUPLICATE_RATE_OBSERVATION"):
        integrate_rate([a,b],60)
