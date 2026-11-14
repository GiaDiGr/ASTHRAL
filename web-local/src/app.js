import {Vault} from './vault.js';
const $=id=>document.getElementById(id);
const runtimeState={ready:false,seconds:null};
let recordingEpoch=0,profileEpoch=0;
let worker,serial=0,vault=null,owner=null,cases=[],corpus=null,stream=null;
const waiting=new Map();

function element(tag,value) {
  const node=document.createElement(tag);
  node.textContent=value;
  return node;
}
function status(value) { $('operation').textContent=value; }
function startWorker() {
  worker=new Worker('./worker.js?v=5');
  worker.onmessage=event=>{
    const value=event.data;
    if(value.type==='ready') {
      runtimeState.ready=true;
      runtimeState.seconds=value.seconds;
      $('runtime-status').textContent='Reference Python engine ready on this device · '+value.seconds.toFixed(2)+' seconds';
      return;
    }
    if(value.type==='failed') {
      $('runtime-status').textContent='Local runtime failed. '+value.error;
      return;
    }
    const pending=waiting.get(value.id);
    if(pending) {
      waiting.delete(value.id);
      if(pending.epoch!==profileEpoch)pending.reject(Error('Profile changed while the operation was pending.'));
      else value.error?pending.reject(Error(value.error)):pending.resolve(value.result);
    }
  };
  worker.onerror=()=>{ $('runtime-status').textContent='Local worker failed. Reload and inspect device diagnostics.'; };
}
function call(action,data) {
  return new Promise((resolve,reject)=>{
    const id=++serial;
    waiting.set(id,{resolve,reject,epoch:profileEpoch});
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
  cases=await (await fetch('./parity-cases.json')).json();
  corpus=await (await fetch('./corpus.json')).json();
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
  $('metrics').replaceChildren(...row.snapshot.observations.slice(0,12).map(value=>{
    const card=document.createElement('article');
    card.append(element('strong',value.concept),element('p',String(value.value??'Not measured')+' '+value.unit),element('small',value.timestamp+' · '+value.quality+' · '+value.method));
    return card;
  }));
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
  $('workspace').hidden=false;
  $('profiles').hidden=true;
  $('lock').hidden=false;
  $('scope').textContent=(vault.temporary?'Temporary synthetic demo · memory only · ':'Encrypted synthetic local profile · ')+owner;
  selectCase();
  await history();
}
async function persist() {
  if(!vault.temporary)await vault.save(await call('serialize'));
  await history();
}
async function history() {
  const epoch=profileEpoch;
  const data=await call('history');
  if(epoch!==profileEpoch||!vault)return;
  const latest=data.evaluations.at(-1);
  $('emergency-banner').hidden=!latest||!['EMERGENCY','URGENT'].includes(latest.output.urgency);
  $('emergency-banner').textContent=latest?latest.output.urgency+' · Last saved synthetic assessment · Human medical review required · Treatment blocked':'';
  const rows=[
    ...data.evaluations.map(row=>({label:row.output.urgency+' · '+(row.snapshot.request.condition_id||'Differential'),detail:row.output})),
    ...data.observations.map(row=>({label:row.text,detail:row}))
  ];
  $('history-list').replaceChildren();
  for(const row of rows.reverse()) {
    const article=document.createElement('article');
    const details=document.createElement('details');
    details.append(element('summary','Record and provenance'),element('pre',JSON.stringify(row.detail,null,2)));
    article.append(element('strong',row.label),details);
    $('history-list').append(article);
  }
  if(!rows.length) $('history-list').append(element('p','No local observations or evaluations saved.'));
  $('profile-status').textContent='Unlocked · audit '+(data.audit_valid?'verified':'FAILED');
}
async function lock() {
  profileEpoch++;
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
  $('profiles').hidden=false;
  $('lock').hidden=true;
  for(const id of ['history-list','assessment','clinical-output','management','urgency','citations','answer','statistics-output','statistics-chart','metrics','model-benchmark']) $(id).replaceChildren();
  for(const id of ['observation-text','scenario','question','search-question'])$(id).value='';
  $('model-status').textContent='Profile locked · local inference released';
  status('Profile locked.');
  $('profile-status').textContent='Profile locked';
  await listProfiles();
}
$('create-form').onsubmit=safe(async()=>{
  if(vault) throw Error('Lock your current profile first.');
  const password=$('create-password').value;
  try {
    owner='profile-'+crypto.randomUUID();
    await call('init_profile',{id:owner});
    vault=await Vault.create($('profile-label').value,password,owner);
    await persist();
    await entered();
    status('Encrypted local profile created. Export a backup and retain your passphrase.');
  } finally { $('create-password').value=''; }
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
  status('Temporary synthetic demo ready. Records stay in memory and are discarded when this page closes. Create a local profile for encrypted persistence.');
  $('workspace').scrollIntoView({behavior:'smooth'});
});
$('case-list').onchange=selectCase;
$('evaluate').onclick=safe(async()=>{
  if(!vault) throw Error('Unlock a local profile first.');
  status('Computing locally in the Python WebAssembly worker…');
  const epoch=profileEpoch;
  const result=await call('evaluate',{snapshot:JSON.parse($('scenario').value)});
  await persist();
  if(epoch!==profileEpoch||!vault)return;
  $('urgency').textContent=result.output.urgency+' · Treatment execution blocked';
  $('urgency').className=['URGENT','EMERGENCY'].includes(result.output.urgency)?'emergency':'';
  $('assessment').replaceChildren();
  for(const [name,value] of Object.entries(result.output.results)) {
    const card=document.createElement('article');
    card.append(
      element('h3',name),
      element('p','Criteria '+value.diagnostic_status+' · Confirmation '+value.confirmation_status),
      element('p','Missing required '+(value.missing_required.join(', ')||'None')),
      element('p','Unmeasured alternatives '+(value.optional_not_measured.join(', ')||'None')),
      element('p','Protocol safety '+(value.required_for_protocol_safety.join(', ')||'None')),
      element('p','Protocol '+value.protocol_status)
    );
    $('assessment').append(card);
  }
  $('clinical-output').textContent=JSON.stringify(result,null,2);
  const management=result.output.management||{state:'Documentary resource mapping unavailable for this context',treatment:'BLOCKED'};
  $('management').replaceChildren();
  for(const [route,guide] of Object.entries(management)) {
    const card=document.createElement('article');
    card.append(element('strong',route),element('p','Documented reference · execution blocked'));
    for(const intervention of guide.interventions??[]) {
      card.append(element('p',intervention.title+' · '+intervention.resource_status+' · '+intervention.authorization));
    }
    const details=document.createElement('details');
    details.append(element('summary','Original guidance, resource checks and source metadata'),element('pre',JSON.stringify(guide,null,2)));
    card.append(details);
    $('management').append(card);
  }
  status(vault.temporary?'Assessment computed in the temporary synthetic demo. Closing this page discards it.':'Assessment computed on this device and saved to the encrypted profile.');
});
$('run-parity').onclick=safe(async()=>{
  await resources();
  status('Running real Python computations against reference outputs…');
  const result=await call('parity',{cases});
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
    article.append(element('strong',block.id),element('p',block.text),
      element('small',block.reference.document+' · '+block.reference.authority+' · SHA-256 '+block.reference.sha256));
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
$('install-offline').onclick=safe(async()=>{
  if(!('serviceWorker'in navigator)) throw Error('Offline installation unsupported.');
  const manifest=await (await fetch('./assets.json')).json();
  const size=manifest.files.filter(file=>!file.optional).reduce((sum,file)=>sum+file.size,0)/1048576;
  status('Installing '+size.toFixed(1)+' MiB of versioned application resources…');
  const registration=await navigator.serviceWorker.register('./sw.js');
  if(registration.installing) {
    await new Promise((resolve,reject)=>{
      const installing=registration.installing;
      installing.addEventListener('statechange',()=>{
        if(installing.state==='installed')resolve();
        if(installing.state==='redundant')reject(Error('Offline installation failed integrity or quota checks.'));
      });
    });
  }
  if(registration.waiting) {
    $('activate-update').hidden=false;
    status('Verified update downloaded. Lock the profile and activate the update when ready.');
    return;
  }
  await navigator.serviceWorker.ready;
  const persistent=await navigator.storage?.persist?.();
  status('Offline resources installed. Persistent storage '+(persistent?'granted':'not granted')+'. Test an offline reload on your device.');
});

import {saveIndex,readIndex,hybridRank} from './vectors.js';
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
  $('model-load').disabled=!navigator.gpu;
  $('model-status').textContent=navigator.gpu?'DOWNLOAD_REQUIRED · select a model and explicitly install':'UNSUPPORTED · WebGPU unavailable · local extractive fallback available';
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
  benchmarks.push(result);
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
  for(const block of corpus.blocks) {
    const verification=await call('search',{corpus,question:block.text,limit:corpus.blocks.length});
    if(!verification.blocks.some(row=>row.id===block.id)) continue;
    const result=await localEmbedding.call('embed',{text:block.text});
    vectors.push({id:block.id,vector:result.vector});
  }
  if(epoch!==modelEpoch) return;
  await saveIndex({model:model.id,revision:model.revision,corpus:corpus.sha256,vectors});
  localEmbedding.ready=true;
  benchmarks.push({...initialized,index_chunks:vectors.length,index_seconds:(performance.now()-start)/1000});
  $('model-benchmark').textContent=JSON.stringify(benchmarks,null,2);
  $('embedding-status').textContent='READY · '+vectors.length+' scientific vectors persisted locally';
});
async function localRetrieve(question,limit=3) {
  const lexical=await call('search',{corpus,question,limit:localEmbedding?.ready?32:limit});
  if($('mode').value!=='FULL'||!localEmbedding?.ready) return lexical.blocks.slice(0,limit);
  try {
    const model=(await models()).find(row=>row.id==='MiniLM-L6-ONNX-q8');
    const index=await readIndex();
    if(!index) return lexical.blocks.slice(0,limit);
    const query=await localEmbedding.call('embed',{text:question});
    return hybridRank(lexical.blocks,index,query.vector,corpus.sha256,model.revision).slice(0,limit);
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
  const question=$('question').value;
  const blocks=await localRetrieve(question);
  renderDocs($('answer'),blocks);
  if($('mode').value!=='FULL'||!localGeneration?.ready) {
    status('Extractive local results · local text generation unavailable or disabled by energy policy.');
    return;
  }
  $('model-status').textContent='GENERATING · local GPU';
  const result=await localGeneration.call('generate',{question,blocks});
  if(epoch!==modelEpoch) return;
  benchmarks.push(result);
  $('model-benchmark').textContent=JSON.stringify(benchmarks,null,2);
  $('model-status').textContent='READY · generation completed on this device';
  if(result.accepted) {
    const card=document.createElement('article');
    card.append(element('strong','Exact source quotation selected by the local model'),
      element('p',result.text),element('small','Source '+result.citation+' · no clinical authority'));
    $('answer').prepend(card);
    status('Accepted local model quotation. Engine decisions remain authoritative.');
  } else status('Local inference completed. Generated wording failed exact citation verification; extractive results remain available.');
});
$('mode').onchange=()=>{
  if($('mode').value!=='FULL') releaseModels();
  $('model-status').textContent=$('mode').value+' · local extractive fallback available';
};

async function cacheOptional(prefixes) {
  const manifest=await (await fetch('./assets.json')).json();
  const cache=await caches.open('asthral-optional-resources-v1');
  for(const asset of manifest.files.filter(row=>prefixes.some(prefix=>row.path===prefix||row.path.startsWith(prefix)))) {
    const url=new URL('./'+asset.path,location.href);
    let response=await cache.match(url);
    if(!response)response=await fetch(url);
    if(!response.ok)throw Error('Optional runtime download failed.');
    const bytes=await response.arrayBuffer();
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if(hash!==asset.sha256)throw Error('Optional runtime integrity failed.');
    const mime=asset.path.endsWith('.js')||asset.path.endsWith('.mjs')?'text/javascript':asset.path.endsWith('.wasm')?'application/wasm':'application/octet-stream';
    await cache.put(url,new Response(bytes,{headers:{'Content-Type':mime}}));
  }
}

import {OfflineVoice} from './offline-voice.js';
let voiceDraft=null;
const offlineVoice=new OfflineVoice({
  cacheOptional,
  unlocked:()=>!!vault&&$('mode').value==='FULL',
  message:value=>{ $('voice-status').textContent=value; },
  transcript:value=>{ if(value) acceptTranscript(value).catch(error=>status(error.message)); }
});
async function acceptTranscript(value) {
  if(!vault||!value?.text)return;
  const parsed=await call('parse_observation',{text:value.text});
  voiceDraft={...value,observation:parsed.observation};
  $('observation-text').value=value.text;
  $('voice-status').textContent=parsed.observation?
    'Local transcript ready · review numbers, units, negations and timing before saving.':
    'No clear intent to record a health observation. Nothing was saved.';
  $('record').disabled=false;
  $('stop-record').disabled=true;
}
$('voice-auto').disabled=true;
$('voice-auto').closest('label').append(element('small',' · Browser recognizer finalization requires review. Automatic persistence is blocked.'));
$('voice-inspect').onclick=safe(async()=>{
  const model=await (await fetch('./voice-model.json')).json();
  $('voice-status').textContent='DOWNLOAD_REQUIRED · '+model.model+' · '+(model.bytes/1048576).toFixed(1)+
    ' MiB plus 5.5 MiB runtime · Apache-2.0 · offline English transcription';
  $('voice-install').disabled=false;
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
