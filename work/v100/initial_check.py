from pathlib import Path
import sys,json,zipfile,hashlib,importlib.util,os,subprocess
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.local_protection import verified_backup
from vigile.store import Store
out=ROOT/'docs/v100';dest=out/'before-v100.zip'
if dest.exists():raise ValueError('PRESERVE_EXISTING_CHECKPOINT')
with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
 for directory in ('engine/vigile','engine/tests','engine/tools','docs/v011'):
  for p in (ROOT/directory).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(ROOT).as_posix())
 for name in ('engine/pyproject.toml','engine/requirements.lock','VIGILE_v011_START_HERE.md'):z.write(ROOT/name,name)
report={'checkpoint_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'voice_packages':{n:bool(importlib.util.find_spec(n)) for n in ('vosk','faster_whisper','whisper','av','numpy','soundfile','pyttsx3','comtypes','win32com')},'installed_model_paths':[]}
for base in (ROOT/'engine/local_ai',Path.home()/'.cache/huggingface',Path.home()/'.cache/whisper',Path.home()/'Downloads'):
 if base.exists():
  report['installed_model_paths'] += [str(p) for p in base.rglob('*') if any(s in p.name.lower() for s in ('vosk','whisper','piper'))][:80]
report['backup']=verified_backup(ROOT/'engine/data/mission-v011-final/vigile.sqlite3',ROOT/'engine/data/backups/v011-before-v100')
(out/'initial-environment.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='backup'},indent=2))