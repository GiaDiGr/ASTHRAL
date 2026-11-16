"""Local-only capability adapter. All biomedical algorithms remain in reference modules."""
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from vigile.registry import Registry
from vigile.service import Engine
from vigile.monitoring import MonitoringService
from vigile.monitoring_models import MonitoringRequest
from vigile.models import (Measurement,Device,BaselineRequest,TrendRequest,EpisodeRequest,
                            FollowUpPlan,FollowUpReview,TransitionRequest)
from vigile.mission_context import MissionContextVersion,append_context
from vigile.management import InventoryVersion,append_inventory,ManagementRecord,append_management_record,countermeasure_documents

class LocalBiomedical:
    def __init__(self,store,owner):
        self.store=store;self.owner=owner
        self.engine=Engine(Registry(Path(__file__).parent),store)
        self.monitor=MonitoringService(self.engine)
    def scope(self,raw):
        if raw.get('subject_id',self.owner)!=self.owner or raw.get('mission_id','browser-mission')!='browser-mission':
            raise ValueError('LOCAL_PROFILE_SCOPE_MISMATCH')
        return {**raw,'subject_id':self.owner,'mission_id':'browser-mission'}
    def episode(self,identifier):
        row=self.engine.episode(identifier)
        if row['subject_id']!=self.owner or row['mission_id']!='browser-mission':raise ValueError('EPISODE_SCOPE_MISMATCH')
        return row
    def dispatch(self,action,data):
        if action=='ingest':
            with self.store.transaction():
                if data.get('device'):
                    device=Device.model_validate(data['device'])
                    if not device.synthetic:raise ValueError('SYNTHETIC_DEVICE_REQUIRED')
                    try:existing=self.store.get('device',device.id)
                    except KeyError:self.engine.register('device',device,'local_profile')
                    else:
                        if existing!=device.model_dump(mode='json'):raise ValueError('IMMUTABLE_DEVICE_CONFLICT')
                m=Measurement.model_validate(self.scope(data['measurement']))
                if not m.synthetic:raise ValueError('SYNTHETIC_MEASUREMENT_REQUIRED')
                return self.engine.ingest(m,'local_profile')
        if action=='baseline':return self.engine.build_baseline(BaselineRequest.model_validate(data),'local_profile')
        if action=='trend':return self.engine.trend(TrendRequest.model_validate(data),'local_profile')
        if action=='monitor':
            raw=self.scope(data)
            raw['measurements']=[self.scope(m) for m in raw.get('measurements',[])]
            return self.monitor.run(MonitoringRequest.model_validate(raw),'local_profile')
        if action=='replay_monitor':return self.monitor.replay(data['id'])
        if action=='episode_open':return self.engine.open_episode(EpisodeRequest.model_validate(self.scope(data)),'local_profile')
        if action=='episode_transition':
            self.episode(data['id'])
            # Local passphrase does not establish clinician identity. Never impersonate clinician.
            return self.engine.transition(data['id'],TransitionRequest.model_validate(data['request']),'local_profile')
        if action=='followup_plan':
            self.episode(data['episode_id'])
            return self.engine.followup(FollowUpPlan.model_validate(data),'local_profile')
        if action=='followup_review':
            plan=self.store.get('followup',data['plan_id']);self.episode(plan['episode_id'])
            return self.engine.review_followup(FollowUpReview.model_validate(data),'local_profile')
        if action=='mission_context':
            raw={**data,'mission_id':'browser-mission','context':{**data['context'],'id':'browser-mission','synthetic':True}}
            return append_context(self.engine,MissionContextVersion.model_validate(raw),'local_profile')
        if action=='management_record':
            self.episode(data['episode_id'])
            return append_management_record(self.engine,ManagementRecord.model_validate(data),'local_profile')
        if action=='countermeasures':
            from vigile.english import english_text
            return [{**row,'display_text':english_text(row['text'])} for row in countermeasure_documents(self.engine.registry)]
        if action=='inventory':
            return append_inventory(self.engine,InventoryVersion.model_validate({**data,'mission_id':'browser-mission'}),'local_profile')
        if action=='timeline':
            return {kind:self.store.all(kind) for kind in ('measurement','device','baseline','trend','finding','monitoring_run','monitoring_event','notification_ack','episode','followup','followup_review','medical_inventory','mission_context','clinical_evaluation','management_record')}
        if action=='notification_ack':
            event=self.store.get('monitoring_event',data['id'])
            if event['subject_id']!=self.owner or event['mission_id']!='browser-mission':raise ValueError('NOTIFICATION_SCOPE_MISMATCH')
            try:return self.store.get('notification_ack',event['id'])
            except KeyError:
                return self.store.put('notification_ack',event['id'],{'id':event['id'],'subject_id':self.owner,'mission_id':'browser-mission','acknowledged_at':datetime.now(timezone.utc).isoformat()},'local_profile')
        if action=='replay_clinical':
            from vigile.store import digest
            from vigile.clinical_engine import ClinicalService
            row=self.store.get('browser_evaluation',data['id'])
            if row['subject_id']!=self.owner:raise ValueError('EVALUATION_SCOPE_MISMATCH')
            if digest(row['snapshot'])!=row['input_hash'] or digest(row['output'])!=row['output_hash']:raise ValueError('EVALUATION_HASH_MISMATCH')
            output=ClinicalService(self.engine).compute(row['snapshot'])
            return {'id':row['id'],'matches':digest(output)==row['output_hash'],'scope':'FULL_FROZEN_CLINICAL_REEXECUTION','clinical_validation':False}
        raise ValueError('UNSUPPORTED_BIOMEDICAL_ACTION')

ACTIONS={'ingest','baseline','trend','monitor','replay_monitor','episode_open','episode_transition','followup_plan','followup_review','mission_context','inventory','timeline','notification_ack','replay_clinical','management_record','countermeasures'}
