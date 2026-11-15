import test from 'node:test';
import assert from 'node:assert/strict';
import {DONKI_EVENT_TYPES,loadNoticePreferences,saveNoticePreferences,readNoticeAcks,acknowledgeNotice,noticeState} from '../src/space-weather-alerts.js';

function storage(){const values=new Map();return {getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)};}
const events=[{type:'FLR',id:'flare-1',time:'2026-11-15T10:00:00Z',description:'Solar flare'}, {type:'FLR',id:'flare-1',time:'2026-11-15T10:01:00Z',description:'Updated solar flare'}, {type:'RBE',id:'rbe-1',time:'2026-11-15T10:02:00Z'}];

test('event preferences are bounded, persisted locally, and default to selected public event categories',()=>{
 const s=storage();assert.deepEqual(loadNoticePreferences(s),['FLR','CME','SEP','RBE']);assert.equal(saveNoticePreferences(['CME','FLR','CME'],s),true);assert.deepEqual(loadNoticePreferences(s),['CME','FLR']);assert.throws(()=>saveNoticePreferences(['LOCAL_WARNING'],s),/Unsupported/);assert.ok(DONKI_EVENT_TYPES.includes('NOTIFICATION'));
});

test('in-app notices deduplicate event updates, respect configured types, and acknowledge without health inference',()=>{
 const s=storage(),notice=noticeState(events,['FLR']);assert.equal(notice.length,1);assert.equal(notice[0].event.description,'Updated solar flare');assert.equal(notice[0].state,'UNACKNOWLEDGED');assert.match(notice[0].scope,/NOT_PERSONAL_RADIATION/);
 const ack=acknowledgeNotice(notice[0].event,s,'2026-11-15T10:05:00Z');assert.equal(ack.stored,true);assert.equal(readNoticeAcks(s).length,1);assert.equal(noticeState(events,['FLR'],readNoticeAcks(s))[0].state,'ACKNOWLEDGED');assert.equal(noticeState(events,['RBE'],readNoticeAcks(s))[0].state,'UNACKNOWLEDGED');
});

test('invalid event notices are rejected and malformed local state degrades safely',()=>{
 const s=storage();assert.throws(()=>acknowledgeNotice({type:'URGENT',id:'x'},s),/invalid DONKI/);s.setItem('asthral.donki.notice-types.v1','not json');assert.deepEqual(loadNoticePreferences(s),[]);s.setItem('asthral.donki.notice-ack.v1','bad');assert.deepEqual(readNoticeAcks(s),[]);
});

test('changed public metadata needs a new acknowledgement and preserves older revision history',()=>{
 const s=storage(),event={type:'CME',id:'cme-1',time:'2026-11-15T10:00:00Z',description:'Coronal mass ejection',parameters:['reported speed 500 km/s']};acknowledgeNotice(event,s,'2026-11-15T10:01:00Z');
 const updated={...event,parameters:['reported speed 600 km/s']};const notice=noticeState([updated],['CME'],readNoticeAcks(s))[0];assert.equal(notice.state,'UPDATED_SINCE_ACK');assert.equal(notice.revision_state,'CHANGED');
 acknowledgeNotice(updated,s,'2026-11-15T10:02:00Z');assert.equal(readNoticeAcks(s).length,2);assert.equal(noticeState([updated],['CME'],readNoticeAcks(s))[0].state,'ACKNOWLEDGED');
});
test('legacy acknowledgements remain in history and do not attest an unknown current revision',()=>{
 const s=storage();s.setItem('asthral.donki.notice-ack.v1',JSON.stringify([{key:'FLR:flare-1',type:'FLR',id:'flare-1',acknowledged_at:'2026-11-15T10:05:00Z'}]));const notice=noticeState([events[1]],['FLR'],readNoticeAcks(s))[0];assert.equal(notice.state,'UPDATED_SINCE_ACK');assert.equal(notice.revision_state,'LEGACY_UNKNOWN');assert.equal(readNoticeAcks(s).length,1);
});

test('failed acknowledgement persistence never creates a stored current acknowledgement',()=>{
 const s={getItem:()=>null,setItem:()=>{throw Error('quota');}};const result=acknowledgeNotice(events[1],s);assert.equal(result.stored,false);assert.equal(noticeState([events[1]],['FLR'],readNoticeAcks(s))[0].state,'UNACKNOWLEDGED');
});
