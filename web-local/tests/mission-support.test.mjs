import test from 'node:test';
import assert from 'node:assert/strict';
import {fetchDonki,DONKI_API,DONKI_HISTORICAL_FIXTURE,cacheDonki,readDonkiCache,cachedDonkiSnapshot} from '../src/space-weather.js';

const ok=data=>new Response(JSON.stringify(data),{status:200,headers:{'content-type':'application/json'}});
const empty=()=>({getItem(){return this.value??null;},setItem(_key,value){this.value=value;}});

test('DONKI queries only the official public API with fixed dates and no profile context',async()=>{
 const calls=[];
 const result=await fetchDonki({startDate:'2026-11-08',endDate:'2026-11-15',now:()=>Date.parse('2026-11-15T12:00:00Z'),fetcher:async(url,options)=>{calls.push({url,options});return ok(url.includes('/FLR?')?[{flrID:'2026-11-08T07:33:00-FLR-001',beginTime:'2026-11-08T07:33Z',classType:'M1.7',sourceLocation:'S07W03',link:'https://ccmc.gsfc.nasa.gov/DONKI/view/FLR/1/1'}]:[]);}});
 assert.equal(calls.length,7);assert.equal(new Set(calls.map(c=>new URL(c.url).origin)).size,1);assert.equal(new URL(calls[0].url).origin,'https://ccmc.gsfc.nasa.gov');
 for(const call of calls){assert.equal(call.options.credentials,'omit');assert.equal(call.options.method,'GET');assert.equal(new URL(call.url).searchParams.has('subject_id'),false);assert.equal(new URL(call.url).searchParams.has('api_key'),false);}
 assert.equal(result.events[0].id,'2026-11-08T07:33:00-FLR-001');assert.equal(result.events[0].time,'2026-11-08T07:33:00.000Z');assert.equal(result.events[0].url,'https://ccmc.gsfc.nasa.gov/DONKI/view/FLR/1/1');assert.equal(result.clinical_authority,false);
 assert.equal(DONKI_API,'https://ccmc.gsfc.nasa.gov/DONKI-API/get/');
});

test('DONKI permits empty arrays, reports partial outages, and fails only if all endpoints fail',async()=>{
 const result=await fetchDonki({startDate:'2026-11-08',endDate:'2026-11-15',now:()=>Date.parse('2026-11-15T12:00:00Z'),fetcher:async url=>url.includes('/CME?')?new Response('offline',{status:503}):ok([])});
 assert.equal(result.events.length,0);assert.equal(result.issues.length,1);assert.equal(result.issues[0].endpoint,'CME');
 await assert.rejects(fetchDonki({startDate:'2026-11-08',endDate:'2026-11-15',now:()=>Date.parse('2026-11-15T12:00:00Z'),fetcher:async()=>new Response('offline',{status:503})}),/All NASA CCMC DONKI endpoints are unavailable/);
});

test('DONKI rejects malformed windows and caps query span',async()=>{
 const options={now:()=>Date.parse('2026-11-15T12:00:00Z'),fetcher:async()=>ok([])};
 await assert.rejects(fetchDonki({...options,startDate:'2026-11-01',endDate:'2026-11-15'}),/seven-day/);
 await assert.rejects(fetchDonki({...options,startDate:'2026-11-16',endDate:'2026-11-15'}),/valid UTC dates/);
});

test('DONKI trusts only exact official event links and retains fixed offline historical fixture separately',async()=>{
 const result=await fetchDonki({startDate:'2026-11-08',endDate:'2026-11-15',now:()=>Date.parse('2026-11-15T12:00:00Z'),fetcher:async url=>ok(url.includes('notifications')?[{messageType:'RBE',messageID:'20261108-AL-001',messageIssueTime:'2026-11-08T21:18Z',messageURL:'https://attacker.invalid/'}]:[])});
 assert.equal(result.events[0].url,null);assert.equal(DONKI_HISTORICAL_FIXTURE.type,'FLR');assert.equal(DONKI_HISTORICAL_FIXTURE.source,'NASA_CCMC_DONKI_FIXED_HISTORICAL_FIXTURE');
});

test('only bounded public DONKI metadata is stored in local public cache',()=>{
 const storage=empty(),sample={provider:'NASA_CCMC_DONKI',fetched_at:'2026-11-15T12:00:00.000Z',events:[],issues:[],contains_personal_data:false};
 assert.equal(cacheDonki(sample,storage),true);assert.deepEqual(readDonkiCache(storage),sample);
 assert.equal(cacheDonki({...sample,contains_personal_data:true},storage),false);
});

test('cached NASA events are explicitly available offline and stale data never implies current conditions',()=>{
 const storage=empty(),sample={provider:'NASA_CCMC_DONKI',fetched_at:'2026-11-15T11:00:00.000Z',events:[{id:'historical'}],issues:[],contains_personal_data:false};
 assert.deepEqual(cachedDonkiSnapshot(Date.parse('2026-11-15T12:00:00Z'),storage),{state:'NO_CACHE',events:[],fetched_at:null});
 cacheDonki(sample,storage);
 assert.equal(cachedDonkiSnapshot(Date.parse('2026-11-15T12:00:00Z'),storage).state,'CACHED');
 const stale=cachedDonkiSnapshot(Date.parse('2026-11-16T12:01:00Z'),storage);
 assert.equal(stale.state,'STALE');assert.deepEqual(stale.events,sample.events);
});
