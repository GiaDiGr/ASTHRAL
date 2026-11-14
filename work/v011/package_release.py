from pathlib import Path
import hashlib,json,zipfile,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/v011'
result=json.loads((OUT/'RESULTS.json').read_text())
source=[]
for directory in ('engine/vigile','engine/tests','engine/tools'):
 source.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.js','.css','.html','.md'))
source.append(ROOT/'engine/pyproject.toml')
with zipfile.ZipFile(OUT/'before-v011.zip') as z:
 before={i.filename:hashlib.sha256(z.read(i)).hexdigest() for i in z.infolist() if not i.is_dir()}
changes=[]
for p in sorted(source):
 relative=p.relative_to(ROOT).as_posix();sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if before.get(relative)!=sha:changes.append({'path':relative,'change':'MODIFIED' if relative in before else 'NEW','sha256':sha})
clinical_json=[p for p in source if 'clinical_knowledge' in p.parts and p.suffix=='.json']
assert all(before[p.relative_to(ROOT).as_posix()]==hashlib.sha256(p.read_bytes()).hexdigest() for p in clinical_json)
manifest={'release':'0.11.0','scope':'CODE_AND_REVIEW_NOT_FULL_INSTALLATION','implementation_hash':result['implementation_hash'],'knowledge_hash':result['knowledge_hash'],'clinical_json_unchanged':True,'clinical_validation':False,'tests':result['tests'],'changes':changes,'files':[],'excluded':['databases','credentials','models','reserved_case_bank','full_original_corpus']}
selected=list(source)+[ROOT/'VIGILE_v011_START_HERE.md']
selected.extend(p for p in OUT.rglob('*') if p.is_file() and p.name not in ('release-manifest.json','archive-verification.json'))
for p in sorted(set(selected)):
 raw=p.read_bytes();manifest['files'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifestpath=OUT/'release-manifest.json';manifestpath.write_text(json.dumps(manifest,indent=2),encoding='utf8')
archive=ROOT/'VIGILE_v0.11.0_code_review.zip'
# Repackage only this newly-created release after redacting ephemeral pytest traces.
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(set(selected+[manifestpath])):z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for file in manifest['files']:assert hashlib.sha256(z.read(file['path'])).hexdigest()==file['sha256']
release={'archive':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'files':len(manifest['files'])+1,'clinical_json_unchanged':True}
(OUT/'archive-verification.json').write_text(json.dumps(release,indent=2),encoding='utf8')
print(json.dumps(release,indent=2));print(json.dumps(changes,indent=2))