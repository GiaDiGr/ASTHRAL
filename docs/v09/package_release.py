from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(r'C:\Users\Gianni\Desktop\Vigile');D=ROOT/'docs/v09'
manifest=json.loads((D/'change-manifest.json').read_text());assert all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest['files'])
for p in D.glob('*.py'):compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
index=json.loads((ROOT/'engine/local_ai/library-v080.json').read_text(encoding='utf8'))
names={r['path'] for r in manifest['files']}|{r['document'] for r in index['documents']}|{'engine/local_ai/library-v080.json'}
names|={p.relative_to(ROOT).as_posix() for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='delivery-hashes.json'}
with zipfile.ZipFile(D/'release-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in sorted(names):z.write(ROOT/name,name)
with zipfile.ZipFile(D/'release-source.zip') as z:
 assert z.testzip() is None
 assert not any(n.endswith(('.sqlite3','reader-token.txt','server-tokens.json','portal-access.txt')) for n in z.namelist())
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.is_file() and p.name!='delivery-hashes.json'}
(D/'delivery-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf8')
print(json.dumps({'release_files':len(names),'archive_bytes':(D/'release-source.zip').stat().st_size,'implementation_hash':manifest['implementation_hash'],'no_database_or_credentials':True,'helpers_compile':True},indent=2))
