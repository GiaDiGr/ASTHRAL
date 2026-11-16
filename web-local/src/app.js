import {loadPublicJson} from './public-json.js';
import {Vault} from './vault.js';
import {initialClinicalInput} from './profile-input.js';
import {installOffline} from './offline-install.js';
import {auditedFetch,PRIVATE_SENTINEL} from './network-audit.js';
const networkEvents=[];const recordNetwork=event=>{networkEvents.push(event);if(networkEvents.length>1000)networkEvents.shift();};
window.fetch=auditedFetch(window.fetch.bind(window),recordNetwork);
import {installPublicFeatures} from './public-science.js';
let clearPublicFeatures=()=>{};
import {cachePublicResources} from './public-resources.js';
import {installExperience,human} from './experience.js';
import {installMissionSupport} from './mission-support.js';
import {installPreventiveExperience} from './preventive-experience.js';
let experience=null;
let missionSupport=null;
let preventiveExperience=null;
const $=id=>document.getElementById(id);
const cosmicLayers=[document.createElement('div'),document.createElement('div')];
for(const layer of cosmicLayers){layer.className='cosmic-scene-layer';layer.setAttribute('aria-hidden','true');document.body.prepend(layer);}
let cosmicActive=0,cosmicScene=-1;
function showCosmicScene(id){const routes=[...$('workspace-nav').querySelectorAll('[data-view]')].map(link=>link.dataset.view).filter(route=>route!=='anatomy');const normalized=id==='anatomy'?'dashboard':id;const index=Math.max(0,routes.indexOf(normalized));const scene=index%24;if(scene===cosmicScene)return;cosmicScene=scene;const next=1-cosmicActive;cosmicLayers[next].dataset.scene=String(scene);cosmicLayers[next].style.backgroundImage=`url('./cosmic-scenes/scene-${String(scene).padStart(2,'0')}.svg')`;cosmicLayers[next].classList.add('cosmic-active');cosmicLayers[cosmicActive].classList.remove('cosmic-active');cosmicActive=next;}
showCosmicScene('dashboard');
const runtimeState={ready:false,seconds:null};
const operationMetrics=[];
let recordingEpoch=0,profileEpoch=0;
let worker,serial=0,vault=null,owner=null,cases=[],corpus=null,stream=null;
const waiting=new Map();
function element(tag,value) {
  const node=document.createElement(tag);
  node.textContent=value;
  return node;
}
function status(value) { $('operation').textContent=value; }
function showWorkspaceView(id='dashboard') {
  if(id==='dashboard') id='anatomy';
  const content=$('workspace').querySelector('.workspace-content');
  const pages=[...content.querySelectorAll(':scope > section')];
  pages.forEach(page=>page.classList.add('workspace-page'));
  if(!pages.some(page=>page.id===id)) id='dashboard';
  for(const page of pages) page.hidden=page.id!==id;
  for(const link of $('workspace-nav').querySelectorAll('[data-view]')) {
    if(link.dataset.view===id || (id==='anatomy' && link.dataset.view==='dashboard')) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  }
  const active=$('workspace-nav').querySelector('[aria-current="page"]');
  if(active){const nav=$('workspace-nav');const left=active.offsetLeft-nav.offsetLeft;nav.scrollTo({left:Math.max(0,left-(nav.clientWidth-active.offsetWidth)/2),behavior:'instant'});}
  document.title=(pages.find(page=>page.id===id)?.querySelector('h1')?.textContent||'ASTHRAL')+' · ASTHRAL';
  window.scrollTo({top:0,behavior:'instant'});
  window.dispatchEvent(new CustomEvent('asthral:viewchange',{detail:{id}}));
  showCosmicScene(id);
}
function startWorker() {
  worker=new Worker('./worker.js?v=5');
  worker.onmessage=event=>{
    const value=event.data;
    if(value.type==='network_audit'){recordNetwork(value.event);return;}
    if(value.type==='ready') {
      runtimeState.ready=true;
      runtimeState.seconds=value.seconds;
      $('runtime-status').textContent='Reference Python engine ready on this device · '+value.seconds.toFixed(2)+' seconds';
      if($('chat-model-status')) $('chat-model-status').textContent='Clinical engine ready locally · text generation is optional and must be installed separately.';
      return;
    }
    if(value.type==='failed') {
      $('runtime-status').textContent='Local runtime failed. '+value.error;
      return;
    }
    const pending=waiting.get(value.id);
    if(pending) {
      waiting.delete(value.id);
      operationMetrics.push({action:pending.action,engine_seconds:value.seconds??null,total_seconds:(performance.now()-pending.started)/1000});if(operationMetrics.length>200)operationMetrics.shift();
      if(pending.epoch!==profileEpoch)pending.reject(Error('Profile changed while the operation was pending.'));
      else value.error?pending.reject(Error(value.error)):pending.resolve(value.result);
    }
  };
  worker.onerror=()=>{ $('runtime-status').textContent='Local worker failed. Reload and inspect device diagnostics.'; };
}
function call(action,data) {
  return new Promise((resolve,reject)=>{
    const id=++serial;
    waiting.set(id,{resolve,reject,epoch:profileEpoch,action,started:performance.now()});
    worker.postMessage({id,action,data});
  });
}
function safe(action) {
  return async event=>{
    event?.preventDefault();
    try { await action(event); }
    catch(error) { status(error.message); }
  };
}
startWorker();
async function resources() {
  if(cases.length) return;
  const nextCases=await loadPublicJson('./demo-scenarios.json');
  const nextCorpus=await loadPublicJson('./corpus.json');
  cases=nextCases;corpus=nextCorpus;
  $('case-list').replaceChildren(...cases.map((row,index)=>{
    const option=element('option',row.id+' · '+(row.snapshot.request.condition_id||'Differential'));
    option.value=String(index);
    return option;
  }));
  selectCase();
}
function selectCase() {
  const row=cases[Number($('case-list').value)||0];
  $('scenario').value=JSON.stringify({request:row.snapshot.request,mission:row.snapshot.mission},null,2);
  experience?.refresh();
  dashboardCaption('Unsaved synthetic scenario preview · not recorded measurements');
  $('metrics').replaceChildren(...row.snapshot.observations.slice(0,12).map(value=>{
    const card=document.createElement('article');
    card.append(element('strong',human(value.concept)),element('p',String(value.value??'Not measured')+' '+value.unit),element('small',value.timestamp+' · '+value.quality+' · '+value.method));
    return card;
  }));
}
function dashboardCaption(text) {
  $('dashboard-caption').textContent=text;
}
async function recordedDashboard(data,epoch,providedTimeline=null) {
  const timeline=experience?(providedTimeline??await call('timeline')):null;
  if(epoch!==profileEpoch||!vault)return;
  dashboardCaption('Recorded profile data · self-reports are separate from sensor-verified measurements');
  const cards=[];
  for(const row of (timeline?.measurement??[]).slice(-8)){
    const m=row.measurement,card=document.createElement('article');card.append(element('strong','Recorded measurement: '+human(m.variable)),element('p',String(m.value??'Not measured')+' '+m.unit),element('small',m.timestamp+' · '+human(row.ingestion_quality??'UNKNOWN')));cards.push(card);
  }
  const last=data.evaluations.at(-1);
  if(last){const card=document.createElement('article');card.append(element('strong','Last saved clinical assessment'),element('p',human(last.snapshot.request.condition_id??'Differential')+' · '+human(last.output.urgency)),element('small','Recorded assessment time: '+last.snapshot.request.as_of+' · not a live sensor reading'));cards.push(card);}
  for(const row of data.observations.slice(-4)){const card=document.createElement('article');card.append(element('strong','Reviewed self-report · not sensor-verified'),element('p',row.text));cards.push(card);}
  if(!cards.length)cards.push(element('p','No measurements or assessments recorded. Missing information remains unknown.'));
  $('metrics').replaceChildren(...cards);
}
async function listProfiles() {
  $('profile-list').replaceChildren(...(await Vault.list()).map(row=>{
    const option=element('option',row.label);
    option.value=row.id;
    return option;
  }));
}
async function entered() {
  const epoch=profileEpoch;
  await resources();
  if(epoch!==profileEpoch||!vault)return;
  $('scope').textContent=(vault.temporary?'Temporary synthetic demo · memory only · ':'Encrypted synthetic local profile · ')+owner;
  if(vault.temporary)selectCase();
  else {
    const saved=await call('history');
    if(epoch!==profileEpoch||!vault)return;
    $('scenario').value=JSON.stringify(initialClinicalInput(saved.evaluations,owner));
    experience?.refresh();
  }
  await history();
  await experience?.update();
  if(epoch!==profileEpoch||!vault)return;
  $('intro').hidden=true;$('workspace').hidden=false;$('profiles').hidden=true;$('lock').hidden=false;
  showWorkspaceView('anatomy');
  $('profile-settings-status').textContent=vault.temporary?'Temporary synthetic demo · memory only · discarded on exit':'Encrypted local profile unlocked · no cloud synchronization';
  $('migration-email').disabled=!!vault.temporary||!!vault.row.email_box;
  $('migration-email-save').disabled=!!vault.temporary||!!vault.row.email_box;
  if(vault.row?.email_box)$('migration-status').textContent='An encrypted local email sign-in is already associated with this profile.';
  else if(!vault.temporary)$('migration-status').textContent='Legacy profile unlocked. Add an email sign-in without changing the original passphrase or encryption key.';
  await missionSupport?.refresh();
  await preventiveExperience?.refresh();
}
async function persist() {
  if(!vault.temporary)await vault.save(await call('serialize'));
  await history();
}
async function history() {
  const epoch=profileEpoch;
  const data=await call('history');
  if(epoch!==profileEpoch||!vault)return;
  const timeline=experience?await call('timeline'):null;
  if(epoch!==profileEpoch||!vault)return;
  const latest=data.evaluations.at(-1);
  $('emergency-banner').hidden=true;
  // Historical results stay in history; current urgency is shown with its assessment.
  $('emergency-banner').textContent=latest?latest.output.urgency+' · Last saved synthetic assessment · Human medical review required · Treatment blocked':'';
  const moment=row=>row.occurred_at||row.timestamp||row.submitted_at||row.computed_at||row.created_at||row.updated_at||row.started_at||row.measurement?.timestamp||row.snapshot?.request?.as_of||null;
  const rows=[
    ...data.evaluations.map(row=>({label:row.output.urgency+' · '+(row.snapshot.request.condition_id||'Differential'),detail:row,occurred_at:row.snapshot.request.as_of})),
    ...data.observations.map(row=>({label:row.text,detail:row,occurred_at:moment(row)})),
    ...(data.prevention_entries??[]).map(row=>({label:row.entry_type.replaceAll('_',' ')+(row.synthetic_data?' · synthetic':' · self-report'),detail:row,occurred_at:moment(row)})),
    ...(data.radiation_records??[]).map(row=>({label:row.quantity_kind.replaceAll('_',' ')+' · '+row.value+' '+row.unit+' · '+row.mode,detail:row,occurred_at:moment(row)})),
    ...(data.eva_activities??[]).map(row=>({label:'EVA · '+String(row.scenario_id||'simulation').replaceAll('_',' ')+' · '+(row.final_state||row.status||'completed')+' · simulated',detail:row,occurred_at:row.ended_at_utc||row.started_at_utc})),
    ...(timeline?.measurement??[]).map(row=>({label:'Measurement · '+human(row.measurement.variable)+' · '+String(row.measurement.value??'unknown')+' '+row.measurement.unit,detail:row,occurred_at:moment(row)})),
    ...(timeline?.baseline??[]).map(row=>({label:'Personal baseline · '+(row.variable||row.concept||'reference'),detail:row,occurred_at:moment(row)})),
    ...(timeline?.trend??[]).map(row=>({label:'Longitudinal trend · '+(row.variable||row.concept||'review'),detail:row,occurred_at:moment(row)})),
    ...(timeline?.finding??[]).map(row=>({label:'Recorded finding · '+(row.title||row.finding_id||row.category||'review'),detail:row,occurred_at:moment(row)})),
    ...(timeline?.monitoring_run??[]).map(row=>({label:'Deterministic monitoring cycle · '+(row.severity||row.status||'completed'),detail:row,occurred_at:moment(row)})),
    ...(timeline?.monitoring_event??[]).map(row=>({label:'Monitoring event · '+(row.event_type||row.category||'recorded'),detail:row,occurred_at:moment(row)})),
    ...(timeline?.episode??[]).map(row=>({label:'Episode · '+(row.status||row.episode_type||'follow-up'),detail:row,occurred_at:moment(row)}))
  ];
  rows.sort((a,b)=>String(b.occurred_at||'').localeCompare(String(a.occurred_at||'')));
  $('history-list').replaceChildren();
  for(const row of rows) {
    const article=document.createElement('article');
    if(row.detail?.id) article.dataset.recordId=row.detail.id;
    const details=document.createElement('details');
    details.className='developer-only';
    details.append(element('summary','Record and provenance'),element('pre',JSON.stringify(row.detail,null,2)));
    const header=document.createElement('div');header.append(element('strong',row.label));if(row.occurred_at){const time=document.createElement('time');time.dateTime=row.occurred_at;time.textContent=new Date(row.occurred_at).toLocaleString();header.append(time);}article.append(header,details);
    if(row.detail.source?.startsWith('SELF_REPORTED'))article.append(element('p','Self-reported information · not sensor-verified · medical review required; no text-based urgency classification.'));
    $('history-list').append(article);
  }
  if(!rows.length) $('history-list').append(element('p','No local observations or evaluations saved.'));
  $('profile-status').textContent='Unlocked · audit '+(data.audit_valid?'verified':'FAILED');
  await recordedDashboard(data,epoch,timeline);
  missionSupport?.setVitalTimeline(timeline, epoch===profileEpoch && !!vault);
}
async function lock() {
  profileEpoch++;
  operationMetrics.length=0;
  experience?.clear();
  await missionSupport?.clear();
  preventiveExperience?.clear();
  clearPublicFeatures();
  stopRecording();
  vault?.lock();
  vault=null;
  owner=null;
  worker.terminate();
  for(const pending of waiting.values()) pending.reject(Error('Profile locked.'));
  waiting.clear();
  runtimeState.ready=false;
  startWorker();
  $('emergency-banner').hidden=true;
  $('emergency-banner').textContent='';
  $('workspace').hidden=true;
  floatingAssistant.hidden=true;floatingPanel.hidden=true;floatingToggle.setAttribute('aria-expanded','false');
  $('profiles').hidden=false;
  $('intro').hidden=false;
  $('lock').hidden=true;
  for(const id of ['history-list','assessment','clinical-output','management','urgency','citations','answer','statistics-output','statistics-chart','metrics','model-benchmark']) $(id).replaceChildren();
  for(const id of ['observation-text','scenario','question','search-question'])$(id).value='';
  $('voice-auto').checked=false;
  $('model-status').textContent='Profile locked · local inference released';
  status('Profile locked.');
  $('profile-status').textContent='Profile locked';
  await listProfiles();
}
$('signin-form').onsubmit=safe(async()=>{
  if(vault) throw Error('Lock the current profile first.');
  const password=$('signin-password').value;
  try {
    const result=await Vault.unlockByEmail($('signin-email').value,password);
    owner=result.vault.row.id;
    await call('init_profile',{id:owner,database:result.database});
    vault=result.vault;
    await entered();
    status('Local profile unlocked on this device.');
  } finally { $('signin-password').value=''; }
});
$('create-account-toggle').onclick=()=>{
  const form=$('create-form'),open=form.hidden;
  form.hidden=!open;$('create-account-toggle').setAttribute('aria-expanded',String(open));
  if(open) $('profile-label').focus();
};
document.querySelectorAll('[data-password]').forEach(button=>button.onclick=()=>{
  const input=$(button.dataset.password),visible=input.type==='password';input.type=visible?'text':'password';button.textContent=visible?'Hide':'Show';button.setAttribute('aria-label',visible?'Hide password':'Show password');
});
$('create-form').onsubmit=safe(async()=>{
  if(vault) throw Error('Lock your current profile first.');
  const password=$('create-password').value;
  try {
    owner='profile-'+crypto.randomUUID();
    await call('init_profile',{id:owner});
    vault=await Vault.createLocalAccount($('profile-label').value,password,owner);
    await persist();
    await entered();
    $('create-form').hidden=true;$('create-account-toggle').setAttribute('aria-expanded','false');
    status('Encrypted local profile created on this device. Keep your password; there is no email reset or cloud sync.');
  } finally { $('create-password').value=''; }
});
$('migration-email-save').onclick=safe(async()=>{
  if(!vault||vault.temporary) throw Error('Unlock a persistent legacy profile first.');
  if(vault.row.email_box) throw Error('This profile already has a local email sign-in.');
  await vault.setLocalEmail($('migration-email').value);
  $('migration-email').value='';
  $('migration-email').disabled=true;$('migration-email-save').disabled=true;
  $('migration-status').textContent='Encrypted email sign-in added. The original password and encryption key are unchanged. This email is an unverified, device-local identifier.';
  status('Legacy profile sign-in updated locally.');
});
$('unlock-form').onsubmit=safe(async()=>{
  const password=$('unlock-password').value;
  try {
    const result=await Vault.unlock($('profile-list').value,password);
    owner=result.vault.row.id;
    await call('init_profile',{id:owner,database:result.database});
    vault=result.vault;
    await entered();
    status('Local profile unlocked.');
  } finally { $('unlock-password').value=''; }
});
$('lock').onclick=safe(lock);
$('explore').onclick=safe(async()=>{
  if(vault) { $('workspace').scrollIntoView({behavior:'smooth'}); return; }
  owner='profile-'+crypto.randomUUID();
  await call('init_profile',{id:owner});
  vault={temporary:true,lock(){},export(){throw Error('Temporary demo has no persistent backup. Create a local profile for encrypted storage.');},remove(){throw Error('Lock the temporary demo to discard it.');}};
  await entered();
  showWorkspaceView('dashboard');
  status('Temporary synthetic demo ready. Records stay in memory and are discarded when this page closes. Create a local profile for encrypted persistence.');
  $('workspace').scrollIntoView({behavior:'instant'});
});
$('case-list').onchange=selectCase;
$('evaluate').onclick=safe(async()=>{
  if(!vault) throw Error('Unlock a local profile first.');
  status('Computing locally in the Python WebAssembly worker…');
  const epoch=profileEpoch;
  experience?.sync();
  const result=await call('evaluate',{snapshot:JSON.parse($('scenario').value),use_registered_context:!document.body.classList.contains('developer-view')});
  await persist();
  if(epoch!==profileEpoch||!vault)return;
  $('urgency').textContent=human(result.output.urgency)+' · Synthetic assessment as of '+result.snapshot.request.as_of+' · Treatment execution blocked';
  $('urgency').className=['URGENT','EMERGENCY'].includes(result.output.urgency)?'emergency':'';
  $('assessment').replaceChildren();
  for(const [name,value] of Object.entries(result.output.results)) {
    const card=document.createElement('article');
    card.append(
      element('h3',human(name)),
      element('p',human(value.diagnostic_status)+' · '+human(value.confirmation_status)),
      element('p','Information needed to resolve criteria (AND/OR alternatives apply): '+(value.missing_required.map(human).join(', ')||'None')),
      element('p','Unmeasured alternatives that do not block this result: '+(value.optional_not_measured.map(human).join(', ')||'None')),
      element('p','Invalid evidence requiring review: '+((value.invalid_required??[]).map(human).join(', ')||'None identified')),
      element('p','Independent protocol safety information needed: '+(value.required_for_protocol_safety.map(human).join(', ')||'None')),
      element('p',human(value.protocol_status))
    );
    $('assessment').append(card);
  }
  $('clinical-output').textContent=JSON.stringify(result,null,2);
  const pending=element('article','Recommended tests and assessment actions (not authorized orders)');
  for(const test of result.output.next_tests??[])pending.append(element('p',human(test.test_id??test.action??'Medical review')+' · '+human(test.priority??'review required')));
  if((result.output.next_tests??[]).length)$('assessment').append(pending);
  const management=result.output.management||{state:'Documentary resource mapping unavailable for this context',treatment:'BLOCKED'};
  $('management').replaceChildren();
  for(const [route,guide] of Object.entries(management)) {
    const card=document.createElement('article');
    card.append(element('strong',human(route)),element('p','Documented reference · execution blocked'));
    for(const intervention of guide.interventions??[]) {
      card.append(element('p','Documented option: '+human(intervention.title)+' · '+human(intervention.resource_status)+' · '+human(intervention.authorization)));
    }
    const details=document.createElement('details');
    details.classList.add('developer-only');
    details.append(element('summary','Original guidance, resource checks and source metadata'),element('pre',JSON.stringify(guide,null,2)));
    card.append(details);
    $('management').append(card);
  }
  status(vault.temporary?'Assessment computed in the temporary synthetic demo. Closing this page discards it.':'Assessment computed on this device and saved to the encrypted profile.');
});
$('run-parity').onclick=safe(async()=>{
  await resources();
  status('Running real Python computations against reference outputs…');
  await cacheOptional(['parity-cases.json']);
  const parityCases=await(await fetch('./parity-cases.json')).json();
  const result=await call('parity',{cases:parityCases});
  $('parity').textContent=JSON.stringify(result,null,2);
  status(result.matched+'/'+result.total+' reference outputs matched.');
  window.asthralParity=result;
});
$('diagnose').onclick=safe(async()=>{
  const report={
    observed_at:new Date().toISOString(),user_agent:navigator.userAgent,
    wasm:WebAssembly.validate(new Uint8Array([0,97,115,109,1,0,0,0])),
    secure_context:isSecureContext,cross_origin_isolated:crossOriginIsolated,
    logical_cores:navigator.hardwareConcurrency??null,
    reported_device_memory_gb:navigator.deviceMemory??null,
    heap:performance.memory?{limit:performance.memory.jsHeapSizeLimit,used:performance.memory.usedJSHeapSize}:null,
    storage:await navigator.storage?.estimate?.(),persistent:await navigator.storage?.persisted?.(),
    opfs:typeof navigator.storage?.getDirectory==='function',
    microphone:!!navigator.mediaDevices?.getUserMedia,audio_worklet:!!window.AudioWorkletNode,
    speech_synthesis:!!window.speechSynthesis,local_stt:'NOT_INSTALLED',
    python_ready:runtimeState.ready,python_init_seconds:runtimeState.seconds,
    webgpu:!!navigator.gpu,peak_memory:'NOT_MEASURABLE_BY_THIS_TEST',
    physical_device_acceptance:'NOT_INFERRED_FROM_USER_AGENT'
  };
  if(navigator.gpu) {
    try {
      const adapter=await navigator.gpu.requestAdapter();
      report.webgpu_adapter=!!adapter;
      if(adapter) report.gpu_limits={
        maxBufferSize:adapter.limits.maxBufferSize,
        maxStorageBufferBindingSize:adapter.limits.maxStorageBufferBindingSize
      };
    } catch(error) { report.gpu_error=String(error); }
  }
  try {
    if(report.opfs) {
      const directory=await navigator.storage.getDirectory();
      const probe='asthral-capability-probe-'+crypto.randomUUID();
      const file=await directory.getFileHandle(probe,{create:true});
      const output=await file.createWritable();
      await output.write('synthetic probe');
      await output.close();
      report.opfs_roundtrip=await (await file.getFile()).text()==='synthetic probe';
      await directory.removeEntry(probe);
    }
  } catch(error) { report.opfs_error=String(error); }
  $('diagnostics').textContent=JSON.stringify(report,null,2);
  window.asthralDiagnostics=report;
  status('Capability test complete. Physical phone acceptance must be recorded separately.');
});
function renderDocs(parent,blocks) {
  parent.replaceChildren();
  if(!blocks.length) parent.append(element('p','No eligible local excerpt matched.'));
  for(const block of blocks) {
    const article=document.createElement('article');
    article.append(element('strong',block.id),element('p',block.display_text??block.text),
      element('small',block.kind==='ENGINE'?'Recorded local assessment · deterministic engine':block.reference.document+' · '+block.reference.authority+' · SHA-256 '+block.reference.sha256));
    parent.append(article);
  }
}
$('search').onclick=safe(async()=>{
  await resources();
  const result=await call('search',{corpus,question:$('search-question').value,limit:3});
  renderDocs($('citations'),result.blocks);
  status('Local reference BM25 retrieval complete.');
});
$('ask').onclick=safe(async()=>{
  await resources();
  const result=await call('search',{corpus,question:$('question').value,limit:3});
  renderDocs($('answer'),result.blocks);
  status('Genuine extractive results. Local text generation has not been installed.');
});
$('observation-form').onsubmit=safe(async()=>{
  if(!vault) throw Error('Unlock your local profile first.');
  await call('save_observation',{
    text:$('observation-text').value,source:'SELF_REPORTED_TYPED',
    validation:'REVIEWED_FREE_TEXT',clinical_eligibility:'NOT_AUTOMATICALLY_ASSESSED'
  });
  await persist();
  $('observation-text').value='';
  status('Reviewed self-report saved in the encrypted profile.');
});
function stopRecording() {
  recordingEpoch++;
  stream?.getTracks().forEach(track=>track.stop());
  stream=null;
  $('stop-record').disabled=true;
  $('record').disabled=false;
  $('voice-status').textContent='Microphone stopped. Audio discarded. Offline transcription is not installed.';
}
$('record').onclick=safe(async()=>{
  if(!vault) throw Error('Unlock your local profile first.');
  if(!navigator.mediaDevices?.getUserMedia) throw Error('Microphone capture unavailable. Use reviewed text.');
  const epoch=++recordingEpoch;
  $('record').disabled=true;
  $('stop-record').disabled=false;
  let captured;
  try { captured=await navigator.mediaDevices.getUserMedia({audio:true,video:false}); }
  catch(error) { stopRecording(); throw error; }
  if(epoch!==recordingEpoch||!vault) { captured.getTracks().forEach(track=>track.stop()); return; }
  stream=captured;
  $('voice-status').textContent='Microphone permission and capture test active. Audio is not retained or transmitted.';
  setTimeout(()=>{if(epoch===recordingEpoch)stopRecording();},10000);
});
$('stop-record').onclick=stopRecording;
document.addEventListener('visibilitychange',()=>{if(document.hidden&&stream) stopRecording();});
$('export').onclick=safe(async()=>{
  const blob=new Blob([vault.export()],{type:'application/json'});
  const link=document.createElement('a');
  link.href=URL.createObjectURL(blob);
  link.download='asthral-encrypted-profile.json';
  link.click();
  setTimeout(()=>URL.revokeObjectURL(link.href),1000);
  status('Encrypted export downloaded. Recovery requires your passphrase.');
});
$('import-file').onchange=safe(async event=>{
  const file=event.target.files[0];
  if(!file) return;
  if(file.size>32*1024*1024) throw Error('Import exceeds supported size.');
  await Vault.recover(await file.text());
  await listProfiles();
  event.target.value='';
  status('Encrypted profile imported. Unlock it with its original passphrase.');
});
$('integrity').onclick=safe(async()=>{
  const result=await call('history');
  status('SQLite hash-chain audit '+(result.audit_valid?'verified':'FAILED')+' · sequence '+result.checkpoint.sequence);
});
$('delete').onclick=safe(async()=>{
  if($('delete-confirm').value!=='DELETE') throw Error('Type DELETE before removing this local profile.');
  await vault.remove();
  $('delete-confirm').value='';
  await lock();
  status('Local encrypted profile deleted. Existing exports are retained.');
});
$('model-install').onclick=()=>{
  $('model-details').textContent='Browser model installation is pending compatibility and integrity tests. Extractive references and deterministic clinical computation are available.';
};
$('mode').onchange=()=>{
  $('model-status').textContent=$('mode').value==='CRITICAL'?'CRITICAL · no costly inference':'Local generation not installed · extractive fallback available';
};
function network() {
  $('network').textContent=navigator.onLine?'Network available · processing local':'Offline · processing local';
}
addEventListener('online',network);
addEventListener('offline',network);
network();
listProfiles().catch(error=>status(error.message));
let offlineInstalling=false;
navigator.serviceWorker?.addEventListener('message',event=>{if(offlineInstalling&&event.data?.type==='OFFLINE_INSTALL_PROGRESS'){const value=event.data;$('offline-status').textContent='Installing / checking '+value.complete+' of '+value.total+' files · '+(value.bytes/1048576).toFixed(1)+' MiB verified';}});
$('install-offline').onclick=async()=>{
 const button=$('install-offline'),message=$('offline-status');button.disabled=true;button.textContent='Installing offline resources…';offlineInstalling=true;
 try{const result=await installOffline({report:text=>{message.textContent=text;status(text);}});
 if(result.update_waiting){$('activate-update').hidden=false;message.textContent='Verified update downloaded. Lock all open profiles, then activate the update.';}
 else{$('activate-update').hidden=true;message.textContent='Offline resources verified: '+result.files+' files. '+(result.persistent?'Persistent storage granted.':'Browser storage can be evicted; retain an encrypted backup.')+' Reload this page, then test without connectivity.';}
 status(message.textContent);
 }catch(error){message.textContent='Offline installation failed: '+error.message;status(message.textContent);}
 finally{offlineInstalling=false;button.disabled=false;button.textContent='Install offline resources';}
};

import {saveIndex,readIndex,hybridRank,vectorRank,fuseRankings} from './vectors.js';
let modelCatalog=null;
let localGeneration=null;
let localEmbedding=null;
let modelEpoch=0;
const benchmarks=[];
class InferenceWorker {
  constructor(statusElement) {
    this.worker=new Worker('./ml-worker.js',{type:'module'});
    this.next=0;
    this.pending=new Map();
    this.ready=false;
    this.worker.onmessage=event=>{
      const message=event.data;
      if(message.type==='network_audit'){recordNetwork(message.event);return;}
      if(message.type==='status') {
        const progress=message.total?' · '+((message.received??0)/1048576).toFixed(1)+' / '+(message.total/1048576).toFixed(1)+' MiB':'';
        statusElement.textContent=message.state+progress+(message.text?' · '+message.text:'');
        return;
      }
      const task=this.pending.get(message.id);
      if(task) {
        this.pending.delete(message.id);
        if(message.error) { statusElement.textContent=(message.state??'LOCAL_FALLBACK_AVAILABLE')+' · '+message.error; task.reject(Error(message.error)); }
        else task.resolve(message.result);
      }
    };
    this.worker.onerror=()=>{
      statusElement.textContent='Unsupported or insufficient resources · local fallback available';
      this.stop();
    };
  }
  call(action,data) {
    return new Promise((resolve,reject)=>{
      const id=++this.next;
      this.pending.set(id,{resolve,reject});
      this.worker.postMessage({id,action,data});
    });
  }
  stop() {
    this.worker.terminate();
    this.ready=false;
    for(const task of this.pending.values()) task.reject(Error('Local inference stopped.'));
    this.pending.clear();
  }
}
async function models() {
  if(!modelCatalog) modelCatalog=await (await fetch('./models.json')).json();
  return modelCatalog.models;
}
function releaseModels() {
  modelEpoch++;
  benchmarks.length=0;
  localGeneration?.stop();
  localEmbedding?.stop();
  localGeneration=null;
  localEmbedding=null;
}
const originalLock=lock;
lock=async function() {
  releaseModels();
  benchmarks.length=0;
  await originalLock();
};
$('lock').onclick=safe(lock);
$('model-install').onclick=safe(async()=>{
  const entries=(await models()).filter(row=>row.id!=='MiniLM-L6-ONNX-q8').sort((a,b)=>a.bytes-b.bytes);
  $('model-choice').replaceChildren(...entries.map(row=>{
    const option=element('option',row.id+' · '+(row.bytes/1048576).toFixed(0)+' MiB download');
    option.value=row.id;
    return option;
  }));
  $('model-details').textContent=entries.map(row=>row.id+' · '+row.license+' · revision '+row.source_revision+
    ' · estimated model VRAM '+row.vram_mb+' MiB').join('\n')+
    '\nThe 0.5B model completed desktop browser inference. The 4B download did not complete in this review. Physical-device acceptance is pending.\nDownload uses public licensed assets. Inference stays on this device. Peak browser memory and reliable physical-device support require measurement.';
  let adapter=null;
  if(navigator.gpu){try{adapter=await navigator.gpu.requestAdapter();}catch{adapter=null;}}
  $('model-load').disabled=!adapter;
  $('model-status').textContent=adapter?'DOWNLOAD_REQUIRED · select a model and explicitly install':'UNSUPPORTED · no WebGPU adapter available · local CPU retrieval and deterministic computation remain available';
  if(!adapter)$('chat-model-status').textContent='Local text generation unavailable in this browser session: no WebGPU adapter. Verified references and the deterministic engine remain available.';
});
$('model-load').onclick=safe(async()=>{
  if(!vault) throw Error('Unlock a synthetic local profile first.');
  if($('mode').value!=='FULL') throw Error('Model installation is available only in FULL mode.');
  const epoch=++modelEpoch;
  await cacheOptional(['webllm.js']);
  if(epoch!==modelEpoch||!vault||$('mode').value!=='FULL')return;
  localGeneration?.stop();
  localGeneration=new InferenceWorker($('model-status'));
  $('model-status').textContent='DOWNLOADING · integrity-verified public model assets';
  const result=await localGeneration.call('install',{id:$('model-choice').value});
  if(epoch!==modelEpoch) return;
  localGeneration.ready=true;
  benchmarks.push({...result,generated_json:undefined,text:undefined});
  $('model-status').textContent='READY · '+result.model+' · actual browser-local inference';
  $('model-benchmark').textContent=JSON.stringify(benchmarks,null,2);
});
$('model-stop').onclick=()=>{
  releaseModels();
  $('model-status').textContent='Model memory released · cached downloads retained · local fallback available';
  $('embedding-status').textContent='Embedding runtime released · lexical retrieval available';
};
$('embed-install').onclick=safe(async()=>{
  const model=(await models()).find(row=>row.id==='MiniLM-L6-ONNX-q8');
  $('embedding-status').textContent='DOWNLOAD_REQUIRED · '+(model.bytes/1048576).toFixed(1)+
    ' MiB model plus 21.6 MiB WASM runtime · Apache-2.0 · separate versioned MiniLM-L6 index';
  $('embed-load').disabled=false;
});
$('embed-load').onclick=safe(async()=>{
  if(!vault) throw Error('Unlock a synthetic local profile first.');
  if($('mode').value!=='FULL') throw Error('Embedding installation is available only in FULL mode.');
  await resources();
  const epoch=modelEpoch;
  await cacheOptional(['embedding-runtime/']);
  if(epoch!==modelEpoch||!vault||$('mode').value!=='FULL')return;
  localEmbedding?.stop();
  localEmbedding=new InferenceWorker($('embedding-status'));
  const model=(await models()).find(row=>row.id==='MiniLM-L6-ONNX-q8');
  const initialized=await localEmbedding.call('install',{id:model.id});
  const vectors=[];
  const start=performance.now();
  // The unchanged Python verifier checks provenance and quarantine before indexing.
  const verified=await call('verify_corpus',{corpus});
  for(const block of verified.blocks) {
    if(epoch!==modelEpoch||!vault)return;
    $('embedding-status').textContent='Building verified local index · '+vectors.length+'/'+verified.blocks.length;
    const result=await localEmbedding.call('embed',{text:block.text});
    vectors.push({id:block.id,vector:result.vector});
  }
  if(epoch!==modelEpoch) return;
  await saveIndex({model:model.id,revision:model.revision,corpus:corpus.sha256,vectors});
  localEmbedding.ready=true;
  benchmarks.push({...initialized,index_chunks:vectors.length,index_seconds:(performance.now()-start)/1000});
  $('model-benchmark').textContent=JSON.stringify(benchmarks,null,2);
  $('embedding-status').textContent='READY · '+vectors.length+' verified source vectors persisted locally';
});
async function localRetrieve(question,limit=3) {
  const lexical=await call('search',{corpus,question,limit:localEmbedding?.ready?32:limit});
  if($('mode').value!=='FULL'||!localEmbedding?.ready) return lexical.blocks.slice(0,limit);
  try {
    const model=(await models()).find(row=>row.id==='MiniLM-L6-ONNX-q8');
    const index=await readIndex();
    if(!index) return lexical.blocks.slice(0,limit);
    const query=await localEmbedding.call('embed',{text:question});
    const verified=await call('verify_corpus',{corpus});
    const semantic=vectorRank(verified.blocks,index,query.vector,corpus.sha256,model.revision,32);
    return fuseRankings(lexical.blocks,semantic,limit);
  } catch(error) {
    $('embedding-status').textContent='Local lexical fallback · '+error.message;
    return lexical.blocks.slice(0,limit);
  }
}
$('search').onclick=safe(async()=>{
  await resources();
  renderDocs($('citations'),await localRetrieve($('search-question').value));
  status('Local citation-verified retrieval complete.');
});
$('ask').onclick=safe(async()=>{
  if(!vault) throw Error('Unlock your local profile first.');
  await resources();
  const epoch=modelEpoch;
  const question=$('question').value.trim();
  if(question.length<3)throw Error('Enter a question of at least three characters.');
  const userMessage=element('div',question);userMessage.className='chat-message chat-user';userMessage.setAttribute('aria-label','Your question');$('answer').append(userMessage);
  $('question').value='';$('chat-model-status').textContent='Retrieving local evidence…';
  const context=await call('assistant_context',{question});
  if(['REFUSED_ACTION','CONTEXT_MISMATCH','INSUFFICIENT_INFORMATION'].includes(context.state)){
    const refusal=element('div',human(context.state));refusal.className='chat-message chat-assistant';refusal.setAttribute('aria-label','ASTHRAL response');$('answer').append(refusal);$('chat-model-status').textContent='The local evidence contract did not authorize an explanation for this question.';status(human(context.state));return;
  }
  const blocks=[...context.blocks.slice(0,2),...(await localRetrieve(question)).filter(b=>b.english_generation_eligible!==false).slice(0,2)];
  const response=element('div','');response.className='chat-message chat-assistant';response.setAttribute('aria-label','ASTHRAL response');
  if($('mode').value!=='FULL'||!localGeneration?.ready||question.length>600) {
    response.append(element('strong','Verified local evidence · text generation unavailable'));
    response.append(element('p','The on-device text model is not loaded or is disabled. The items below are verbatim local evidence; they are not a generated medical explanation.'));
    const citations=document.createElement('div');citations.className='chat-sources';renderDocs(citations,blocks);response.append(citations);$('answer').append(response);$('chat-model-status').textContent='Extractive fallback only · local text generation unavailable or disabled.';status('Displayed extractive evidence. No model generation was performed.');
    return;
  }
  $('model-status').textContent='Generating locally…';$('chat-model-status').textContent='Generating a response on this device…';
  const numeric=context.numeric&&/baseline|trend|change|recorded|measured|capacity|strength|sleep/i.test(question)?context.numeric:null;
  const result=await localGeneration.call('generate',{question,blocks,explain:true,prepared_messages:numeric?.prompt.messages,prepared_schema:numeric?.prompt.schema,prepared_max_tokens:numeric?.prompt.max_tokens});
  if(epoch!==modelEpoch) return;
  const metric={...result,generated_json:undefined,text:undefined};
  benchmarks.push(metric);
  $('model-status').textContent='READY · generation completed on this device';
  try {
    if(result.finish_reason==='length')throw Error('TRUNCATED_MODEL_RESPONSE');
    const generated=JSON.parse(result.generated_json);
    const checked=numeric?await call('validate_numeric_assistant',{generated,facts:numeric.facts}):await call('validate_assistant',{generated,blocks});
    if(epoch!==modelEpoch)return;
    if(!checked.sentences.length)throw Error('NO_SUPPORTED_GENERATED_EXPLANATION');
    metric.accepted=true;metric.validation_pending=false;metric.validation='PASSED_REFERENCE_VALIDATOR';
    response.append(element('strong','Local AI explanation · reviewed sources required'));
    for(const sentence of checked.sentences){const card=document.createElement('article');card.append(element('p',sentence.text),element('small','Sources '+sentence.evidence_ids.join(', ')+' · explanation only; no clinical authority'));if(numeric)card.append(element('p','Recorded synthetic cycle: '+numeric.as_of+' · descriptive historical data, not a live sensor reading.'));response.append(card);}
    $('answer').append(response);$('chat-model-status').textContent='Local response passed citation and consistency checks.';
    status('Local generation passed citation and clinical consistency gates. Deterministic results remain authoritative.');
  } catch(error){
    metric.accepted=false;metric.validation_pending=false;metric.validation='REJECTED_BY_REFERENCE_VALIDATOR';
    metric.validation_error_code=['CLINICAL_CLAIM_REQUIRES_EXACT_ENGINE_TEXT','FACT_SCOPE_MISMATCH','FACT_DOES_NOT_MATCH_STORED_REFERENCE','TRUNCATED_MODEL_RESPONSE','INVALID_GENERATED_SCHEMA','INVALID_SENTENCE','INVALID_CITATION','STRUCTURED_FACT_REALIZATION_REJECTED','OPTIONAL_DATA_REQUIRES_ENGINE_SUMMARY','CLINICAL_STATE_CONTRADICTION','UNSAFE_GENERATED_TEXT','UNSUPPORTED_NUMBER','ENGINE_EXPLANATION_REQUIRES_VERBATIM_SUPPORT','DOCUMENT_CANNOT_ESTABLISH_PERSONAL_MEASUREMENTS','NO_SUPPORTED_GENERATED_EXPLANATION'].find(code=>String(error).includes(code))??(error instanceof SyntaxError?'INVALID_MODEL_JSON':'REFERENCE_VALIDATION_FAILED');
    response.append(element('strong','Verified local evidence fallback'));
    response.append(element('p','The generated wording did not pass the reference checks. It was discarded; the items below are verbatim evidence and do not constitute a generated explanation.'));
    const citations=document.createElement('div');citations.className='chat-sources';renderDocs(citations,blocks);response.append(citations);$('answer').append(response);$('chat-model-status').textContent='Generated text rejected; verbatim evidence fallback shown.';
    status('Generated wording rejected by the reference safety contract.');
  } finally {$('model-benchmark').textContent=JSON.stringify(benchmarks,null,2);}
});
$('chat-form').onsubmit=safe(async()=>{ $('ask').click(); });
$('question').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('chat-form').requestSubmit();}});
$('chat-suggestions').addEventListener('click',event=>{const button=event.target.closest('[data-prompt]');if(button){$('question').value=button.dataset.prompt;$('question').focus();}});
$('workspace-nav').addEventListener('click',event=>{const link=event.target.closest('[data-view]');if(!link)return;event.preventDefault();location.hash=link.getAttribute('href');showWorkspaceView(link.dataset.view);});
$('workspace-nav').addEventListener('wheel',event=>{if(Math.abs(event.deltaY)>Math.abs(event.deltaX)){$('workspace-nav').scrollLeft+=event.deltaY;event.preventDefault();}},{passive:false});
window.addEventListener('asthral:notification-details',event=>{
  if(!vault){status('Unlock a local profile to view health records.');return;}
  const id=event.detail?.id;
  if(typeof id!=='string'||!id){status('The source record is unavailable.');return;}
  showWorkspaceView('history');
  const article=[...$('history-list').querySelectorAll('[data-record-id]')].find(item=>item.dataset.recordId===id);
  if(!article){status('The source record is unavailable in this profile. History remains available.');return;}
  const details=article.querySelector('details');if(details){details.classList.remove('developer-only');details.open=true;}
  article.scrollIntoView({block:'center',behavior:'instant'});article.tabIndex=-1;article.focus({preventScroll:true});status('Showing the recorded source event.');
});
window.addEventListener('hashchange',()=>{if(vault&&location.hash)showWorkspaceView(location.hash.slice(1));});
const floatingAssistant=element('div');floatingAssistant.className='floating-assistant';floatingAssistant.hidden=true;
const floatingToggle=element('button','ASTHRAL assistant');floatingToggle.type='button';floatingToggle.setAttribute('aria-expanded','false');
const floatingPanel=element('section');floatingPanel.className='floating-assistant-panel';floatingPanel.hidden=true;floatingPanel.setAttribute('aria-label','Contextual assistant');
const floatingText=element('p','No simulation warnings. Open Ask ASTHRAL to review recorded evidence.');
const floatingAnnouncement=element('p','');floatingAnnouncement.className='sr-only';floatingAnnouncement.setAttribute('role','status');floatingAnnouncement.setAttribute('aria-live','polite');
const activeTrainingWarnings=new Map();
const floatingOpen=element('button','Open Ask ASTHRAL');floatingOpen.type='button';floatingOpen.onclick=()=>{if(!vault)return;floatingPanel.hidden=true;floatingToggle.setAttribute('aria-expanded','false');showWorkspaceView('assistant');};
const floatingDetails=element('button','View details');floatingDetails.type='button';floatingDetails.hidden=true;floatingDetails.onclick=()=>{if(!vault)return;floatingPanel.hidden=true;floatingToggle.setAttribute('aria-expanded','false');showWorkspaceView('monitoring');requestAnimationFrame(()=>$('#physiology-simulator')?.scrollIntoView({behavior:'smooth',block:'start'}));};
floatingToggle.onclick=()=>{floatingPanel.hidden=!floatingPanel.hidden;floatingToggle.setAttribute('aria-expanded',String(!floatingPanel.hidden));};
floatingPanel.append(element('h2','ASTHRAL assistant'),floatingText,floatingAnnouncement,floatingDetails,floatingOpen);floatingAssistant.append(floatingPanel,floatingToggle);document.body.append(floatingAssistant);
window.addEventListener('asthral:viewchange',()=>{floatingAssistant.hidden=!vault||$('workspace').hidden;});
function renderTrainingNotifications(announcement=''){
 const current=[...activeTrainingWarnings.values()];
 floatingText.textContent=current.length?current.map(y=>{const shown=typeof y.value==='number'&&String(y.parameter).endsWith('_oxygen_partial_pressure')?y.value.toFixed(2):y.value;return `SIMULATION WARNING · ${y.label}: ${shown} ${y.unit} · ${y.rule} · illustrative rule ${y.version}.`;}).join(' ')+' No cause or treatment is inferred. Review simulated context.':announcement||'No active simulation warnings. This does not establish normal health.';
 floatingToggle.textContent=current.length?`ASTHRAL assistant · ${current.length} simulation notice${current.length===1?'':'s'}`:'ASTHRAL assistant';
 floatingDetails.hidden=!current.length;
 if(announcement)floatingAnnouncement.textContent=announcement;
}
window.addEventListener('asthral:simulation-transition',event=>{if(!vault)return;const x=event.detail;if(x.active)activeTrainingWarnings.set(x.parameter,x);else activeTrainingWarnings.delete(x.parameter);renderTrainingNotifications(x.active?`${x.label} crossed its configured synthetic training boundary.`:`${x.label} simulation warning cleared. This does not establish clinical recovery.`);});
window.addEventListener('asthral:simulation-value-update',event=>{if(!vault)return;const x=event.detail;if(activeTrainingWarnings.has(x.parameter)){activeTrainingWarnings.set(x.parameter,x);renderTrainingNotifications();}});
window.addEventListener('asthral:simulation-reset',()=>{activeTrainingWarnings.clear();renderTrainingNotifications('Simulation reset. No health records were changed.');});
$('mode').onchange=()=>{
  if($('mode').value!=='FULL') releaseModels();
  $('model-status').textContent=$('mode').value+' · local extractive fallback available';
};
async function cacheOptional(prefixes) {return cachePublicResources(prefixes);}
import {OfflineVoice} from './offline-voice.js';
let voiceDraft=null;
const offlineVoice=new OfflineVoice({
  cacheOptional,
  unlocked:()=>!!vault&&$('mode').value==='FULL',
  message:value=>{ $('voice-status').textContent=value; },
  transcript:value=>{
    if(!value)return;
    if(voiceTarget==='chat') {
      $('question').value=value.text;
      $('chat-voice-status').textContent='Transcript ready. Review the words, numbers and units, then press Send.';
      voiceTarget='observation';location.hash='#assistant';showWorkspaceView('assistant');return;
    }
    acceptTranscript(value).catch(error=>status(error.message));
  }
});
let voiceTarget='observation';
async function acceptTranscript(value) {
  if(!vault||!value?.text)return;
  const parsed=await call('parse_observation',{text:value.text});
  voiceDraft={...value,observation:parsed.observation};
  const policy=await call('voice_policy',{...value,auto_save:$('voice-auto').checked});
  if(policy.eligible){await call('save_observation',{...value,auto_save:true,source:'SELF_REPORTED_VOICE',validation:'AUTOMATIC_SELF_REPORT',clinical_eligibility:'NOT_AUTOMATICALLY_ASSESSED'});await persist();voiceDraft=null;$('observation-text').value='';$('voice-status').textContent=vault.temporary?'Eligible self-reported duration saved to temporary memory.':'Eligible self-reported duration committed to encrypted local storage.';return;}
  $('observation-text').value=value.text;
  $('voice-status').textContent=parsed.observation?
    'Local transcript ready · review numbers, units, negations and timing before saving.':
    'No clear intent to record a health observation. Nothing was saved.';
  $('record').disabled=false;
  $('stop-record').disabled=true;
}
$('voice-auto').disabled=false;
$('voice-auto').closest('label').append(element('small',' · Only explicit sleep/exercise reports for the past 24 hours with every word confidence at least 0.95 qualify. Physiological readings and symptoms require review.'));
$('voice-inspect').onclick=safe(async()=>{
  const model=await (await fetch('./voice-model.json')).json();
  $('voice-status').textContent='DOWNLOAD_REQUIRED · '+model.model+' · '+(model.bytes/1048576).toFixed(1)+
    ' MiB plus 5.5 MiB runtime · Apache-2.0 · offline English transcription';
  $('voice-install').disabled=false;
});
$('chat-microphone').onclick=safe(async()=>{
  if(!vault) throw Error('Open the synthetic demo or unlock a local profile first.');
  voiceTarget='chat';
  location.hash='#voice';showWorkspaceView('voice');
  if(!offlineVoice.model) {
    $('chat-voice-status').textContent='Offline voice model is not installed. Install local voice resources here before using the microphone.';
    $('voice-status').textContent='Voice model not installed. Review model details and install to enable recording.';
    return;
  }
  $('chat-voice-status').textContent='Requesting microphone access after your tap…';
  $('record').click();
});
$('voice-install').onclick=safe(async()=>{
  if(!vault)throw Error('Unlock a synthetic local profile first.');
  if($('mode').value!=='FULL')throw Error('Speech model loading requires FULL mode.');
  $('voice-status').textContent='Downloading and verifying the offline English speech model…';
  let result;
  try { result=await offlineVoice.install(); }
  catch(error) { $('voice-status').textContent='LOCAL_FALLBACK_AVAILABLE · '+error.message; throw error; }
  if(!vault){offlineVoice.close();return;}
  $('voice-status').textContent='READY · '+result.model+' · local WebAssembly speech recognition';
});
$('record').onclick=safe(async()=>{
  voiceDraft=null;
  $('record').disabled=true;
  $('stop-record').disabled=false;
  try {
    await offlineVoice.start();
    $('voice-status').textContent='RECORDING · microphone active · maximum 40 seconds · audio stays in memory';
  } catch(error) {
    $('record').disabled=false;
    $('stop-record').disabled=true;
    throw error;
  }
});
$('stop-record').onclick=safe(async()=>{
  $('voice-status').textContent='Microphone off · transcribing on this device…';
  await acceptTranscript(await offlineVoice.stop(true));
});
$('cancel-record').onclick=safe(async()=>{
  await offlineVoice.stop(false);
  voiceDraft=null;
  $('observation-text').value='';
  $('record').disabled=false;
  $('stop-record').disabled=true;
  $('voice-status').textContent='Canceled · microphone off · pending audio discarded';
});
$('voice-file').onchange=safe(async event=>{
  const file=event.target.files[0];
  if(!file)return;
  await acceptTranscript(await offlineVoice.fromAudioFile(file));
  event.target.value='';
});
$('observation-form').onsubmit=safe(async()=>{
  if(!vault)throw Error('Unlock your local profile first.');
  const content=$('observation-text').value;
  const parsed=await call('parse_observation',{text:content});
  if(voiceDraft&&!parsed.observation)throw Error('Voice entry needs an explicit health-report statement before saving.');
  await call('save_observation',{
    text:content,source:voiceDraft?'SELF_REPORTED_VOICE':'SELF_REPORTED_TYPED',
    observation:parsed.observation,confidence:voiceDraft?.words?.length?
      Math.min(...voiceDraft.words.map(word=>word.conf??0)):null,
    original_transcript:voiceDraft?.text??null,
    validation:'USER_REVIEWED_SELF_REPORT',clinical_eligibility:'NOT_AUTOMATICALLY_ASSESSED'
  });
  await persist();
  voiceDraft=null;
  $('observation-text').value='';
  status(vault.temporary?'Reviewed observation saved to temporary in-memory history.':'Reviewed observation saved in your encrypted local history.');
});
const lockBeforeVoice=lock;
lock=async function(){
  offlineVoice.close();
  voiceDraft=null;
  $('voice-file').value='';
  $('voice-status').textContent='Profile locked · pending speech discarded';
  await lockBeforeVoice();
};
$('lock').onclick=safe(lock);
document.addEventListener('visibilitychange',()=>{
  if(document.hidden)offlineVoice.stop(false);
});
const policyBeforeVoice=$('mode').onchange;
$('mode').onchange=()=>{
  if($('mode').value!=='FULL')offlineVoice.close();
  window.dispatchEvent(new CustomEvent('asthral:power-mode',{detail:{mode:$('mode').value}}));
  policyBeforeVoice();
};
let statisticsCases=[];
async function statisticsResources() {
  if(statisticsCases.length)return;
  statisticsCases=await (await fetch('./statistics-cases.json')).json();
  $('statistics-case').replaceChildren(...statisticsCases.map((sample,index)=>{
    const option=element('option',sample.kind+' · '+sample.snapshots[0].measurement.variable+' · '+sample.snapshots.length+' observations');
    option.value=String(index);
    return option;
  }));
}
$('statistics-run').onclick=safe(async()=>{
  if(!vault)throw Error('Unlock a local profile first.');
  await statisticsResources();
  const sample=statisticsCases[Number($('statistics-case').value)||0];
  if(!sample)throw Error('Statistical synthetic fixtures unavailable in this build.');
  const result=await call('statistics',{sample});
  await persist();
  $('statistics-output').textContent=JSON.stringify(result,null,2);
  const measurements=sample.snapshots.map(row=>row.measurement).sort((a,b)=>a.timestamp.localeCompare(b.timestamp));
  const minimum=Math.min(...measurements.map(row=>row.value));
  const maximum=Math.max(...measurements.map(row=>row.value));
  const span=maximum-minimum||1;
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox','0 0 600 160');
  svg.setAttribute('role','img');
  svg.setAttribute('aria-label','Synthetic observations used for the descriptive calculation');
  const start=Date.parse(measurements[0].timestamp);
  const duration=Date.parse(measurements.at(-1).timestamp)-start||1;
  for(const measurement of measurements) {
    const circle=document.createElementNS(svg.namespaceURI,'circle');
    circle.setAttribute('cx',String(30+540*(Date.parse(measurement.timestamp)-start)/duration));
    circle.setAttribute('cy',String(130-100*(measurement.value-minimum)/span));
    circle.setAttribute('r','5');
    circle.setAttribute('fill','#b3edd9');
    svg.append(circle);
  }
  $('statistics-chart').replaceChildren(svg,element('p',measurements[0].variable+' · '+measurements[0].unit+' · observed synthetic points'));
  status('Reference '+sample.kind+' recomputed locally · parity '+(result.reference_matches?'matched':'FAILED'));
});
const enteredBeforeStatistics=entered;
entered=async function(){await enteredBeforeStatistics();await statisticsResources();};
$('activate-update').onclick=safe(async()=>{
  if(vault)throw Error('Lock the profile before activating an application update.');
  const registration=await navigator.serviceWorker.getRegistration();
  if(!registration?.waiting)throw Error('No downloaded update is waiting.');
  navigator.serviceWorker.addEventListener('controllerchange',()=>location.reload(),{once:true});
  registration.waiting.postMessage({action:'ACTIVATE_UPDATE'});
});
experience=await installExperience({call,persist,isTemporary:()=>!!vault?.temporary});
missionSupport=installMissionSupport({call,persist,status,isTemporary:()=>!!vault?.temporary,mode:()=>$('mode')?.value??'FULL'});
preventiveExperience=installPreventiveExperience({call,persist,status,isTemporary:()=>!!vault?.temporary});
if(vault&&cases.length){experience.refresh();await experience.update();await history();}
clearPublicFeatures=await installPublicFeatures();

const speechRegression=element('button','Run synthetic offline speech regression');speechRegression.className='developer-only';$('voice').append(speechRegression);const speechReport=element('pre','');speechReport.id='speech-regression-report';speechReport.className='developer-only';$('voice').append(speechReport);
speechRegression.onclick=safe(async()=>{
 if(!vault||!offlineVoice.model)throw Error('Unlock a synthetic profile and load the offline speech model first.');
 speechRegression.disabled=true;
 try{const manifest=await(await fetch('./test-audio/manifest.json')).json(),results=[];
 for(const fixture of manifest){const response=await fetch('./test-audio/'+fixture.file),bytes=await response.arrayBuffer();const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(actual!==fixture.sha256)throw Error('Synthetic audio integrity failure.');
 const start=performance.now();const transcript=await offlineVoice.fromAudioFile(new File([bytes],fixture.file,{type:'audio/wav'}));const parsed=await call('parse_observation',{text:transcript.text}),expected=await call('parse_observation',{text:fixture.text});
 results.push({id:fixture.id,expected:fixture.text,actual:transcript.text,seconds:(performance.now()-start)/1000,exact_transcript:fixture.text.toLowerCase()===transcript.text,structured_values_match:JSON.stringify(parsed.observation?.values??null)===JSON.stringify(expected.observation?.values??null),parsed:parsed.observation,finalization:transcript.finalization,record_saved:false});speechReport.textContent=JSON.stringify(results,null,2);}
 status('Synthetic speech regression finished. No test audio or observations were saved. Review every mismatch.');
 }finally{speechRegression.disabled=false;}
});

const privacyCheck=element('button','Inspect network privacy evidence');privacyCheck.className='developer-only';$('advanced-settings').append(privacyCheck);const privacyOutput=element('pre','');privacyOutput.id='network-privacy-report';privacyOutput.className='developer-only';$('advanced-settings').append(privacyOutput);
privacyCheck.onclick=()=>{privacyOutput.textContent=JSON.stringify({observed_at:new Date().toISOString(),synthetic_sentinel:PRIVATE_SENTINEL,events:networkEvents,matching_attempts:networkEvents.filter(x=>x.contains_sentinel).length,network_writes:networkEvents.filter(x=>x.method!=='GET').length,scope:'APP_AND_MODEL_FETCH_INSTRUMENTATION_NOT_INDEPENDENT_PACKET_CAPTURE',limitations:['Redirect internals and native browser voice engines are not instrumented.','No claim against compromised same-origin code or operating system.']},null,2);};

const performanceCheck=element('button','Inspect measured workflow latency');performanceCheck.className='developer-only';$('advanced-settings').append(performanceCheck);const measuredPerformance=element('pre','');measuredPerformance.id='workflow-performance-report';measuredPerformance.className='developer-only';$('advanced-settings').append(measuredPerformance);performanceCheck.onclick=()=>{measuredPerformance.textContent=JSON.stringify({observed_at:new Date().toISOString(),python_startup_seconds:runtimeState.seconds,operations:operationMetrics,peak_memory:'NOT_MEASURED',thermal_energy:'NOT_MEASURED',physical_mobile:'NOT_TESTED'},null,2);};

const loadMission=element('button','Load synthetic mission observations');$('anatomy').append(loadMission);const missionNotice=element('p','Disposable demo only: five synthetic measurements, a personal baseline and a real monitoring cycle. No connected sensor or actual treatment is implied.');loadMission.after(missionNotice);
loadMission.onclick=safe(async()=>{
 if(!vault?.temporary)throw Error('Use a new temporary synthetic demo for the seeded mission. Persistent profiles are not modified by this generator.');
 const existing=await call('timeline');if(existing.measurement.length||existing.monitoring_run.length)throw Error('This demo already contains measurements. Lock it and open a new temporary demo to start another seeded mission.');
 loadMission.disabled=true;
 try{const fixture=await(await fetch('./monitor-fixture.json')).json();let result;
 for(const step of fixture.steps){const data=structuredClone(step.data);if(step.action==='ingest')Object.assign(data.measurement,{subject_id:owner,mission_id:'browser-mission'});if(step.action==='monitor')Object.assign(data,{subject_id:owner,mission_id:'browser-mission'});result=await call(step.action,data);}
 const replay=await call('replay_monitor',{id:result.id});await persist();await experience.update();status(replay.matches?'Synthetic mission calculated and frozen cycle reproduced exactly. All treatment execution remains blocked.':'REPLAY MISMATCH — integration must stop.');
 }finally{loadMission.disabled=false;}
});

function bindLocalImageReview(inputId,previewId,statusId,allowedTypes,maxBytes=10*1024*1024) {
  let objectUrl=null;
  $(inputId).addEventListener('change',safe(async event=>{
    const file=event.target.files?.[0];$(previewId).replaceChildren();
    if(objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null;}
    if(!file){$(statusId).textContent='No image selected.';return;}
    if(!allowedTypes.includes(file.type)||file.size===0||file.size>maxBytes)throw Error('Choose a supported image under 10 MiB. The file was not retained.');
    const bitmap=await createImageBitmap(file);
    if(bitmap.width<64||bitmap.height<64||bitmap.width>8192||bitmap.height>8192){bitmap.close();throw Error('Image dimensions are outside the supported intake range (64–8192 pixels).');}
    objectUrl=URL.createObjectURL(file);
    const img=document.createElement('img');img.alt='Temporary local image preview';img.src=objectUrl;
    const metadata=element('p',file.type+' · '+(file.size/1048576).toFixed(2)+' MiB · '+bitmap.width+' × '+bitmap.height+' pixels · preview in memory only');bitmap.close();
    $(previewId).append(img,metadata);
    $(statusId).textContent='Intake checks passed. No compatible model is packaged for analysis; no clinical result was produced.';
  }));
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null;$(previewId).replaceChildren();$(inputId).value='';}});
}
bindLocalImageReview('ocular-file','ocular-preview','ocular-status',['image/png','image/jpeg']);
bindLocalImageReview('skin-file','skin-preview','skin-status',['image/png','image/jpeg']);
