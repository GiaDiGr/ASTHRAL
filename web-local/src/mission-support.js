import {DONKI_API,fetchDonki,DONKI_HISTORICAL_FIXTURE,cacheDonki,cachedDonkiSnapshot} from './space-weather.js';
import {normalizeSourceRegistry} from './research-sources.js';

const $=id=>document.getElementById(id);
const el=(tag,text='')=>{const node=document.createElement(tag);node.textContent=text;return node;};
const uuid=prefix=>prefix+'-'+crypto.randomUUID();
const nowLocal=()=>new Date().toISOString().slice(0,16);
const utc=value=>{if(!value)throw Error('Choose a timestamp.');const date=new Date(value);if(!Number.isFinite(date.getTime()))throw Error('Enter a valid timestamp.');return date.toISOString();};
const rateKinds=['ABSORBED_DOSE_RATE','DOSE_EQUIVALENT_RATE'];
const units={ABSORBED_DOSE:['Gy','mGy','uGy','rad'],CUMULATIVE_ABSORBED_DOSE:['Gy','mGy','uGy','rad'],ABSORBED_DOSE_RATE:['Gy/h','mGy/h','uGy/h','rad/h'],DOSE_EQUIVALENT:['Sv','mSv','uSv','rem'],DOSE_EQUIVALENT_RATE:['Sv/h','mSv/h','uSv/h','rem/h'],EFFECTIVE_DOSE:['Sv','mSv','uSv','rem']};
const quantityLabels={ABSORBED_DOSE:'Absorbed dose',CUMULATIVE_ABSORBED_DOSE:'Cumulative absorbed-dose counter',ABSORBED_DOSE_RATE:'Absorbed-dose rate',DOSE_EQUIVALENT:'Dose equivalent',DOSE_EQUIVALENT_RATE:'Dose-equivalent rate',EFFECTIVE_DOSE:'Effective-dose estimate'};

function input(parent,label,type='text',options={}){
 const wrapper=el('label',label),field=document.createElement(type==='select'?'select':'input');
 if(type==='select')for(const [value,text] of options.choices??[]){const option=el('option',text);option.value=value;field.append(option);}
 else field.type=type;
 field.setAttribute('aria-label',label);if(type==='number')field.step='any';if(options.required)field.required=true;if(options.maxLength)field.maxLength=options.maxLength;if(options.placeholder)field.placeholder=options.placeholder;if(options.value!==undefined)field.value=options.value;
 wrapper.append(field);parent.append(wrapper);return field;
}
function button(parent,text,handler){const control=el('button',text);control.type='button';control.addEventListener('click',event=>{event.preventDefault();Promise.resolve(handler()).catch(error=>{const status=parent.querySelector('[role="status"]');if(status)status.textContent=error.message;});});parent.append(control);return control;}
function makeSection(id,title,kicker,intro){const section=el('section');section.id=id;section.className='workspace-page mission-support-page';section.hidden=true;const header=el('div');header.className='page-intro';header.append(el('p',kicker),el('h1',title),el('p',intro));section.append(header);return section;}
function addView(id,label){const menu=$('workspace-nav')?.querySelector('.more-nav>div');if(!menu||document.querySelector(`[data-view="${id}"]`))return;const link=el('a',label);link.href='#'+id;link.dataset.view=id;menu.append(link);}
function safeOfficialLink(value){try{const url=new URL(value);return url.protocol==='https:'&&url.hostname==='ccmc.gsfc.nasa.gov'&&url.pathname.startsWith('/DONKI/')?url.href:null;}catch{return null;}}
function renderEvents(target,events,mode){
 target.replaceChildren();
 if(!events.length){target.append(el('p','No events were returned for the selected period. This does not mean space-weather conditions are known to be benign.'));return;}
 for(const event of events){
  const card=el('article');card.append(el('span',event.kind==='NOTIFICATION'?'NASA DONKI notification · research context':'NASA DONKI event · research context'),el('h3',event.type+' · '+event.id),el('p',event.description||'No summary provided by the event record.'));
  const time=event.time?new Date(event.time).toISOString():'Time not supplied';card.append(el('p','Event time (UTC): '+time));
  if(event.parameters?.length)card.append(el('p','Reported parameters: '+event.parameters.join(' · ')));
  card.append(el('p','NASA DONKI is not a personal dosimeter. This event alone cannot determine crew exposure or risk.'));
  const link=safeOfficialLink(event.url);if(link){const a=el('a','Open the original CCMC/NASA record');a.href=link;a.target='_blank';a.rel='noopener noreferrer';card.append(a);}
  if(mode==='HISTORICAL_FIXTURE')card.append(el('small','Fixed historical official fixture · not live, not current, and not an alert.'));
  target.append(card);
 }
}
function sourceRegister(){
 const details=el('details'),summary=el('summary','Offline source register · reviewed bibliographic links'),content=el('div'),status=el('p','Loading local source metadata…');details.append(summary,status,content);
 const load=(async()=>{try{const response=await fetch('./research/sources.json',{credentials:'omit',redirect:'error'});if(!response.ok)throw Error('Local source metadata unavailable.');const raw=await response.text();if(raw.length>100_000)throw Error('Local source metadata exceeded its size limit.');const registry=normalizeSourceRegistry(JSON.parse(raw));status.textContent='Bibliographic metadata reviewed '+registry.reviewed_at+'. Linked reports remain at official NASA publishers; this application includes project summaries, not full report texts.';for(const source of registry.sources){const card=el('article'),heading=el('h3',source.title),metadata=el('p',source.institution+' · '+source.publication_date+' · '+source.evidence_category+' · '+source.reuse_status),link=el('a','Open official NASA source');link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';card.append(heading,metadata,link);content.append(card);}}catch(error){status.textContent=error.message+' The curated summary remains local; Internet links may be unavailable offline.';}})();
 return {node:details,load};
}

export function installMissionSupport({call,persist,status=()=>{},mode=()=> 'FULL',isTemporary=()=>false}={}){
 const workspace=document.querySelector('#workspace .workspace-content');if(!workspace)throw Error('Workspace is unavailable.');
 const prevention=makeSection('prevention','Prevention & recovery','VOLUNTARY SELF-TRACKING','Record exercise, hydration, meals, sleep and well-being in this local profile. Entries are self-reports, not prescriptions, sensor measurements, nutrition analysis or diagnoses.');
 const preventionSources=sourceRegister();prevention.append(preventionSources.node);
 const preventionPanel=el('section');prevention.append(preventionPanel,el('div'));
 preventionPanel.append(el('h2','Record an entry'),el('p','Use only your own entry or the synthetic demonstration. No plan, target or treatment is generated.'));
 const form=el('div');form.className='mission-entry-form';preventionPanel.append(form);
 const type=input(form,'Entry type','select',{choices:[['EXERCISE_SESSION','Exercise session'],['HYDRATION','Hydration amount'],['MEAL_NOTE','Meal note'],['SLEEP','Sleep session'],['WELLBEING','Voluntary well-being check-in']]});
 const label=input(form,'Short label or activity (optional)');const occurred=input(form,'Occurred at (local entry; stored UTC)','datetime-local',{value:nowLocal()});
 const exerciseType=input(form,'Exercise category','select',{choices:[['USER_REPORTED','User described'],['RESISTANCE','Resistance'],['AEROBIC','Aerobic'],['MOBILITY','Mobility'],['BALANCE','Balance'],['OTHER','Other']]});
 const duration=input(form,'Duration (minutes)','number');const exertion=input(form,'Perceived exertion, self-rated 0 to 10 (optional)','number');
 const hydration=input(form,'Water/fluid amount as entered (mL)','number');const sleepQuality=input(form,'Sleep quality, subjective 1 to 5 (optional)','number');
 const mood=input(form,'Mood, voluntary self-rating 1 to 5 (optional)','number');const stress=input(form,'Perceived stress, voluntary self-rating 1 to 5 (optional)','number');
 const note=input(form,'Optional note (local only)');const recordPrevention=button(form,'Save self-reported entry',async()=>{
  const entry={entry_type:type.value,occurred_at:utc(occurred.value),label:label.value,note:note.value};
  if(type.value==='EXERCISE_SESSION'){entry.workout_type=exerciseType.value;entry.duration_minutes=duration.value;entry.perceived_exertion_0_10=exertion.value===''?null:Number(exertion.value);}
  if(type.value==='HYDRATION')entry.amount_ml=hydration.value;
  if(type.value==='SLEEP'){entry.duration_minutes=duration.value;entry.subjective_quality_1_5=sleepQuality.value===''?null:Number(sleepQuality.value);}
  if(type.value==='WELLBEING'){entry.mood_rating_1_5=mood.value===''?null:Number(mood.value);entry.stress_rating_1_5=stress.value===''?null:Number(stress.value);}
  const saved=await call('prevention_add',entry);await persist();status('Self-reported '+saved.entry_type.toLowerCase().replaceAll('_',' ')+' entry saved locally.');await refreshPrevention();
 });
 const preventionStatus=el('p');preventionStatus.setAttribute('role','status');preventionStatus.setAttribute('aria-live','polite');form.append(preventionStatus);
 function updatePreventionFields(){for(const [field,visible] of [[exerciseType,type.value==='EXERCISE_SESSION'],[duration,['EXERCISE_SESSION','SLEEP'].includes(type.value)],[exertion,type.value==='EXERCISE_SESSION'],[hydration,type.value==='HYDRATION'],[sleepQuality,type.value==='SLEEP'],[mood,type.value==='WELLBEING'],[stress,type.value==='WELLBEING']])field.parentElement.hidden=!visible;}
 type.addEventListener('change',updatePreventionFields);updatePreventionFields();
 const exerciseNote=el('p','MotionGuard pose inference is unavailable in this browser build. Manual session logging works without camera access; no video is captured.');preventionPanel.append(exerciseNote);
 const journal=el('section');journal.append(el('h2','Local history'),el('p','Duration and ratings remain self-reported. No recovery or fitness conclusion is calculated.'));const journalRows=el('div');journalRows.className='mission-journal';journal.append(journalRows);prevention.append(journal);
 async function refreshPrevention(){const result=await call('prevention_list');journalRows.replaceChildren();for(const row of [...result.entries].reverse()){const card=el('article');card.append(el('h3',row.entry_type.replaceAll('_',' ')+' · '+row.occurred_at),el('p',[row.label,row.duration_minutes?row.duration_minutes+' min':null,row.amount_ml?row.amount_ml+' mL':null,row.subjective_quality_1_5?'sleep quality '+row.subjective_quality_1_5+'/5':null].filter(Boolean).join(' · ')||row.note));card.append(el('small','SELF-REPORTED · not sensor-verified · no clinical interpretation'));journalRows.append(card);}if(!result.entries.length)journalRows.append(el('p','No prevention entries yet.'));}

 const radiation=makeSection('space-radiation','Space Weather & Radiation','SEPARATE EVENT AND EXPOSURE RECORDS','NASA DONKI events describe reported space-weather information. Personal radiation exposure requires appropriately sourced dosimetry; DONKI cannot calculate it. No flight-safety or medical eligibility decision is made here.');
 const radiationSources=sourceRegister();radiation.append(radiationSources.node);
 const radiationIntro=el('section');radiationIntro.append(el('h2','Personal radiation records'),el('p','Manual records are not sensor-verified by ASTHRAL. Measurements, modelled estimates and synthetic fixtures stay separately labelled. Gy and Sv are never interconverted by this tool.'));radiation.append(radiationIntro);
 const radForm=el('div');radForm.className='mission-entry-form';radiationIntro.append(radForm);
 const quantity=input(radForm,'Radiation quantity','select',{choices:Object.entries(quantityLabels)});const value=input(radForm,'Value','number',{required:true});const unit=input(radForm,'Unit','select',{choices:units[quantity.value].map(v=>[v,v])});
 const radiationMode=input(radForm,'Data mode','select',{choices:[['MEASURED','Measured or manually reported'],['MODELLED','Model output'],['SYNTHETIC','Synthetic software fixture']]});
 const quality=input(radForm,'Data quality','select',{choices:[['UNKNOWN','Unknown'],['VALID','Declared valid'],['INVALID','Invalid / do not use in calculations']]});
 const instrument=input(radForm,'Instrument identifier (optional)');const segment=input(radForm,'Mission segment','text',{required:true});const location=input(radForm,'Location / shielding context','text',{required:true});
 const source=input(radForm,'Source and provenance','text',{required:true,placeholder:'Manual report, imported file, model name, or fixture'});const modelName=input(radForm,'Model name (required for modelled data)');const modelVersion=input(radForm,'Model version (required for modelled data)');
 const uncertainty=input(radForm,'Uncertainty in the same unit (optional)','number');const noteRad=input(radForm,'Note (optional)');const radTime=input(radForm,'Observation time (UTC offset required)','datetime-local',{value:nowLocal()});
 quantity.addEventListener('change',()=>{unit.replaceChildren(...units[quantity.value].map(v=>{const option=el('option',v);option.value=v;return option;}));});
 const modelLabel=el('p','Model outputs require explicit model name and version; uncertainties are recorded without deriving a risk estimate.');radForm.append(modelLabel);
 const radStatus=el('p');radStatus.setAttribute('role','status');radStatus.setAttribute('aria-live','polite');radForm.append(radStatus);
 const savedRows=el('div');radiation.append(el('section'),savedRows);
 button(radForm,'Save radiation record',async()=>{
  const raw={quantity_kind:quantity.value,value:value.value,unit:unit.value,timestamp:utc(radTime.value),mode:radiationMode.value,quality:quality.value,mission_segment:segment.value,location:location.value,instrument_id:instrument.value||null,source:source.value,note:noteRad.value};
  if(radiationMode.value==='MODELLED')raw.model={name:modelName.value,version:modelVersion.value};
  if(uncertainty.value!=='')raw.uncertainty={value:Number(uncertainty.value),unit:unit.value};
  const saved=await call('radiation_add',raw);await persist();radStatus.textContent='Record stored. Mode: '+saved.mode+'; ASTHRAL has not verified an instrument or inferred health risk.';await refreshRadiation();
 });
 const rateSection=el('section');rateSection.append(el('h2','Dose-rate interval calculation'),el('p','Trapezoidal integration assumes rates changed linearly between adjacent samples. Only valid MEASURED readings with one instrument, segment and location are eligible. Gaps are not filled. The allowed maximum interval must be entered explicitly.'));radiation.append(rateSection);
 const rateType=input(rateSection,'Rate quantity','select',{choices:rateKinds.map(kind=>[kind,quantityLabels[kind]])});const maxGap=input(rateSection,'Maximum gap to include (seconds)','number');const calcResult=el('pre');calcResult.setAttribute('role','status');calcResult.setAttribute('aria-live','polite');rateSection.append(calcResult);
 button(rateSection,'Calculate eligible intervals',async()=>{const result=await call('radiation_integrate',{quantity_kind:rateType.value,max_gap_seconds:Number(maxGap.value)});calcResult.textContent=JSON.stringify(result,null,2);});
 const counterSection=el('section');counterSection.append(el('h2','Cumulative counter review'),el('p','Counter resets and duplicate timestamps are flagged. No delta is assigned across a reset.'));const counterResult=el('pre');counterSection.append(counterResult);radiation.append(counterSection);
 const fixtureSection=el('section');fixtureSection.append(el('h2','Synthetic EVA and event-separation demonstration'),el('p','Arbitrary software fixture values below are synthetic and do not model a flight environment, dosimeter, radiation limit or biological effect. The nearby historical DONKI event is an independent timeline annotation; it does not cause or change the synthetic readings.'));const fixtureStatus=el('p');fixtureStatus.setAttribute('role','status');fixtureSection.append(fixtureStatus);
 const fixtureButton=button(fixtureSection,'Load synthetic timeline in this temporary demo',async()=>{
  if(!isTemporary())throw Error('Synthetic fixture records are available only inside the disposable demo.');
  const anchor=Date.parse('2026-11-05T18:21:00Z');
  for(const [minutes,reading,tag] of [[0,1,'habitat'],[30,12,'EVA'],[60,2,'habitat']])await call('radiation_add',{quantity_kind:'ABSORBED_DOSE_RATE',value:reading,unit:'uGy/h',timestamp:new Date(anchor+minutes*60000).toISOString(),mode:'SYNTHETIC',quality:'UNKNOWN',mission_segment:'synthetic-eva-exercise',location:tag,instrument_id:'synthetic-dosimeter-fixture',source:'ARBITRARY_SYNTHETIC_SOFTWARE_FIXTURE',note:'Not an astronaut measurement and not a radiation transport model.'});
  await persist();fixtureStatus.textContent='Three synthetic values stored in temporary memory only. They are unrelated to the historical solar flare record.';await refreshRadiation();
 });
 radiation.append(fixtureSection);
 async function refreshRadiation(){const result=await call('radiation_list');savedRows.replaceChildren(el('h2','Local radiation history'));for(const row of [...result.records].reverse()){const card=el('article');card.append(el('h3',quantityLabels[row.quantity_kind]+' · '+row.value+' '+row.unit),el('p',row.timestamp+' · '+row.mode+' · '+row.quality),el('p',row.mission_segment+' · '+row.location+' · '+row.source),el('small','Sensor verified by ASTHRAL: no · Clinical interpretation: none'));savedRows.append(card);}if(!result.records.length)savedRows.append(el('p','No radiation records. Missing data means exposure is unknown, not zero.'));counterResult.textContent=JSON.stringify(result.counter_review,null,2);fixtureButton.disabled=!isTemporary();}

 const space=makeSection('space-weather','Space Weather','OPTIONAL NASA DONKI INFORMATION','NASA CCMC DONKI records space-weather events and analyses for research and prototyping. They do not measure this crew member’s exposure and are not operational life-safety alerts. Live requests send only a date range and fixed event endpoints; no profile, location or health data are sent.');
 const spaceSources=sourceRegister();space.append(spaceSources.node);
 const spaceControls=el('section'),start=input(spaceControls,'Start date (UTC)','date'),end=input(spaceControls,'End date (UTC)','date'),sync=el('button','Synchronize NASA DONKI (optional online request)'),spaceStatus=el('p');spaceStatus.setAttribute('role','status');spaceStatus.setAttribute('aria-live','polite');
 const spaceRows=el('div');space.append(spaceControls,spaceRows);spaceControls.append(el('h2','Recent NASA CCMC DONKI events'),el('p','The query window is limited to the last 7 days. No browser background alerts are used.'),start,end,sync,spaceStatus);
 const fixture=el('details');fixture.append(el('summary','Fixed historical NASA fixture (offline reference; not current)'));const fixtureRows=el('div');fixture.append(fixtureRows);space.append(fixture);renderEvents(fixtureRows,[DONKI_HISTORICAL_FIXTURE],'HISTORICAL_FIXTURE');
 sync.addEventListener('click',async()=>{sync.disabled=true;spaceStatus.textContent='Requesting public NASA CCMC data…';try{const result=await fetchDonki({startDate:start.value,endDate:end.value});cacheDonki(result);renderEvents(spaceRows,result.events,'ONLINE');spaceStatus.textContent='NASA CCMC data returned at '+result.fetched_at+' · '+result.events.length+' records · '+result.issues.length+' endpoint issues. DONKI is research/prototyping data, not a real-time crew warning.';}catch(error){showCachedEvents('NASA connection unavailable · ');}finally{sync.disabled=false;}});
 function showCachedEvents(prefix=''){const cache=cachedDonkiSnapshot();if(cache.state==='NO_CACHE'){spaceStatus.textContent=prefix+'No NASA event cache is saved on this device. Current conditions are unknown.';renderEvents(spaceRows,[],'UNAVAILABLE');return;}renderEvents(spaceRows,cache.events,'CACHED');spaceStatus.textContent=prefix+(cache.state==='STALE'?'STALE cached':'Cached')+' public event data last synchronized '+cache.fetched_at+'. Current conditions are unknown; this is not an operational warning.';}
 const refreshButton=button(spaceControls,'Show locally cached NASA events',async()=>showCachedEvents());
 start.value=new Date(Date.now()-7*86400000).toISOString().slice(0,10);end.value=new Date().toISOString().slice(0,10);
 const preventionStatusReset=()=>{preventionStatus.textContent='';radStatus.textContent='';calcResult.textContent='';};
 workspace.append(prevention,radiation,space);
 addView('prevention','Prevention & recovery');addView('space-radiation','Space Weather & Radiation');addView('space-weather','Space Weather');
 async function refresh(){if(!document.querySelector('#workspace').hidden){await Promise.all([refreshPrevention(),refreshRadiation(),preventionSources.load,radiationSources.load,spaceSources.load]);showCachedEvents();}}
 return {refresh,clear(){journalRows.replaceChildren();savedRows.replaceChildren();counterResult.textContent='';calcResult.textContent='';spaceRows.replaceChildren();spaceStatus.textContent='';fixtureStatus.textContent='';preventionStatusReset();for(const section of [prevention,radiation])for(const field of section.querySelectorAll('input'))field.value='';for(const section of [prevention,radiation])for(const field of section.querySelectorAll('select'))field.selectedIndex=0;},DONKI_API};
}
