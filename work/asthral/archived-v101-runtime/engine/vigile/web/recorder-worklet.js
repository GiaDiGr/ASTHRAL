// PCM is transferred to this page's memory only; no network or persistence.
class VigilePCM extends AudioWorkletProcessor {
 process(inputs,outputs){
  const samples=inputs[0]?.[0];
  if(samples){const copy=new Float32Array(samples);this.port.postMessage(copy,[copy.buffer]);}
  // The graph stays active through a zero-gain destination; no monitor playback.
  return true;
 }
}
registerProcessor('vigile-pcm',VigilePCM);