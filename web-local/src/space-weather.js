export const DONKI_API='https://ccmc.gsfc.nasa.gov/DONKI-API/get/';
const EVENT_ENDPOINTS=['FLR','CME','SEP','GST','IPS','RBE'];
const CACHE_KEY='asthral.public.donki.v1';
const MAX_BYTES=2*1024*1024;
const EVENT_ID={FLR:'flrID',CME:'activityID',SEP:'sepID',GST:'gstID',IPS:'activityID',RBE:'rbeID'};
const EVENT_TIME={FLR:'beginTime',CME:'startTime',SEP:'eventTime',GST:'startTime',IPS:'eventTime',RBE:'eventTime'};
const boundedJson=async response=>{
 if(!response.ok)throw Error('DONKI HTTP '+response.status);
 const reader=response.body?.getReader();if(!reader){const raw=await response.arrayBuffer();if(raw.byteLength>MAX_BYTES)throw Error('DONKI response too large');return JSON.parse(new TextDecoder().decode(raw));}
 let size=0,complete=false;const chunks=[];try{for(;;){const {value,done}=await reader.read();if(done){complete=true;break;}size+=value.byteLength;if(size>MAX_BYTES)throw Error('DONKI response too large');chunks.push(value);}}finally{if(!complete)await reader.cancel().catch(()=>{});reader.releaseLock?.();}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}return JSON.parse(new TextDecoder().decode(bytes));
};
const text=(value,max=320)=>typeof value==='string'?value.replace(/[\u0000-\u001f\u007f]/g,' ').trim().slice(0,max):'';
const utcTime=value=>{if(typeof value!=='string'||value.length>64)return null;const normalized=/Z$|[+-]\d{2}:?\d{2}$/.test(value)?value:value+'Z';const time=Date.parse(normalized);return Number.isFinite(time)?new Date(time).toISOString():null;};
const trustedLink=value=>{try{const url=new URL(value);return url.protocol==='https:'&&url.hostname==='ccmc.gsfc.nasa.gov'&&url.pathname.startsWith('/DONKI/')?url.href:null;}catch{return null;}};
function normalize(type,raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('DONKI item must be an object');
 const id=text(raw[EVENT_ID[type]],128);if(!id)throw Error('DONKI event identifier missing');
 const time=utcTime(raw[EVENT_TIME[type]]||raw.messageIssueTime);if(!time)throw Error('DONKI event timestamp missing or invalid');
 const descriptions={FLR:`Solar flare ${text(raw.classType,40)||'class not supplied'}`,CME:'Coronal mass ejection record',SEP:'Solar energetic particle record',GST:'Geomagnetic storm record',IPS:'Interplanetary shock record',RBE:'Radiation belt enhancement record'};
 const parameters=[];if(type==='FLR'){if(raw.classType)parameters.push('class '+text(raw.classType,40));if(raw.sourceLocation)parameters.push('source '+text(raw.sourceLocation,40));}
 if(type==='CME'){const analysis=Array.isArray(raw.cmeAnalyses)?raw.cmeAnalyses.find(item=>item?.isMostAccurate===true)??raw.cmeAnalyses[0]:null;if(analysis&&Number.isFinite(Number(analysis.speed)))parameters.push('reported speed '+Number(analysis.speed)+' km/s');if(analysis?.type)parameters.push('reported type '+text(analysis.type,60));}
 if(type==='SEP'&&raw.linkedEvents?.length)parameters.push('linked-event identifiers available');if(type==='GST'&&raw.kpIndex?.length)parameters.push('Kp observations available');if(type==='RBE'&&raw.instruments?.length)parameters.push('instrument metadata available');
 const url=trustedLink(raw.link||raw.messageURL);return {type,id,time,description:descriptions[type],parameters,url,catalog:text(raw.catalog,80),source:'NASA_CCMC_DONKI',research_quality:'PROTOTYPING_RESEARCH_CONTEXT'};
}
function normalizeNotification(raw){if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('DONKI notification must be an object');const id=text(raw.messageID,128),time=utcTime(raw.messageIssueTime);if(!id||!time)throw Error('DONKI notification identifier or timestamp missing');const type=text(raw.messageType,40);return {type:'NOTIFICATION',id,time,description:'DONKI notification for '+(type||'unspecified event type'),parameters:type?[`notification type ${type}`]:[],url:trustedLink(raw.messageURL),catalog:'',source:'NASA_CCMC_DONKI',research_quality:'PROTOTYPING_RESEARCH_CONTEXT'};}
const validDate=value=>typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&Number.isFinite(Date.parse(value+'T00:00:00Z'))&&new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;
export async function fetchDonki({startDate,endDate,fetcher=fetch,signal,now=()=>Date.now()}={}){
 if(!validDate(startDate)||!validDate(endDate)||startDate>endDate)throw Error('DONKI dates must be valid UTC dates in order.');
 const days=(Date.parse(endDate+'T00:00:00Z')-Date.parse(startDate+'T00:00:00Z'))/86400000;if(days>7||Date.parse(endDate+'T23:59:59Z')>now()+86400000)throw Error('DONKI query is limited to a recent seven-day interval.');
 const request=async endpoint=>{const url=new URL(endpoint,DONKI_API);url.searchParams.set('startDate',startDate);url.searchParams.set('endDate',endDate);if(endpoint==='notifications')url.searchParams.set('type','all');const response=await fetcher(url.href,{method:'GET',credentials:'omit',referrerPolicy:'no-referrer',redirect:'error',signal,headers:{Accept:'application/json'}});const data=await boundedJson(response);if(data!==null&&!Array.isArray(data))throw Error('DONKI response is not an event list');return data??[];};
 const settled=await Promise.allSettled([...EVENT_ENDPOINTS.map(type=>request(type).then(items=>({type,items}))),request('notifications').then(items=>({type:'NOTIFICATION',items}))]);const events=[],issues=[];
 for(let index=0;index<settled.length;index++){const result=settled[index],type=index<EVENT_ENDPOINTS.length?EVENT_ENDPOINTS[index]:'NOTIFICATION';if(result.status==='rejected'){issues.push({endpoint:type,error:text(result.reason?.message||'Unavailable',180)});continue;}for(const raw of result.value.items.slice(0,200)){try{events.push(type==='NOTIFICATION'?normalizeNotification(raw):normalize(type,raw));}catch(error){issues.push({endpoint:type,error:text(error.message,180)});}}}
 if(!settled.some(result=>result.status==='fulfilled'))throw Error('All NASA CCMC DONKI endpoints are unavailable.');
 events.sort((a,b)=>b.time.localeCompare(a.time));return {provider:'NASA_CCMC_DONKI',base_url:DONKI_API,start_date:startDate,end_date:endDate,fetched_at:new Date(now()).toISOString(),events:events.slice(0,500),issues,contains_personal_data:false,clinical_authority:false};
}
export function cacheDonki(result,storage=globalThis.localStorage){try{if(!result||result.provider!=='NASA_CCMC_DONKI'||result.contains_personal_data!==false)return false;const serialized=JSON.stringify(result);if(serialized.length>2_000_000)return false;storage?.setItem(CACHE_KEY,serialized);return true;}catch{return false;}}
export function readDonkiCache(storage=globalThis.localStorage){try{const raw=storage?.getItem(CACHE_KEY);if(!raw||raw.length>2_000_000)return null;const result=JSON.parse(raw);if(result?.provider!=='NASA_CCMC_DONKI'||result.contains_personal_data!==false||!Array.isArray(result.events)||!Number.isFinite(Date.parse(result.fetched_at)))return null;return result;}catch{return null;}}
export function cachedDonkiSnapshot(now=Date.now(),storage=globalThis.localStorage){const result=readDonkiCache(storage);if(!result)return {state:'NO_CACHE',events:[],fetched_at:null};const age=now-Date.parse(result.fetched_at);return {state:age<0||age>86400000?'STALE':'CACHED',events:result.events,fetched_at:result.fetched_at,age_ms:Math.max(0,age)};}
export const DONKI_HISTORICAL_FIXTURE={type:'FLR',id:'2026-11-05T18:21:00-FLR-001',time:'2026-11-05T18:21:00.000Z',description:'Solar flare M3.5',parameters:['class M3.5','source S08E35'],url:'https://ccmc.gsfc.nasa.gov/DONKI/view/FLR/49391/-1',catalog:'M2M_CATALOG',source:'NASA_CCMC_DONKI_FIXED_HISTORICAL_FIXTURE',research_quality:'PROTOTYPING_RESEARCH_CONTEXT'};
