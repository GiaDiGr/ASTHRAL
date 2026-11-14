'use strict';
// Voice is a separate untrusted text input. It cannot write clinical data.
(()=>{
 const by=id=>document.getElementById(id);
 const state={epoch:0,stream:null,context:null,node:null,source:null,chunks:[],samples:0,recording:false,pending:false,pipeline:{},sendFromTranscript:false,timer:null,fetch:null,audio:null,url:null,speech:null};
 const status=text=>{by('voice-state').textContent=text;};
 function stopTracks(){state.recording=false;state.pending=false;clearTimeout(state.timer);state.stream?.getTracks().forEach(t=>t.stop());state.source?.disconnect();state.node?.disconnect();state.context?.close().catch(()=>{});state.stream=null;state.source=null;state.node=null;state.context=null;state.recording=false;state.pending=false;by('voice-record').textContent='🎙 Hablar / terminar';by('voice-record').setAttribute('aria-pressed','false');by('voice-record').disabled=false;}
 function stopPlayback(){state.fetch?.abort();state.fetch=null;if(state.audio){state.audio.pause();state.audio.src='';state.audio=null;}if(state.url)URL.revokeObjectURL(state.url);state.url=null;by('voice-stop').disabled=true;}
 function reset(){state.pipeline={};state.sendFromTranscript=false;state.epoch++;stopTracks();stopPlayback();state.chunks=[];state.samples=0;state.speech=null;by('voice-play').disabled=true;by('voice-transcript').value='';by('voice-send').disabled=true;by('voice-approved').textContent='';status('Micrófono apagado. Sin escucha permanente.');}
 function target(){const monitor=by('assistant-target').value==='monitoring';const id=monitor?currentCycle()?.id:selected?.id;if(!id)throw Error('Selecciona un ciclo o una evaluación antes de grabar.');return monitor?{monitoring_id:id}:{evaluation_id:id};}
 function pcmWave(chunks,rate){
  const n=chunks.reduce((v,c)=>v+c.length,0),all=new Float32Array(n);let offset=0;for(const c of chunks){all.set(c,offset);offset+=c.length;}
  const count=Math.min(640000,Math.floor(n*16000/rate)),buffer=new ArrayBuffer(44+count*2),v=new DataView(buffer);
  function ascii(at,s){for(let i=0;i<s.length;i++)v.setUint8(at+i,s.charCodeAt(i));}
  ascii(0,'RIFF');v.setUint32(4,36+count*2,true);ascii(8,'WAVEfmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,16000,true);v.setUint32(28,32000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);ascii(36,'data');v.setUint32(40,count*2,true);
  for(let i=0;i<count;i++){const start=Math.floor(i*rate/16000),end=Math.max(start+1,Math.floor((i+1)*rate/16000));let sum=0;for(let j=start;j<end&&j<all.length;j++)sum+=all[j];const x=Math.max(-1,Math.min(1,sum/(end-start)));v.setInt16(44+i*2,x<0?Math.round(x*32768):Math.round(x*32767),true);}
  const bytes=new Uint8Array(buffer);let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(binary);
 }
 async function finish(epoch,scope,language,rate){
  if(epoch!==state.epoch)return;state.pipeline.recordStop=performance.now();
  const chunks=state.chunks;state.chunks=[];stopTracks();if(epoch!==state.epoch)return;
  status('Micrófono apagado. Transcribiendo localmente…');const abort=new AbortController();state.fetch=abort;
  try{
   const raw=pcmWave(chunks,rate);const start=performance.now();
   const response=await fetch('/api/voice/transcribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...scope,language,audio_base64:raw}),signal:abort.signal,cache:'no-store'});
   if(!response.ok)throw Error('STT no disponible o audio rechazado ('+response.status+'). Puedes continuar por texto.');
   const result=await response.json();if(epoch!==state.epoch)return;
   state.pipeline.transcriptReady=performance.now();state.pipeline.capture_seconds=result.capture_seconds;state.pipeline.transcription_seconds=result.transcription_seconds;by('voice-transcript').value=result.text;by('voice-send').disabled=result.text.trim().length<3;
   by('voice-timing').textContent='Audio: '+result.capture_seconds.toFixed(2)+' s · STT servidor: '+result.transcription_seconds.toFixed(2)+' s · solicitud: '+((performance.now()-start)/1000).toFixed(2)+' s';
   status('Transcripción editable. Revisa números, unidades, negaciones y contexto antes de enviar. No es una medición autoritativa.');
  }catch(e){if(epoch===state.epoch&&e.name!=='AbortError')status(e.message);}finally{if(epoch===state.epoch)state.fetch=null;}
 }
 async function record(){
  if(state.recording){await state.finish?.();return;}if(state.pending)return;
  const epoch=++state.epoch;let scope;
  try{
   scope=target();if(!navigator.mediaDevices?.getUserMedia||!window.AudioWorkletNode)throw Error('Captura PCM local no disponible en este navegador. Continúa por texto.');
   stopPlayback();state.pending=true;by('voice-record').disabled=true;status('Solicitando permiso de micrófono. Sólo se grabará tras tu interacción.');
   const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});
   if(epoch!==state.epoch){stream.getTracks().forEach(t=>t.stop());return;}
   state.stream=stream;const context=new AudioContext({sampleRate:16000});state.context=context;await context.audioWorklet.addModule('/assets/recorder-worklet.js');
   if(epoch!==state.epoch){stream.getTracks().forEach(t=>t.stop());context.close().catch(()=>{});return;}
   const node=new AudioWorkletNode(context,'vigile-pcm'),source=context.createMediaStreamSource(stream),mute=context.createGain();mute.gain.value=0;
   state.node=node;state.source=source;state.chunks=[];state.samples=0;source.connect(node);node.connect(mute);mute.connect(context.destination);await context.resume();
   const language=by('voice-language').value;state.finish=()=>finish(epoch,scope,language,context.sampleRate);
   node.port.onmessage=e=>{if(epoch!==state.epoch||!state.recording)return;state.chunks.push(e.data);state.samples+=e.data.length;if(state.samples>=context.sampleRate*40)state.finish();};
   state.pending=false;state.recording=true;by('voice-record').disabled=false;by('voice-record').textContent='■ Terminar grabación';by('voice-record').setAttribute('aria-pressed','true');status('Grabando · MICRÓFONO ACTIVO · máximo 40 segundos. Pulsa terminar o cancelar.');state.timer=setTimeout(()=>finish(epoch,scope,language,context.sampleRate),40000);for(const track of stream.getTracks())track.addEventListener('ended',()=>{if(epoch===state.epoch&&state.recording){reset();status('Micrófono desconectado. Audio descartado; interfaz textual disponible.');}});
  }catch(e){if(epoch!==state.epoch)return;stopTracks();status(e.name==='NotAllowedError'?'Permiso de micrófono denegado. La interfaz textual sigue disponible.':e.name==='NotFoundError'?'No se encontró micrófono. Continúa por texto.':'No se pudo iniciar el micrófono. Está apagado; continúa por texto.');}
 }
 async function play(){
  const ticket=state.speech;if(!ticket?.response_id)return;state.pipeline.playClick=performance.now();const epoch=++state.epoch;stopTracks();state.chunks=[];stopPlayback();status('Sintetizando el texto validado visible, localmente…');const abort=new AbortController();state.fetch=abort;by('voice-stop').disabled=false;
  try{
   const start=performance.now();const response=await fetch('/api/voice/synthesize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({response_id:ticket.response_id,target_id:ticket.target_id,rate:Number(by('voice-rate').value)}),signal:abort.signal,cache:'no-store'});
   if(!response.ok)throw Error('TTS no disponible, contexto caducado o límite de recursos. El texto sigue visible.');
   const blob=await response.blob();if(epoch!==state.epoch)return;
   state.url=URL.createObjectURL(blob);const audio=new Audio(state.url);state.audio=audio;audio.onended=()=>{if(epoch===state.epoch){stopPlayback();status('Reproducción terminada. Micrófono apagado.');}};
   await audio.play();state.pipeline.playStart=performance.now();state.pipeline.synthesis_seconds=Number(response.headers.get('X-Synthesis-Seconds'));if(epoch!==state.epoch){stopPlayback();return;}
   by('voice-timing').textContent='Síntesis servidor: '+Number(response.headers.get('X-Synthesis-Seconds')).toFixed(2)+' s · solicitud hasta reproducción: '+((performance.now()-start)/1000).toFixed(2)+' s';status('Reproduciendo sólo el texto validado visible. Micrófono apagado.');if(state.pipeline.recordStop){const total=(state.pipeline.playStart-state.pipeline.recordStop)/1000;const review=(state.pipeline.questionSent-state.pipeline.transcriptReady)/1000;const wait=(state.pipeline.playClick-state.pipeline.responseReady)/1000;by('voice-timing').textContent+=' · total desde fin de grabación: '+total.toFixed(2)+' s (incluye revisión humana '+Math.max(0,review).toFixed(2)+' s y espera para reproducir '+Math.max(0,wait).toFixed(2)+' s).';}by('voice-pipeline').textContent=JSON.stringify(state.pipeline,null,2);
  }catch(e){if(epoch===state.epoch&&e.name!=='AbortError'){stopPlayback();status(e.message);}}
 }
 window.VigileVoice={reset,beforeQuestion(){if(!state.sendFromTranscript)state.pipeline={};state.sendFromTranscript=false;state.pipeline.questionSent=performance.now();state.epoch++;stopTracks();stopPlayback();state.chunks=[];state.speech=null;by('voice-play').disabled=true;status('Consulta por texto; micrófono apagado.');},accept(answer){state.pipeline.responseReady=performance.now();state.pipeline.server_timings=answer.timings;state.pipeline.model_metrics=answer.metrics;state.pipeline.inference_attempted=answer.inference_attempted;stopTracks();stopPlayback();state.speech=answer.speech?.response_id?answer.speech:null;by('voice-approved').textContent=state.speech?.text||'Sin texto aprobado para síntesis; usa la respuesta textual.';by('voice-play').disabled=!state.speech;}};
 by('voice-record').onclick=record;by('voice-cancel').onclick=()=>{reset();status('Cancelado. Micrófono apagado y audio descartado.');};by('voice-play').onclick=play;by('voice-stop').onclick=()=>{stopPlayback();status('Reproducción detenida. Micrófono apagado.');};
 by('voice-transcript').oninput=()=>{by('voice-send').disabled=by('voice-transcript').value.trim().length<3;};
 by('voice-send').onclick=()=>{const text=by('voice-transcript').value.trim();if(text.length<3)return;by('question').value=text;state.sendFromTranscript=true;ask(text);};
 for(const id of ['subject','evaluation','monitoring-cycle','mission-frame','assistant-target','voice-language','operation-mode'])by(id).addEventListener('change',reset,true);
 by('logout').addEventListener('click',reset,true);document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});window.addEventListener('pagehide',reset);
 by('voice-refresh').onclick=async()=>{try{const r=await api('voice/status');const lang=by('voice-language').value;by('voice-availability').textContent='STT '+(r.stt?.[lang]?.available?'local disponible':'no disponible')+' · TTS '+(r.tts?.[lang]?.available?'local disponible':'no disponible')+' · '+(r.mode||'sin configuración');}catch(e){by('voice-availability').textContent='Estado de voz no disponible. Puedes continuar por texto.';}};
 reset();
})();