from pathlib import Path
import socket,subprocess,json,time,httpx
root=Path(__file__).resolve().parents[2]/'engine';folder=root/'data/portal-v090-release'
for port in (8895,8896):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
rows=[]
for name,args in [('backend',['-m','vigile','serve','--integration-dir',str(folder),'--port','8895']),('portal',['-m','vigile.portal','--config',str(folder/'portal-config.json'),'--port','8896'])]:
 with (folder/(name+'.log')).open('a',encoding='utf8') as log:p=subprocess.Popen([str(root/'.venv/Scripts/python.exe'),*args],cwd=root,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 rows.append({'name':name,'pid':p.pid,'args':args})
(root.parent/'docs/v09/processes.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
with httpx.Client(trust_env=False,timeout=2) as c:
 for url in ('http://127.0.0.1:8895/health','http://127.0.0.1:8896/'):
  for _ in range(30):
   try:
    if c.get(url).status_code==200:break
   except httpx.HTTPError:pass
   time.sleep(.2)
  else:raise RuntimeError('START_FAILED')
print(json.dumps(rows))

