"""Immutable receipt-time projections for synthetic mission review.

Frames are captured at ingestion checkpoints, never reconstructed by timestamp alone.
The unchanged legacy dashboard remains a live view. No writes exposed to reader clients.
"""
from datetime import datetime
from pydantic import AwareDatetime, Field
from .models import Model, Id
from .store import digest
from .mission_context import mission_at

class FrameIndex(Model):
    id: Id
    as_of: AwareDatetime
    phase: str
    gravity: str
    monitoring_id: Id
    snapshot_hash: str = Field(pattern='^[a-f0-9]{64}$')

def frame_index(engine,subject_id,mission_id):
    profile=engine.store.get('profile',subject_id)
    if profile['mission_id']!=mission_id: raise ValueError('FRAME_SCOPE_MISMATCH')
    import json
    with engine.store.lock:
        rows=engine.store.db.execute("SELECT json_extract(payload,'$.index') FROM records WHERE kind='mission_frame' AND json_extract(payload,'$.scope.subject_id')=? AND json_extract(payload,'$.scope.mission_id')=? ORDER BY seq",(subject_id,mission_id)).fetchall()
    return [FrameIndex.model_validate(json.loads(r[0])).model_dump(mode='json') for r in rows]

def read_frame(engine,identifier,subject_id,mission_id):
    r=engine.store.get('mission_frame',identifier)
    if r['scope']!={'subject_id':subject_id,'mission_id':mission_id}: raise ValueError('FRAME_SCOPE_MISMATCH')
    if digest(r['snapshot'])!=r['index']['snapshot_hash']: raise ValueError('FRAME_HASH_MISMATCH')
    return {**r['snapshot'],'historical_frame':r['index'],'knowledge_time':'RECEIPT_CHECKPOINT_NOT_TIMESTAMP_RECONSTRUCTION'}

def capture_frame(app,identifier,monitoring_id,actor='researcher'):
    engine=app.state.engine
    with engine.store.transaction():
        run=engine.store.get('monitoring_run',monitoring_id)
        sid,mid=run['subject_id'],run['mission_id'];at=datetime.fromisoformat(run['as_of'])
        if not engine.store.get('profile',sid)['synthetic']: raise ValueError('SYNTHETIC_FRAME_REQUIRED')
        runs=[r for r in engine.store.all('monitoring_run') if (r['subject_id'],r['mission_id'])==(sid,mid)]
        if runs[-1]['id']!=monitoring_id: raise ValueError('FRAME_MUST_BE_CAPTURED_AT_CURRENT_RECEIPT')
        from .dashboard_api import dashboard_projection
        snapshot=dashboard_projection(app,engine,sid,mid)
        snapshot['mission']=mission_at(engine.store,mid,at)
        # Receipt scope is frozen now; additionally omit samples from the simulated future.
        snapshot['measurements']=[r for r in snapshot['measurements'] if datetime.fromisoformat(r['measurement']['timestamp'])<=at
                                  and (not r['measurement'].get('interval_end') or datetime.fromisoformat(r['measurement']['interval_end'])<=at)]
        snapshot['evaluations']=[r for r in snapshot['evaluations'] if datetime.fromisoformat(r['as_of'])<=at]
        for ev in snapshot['evaluations']:
            ev['observations']=[o for o in ev['observations'] if datetime.fromisoformat(o['timestamp'])<=at]
        index=FrameIndex(id=identifier,as_of=at,phase=snapshot['mission']['phase'],gravity=snapshot['mission']['gravity'],
                         monitoring_id=monitoring_id,snapshot_hash=digest(snapshot)).model_dump(mode='json')
        engine.store.put('mission_frame',identifier,{'scope':{'subject_id':sid,'mission_id':mid},'index':index,'snapshot':snapshot},actor)
        return index
