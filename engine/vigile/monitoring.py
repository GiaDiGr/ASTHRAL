"""Atomic experimental cycles composed from acquisition, statistics and clinical services.

No background inference, no imputation, no therapy, no learned alarm thresholds.
"""
from datetime import datetime
from decimal import Decimal
import json
from .models import TrendRequest,EvaluationRequest,EpisodeRequest,EpisodeAttachment,FollowUpPlan,Measurement
from .clinical_models import ClinicalRequest,MeasurementBinding
from .clinical_engine import ClinicalService,UNITS as CLINICAL_UNITS,normalize
from .quality import Inconclusive,comparable,convert
from .store import Store,digest
from .monitoring_models import MonitoringRequest,MonitoringResult

# Explicit adapters to the supplied sensor catalogue and source IDs, not new diagnoses.
DOMAINS={
 'CARDIOVASCULAR':{'sources':['S01','S05'],'indicators':{'physiology.vo2max':'mL/min/kg','physiology.heart_rate':'bpm','adult_sbp_mm_hg':'mmHg','upright_sbp_mm_hg':'mmHg'},'limitations':['HEMODYNAMIC_TREND_NOT_ETIOLOGY','UPRIGHT_TEST_NOT_APPLICABLE_IN_FREE_MICROGRAVITY','MEASUREMENT_POSTURE_PROTOCOL_REQUIRED']},
 'MUSCULOSKELETAL':{'sources':['S01','S06'],'indicators':{'physiology.strength':'N','bone.hip_bmd':'g/cm2','bone.lumbar_bmd':'g/cm2'},'limitations':['DXA_MAINLY_GROUND_PRE_POST_NOT_ASSUMED_AVAILABLE_IN_FLIGHT','MATCH_SITE_AND_METHOD','TREND_NOT_FRACTURE_DIAGNOSIS']},
 'RADIATION':{'sources':['S01','S16'],'indicators':{'radiation.interval_effective_dose':'mSv','radiation.career_spaceflight':'mSv'},'limitations':['NO_ORGAN_DOSE_OR_RATE_CONVERSION_TO_EFFECTIVE_DOSE','MEASURED_DOSE_NOT_CANCER_DIAGNOSIS','WINDOW_SUM_NOT_LIFETIME_DOSE']},
 'SLEEP_BEHAVIOR':{'sources':['S10','S12'],'indicators':{'sleep.duration':'h','sleep.efficiency':'%','cognition.reaction_time':'ms','behavior.fatigue_score':'1'},'limitations':['WEAR_TIME_DIARY_TEST_VERSION_REQUIRED','NO_PSYCHIATRIC_DIAGNOSIS','FATIGUE_SCALE_MUST_MATCH_PROTOCOL']},
 'IMMUNE':{'sources':['S09'],'indicators':{'immune.viral_load':'copies/mL'},'limitations':['ANALYTE_MUST_BE_IDENTIFIED_IN_SITE_AND_PROTOCOL','LAB_CAPABILITY_NOT_ASSUMED','PCR_TREND_NOT_REACTIVATION_DIAGNOSIS','NO_VERIFIED_SPACE_THRESHOLD']},
 'ELECTROLYTES_OXYGENATION':{'sources':['S14','SRC-DKA-2024'],'indicators':{'potassium_mmol_l':'mmol/L','physiology.spo2':'%','environment.ppo2':'kPa'},'limitations':['DESCRIPTIVE_ONLY_NO_UNIVERSAL_THRESHOLD','POTASSIUM_DKA_SAFETY_REMAINS_SEPARATE','OXIMETRY_PERFUSION_MOTION_PRESSURE_CONTEXT_REQUIRED','AMBIENT_OXYGEN_NOT_ARTERIAL_OXYGENATION']}}
ROUTES={
 'DM':{'fasting_plasma_glucose_mg_dl','a1c_percent','ogtt_2h_plasma_glucose_mg_dl','random_plasma_glucose_mg_dl'},
 'DKA':{'plasma_glucose_mg_dl','beta_hydroxybutyrate_mmol_l','venous_pH','bicarbonate_mmol_l','urine_ketones_plus'},
 'HYPOGLYCEMIA':{'plasma_glucose_mg_dl','capillary_glucose_mg_dl','altered_mental_or_physical_status','assistance_required_for_hypoglycemia'},
 'AKI':{'serum_creatinine_mg_dl','baseline_creatinine_mg_dl','urine_output_ml_kg_h'},
 'ORTHOSTATIC_HYPOTENSION':{'baseline_sbp_mm_hg','upright_sbp_mm_hg','baseline_dbp_mm_hg','upright_dbp_mm_hg','physiology.heart_rate','physiology.vo2max'},
 'POTS':{'delta_hr_bpm','orthostatic_symptoms_frequent','physiology.heart_rate'},
 'ANAPHYLAXIS':{'acute_onset_minutes_to_hours','known_or_highly_probable_allergen','laryngeal_involvement','bronchospasm'}}
NORMATIVE={'physiology.vo2max':('VIGILE-AER-003','premission_aerobic_capacity','current_aerobic_capacity'),'physiology.strength':('VIGILE-MUS-002','baseline_strength','current_strength')}

class MonitoringService:
    def __init__(self,engine):
        self.engine=engine;self.store=engine.store;self.clinical=ClinicalService(engine)
        sources=set(engine.registry.catalogs['sources'])|set(self.clinical.knowledge.sources)
        if any(s not in sources for p in DOMAINS.values() for s in p['sources']):raise ValueError('MONITORING_SOURCE_UNRESOLVED')
    @staticmethod
    def projection(r):return {k:v for k,v in r.items() if k not in ('replay_records','request')}
    def records_before(self,req):
        rows=self.store.db.execute("SELECT kind,id,CASE WHEN kind='monitoring_run' THEN json_remove(payload,'$.replay_records') ELSE payload END AS payload FROM records WHERE kind!='mission_frame' ORDER BY seq").fetchall()
        allrows=[(r['kind'],r['id'],json.loads(r['payload'])) for r in rows]
        scoped=[];devices={m.device_id for m in req.measurements};baselines=set(req.baseline_ids);episodes=set()
        for k,i,p in allrows:
            if k=='medical_inventory' and req.resource_policy=='MISSION_INVENTORY' and p['mission_id']==req.mission_id and datetime.fromisoformat(p['effective_at'])<=req.as_of:scoped.append([k,i,p]);continue
            q=p.get('measurement',p)
            if ((q.get('subject_id'),q.get('mission_id'))==(req.subject_id,req.mission_id) or k=='profile' and i==req.subject_id or k=='mission' and i==req.mission_id or k=='mission_context' and p['mission_id']==req.mission_id and datetime.fromisoformat(p['effective_at'])<=req.as_of):
                if k=='monitoring_run':p={key:value for key,value in p.items() if key!='replay_records'}
                scoped.append([k,i,p])
                if k=='measurement':devices.add(q['device_id'])
                if k=='baseline':baselines.add(i)
                if k=='episode':episodes.add(i)
        scoped.extend([k,i,p] for k,i,p in allrows if k=='device' and i in devices or k=='baseline_withdrawal' and p['baseline_id'] in baselines or k in ('episode_attachment','transition','followup','note') and p.get('episode_id') in episodes)
        return scoped
    def run(self,req,actor):
        # One outer transaction: failures leave neither partial measurements nor alerts.
        with self.store.transaction():
            try:old=self.store.get('monitoring_run',req.id)
            except KeyError:old=None
            if old:
                if old['request']!=req.model_dump(mode='json'):raise ValueError('MONITORING_IDEMPOTENCY_CONFLICT')
                if old['implementation_hash']!=self.engine.implementation_hash:raise ValueError('MONITORING_VERSION_MISMATCH')
                return self.projection(old)
            prior=[r for r in self.store.all('monitoring_run') if (r['subject_id'],r['mission_id'])==(req.subject_id,req.mission_id)]
            previous=prior[-1] if prior else None
            if (previous['id'] if previous else None)!=req.previous_run_id:raise ValueError('MONITORING_PREDECESSOR_CONFLICT')
            if previous and req.as_of<datetime.fromisoformat(previous['as_of']):raise ValueError('MONITORING_TIME_REVERSED')
            from .mission_context import mission_at
            profile=self.store.get('profile',req.subject_id);mission=mission_at(self.store,req.mission_id,req.as_of)
            if profile['mission_id']!=req.mission_id:raise ValueError('MONITORING_SCOPE_MISMATCH')
            frozen=self.records_before(req)
            for m in req.measurements:
                try:existing=self.engine.measurement(m.id)
                except KeyError:self.engine.ingest(m,actor)
                else:
                    if existing!=m:raise ValueError('IMMUTABLE_MEASUREMENT_CONFLICT')
            result=self.compute(req,previous,mission,actor)
            result.update(id=req.id,subject_id=req.subject_id,mission_id=req.mission_id,previous_run_id=req.previous_run_id,as_of=req.as_of.isoformat(),clinical_context_id=req.clinical_context_id,mode='EXPERIMENTAL_NOT_CLINICALLY_VALIDATED',clinical_execution='BLOCKED',implementation_hash=self.engine.implementation_hash,knowledge_hash=self.clinical.knowledge.hash,policy_reference=req.policy_reference)
            result['input_hash']=digest({'request':req.model_dump(mode='json'),'records':frozen})
            result['output_hash']=digest(result)
            MonitoringResult.model_validate(result)
            self.store.put('monitoring_run',req.id,{**result,'request':req.model_dump(mode='json'),'replay_records':frozen},actor)
            return result
    def compute(self,req,previous,mission,actor):
        scoped=[Measurement.model_validate(r['measurement']) for r in self.store.all('measurement') if (r['measurement']['subject_id'],r['measurement']['mission_id'])==(req.subject_id,req.mission_id)]
        history=[m for m in scoped if req.history_start<=m.timestamp<=req.as_of]
        base_map={}
        for bid in req.baseline_ids:
            b=self.store.get('baseline',bid)
            if (b['subject_id'],b['mission_id'])!=(req.subject_id,req.mission_id):raise ValueError('BASELINE_SCOPE_MISMATCH')
            if b['variable'] in base_map:raise ValueError('AMBIGUOUS_BASELINE_SELECTION')
            base_map[b['variable']]=b
        domains=[];events=[];states={};clinical={};episode_ids=dict(previous['episode_ids']) if previous else {};followups=[]
        def event(key,kind,state,urgency,ids,sources,detail=None):
            fingerprint=digest([kind,state,urgency,detail]);old=(previous or {}).get('event_states',{}).get(key)
            new_evidence=not old or bool(set(ids)-set(old['evidence_ids']))
            changed=not old or old['fingerprint']!=fingerprint
            notify=kind!='DESCRIPTIVE_CHANGE' and (changed or urgency in ('URGENT','EMERGENCY') and new_evidence)
            reason='NEW_OR_CHANGED_STATE' if changed else 'NEW_URGENT_EVIDENCE' if notify else 'UNCHANGED_STATE_NO_REPEAT_NOTIFICATION'
            if kind=='DESCRIPTIVE_CHANGE':reason='DESCRIPTIVE_ONLY_NOT_CLINICAL_ALERT'
            item={'id':'me-'+digest([req.id,key])[:32],'key':key,'kind':kind,'state':state,'urgency':urgency,'notify':notify,'reason':reason,'evidence_ids':sorted(set(ids)),'source_ids':sources,'diagnosis':None,'clinical_execution':'BLOCKED'}
            events.append(item);states[key]={'fingerprint':fingerprint,'evidence_ids':item['evidence_ids'],'state':state,'urgency':urgency}
            self.store.put('monitoring_event',item['id'],{**item,'subject_id':req.subject_id,'mission_id':req.mission_id,'run_id':req.id},actor)
            return item
        for m in req.measurements:
            if m.timestamp>req.as_of or (m.interval_end and m.interval_end>req.as_of):
                event('receipt:'+m.id,'DATA_QUALITY','FUTURE_TIMESTAMP','ROUTINE',[m.id],[])
            elif m.timestamp<req.history_start:
                event('receipt:'+m.id,'DATA_QUALITY','OUTSIDE_HISTORY_WINDOW','ROUTINE',[m.id],[])
            elif previous and m.timestamp<datetime.fromisoformat(previous['as_of']):
                event('receipt:'+m.id,'DATA_QUALITY','LATE_ARRIVAL_REANALYZED_NOT_CURRENT','ROUTINE',[m.id],[])
        for domain,policy in DOMAINS.items():
            indicators=[]
            for variable,unit in policy['indicators'].items():
                ms=sorted([m for m in history if m.variable==variable],key=lambda m:(m.timestamp,m.id));valid=[];issues=[]
                # Historical analysis retains historical validity. Current decision also checks age.
                for m in ms:
                    try:valid.append(self.engine.checked(m.id,req.as_of,True))
                    except Inconclusive as exc:issues.append({'measurement_id':m.id,'reason':str(exc)})
                state='NOT_MEASURED';latest=None;value=None;comparison=None;trend=None;finding=None
                if ms:
                    latest=ms[-1]
                    try:
                        self.engine.checked(latest.id,req.as_of)
                        if latest.phase!=mission['phase']:raise Inconclusive('CURRENT_MISSION_PHASE_MISMATCH')
                        simultaneous=[m for m in ms if m.timestamp==latest.timestamp]
                        if len({convert(m.value,m.unit,unit) for m in simultaneous})>1:raise Inconclusive('CONFLICTING_DATA')
                        if variable=='immune.viral_load' and not latest.site:raise Inconclusive('ANALYTE_SITE_REQUIRED')
                        value=convert(latest.value,latest.unit,unit);state='DESCRIPTIVE_AVAILABLE'
                    except Inconclusive as exc:state=str(exc);issues.append({'measurement_id':latest.id,'reason':state})
                b=base_map.get(variable)
                if value is not None and b:
                    try:
                        self.engine.baseline_status(b['id'],req.as_of)
                        bms=[self.engine.checked(i,req.as_of,True) for i in b['input_ids']]
                        comparable([*bms,latest],include_phase=False)
                        if max(m.timestamp for m in bms)>=latest.timestamp:raise Inconclusive('BASELINE_NOT_PRIOR')
                        bv=convert(b['value'],b['unit'],unit)
                        comparison={'baseline_id':b['id'],'baseline_value':bv,'absolute_change':value-bv,'retention_percent':100*value/bv if bv>0 else None,'interpretation':'DESCRIPTIVE_NOT_DIAGNOSTIC'}
                    except Inconclusive as exc:issues.append({'baseline_id':b['id'],'reason':str(exc)})
                if len(valid)>=2 and latest and value is not None:
                    selected=[m for m in valid if m.phase==latest.phase]
                    if len(selected)>=2:
                        try:
                            tr=self.engine.trend(TrendRequest(measurement_ids=[m.id for m in selected],as_of=req.as_of,ewma_lambda=req.ewma_lambda,cusum_target=convert(selected[0].value,selected[0].unit,selected[0].unit),cusum_allowance=req.cusum_allowance,baseline_id=b['id'] if comparison else None,policy_reference=req.policy_reference),actor)
                            # Remove generated storage ID: the mathematical result is replay-stable.
                            trend={k:tr[k] for k in ('slope_per_day','cadence_semantics','trace','status','input_ids','maximum_observed_gap_seconds')}
                        except Inconclusive as exc:issues.append({'reason':str(exc)})
                if value is not None and comparison and variable in NORMATIVE:
                    rid,bkey,ckey=NORMATIVE[variable]
                    f=self.engine.evaluate(EvaluationRequest(rule_id=rid,subject_id=req.subject_id,mission_id=req.mission_id,as_of=req.as_of,bindings={bkey:b['id'],ckey:latest.id},mode='SIMULATION'),actor)
                    finding=f['id'];event('norm:'+variable,'NORMATIVE_REQUIREMENT',f['result'],'ROUTINE',[latest.id,b['id']],policy['sources'])
                elif comparison and comparison['absolute_change']!=0:event('change:'+variable,'DESCRIPTIVE_CHANGE','NUMERIC_CHANGE_NOT_DIAGNOSIS','ROUTINE',[latest.id,b['id']],policy['sources'])
                if issues:event('quality:'+variable,'DATA_QUALITY',state if value is None else 'HISTORICAL_OR_BASELINE_ISSUES','ROUTINE',[i['measurement_id'] for i in issues if 'measurement_id' in i],policy['sources'],sorted({i['reason'] for i in issues}))
                indicators.append({'variable':variable,'unit':unit,'state':state,'latest_measurement_id':latest.id if latest else None,'value':value,'valid_count':len(valid),'quality_issues':issues,'baseline_comparison':comparison,'trend':trend,'normative_finding_id':finding,'source_ids':policy['sources'],'limitations':['EXPERIMENTAL_NOT_CLINICALLY_VALIDATED','NO_IMPUTATION','NO_VERIFIED_CLINICAL_CHANGE_THRESHOLD']})
            domains.append({'domain':domain,'available_indicators':[i['variable'] for i in indicators if i['value'] is not None],'missing_indicators':[i['variable'] for i in indicators if i['value'] is None],'indicators':indicators,'source_ids':policy['sources'],'method':'PERSONAL_BASELINE_AND_EXISTING_DESCRIPTIVE_STATISTICS','phase':mission['phase'],'gravity':mission['gravity'],'applicability':'DESCRIPTIVE_MONITORING_ONLY','limitations':policy['limitations'],'accumulated_dose':self.radiation(history,req) if domain=='RADIATION' else None})
        same_context=previous and previous['clinical_context_id']==req.clinical_context_id
        # Carry only the explicit current context, never unselected observations from another episode.
        carried=(previous or {}).get('clinical_evaluations',{}) if same_context else {}
        obs={};bindings={}
        if carried:
            first=next(iter(carried.values()))
            prior_request=self.store.get('clinical_evaluation',first['id'])['snapshot']['request']
            obs={o['id']:o for o in prior_request['observations'] if datetime.fromisoformat(o['timestamp'])>=req.clinical_window_start}
            bindings={b['measurement_id']:b for b in prior_request['measurement_bindings'] if self.engine.measurement(b['measurement_id']).timestamp>=req.clinical_window_start}
        for o in req.observations:
            raw=o.model_dump(mode='json')
            if o.id in obs and obs[o.id]!=raw:raise ValueError('IMMUTABLE_OBSERVATION_CONFLICT')
            obs[o.id]=raw
        for m in req.measurements:
            if m.variable in CLINICAL_UNITS:bindings[m.id]={'measurement_id':m.id,'concept':m.variable,'sample_id':req.sample_ids.get(m.id,m.id)}
        # Preserve phase failures as invalid evidence, never revive an older reading.
        for identifier,binding in list(bindings.items()):
            m=self.engine.measurement(identifier)
            if m.phase!=mission['phase'] and binding['concept']!='baseline_creatinine_mg_dl':
                obs[identifier]={'id':identifier,'concept':binding['concept'],'value':m.value,'unit':m.unit,'timestamp':m.timestamp.isoformat(),'quality':'INVALID','method':m.method,'sample_id':binding['sample_id'],'provenance':'CURRENT_MISSION_PHASE_MISMATCH: '+m.provenance[:240]}
                del bindings[identifier]
        concepts={m.variable for m in req.measurements}|{o['concept'] for o in obs.values()}|{b['concept'] for b in bindings.values()}
        routes={r for r,fields in ROUTES.items() if concepts&fields}|set(carried)
        for route in sorted(routes):
            cr=ClinicalRequest(subject_id=req.subject_id,mission_id=req.mission_id,condition_id=route,population=req.population,age_years=req.age_years,resource_policy=req.resource_policy,as_of=req.as_of,window_start=req.clinical_window_start,observations=list(obs.values()),measurement_bindings=list(bindings.values()))
            parent=carried.get(route,{}).get('id')
            evaluation=self.clinical.evaluate(cr,actor,parent,identifier='ce-'+digest([req.id,route])[:32]);clinical[route]=evaluation;r=evaluation['results'][route]
            snapshot=self.store.get('clinical_evaluation',evaluation['id'])['snapshot'];_,_,histories=normalize(cr,snapshot['observations'])
            def criterion_fields(node):
                return ({node['field']} if 'field' in node else set())|set().union(*(criterion_fields(child) for key in ('all_of','any_of') for child in node.get(key,[])))
            relevant=criterion_fields(self.clinical.knowledge.criteria[route]['logic'])
            derived_ids={i for ids in r['metadata'].get('derivation_inputs',{}).values() for i in ids}
            evidence=[max(h,key=lambda o:datetime.fromisoformat(o['timestamp']))['id'] for k,h in histories.items() if k in relevant and h]
            evidence+=sorted(derived_ids)
            ev=event('clinical:'+route,'CLINICAL_CRITERIA',r['diagnostic_status'],r['urgency'],evidence,r['source_ids'],[r['confirmation_status'],r['protocol_status'],r['missing_required'],r['invalid_required'],r['required_for_protocol_safety'],r['metadata'].get('hypoglycemia_level_minimum_supported')])
            if ev['notify'] and r['diagnostic_status'] not in ('NOT_APPLICABLE','CRITERIA_NOT_MET'):
                fid='mf-'+digest([req.id,route])[:32]
                self.store.put('finding',fid,{'id':fid,'subject_id':req.subject_id,'mission_id':req.mission_id,'condition_ids':[route],'kind':'EXPERIMENTAL_MONITORING_EVENT','result':'FINDING','diagnosis':None,'timestamp':req.as_of.isoformat(),'evaluation_id':evaluation['id'],'source_ids':r['source_ids'],'status':'RESEARCH_ONLY','reason':'CLINICAL_CRITERIA_OR_INSUFFICIENT_EVIDENCE_REQUIRES_REVIEW'},actor)
                if route not in episode_ids or not same_context or self.engine.episode(episode_ids[route])['state']=='CLOSED':
                    eid='ep-'+digest([req.id,route])[:32];self.engine.open_episode(EpisodeRequest(id=eid,subject_id=req.subject_id,mission_id=req.mission_id,condition_id=route,finding_ids=[fid]),actor);episode_ids[route]=eid
                else:self.engine.attach_findings(episode_ids[route],EpisodeAttachment(finding_ids=[fid]),actor)
                if req.followup_at:
                    plan='fu-'+digest([req.id,route])[:32]
                    self.engine.followup(FollowUpPlan(id=plan,episode_id=episode_ids[route],due_at=req.followup_at,goal_description='Experimental monitoring: review evidence, pending tests and repeat evaluation; no automatic recovery or treatment.',protocol_reference=req.policy_reference),actor);followups.append(plan)
        # Keep unresolved prior states when an indicator is absent; absence never clears an alert.
        for key,value in (previous or {}).get('event_states',{}).items():states.setdefault(key,value)
        return {'domains':domains,'clinical_evaluations':clinical,'events':events,'event_states':states,'episode_ids':episode_ids,'followup_ids':followups}
    def radiation(self,history,req):
        ms=sorted([m for m in history if m.variable=='radiation.interval_effective_dose'],key=lambda m:(m.timestamp,m.id));total=Decimal(0);end=None;issues=[];covered=0
        if ms:
            try:
                comparable(ms,include_phase=False)
                if len({m.device_id for m in ms})>1:raise Inconclusive('UNVERIFIED_DOSIMETER_HANDOVER')
            except Inconclusive as exc:issues.append({'reason':str(exc)})
        for m in ms:
            try:
                self.engine.checked(m.id,req.as_of,True)
                if m.method!='INTERVAL_TOTAL' or not m.interval_end:raise Inconclusive('INTERVAL_TOTAL_REQUIRED')
                if end and m.timestamp<end:raise Inconclusive('OVERLAPPING_DOSE_INTERVALS')
                if m.value<0:raise Inconclusive('NEGATIVE_DOSE')
                total+=Decimal(str(convert(m.value,m.unit,'mSv')));covered+=(m.interval_end-m.timestamp).total_seconds();end=m.interval_end
            except Inconclusive as exc:issues.append({'id':m.id,'reason':str(exc)})
        complete=bool(ms) and not issues and ms[0].timestamp==req.history_start and end==req.as_of and covered==(req.as_of-req.history_start).total_seconds()
        return {'state':'INVALID_NO_TOTAL' if issues else 'COMPLETE_WINDOW' if complete else 'PARTIAL_WINDOW' if ms else 'NOT_MEASURED','effective_dose_mSv':None if issues or not ms else float(total),'coverage_seconds':covered,'issues':issues,'interpretation':'RECORDED_INTERVALS_ONLY_NOT_LIFETIME_DOSE_OR_DIAGNOSIS'}
    def replay(self,identifier):
        r=self.store.get('monitoring_run',identifier)
        if r['implementation_hash']!=self.engine.implementation_hash or r['knowledge_hash']!=self.clinical.knowledge.hash:raise ValueError('REPLAY_VERSION_MISMATCH')
        if digest({'request':r['request'],'records':r['replay_records']})!=r['input_hash']:raise ValueError('REPLAY_INPUT_HASH_MISMATCH')
        projected=self.projection(r);expected=projected.pop('output_hash')
        if digest(projected)!=expected:raise ValueError('REPLAY_STORED_OUTPUT_HASH_MISMATCH')
        from .service import Engine
        temporary=Store(':memory:')
        try:
            isolated=Engine(self.engine.registry,temporary)
            temporary.put_many([tuple(row) for row in r['replay_records']],'replay')
            output=MonitoringService(isolated).run(MonitoringRequest.model_validate(r['request']),'replay')
            matches=output['output_hash']==expected
        finally:temporary.close()
        return {'id':identifier,'matches':matches,'scope':'FULL_FROZEN_CYCLE_REEXECUTION','clinical_validation':False}

def install_monitoring_routes(app,engine,research):
    service=MonitoringService(engine);app.state.monitoring=service
    @app.post('/monitoring/cycles',response_model=MonitoringResult,response_model_exclude_unset=True,status_code=201)
    def cycle(body:MonitoringRequest,actor=research):return service.run(body,actor)
    @app.get('/monitoring/cycles',response_model=list[MonitoringResult],response_model_exclude_unset=True)
    def cycles(subject_id:str,mission_id:str):return [service.projection(r) for r in engine.store.all('monitoring_run') if (r['subject_id'],r['mission_id'])==(subject_id,mission_id)]
    @app.get('/monitoring/cycles/{identifier}',response_model=MonitoringResult,response_model_exclude_unset=True)
    def get(identifier:str):return service.projection(engine.store.get('monitoring_run',identifier))
    @app.get('/monitoring/cycles/{identifier}/replay')
    def replay(identifier:str):return service.replay(identifier)
    @app.get('/monitoring/domains')
    def domains():return {'domains':DOMAINS,'mode':'EXPERIMENTAL_NOT_CLINICALLY_VALIDATED','clinical_execution':'BLOCKED'}
