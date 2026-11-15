import test from 'node:test';
import assert from 'node:assert/strict';
import {auditedFetch,PRIVATE_SENTINEL} from '../src/network-audit.js';
test('network observer blocks synthetic private data and writes before transport',async()=>{
 const observed=[];let calls=0;const request=auditedFetch(async()=>{calls++;return new Response('public');},event=>observed.push(event));
 await request('https://example.test/approved-model');
 await assert.rejects(request('https://example.test/?question='+PRIVATE_SENTINEL),/blocked/);
 await assert.rejects(request('https://example.test/',{method:'POST',body:PRIVATE_SENTINEL}),/blocked/);
 assert.equal(calls,1);assert.equal(observed.filter(x=>x.blocked).length,2);
 assert.ok(!JSON.stringify(observed).includes(PRIVATE_SENTINEL));
});
