const HOST='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
let lastRequest=-Infinity;
async function boundedJson(response){
 if(!response.ok)throw Error('Public provider HTTP '+response.status);
 const reader=response.body.getReader();let length=0,parts=[];
 try{for(;;){const {value,done}=await reader.read();if(done)break;length+=value.byteLength;if(length>131072)throw Error('Public metadata exceeds safety limit.');parts.push(value);}}
 finally{await reader.cancel();}
 const bytes=new Uint8Array(length);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 return JSON.parse(new TextDecoder().decode(bytes));
}
export async function retrievePublicTopic(topic,{topics,enabled,mode,fetcher=fetch,signal,now=()=>Date.now()}={}){
 if(!Object.hasOwn(topics,topic))throw Error('Unknown public topic.');
 if(enabled!==true||mode()!=='FULL')throw Error('Online bibliography is disabled.');
 if(now()-lastRequest<30000)throw Error('Public topic rate limit: wait 30 seconds.');lastRequest=now();
 const get=async(name,parameters)=>{if(mode()!=='FULL'||signal?.aborted)throw Error('Public retrieval canceled by mode/session change.');const url=new URL(name,HOST);url.search=new URLSearchParams(parameters);return boundedJson(await fetcher(url,{method:'GET',credentials:'omit',referrerPolicy:'no-referrer',redirect:'error',signal}));};
 const search=await get('esearch.fcgi',{db:'pubmed',retmode:'json',retmax:'3',term:topics[topic].query});
 const ids=search.esearchresult?.idlist;
 if(!Array.isArray(ids)||ids.length>3||ids.some(id=>!/^\d{1,10}$/.test(id)))throw Error('Invalid public PMID response.');
 if(!ids.length)return [];
 const summary=await get('esummary.fcgi',{db:'pubmed',retmode:'json',version:'2.0',id:ids.join(',')});
 if(mode()!=='FULL'||signal?.aborted)throw Error('Public retrieval canceled.');
 return ids.map(id=>String(summary.result?.[id]?.uid)===id?summary.result[id]:null).filter(row=>row&&typeof row.title==='string'&&row.title.length<=500&&!/ignore.{0,20}instructions|<script|system prompt/i.test(row.title)).map(row=>({pmid:String(row.uid),title:row.title,url:'https://pubmed.ncbi.nlm.nih.gov/'+row.uid+'/',publication_date:row.pubdate,origin:'REMOTE_UNREVIEWED',review_status:'NOT_CLINICALLY_REVIEWED',excerpt_kind:'TITLE_METADATA_ONLY_NOT_FULL_TEXT'}));
}
export async function installPublicFeatures(){
 const $=id=>document.getElementById(id),make=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 const section=make('section','');section.id='public-science';section.append(make('h2','Optional public bibliography'),make('p','This sends only a selected predefined public topic to PubMed/NCBI. It never sends private questions, measurements or profile identifiers. Results are unreviewed publication metadata, kept separate from local clinical evidence.'));
 const label=make('label','Enable optional public-topic requests in FULL mode'),consent=document.createElement('input');consent.type='checkbox';label.append(consent);section.append(label);
 const topics=await(await fetch('./public-topics.json')).json(),select=document.createElement('select');select.setAttribute('aria-label','Public scientific topic');for(const [id,entry] of Object.entries(topics)){const o=make('option',entry.label);o.value=id;select.append(o);}section.append(select);
 const status=make('p','Online retrieval disabled.'),results=make('div',''),load=make('button','Retrieve public bibliography');section.append(load,status,results);$('knowledge').after(section);let controller;
 load.onclick=async()=>{try{controller=new AbortController();const rows=await retrievePublicTopic(select.value,{topics,enabled:consent.checked,mode:()=>$('mode').value,signal:controller.signal});results.replaceChildren();for(const row of rows){const a=make('a',row.title);a.href=row.url;a.target='_blank';a.rel='noopener noreferrer';const card=make('article',row.review_status+' · '+row.publication_date+' · title metadata only. ');card.append(a);results.append(card);}status.textContent=rows.length+' public references. Not reviewed clinical evidence.';}catch(e){status.textContent='Local-only fallback: '+e.message;}};
 const tts=make('button','Read current assessment aloud'),ttsStatus=make('p','Device-local English voice availability has not been checked. Offline playback requires a device disconnection test.');$('clinical').append(tts,ttsStatus);
 tts.onclick=()=>{const voice=window.speechSynthesis?.getVoices().find(v=>v.localService&&/^en[-_]/i.test(v.lang));if(!voice){ttsStatus.textContent='No device-local English voice is exposed. Text remains available; network voices are not used.';return;}const text=$('assessment').innerText;if(!text){ttsStatus.textContent='Complete an assessment first.';return;}speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.lang=voice.lang;utterance.voice=voice;utterance.onend=()=>ttsStatus.textContent='Playback ended using '+voice.name+' (reported local by browser; offline acceptance pending).';utterance.onerror=()=>ttsStatus.textContent='Playback unavailable; read the assessment text.';speechSynthesis.speak(utterance);};
 const cleanup=()=>{controller?.abort();results.replaceChildren();consent.checked=false;window.speechSynthesis?.cancel();};
 $('mode').addEventListener('change',()=>{if($('mode').value!=='FULL')cleanup();});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)window.speechSynthesis?.cancel();});
 return cleanup;
}
