import test from 'node:test';
import assert from 'node:assert/strict';
import {retrievePublicTopic} from '../src/public-science.js';
const topics={cardiovascular:{query:'spaceflight cardiovascular deconditioning'}};
test('public bibliography sends only predefined topics and bounded numeric PMIDs',async()=>{
 const requests=[];
 const sentinel='ASTHRAL_PRIVATE_SYNTHETIC_SENTINEL';
 const fetcher=async(url,options)=>{requests.push({url:String(url),options});return Response.json(String(url).includes('esearch')?{esearchresult:{idlist:['123']}}:{result:{'123':{uid:'123',title:'Public spaceflight research',pubdate:'2024'}}});};
 const result=await retrievePublicTopic('cardiovascular',{topics,enabled:true,mode:()=>'FULL',fetcher,now:()=>100000});
 assert.equal(result[0].review_status,'NOT_CLINICALLY_REVIEWED');assert.equal(requests.length,2);
 assert.ok(!JSON.stringify(requests).includes(sentinel));
 assert.ok(requests.every(r=>new URL(r.url).hostname==='eutils.ncbi.nlm.nih.gov'&&r.options.credentials==='omit'&&r.options.redirect==='error'&&!r.options.body));
 const count=requests.length;
 await assert.rejects(retrievePublicTopic(sentinel,{topics,enabled:true,mode:()=>'FULL',fetcher,now:()=>200000}),/Unknown/);
 await assert.rejects(retrievePublicTopic('cardiovascular',{topics,enabled:true,mode:()=>'CRITICAL',fetcher,now:()=>200000}),/disabled/);
 await assert.rejects(retrievePublicTopic('cardiovascular',{topics,enabled:false,mode:()=>'FULL',fetcher,now:()=>200000}),/disabled/);
 assert.equal(requests.length,count);
});
test('mode change between metadata requests prevents the second request',async()=>{
 let mode='FULL',calls=0;
 const fetcher=async()=>{calls++;mode='LOW_POWER';return Response.json({esearchresult:{idlist:['123']}});};
 await assert.rejects(retrievePublicTopic('cardiovascular',{topics,enabled:true,mode:()=>mode,fetcher,now:()=>300000}),/canceled/);
 assert.equal(calls,1);
});
