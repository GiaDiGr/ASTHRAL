// View initialization only. Clinical decisions remain exclusively in the Python worker.
export function initialClinicalInput(evaluations,owner){
 const latest=evaluations.at(-1);
 if(latest){
  const snapshot=latest.snapshot;
  if(latest.subject_id!==owner||snapshot.request.subject_id!==owner||snapshot.request.mission_id!=='browser-mission'||snapshot.mission.id!=='browser-mission')throw Error('SAVED_CLINICAL_INPUT_SCOPE_MISMATCH');
  return structuredClone({request:snapshot.request,mission:snapshot.mission});
 }
 return {request:{subject_id:owner,mission_id:'browser-mission',condition_id:'DM',presentation_id:null,population:'UNKNOWN',age_years:null,as_of:null,window_start:null,observations:[],measurement_bindings:[],resources:{},resource_policy:'MISSION_INVENTORY'},mission:{id:'browser-mission',phase:'IN_MISSION',gravity:'EARTH',environment:'HABITABLE_CABIN',mode:'NOMINAL',synthetic:true}};
}

export function criterionInputConcepts(logic,derivations,supported){
 const available=new Set(supported),found=new Set();
 const add=name=>{if(available.has(name))found.add(name);else for(const input of derivations[name]??[])if(available.has(input))found.add(input);};
 const visit=value=>{if(Array.isArray(value)){value.forEach(visit);return;}if(!value||typeof value!=='object')return;if(value.field)add(value.field);if(value.derived_field)add(value.derived_field);Object.values(value).forEach(visit);};
 visit(logic);return [...found];
}
