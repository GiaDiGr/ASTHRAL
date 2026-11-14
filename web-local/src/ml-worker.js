/* Model downloads contain only public, pinned assets. Inference stays in this worker. */
const originalFetch=self.fetch.bind(self);
const catalog=(async()=>await (await originalFetch('./models.json')).json())();
const hex=bytes=>[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
let allowed=new Map();
let downloadQueue=Promise.resolve();
let engine=null,embedder=null,selected=null;
let completedBytes=0,totalBytes=0;

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
        response=await originalFetch(normalized,{credentials:'omit',referrerPolicy:'no-referrer'});
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
    throw Error('Model asset integrity verification failed.');
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
  if(absolute.origin===self.location.origin) return originalFetch(input,options);
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
  for(const file of selected.files) await verifiedAsset(file.url);
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
        let firstToken=null,tokens=0,text='';
        const stream=await engine.chat.completions.create({
          messages:[
            {role:'system',content:'Select one short exact quotation from the provided source excerpts. Output only that exact quotation. Never diagnose, prescribe, change a stored decision or infer missing information. If no excerpt matches, output INSUFFICIENT_EVIDENCE.'},
            {role:'user',content:JSON.stringify({question:message.data.question,excerpts:message.data.blocks.map(block=>({id:block.id,text:block.text}))})}
          ],temperature:0,max_tokens:128,stream:true
        });
        for await(const part of stream) {
          const delta=part.choices[0]?.delta?.content??'';
          if(delta) {
            if(firstToken===null) firstToken=(performance.now()-start)/1000;
            text+=delta;
            tokens++;
          }
        }
        const elapsed=(performance.now()-start)/1000;
        const match=message.data.blocks.find(block=>block.text.includes(text.trim()));
        result={text:match?text.trim():null,citation:match?.id??null,accepted:!!match,
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
