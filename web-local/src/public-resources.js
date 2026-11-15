export async function cachePublicResources(prefixes,{fetcher=fetch,storage=caches,base=location.href}={}){
 const manifest=await(await fetcher(new URL('./assets.json',base))).json();
 const cache=await storage.open('asthral-optional-resources-v1');
 const hash=async raw=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(x=>x.toString(16).padStart(2,'0')).join('');
 for(const asset of manifest.files.filter(row=>prefixes.some(prefix=>row.path===prefix||row.path.startsWith(prefix)))){
  const url=new URL('./'+asset.path,base);if(url.origin!==new URL(base).origin)throw Error('External optional asset path blocked.');
  let response=await cache.match(url),bytes=response?await response.arrayBuffer():null;
  if(bytes&&(bytes.byteLength!==asset.size||await hash(bytes)!==asset.sha256)){await cache.delete(url);bytes=null;}
  if(!bytes){response=await fetcher(url);if(!response.ok)throw Error('Optional runtime unavailable.');bytes=await response.arrayBuffer();}
  if(bytes.byteLength!==asset.size||await hash(bytes)!==asset.sha256)throw Error('Optional runtime integrity failed.');
  const mime=/\.m?js$/.test(asset.path)?'text/javascript':asset.path.endsWith('.wasm')?'application/wasm':'application/octet-stream';
  await cache.put(url,new Response(bytes,{headers:{'Content-Type':mime}}));
 }
}
