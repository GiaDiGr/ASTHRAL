"""Pin the previous runtime to its archived source before upgrading the working tree.
Only known VIGILE backend/portal children on 8895/8896 may be restarted. Never Ollama.
"""
from pathlib import Path
import json,zipfile,shutil,subprocess,os,sys,time,httpx,base64
ROOT=Path(__file__).resolve().parents[2];archive=ROOT/'work/v011/v010-runtime';engine=archive/'engine'
if not archive.exists():
    archive.mkdir()
    with zipfile.ZipFile(ROOT/'docs/v011/before-v011.zip') as z:
        for name in z.namelist():
            target=(archive/name).resolve()
            if not target.is_relative_to(archive.resolve()):raise ValueError('ARCHIVE_PATH_ESCAPE')
        z.extractall(archive)
    for name in ('docs/clinical/deep-research-report-2026-10-16.md','01_INFORMES/REPORTE_CONSOLIDADO_COMPLETO.md','docs/v07/README.md','docs/v07/CONTRACTS.md','docs/v08/sources/ADA2026-short-excerpt.txt'):
        target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
verify=archive/'verify_old.py'
verify.write_text('''import os,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'engine'))
from vigile.store import Store
from vigile.service import Engine
from vigile.registry import Registry
from vigile.monitoring import MonitoringService
from vigile.clinical_engine import ClinicalService
root=Path(os.environ['VIGILE_CORPUS']);s=Store(root/'engine/data/backups/v0100-before-v011/vigile.sqlite3')
try:
 e=Engine(Registry(root),s);assert e.implementation_hash=='c896211d20b52ade1279aeb306421891f5e29b542f910074d542321c4b815db9'
 result={'implementation_hash':e.implementation_hash,'clinical':[ClinicalService(e).replay(r['id']) for r in s.all('clinical_evaluation')],'monitoring':[MonitoringService(e).replay(r['id']) for r in s.all('monitoring_run')],'audit':s.verify()}
 assert all(r['matches'] for r in result['clinical']+result['monitoring']) and result['audit']
 (root/'docs/v011/archived-v010-replays.json').write_text(json.dumps(result,indent=2));print('Archived v010: all 39 replays match')
finally:s.close()
''',encoding='utf8')
env=os.environ.copy();env.pop('VIGILE_TOKENS',None);env.update(VIGILE_CORPUS=str(ROOT),VIGILE_DB=str(ROOT/'engine/data/portal-v0100-integrated/vigile.sqlite3'),VIGILE_TOKEN_FILE=str(ROOT/'engine/data/portal-v0100-integrated/server-tokens.json'))
subprocess.run([sys.executable,str(verify)],env=env,check=True)
if '--restart' not in sys.argv:sys.exit(0)
net=subprocess.run(['netstat','-ano','-p','tcp'],capture_output=True,text=True,check=True).stdout
pids={}
for line in net.splitlines():
    cols=line.split()
    if len(cols)==5 and cols[1] in ('127.0.0.1:8895','127.0.0.1:8896') and cols[3]=='LISTENING':pids[int(cols[1].split(':')[1])]=int(cols[-1])
if set(pids)!={8895,8896}:raise ValueError('EXPECTED_VIGILE_LISTENERS_REQUIRED')
query='$ids=@('+','.join(str(p) for p in pids.values())+'); Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -in $ids} | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress'
raw=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(query.encode('utf-16le')).decode()],capture_output=True,text=True,timeout=30,check=True).stdout
processes=json.loads(raw);processes=[processes] if isinstance(processes,dict) else processes
for port,pid in pids.items():
    cmd=next(p['CommandLine'] for p in processes if p['ProcessId']==pid)
    marker='vigile.api:create_app' if port==8895 else 'vigile.portal'
    inline_backend=port==8895 and ('vigile.api import create_app' in cmd and 'uvicorn.run' in cmd or '-m vigile serve' in cmd) and 'portal-v0100-integrated' in cmd
    if (marker not in cmd and not inline_backend) or str(port) not in cmd:
        import re
        print({'port':port,'pid':pid,'python': 'python' in cmd.lower(),'vigile_modules':re.findall(r'vigile[.\w:]*',cmd),'contains_uvicorn':'uvicorn' in cmd,'contains_create_app':'create_app' in cmd,'contains_old_folder':'portal-v0100-integrated' in cmd,'contains_expected_port':str(port) in cmd})
        raise ValueError('PROCESS_IDENTITY_MISMATCH_NO_PROCESS_STOPPED')
if any('ESTABLISHED' in line and any('127.0.0.1:'+str(p) in line for p in (8891,8895,8896)) for line in net.splitlines()):
    raise ValueError('ACTIVE_LOCAL_CONNECTION_NO_RESTART')
# Only the verified idle VIGILE development listeners; never traverse process trees.
for pid in pids.values():subprocess.run(['taskkill','/F','/PID',str(pid)],capture_output=True,check=True)
commands=[[sys.executable,'-m','uvicorn','vigile.api:create_app','--factory','--host','127.0.0.1','--port','8895','--no-access-log'],
          [sys.executable,'-m','vigile.portal','--config',str(ROOT/'engine/data/portal-v0100-integrated/portal-config.json'),'--port','8896']]
children=[]
for index,cmd in enumerate(commands):
    log=(ROOT/'work/v011'/('legacy-backend.log' if not index else 'legacy-portal.log')).open('ab')
    child=subprocess.Popen(cmd,cwd=engine,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));children.append(child.pid);log.close()
for _ in range(20):
    try:
        with httpx.Client(trust_env=False,timeout=2) as c:
            a=c.get('http://127.0.0.1:8895/health');b=c.get('http://127.0.0.1:8896/')
        if a.status_code==b.status_code==200:break
    except httpx.HTTPError:pass
    time.sleep(.5)
else:raise RuntimeError('ARCHIVED_SERVICE_START_FAILED_SEE_LOCAL_LOGS')
(ROOT/'docs/v011/legacy-runtime.json').write_text(json.dumps({'archive':str(archive),'pids':children,'ports':[8895,8896],'health':[a.status_code,b.status_code],'ollama_unchanged':True},indent=2))
print('Legacy v010 source pinned, 8895/8896 healthy; Ollama unchanged.')
