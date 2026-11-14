from pathlib import Path
import json,hashlib,zipfile,sys
R=Path(__file__).resolve().parents[2];D=R/'docs/v100';f=json.loads((D/'CANDIDATE_R2_FREEZE.json').read_text(encoding='utf8'))
for rel,h in f['files'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,rel
# Explicit allowlist; no runtime data/secrets/model weights/failed development XML.
files=set()
for rel in f['files']:
 if '/data/' not in rel:files.add(rel)
files.add('MANIFIESTO_SHA256.json');files.update(i['path'].replace('\\','/') for i in json.loads((R/'MANIFIESTO_SHA256.json').read_text(encoding='utf-8-sig')))
files.add('VIGILE_v100_START_HERE.md')
library=json.loads((R/'engine/local_ai/library-v080.json').read_text(encoding='utf8'))
files.update(d['document'] for d in library['documents'])
for p in (R/'docs/v011').glob('*.md'):files.add(p.relative_to(R).as_posix())
for p in D.rglob('*'):
 if not p.is_file() or p.suffix not in ('.md','.json','.jpg','.wav','.xml'):continue
 if p.name in ('voice-development-tests.xml',):continue
 # Keep failed raw development trace locally; only final passing evidence in deliverable.
 if p.suffix=='.xml' and p.name not in ('baseline-tests.xml','final-tests.xml','final-r2-tests.xml'):continue
 if '/e2e-development/' in p.as_posix():continue
 files.add(p.relative_to(R).as_posix())
for name in ['evaluate_product_voice.py','benchmark_voice.py','evaluate_rag.py','benchmark_prefixes.py','verify_old.py','additional_rag.py','make_results.py']:
 files.add('work/v100/'+name)
files.update(['docs/v09/rag-qrels.json','docs/v09/audit-bank.json'])
# Old comparison needs private original receipt DB, intentionally excluded; reports retained.
rows=[]
for rel in sorted(files):
 p=(R/rel).resolve();assert p.is_relative_to(R.resolve()) and p.is_file(),rel
 assert not any(part in ('data','.venv','ollama-models','ollama-v0.40.6') for part in Path(rel).parts),rel
 assert p.suffix not in ('.sqlite3','.dpapi','.exe','.gguf','.bin'),rel
 raw=p.read_bytes()
 assert b'VIGILE-DPAPI-1:' not in raw or rel.startswith(('engine/vigile/local_protection.py','engine/tests/')),rel
 rows.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest={'format':'VIGILE_REVIEW_PACKAGE_1','date':'2026-10-27','scope':'Internal team review; original research documents retain their original rights; not a public redistribution license','files':rows,'excludes':['Databases/WAL/backups','DPAPI envelopes and credentials','Private keys/anchors','Ollama/runtime binaries','All model weights and Windows voices'],'requires_separate_provisioning':['Python/Windows voices','Ollama and vigile-qwen3-4b:latest','Explicit Vosk setup'],'reserved_used':True,'source_freeze_verified':True,'clinical_validation':False}
(D/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
package=R/'VIGILE-v1.0.0-r2-team-review.zip'
with package.open('xb') as out:
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for row in rows:z.write(R/row['path'],row['path'])
  z.write(D/'PACKAGE_MANIFEST.json','docs/v100/PACKAGE_MANIFEST.json')
with zipfile.ZipFile(package) as z:
 for row in rows:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
report={'path':package.name,'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'bytes':package.stat().st_size,'files':len(rows)+1,'source_freeze_verified':True,'archive_contents_verified':True,'no_runtime_data_or_weights':True}
(D/'PACKAGE_CHECK.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))