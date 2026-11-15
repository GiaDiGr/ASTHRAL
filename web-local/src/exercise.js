export const EXERCISE_PLANS = Object.freeze([
  {id:'mobility-basics',title:'Mobility movement examples',workout_type:'MOBILITY',objective:'Practice controlled, comfortable range-of-motion movements.',precautions:'Generic educational examples only. Follow mission medical restrictions and stop if symptoms or pain occur. No individualized clearance or prescription is provided.',activities:[
    {id:'seated-shoulder-range',name:'Seated shoulder range',setup:'Sit with feet supported and shoulders relaxed.',instructions:'Slowly raise the arms only through a comfortable range, then return them to rest. Avoid forcing the end range.',phases:['Arms at rest, shoulders relaxed','Raise both arms within a comfortable range','Lower arms back to rest'],tracking:'Optional sets and repetitions; enter only what you actually completed.'},
    {id:'ankle-circles',name:'Ankle circles',setup:'Sit securely with one foot supported or comfortably lifted.',instructions:'Move the ankle gently through a small circular path, then change direction. Keep the movement comfortable.',phases:['Support the lower leg comfortably','Draw small circles with the foot in one direction','Change direction without forcing the range'],tracking:'Optional time or repetitions.'},
    {id:'seated-trunk-turn',name:'Seated trunk turn',setup:'Sit upright with feet stable and hands resting on thighs.',instructions:'Turn the trunk gently to one side without bouncing, return to center, and repeat on the other side.',phases:['Sit centered with feet stable','Turn gently to one side without bouncing','Return to center and repeat toward the other side'],tracking:'Optional sets and repetitions.'}
  ]},
  {id:'resistance-examples',title:'Resistance movement examples',workout_type:'RESISTANCE',objective:'Review simple bodyweight movement patterns and record a self-selected session.',precautions:'No resistance, repetitions, intensity, or progression is prescribed. Use only activities cleared for the individual and mission; a chair or support should be stable.',activities:[
    {id:'sit-to-stand',name:'Supported sit-to-stand',setup:'Use a stable chair placed against a fixed surface; keep an accessible support nearby.',instructions:'From sitting, lean forward as comfortable, stand using the support available, then sit down with control. Do not continue if balance or symptoms are concerning.',phases:['Begin seated with stable support available','Lean forward as comfortable and stand using support','Sit down again with control'],tracking:'Record completed sets and repetitions only if applicable.'},
    {id:'wall-push',name:'Wall push movement',setup:'Stand facing a fixed wall at a comfortable reach; feet remain planted.',instructions:'Place hands on the wall, bend the elbows to move the chest slightly toward it, then press back. Keep the range comfortable.',phases:['Place hands on wall with feet planted','Bend elbows and move slightly toward wall','Press back to the starting position'],tracking:'Record completed sets and repetitions only if applicable.'},
    {id:'seated-knee-extension',name:'Seated knee extension',setup:'Sit with back supported and feet near the floor.',instructions:'Straighten one knee within a comfortable range, pause if comfortable, lower the foot, and alternate sides.',phases:['Sit with back supported and knee bent','Straighten one knee within comfortable range','Lower the foot and alternate sides'],tracking:'Record completed sets and repetitions only if applicable.'}
  ]},
  {id:'aerobic-examples',title:'Aerobic activity examples',workout_type:'AEROBIC',objective:'Describe and time a user-selected aerobic activity.',precautions:'No duration or exertion target is prescribed. Use a previously authorized activity and stop according to personal and mission guidance.',activities:[
    {id:'walk-logged',name:'Walking or locomotion activity',setup:'Use an area and method already approved for the user.',instructions:'Record the activity and elapsed time manually. ASTHRAL does not verify pace, distance, workload, or physiological response.',phases:['Select an activity already authorized for you','Perform it according to your existing plan','Record only the time/workload you actually observed'],tracking:'Elapsed seconds and optional user-entered workload note.'},
    {id:'stationary-march',name:'Stationary marching example',setup:'Stand near a stable support; a seated alternative may be selected by the user if already approved.',instructions:'Alternate lifting each foot in a comfortable rhythm. Keep support accessible and do not treat the timer as an intensity target.',phases:['Stand near stable support or use an already-approved seated position','Alternate lifting one foot at a time comfortably','Pause or stop if needed; record only observed time'],tracking:'Elapsed seconds and optional user-entered workload note.'}
  ]},
  {id:'coordination-examples',title:'Coordination and balance examples',workout_type:'BALANCE',objective:'Review low-complexity coordination examples with stable support.',precautions:'Balance activity can cause falls. Use a stable hand support and another person if required by mission guidance; do not close eyes or remove support for this demo.',activities:[
    {id:'supported-weight-shift',name:'Supported weight shift',setup:'Stand holding a stable support with both feet comfortably apart.',instructions:'Shift weight slightly from one foot toward the other while maintaining hand support. Return to center between movements.',phases:['Stand with both feet supported and hands holding a stable surface','Shift weight slightly toward one foot','Return to center before changing sides'],tracking:'Record only the time or repetitions actually completed.'},
    {id:'seated-alternation',name:'Seated alternating reach',setup:'Sit securely with both feet supported and objects removed from fall range.',instructions:'Reach one hand toward a nearby target within comfortable range, return, then alternate. Do not reach beyond stable balance.',phases:['Sit securely with both feet supported','Reach one hand toward a nearby target within comfortable range','Return to center and alternate hands'],tracking:'Record completed sets and repetitions only if applicable.'}
  ]}
]);

export function sessionElapsed(session, now=Date.now()){
  const accumulated=Number.isFinite(session?.elapsed_seconds)?session.elapsed_seconds:0;
  if(session?.status!=='IN_PROGRESS'||!session?.segment_started_at)return accumulated;
  const then=Date.parse(session.segment_started_at);
  return Number.isFinite(then)?accumulated+Math.max(0,Math.floor((now-then)/1000)):accumulated;
}

export function pauseSession(session, at=new Date().toISOString()){
  return {...session,status:'PAUSED',elapsed_seconds:sessionElapsed(session,Date.parse(at)),segment_started_at:null,updated_at:at};
}

export function resumeSession(session, at=new Date().toISOString()){
  if(!['PAUSED','IN_PROGRESS'].includes(session.status))throw new Error('Only paused or in-progress sessions can be resumed.');
  return {...session,status:'IN_PROGRESS',segment_started_at:at,updated_at:at};
}

export function validatePerceivedExertion(value){
 if(value===null||value===undefined||value==='')return null;
 const score=Number(value);if(!Number.isInteger(score)||score<0||score>10)throw new Error('Perceived exertion must be a whole number from 0 to 10.');return score;
}

export function sleepInterval(start,end){
  if(typeof start!=='string'||typeof end!=='string'||!/(?:Z|[+-]\d{2}:\d{2})$/i.test(start)||!/(?:Z|[+-]\d{2}:\d{2})$/i.test(end))throw new Error('Sleep timestamps must include a timezone-qualified offset.');
  const a=Date.parse(start),b=Date.parse(end);
  if(!Number.isFinite(a)||!Number.isFinite(b)||b<=a||b-a>24*60*60*1000)throw new Error('Sleep times must be valid, ordered, timezone-qualified, and no more than 24 hours apart.');
  return Math.round((b-a)/60000);
}

export function dailySeries(rows,entryType,selectValue){
  return rows.filter(row=>row.entry_type===entryType&&selectValue(row)!==null&&selectValue(row)!==undefined)
    .map(row=>({date:row.occurred_at.slice(0,10),value:selectValue(row),source:row.synthetic_data?'SYNTHETIC_FIXTURE':row.source}))
    .sort((a,b)=>a.date.localeCompare(b.date));
}

export function dailySumSeries(rows,entryType,selectValue){
 const days=new Map();for(const row of rows.filter(x=>x.entry_type===entryType&&selectValue(x)!==null&&selectValue(x)!==undefined)){const date=row.occurred_at.slice(0,10),day=days.get(date)||{date,value:0,entries:0,synthetic_entries:0,self_reported_entries:0};day.value+=selectValue(row);day.entries++;if(row.synthetic_data)day.synthetic_entries++;else day.self_reported_entries++;days.set(date,day);}
 return [...days.values()].sort((a,b)=>a.date.localeCompare(b.date)).map(day=>({...day,value:Math.round(day.value*1000)/1000,source:day.synthetic_entries&&day.self_reported_entries?'MIXED_PROVENANCE':day.synthetic_entries?'SYNTHETIC_FIXTURE':'SELF_REPORTED'}));
}

export function exerciseSummary(rows){
  const byId=new Map();
  for(const row of rows){const session=row.training_session;if(!session?.session_id)continue;const old=byId.get(session.session_id);if(!old||old.occurred_at<row.occurred_at)byId.set(session.session_id,row);}
  const sessions=[...byId.values()].sort((a,b)=>a.occurred_at.localeCompare(b.occurred_at));
  const completed=sessions.filter(row=>row.training_session.status==='COMPLETED');
  return {sessions,started:sessions.length,completed:completed.length,completion_rate:sessions.length?completed.length/sessions.length:null,
    completed_seconds:completed.reduce((sum,row)=>sum+(row.training_session.elapsed_seconds||0),0),
    scope:'Descriptive completion fraction among sessions started; no schedule, adherence target, fitness result, or clinical interpretation.'};
}

export function dailyMealTotals(rows){
 const nutrients=['energy_kcal','protein_g','carbohydrate_g','fat_g','water_g'],days=new Map();
 for(const row of rows.filter(x=>x.entry_type==='MEAL_NOTE'&&x.food_id&&x.nutrient_estimate)){
  const date=row.occurred_at.slice(0,10);let day=days.get(date);if(!day){day={date,entries:0,synthetic_entries:0,self_reported_entries:0,nutrients:Object.fromEntries(nutrients.map(key=>[key,{known_sum:0,known_entries:0,missing_entries:0}]))};days.set(date,day);}day.entries++;if(row.synthetic_data)day.synthetic_entries++;else day.self_reported_entries++;
  for(const key of nutrients){const value=row.nutrient_estimate[key],item=day.nutrients[key];if(value===null||value===undefined)item.missing_entries++;else{item.known_sum+=value;item.known_entries++;}}
 }
 return [...days.values()].sort((a,b)=>a.date.localeCompare(b.date)).map(day=>({
  ...day,source:day.synthetic_entries&&day.self_reported_entries?'MIXED_PROVENANCE':day.synthetic_entries?'SYNTHETIC_FIXTURE':'SELF_REPORTED',nutrients:Object.fromEntries(Object.entries(day.nutrients).map(([key,item])=>[key,{...item,complete_estimated_total:item.missing_entries===0?Math.round(item.known_sum*1000)/1000:null}]))
 }));
}
