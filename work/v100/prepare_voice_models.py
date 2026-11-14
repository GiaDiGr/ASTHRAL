from pathlib import Path
import urllib.request,json,hashlib,zipfile,time
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'engine/local_ai/voice';base.mkdir(exist_ok=False)
rows=[]
for lang,name in [('en','vosk-model-small-en-us-0.15'),('es','vosk-model-small-es-0.42')]:
 url='https://alphacephei.com/vosk/models/'+name+'.zip';p=base/(name+'.zip');start=time.perf_counter()
 with urllib.request.urlopen(url,timeout=60) as source,p.open('xb') as target:
  total=0
  while block:=source.read(1024*1024):
   total+=len(block)
   if total>120_000_000:raise ValueError('DOWNLOAD_SIZE_LIMIT')
   target.write(block)
 with zipfile.ZipFile(p) as z:
  if sum(i.file_size for i in z.infolist())>300_000_000:raise ValueError('EXPANDED_SIZE_LIMIT')
  for i in z.infolist():
   if not (base/i.filename).resolve().is_relative_to(base.resolve()):raise ValueError('ZIP_PATH_ESCAPE')
  z.extractall(base)
 rows.append({'language':lang,'model':name,'url':url,'license':'Apache-2.0','archive_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':[{'path':str(f.relative_to(base)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in (base/name).rglob('*') if f.is_file()],'seconds':time.perf_counter()-start})
 print(lang,total,flush=True)
(ROOT/'docs/v100/voice-model-downloads.json').write_text(json.dumps({'models':rows,'automatic_runtime_downloads':False,'redistribution_in_release_zip':False},indent=2),encoding='utf8')