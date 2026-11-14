const hex=bytes=>[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
const EXPECTED_MANIFEST='b666c87df4f065ea36aeb1349bde8e123d1386f687b4b955d277eca6f6a6e5b8';
const CACHE='asthral-static-b666c87df4f065ea';
// Pages redirects /index.html to /. A redirected cached response cannot satisfy
// a navigation request whose redirect mode is manual; preserve verified bytes/headers.
function cacheable(response){return new Response(response.body,{status:response.status,statusText:response.statusText,headers:response.headers});}
async function progress(value){for(const client of await self.clients.matchAll({type:'window',includeUncontrolled:true}))client.postMessage({type:'OFFLINE_INSTALL_PROGRESS',...value});}
async function manifest(){
 const cache=await caches.open(CACHE);let response;
 try{response=await fetch('./assets.json',{cache:'no-store',credentials:'omit'});if(!response.ok)throw Error('Manifest HTTP '+response.status);}catch(error){response=await cache.match('./assets.json');if(!response)throw error;}
 const bytes=await response.clone().arrayBuffer();
 if(hex(await crypto.subtle.digest('SHA-256',bytes))!==EXPECTED_MANIFEST)throw Error('Application manifest version or integrity mismatch. Reload the current release while online.');
 return {data:JSON.parse(new TextDecoder().decode(bytes)),response};
}
let installing=null;
async function ensureOffline(){
 if(installing)return installing;
 installing=(async()=>{
  const {data,response}=await manifest(),files=data.files.filter(file=>!file.optional),cache=await caches.open(CACHE);
  const stores=[CACHE,...(await caches.keys()).filter(name=>name.startsWith('asthral-static-')&&name!==CACHE)];let complete=0,bytes=0;
  await progress({stage:'VERIFYING',complete,total:files.length,bytes,total_bytes:files.reduce((n,f)=>n+f.size,0)});
  for(const file of files){
   const url=new URL('./'+file.path,self.location.href);if(url.origin!==self.location.origin||file.path.includes('..'))throw Error('Static resource path rejected.');
   let asset;
   for(const name of stores){const previous=await(await caches.open(name)).match(url);if(previous&&hex(await crypto.subtle.digest('SHA-256',await previous.clone().arrayBuffer()))===file.sha256){asset=previous;break;}}
   if(!asset){asset=await fetch(url,{cache:'no-store',credentials:'omit'});if(!asset.ok)throw Error('Offline resource HTTP '+asset.status+': '+file.path);const raw=await asset.clone().arrayBuffer();if(raw.byteLength!==file.size||hex(await crypto.subtle.digest('SHA-256',raw))!==file.sha256)throw Error('Offline resource integrity failure: '+file.path);}
   await cache.put(url,cacheable(asset));complete++;bytes+=file.size;await progress({stage:'INSTALLING',complete,total:files.length,bytes,total_bytes:files.reduce((n,f)=>n+f.size,0)});
  }
  await cache.put('./assets.json',response);await cache.put('./',await cache.match('./index.html'));
  await progress({stage:'VERIFIED_READY',complete,total:files.length,bytes,total_bytes:bytes});return {files:complete,bytes,manifest_sha256:EXPECTED_MANIFEST};
 })();
 try{return await installing;}finally{installing=null;}
}
self.addEventListener('install',event=>event.waitUntil(ensureOffline()));
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('message',event=>{
 if(event.data?.action==='ACTIVATE_UPDATE')self.skipWaiting();
 if(event.data?.action==='ENSURE_OFFLINE')event.waitUntil(ensureOffline().then(result=>event.ports[0]?.postMessage({ok:true,result})).catch(error=>event.ports[0]?.postMessage({ok:false,error:String(error.message??error)})));
});
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin)return;
 event.respondWith((async()=>{
  if(url.pathname.endsWith('/voice-model.tar.gz')){
   const core=await caches.open(CACHE),modelResponse=await core.match('./voice-model.json');if(!modelResponse)return new Response('Install offline resources first.',{status:503});
   const model=await modelResponse.json(),optional=await caches.open('asthral-optional-resources-v1'),parts=[];
   for(const part of model.parts){const response=await optional.match('./'+part.path);if(!response)return new Response('Speech model chunks missing.',{status:503});const raw=await response.arrayBuffer();if(hex(await crypto.subtle.digest('SHA-256',raw))!==part.sha256)return new Response('Speech model integrity failed.',{status:503});parts.push(raw);}
   return new Response(new Blob(parts),{headers:{'Content-Type':'application/gzip','Content-Length':String(model.bytes)}});
  }
  for(const name of [CACHE,'asthral-optional-resources-v1']){const cached=await(await caches.open(name)).match(event.request,{ignoreSearch:true});if(cached)return event.request.mode==='navigate'&&cached.redirected?cacheable(cached):cached;}
  return fetch(event.request);
 })());
});
