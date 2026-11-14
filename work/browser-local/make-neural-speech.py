import sys,json,array,wave,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('work/browser-local/tts-toolchain').resolve()))
import numpy as np
import onnxruntime as ort
root=Path('work/browser-local/synthetic-speech');config=json.loads((root/'en_US-ljspeech-high.onnx.json').read_bytes());mapping=config['phoneme_id_map'];rows=json.loads((root/'phonemes.json').read_bytes())
options=ort.SessionOptions();options.intra_op_num_threads=2;session=ort.InferenceSession(str(root/'piper.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
print('Inputs:',[(i.name,i.shape) for i in session.get_inputs()])
for row in rows:
 phonemes=row['phonemes'].replace('_','').strip()+'.';missing=set(phonemes)-set(mapping);assert not missing,repr(missing)
 ids=[*mapping['^'],*mapping['_']]
 for character in phonemes:ids.extend(mapping[character]);ids.extend(mapping['_'])
 ids.extend(mapping['$']);scales=config.get('inference',{})
 output=session.run(None,{'input':np.array([ids],dtype=np.int64),'input_lengths':np.array([len(ids)],dtype=np.int64),'scales':np.array([scales.get('noise_scale',.667),scales.get('length_scale',1),scales.get('noise_w',.8)],dtype=np.float32)})[0].reshape(-1)
 pcm=(np.clip(output,-1,1)*32767).astype('<i2').tobytes();path=root/('neural-'+row['id']+'.wav')
 with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(config['audio']['sample_rate']);w.writeframes(pcm)
 row.update(file=path.name,source='SYNTHETIC_LOCAL_PIPER_LJSPEECH_TEST_ONLY',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size);row.pop('phonemes')
(root/'neural-manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf8');print(json.dumps([{'file':r['file'],'bytes':r['bytes']} for r in rows]))
