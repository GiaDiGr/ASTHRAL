"""Append-only synthetic mission phase history; no clinical criteria or authorization."""
from datetime import datetime
from pydantic import AwareDatetime, model_validator
from .models import Model, Id, MissionContext

class MissionContextVersion(Model):
    id: Id
    mission_id: Id
    effective_at: AwareDatetime
    context: MissionContext

    @model_validator(mode='after')
    def scope(self):
        if self.context.id != self.mission_id or not self.context.synthetic:
            raise ValueError('SYNTHETIC_MATCHING_CONTEXT_REQUIRED')
        return self

def mission_at(store, mission_id, as_of):
    base = store.get('mission', mission_id)
    versions = [v for v in store.all('mission_context') if v['mission_id'] == mission_id
                and datetime.fromisoformat(v['effective_at']) <= as_of]
    return max(versions, key=lambda v: datetime.fromisoformat(v['effective_at']))['context'] if versions else base

def append_context(engine, version, actor):
    with engine.store.transaction():
        base = engine.store.get('mission', version.mission_id)
        if not base['synthetic']: raise ValueError('SYNTHETIC_MISSION_REQUIRED')
        previous = [v for v in engine.store.all('mission_context') if v['mission_id'] == version.mission_id]
        if any(datetime.fromisoformat(v['effective_at']) >= version.effective_at for v in previous):
            raise ValueError('CONTEXT_TIME_MUST_ADVANCE')
        committed = [v for v in engine.store.all('monitoring_run') if v['mission_id'] == version.mission_id]
        if any(datetime.fromisoformat(v['as_of']) >= version.effective_at for v in committed):
            raise ValueError('COMMITTED_CONTEXT_CANNOT_BE_REWRITTEN')
        return engine.store.put('mission_context', version.id, version.model_dump(mode='json'), actor)
