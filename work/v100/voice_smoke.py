from pathlib import Path
import sys,json,wave,io
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.voice import LocalVoice
v=LocalVoice();print(json.dumps(v.status(),indent=2))
for lang,text in [('en','Vigile, what information is missing from my evaluation?'),('es','Vigile, qué cambió desde mi última evaluación?')]:
 raw,metrics=v.synthesize(text,lang)
 with wave.open(io.BytesIO(raw),'rb') as w: print(lang,w.getparams())
 print(json.dumps({'reference':text,'stt':v.transcribe(raw,lang),'tts':metrics},ensure_ascii=True))
v.close()