"""Validated, append-only synthetic EVA activity records for the browser bridge."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvaActivityRecord(BaseModel):
    """A completed software simulation; never a sensor or flight-operation record."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    id: str = Field(min_length=8, max_length=180, pattern=r'^[A-Za-z0-9_-]+$')
    subject_id: str = Field(min_length=1, max_length=180)
    mission_id: str = Field(min_length=1, max_length=120)
    eva_id: str = Field(min_length=1, max_length=120)
    mode: Literal['SIMULATION']
    scenario_id: Literal['nominal', 'thermal_warning', 'critical_training']
    started_at_utc: datetime
    ended_at_utc: datetime
    final_state: Literal['active', 'warning', 'critical', 'paused', 'completed', 'error']
    training_condition: bool
    report: dict[str, Any]
    session: dict[str, Any]

    @model_validator(mode='after')
    def validate_report_contract(self):
        report = self.report
        if report.get('report_type') != 'EVA Medical Handover Report':
            raise ValueError('EVA_HANDOVER_REPORT_TYPE_REQUIRED')
        if report.get('mode') != 'SIMULATION' or report.get('delivery_status') != 'PREPARED_LOCALLY_NOT_SENT':
            raise ValueError('EVA_REPORT_MUST_BE_LOCAL_SIMULATION')
        if report.get('eva_id') != self.eva_id or report.get('mission_id') != self.mission_id:
            raise ValueError('EVA_REPORT_SESSION_BINDING_MISMATCH')
        if report.get('scenario', {}).get('id') != self.scenario_id:
            raise ValueError('EVA_REPORT_SCENARIO_MISMATCH')
        if report.get('training_condition') is not self.training_condition:
            raise ValueError('EVA_REPORT_TRAINING_FLAG_MISMATCH')
        if self.ended_at_utc < self.started_at_utc:
            raise ValueError('EVA_ACTIVITY_TIME_ORDER_INVALID')
        if report.get('final_state') != self.final_state:
            raise ValueError('EVA_REPORT_FINAL_STATE_MISMATCH')
        if self.session.get('state') != 'completed':
            raise ValueError('EVA_ACTIVITY_MUST_BE_COMPLETED_BEFORE_STORAGE')
        if self.session.get('scenario_time_utc') != report.get('scenario_time_utc'):
            raise ValueError('EVA_SCENARIO_TIME_BINDING_MISMATCH')
        try:
            encoded = json.dumps(self.model_dump(mode='json'), ensure_ascii=False, allow_nan=False).encode('utf-8')
        except (TypeError, ValueError) as error:
            raise ValueError('EVA_RECORD_MUST_BE_JSON_SAFE') from error
        if len(encoded) > 400_000:
            raise ValueError('EVA_RECORD_SIZE_LIMIT_EXCEEDED')
        return self
