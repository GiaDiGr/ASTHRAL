/* Model downloads contain only public, pinned assets. Inference stays in this worker. */
import {auditedFetch} from './network-audit.js';
const originalFetch=auditedFetch(self.fetch.bind(self),event=>self.postMessage({type:'network_audit',event}));
const catalog=(async()=>await (await originalFetch('./models.json')).json())();
const hex=bytes=>[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
let allowed=new Map();
let downloadQueue=Promise.resolve();
let engine=null,embedder=null,selected=null;
let completedBytes=0,totalBytes=0;

async function downloadPublicAsset(file) {
  const partial=await caches.open('asthral-public-download-parts-v1');
  const step=8*1024*1024;
  if(file.size<16*1024*1024)return originalFetch(file.url,{credentials:'omit',referrerPolicy:'no-referrer'});
  const parts=[];
  for(let start=0;start<file.size;start+=step){
    const end=Math.min(start+step,file.size)-1;
    const key=new URL('./public-model-parts/'+file.sha256+'/'+start,self.location.href);
    let response=await partial.match(key);
    if(!response){
      response=await originalFetch(file.url,{headers:{Range:'bytes='+start+'-'+end},credentials:'omit',referrerPolicy:'no-referrer'});
      if(response.status===200){if(start!==0)throw Error('Range capability changed during public download.');return response;}
      if(response.status!==206||response.headers.get('Content-Range')!=='bytes '+start+'-'+end+'/'+file.size)throw Error('Public range response did not match the pinned asset.');
      const raw=await response.arrayBuffer();
      if(raw.byteLength!==end-start+1)throw Error('Interrupted public model range. Completed ranges remain resumable.');
      response=new Response(raw);await partial.put(key,response.clone());
    }
    const raw=await response.arrayBuffer();
    if(raw.byteLength!==end-start+1){await partial.delete(key);throw Error('Invalid cached public range.');}
    parts.push(raw);
    self.postMessage({type:'status',state:'DOWNLOADING_RESUMABLE',received:completedBytes+end+1,total:totalBytes});
  }
  return new Response(new Blob(parts)); // official complete-file SHA-256 is checked before execution/cache admission
}

async function verifiedAsset(url) {
  const normalized=new URL(url,self.location.href).href.split('?')[0];
  const file=allowed.get(normalized);
  if(!file) throw Error('Unapproved model asset request blocked.');
  const cache=await caches.open('asthral-approved-models-v1');
  let response=await cache.match(normalized);
  if(!response) {
    let failure;
    for(let attempt=0;attempt<3;attempt++) {
      try {
        response=await downloadPublicAsset(file);
        if(response.ok) { failure=null; break; }
        throw Error('HTTP '+response.status);
      } catch(error) {
        failure=error;
        await new Promise(resolve=>setTimeout(resolve,1000*(attempt+1)));
      }
    }
    if(failure) throw Error('Public model asset unavailable: '+normalized.split('/').at(-1)+' · '+String(failure));
  }
  const bytes=await response.arrayBuffer();
  if(bytes.byteLength!==file.size||hex(await crypto.subtle.digest('SHA-256',bytes))!==file.sha256) {
    await cache.delete(normalized);
    const partial=await caches.open('asthral-public-download-parts-v1'),prefix=new URL('./public-model-parts/'+file.sha256+'/',self.location.href).href;
    for(const key of await partial.keys())if(key.url.startsWith(prefix))await partial.delete(key);
    throw Error('Model asset integrity verification failed. Unverified partial bytes were discarded.');
  }
  const verified=new Response(bytes,{headers:{'Content-Type':normalized.endsWith('.json')?'application/json':'application/octet-stream'}});
  await cache.put(normalized,verified.clone());
  completedBytes+=file.size;
  self.postMessage({type:'status',state:'VERIFYING_INTEGRITY',received:completedBytes,total:totalBytes});
  return verified;
}
self.fetch=(input,options)=>{
  const url=typeof input==='string'?input:input.url??String(input);
  const absolute=new URL(url,self.location.href);
  const method=options?.method??(typeof input==='object'?input.method:'GET')??'GET';
  if(method!=='GET') return Promise.reject(Error('Model runtime network writes blocked.'));
  if(absolute.origin===self.location.origin){
    if(!/\/(?:models\.json|embedding-runtime\/[A-Za-z0-9_.-]+|webllm\.js)$/.test(absolute.pathname)||absolute.search&&!/^\?asthral=2$/.test(absolute.search))return Promise.reject(Error('Unapproved same-origin model request.'));
    return originalFetch(input,options);
  }
  const task=downloadQueue.then(()=>verifiedAsset(absolute.href));
  downloadQueue=task.catch(()=>{});
  return task;
};

async function install(id) {
  const models=(await catalog).models;
  selected=models.find(model=>model.id===id);
  if(!selected) throw Error('Model not approved.');
  allowed=new Map(models.flatMap(model=>model.files.map(file=>[file.url,file])));
  completedBytes=0;
  totalBytes=selected.bytes;
  self.postMessage({type:'status',state:'DOWNLOADING',total:totalBytes,received:0});
  for(const file of selected.files) {
    const verified=await verifiedAsset(file.url);
    // WebLLM Cache.add() bypasses the overridden fetch. Seed its exact public
    // cache keys with verified bytes so runtime initialization needs no second download.
    if(id!=='MiniLM-L6-ONNX-q8') {
      const scope=file.url===selected.model_lib?'webllm/wasm':file.url.endsWith('/mlc-chat-config.json')?'webllm/config':'webllm/model';
      await (await caches.open(scope)).put(file.url,verified);
    }
  }
  self.postMessage({type:'status',state:'LOADING'});
  const started=performance.now();
  if(id==='MiniLM-L6-ONNX-q8') {
    const {pipeline,env}=await import('./embedding-runtime/transformers.min.js');
    env.allowLocalModels=false;
    env.useBrowserCache=false;
    env.backends.onnx.wasm.numThreads=1;
    env.backends.onnx.wasm.wasmPaths={mjs:new URL('./embedding-runtime/ort-wasm-simd-threaded.jsep.mjs?asthral=2',self.location.href).href,wasm:new URL('./embedding-runtime/ort-wasm-simd-threaded.jsep.wasm',self.location.href).href};
    embedder=await pipeline('feature-extraction',selected.model,{revision:selected.revision,quantized:true,dtype:'q8',device:'wasm'});
  } else {
    if(!navigator.gpu) throw Error('WebGPU is unavailable. Local extractive fallback remains available.');
    const {CreateMLCEngine}=await import('./webllm.js');
    const record={
      model:selected.model,model_id:selected.id,model_lib:selected.model_lib,
      vram_required_MB:selected.vram_mb,low_resource_required:true,
      overrides:{context_window_size:2048}
    };
    engine=await CreateMLCEngine(selected.id,{
      appConfig:{model_list:[record],useIndexedDBCache:false},
      initProgressCallback:value=>self.postMessage({type:'status',state:'LOADING',progress:value.progress,text:value.text})
    });
  }
  return {state:'READY',model:id,init_seconds:(performance.now()-started)/1000,local_execution:true};
}

let queue=Promise.resolve();
self.onmessage=event=>{
  const message=event.data;
  queue=queue.then(async()=>{
    try {
      let result;
      if(message.action==='install') result=await install(message.data.id);
      else if(message.action==='embed') {
        if(!embedder) throw Error('Embedding model not loaded.');
        const value=await embedder(message.data.text,{pooling:'mean',normalize:true});
        result={vector:Array.from(value.data),model:selected.id,revision:selected.revision};
      } else if(message.action==='generate') {
        if(!engine) throw Error('Local model not loaded.');
        const start=performance.now();
        let firstToken=null,tokens=0,text='',finishReason=null;
        const configuration=message.data.explain?await(await originalFetch('./assistant-config.json')).json():null;
        const messages=message.data.prepared_messages??(message.data.explain?[{role:'system',content:configuration.system},{role:'user',content:JSON.stringify({question:message.data.question,evidence:message.data.blocks.map(block=>({id:block.id,kind:block.kind,text:block.kind==='ENGINE'?block.text:block.text.slice(0,600)}))})}]:null);
        const stream=await engine.chat.completions.create({
          messages:[
            {role:'system',content:'Select one short exact quotation from the provided source excerpts. Output only that exact quotation. Never diagnose, prescribe, change a stored decision or infer missing information. If no excerpt matches, output INSUFFICIENT_EVIDENCE.'},
            {role:'user',content:JSON.stringify({question:message.data.question,excerpts:message.data.blocks.map(block=>({id:block.id,text:block.text}))})}
          ],temperature:0,max_tokens:message.data.prepared_messages?400:(message.data.explain?configuration.max_tokens:192),stream:true,
          ...(message.data.explain?{response_format:{type:'json_object',schema:JSON.stringify(message.data.prepared_schema??configuration.schema)}}:{}),
          ...(messages?{messages}:{})
        });
        for await(const part of stream) {
          finishReason=part.choices[0]?.finish_reason??finishReason;
          const delta=part.choices[0]?.delta?.content??'';
          if(delta) {
            if(firstToken===null) firstToken=(performance.now()-start)/1000;
            text+=delta;
            tokens++;
          }
        }
        const elapsed=(performance.now()-start)/1000;
        const match=message.data.blocks.find(block=>block.text.includes(text.trim()));
        result={...(message.data.explain?{generated_json:text}:{}),text:match?text.trim():null,citation:match?.id??null,accepted:message.data.explain?null:!!match,validation_pending:!!message.data.explain,finish_reason:finishReason,
                raw_output_withheld:!match,model:selected.id,local_execution:true,
                time_to_first_token_seconds:firstToken,seconds:elapsed,
                emitted_chunks:tokens,chunks_per_second:tokens/elapsed,
                actual_token_throughput:'SEE_RUNTIME_STATS',runtime_stats:await engine.runtimeStatsText()};
      } else throw Error('Unsupported local model action.');
      self.postMessage({id:message.id,result});
    } catch(error) {
      self.postMessage({id:message.id,error:String(error),state:'LOCAL_FALLBACK_AVAILABLE'});
    }
  });
};
