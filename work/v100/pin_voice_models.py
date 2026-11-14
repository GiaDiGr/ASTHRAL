from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
manifest=json.loads((ROOT/'docs/v100/voice-model-downloads.json').read_text(encoding='utf8'))
(ROOT/'engine/local_ai/voice/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
p=ROOT/'engine/vigile/voice.py';s=p.read_text(encoding='utf8');s=s.replace('import io,wave,array,math,json,time,threading,subprocess,base64,os,gc','import io,wave,array,math,json,time,threading,subprocess,base64,os,gc,hashlib')
s=s.replace('def __init__(self,models=None):','def __init__(self,models=None,manifest=None):')
s=s.replace("        self.lock=threading.Lock();", "        self.manifest=Path(manifest) if manifest else root/'manifest.json';self._verified={};self._failed=set()\n        self.lock=threading.Lock();")
anchor='    def _sapi(self,payload,timeout=25):'
s=s.replace(anchor,'''    def _verify_model(self,language):
        try:
            value=json.loads(self.manifest.read_text(encoding='utf8'))
            row=next(r for r in value['models'] if r['language']==language and r['model']==self.paths[language].name)
            entries=[]
            for item in row['files']:
                file=(self.paths[language].parent/item['path']).resolve()
                if not file.is_relative_to(self.paths[language]) or not file.is_file():raise ValueError('MODEL_PATH')
                stat=file.stat();entries.append((str(file),stat.st_size,stat.st_mtime_ns,item['sha256']))
            fingerprint=(hashlib.sha256(self.manifest.read_bytes()).hexdigest(),entries)
            if self._verified.get(language)!=fingerprint:
                for name,size,mtime,expected in entries:
                    if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=expected:raise ValueError('MODEL_HASH')
                self._verified[language]=fingerprint
            return True
        except (OSError,ValueError,KeyError,TypeError,StopIteration):
            self._failed.add(language);raise VoiceError('STT_MODEL_INTEGRITY_FAILED') from None

'''+anchor)
s=s.replace("'model':p.name} for lang,p", "'model':p.name,'load_verified':lang in self._verified} for lang,p")
s=s.replace("'available':installed and (p/'am/final.mdl').is_file() and admitted", "'available':installed and self.manifest.is_file() and (p/'am/final.mdl').is_file() and admitted and lang not in self._failed")
s=s.replace("'mode':mode,'resource_admitted'", "'mode':mode,'busy':self.lock.locked(),'resource_admitted'")
s=s.replace("            if self._language!=language:\n                self._model=None;gc.collect();", "            self._verify_model(language)\n            if self._model is None or self._language!=language:\n                self._model=None;self._language=None;gc.collect();")
s=s.replace("        except (ImportError,RuntimeError):raise VoiceError('STT_LOCAL_ENGINE_FAILED') from None", "        except VoiceError:raise\n        except Exception:\n            self._model=None;self._language=None\n            raise VoiceError('STT_LOCAL_ENGINE_FAILED') from None")
p.write_text(s,encoding='utf8')
p=ROOT/'engine/vigile/voice_api.py';s=p.read_text(encoding='utf8');s=s.replace("'STT_LOCAL_ENGINE_FAILED','TTS_LOCAL", "'STT_LOCAL_ENGINE_FAILED','STT_MODEL_INTEGRITY_FAILED','TTS_LOCAL")
p.write_text(s,encoding='utf8')