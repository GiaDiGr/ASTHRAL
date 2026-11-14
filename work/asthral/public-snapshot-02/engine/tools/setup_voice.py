"""Explicit setup only. Default verifies installed voice models; never downloads at runtime."""
from pathlib import Path
import argparse,json,hashlib,zipfile,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--download-models',action='store_true',help='Explicitly download two Apache-2.0 Vosk archives (~79 MB compressed)');a=p.parse_args()
 manifest=json.loads((ROOT/'vigile/voice_assets/models.json').read_text(encoding='utf8'));base=ROOT/'local_ai/voice';base.mkdir(parents=True,exist_ok=True)
 for row in manifest['models']:
  if a.download_models and not (base/row['model']/'am/final.mdl').is_file():
   archive=base/(row['model']+'.zip')
   if not archive.exists():
    print('Setup download',row['url'],row['archive_bytes'],'bytes; Apache-2.0',flush=True)
    with urllib.request.urlopen(row['url'],timeout=60) as source,archive.open('xb') as target:
     size=0
     while block:=source.read(1024*1024):
      size+=len(block)
      if size>row['archive_bytes']:raise ValueError('ARCHIVE_SIZE_EXCEEDED')
      target.write(block)
   if hashlib.sha256(archive.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('ARCHIVE_HASH_MISMATCH_PRESERVED_FOR_INSPECTION')
   with zipfile.ZipFile(archive) as z:
    if sum(i.file_size for i in z.infolist())>300_000_000:raise ValueError('EXPANSION_LIMIT')
    for i in z.infolist():
     if not (base/i.filename).resolve().is_relative_to((base/row['model']).resolve()):raise ValueError('ZIP_PATH_REJECTED')
    z.extractall(base)
  for item in row['files']:
   path=(base/item['path']).resolve()
   if not path.is_relative_to((base/row['model']).resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('MODEL_MISSING_OR_HASH_MISMATCH: '+row['model'])
  print(row['language'],'VERIFIED',row['model'])
 print('No runtime downloads. Windows SAPI EN/ES voices must already be installed. Hash pinning is not a vendor signature.')
if __name__=='__main__':main()