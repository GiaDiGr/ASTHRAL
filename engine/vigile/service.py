from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
import hashlib
from .models import Measurement, Device, MissionContext, AstronautProfile
from .store import digest
from .quality import assess, comparable, convert, Inconclusive
from .algorithms import baseline, trends, hour_average
from .rules import calculate, result
from .extensions import ResearchExtensions
from .pathways import pathway_record, INTERACTION_SOURCES

# Explicit adapters; no fuzzy variable/condition matching.
VARIABLES={
 'vo2max_relative':('physiology.vo2max','mL/min/kg'),
 'premission_aerobic_capacity':('physiology.vo2max','mL/min/kg'),
 'current_aerobic_capacity':('physiology.vo2max','mL/min/kg'),
 'baseline_strength':('physiology.strength','N'), 'current_strength':('physiology.strength','N'),
 'body_weight':('strength.body_weight','kg_equivalent'),
 'deadlift_strength_value':('strength.deadlift','kg_equivalent'),
 'bench_press_strength_value':('strength.bench_press','kg_equivalent'),
 'past_spaceflight_effective_dose':('radiation.career_spaceflight','mSv'),
 'projected_upcoming_mission_effective_dose':('radiation.projected_spaceflight','mSv'),
 'modeled_design_reference_spe_effective_dose':('radiation.design_spe','mSv'),
 'nuclear_technology_effective_dose':('radiation.nuclear','mSv'),
 'mission_year_equivalent':('mission.duration_equivalent','mission-year'),
 'crew_support_duration_days':('mission.support_duration','day'),
 'nasa_effective_gcr_dose_rate':('radiation.design_gcr_rate','mSv/day'),
 'diluent_fraction_percent':('environment.diluent','%'),
 'total_pressure':('environment.pressure','kPa'),
 'absolute_total_pressure_change':('environment.pressure_change','psi'),
 'maximum_absolute_pressure_change_rate':('environment.pressure_rate','psi/min'),
}
SERVER_CONTEXT={'data_quality_status','measurement_comparability','measurement_unit','test_id',
 'window_coverage_complete','aggregation_method_validated','compartment_id',
 'microgravity_eva_planned_or_required','extraterrestrial_surface_eva_planned_or_required',
 'exposure_context','environment','measurement_method'}

class Engine(ResearchExtensions):
    def __init__(self, registry, store):
        self.registry,self.store=registry,store
        registry.import_to(store)
        self.implementation_hash=digest({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob("*.py")})

    def register(self, kind, model, actor):
        if kind=='profile': self.store.get('mission',model.mission_id)
        return self.store.put(kind,model.id,model.model_dump(mode='json'),actor)

    def ingest(self, m, actor):
        profile=self.store.get('profile',m.subject_id)
        mission=self.store.get('mission',m.mission_id)
        device=Device.model_validate(self.store.get('device',m.device_id))
        if profile['mission_id']!=m.mission_id or profile['synthetic']!=m.synthetic or mission['synthetic']!=m.synthetic:
            raise ValueError('Subject/mission/synthetic scope mismatch')
        state=assess(m,device,datetime.now(timezone.utc),historical=True)
        return self.store.put('measurement',m.id,{'measurement':m.model_dump(mode='json'),
                              'ingestion_quality':state},actor)

    def measurement(self, identifier):
        return Measurement.model_validate(self.store.get('measurement',identifier)['measurement'])

    def checked(self, identifier, as_of, historical=False):
        m=self.measurement(identifier)
        d=Device.model_validate(self.store.get('device',m.device_id))
        state=assess(m,d,as_of,historical)
        if state!='VALID': raise Inconclusive(state)
        self.check_conflicts(m,d,as_of)
        return m

    def check_conflicts(self,m,d,as_of):
        for raw in self.store.all('measurement'):
            other=Measurement.model_validate(raw['measurement'])
            if other.device_id==m.device_id or (other.subject_id,other.mission_id,other.variable,other.compartment,other.site)!=(m.subject_id,m.mission_id,m.variable,m.compartment,m.site): continue
            od=Device.model_validate(self.store.get('device',other.device_id))
            if (other.method,other.protocol,other.phase)!=(m.method,m.protocol,m.phase): continue
            if assess(other,od,as_of,True)!='VALID': continue
            overlap=(m.interval_end and other.interval_end and other.timestamp<m.interval_end and m.timestamp<other.interval_end)
            delta=abs((other.timestamp-m.timestamp).total_seconds())
            alignment=max(d.alignment_seconds or 0,od.alignment_seconds or 0)
            if not overlap and delta>alignment: continue
            if d.conflict_tolerance is None or od.conflict_tolerance is None: raise Inconclusive('MULTISENSOR_POLICY_REQUIRED')
            tolerance=min(d.conflict_tolerance,convert(od.conflict_tolerance,od.unit,d.unit))
            if abs(convert(other.value,other.unit,d.unit)-convert(m.value,m.unit,d.unit))>tolerance:
                raise Inconclusive('CONFLICTING_DATA')

    def resolve(self, identifier, as_of, historical=False):
        try:
            m=self.checked(identifier,as_of,historical)
            return m,{'measurement':m.model_dump(mode='json'),'device':self.store.get('device',m.device_id)}
        except KeyError:
            b=self.baseline_status(identifier,as_of)
            if not historical: raise Inconclusive('BASELINE_IN_CURRENT_SLOT')
            ms=[self.checked(mid,as_of,True) for mid in b['input_ids']]
            first=ms[0]
            m=first.model_copy(update={'id':identifier,'value':b['value'],'unit':b['unit'],
                                      'timestamp':max(x.timestamp for x in ms)})
            return m,{'baseline':b,'measurements':[x.model_dump(mode='json') for x in ms],
                      'devices':[self.store.get('device',x.device_id) for x in ms]}

    def replay_records(self, req):
        import json
        ids=set(req.co2_measurement_ids)
        for binding in req.bindings.values():
            ids.update(binding.values() if isinstance(binding,dict) else [binding])
        baselines=[]
        for identifier in list(ids):
            try:
                b=self.store.get('baseline',identifier); baselines.append(identifier); ids.update(b['input_ids'])
            except KeyError: pass
        with self.store.lock:
            rows=self.store.db.execute("SELECT kind,id,payload FROM records WHERE kind IN ('measurement','baseline','baseline_withdrawal','profile','mission','mission_context','device') ORDER BY kind,id").fetchall()
        records=[(row['kind'],row['id'],json.loads(row['payload'])) for row in rows]
        selected=[]; devices=set()
        for kind,identifier,payload in records:
            if kind=='measurement':
                m=payload['measurement']
                if identifier in ids or (m['subject_id'],m['mission_id'])==(req.subject_id,req.mission_id):
                    selected.append((kind,identifier,payload)); devices.add(m['device_id'])
            elif (kind=='baseline' and identifier in baselines or
                  kind=='baseline_withdrawal' and payload['baseline_id'] in baselines or
                  kind=='profile' and identifier==req.subject_id or
                  kind=='mission' and identifier==req.mission_id or
                  kind=='mission_context' and payload['mission_id']==req.mission_id and datetime.fromisoformat(payload['effective_at'])<=req.as_of): selected.append((kind,identifier,payload))
        selected.extend((k,i,v) for k,i,v in records if k=='device' and i in devices)
        return [list(row) for row in sorted(selected,key=lambda row:(row[0],row[1]))]

    def evaluate(self, req, actor):
        with self.store.lock:
            return self._evaluate(req,actor)

    def _evaluate(self, req, actor):
        frozen_records=self.replay_records(req)
        from .mission_context import mission_at
        mission=MissionContext.model_validate(mission_at(self.store,req.mission_id,req.as_of))
        profile=AstronautProfile.model_validate(self.store.get('profile',req.subject_id))
        rule=self.registry.rule(req.rule_id)
        snapshots=[]; conversions=[]; inputs={}; metric=None
        ctx={'mission_phase':mission.phase,'environment':mission.environment,'mode':mission.mode}
        try:
            if profile.mission_id!=mission.id: raise Inconclusive('SUBJECT_MISSION_MISMATCH')
            if req.mode!='SIMULATION':
                outcome=result('REQUIRES_VALIDATION','OPERATIONAL_ACTIVATION_BLOCKED')
            else:
                if not profile.synthetic or not mission.synthetic:
                    raise Inconclusive('SYNTHETIC_SCOPE_REQUIRED')
                allowed={f['name'] for f in rule['inputs'] if f['type'] not in ('number','map_anatomical_site_to_number','map_component_to_quantity')}-SERVER_CONTEXT
                allowed|={'radiation_context','nuclear_technology_emitting_ionizing_radiation_present','beyond_low_earth_orbit'}
                if set(req.context)-allowed: raise Inconclusive('CLIENT_CONTEXT_OVERRIDE_FORBIDDEN')
                inputs.update(req.context)
                ctx.update({k:req.context[k] for k in ('radiation_context','nuclear_technology_emitting_ionizing_radiation_present','beyond_low_earth_orbit') if k in req.context})
                for key in ('microgravity_eva_planned_or_required','extraterrestrial_surface_eva_planned_or_required','exposure_context'):
                    inputs[key]=getattr(mission,key)
                inputs['environment']=mission.environment
                resolved={}
                numeric_fields={f['name'] for f in rule['inputs'] if f['type'] in ('number','map_anatomical_site_to_number','map_component_to_quantity')}
                if set(req.bindings)-numeric_fields: raise Inconclusive('UNKNOWN_INPUT_BINDING')
                for key,binding in req.bindings.items():
                    historic=key.startswith('premission') or key.startswith('baseline')
                    members=binding if isinstance(binding,dict) else {'':binding}
                    if not members: raise Inconclusive('EMPTY_MEASUREMENT_MAP')
                    for site,identifier in members.items():
                        m,snapshot=self.resolve(identifier,req.as_of,historic)
                        snapshots.append(snapshot)
                        if m.subject_id!=req.subject_id or m.mission_id!=req.mission_id or not m.synthetic:
                            raise Inconclusive('MEASUREMENT_SCOPE_MISMATCH')
                        if historic and m.phase!='PRE_MISSION': raise Inconclusive('BASELINE_NOT_PREFLIGHT')
                        if not historic and m.phase!=mission.phase: raise Inconclusive('PHASE_MISMATCH')
                        if key in ('premission_bmd','current_bmd'):
                            if not site or m.site!=site: raise Inconclusive('ANATOMICAL_SITE_MISMATCH')
                            variable,unit='physiology.bmd','g/cm2'
                        elif key in ('calculated_requirements','provided_amounts'):
                            if not site: raise Inconclusive('MISSING_NUTRIENT_COMPONENT')
                            variable,unit='nutrition.'+site,m.unit
                        else:
                            if site or key not in VARIABLES: raise Inconclusive('UNSUPPORTED_INPUT_SHAPE')
                            variable,unit=VARIABLES[key]
                        if m.variable!=variable: raise Inconclusive('VARIABLE_MISMATCH')
                        if variable.startswith('environment.') and not m.compartment: raise Inconclusive('MISSING_COMPARTMENT')
                        value=convert(m.value,m.unit,unit)
                        conversions.append({'input_id':identifier,'from':m.unit,'to':unit,'original':m.value,'normalized':value})
                        if site: inputs.setdefault(key,{})[site]=value
                        else: inputs[key]=value
                        resolved[(key,site)]=m
                if req.rule_id in ('VIGILE-MUS-001','VIGILE-ENV-004','VIGILE-NUT-001') and resolved:
                    values=list(resolved.values())
                    if len({m.protocol for m in values})!=1:
                        raise Inconclusive('PROTOCOL_MISMATCH')
                    if req.rule_id in ('VIGILE-ENV-004','VIGILE-NUT-001'):
                        if len({(m.timestamp,m.interval_end) for m in values})!=1 or any(m.interval_end is None for m in values):
                            raise Inconclusive('ACCOUNTING_PERIOD_MISMATCH')
                pairs=[('premission_aerobic_capacity' ,'current_aerobic_capacity'),('baseline_strength','current_strength'),
                       ('premission_bmd','current_bmd'),('calculated_requirements','provided_amounts')]
                for b,c in pairs:
                    for (key,site),m in resolved.items():
                        if key!=b or (c,site) not in resolved: continue
                        current=resolved[(c,site)]
                        comparable([m,current],include_phase=False)
                        if b!='calculated_requirements' and current.timestamp<=m.timestamp:
                            raise Inconclusive('BASELINE_NOT_PRIOR')
                        if b=='calculated_requirements':
                            if m.timestamp!=current.timestamp or m.interval_end!=current.interval_end or not m.interval_end:
                                raise Inconclusive('NUTRITION_PERIOD_MISMATCH')
                            inputs[c][site]=convert(current.value,current.unit,m.unit)
                # Check the actual registered method, never a caller's method label.
                if ('vo2max_relative','') in resolved:
                    inputs['measurement_method']=resolved[('vo2max_relative','')].method
                if ('current_aerobic_capacity','') in resolved:
                    inputs['measurement_unit']=resolved[('current_aerobic_capacity','')].unit
                if ('current_strength','') in resolved:
                    inputs['test_id']=resolved[('current_strength','')].protocol
                inputs['measurement_comparability']='COMPARABLE'
                inputs['data_quality_status']='ACCEPTABLE'
                if req.rule_id=='VIGILE-ENV-002':
                    if 'one_hour_average_ppco2' in req.bindings: raise Inconclusive('DIRECT_CO2_AVERAGE_FORBIDDEN')
                    ms=[self.checked(mid,req.as_of,True) for mid in req.co2_measurement_ids]
                    for m in ms:
                        if m.subject_id!=req.subject_id or m.mission_id!=req.mission_id or not m.synthetic or m.phase!=mission.phase:
                            raise Inconclusive('MEASUREMENT_SCOPE_MISMATCH')
                        self.check_conflicts(m,Device.model_validate(self.store.get('device',m.device_id)),req.as_of)
                        snapshots.append({'measurement':m.model_dump(mode='json'),'device':self.store.get('device',m.device_id)})
                    metric=hour_average(ms,req.as_of)
                    inputs.update(one_hour_average_ppco2=metric['value'],window_coverage_complete=True,
                                  aggregation_method_validated=True,compartment_id=ms[0].compartment)
                elif req.co2_measurement_ids: raise Inconclusive('UNEXPECTED_CO2_INPUTS')
                outcome=calculate(rule,inputs,ctx)
        except (Inconclusive,KeyError) as exc:
            outcome=result('CONFLICTING_DATA' if str(exc)=='CONFLICTING_DATA' else 'INCONCLUSIVE',str(exc))
        bundle={'replay_records':frozen_records,'request':req.model_dump(mode='json'),'rule':rule,'rule_hash':digest(rule),
                'corpus_hash':self.registry.fingerprint,'mission':mission.model_dump(mode='json'),
                'profile':profile.model_dump(mode='json'),'snapshots':snapshots,'conversions':conversions,
                'normalized_inputs':inputs,'calculation_context':ctx,'metric':metric,
                'engine_version':'0.6.0','implementation_hash':self.implementation_hash,'algorithm_version':'1.0.0','outcome':outcome}
        identifier=digest(bundle)
        finding={'id':identifier,'kind':'NORMATIVE_COMPLIANCE_SIMULATION','rule_id':req.rule_id,
                 'subject_id':req.subject_id,'mission_id':req.mission_id,'timestamp':req.as_of.isoformat(),
                 'condition_ids':self.registry.conditions_for(req.rule_id),'bundle':bundle,**outcome}
        try:
            existing=self.store.get('finding',identifier)
            self.store.audit('REPLAY_REQUEST',actor,{'finding_id':identifier})
            return existing
        except KeyError:
            return self.store.put('finding',identifier,finding,actor)

    def reproduce(self, identifier):
        from .store import Store
        from .models import EvaluationRequest
        finding=self.store.get('finding',identifier)
        if 'bundle' not in finding:
            note=self.store.get('clinical_note',finding['note_id'])
            original={k:v for k,v in note.items() if k!='finding_id'}
            if digest(original)!=finding.get('note_hash',identifier): raise ValueError('NOTE_HASH_MISMATCH')
            return {'finding_id':identifier,'verified':True,'replay_scope':'HUMAN_RECORD_INTEGRITY_ONLY','finding':finding}
        b=finding['bundle']
        if digest(b)!=identifier or digest(b['rule'])!=b['rule_hash']:
            raise ValueError('REPRODUCTION_HASH_MISMATCH')
        if b['implementation_hash']!=self.implementation_hash:
            raise ValueError('ENGINE_VERSION_UNAVAILABLE_FOR_REPLAY')
        if b['corpus_hash']!=self.registry.fingerprint: raise ValueError('CORPUS_VERSION_UNAVAILABLE_FOR_REPLAY')
        if 'replay_records' not in b: raise ValueError('LEGACY_BUNDLE_REQUIRES_ARCHIVED_ENGINE')
        temporary=Store(':memory:')
        try:
            isolated=Engine(self.registry,temporary)
            temporary.put_many(b['replay_records'],'replay')
            repeated=isolated.evaluate(EvaluationRequest.model_validate(b['request']),'replay')
            if repeated['id']!=identifier: raise ValueError('REPRODUCTION_RESULT_MISMATCH')
        finally: temporary.close()
        return {'finding_id':identifier,'verified':True,'replay_scope':'FULL_INPUT_GATES_AND_COMPARATOR_REEXECUTED',
                'outcome':repeated['bundle']['outcome'],'bundle':b}

    def build_baseline(self, req, actor):
        return self.build_baseline_v2(req,actor)

    def trend(self, req, actor):
        try: return self.trend_v2(req,actor)
        except (OverflowError,ZeroDivisionError): raise Inconclusive('NUMERIC_OVERFLOW')

    def open_episode(self, req, actor):
        if req.condition_id not in self.registry.catalogs['conditions']:
            from .clinical_knowledge import ClinicalKnowledge
            if req.condition_id not in ClinicalKnowledge().criteria: raise ValueError('UNKNOWN_EPISODE_CONDITION')
        else: self.registry.get('conditions',req.condition_id)
        p=self.store.get('profile',req.subject_id)
        if p['mission_id']!=req.mission_id: raise ValueError('Episode mission mismatch')
        for fid in req.finding_ids:
            f=self.store.get('finding',fid)
            if (f['subject_id'],f['mission_id'])!=(req.subject_id,req.mission_id) or req.condition_id not in f['condition_ids']:
                raise ValueError('Finding episode scope mismatch')
        payload={**req.model_dump(mode='json'),'state':'FINDING' if req.finding_ids else 'MONITORING',
                 'authorization_state':'NONE'}
        return self.store.put('episode',req.id,payload,actor)

    def episode(self, identifier):
        e=self.store.get('episode',identifier)
        transitions=[t for t in self.store.all('transition') if t['episode_id']==identifier]
        if transitions: e['state']=transitions[-1]['target']
        e['transitions']=transitions
        e['finding_ids']=list(dict.fromkeys(e['finding_ids']+[fid for a in self.store.all('episode_attachment') if a['episode_id']==identifier for fid in a['finding_ids']]))
        return e

    def transition(self, identifier, req, actor):
        with self.store.transaction():
            e=self.episode(identifier)
            if req.expected_state and req.expected_state!=e['state']: raise ValueError('STALE_EPISODE_STATE')
            # No diagnostic or therapeutic protocol is supplied/authorized in this corpus.
            if req.target in ('TRIAGE','AUTHORIZED_ACTION'):
                self.store.append_audit('BLOCKED_TRANSITION',actor,{'episode_id':identifier,'target':req.target})
                return {'result':'BLOCKED_NO_AUTHORIZATION','state':e['state']}
            allowed={'MONITORING':['FINDING','ASSESSMENT'], 'FINDING':['ASSESSMENT'],
                     'ASSESSMENT':['RECOVERY','FOLLOW_UP'], 'RECOVERY':['FOLLOW_UP'], 'FOLLOW_UP':['CLOSED']}
            if req.target not in allowed.get(e['state'],[]): raise ValueError('INVALID_EPISODE_TRANSITION')
            if req.target in ('RECOVERY','FOLLOW_UP','CLOSED') and actor!='clinician':
                self.store.append_audit('BLOCKED_TRANSITION',actor,{'episode_id':identifier,'target':req.target})
                return {'result':'BLOCKED_NO_AUTHORIZATION','state':e['state']}
            t={'episode_id':identifier,'previous':e['state'],**req.model_dump(mode='json'),
               'semantic':'HUMAN_DOCUMENTED_WORKFLOW_NOT_CLINICAL_OUTCOME'}
            self.store.insert_record('transition',uuid4().hex,t,actor)
            return self.episode(identifier)

    def note(self, req, actor):
        episode=self.episode(req.episode_id)
        if req.kind=='DIAGNOSIS':
            self.store.audit('BLOCKED_DIAGNOSIS',actor,{'episode_id':req.episode_id,'request_hash':digest(req.model_dump(mode='json'))})
            return {'result':'BLOCKED_NO_AUTHORIZATION'}
        for eid in req.evidence_ids: self.registry.get('extractions',eid)
        note={**req.model_dump(mode='json'),'status':'HUMAN_MEDICAL_REVIEW_REQUIRED','diagnosis':None}
        records=[]
        if req.kind=='OBSERVATION':
            note_hash=digest(note)
            finding={'id':note_hash,'kind':'HUMAN_REPORTED_FINDING','result':'FINDING','diagnosis':None,
                'status':'HUMAN_MEDICAL_REVIEW_REQUIRED','subject_id':episode['subject_id'],
                'mission_id':episode['mission_id'],'timestamp':req.observed_at.isoformat(),
                'condition_ids':[episode['condition_id']],'note_id':req.id,'note_hash':note_hash,'evidence_ids':req.evidence_ids}
            note['finding_id']=finding['id']
            records.append(('finding',finding['id'],finding))
        self.store.put_many([('clinical_note',req.id,note),*records],actor)
        return note

    def action(self, req, actor):
        e=self.episode(req.episode_id)
        mission=self.store.get('mission',e['mission_id'])
        reason='BLOCKED_CONTEXT_NOT_APPLICABLE' if req.action=='postflight_standing_test' and mission['gravity']=='MICROGRAVITY' else 'BLOCKED_NO_AUTHORIZATION'
        self.store.audit('BLOCKED_ACTION',actor,{'episode_id':req.episode_id,'request_hash':digest(req.model_dump(mode='json')),'result':reason})
        return {'result':reason,'protocol_status':'AUTHORIZED_PROTOCOL_REQUIRED','executed':False}

    def pathway(self, identifier):
        e=self.episode(identifier)
        c=self.registry.get('conditions',e['condition_id'])
        return {'episode':e,'condition':c,'assessment':'HUMAN_MEDICAL_REVIEW_REQUIRED',
                'intervention':'AUTHORIZED_PROTOCOL_REQUIRED','diagnosis':None,'therapeutic_steps':[],
                'structured_pathway':pathway_record(self.registry,e['condition_id'])}

    def followup(self, req, actor):
        self.episode(req.episode_id)
        return self.store.put('followup',req.id,{**req.model_dump(mode='json'),'status':'HUMAN_PLAN_RECORDED',
                              'automatic_recovery_determination':False},actor)

    def review_followup(self, req, actor):
        plan=self.store.get('followup',req.plan_id); e=self.episode(plan['episode_id'])
        for mid in req.measurement_ids:
            m=self.measurement(mid)
            if (m.subject_id,m.mission_id)!=(e['subject_id'],e['mission_id']): raise ValueError('Follow-up scope mismatch')
        return self.store.put('followup_review',uuid4().hex,{**req.model_dump(mode='json'),
                              'reviewed_at':datetime.now(timezone.utc).isoformat(),'recovery_status':'HUMAN_ASSESSMENT_REQUIRED'},actor)

    def multisystem(self, req, actor):
        interaction=self.registry.get('interactions',req.interaction_id)
        if req.interaction_id in ('MSI05','MSI10'):
            payload={'result':'INCONCLUSIVE','reason':'EXERCISE_OR_MEDICATION_RECORD_REQUIRED','interaction_id':req.interaction_id,'clinical_execution':'BLOCKED','request':req.model_dump(mode='json'),'source_ids':INTERACTION_SOURCES[req.interaction_id]}
            return self.store.put('multisystem',uuid4().hex,payload,actor)
        fs=[self.store.get('finding',i) for i in req.finding_ids]
        if len(set(req.finding_ids))!=len(fs): raise ValueError('Duplicate finding')
        if len({(f['subject_id'],f['mission_id']) for f in fs})!=1: raise ValueError('Multisystem scope mismatch')
        if any(f['result'] not in ('REQUIREMENT_NOT_MET','FINDING','STATISTICAL_DEVIATION') for f in fs):
            raise ValueError('Only actual findings may co-occur')
        times=[datetime.fromisoformat(f['timestamp']) for f in fs]
        if (max(times)-min(times)).total_seconds()>req.max_separation_seconds: raise ValueError('Temporal mismatch')
        groups={'MSI01':[{'C012','C013'},{'C014','C015'}], 'MSI02':[{'C012','C013','C016'},{'C018','C019'}],
          'MSI03':[{'C004','C008'},{'C005'}], 'MSI04':[{'C003'},{'C021'}],
          'MSI05':[{'C001'},{'C002','C003','C004'}], 'MSI06':[{'C027'},{'C008','C015'}],
          'MSI07':[{'C023'},{'C001','C002','C003','C018'}], 'MSI08':[{'C009'},{'C008'}],
          'MSI09':[{'C037'},{'C030','C026','C027','C014','C038'}], 'MSI10':[{'C040'},{'C023','C004','C018'}],
          'MSI11':[{'C011'},{'C043','C004'}], 'MSI12':[{'C028'},{'C004','C015','C016','C041'}]}
        present=set(cid for f in fs for cid in f['condition_ids'])
        if not all(present & g for g in groups[req.interaction_id]): raise ValueError('Interaction condition mismatch')
        payload={'kind':'MULTISYSTEM_FINDING','status':'RESEARCH_ONLY','diagnosis':None,
                 'causality':'NOT_INFERRED','source_ids':INTERACTION_SOURCES[req.interaction_id],
                 'link_validation':'ENGINEERING_MAPPING_REQUIRES_REVIEW','interaction':interaction,'request':req.model_dump(mode='json')}
        return self.store.put('multisystem',uuid4().hex,payload,actor)
