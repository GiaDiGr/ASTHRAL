"""Incremental research services; no new clinical thresholds or activation mechanism."""
from datetime import datetime,timezone
from uuid import uuid4
from statistics import mean,stdev
from .quality import Inconclusive,assess,comparable,convert
from .models import Device,Measurement
from .algorithms import baseline,trends
from .store import digest
from .pathways import pathway_record

class ResearchExtensions:
    def save_research_record(self,kind,payload,actor):
        identifier=uuid4().hex
        return self.store.put(kind,identifier,{'id':identifier,**payload},actor)

    def baseline_status(self, identifier, as_of):
        b=self.store.get('baseline',identifier)
        if datetime.fromisoformat(b['request']['as_of'])>as_of:
            raise Inconclusive('BASELINE_NOT_YET_AVAILABLE')
        expiry=b.get('valid_until')
        if expiry and datetime.fromisoformat(expiry)<as_of:
            raise Inconclusive('BASELINE_EXPIRED')
        for event in self.store.all('baseline_withdrawal'):
            if event['baseline_id']==identifier and datetime.fromisoformat(event['effective_at'])<=as_of:
                raise Inconclusive('BASELINE_WITHDRAWN')
        return b

    def withdraw_baseline(self, req, actor):
        self.store.get('baseline',req.baseline_id)
        payload=req.model_dump(mode='json')
        return self.save_research_record('baseline_withdrawal',payload,actor)

    def build_baseline_v2(self, req, actor):
        ms=[self.checked(mid,req.as_of,True) for mid in req.measurement_ids]
        b=baseline(ms,req.minimum_observations)
        version=1
        if req.supersedes:
            prior=self.store.get('baseline',req.supersedes)
            old=self.measurement(prior['input_ids'][0])
            comparable([old,ms[0]])
            if req.as_of<=datetime.fromisoformat(prior['request']['as_of']):
                raise ValueError('REVISION_TIME_MUST_ADVANCE')
            version=prior.get('version',1)+1
        payload={**b,'id':req.id,'version':version,'supersedes':req.supersedes,
                 'valid_until':req.valid_until.isoformat() if req.valid_until else None,
                 'request':req.model_dump(mode='json'),'subject_id':ms[0].subject_id,'mission_id':ms[0].mission_id,
                 'variable':ms[0].variable,'method':ms[0].method,'protocol':ms[0].protocol,'site':ms[0].site,
                 'snapshots':[{'measurement':m.model_dump(mode='json'),'device':self.store.get('device',m.device_id)} for m in sorted(ms,key=lambda m:m.id)],
                 'implementation_hash':self.implementation_hash,'algorithm_version':'ALG001-2',
                 'validity_policy':'UNSPECIFIED_RESEARCH_ONLY' if req.valid_until is None else 'EXPLICIT_EXPIRY'}
        return self.store.put('baseline',req.id,payload,actor)

    def trend_v2(self, req, actor):
        ms=[self.checked(mid,req.as_of,True) for mid in req.measurement_ids]
        times=sorted(m.timestamp for m in ms)
        gaps=[(b-a).total_seconds() for a,b in zip(times,times[1:])]
        if req.max_gap_seconds and any(g>req.max_gap_seconds for g in gaps):
            raise Inconclusive('TEMPORAL_GAP_EXCEEDS_POLICY')
        # No automatic physiological computation on logarithmic measurements.
        if any(m.unit=='dBA' for m in ms): raise Inconclusive('LOGARITHMIC_ANALYSIS_REQUIRES_SPECIFIC_PROTOCOL')
        out=trends(ms,req.ewma_lambda,req.cusum_target,req.cusum_allowance,req.ewma_initial,req.cusum_decision_limit)
        comparison=None
        if req.baseline_id:
            b=self.baseline_status(req.baseline_id,req.as_of)
            bms=[self.checked(i,req.as_of,True) for i in b['input_ids']]
            comparable([*bms,*ms],include_phase=False)
            if max(m.timestamp for m in bms)>=min(m.timestamp for m in ms):
                raise Inconclusive('BASELINE_NOT_PRIOR')
            last=max(ms,key=lambda m:m.timestamp)
            value=convert(last.value,last.unit,b['unit'])
            base_values=[convert(m.value,m.unit,b['unit']) for m in bms]
            sd=stdev(base_values) if len(base_values)>1 else 0
            comparison={'baseline_id':req.baseline_id,'baseline_version':b.get('version',1),
                'absolute_change':value-b['value'],
                'retention_percent':None if b['value']<=0 else 100*value/b['value'],
                'z':None if sd==0 else (value-mean(base_values))/sd,
                'robust_z':None if b['mad']==0 else .6745*(value-b['value'])/b['mad'],
                'interpretation':'DESCRIPTIVE_NOT_DIAGNOSTIC'}
        payload={'request':req.model_dump(mode='json'),**out,'subject_id':ms[0].subject_id,
             'mission_id':ms[0].mission_id,'unit':min(ms,key=lambda m:m.timestamp).unit,
             'baseline_comparison':comparison,'maximum_observed_gap_seconds':max(gaps),
             'cadence_validation':'CONFIGURED' if req.max_gap_seconds else 'NOT_SPECIFIED',
             'snapshots':[{'measurement':m.model_dump(mode='json'),'device':self.store.get('device',m.device_id)} for m in sorted(ms,key=lambda m:m.id)],
             'implementation_hash':self.implementation_hash,'algorithm_version':'LONGITUDINAL-2'}
        # Overflow is an inconclusive computation, never JSON infinity.
        try: digest(payload)
        except ValueError: raise Inconclusive('NUMERIC_OVERFLOW')
        return self.save_research_record('trend',payload,actor)

    def quality_report(self, req, actor):
        assessments=[]
        if len(set(req.measurement_ids))!=len(req.measurement_ids): raise ValueError('DUPLICATE_INPUT_IDS')
        for identifier in req.measurement_ids:
            try:
                m=self.checked(identifier,req.as_of,req.historical)
                assessments.append({'measurement_id':identifier,'state':'VALID','device_id':m.device_id})
            except KeyError: assessments.append({'measurement_id':identifier,'state':'MISSING_REFERENCE'})
            except Inconclusive as exc: assessments.append({'measurement_id':identifier,'state':str(exc)})
        payload={'request':req.model_dump(mode='json'),'assessments':assessments,
                 'result':'VALID' if all(a['state']=='VALID' for a in assessments) else 'INCONCLUSIVE',
                 'diagnosis':None,'no_imputation':True}
        return self.save_research_record('quality_report',payload,actor)

    def attach_findings(self, identifier, req, actor):
        with self.store.transaction():
            e=self.episode(identifier)
            if e['state']=='CLOSED': raise ValueError('EPISODE_CLOSED')
            if len(set(req.finding_ids))!=len(req.finding_ids): raise ValueError('DUPLICATE_FINDINGS')
            for fid in req.finding_ids:
                f=self.store.get('finding',fid)
                if (f['subject_id'],f['mission_id'])!=(e['subject_id'],e['mission_id']) or e['condition_id'] not in f['condition_ids']:
                    raise ValueError('Finding episode scope mismatch')
                if fid in e['finding_ids']: raise ValueError('FINDING_ALREADY_ATTACHED')
            record={'episode_id':identifier,'finding_ids':req.finding_ids}
            self.store.insert_record('episode_attachment',uuid4().hex,record,actor)
        return self.episode(identifier)

    def followup_status(self, identifier, as_of):
        plan=self.store.get('followup',identifier)
        reviews=[r for r in self.store.all('followup_review') if r['plan_id']==identifier and datetime.fromisoformat(r.get('reviewed_at',as_of.isoformat()))<=as_of]
        complete=bool(reviews and reviews[-1].get('completed',False))
        return {'plan':plan,'reviews':reviews,'as_of':as_of.isoformat(),
                'status':'COMPLETED_BY_HUMAN' if complete else 'OVERDUE' if datetime.fromisoformat(plan['due_at'])<as_of else 'SCHEDULED',
                'clinical_recovery':'NOT_DETERMINED'}

    def register_evidence_revision(self, req, actor):
        self.registry.get('sources',req.source_id)
        with self.store.transaction():
            revisions=self.store.all('evidence_revision')
            if any(v['source_id']==req.source_id and v['version']==req.version for v in revisions):
                raise ValueError('EVIDENCE_VERSION_ALREADY_EXISTS')
            if req.supersedes:
                prior=self.store.get('evidence_revision',req.supersedes)
                if prior['source_id']!=req.source_id: raise ValueError('EVIDENCE_LINEAGE_MISMATCH')
            payload={**req.model_dump(mode='json'),'clinical_activation':'BLOCKED',
                     'document_verification':'HASH_DECLARED_BY_REVIEWER_NOT_INDEPENDENTLY_FETCHED'}
            identifier=digest(payload)
            self.store.insert_record('evidence_revision',identifier,{'id':identifier,**payload},actor)
            return {'id':identifier,**payload}

    def evidence_for_rule(self, identifier):
        rule=self.registry.rule(identifier)
        aliases={'NASA-STD-3001-V1-REV-C':'S01','NASA-STD-3001-V2-REV-F':'S02'}
        refs=[]
        for locator in rule['source_locators']:
            sid=aliases.get(locator['source_id'])
            refs.append({'original_locator':locator,'catalog_source_id':sid,
                'source':self.registry.get('sources',sid) if sid else None,
                'resolution':'EXPLICIT_REVISION_ALIAS' if sid else 'SEPARATE_DOCUMENT_NOT_MERGED',
                'recorded_revisions':[{k:x[k] for k in ('id','source_id','version','document_sha256','status','clinical_activation','document_verification')} for x in self.store.all('evidence_revision') if x['source_id']==sid]})
        return {'rule_id':identifier,'rule_hash':digest(rule),'evidence':refs,
                'clinical_activation':'BLOCKED','issues':self.registry.issues}

    def clinical_coverage(self):
        return [pathway_record(self.registry,c['condition_id']) for c in self.registry.list('conditions')]

    def assess_resources(self, req, actor):
        from .models import QualityRequest
        q=self.quality_report(QualityRequest(measurement_ids=req.measurement_ids,as_of=req.as_of),actor)
        payload={'request':req.model_dump(mode='json'),
                 'result':'INCONCLUSIVE' if q['result']!='VALID' else 'POLICY_CONFLICT' if req.proposed_interval_seconds>req.required_interval_seconds else 'COMPATIBLE_WITH_DECLARED_POLICY',
                 'quality_result':q['result'],'rule_thresholds_changed':False,'measurements_resampled':False,
                 'clinical_execution':'BLOCKED','policy_origin':'CALLER_DECLARED_ENGINEERING_POLICY'}
        return self.save_research_record('resource_assessment',payload,actor)
