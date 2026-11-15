const PREF_KEY='asthral.donki.notice-types.v1';
const ACK_KEY='asthral.donki.notice-ack.v1';
export const DONKI_EVENT_TYPES=Object.freeze(['FLR','CME','SEP','GST','IPS','RBE','NOTIFICATION']);

export function loadNoticePreferences(storage=globalThis.localStorage){
 try{const raw=storage?.getItem(PREF_KEY);if(raw===null||raw===undefined)return ['FLR','CME','SEP','RBE'];const parsed=JSON.parse(raw);if(!Array.isArray(parsed)||parsed.length>DONKI_EVENT_TYPES.length)return [];return [...new Set(parsed.filter(x=>DONKI_EVENT_TYPES.includes(x)))];}catch{return [];}
}
export function saveNoticePreferences(types,storage=globalThis.localStorage){
 if(!Array.isArray(types)||types.some(x=>!DONKI_EVENT_TYPES.includes(x)))throw Error('Unsupported DONKI event type preference.');
 try{storage?.setItem(PREF_KEY,JSON.stringify([...new Set(types)]));return true;}catch{return false;}
}
export function readNoticeAcks(storage=globalThis.localStorage){
 try{const rows=JSON.parse(storage?.getItem(ACK_KEY)||'[]');return Array.isArray(rows)?rows.filter(x=>x&&typeof x.key==='string'&&typeof x.acknowledged_at==='string').slice(-500):[];}catch{return [];}
}
export function noticeRevision(event){return JSON.stringify([event.type,event.id,event.time,String(event.description??'').slice(0,2000),Array.isArray(event.parameters)?event.parameters.slice(0,20).map(x=>String(x).slice(0,200)):[],String(event.url??'').slice(0,1000),String(event.catalog??'').slice(0,80)]);}
export function acknowledgeNotice(event,storage=globalThis.localStorage,at=new Date().toISOString()){
 if(!event||!DONKI_EVENT_TYPES.includes(event.type)||typeof event.id!=='string'||!event.id)throw Error('Cannot acknowledge an invalid DONKI event.');
 const key=`${event.type}:${event.id}`,revision=noticeRevision(event),rows=readNoticeAcks(storage).filter(x=>x.key!==key||x.revision!==revision);rows.push({key,type:event.type,id:event.id,revision,acknowledged_at:at});
 try{storage?.setItem(ACK_KEY,JSON.stringify(rows.slice(-500)));return {key,acknowledged_at:at,stored:true};}catch{return {key,acknowledged_at:at,stored:false};}
}
export function noticeState(events,preferences,acks=readNoticeAcks()){
 const selected=new Set(preferences),ackMap=new Map(acks.map(x=>[x.key,x]));const dedup=new Map();
 for(const event of events||[]){if(!event||!selected.has(event.type)||typeof event.id!=='string'||typeof event.time!=='string')continue;const key=`${event.type}:${event.id}`;const old=dedup.get(key);if(!old||event.time>old.time)dedup.set(key,event);}
 return [...dedup.values()].sort((a,b)=>b.time.localeCompare(a.time)).map(event=>{const key=`${event.type}:${event.id}`,acknowledgement=ackMap.get(key)||null,current=acknowledgement?.revision===noticeRevision(event);return {event,key,acknowledgement,state:current?'ACKNOWLEDGED':acknowledgement?'UPDATED_SINCE_ACK':'UNACKNOWLEDGED',revision_state:current?'CURRENT':acknowledgement?.revision?'CHANGED':acknowledgement?'LEGACY_UNKNOWN':'NOT_ACKNOWLEDGED',scope:'PUBLIC_DONKI_EVENT_NOTICE_NOT_PERSONAL_RADIATION_OR_SAFETY_WARNING'};});
}
