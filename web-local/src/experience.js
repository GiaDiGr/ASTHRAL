import {utcInput} from './time.js';
import {criterionInputConcepts} from './profile-input.js';
export const human=value=>({DM:'Diabetes assessment',DKA:'Diabetic ketoacidosis',HYPOGLYCEMIA:'Low blood glucose',AKI:'Acute kidney injury',POTS:'Postural orthostatic tachycardia assessment',ORTHOSTATIC_HYPOTENSION:'Orthostatic hypotension',ANAPHYLAXIS:'Anaphylaxis',CRITERIA_MET:'Documented criteria satisfied',CRITERIA_NOT_MET:'Documented criteria not satisfied',INSUFFICIENT_DATA:'Insufficient evidence',BLOCKED_MISSING_DATA:'Protocol blocked: safety information is missing',BLOCKED_NO_AUTHORIZATION:'Human medical authorization required',SATISFIED:'Confirmation requirements satisfied',UNKNOWN:'Unknown',TRUE:'Satisfied',FALSE:'Not satisfied',INVALID:'Invalid evidence',NOT_APPLICABLE:'Not applicable',potassium_mmol_l:'Blood potassium',bicarbonate_mmol_l:'Bicarbonate',urine_ketones_plus:'Urine ketones',venous_pH:'Venous pH',plasma_glucose_mg_dl:'Plasma glucose',beta_hydroxybutyrate_mmol_l:'Beta-hydroxybutyrate'}[value]??String(value).replaceAll('_',' ').replaceAll('.',' '));
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
const field=(parent,title,type='text',value='')=>{const label=node('label',title),input=node('input');input.type=type;input.value=value;if(type==='number')input.step='any';label.append(input);parent.append(label);return input;};
const choice=(parent,title,options,value)=>{const label=node('label',title),select=node('select');for(const [id,text] of options){const option=node('option',text);option.value=id;select.append(option);}if(value!==undefined)select.value=value;label.append(select);parent.append(label);return select;};
const button=(parent,title,action)=>{const b=node('button',title);b.type='button';b.onclick=action;parent.append(b);return b;};
const utc=input=>{if(!input.value)throw Error('An explicit timestamp is required.');return utcInput(input.value);};
const dateValue=value=>value?new Date(value).toISOString().slice(0,19):'';
export async function installExperience(api){
 const $=id=>document.getElementById(id),schema=await api.call('clinical_schema');let rows=[],snapshot=null,timeline=null;
 const advanced=node('details');advanced.id='advanced-settings';advanced.append(node('summary','Settings and Developer View'));
 const toggle=field(advanced,'Show Developer View','checkbox');toggle.onchange=()=>document.body.classList.toggle('developer-view',toggle.checked);
 $('intro').append(advanced);for(const id of ['install-offline','offline-status','activate-update','diagnose','run-parity'])advanced.append($(id));
 const diagnostics=$('diagnostics').closest('details');diagnostics.classList.add('developer-only');advanced.append(diagnostics);
 $('case-list').closest('label').classList.add('developer-only');$('scenario').closest('label').classList.add('developer-only');$('clinical-output').closest('details').classList.add('developer-only');
 const clinical=$('clinical'),form=node('div');form.id='clinical-form';clinical.insertBefore(form,$('scenario').closest('label'));
 const route=choice(form,'Assessment pathway',Object.keys(schema.criteria).map(id=>[id,human(id)]));
 const population=choice(form,'Population',[['UNKNOWN','Unknown'],['ADULT','Adult'],['NONPREGNANT_ADULT','Nonpregnant adult']]);
 const resourcePolicy=choice(form,'Medical resource source',[['MISSION_INVENTORY','Recorded mission inventory (unknown until recorded)'],['DECLARED_R2','Legacy declared synthetic resources']]);
 const age=field(form,'Age in years (leave empty if unknown)','number');age.min='0';age.step='1';
 const asof=field(form,'Assessment time (UTC)','datetime-local');
 const start=field(form,'Evidence window start (UTC)','datetime-local');
 const guidance=node('p','Leave unmeasured values empty. Required information depends on the complete criterion tree; missing alternatives are not automatically mandatory. The engine derives supported changes from raw inputs. Use distinct sample identifiers and timestamps for repeated observations.');form.append(guidance);
 const observations=node('div');observations.id='observation-fields';form.append(observations);
 const supported=[...new Set([...Object.keys(schema.units),...schema.booleans])].sort();
 const additional=node('details');additional.append(node('summary','Add repeated, contextual or protocol-safety observations'));
 const additionalConcept=choice(additional,'Supported observation concept',supported.map(concept=>[concept,human(concept)]));
 button(additional,'Add observation',()=>addRow(additionalConcept.value));form.append(additional);
 function addRow(concept,original=null){
    const group=node('fieldset');group.append(node('legend',human(concept)));
    const bool=schema.booleans.includes(concept)||typeof original?.value==='boolean';
    const unit=schema.units[concept]??original?.unit??'1';
    const value=bool?choice(group,'Observation',[['','Not measured'],['true','Yes'],['false','No']],original?String(original.value):''):field(group,'Value',schema.units[concept]?'number':'text',original?.value??'');
    if(!bool&&!schema.units[concept]&&typeof original?.value==='number')value.type='number';
    const unitInput=field(group,'Unit','text',unit);unitInput.readOnly=!!schema.units[concept];
    const timestamp=field(group,'Observed at (UTC)','datetime-local',dateValue(original?.timestamp));
    const quality=choice(group,'Evidence quality',[['UNKNOWN','Unknown'],['VALID','Valid by declared source'],['INVALID','Invalid'],['NOT_MEASURED','Not measured']],original?.quality??'UNKNOWN');
    const method=field(group,'Measurement / observation method','text',original?.method??'');
    const sample=field(group,'Sample identifier (same sample only when genuinely shared)','text',original?.sample_id??'');
    rows.push({concept,bool,value,unitInput,timestamp,quality,method,sample,original});observations.append(group);
 }

 function draw(){
  observations.replaceChildren();rows=[];
  const existing=snapshot?.request.observations??[];
  const concepts=[...new Set([...existing.map(o=>o.concept),...criterionInputConcepts(schema.criteria[route.value]?.logic,schema.derivation_inputs??{},supported)])];
  for(const concept of concepts){const originals=existing.filter(o=>o.concept===concept);for(const original of originals.length?originals:[null])addRow(concept,original);}
 }
 route.onchange=()=>{snapshot={...snapshot,request:{...snapshot.request,condition_id:route.value,presentation_id:null,observations:[]}};draw();};
 function refresh(){snapshot=JSON.parse($('scenario').value);route.value=snapshot.request.condition_id??'DM';population.value=snapshot.request.population;age.value=snapshot.request.age_years??'';asof.value=dateValue(snapshot.request.as_of);start.value=dateValue(snapshot.request.window_start);draw();}
 function sync(){
  if(document.body.classList.contains('developer-view'))return;
  const request={...snapshot.request,condition_id:route.value,presentation_id:null,population:population.value,age_years:age.value===''?null:Number(age.value),as_of:utc(asof),window_start:utc(start),resource_policy:resourcePolicy.value,resources:resourcePolicy.value==='MISSION_INVENTORY'?{}:snapshot.request.resources,observations:[]};
  for(const row of rows){if(row.value.value==='')continue;
   const value=row.bool?row.value.value==='true':row.value.type==='number'?Number(row.value.value):row.value.value;
   if(!row.method.value||!row.sample.value)throw Error('Each entered observation needs a method, timestamp and sample identifier.');
   request.observations.push({id:row.original&&row.original.value===value&&row.original.timestamp===utc(row.timestamp)&&row.original.quality===row.quality.value&&row.original.unit===row.unitInput.value&&row.original.method===row.method.value&&row.original.sample_id===row.sample.value?row.original.id:'obs-'+crypto.randomUUID(),concept:row.concept,value,unit:row.unitInput.value,timestamp:utc(row.timestamp),quality:row.quality.value,method:row.method.value,sample_id:row.sample.value,provenance:row.original?.provenance??'SYNTHETIC_MANUAL_OBSERVATION_NOT_SENSOR_VERIFIED'});
  }
  $('scenario').value=JSON.stringify({request,mission:snapshot.mission});
 }
 const monitor=node('section');monitor.id='monitoring';monitor.append(node('h2','Measurements, monitoring and follow-up'),node('p','Synthetic research records only. Manual entries are not verified sensor readings. Calculations use the reference Python services; treatment remains blocked.'));
 $('dashboard').after(monitor);
 const sampleData=await(await fetch('./statistics-cases.json')).json(),devices=[...new Map(sampleData.flatMap(x=>x.snapshots).map(x=>[x.device.id,x.device])).values()];
 const selected=choice(monitor,'Reviewed synthetic device policy',devices.map(x=>[x.id,human(x.variable)+' · '+x.unit]));
 const measuredValue=field(monitor,'Synthetic measurement value','number'),measuredAt=field(monitor,'Measurement timestamp (UTC)','datetime-local');
 const phase=choice(monitor,'Measurement phase',[['PRE_MISSION','Before flight'],['IN_MISSION','During mission'],['POST_MISSION','After flight']]);
 const quality=choice(monitor,'Measurement quality',[['ACCEPTABLE','Acceptable technical quality'],['UNKNOWN','Unknown'],['INVALID','Invalid'],['NOT_MEASURED','Not measured']]);
 const out=node('p');out.role='status';monitor.append(out);
 const measuredList=node('div');monitor.append(measuredList);
 const run=fn=>async()=>{try{out.textContent='Working locally…';const result=await fn();await api.persist();out.textContent='Local record committed. Treatment execution remains blocked.';await update();return result;}catch(e){out.textContent=e.message;}};
 button(monitor,'Save synthetic measurement',run(async()=>{
  const device=devices.find(x=>x.id===selected.value);const missing=quality.value==='NOT_MEASURED';
  if(!missing&&measuredValue.value==='')throw Error('Enter a value or explicitly select Not measured.');
  return api.call('ingest',{device,measurement:{id:'m-'+crypto.randomUUID(),variable:device.variable,value:missing?null:Number(measuredValue.value),unit:device.unit,timestamp:utc(measuredAt),device_id:device.id,calibration_id:device.calibration_id,method:'DIRECT',protocol:'V011_SYNTHETIC_TECHNICAL_FIXTURE_NOT_A_CLINICAL_PROTOCOL',phase:phase.value,reported_quality:quality.value,synthetic:true,provenance:'SYNTHETIC_MANUAL_ENTRY_NOT_SENSOR_VERIFIED'}});
 }));
 const calcAt=field(monitor,'Calculation / cycle time (UTC)','datetime-local');
 const min=field(monitor,'Minimum baseline observations (research configuration)','number','3');min.min='1';min.step='1';
 let checked=[],baselineChecks=[];
 const separateReview=field(monitor,'Start a separate clinical presentation (do not carry previous observations)','checkbox');
 button(monitor,'Build personal research baseline',run(()=>api.call('baseline',{id:'b-'+crypto.randomUUID(),measurement_ids:checked.filter(x=>x.input.checked).map(x=>x.id),minimum_observations:Number(min.value),as_of:utc(calcAt),protocol_reference:'USER_DECLARED_RESEARCH_CONFIGURATION_NOT_CLINICALLY_VALIDATED'})));
 button(monitor,'Analyze selected measurement trend',run(()=>{const ms=checked.filter(x=>x.input.checked).map(x=>x.row);return api.call('trend',{measurement_ids:ms.map(m=>m.id),as_of:utc(calcAt),ewma_lambda:1,cusum_target:ms[0]?.value??0,cusum_allowance:0,policy_reference:'USER_DECLARED_DESCRIPTIVE_NOT_CLINICALLY_VALIDATED'});}));
 button(monitor,'Run monitoring and reassessment',run(()=>{
  sync();const s=JSON.parse($('scenario').value),as_of=utc(calcAt),prior=timeline.monitoring_run.at(-1),measurements=timeline.measurement.map(x=>x.measurement);
  const history_start=[s.request.window_start,...measurements.map(m=>m.timestamp)].sort()[0];
  return api.call('monitor',{id:'cycle-'+crypto.randomUUID(),previous_run_id:prior?.id??null,as_of,history_start,clinical_window_start:s.request.window_start,clinical_context_id:separateReview.checked?'context-'+crypto.randomUUID():(prior?.clinical_context_id??'context-'+crypto.randomUUID()),policy_reference:'BROWSER_SYNTHETIC_RESEARCH_NOT_CLINICALLY_VALIDATED',population:population.value,age_years:s.request.age_years,observations:s.request.observations,measurements:[],baseline_ids:baselineChecks.filter(x=>x.input.checked).map(x=>x.id),resource_policy:'MISSION_INVENTORY'});
 }));
 const summary=node('div');monitor.append(summary);
 const followup=node('section');followup.id='followup';followup.append(node('h2','Episodes and follow-up'),node('p','Human-reported follow-up does not establish recovery or authorize treatment. Local profile unlock does not establish clinician identity.'));
 monitor.after(followup);
 const episodeSelect=choice(followup,'Episode',[]),due=field(followup,'Follow-up due (UTC)','datetime-local'),note=field(followup,'Observation or follow-up note');
 button(followup,'Open monitoring episode',run(()=>api.call('episode_open',{id:'ep-'+crypto.randomUUID(),condition_id:route.value,finding_ids:[]})));
 button(followup,'Record follow-up plan',run(()=>api.call('followup_plan',{id:'fu-'+crypto.randomUUID(),episode_id:episodeSelect.value,due_at:utc(due),goal_description:note.value,protocol_reference:'HUMAN_RECORDED_REVIEW_PLAN_NOT_TREATMENT_AUTHORIZATION'})));
 const planSelect=choice(followup,'Follow-up plan',[]);
 button(followup,'Record completed human review',run(()=>api.call('followup_review',{plan_id:planSelect.value,completed:true,measurement_ids:[],note:note.value})));
 const followupList=node('div');followup.append(followupList);
 async function update(){
  timeline=await api.call('timeline');inventoryState.replaceChildren();for(const resource of timeline.medical_inventory.at(-1)?.resources??[])inventoryState.append(node('p',resource.label+' · '+human(resource.availability)+' · '+(resource.quantity??'Quantity unknown')+' '+(resource.unit??'')+' · Unverified human report'));checked=[];measuredList.replaceChildren();summary.replaceChildren();followupList.replaceChildren();
  for(const row of timeline.measurement){const m=row.measurement;const input=field(measuredList,human(m.variable)+' · '+String(m.value??'Not measured')+' '+m.unit+' · '+m.timestamp+' · '+human(row.ingestion_quality),'checkbox');checked.push({id:m.id,input,row:m});}
  for(const run of timeline.monitoring_run){const card=node('article');card.append(node('h3','Monitoring cycle · '+run.as_of));for(const e of run.events)card.append(node('p',human(e.state)+' · '+human(e.urgency)+' · '+human(e.kind)));button(card,'Reproduce this monitoring cycle',async()=>{try{const result=await api.call('replay_monitor',{id:run.id});out.textContent=result.matches?'Frozen cycle reproduced exactly.':'REPLAY MISMATCH — stop integration.';}catch(e){out.textContent=e.message;}});summary.append(card);}
  baselineChecks=[];for(const b of timeline.baseline){const input=field(summary,'Use personal research baseline: '+human(b.variable)+' · '+b.value+' '+b.unit+' · version '+b.version,'checkbox');baselineChecks.push({id:b.id,input});}
  for(const t of timeline.trend)summary.append(node('p','Descriptive trend · slope/day '+t.slope_per_day+' · not a diagnosis'));
  episodeSelect.replaceChildren(...timeline.episode.map(e=>{const o=node('option',human(e.condition_id)+' · '+e.id);o.value=e.id;return o;}));
  planSelect.replaceChildren(...timeline.followup.map(p=>{const o=node('option',p.goal_description+' · due '+p.due_at);o.value=p.id;return o;}));
  for(const p of timeline.followup)followupList.append(node('article','Follow-up due '+p.due_at+' · '+p.goal_description+' · '+(timeline.followup_review.some(x=>x.plan_id===p.id&&x.completed)?'Human review recorded; recovery not determined':'Review pending')));
 }
 const inventory=node('section');inventory.id='inventory';inventory.append(node('h2','Mission medical resources'),node('p','This is a human-reported synthetic inventory. Availability does not establish verification, clinical eligibility, authorization or completed treatment.'));
 followup.after(inventory);
 const resourceId=field(inventory,'Resource identifier from documented requirement'),resourceLabel=field(inventory,'Resource label'),resourceKind=choice(inventory,'Resource kind',[['EQUIPMENT','Equipment'],['MEDICATION','Medication'],['CONSUMABLE','Consumable'],['CAPABILITY','Capability']]);
 const quantity=field(inventory,'Quantity (empty means unknown)','number'),unit=field(inventory,'Quantity unit'),availability=choice(inventory,'Declared availability',[['UNKNOWN','Unknown'],['AVAILABLE','Reported available'],['UNAVAILABLE','Reported unavailable']]),effective=field(inventory,'Inventory effective time (UTC)','datetime-local');
 const inventoryState=node('div');inventory.append(inventoryState);
 button(inventory,'Record synthetic inventory version',run(async()=>{
  if(!resourceId.value||!resourceLabel.value)throw Error('Resource identifier and label are required.');const at=utc(effective),prior=timeline.medical_inventory.at(-1);
  const resources=[...(prior?.resources??[]).filter(r=>r.id!==resourceId.value),{id:resourceId.value,kind:resourceKind.value,label:resourceLabel.value,quantity:quantity.value===''?null:Number(quantity.value),unit:unit.value||null,availability:availability.value,verification:'UNVERIFIED',updated_at:at,source:'SYNTHETIC_MANUAL_INVENTORY',responsible:'LOCAL_PROFILE_SELF_REPORT',synthetic:true}];
  const row=await api.call('inventory',{id:'inventory-'+crypto.randomUUID(),version:(prior?.version??0)+1,supersedes:prior?.id??null,effective_at:at,updated_at:at,source:'SYNTHETIC_MANUAL_INVENTORY',responsible:'LOCAL_PROFILE_SELF_REPORT',resources,synthetic:true});inventoryState.textContent='Inventory version '+row.version+' recorded. Resources remain unverified.';return row;
 }));
 const context=node('section');context.id='mission-context';context.append(node('h2','Mission context'),node('p','Context versions apply from their explicit effective time. Historical committed monitoring contexts cannot be rewritten.'));
 inventory.after(context);
 const missionPhase=choice(context,'Mission phase',[['IN_MISSION','During mission'],['PRE_MISSION','Before flight'],['POST_MISSION','After flight']]),gravity=choice(context,'Gravity context',[['EARTH','Earth'],['MICROGRAVITY','Microgravity'],['PARTIAL','Partial gravity']]),contextAt=field(context,'Context effective time (UTC)','datetime-local');
 button(context,'Append mission context',run(()=>api.call('mission_context',{id:'context-'+crypto.randomUUID(),effective_at:utc(contextAt),context:{phase:missionPhase.value,gravity:gravity.value,environment:'HABITABLE_CABIN',mode:'NOMINAL'}})));
 const management=node('section');management.id='management-history';management.append(node('h2','Documented management and human reports'),node('p','A proposal or unverified report is not an authorized order or proof that treatment occurred. ASTHRAL does not prescribe, dispense or execute treatment.'));
 context.after(management);
 const managementEpisode=choice(management,'Related monitoring episode',[]),managementEvaluation=choice(management,'Frozen monitoring assessment',[]),intervention=choice(management,'Documented intervention reference',[]);
 const reportStatus=choice(management,'Report classification',[['DOCUMENTED','Documentary reference only'],['PROPOSED','Proposed, not authorized'],['REVIEW_PENDING','Awaiting human review'],['HUMAN_REPORTED_PERFORMED','Human report: performed (unverified)'],['POST_INTERVENTION_OBSERVATION','Reported observation after an intervention']]);
 const occurred=field(management,'Reported event time (UTC)','datetime-local'),managementNote=field(management,'Report note (synthetic only)');const managementList=node('div');management.append(managementList);
 function selectInterventions(){const ep=timeline?.episode.find(e=>e.id===managementEpisode.value),ev=timeline?.clinical_evaluation.find(e=>e.id===managementEvaluation.value);intervention.replaceChildren(...(ev?.management?.[ep?.condition_id]?.interventions??[]).map(doc=>{const option=node('option',human(doc.title));option.value=doc.id;return option;}));}
 function selectManagementAssessments(){const ep=timeline?.episode.find(e=>e.id===managementEpisode.value);managementEvaluation.replaceChildren(...(timeline?.clinical_evaluation??[]).filter(e=>ep&&e.results[ep.condition_id]).map(e=>{const option=node('option',human(ep.condition_id)+' · '+e.snapshot.request.as_of);option.value=e.id;return option;}));selectInterventions();}
 managementEpisode.onchange=selectManagementAssessments;managementEvaluation.onchange=selectInterventions;
 button(management,'Record unverified management report',run(()=>api.call('management_record',{id:'management-'+crypto.randomUUID(),episode_id:managementEpisode.value,evaluation_id:managementEvaluation.value,intervention_id:intervention.value,status:reportStatus.value,occurred_at:utc(occurred),recorded_at:new Date().toISOString(),source:'SYNTHETIC_LOCAL_PROFILE_SELF_REPORT',reported_authority:'UNVERIFIED_SELF_REPORT_NO_AUTHORIZATION',note:managementNote.value,synthetic:true})));
 const originalUpdate=update;
 update=async function(){await originalUpdate();managementEpisode.replaceChildren(...timeline.episode.map(e=>{const option=node('option',human(e.condition_id));option.value=e.id;return option;}));selectManagementAssessments();managementList.replaceChildren(...timeline.management_record.map(r=>node('article',human(r.status)+' · '+r.note+' · Authority not verified; execution by ASTHRAL: no; efficacy not verified.')));};
 const nav=$('workspace').querySelector('nav');for(const [id,text] of [['monitoring','Monitoring'],['followup','Follow-up'],['voice','Record observation'],['inventory','Resources'],['mission-context','Mission'],['management-history','Management reports']]){const a=node('a',text);a.href='#'+id;nav.append(a);}
 return {refresh, sync, update,clear(){rows=[];timeline=null;snapshot=null;out.textContent='';for(const section of [monitor,inventory,context,management])for(const select of section.querySelectorAll('select'))select.selectedIndex=0;for(const input of form.querySelectorAll('input'))input.value='';population.value='UNKNOWN';observations.replaceChildren();measuredList.replaceChildren();summary.replaceChildren();followupList.replaceChildren();episodeSelect.replaceChildren();planSelect.replaceChildren();for(const input of monitor.querySelectorAll('input'))input.value='';note.value='';due.value='';inventoryState.replaceChildren();for(const input of inventory.querySelectorAll('input'))input.value='';contextAt.value='';managementList.replaceChildren();managementEpisode.replaceChildren();managementEvaluation.replaceChildren();intervention.replaceChildren();managementNote.value='';occurred.value='';}};
}
