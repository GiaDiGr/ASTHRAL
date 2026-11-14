export class OfflineVoice {
  constructor(options) { this.options=options; this.model=null; this.active=null; this.epoch=0; }
  async install() {
    const manifest=await (await fetch('./voice-model.json')).json();
    await this.options.cacheOptional(['vosk.js','voice-assets/']);
    if(!window.Vosk) {
      await new Promise((resolve,reject)=>{
        const script=document.createElement('script');
        script.src='./vosk.js';
        script.onload=resolve;
        script.onerror=()=>reject(Error('Offline speech runtime unavailable.'));
        document.head.append(script);
      });
    }
    const parts=[];
    for(const part of manifest.parts) {
      const cache=await caches.open('asthral-optional-resources-v1');
      const response=await cache.match(new URL('./'+part.path,location.href));
      if(!response)throw Error('Offline speech model chunk missing.');
      const bytes=await response.arrayBuffer();
      const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
      if(hash!==part.sha256)throw Error('Speech model chunk integrity failed.');
      parts.push(bytes);
    }
    if(!navigator.serviceWorker?.controller)throw Error('Install offline resources and reload before loading offline speech.');
    const url=new URL('./voice-model.tar.gz?sha256='+manifest.sha256,location.href).href;
    const model=new Vosk.Model(url,2);
    model.on('asthral-stage',message=>this.options.message('Offline speech startup: '+message.stage));
    try {
      await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(Error('Offline speech model startup timed out. Reviewed text remains available.')),45000);
        model.on('load',message=>{clearTimeout(timer);message.result?resolve():reject(Error('Offline speech model could not load.'));});
        model.on('error',message=>{clearTimeout(timer);reject(Error('Offline speech runtime failed: '+(message.error??JSON.stringify(message))));});
      });
      this.model=model;
    } catch(error) { model.terminate(); throw error; }

    return {model:manifest.model,bytes:manifest.bytes,runtime:'vosk-browser-0.0.8',local:true};
  }
  recognizer() {
    if(!this.model)throw Error('Load the offline English speech model first.');
    const recognizer=new this.model.KaldiRecognizer(16000);
    recognizer.setWords(true);
    return recognizer;
  }
  async fromAudioFile(file) {
    if(!this.options.unlocked())throw Error('Unlock a local profile first.');
    if(file.size>2000000)throw Error('Audio fixture exceeds the supported test size.');
    const epoch=++this.epoch;
    const context=new AudioContext({sampleRate:16000});
    try {
      const audio=await context.decodeAudioData(await file.arrayBuffer());
      if(audio.duration>40)throw Error('Audio exceeds the 40 second bound.');
      const offline=new OfflineAudioContext(1,Math.ceil(audio.duration*16000),16000);
      const source=offline.createBufferSource();source.buffer=audio;source.connect(offline.destination);source.start();
      const normalized=await offline.startRendering();
      return await this.transcribe(normalized.getChannelData(0),epoch);
    } finally { await context.close(); }
  }
  async transcribe(samples,epoch) {
    const recognizer=this.recognizer();
    let phrases=[],words=[];
    try {
      return await new Promise((resolve,reject)=>{
        let timer;
        const finish=()=>{
          clearTimeout(timer);
          if(epoch!==this.epoch||!this.options.unlocked())return reject(Error('Recording discarded after profile lock or cancellation.'));
          resolve({text:phrases.join(' ').trim(),words,source:'SELF_REPORTED_VOICE',automatic_save:false,finalization:'EXPLICIT_WORKER_FINAL_RESULT'});
        };
        recognizer.on('result',message=>{
          if(message.result?.text) {
            phrases.push(message.result.text);
            words.push(...(message.result.result??[]));
          }
          if(message.asthral_final)finish();
        });
        recognizer.on('error',()=>reject(Error('Offline recognizer failed.')));
        recognizer.acceptWaveformFloat(new Float32Array(samples),16000);
        recognizer.retrieveFinalResult();
        timer=setTimeout(()=>reject(Error('Offline transcription timeout.')),15000);
      });
    } finally { recognizer.remove(); }
  }
  async start() {
    if(!this.options.unlocked())throw Error('Unlock a local profile first.');
    if(!this.model)throw Error('Install the offline English speech model first.');
    const epoch=++this.epoch;
    const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true},video:false});
    if(epoch!==this.epoch||!this.options.unlocked()) {stream.getTracks().forEach(t=>t.stop());return;}
    const context=new AudioContext({sampleRate:16000});
    await context.audioWorklet.addModule('./voice-worklet.js');
    if(epoch!==this.epoch) {stream.getTracks().forEach(t=>t.stop());await context.close();return;}
    const node=new AudioWorkletNode(context,'asthral-voice-pcm');
    const source=context.createMediaStreamSource(stream),mute=context.createGain();
    mute.gain.value=0;
    const chunks=[];
    this.active={stream,context,node,source,chunks,epoch,timer:null};
    node.port.onmessage=event=>{if(this.active?.epoch===epoch)chunks.push(event.data);};
    source.connect(node);node.connect(mute);mute.connect(context.destination);
    await context.resume();
    this.active.timer=setTimeout(()=>this.stop(true).then(value=>this.options.transcript(value)).catch(error=>this.options.message(error.message)),40000);
  }
  async stop(review) {
    const active=this.active;
    this.active=null;
    if(!review)this.epoch++;
    if(!active)return null;
    clearTimeout(active.timer);
    active.stream.getTracks().forEach(track=>track.stop());
    active.source.disconnect();active.node.disconnect();
    await active.context.close();
    if(!review)return null;
    const count=active.chunks.reduce((sum,part)=>sum+part.length,0);
    if(count>active.context.sampleRate*41)throw Error('Audio size bound exceeded.');
    const raw=new Float32Array(count);
    let offset=0;
    for(const part of active.chunks){raw.set(part,offset);offset+=part.length;}
    const count16000=Math.floor(count*16000/active.context.sampleRate);
    const samples=new Float32Array(count16000);
    for(let i=0;i<count16000;i++)samples[i]=raw[Math.min(raw.length-1,Math.floor(i*active.context.sampleRate/16000))];
    return this.transcribe(samples,active.epoch);
  }
  close() { this.stop(false); this.model?.terminate(); this.model=null; }
}
