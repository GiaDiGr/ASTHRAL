"""Local WAV/PCM voice. No cloud API, downloads, audio files or clinical writes."""
from pathlib import Path
import io,wave,array,math,json,time,threading,subprocess,base64,os,gc,hashlib

MAX_SECONDS=40
MAX_WAV_BYTES=1_350_000
class VoiceError(ValueError):pass

def decode_wav(raw):
    if not isinstance(raw,bytes) or not 44<=len(raw)<=MAX_WAV_BYTES:raise VoiceError('AUDIO_SIZE_INVALID')
    try:
        with wave.open(io.BytesIO(raw),'rb') as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())!=(1,2,16000,'NONE'):raise VoiceError('PCM16_MONO_16000_REQUIRED')
            n=w.getnframes()
            if not 3200<=n<=16000*MAX_SECONDS:raise VoiceError('AUDIO_DURATION_INVALID')
            pcm=w.readframes(n)
            if len(pcm)!=n*2:raise VoiceError('AUDIO_TRUNCATED')
    except (wave.Error,EOFError,OverflowError):raise VoiceError('AUDIO_FORMAT_INVALID') from None
    samples=array.array('h',pcm)
    rms=math.sqrt(sum(v*v for v in samples)/len(samples))
    if rms<30:raise VoiceError('AUDIO_SILENCE_OR_TOO_QUIET')
    return pcm,n/16000,rms

def safe_environment():
    allowed={'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PSMODULEPATH','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','PROCESSOR_ARCHITECTURE','PROCESSOR_IDENTIFIER','NUMBER_OF_PROCESSORS','HOMEDRIVE','HOMEPATH','PATHEXT'}
    return {k:v for k,v in os.environ.items() if k.upper() in allowed}

class LocalVoice:
    def __init__(self,models=None,manifest=None):
        root=Path(__file__).resolve().parents[1]/'local_ai/voice'
        self.paths={k:Path(v).resolve() for k,v in (models or {'en':root/'vosk-model-small-en-us-0.15','es':root/'vosk-model-small-es-0.42'}).items()}
        self.manifest=Path(manifest) if manifest else Path(__file__).with_name('voice_assets')/'models.json';self._verified={};self._failed=set()
        self.lock=threading.Lock();self._model=None;self._language=None;self._voices=None;self._voices_at=0
    def _verify_model(self,language):
        try:
            value=json.loads(self.manifest.read_text(encoding='utf8'))
            row=next(r for r in value['models'] if r['language']==language and r['model']==self.paths[language].name)
            if not row['files']:raise ValueError('EMPTY_MODEL_MANIFEST')
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

    def _sapi(self,payload,timeout=25):
        script=Path(__file__).with_name('voice_assets')/'sapi.ps1'
        try:
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(script)],input=json.dumps(payload,ensure_ascii=True),text=True,capture_output=True,timeout=timeout,env=safe_environment(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode or len(result.stdout)>22_000_000:raise VoiceError('TTS_LOCAL_ENGINE_FAILED')
            return json.loads(result.stdout)
        except (OSError,subprocess.TimeoutExpired,json.JSONDecodeError):raise VoiceError('TTS_LOCAL_ENGINE_UNAVAILABLE') from None
    def status(self,mode='FULL'):
        try:
            if self._voices is None or time.monotonic()-self._voices_at>60:
                self._voices=self._sapi({'operation':'status'});self._voices_at=time.monotonic()
            voices=self._voices
        except VoiceError:voices={}
        from importlib.util import find_spec
        installed=find_spec('vosk') is not None
        from .space_compute import available_memory_bytes
        free=available_memory_bytes();admitted=free is None or free>=512*1024**2
        return {'stt':{lang:{'available':installed and self.manifest.is_file() and (p/'am/final.mdl').is_file() and admitted and lang not in self._failed,'model':p.name,'load_verified':lang in self._verified} for lang,p in self.paths.items()},'tts':{lang:{'available':bool(voices.get(lang)) and admitted,'voice':voices.get(lang)} for lang in ('en','es')},'mode':mode,'busy':self.lock.locked(),'resource_admitted':admitted,'voice_profile':'SAME_CPU_PROFILE_NO_PROVEN_LOW_POWER_REDUCTION','llm_required':False,'audio_retention':'MEMORY_ONLY_NO_RECORDING_FILES','max_seconds':MAX_SECONDS,'max_wav_bytes':MAX_WAV_BYTES,'stt_accuracy':'NOT_MEDICALLY_VALIDATED','process_isolation':'SAME_USER_NOT_A_SECURITY_BOUNDARY'}
    def transcribe(self,raw,language,mode='FULL'):
        if language not in ('en','es'):raise VoiceError('LANGUAGE_NOT_SUPPORTED')
        pcm,seconds,rms=decode_wav(raw)
        if not self.lock.acquire(blocking=False):raise VoiceError('VOICE_BUSY')
        start=time.perf_counter()
        try:
            if not self.status(mode)['stt'][language]['available']:raise VoiceError('STT_UNAVAILABLE_OR_RESOURCE_LIMIT')
            import vosk
            vosk.SetLogLevel(-1)
            self._verify_model(language)
            if self._model is None or self._language!=language:
                self._model=None;self._language=None;gc.collect();self._model=vosk.Model(str(self.paths[language]));self._language=language
            rec=vosk.KaldiRecognizer(self._model,16000);rec.SetWords(True);words=[];parts=[]
            for offset in range(0,len(pcm),8000):
                if rec.AcceptWaveform(pcm[offset:offset+8000]):
                    r=json.loads(rec.Result());parts.append(r.get('text',''));words.extend(r.get('result',[]))
            r=json.loads(rec.FinalResult());parts.append(r.get('text',''));words.extend(r.get('result',[]))
            text=' '.join(p for p in parts if p).strip()
            if not text:raise VoiceError('NO_SPEECH_RECOGNIZED')
            if len(text)>1200:raise VoiceError('TRANSCRIPT_TOO_LONG')
            return {'text':text,'language':language,'words':words[:512],'capture_seconds':seconds,'transcription_seconds':time.perf_counter()-start,'model':self.paths[language].name,'requires_user_review':True,'is_authoritative_measurement':False,'retained_audio':False}
        except VoiceError:raise
        except Exception:
            self._model=None;self._language=None
            raise VoiceError('STT_LOCAL_ENGINE_FAILED') from None
        finally:self.lock.release()
    def synthesize(self,text,language,rate=0,mode='FULL'):
        if language not in ('en','es') or not isinstance(text,str) or not 1<=len(text)<=3500 or not isinstance(rate,int) or not -3<=rate<=3:raise VoiceError('TTS_INPUT_INVALID')
        if not self.lock.acquire(blocking=False):raise VoiceError('VOICE_BUSY')
        start=time.perf_counter()
        try:
            if not self.status(mode)['tts'][language]['available']:raise VoiceError('TTS_UNAVAILABLE_OR_RESOURCE_LIMIT')
            r=self._sapi({'operation':'synthesize','language':language,'rate':rate,'text':text})
            raw=base64.b64decode(r['audio'],validate=True)
            if not 44<len(raw)<16_000_000 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':raise VoiceError('TTS_INVALID_OUTPUT')
            return raw,{'synthesis_seconds':time.perf_counter()-start,'voice':r['voice'],'audio_bytes':len(raw),'audio_retained':False}
        except (KeyError,TypeError):raise VoiceError('TTS_LOCAL_ENGINE_FAILED') from None
        finally:self.lock.release()
    def close(self):self._model=None;self._language=None;gc.collect()