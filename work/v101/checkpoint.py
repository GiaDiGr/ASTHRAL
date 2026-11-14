from pathlib import Path
import json,hashlib,zipfile,shutil,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
f=json.loads((R/'docs/v100/CANDIDATE_R2_FREEZE.json').read_text(encoding='utf8'))
archive=R/'docs/v100/candidate-code-r2.zip';assert hashlib.sha256(archive.read_bytes()).hexdigest()==f['code_archive_sha256']
out=R/'work/v101/r2-runtime';out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(archive) as z:
 for item in z.infolist():assert (out/item.filename).resolve().is_relative_to(out.resolve())
 z.extractall(out)
for row in json.loads((R/'engine/local_ai/library-v080.json').read_text(encoding='utf8'))['documents']:
 p=out/row['document'];p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():shutil.copy2(R/row['document'],p)
from vigile.local_protection import verified_backup
backup=verified_backup(R/'engine/data/mission-v100-r2/vigile.sqlite3',R/'work/v101/r2-db-copy')
D=R/'docs/v101';D.mkdir(exist_ok=False)
(D/'checkpoint.json').write_text(json.dumps({'r2_code_archive_sha256':f['code_archive_sha256'],'implementation_hash':f['implementation_hash'],'backup':backup,'r2_originals_untouched':True},indent=2),encoding='utf8')
print('R2 archive verified, isolated runtime and verified DB copy prepared.')