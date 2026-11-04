"""Experimental longitudinal orchestration contracts, without therapy authority."""
from typing import Literal
from pydantic import StrictInt, Field, AwareDatetime, FiniteFloat, JsonValue, model_validator
from .models import Model,Id,Measurement
from .clinical_models import ClinicalObservation
from .clinical_contracts import ClinicalEvaluationResponse,Urgency

class MonitoringRequest(Model):
    id: Id
    subject_id: Id
    mission_id: Id
    previous_run_id: Id | None = None
    resource_policy: Literal['DECLARED_R2','MISSION_INVENTORY'] = 'DECLARED_R2'
    as_of: AwareDatetime
    history_start: AwareDatetime
    clinical_window_start: AwareDatetime
    clinical_context_id: Id
    policy_reference: str = Field(min_length=1,max_length=200)
    population: Literal['ADULT','NONPREGNANT_ADULT','UNKNOWN'] = 'UNKNOWN'
    age_years: StrictInt | None = Field(default=None,ge=0)
    measurements: list[Measurement] = Field(default_factory=list,max_length=256)
    observations: list[ClinicalObservation] = Field(default_factory=list,max_length=256)
    sample_ids: dict[Id,Id] = Field(default_factory=dict,max_length=256)
    baseline_ids: list[Id] = Field(default_factory=list,max_length=32)
    followup_at: AwareDatetime | None = None
    ewma_lambda: FiniteFloat = Field(default=1,gt=0,le=1)
    cusum_allowance: FiniteFloat = Field(default=0,ge=0)
    @model_validator(mode='after')
    def coherent(self):
        if not self.history_start<=self.clinical_window_start<=self.as_of:raise ValueError('INVALID_MONITORING_WINDOW')
        if self.followup_at and self.followup_at<self.as_of:raise ValueError('FOLLOWUP_BEFORE_EVALUATION')
        if len({m.id for m in self.measurements})!=len(self.measurements):raise ValueError('DUPLICATE_MEASUREMENT')
        if len(set(self.baseline_ids))!=len(self.baseline_ids):raise ValueError('DUPLICATE_BASELINE')
        if any((m.subject_id,m.mission_id)!=(self.subject_id,self.mission_id) for m in self.measurements):raise ValueError('MONITORING_MEASUREMENT_SCOPE')
        if len({o.id for o in self.observations})!=len(self.observations):raise ValueError('DUPLICATE_OBSERVATION')
        if set(self.sample_ids)-{m.id for m in self.measurements}:raise ValueError('SAMPLE_MAPPING_REQUIRES_CURRENT_MEASUREMENT')
        return self

class IndicatorResult(Model):
    variable: str
    unit: str
    state: str
    latest_measurement_id: str | None = None
    value: float | None = None
    valid_count: int = 0
    quality_issues: list[dict[str,JsonValue]] = Field(default_factory=list)
    baseline_comparison: dict[str,JsonValue] | None = None
    trend: dict[str,JsonValue] | None = None
    normative_finding_id: str | None = None
    source_ids: list[str]
    limitations: list[str]

class DomainResult(Model):
    domain: str
    available_indicators: list[str]
    missing_indicators: list[str]
    indicators: list[IndicatorResult]
    source_ids: list[str]
    method: str
    phase: str
    gravity: str
    applicability: str
    limitations: list[str]
    accumulated_dose: dict[str,JsonValue] | None = None

class MonitoringEvent(Model):
    id: str
    key: str
    kind: Literal['CLINICAL_CRITERIA','NORMATIVE_REQUIREMENT','DATA_QUALITY','DESCRIPTIVE_CHANGE']
    state: str
    urgency: Urgency
    notify: bool
    reason: str
    evidence_ids: list[str]
    source_ids: list[str]
    diagnosis: None = None
    clinical_execution: Literal['BLOCKED'] = 'BLOCKED'

class MonitoringResult(Model):
    id: str
    subject_id: str
    mission_id: str
    previous_run_id: str | None
    as_of: str
    mode: Literal['EXPERIMENTAL_NOT_CLINICALLY_VALIDATED']
    domains: list[DomainResult]
    clinical_evaluations: dict[str,ClinicalEvaluationResponse]
    events: list[MonitoringEvent]
    episode_ids: dict[str,str]
    followup_ids: list[str]
    clinical_context_id: str
    event_states: dict[str,dict[str,JsonValue]]
    input_hash: str
    output_hash: str
    implementation_hash: str
    knowledge_hash: str
    policy_reference: str
    clinical_execution: Literal['BLOCKED']
