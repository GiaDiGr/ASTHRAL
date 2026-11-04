"""Strict clinical research contracts; no client-owned authorization or execution."""
from typing import Literal
from pydantic import AwareDatetime, Field, StrictBool, StrictFloat, StrictInt, StrictStr, model_validator
from .models import Model, Id
import math

class ClinicalObservation(Model):
    id: Id
    concept: str = Field(min_length=1,max_length=120)
    value: StrictBool | StrictInt | StrictFloat | StrictStr | None
    unit: str = '1'
    timestamp: AwareDatetime
    quality: Literal['VALID','INVALID','UNKNOWN','NOT_MEASURED'] = 'UNKNOWN'
    method: str = Field(min_length=1,max_length=100)
    sample_id: Id
    provenance: str = Field(min_length=1,max_length=300)
    @model_validator(mode='after')
    def finite(self):
        if isinstance(self.value,float) and not math.isfinite(self.value): raise ValueError('NONFINITE')
        return self

class MeasurementBinding(Model):
    measurement_id: Id
    concept: str
    sample_id: Id

class ClinicalRequest(Model):
    subject_id: Id
    mission_id: Id
    condition_id: Literal['DM','DKA','ORTHOSTATIC_HYPOTENSION','POTS','AKI','ANAPHYLAXIS','HYPOGLYCEMIA'] | None = None
    presentation_id: str | None = None
    population: Literal['ADULT','NONPREGNANT_ADULT','UNKNOWN'] = 'UNKNOWN'
    age_years: StrictInt | None = Field(default=None,ge=0)
    as_of: AwareDatetime
    window_start: AwareDatetime
    observations: list[ClinicalObservation] = Field(default_factory=list,max_length=256)
    measurement_bindings: list[MeasurementBinding] = Field(default_factory=list,max_length=256)
    resources: dict[str,StrictBool] = Field(default_factory=dict,max_length=64)
    resource_policy: Literal['DECLARED_R2','MISSION_INVENTORY'] = 'DECLARED_R2'
    @model_validator(mode='after')
    def window(self):
        if self.resource_policy=='MISSION_INVENTORY' and self.resources:raise ValueError('DECLARED_AND_INVENTORY_RESOURCES_CANNOT_BE_MIXED')
        if self.window_start>self.as_of: raise ValueError('INVALID_WINDOW')
        if self.age_years is not None and self.age_years<18 and self.population!='UNKNOWN': raise ValueError('ADULT_POPULATION_AGE_CONFLICT')
        if not self.condition_id and not self.presentation_id: raise ValueError('ROUTE_REQUIRED')
        if self.condition_id and self.presentation_id: raise ValueError('AMBIGUOUS_ROUTE')
        if len({o.id for o in self.observations})!=len(self.observations): raise ValueError('DUPLICATE_OBSERVATION_ID')
        return self

class ClinicalMetadata(Model):
    hypoglycemia_level_minimum_supported: Literal[1,2,3] | None = None
    aki_stage: Literal[1,2,3] | None = None
    aki_stage_is_minimum_supported: bool = False
    resolution_status: Literal['MET','NOT_MET','UNKNOWN'] | None = None
    disease_excluded: Literal[False] = False
    clinical_validation: Literal['NOT_VALIDATED'] = 'NOT_VALIDATED'
    derivation_inputs: dict[str,list[str]] = Field(default_factory=dict)

class ClinicalEvaluationResult(Model):
    condition_id: str
    diagnostic_status: Literal['NOT_EVALUATED','INSUFFICIENT_DATA','SUSPECTED','CRITERIA_MET','CRITERIA_NOT_MET','CONFLICTING_EVIDENCE','NOT_APPLICABLE']
    urgency: Literal['ROUTINE','PROMPT','URGENT','EMERGENCY']
    confirmation_status: Literal['NOT_APPLICABLE','NOT_REQUIRED','REQUIRED','PENDING','SATISFIED','UNAVAILABLE']
    protocol_status: Literal['NOT_EVALUATED','NOT_INDICATED','ELIGIBLE','BLOCKED_MISSING_DATA','BLOCKED_CONTRAINDICATION','BLOCKED_RESOURCE','BLOCKED_AUTHORIZATION','READY_FOR_CREW']
    treatment_status: Literal['NOT_STARTED'] = 'NOT_STARTED'
    criterion_id: str
    criterion_version: str
    source_ids: list[str]
    source_statuses: dict[str,str]
    evaluation_tree: dict
    missing_fields: list[str] # deprecated: all indeterminate leaves, not requirements
    missing_required: list[str]
    optional_not_measured: list[str]
    required_for_protocol_safety: list[str]
    invalid_required: list[str]
    invalid_fields: list[str]
    missing_requirement_semantics: str
    data_requirement_version: str
    data_issues: list[dict]
    space_applicability: str
    limitations: list[str]
    protocol: dict
    metadata: ClinicalMetadata = Field(default_factory=ClinicalMetadata)

class ProtocolEligibilityRequest(Model):
    evaluation_id: Id
