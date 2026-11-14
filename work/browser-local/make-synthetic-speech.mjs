import create from './toolchain/node_modules/@echogarden/espeak-ng-emscripten/espeak-ng.js';
import {writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const runtime=await create();const speaker=new runtime.eSpeakNGWorker();speaker.set_voice('en-us');speaker.set_rate(145);
await mkdir(new URL('./synthetic-speech/',import.meta.url),{recursive:true});
const texts=[
 ['heart-rate','record my heart rate as eighty two beats per minute right now'],
 ['temperature','record my temperature as thirty seven point two degrees celsius right now'],
 ['blood-pressure','record my blood pressure as one hundred twenty over eighty millimeters of mercury right now'],
 ['negation','I have no chest pain'],
 ['question','Do I need to record my glucose'],
 ['sleep','record my sleep duration as seven hours in the past twenty four hours']
];const manifest=[];
for(const [id,text] of texts){const parts=[];speaker.synthesize(text,data=>{parts.push(Buffer.from(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength)));return false;});const pcm=Buffer.concat(parts);const rate=speaker.get_samplerate();const header=Buffer.alloc(44);header.write('RIFF');header.writeUInt32LE(pcm.length+36,4);header.write('WAVEfmt ',8);header.writeUInt32LE(16,16);header.writeUInt16LE(1,20);header.writeUInt16LE(1,22);header.writeUInt32LE(rate,24);header.writeUInt32LE(rate*2,28);header.writeUInt16LE(2,32);header.writeUInt16LE(16,34);header.write('data',36);header.writeUInt32LE(pcm.length,40);const wav=Buffer.concat([header,pcm]);await writeFile(new URL('./synthetic-speech/'+id+'.wav',import.meta.url),wav);manifest.push({id,text,source:'SYNTHETIC_ESPEAK_NG_EMSCRIPTEN_0.3.5',sample_rate:rate,bytes:wav.length,sha256:createHash('sha256').update(wav).digest('hex')});}
await writeFile(new URL('./synthetic-speech/manifest.json',import.meta.url),JSON.stringify(manifest,null,2));console.log(JSON.stringify(manifest.map(x=>({id:x.id,bytes:x.bytes,sample_rate:x.sample_rate}))));
