from decimal import Decimal
from math import isfinite
from .models import Measurement, Device

class Inconclusive(ValueError):
    pass

# Exact declared conversion factors; never cross dose semantics or turn a rate into a dose.
UNITS = {
    "copies/mL": ("viral_copies_per_ml", "1"), "1": ("dimensionless", "1"),
    # CLINICAL_UNITS_IDENTITY: no generic mass-to-molar conversion across analytes.
    "mg/dL": ("mass_concentration_mg_dl", "1"), "mmol/L": ("molar_concentration_mmol_l", "1"),
    "pH": ("ph_scale", "1"), "mL/kg/h": ("mass_normalized_urine_rate", "1"), "+": ("urine_ketone_ordinal", "1"),
    "kPa": ("pressure", "1"), "Pa": ("pressure", "0.001"),
    "mmHg": ("pressure", "0.133322387415"), "psi": ("pressure", "6.894757293168"),
    "mSv": ("effective_dose", "1"), "Sv": ("effective_dose", "1000"),
    "mGy": ("absorbed_dose", "1"), "Gy": ("absorbed_dose", "1000"),
    "mGy-Eq": ("organ_equivalent", "1"), "mSv/day": ("effective_rate", "1"),
    "psi/min": ("pressure_rate", "1"), "mL/min/kg": ("relative_vo2", "1"),
    "N": ("force", "1"), "kgf": ("force", "9.80665"),
    "kg_equivalent": ("test_load", "1"), "kg": ("mass", "1"),
    "g/cm2": ("areal_bmd", "1"), "%": ("percent", "1"),
    "day": ("time_day", "1"), "mission-year": ("mission_year", "1"),
    "kcal": ("energy", "1"), "g": ("nutrient_mass", "1"),
    "h": ("time", "3600"), "min": ("time", "60"), "s": ("time", "1"),
    "bpm": ("heart_rate", "1"), "ms": ("time", "0.001"),
    "g/cm²": ("areal_bmd", "1"), "mV": ("voltage", "1"),
    "mL/L": ("volume_fraction_per_mille", "1"), "mL": ("volume", "1"), "L": ("volume", "1000"),
    "um": ("length", "1"), "μm": ("length", "1"), "mm": ("length", "1000"),
    "degC": ("temperature_celsius", "1"), "°C": ("temperature_celsius", "1"),
    "cm/s": ("velocity", "1"), "m/s": ("velocity", "100"),
    "dBA": ("log_sound_level_a_weighted", "1")
}

def convert(value, source, target):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not isfinite(value):
        raise Inconclusive("INVALID_NUMERIC_INPUT")
    if source not in UNITS or target not in UNITS or UNITS[source][0] != UNITS[target][0]:
        raise Inconclusive("DIMENSIONAL_MISMATCH")
    converted=float(Decimal(str(value)) * Decimal(UNITS[source][1]) / Decimal(UNITS[target][1]))
    if not isfinite(converted): raise Inconclusive("NUMERIC_OVERFLOW")
    return converted

def assess(m: Measurement, d: Device, as_of, historical=False):
    if m.value is None:
        return "NOT_MEASURED" if m.reported_quality=="NOT_MEASURED" else "MISSING"
    if m.reported_quality != "ACCEPTABLE":
        return m.reported_quality
    if m.timestamp > as_of or (m.interval_end and m.interval_end > as_of):
        return "FUTURE_TIMESTAMP"
    if m.device_id != d.id or m.variable != d.variable or m.synthetic != d.synthetic:
        return "DEVICE_MISMATCH"
    if m.calibration_id != d.calibration_id or not d.calibrated_at <= m.timestamp <= d.valid_until:
        return "INVALID_CALIBRATION"
    if m.interval_end and m.interval_end > d.valid_until:
        return "INVALID_CALIBRATION"
    if not historical and (as_of - (m.interval_end or m.timestamp)).total_seconds() > d.max_age_seconds:
        return "STALE"
    try:
        value = convert(m.value, m.unit, d.unit)
    except Inconclusive:
        return "DIMENSIONAL_MISMATCH"
    if not d.technical_min <= value <= d.technical_max:
        return "OUTSIDE_TECHNICAL_RANGE"
    return "VALID"

def comparable(measurements, include_phase=True):
    if not measurements:
        raise Inconclusive("MISSING_REQUIRED_INPUT")
    keys = ["subject_id", "mission_id", "variable", "method", "protocol", "site", "compartment", "synthetic"]
    if include_phase:
        keys.append("phase")
    first = measurements[0]
    for m in measurements[1:]:
        if any(getattr(m,k) != getattr(first,k) for k in keys):
            raise Inconclusive("NOT_COMPARABLE")
        convert(m.value, m.unit, first.unit)

def sensor_consistency(measurements, tolerance, max_separation_seconds):
    if tolerance < 0 or max_separation_seconds < 0:
        raise ValueError("Invalid technical policy")
    comparable(measurements)
    if (max(m.timestamp for m in measurements) - min(m.timestamp for m in measurements)).total_seconds() > max_separation_seconds:
        raise Inconclusive("TEMPORAL_MISMATCH")
    values = [convert(m.value,m.unit,measurements[0].unit) for m in measurements]
    return "CONFLICTING_DATA" if max(values)-min(values) > tolerance else "CONSISTENT"
