/* In-memory training controls. Values and boundaries are illustrative software
 * fixtures, not mission limits, clinical criteria, or sensor readings. */
export const SIMULATION_VERSION='training-fixture-1';
export const ATMOSPHERE_TRAINING_VERSION='atmosphere-training-fixture-1';
export const ATMOSPHERE_TRAINING_BOUNDS=Object.freeze({low_kpa:10,high_kpa:40});
export const PARAMETERS=Object.freeze([
 {id:'heart_rate',label:'Heart rate',unit:'bpm',min:40,max:180,step:1,initial:72,warning:120,direction:'above'},
 {id:'spo2',label:'Oxygen saturation',unit:'%',min:70,max:100,step:1,initial:98,warning:90,direction:'below'},
 {id:'respiratory_rate',label:'Respiratory rate',unit:'breaths/min',min:4,max:40,step:1,initial:16},
 {id:'systolic',label:'Systolic pressure',unit:'mmHg',min:60,max:200,step:1,initial:120},
 {id:'diastolic',label:'Diastolic pressure',unit:'mmHg',min:30,max:130,step:1,initial:80},
 {id:'temperature',label:'Body temperature',unit:'°C',min:34,max:41,step:.1,initial:36.8},
 {id:'glucose',label:'Blood glucose',unit:'mg/dL',min:40,max:300,step:1,initial:100},
 {id:'etco2',label:'End-tidal CO₂',unit:'mmHg',min:10,max:70,step:1,initial:38},
]);
export const initialSimulation=()=>Object.fromEntries(PARAMETERS.map(p=>[p.id,p.initial]));
export const TRAINING_PRESETS=Object.freeze({
 'Nominal monitoring':{},'Elevated heart rate':{heart_rate:130},'Reduced oxygen saturation':{spo2:88},
 'Blood pressure scenario':{systolic:155,diastolic:95},'Temperature scenario':{temperature:38.5},
 'Glucose scenario':{glucose:180},'End-tidal CO₂ scenario':{etco2:50},
 'Combined training scenario':{heart_rate:130,spo2:88,respiratory_rate:24},'Recovery scenario':{heart_rate:80,spo2:97},
});
export function evaluateTraining(id,value){
 const p=PARAMETERS.find(x=>x.id===id);
 if(!p||!Number.isFinite(value)||value<p.min||value>p.max)throw Error('Invalid simulation input');
 const active=p.warning!==undefined&&(p.direction==='above'?value>p.warning:value<p.warning);
 return {parameter:id,value,unit:p.unit,category:active?'TRAINING_WARNING':'NO_CONFIGURED_WARNING',rule:active?`${p.direction} ${p.warning} ${p.unit}`:'No training warning triggered',version:SIMULATION_VERSION,synthetic:true,clinical_authority:false};
}
export function oxygenPartialPressure(totalKpa,oxygenPercent){
 if(!Number.isFinite(totalKpa)||!Number.isFinite(oxygenPercent)||totalKpa<0||oxygenPercent<0||oxygenPercent>100)throw Error('Invalid synthetic atmosphere');
 return totalKpa*oxygenPercent/100;
}
export function evaluateAtmosphereTraining(environment,totalKpa,oxygenPercent){
 const labels={cabin:'Cabin',spacesuit:'Spacesuit'};
 if(!Object.hasOwn(labels,environment))throw Error('Unknown atmosphere fixture');
 const result={parameter:`${environment}_oxygen_partial_pressure`,label:`${labels[environment]} oxygen partial pressure`,unit:'kPa',version:ATMOSPHERE_TRAINING_VERSION,synthetic:true,clinical_authority:false};
 if(totalKpa===null||totalKpa===undefined||totalKpa===''||oxygenPercent===null||oxygenPercent===undefined||oxygenPercent==='')return {...result,value:null,category:'TRAINING_DATA_INSUFFICIENT',status:'TRAINING_DATA_INSUFFICIENT',rule:'Total pressure and oxygen fraction are both required to calculate dry-gas oxygen partial pressure.'};
 if(!Number.isFinite(Number(totalKpa))||!Number.isFinite(Number(oxygenPercent))||Number(totalKpa)<0||Number(totalKpa)>200||Number(oxygenPercent)<0||Number(oxygenPercent)>100)return {...result,value:null,category:'TRAINING_INPUT_INVALID',status:'TRAINING_INPUT_INVALID',rule:'Inputs must stay within the declared software-fixture bounds (0–200 kPa and 0–100% O₂).'};
 const partialPressure=oxygenPartialPressure(Number(totalKpa),Number(oxygenPercent)),value=Number(partialPressure.toFixed(2));
 if(partialPressure<ATMOSPHERE_TRAINING_BOUNDS.low_kpa)return {...result,value,category:'TRAINING_WARNING',status:'TRAINING_WARNING_LOW',rule:`calculated dry-gas oxygen partial pressure below ${ATMOSPHERE_TRAINING_BOUNDS.low_kpa} kPa`};
 if(partialPressure>ATMOSPHERE_TRAINING_BOUNDS.high_kpa)return {...result,value,category:'TRAINING_WARNING',status:'TRAINING_WARNING_HIGH',rule:`calculated dry-gas oxygen partial pressure above ${ATMOSPHERE_TRAINING_BOUNDS.high_kpa} kPa`};
 return {...result,value,category:'NO_CONFIGURED_WARNING',status:'NO_CONFIGURED_WARNING',rule:'No atmospheric training boundary crossed'};
}

export function drawSyntheticEcg(canvas,heartRate){
 if(!canvas||!Number.isFinite(heartRate)||heartRate<=0)return;
 const ctx=canvas.getContext('2d');if(!ctx)return;
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.strokeStyle='#4fe5d0';ctx.lineWidth=2;ctx.beginPath();
 const period=60/heartRate;
 for(let x=0;x<canvas.width;x++){
  const phase=(x/canvas.width*6/period)%1;
  const peak=Math.exp(-Math.pow((phase-.21)/.018,2))*-42+Math.exp(-Math.pow((phase-.27)/.025,2))*14+Math.exp(-Math.pow((phase-.48)/.09,2))*-7;
  const y=canvas.height*.54+peak;x?ctx.lineTo(x,y):ctx.moveTo(x,y);
 }
 ctx.stroke();
}

function emitAtmosphereTransition(previous,current){
 if(previous==='UNKNOWN')return;
 if(previous===current.status){if(current.status!=='NO_CONFIGURED_WARNING')window.dispatchEvent(new CustomEvent('asthral:simulation-value-update',{detail:{...current,active:true}}));return;}
 const active=current.status!=='NO_CONFIGURED_WARNING';
 window.dispatchEvent(new CustomEvent('asthral:simulation-transition',{detail:{
  parameter:current.parameter,label:current.label,value:current.value??'unknown',unit:current.unit,category:active?'TRAINING_WARNING':current.status,
  rule:current.rule,version:current.version,synthetic:true,clinical_authority:false,active,observed_at:new Date().toISOString(),
  context:'Atmospheric software fixture. Not life-support telemetry or an operational safety assessment.'
 }}));
}

export function mountPhysiologySimulator(parent){
 const root=document.createElement('section');root.className='phys-simulator';root.id='physiology-simulator';
 const title=document.createElement('h2');title.textContent='Interactive physiological simulation';
 const modeButton=document.createElement('button');modeButton.type='button';modeButton.textContent='Enter Synthetic Test Mode';modeButton.setAttribute('aria-expanded','false');
 const content=document.createElement('div');content.hidden=true;
 const notice=document.createElement('p');notice.className='phys-simulator-notice';notice.textContent='SYNTHETIC TEST MODE — NOT LIVE MEDICAL DATA. Training boundaries are illustrative, not NASA limits or diagnoses. Values remain in memory and are not saved to health records.';
 const signal=document.createElement('canvas');signal.width=900;signal.height=120;signal.hidden=true;signal.setAttribute('aria-label','Synthetic ECG-style demonstration waveform, not an ECG recording');
 const caption=document.createElement('p');caption.textContent='Synthetic ECG-style demonstration waveform · rate-driven illustration, not a clinical ECG';
 const cards=document.createElement('div');cards.className='phys-simulator-grid';
 const events=document.createElement('div');events.className='phys-simulation-events';
 const reset=document.createElement('button');reset.type='button';reset.textContent='Reset simulation';
 const presetLabel=document.createElement('label');presetLabel.textContent='Synthetic training scenario';const preset=document.createElement('select');preset.setAttribute('aria-label','Synthetic training scenario');for(const name of Object.keys(TRAINING_PRESETS))preset.append(new Option(name,name));presetLabel.append(preset);
 const atmosphere=document.createElement('section');atmosphere.className='phys-atmosphere';const atmosphereHeading=document.createElement('h3');atmosphereHeading.textContent='Cabin and spacesuit atmosphere · synthetic';const explanation=document.createElement('p');explanation.textContent='Dry-gas oxygen partial pressure = total pressure × oxygen fraction. This simplified calculation is not inspired oxygen pressure, SpO₂, life-support telemetry or an operational safety assessment.';atmosphere.append(atmosphereHeading,explanation);
 const atmosphereInputs=[];const atmosphereStates=new Map();
 const atmosphereDefinitions=[
  {id:'cabin',label:'Cabin',pressure:101.3,oxygen:21,context:'Spacecraft cabin synthetic atmosphere.'},
  {id:'spacesuit',label:'Spacesuit',pressure:29.6,oxygen:100,context:'Spacesuit synthetic atmosphere; no EVA telemetry is available.'},
 ];
 for(const definition of atmosphereDefinitions){
  const panel=document.createElement('fieldset');panel.className=`phys-atmosphere-panel phys-atmosphere-${definition.id}`;panel.dataset.environment=definition.id;
  const legend=document.createElement('legend');legend.textContent=`${definition.label} atmosphere`;panel.append(legend);
  const pressureLabel=document.createElement('label');pressureLabel.textContent=`${definition.label} total pressure (kPa)`;
  const pressure=document.createElement('input');pressure.type='number';pressure.min='0';pressure.max='200';pressure.step='0.1';pressure.value=definition.pressure;pressure.setAttribute('aria-label',`${definition.label} total pressure (kPa)`);pressureLabel.append(pressure);
  const oxygenLabel=document.createElement('label');oxygenLabel.textContent=`${definition.label} O₂ Concentration (%)`;
  const oxygen=document.createElement('input');oxygen.type='range';oxygen.min='0';oxygen.max='100';oxygen.step='0.1';oxygen.value=definition.oxygen;oxygen.setAttribute('aria-label',`${definition.label} O₂ Concentration (%)`);
  const oxygenValue=document.createElement('output');oxygenValue.textContent=`${definition.oxygen.toFixed(1)}%`;oxygenLabel.append(oxygen,oxygenValue);
  const result=document.createElement('div');result.className='phys-atmosphere-results';
  const concentration=document.createElement('p'),total=document.createElement('p'),partial=document.createElement('p'),co2=document.createElement('p'),reserve=document.createElement('p'),context=document.createElement('small');
  result.append(concentration,total,partial,co2,reserve,context);panel.append(pressureLabel,oxygenLabel,result);atmosphere.append(panel);
  const state={status:'UNKNOWN',value:null};atmosphereStates.set(definition.id,state);atmosphereInputs.push({definition,pressure,oxygen,oxygenValue,result,concentration,total,partial,co2,reserve,context});
 }
 const bounds=document.createElement('p');bounds.className='phys-atmosphere-boundary';bounds.textContent=`Illustrative software-only training boundaries for both dry-gas partial pressures: below ${ATMOSPHERE_TRAINING_BOUNDS.low_kpa} kPa or above ${ATMOSPHERE_TRAINING_BOUNDS.high_kpa} kPa (${ATMOSPHERE_TRAINING_VERSION}). These are not NASA operational limits, crew safety criteria or clinical thresholds.`;atmosphere.append(bounds);
 const source=document.createElement('a');source.href='https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-003-habitable-atmosphere.pdf';source.target='_blank';source.rel='noopener noreferrer';source.textContent='NASA reference · habitable atmosphere and inspired oxygen';atmosphere.append(source);
 content.append(notice,presetLabel,signal,caption,cards,events,reset,atmosphere);root.append(title,modeButton,content);parent.prepend(root);
 const headerIndicator=document.createElement('span');headerIndicator.className='synthetic-mode-indicator';headerIndicator.textContent='SYNTHETIC TEST MODE — NOT LIVE MEDICAL DATA';headerIndicator.hidden=true;headerIndicator.setAttribute('role','status');headerIndicator.setAttribute('aria-live','polite');document.querySelector('.site-header')?.append(headerIndicator);
 let state=initialSimulation();const inputs=new Map(),values=new Map(),flags=new Map();let modeActive=false;
 function showAtmosphereState(previous,next){
  if(next.status==='NO_CONFIGURED_WARNING'){
   if(previous!=='UNKNOWN'&&previous!=='NO_CONFIGURED_WARNING')events.textContent=`Simulation warning cleared for ${next.label}; this does not establish atmospheric safety.`;
  }else events.textContent=`SIMULATION WARNING · ${next.label}: ${next.value??'unknown'} ${next.unit} · ${next.rule} · illustrative rule ${next.version}. No life-support telemetry or safety conclusion is available.`;
 }
 function renderAtmosphere(entry){
  const {definition,pressure,oxygen,oxygenValue,concentration,total,partial,co2,reserve,context}=entry;
  oxygenValue.textContent=`${Number(oxygen.value).toFixed(1)}%`;
  const pressureValue=pressure.value===''?NaN:Number(pressure.value),oxygenValueNumber=oxygen.value===''?NaN:Number(oxygen.value);
  const assessment=evaluateAtmosphereTraining(definition.id,pressure.value===''?null:pressureValue,oxygen.value===''?null:oxygenValueNumber);
  if(assessment.category==='TRAINING_DATA_INSUFFICIENT'||assessment.category==='TRAINING_INPUT_INVALID'){
   concentration.textContent=`${definition.label} O₂ concentration: ${oxygen.value===''?'not entered':oxygen.value+'%'}`;
   total.textContent=`${definition.label} total pressure: ${pressure.value===''?'not entered':pressure.value+' kPa'}`;
   partial.textContent=assessment.category==='TRAINING_DATA_INSUFFICIENT'?'Calculated oxygen partial pressure: insufficient information':`Atmosphere input invalid: ${assessment.rule}`;
   co2.textContent='CO₂ concentration / partial pressure: not measured or configured.';
   reserve.textContent=definition.id==='spacesuit'?'Oxygen reserve / supply status: not instrumented.' : 'Cabin supply telemetry: not available.';
   context.textContent=definition.context+' No atmospheric safety conclusion is available.';
   const next={...assessment};
   const previous=atmosphereStates.get(definition.id);atmosphereStates.set(definition.id,next);showAtmosphereState(previous.status,next);emitAtmosphereTransition(previous.status,next);return;
  }
  const pp=oxygenPartialPressure(pressureValue,oxygenValueNumber),rounded=Number(pp.toFixed(2));
  concentration.textContent=`${definition.label} O₂ concentration: ${oxygenValueNumber.toFixed(1)}%`;
  total.textContent=`${definition.label} total pressure: ${pressureValue.toFixed(1)} kPa`;
  partial.textContent=`Calculated dry-gas O₂ partial pressure: ${rounded.toFixed(2)} kPa · synthetic`;
  co2.textContent='CO₂ concentration / partial pressure: not measured or configured.';
  reserve.textContent=definition.id==='spacesuit'?'Oxygen reserve / supply status: not instrumented.':'Cabin supply telemetry: not available.';
  context.textContent=`${definition.context} Illustrative scenario only; independent of astronaut SpO₂.`;
  const next={...assessment,value:rounded};
  const previous=atmosphereStates.get(definition.id);atmosphereStates.set(definition.id,next);showAtmosphereState(previous.status,next);emitAtmosphereTransition(previous.status,next);
 }
 for(const entry of atmosphereInputs){entry.pressure.addEventListener('input',()=>renderAtmosphere(entry));entry.oxygen.addEventListener('input',()=>renderAtmosphere(entry));renderAtmosphere(entry);}
 const atmosphereReset=atmosphereInputs.flatMap(({pressure,oxygen})=>[[pressure,pressure.value],[oxygen,oxygen.value]]);
 function draw(){drawSyntheticEcg(signal,state.heart_rate);window.dispatchEvent(new CustomEvent('asthral:simulation-values',{detail:{active:modeActive,heart_rate:state.heart_rate,values:{...state}}}));}
 function set(p,value){state[p.id]=value;values.get(p.id).textContent=`${value} ${p.unit}`;const result=evaluateTraining(p.id,value);const prior=flags.get(p.id)||false;const active=result.category==='TRAINING_WARNING';flags.set(p.id,active);inputs.get(p.id).closest('article').dataset.trainingWarning=String(active);if(active!==prior){events.textContent=active?`SIMULATION WARNING · ${p.label}: ${value} ${p.unit} is ${result.rule} in training rule ${result.version}. Review the simulated context; no cause or treatment is inferred.`:`Simulation warning cleared for ${p.label}; this does not establish clinical recovery.`;window.dispatchEvent(new CustomEvent('asthral:simulation-transition',{detail:{...result,label:p.label,active,observed_at:new Date().toISOString()}}));}else if(active){window.dispatchEvent(new CustomEvent('asthral:simulation-value-update',{detail:{...result,label:p.label,active:true}}));}draw();}
 for(const p of PARAMETERS){const card=document.createElement('article'),label=document.createElement('label'),output=document.createElement('output'),input=document.createElement('input');label.textContent=p.label;input.type='range';input.min=p.min;input.max=p.max;input.step=p.step;input.value=p.initial;input.setAttribute('aria-label',p.label+' simulation');output.textContent=`${p.initial} ${p.unit}`;label.append(output,input);card.append(label);cards.append(card);inputs.set(p.id,input);values.set(p.id,output);input.addEventListener('input',()=>set(p,Number(input.value)));}
 preset.addEventListener('change',()=>{const next={...initialSimulation(),...TRAINING_PRESETS[preset.value]};for(const p of PARAMETERS){inputs.get(p.id).value=next[p.id];set(p,next[p.id]);}});
 reset.addEventListener('click',()=>{state=initialSimulation();flags.clear();preset.value='Nominal monitoring';for(const p of PARAMETERS){inputs.get(p.id).value=state[p.id];values.get(p.id).textContent=`${state[p.id]} ${p.unit}`;inputs.get(p.id).closest('article').dataset.trainingWarning='false';}for(const [input,value] of atmosphereReset){input.value=value;input.dispatchEvent(new Event('input'));}for(const entry of atmosphereInputs)renderAtmosphere(entry);events.textContent='Simulation reset. No health records were changed.';window.dispatchEvent(new CustomEvent('asthral:simulation-reset'));draw();});
 function setMode(active){modeActive=active;content.hidden=!active;signal.hidden=!active;modeButton.textContent=active?'Exit Synthetic Test Mode':'Enter Synthetic Test Mode';modeButton.setAttribute('aria-expanded',String(active));headerIndicator.hidden=!active;window.dispatchEvent(new CustomEvent('asthral:simulation-mode',{detail:{active,version:SIMULATION_VERSION,synthetic:true}}));draw();}
 modeButton.addEventListener('click',()=>{if(modeActive){reset.click();setMode(false);}else{setMode(true);}});
 draw();return {clear(){if(modeActive)reset.click();else{for(const entry of atmosphereInputs)renderAtmosphere(entry);}setMode(false);}};
}
