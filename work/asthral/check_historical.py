from pathlib import Path
import sys,zipfile,subprocess,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.local_protection import verified_backup,restrict_directory
out=R/'work/asthral/archived-v101-runtime';out.mkdir(exist_ok=False)
with zipfile.ZipFile(R/'docs/v101-ux/candidate-code-v101-ux.zip') as z:
 for name in z.namelist():assert (out/name).resolve().is_relative_to(out.resolve())
 z.extractall(out)
for source,dest in [(R/'work/asthral/baseline-db/vigile.sqlite3',R/'work/asthral/replay-v101-db'),(R/'work/v101/r2-db-copy/vigile.sqlite3',R/'work/asthral/replay-r2-db')]:verified_backup(source,dest);restrict_directory(dest)
script='''from pathlib import Path
import sys,json
R=Path(sys.argv[1]);sys.path.insert(0,sys.argv[2])
from vigile.api import create_app
from fastapi.testclient import TestClient
with TestClient(create_app(R,sys.argv[3],{})) as c:
 engine=c.app.state.engine
 clinical=[c.app.state.clinical.replay(r['id']) for r in engine.store.all('clinical_evaluation')]
 monitoring=[c.app.state.monitoring.replay(r['id']) for r in engine.store.all('monitoring_run')]
 assert all(r['matches'] for r in clinical+monitoring) and engine.store.verify()
 result={'version':sys.argv[4],'clinical_replays':len(clinical),'monitoring_replays':len(monitoring),'all_match':True,'audit_valid':True,'implementation_hash':engine.implementation_hash,'isolated_copy_only':True,'original_database_opened':False}
 Path(sys.argv[5]).write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
'''
(R/'work/asthral/replay_archived.py').write_text(script,encoding='utf8')
processes=[]
for version,code,db in [('R2',R/'work/v101/r2-runtime/engine',R/'work/asthral/replay-r2-db/vigile.sqlite3'),('v1.0.1-UX',out/'engine',R/'work/asthral/replay-v101-db/vigile.sqlite3')]:
 p=subprocess.Popen([sys.executable,str(R/'work/asthral/replay_archived.py'),str(R),str(code),str(db),version,str(R/'docs/asthral'/('replay-'+version+'.json'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8');processes.append(p)
for p in processes:
 stdout,stderr=p.communicate(timeout=120);print(stdout.strip());assert p.returncode==0,stderr[-1000:]