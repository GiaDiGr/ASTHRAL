import create from './toolchain/node_modules/@echogarden/espeak-ng-emscripten/espeak-ng.js';
import {readFile,writeFile} from 'node:fs/promises';
const runtime=await create();const speaker=new runtime.eSpeakNGWorker();speaker.set_voice('en');
const rows=JSON.parse(await readFile(new URL('./synthetic-speech/manifest.json',import.meta.url),'utf8'));
for(const row of rows)row.phonemes=speaker.synthesize_ipa(row.text).ipa;
await writeFile(new URL('./synthetic-speech/phonemes.json',import.meta.url),JSON.stringify(rows,null,2));console.log(JSON.stringify(rows.map(x=>({id:x.id,phonemes:x.phonemes}))));

