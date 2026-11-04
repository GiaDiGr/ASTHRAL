"""Versioned, read-only clinical wire contracts. Exclude unset fields on responses.

Legacy records remain readable without inventing four-state classifications.
"""
from typing import Literal
from pydantic import Field, JsonValue, model_validator
from .models import Model
from .clinical_models import ClinicalEvaluationResult
from .management import ManagementView

Urgency = Literal['ROUTINE','PROMPT','URGENT','EMERGENCY']
Truth = Literal['TRUE','FALSE','UNKNOWN','INVALID']

class ConfirmationEvidence(Model):
    path_id: str
    sample_id: str
    timestamp: str

class TraceNode(Model):
    operator: str
    state: bool | None
    truth_state: Truth | None = None  # absent in historical records
    field: str | None = None
    expected: JsonValue = None
    actual: JsonValue = None
    path: str | None = None
    logic_version: str | None = None
    children: list['TraceNode'] | None = None
    decisive_children: list[str] | None = None
    reasons: list[str] | None = None
    required_for_resolution: bool | None = None
    nonblocking_ancestor: str | None = None
    path_id: str | None = None
    sample_id: str | None = None
    context_observation_ids: list[str] | None = None
    confirmation_rule: str | None = None
    confirmation_evidence: list[ConfirmationEvidence] | None = None

    @model_validator(mode='after')
    def consistent_projection(self):
        if self.truth_state is not None:
            expected = {'TRUE':True,'FALSE':False}.get(self.truth_state)
            if self.state is not expected: raise ValueError('INCONSISTENT_TRUTH_PROJECTION')
        return self

class DataIssue(Model):
    observation_id: str | None = None
    concept: str
    reason: str

class ProtocolDecision(Model):
    protocol_id: str
    indication_supported: bool
    status: Literal['NOT_INDICATED','BLOCKED_MISSING_DATA','BLOCKED_CONTRAINDICATION','BLOCKED_RESOURCE','BLOCKED_AUTHORIZATION']
    block_reasons: list[str]
    required_for_protocol_safety: list[str] | None = None
    missing_resources: list[str] | None = None
    authorization: Literal['NO_VERIFIED_MISSION_POLICY']
    automatic_execution: Literal[False]

class ClinicalResultResponse(ClinicalEvaluationResult):
    evaluation_tree: TraceNode
    protocol: ProtocolDecision
    data_issues: list[DataIssue]
    missing_required: list[str] = Field(default_factory=list, description='Unresolved candidates, respecting AND/OR; not all individually mandatory. Absent in legacy records.')
    optional_not_measured: list[str] = Field(default_factory=list, description='Unmeasured leaves nonblocking for this decision, never proof of normality.')
    invalid_required: list[str] = Field(default_factory=list, description='Unusable leaves in unresolved branches.')
    invalid_fields: list[str] = Field(default_factory=list)
    required_for_protocol_safety: list[str] = Field(default_factory=list, description='Independent protocol safety requirements; not diagnostic alternatives.')
    missing_requirement_semantics: str | None = None
    data_requirement_version: str | None = None

class DifferentialRow(Model):
    condition_id: str
    reported_condition_id: str
    tier: str
    diagnostic_status: str
    support: list[str]
    contradictions: list[str]
    criteria_implemented: bool
    source_ids: list[str]
    external_evaluation_required: bool
    urgency: Urgency

class TestReason(Model):
    condition_id: str
    reason: str
    concepts: list[str] | None = None
    unresolved_candidates: list[str] | None = None
    purpose: Literal['DIAGNOSTIC_RESOLUTION','PROTOCOL_SAFETY'] | None = None
    alternatives_follow_evaluation_tree: bool | None = None
    source_ids: list[str] | None = None

class PendingTest(Model):
    test_id: str | None
    action: str | None = None
    catalogue_status: str | None = None
    reasons: list[TestReason]
    urgency: Urgency
    availability: bool | None
    risk: str
    cost: str
    execution_authorized: Literal[False]

class ClinicalEvaluationResponse(Model):
    id: str
    parent_id: str | None
    results: dict[str,ClinicalResultResponse]
    differential: list[DifferentialRow]
    next_tests: list[PendingTest]
    urgency: Urgency
    treatment_status: Literal['NOT_STARTED']
    presentation_protocol: ProtocolDecision | None
    management: dict[str,ManagementView] | None = None
    input_hash: str
    knowledge_hash: str
    knowledge_version: str
    implementation_hash: str
    output_hash: str

class ClinicalReplayResponse(Model):
    id: str
    matches: bool
    input_hash: str
    knowledge_hash: str

class EligibilityResponse(Model):
    evaluation_id: str
    eligibility: list[ProtocolDecision]
    new_authorization: Literal[False]
