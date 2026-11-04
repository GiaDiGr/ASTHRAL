"""Typed transport contracts. Client assertions never confer clinical authority."""
from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, FiniteFloat, model_validator, field_validator, StrictBool

Id = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")]

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class MissionContext(Model):
    id: Id
    phase: Literal["PRE_MISSION", "IN_MISSION", "POST_MISSION"]
    gravity: Literal["MICROGRAVITY", "PARTIAL", "EARTH"]
    environment: Literal["HABITABLE_VOLUME", "HABITABLE_CABIN", "FREE_SPACE", "PLANETARY_SURFACE"]
    mode: Literal["NOMINAL", "OFF_NOMINAL"]
    microgravity_eva_planned_or_required: StrictBool | None = None
    extraterrestrial_surface_eva_planned_or_required: StrictBool | None = None
    exposure_context: Literal["INDEFINITE_CABIN", "LIMITED_SPECIAL_OPERATION"] | None = None
    synthetic: StrictBool

class AstronautProfile(Model):
    id: Id
    mission_id: Id
    synthetic: StrictBool

class Device(Model):
    id: Id
    variable: Id
    unit: str
    calibration_id: Id
    calibrated_at: AwareDatetime
    valid_until: AwareDatetime
    technical_min: FiniteFloat
    technical_max: FiniteFloat
    max_age_seconds: Annotated[int, Field(gt=0)]
    policy_reference: Annotated[str, Field(min_length=1)]
    conflict_tolerance: Annotated[FiniteFloat, Field(ge=0)] | None = None
    alignment_seconds: Annotated[int, Field(ge=0)] | None = None
    synthetic: StrictBool

    @model_validator(mode="after")
    def ordered(self):
        if self.valid_until <= self.calibrated_at or self.technical_max <= self.technical_min:
            raise ValueError("Invalid calibration interval or technical range")
        return self

class Measurement(Model):
    id: Id
    subject_id: Id
    mission_id: Id
    variable: Id
    value: FiniteFloat | None
    unit: str
    timestamp: AwareDatetime
    interval_end: AwareDatetime | None = None
    device_id: Id
    calibration_id: Id
    method: Annotated[str, Field(min_length=1)]
    protocol: Id
    site: str | None = None
    compartment: Id | None = None
    phase: Literal["PRE_MISSION", "IN_MISSION", "POST_MISSION"]
    reported_quality: Literal["ACCEPTABLE", "DEGRADED", "INVALID", "UNKNOWN", "NOT_MEASURED"]
    synthetic: StrictBool
    provenance: Annotated[str, Field(min_length=1)]

    @field_validator('value', mode='before')
    @classmethod
    def actual_number(cls, value):
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float))):
            raise ValueError('Measurement must be a JSON number, not a boolean or string')
        return value

    @model_validator(mode="after")
    def interval(self):
        if self.interval_end and self.interval_end <= self.timestamp:
            raise ValueError("Interval end must follow start")
        return self

class EvaluationRequest(Model):
    rule_id: Id
    subject_id: Id
    mission_id: Id
    as_of: AwareDatetime
    bindings: dict[str, Id | dict[str, Id]] = Field(default_factory=dict)
    # Non-numeric contextual inputs only; numeric values must reference stored measurements.
    context: dict[str, str | bool | list[str]] = Field(default_factory=dict)
    co2_measurement_ids: list[Id] = Field(default_factory=list)
    mode: Literal["SIMULATION", "OPERATIONAL"] = "OPERATIONAL"

class BaselineRequest(Model):
    id: Id
    measurement_ids: Annotated[list[Id], Field(min_length=1)]
    minimum_observations: Annotated[int, Field(gt=0)]
    protocol_reference: Annotated[str, Field(min_length=1)]
    as_of: AwareDatetime
    supersedes: Id | None = None
    valid_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def validity(self):
        if self.valid_until and self.valid_until <= self.as_of:
            raise ValueError("Baseline validity must end after calculation time")
        return self

class TrendRequest(Model):
    measurement_ids: Annotated[list[Id], Field(min_length=2)]
    as_of: AwareDatetime
    ewma_lambda: Annotated[FiniteFloat, Field(gt=0, le=1)]
    cusum_target: FiniteFloat
    cusum_allowance: Annotated[FiniteFloat, Field(ge=0)]

    baseline_id: Id | None = None
    max_gap_seconds: Annotated[int, Field(gt=0)] | None = None
    ewma_initial: FiniteFloat | None = None
    cusum_decision_limit: Annotated[FiniteFloat, Field(gt=0)] | None = None
    policy_reference: Annotated[str, Field(min_length=1)] = "RESEARCH_CONFIGURATION_UNVALIDATED"

class EpisodeRequest(Model):
    id: Id
    subject_id: Id
    mission_id: Id
    condition_id: Id
    finding_ids: list[Id] = Field(default_factory=list)

class TransitionRequest(Model):
    target: Literal["FINDING", "ASSESSMENT", "TRIAGE", "AUTHORIZED_ACTION", "RECOVERY", "FOLLOW_UP", "CLOSED"]
    note: Annotated[str, Field(min_length=1)]
    authorization_id: Id | None = None
    expected_state: str | None = None

class ClinicalNote(Model):
    observed_at: AwareDatetime
    id: Id
    episode_id: Id
    kind: Literal["OBSERVATION", "HYPOTHESIS", "DIAGNOSIS"]
    text: Annotated[str, Field(min_length=1)]
    evidence_ids: list[Id] = Field(default_factory=list)

class FollowUpPlan(Model):
    id: Id
    episode_id: Id
    due_at: AwareDatetime
    goal_description: Annotated[str, Field(min_length=1)]
    protocol_reference: Annotated[str, Field(min_length=1)]

class FollowUpReview(Model):
    completed: StrictBool = False
    plan_id: Id
    measurement_ids: list[Id]
    note: Annotated[str, Field(min_length=1)]

class ActionRequest(Model):
    episode_id: Id
    action: str
    authorization_id: Id | None = None

class MultisystemRequest(Model):
    finding_ids: Annotated[list[Id], Field(min_length=2)]
    interaction_id: Id
    max_separation_seconds: Annotated[int, Field(gt=0)]
    policy_reference: Annotated[str, Field(min_length=1)]

class BaselineWithdrawal(Model):
    baseline_id: Id
    effective_at: AwareDatetime
    reason: Annotated[str, Field(min_length=1)]

class QualityRequest(Model):
    measurement_ids: Annotated[list[Id], Field(min_length=1, max_length=1000)]
    as_of: AwareDatetime
    historical: StrictBool = False

class EvidenceRevision(Model):
    source_id: Id
    version: Annotated[str, Field(min_length=1)]
    locator: Annotated[str, Field(min_length=1)]
    document_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    status: Literal["REQUIRES_VALIDATION", "REJECTED", "REVIEWED_METADATA_ONLY"]
    note: Annotated[str, Field(min_length=1)]
    supersedes: Id | None = None

class EpisodeAttachment(Model):
    finding_ids: Annotated[list[Id], Field(min_length=1)]

class ResourceAssessment(Model):
    mode: Literal["FULL", "LOW_POWER", "EMERGENCY_POWER"]
    proposed_interval_seconds: Annotated[int, Field(gt=0)]
    required_interval_seconds: Annotated[int, Field(gt=0)]
    policy_reference: Annotated[str, Field(min_length=1)]
    measurement_ids: Annotated[list[Id], Field(min_length=1, max_length=1000)]
    as_of: AwareDatetime
