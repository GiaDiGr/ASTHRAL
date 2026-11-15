import test from 'node:test';
import assert from 'node:assert/strict';
import {cachePublicResources} from '../src/public-resources.js';
const hash=async text=>Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex');
test('optional runtime updates evict stale public bytes and preserve JavaScript MIME',async()=>{
 let cached=new Response('old'),requests=0;
 const asset={path:'test.mjs',size:3,sha256:await hash('new')};
 const cache={match:async()=>cached?.clone(),delete:async()=>{cached=null;},put:async(key,value)=>{cached=value;}};
 const fetcher=async url=>{requests++;return String(url).endsWith('assets.json')?Response.json({files:[asset]}):new Response('new');};
 await cachePublicResources(['test.mjs'],{fetcher,storage:{open:async()=>cache},base:'https://example.test/'});
 assert.equal(await cached.clone().text(),'new');assert.equal(cached.headers.get('Content-Type'),'text/javascript');assert.equal(requests,2);
 await cachePublicResources(['test.mjs'],{fetcher,storage:{open:async()=>cache},base:'https://example.test/'});assert.equal(requests,3);
});
test('unverified replacement bytes never enter the optional cache',async()=>{
 let admitted=false;
 const asset={path:'test.mjs',size:3,sha256:await hash('new')};
 const fetcher=async url=>String(url).endsWith('assets.json')?Response.json({files:[asset]}):new Response('bad');
 await assert.rejects(cachePublicResources(['test.mjs'],{fetcher,storage:{open:async()=>({match:async()=>null,put:async()=>{admitted=true;}})},base:'https://example.test/'}),/integrity/);
 assert.equal(admitted,false);
});
