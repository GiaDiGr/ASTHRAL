import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
const origin='https://synthetic.example/';
const hash=async bytes=>Buffer.from(await webcrypto.subtle.digest('SHA-256',bytes)).toString('hex');
function redirected(response){Object.defineProperty(response,'redirected',{value:true});const clone=response.clone.bind(response);response.clone=()=>redirected(clone());return response;}
const absolute=key=>new URL(typeof key==='string'?key:(key.url??key.href),origin).href;
function storage(){const stores=new Map();return {keys:async()=>[...stores.keys()],open:async name=>{if(!stores.has(name))stores.set(name,new Map());const rows=stores.get(name);return {put:async(key,value)=>rows.set(absolute(key),value.clone()),match:async(key,options)=>{const target=absolute(key);const row=[...rows].find(([url])=>options?.ignoreSearch?url.split('?')[0]===target.split('?')[0]:url===target);return row?.[1].clone();}};}};}
async function fixture(){
 const html=new TextEncoder().encode('<!doctype html><title>Synthetic offline test</title>');
 const script=new TextEncoder().encode('/* public synthetic fixture */');
 const files=await Promise.all([['index.html',html],['app.js',script]].map(async([path,raw])=>({path,size:raw.length,sha256:await hash(raw),optional:false})));
 const manifest=new TextEncoder().encode(JSON.stringify({files}));
 const source=(await readFile(new URL('../src/sw.js',import.meta.url),'utf8')).replace('__ASSET_MANIFEST_SHA__',await hash(manifest)).replace('__BUILD_ID__','synthetic-build');
 const caches=storage();let online=true,calls=0;
 const fetcher=async key=>{calls++;if(!online)throw Error('Synthetic network disconnected');const url=absolute(key);if(url.endsWith('/assets.json'))return new Response(manifest);if(url.endsWith('/index.html'))return redirected(new Response(html,{headers:{'Content-Type':'text/html'}}));if(url.endsWith('/app.js'))return new Response(script);throw Error('Unexpected test URL '+url);};
 const start=()=>{const events={};vm.runInNewContext(source,{URL,Response,Blob,TextDecoder,crypto:webcrypto,caches,fetch:fetcher,self:{location:{href:origin+'sw.js?build=test',origin:new URL(origin).origin},clients:{matchAll:async()=>[],claim:async()=>{}},addEventListener:(name,handler)=>events[name]=handler}});return events;};
 return {start,caches,disconnect:()=>online=false,calls:()=>calls};
}
async function install(events){let complete;events.install({waitUntil:promise=>complete=promise});await complete;}
async function navigate(events,path='/'){let result;events.fetch({request:{method:'GET',url:new URL(path,origin).href,mode:'navigate',redirect:'manual'},respondWith:promise=>result=promise});return result;}
test('Pages redirected HTML is normalized before serving a manual-mode navigation',async()=>{
 const f=await fixture(),events=f.start();await install(events);const response=await navigate(events);
 assert.equal(response.status,200);assert.equal(response.redirected,false);assert.match(await response.text(),/Synthetic offline test/);
});
test('a restarted service worker serves cached root and assets with no network',async()=>{
 const f=await fixture();await install(f.start());f.disconnect();const calls=f.calls();const restarted=f.start();
 const response=await navigate(restarted,'/?offline-test=1');assert.equal(response.redirected,false);assert.match(await response.text(),/Synthetic offline test/);
 const asset=await navigate(restarted,'/app.js');assert.match(await asset.text(),/public synthetic fixture/);assert.equal(f.calls(),calls);
});
