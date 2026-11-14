const hex=bytes=>[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
const CACHE='asthral-static-__BUILD_ID__';
let manifest;
self.addEventListener('install',event=>{
  event.waitUntil((async()=>{
    const response=await fetch('./assets.json',{cache:'no-store'});
    const bytes=await response.clone().arrayBuffer();
    manifest=JSON.parse(new TextDecoder().decode(bytes));
    const cache=await caches.open(CACHE);
    try {
      for(const file of manifest.files.filter(row=>!row.optional)) {
        const asset=await fetch('./'+file.path,{cache:'no-store'});
        if(!asset.ok) throw Error('Offline asset unavailable '+file.path);
        const raw=await asset.clone().arrayBuffer();
        if(hex(await crypto.subtle.digest('SHA-256',raw))!==file.sha256) throw Error('Offline asset integrity failed '+file.path);
        await cache.put('./'+file.path,asset);
      }
      await cache.put('./assets.json',response);
      await cache.put('./',await cache.match('./index.html'));
    } catch(error) {
      await caches.delete(CACHE);
      throw error;
    }
  })());
});
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('message',event=>{
  if(event.data?.action==='ACTIVATE_UPDATE') self.skipWaiting();
});
self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=='GET'||url.origin!==self.location.origin) return;
  event.respondWith((async()=>{
    if(url.pathname.endsWith('/voice-model.tar.gz')) {
      const core=await caches.open(CACHE);
      const manifestResponse=await core.match('./voice-model.json');
      if(!manifestResponse)return new Response('Install offline resources first.',{status:503});
      const model=await manifestResponse.json();
      const optional=await caches.open('asthral-optional-resources-v1');
      const parts=[];
      for(const part of model.parts) {
        const response=await optional.match('./'+part.path);
        if(!response)return new Response('Speech model chunks missing.',{status:503});
        parts.push(await response.arrayBuffer());
      }
      return new Response(new Blob(parts),{headers:{'Content-Type':'application/gzip','Content-Length':String(model.bytes)}});
    }
    // Only public, manifest-listed static assets enter this cache.
    for(const name of [CACHE,'asthral-optional-resources-v1']) {
      const cache=await caches.open(name);
      const cached=await cache.match(event.request,{ignoreSearch:true});
      if(cached) return cached;
    }
    return fetch(event.request);
  })());
});
