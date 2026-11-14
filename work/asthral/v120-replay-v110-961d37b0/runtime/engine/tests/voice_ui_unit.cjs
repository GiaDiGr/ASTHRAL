// Unit tests of microphone lifecycle using simulated browser devices.
// These are NOT recognition/synthesis accuracy measurements.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../vigile/web/voice-controller.js'),'utf8');
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
function harness(){
 const elements={},tracks=[],contexts=[],timers=[],nodes=[];let nextMedia=null,nextModule=null;
 function el(id){return elements[id]??=( {value:id==='assistant-target'?'monitoring':id==='voice-language'?'en':id==='voice-rate'?'0':'',disabled:false,textContent:'',events:{},setAttribute(k,v){this[k]=v;},addEventListener(k,v){(this.events[k]??=[]).push(v);},trigger(k){for(const f of this.events[k]||[])f();}});}
 function stream(){const t={stopped:false,events:{},stop(){this.stopped=true;},addEventListener(k,f){this.events[k]=f;}};tracks.push(t);return {getTracks:()=>[t],track:t};}
 class AC{constructor(){this.sampleRate=16000;this.closed=false;this.audioWorklet={addModule:()=>{const d=nextModule;nextModule=null;return d?d.promise:Promise.resolve();}};contexts.push(this);}createMediaStreamSource(){return {connect(){},disconnect(){}};}createGain(){return {gain:{},connect(){}};}close(){this.closed=true;return Promise.resolve();}resume(){return Promise.resolve();}}
 class AW{constructor(){this.port={};nodes.push(this);}connect(){}disconnect(){}}
 class Audio{constructor(){this.playing=false;}play(){this.playing=true;return Promise.resolve();}pause(){this.playing=false;}}
 const ctx={document:{getElementById:el,hidden:false,addEventListener(){}},window:{AudioWorkletNode:AW,addEventListener(){}},navigator:{mediaDevices:{getUserMedia:()=>{const d=nextMedia;nextMedia=null;return d?d.promise:Promise.resolve(stream());}}},AudioContext:AC,AudioWorkletNode:AW,Audio,AbortController,URL:{createObjectURL:()=> 'blob:local',revokeObjectURL(){}},Float32Array,Uint8Array,ArrayBuffer,DataView,JSON,Number,Math,Error,performance:{now:()=>Date.now()},setTimeout:f=>{timers.push(f);return timers.length;},clearTimeout(){},btoa:s=>Buffer.from(s,'binary').toString('base64'),api:async()=>({}),currentCycle:()=>({id:'cycle-A'}),selected:{id:'evaluation-A'},ask(){ctx.window.VigileVoice.beforeQuestion();},fetch:async()=>({ok:true,headers:{get:()=>'.01'},blob:async()=>({}),json:async()=>({text:'safe reviewed text',capture_seconds:1,transcription_seconds:.1})})};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 return {ctx,el,tracks,contexts,timers,nodes,stream,media(d){nextMedia=d;},module(d){nextModule=d;}};
}
async function flush(){await Promise.resolve();await Promise.resolve();await new Promise(r=>setImmediate(r));}
(async()=>{
 {const h=harness(),d=deferred(),s=h.stream();h.media(d);const pending=h.el('voice-record').onclick();h.el('subject').trigger('change');d.resolve(s);await pending;assert.equal(s.track.stopped,true);}
 {const h=harness(),d=deferred();h.module(d);const old=h.el('voice-record').onclick();await flush();assert.equal(h.contexts.length,1);h.el('subject').trigger('change');await h.el('voice-record').onclick();const newer=h.tracks.at(-1);assert.equal(newer.stopped,false);d.resolve();await old;assert.equal(newer.stopped,false,'old startup must not stop newer microphone');h.ctx.window.VigileVoice.reset();}
 {const h=harness();await h.el('voice-record').onclick();const oldTimer=h.timers[0];h.el('evaluation').trigger('change');await h.el('voice-record').onclick();oldTimer();await flush();assert.equal(h.tracks.at(-1).stopped,false,'stale finish must not touch new stream');h.ctx.window.VigileVoice.reset();}
 {const h=harness();h.ctx.window.VigileVoice.accept({speech:{response_id:'approved',target_id:'cycle-A',text:'Approved visible text'}});await h.el('voice-record').onclick();await h.el('voice-play').onclick();assert(h.tracks.every(t=>t.stopped),'playback must turn mic off');h.ctx.window.VigileVoice.reset();}
 {const h=harness();await h.el('voice-record').onclick();h.tracks[0].events.ended();assert(h.tracks[0].stopped);assert.match(h.el('voice-state').textContent,/disconnected/);}
 {const h=harness(),d=deferred();h.media(d);const p=h.el('voice-record').onclick();d.reject(Object.assign(new Error(),{name:'NotAllowedError'}));await p;assert.match(h.el('voice-state').textContent,/denied/);assert.equal(h.el('voice-record').disabled,false);}
 {const h=harness();await h.el('voice-record').onclick();h.ctx.window.VigileVoice.beforeQuestion();assert(h.tracks[0].stopped);assert.equal(h.el('voice-play').disabled,true);}
 {const h=harness();await h.el('voice-record').onclick();h.el('voice-cancel').onclick();assert(h.tracks.every(t=>t.stopped));assert.equal(h.el('voice-transcript').value,'');assert.match(h.el('voice-state').textContent,/discarded/);}
 console.log('8 simulated browser lifecycle scenarios passed; no claim of real-device testing.');
})().catch(e=>{console.error(e);process.exitCode=1;});