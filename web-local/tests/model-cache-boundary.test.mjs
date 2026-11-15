import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
const source=(await readFile(new URL('../src/ml-worker.js',import.meta.url),'utf8')).replace("import {auditedFetch} from './network-audit.js';",'const auditedFetch=fetcher=>fetcher;').replace("const {CreateMLCEngine}=await import('./webllm.js');",'const CreateMLCEngine=fakeCreateEngine;');
const hash=async raw=>Buffer.from(await webcrypto.subtle.digest('SHA-256',raw)).toString('hex');
async function fixture(corrupt=false){
 const data=[['mlc-chat-config.json','{"synthetic":true}'],['tokenizer.json','{"synthetic":"tokenizer"}'],['params_shard_0.bin','SYNTHETIC_WEIGHTS_NOT_A_MODEL'],['model.wasm','SYNTHETIC_WASM_NOT_EXECUTABLE']];
 const files=await Promise.all(data.map(async([name,text])=>{const raw=new TextEncoder().encode(text);return {url:'https://public.example/pinned/'+name,size:raw.length,sha256:await hash(raw),raw};}));
 const model={id:'SYNTHETIC_TEST_MODEL',model:'https://public.example/pinned/',model_lib:files.at(-1).url,files,bytes:files.reduce((n,f)=>n+f.size,0),vram_mb:1};
 const stores=new Map(),requests=[],messages=[];let initialized=false;
 const caches={open:async name=>{if(!stores.has(name))stores.set(name,new Map());const rows=stores.get(name);return {match:async key=>rows.get(String(key))?.clone(),put:async(key,value)=>rows.set(String(key),value.clone()),delete:async key=>rows.delete(String(key)),keys:async()=>[...rows.keys()].map(url=>({url}))};}};
 await(await caches.open('webllm/model')).put(files[2].url,new Response('STALE_UNVERIFIED_RUNTIME_CACHE'));
 if(corrupt)await(await caches.open('asthral-approved-models-v1')).put(files[2].url,new Response('CORRUPTED_APPROVED_CACHE'));
 const self={location:{href:'https://synthetic.example/ml-worker.js',origin:'https://synthetic.example'},postMessage:m=>messages.push(m),fetch:async input=>{const url=String(input);if(url==='./models.json')return Response.json({models:[model]});requests.push(url);const file=files.find(f=>f.url===url);assert.ok(file,'unapproved request rejected');return new Response(file.raw);}};
 const fakeCreateEngine=async()=>{initialized=true;for(const file of files){const scope=file.url===model.model_lib?'webllm/wasm':file.url.endsWith('/mlc-chat-config.json')?'webllm/config':'webllm/model';const response=await(await caches.open(scope)).match(file.url);assert.ok(response,'runtime must find a seeded cache entry instead of calling Cache.add');assert.equal(await hash(await response.arrayBuffer()),file.sha256);}return {};};
 const context=vm.createContext({self,caches,Response,URL,Blob,crypto:webcrypto,performance,navigator:{gpu:{}},setTimeout,fakeCreateEngine});vm.runInContext(source,context);
 self.onmessage({data:{id:'test-install',action:'install',data:{id:model.id}}});await vm.runInContext('queue',context);return {initialized,requests,messages,files};
}
test('WebLLM caches receive exact verified public bytes before runtime initialization',async()=>{
 const result=await fixture();assert.equal(result.initialized,true);assert.equal(result.requests.length,4);assert.equal(result.messages.at(-1).result.state,'READY');
});
test('corrupted approved bytes block runtime initialization instead of seeding model caches',async()=>{
 const result=await fixture(true);assert.equal(result.initialized,false);assert.match(result.messages.at(-1).error,/integrity verification failed/);
});
