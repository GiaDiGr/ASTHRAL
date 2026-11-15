"""Transport diagnostics using unchanged static-handler behavior and real clients."""
from pathlib import Path
import sys,json,hashlib,time,threading,traceback,urllib.request
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
from serve_browser_build import Handler
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'web-local/build-output-final-integration-r6';OUT=ROOT/'work/transport-investigation';OUT.mkdir(exist_ok=True)
log=[];guard=threading.Lock()
class DiagnosticHandler(Handler):
 protocol_version="HTTP/1.0"  # Explicit negative control, not the corrected dev server
 def do_GET(self):
  started=time.monotonic();item={'path':self.path,'range':self.headers.get('Range'),'started':started}
  try:super().do_GET();item['completed_handler']=True
  except Exception as error:item['exception']=repr(error);item['traceback']=traceback.format_exc();raise
  finally:
   item['seconds']=time.monotonic()-started
   with guard:log.append(item);(OUT/'server.json').write_text(json.dumps(log,indent=2))
 def send_header(self,name,value):
  super().send_header(name,value)
class Server(ThreadingHTTPServer):
 def handle_error(self,request,address):
  with guard:log.append({'server_exception':traceback.format_exc()})
server=Server(('127.0.0.1',8930),partial(DiagnosticHandler,directory=str(BUILD)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
paths=['runtime/pydantic-2.12.5-py3-none-any.whl','runtime/sqlite3-1.0.0-cp313-cp313-pyodide_2025_0_wasm32.whl','runtime/pyodide-lock.json','engine.zip','corpus.json']
expected={path:hashlib.sha256((BUILD/path).read_bytes()).hexdigest() for path in paths}
def get(path):
 start=time.monotonic();row={'path':path}
 try:
  with urllib.request.urlopen('http://127.0.0.1:8930/'+path,timeout=15) as r:
   raw=r.read();row.update(status=r.status,headers=dict(r.headers),bytes=len(raw),hash_match=hashlib.sha256(raw).hexdigest()==expected[path])
 except Exception as error:row['error']=repr(error)
 row['seconds']=time.monotonic()-start;return row
report={'http_sequential':[get(path) for path in paths for _ in range(3)]}
with ThreadPoolExecutor(max_workers=12) as pool:report['http_concurrent']=list(pool.map(get,paths*5))
print('HTTP',sum('error' in x for x in report['http_sequential']+report['http_concurrent']),flush=True)
with sync_playwright() as p:
 exe=next((Path.home()/'AppData/Local/ms-playwright/chromium-1181').rglob('chrome.exe'))
 browser=p.chromium.launch(headless=True,executable_path=str(exe),args=['--log-net-log='+str(OUT/'chromium-netlog.json'),'--net-log-capture-mode=Default'])
 page=browser.new_page();report['request_failures']=[];page.on('requestfailed',lambda r:report['request_failures'].append({'url':r.url,'error':r.failure}))
 page.goto('http://127.0.0.1:8930/icon.svg')
 report['chromium_fetch']=page.evaluate('''async ({paths,expected})=>{const results=[];for(let round=0;round<5;round++){const batch=await Promise.all(paths.map(async path=>{const started=performance.now();try{const response=await fetch('/'+path);const bytes=await response.arrayBuffer();const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');return {path,round,status:response.status,bytes:bytes.byteLength,hash_match:hash===expected[path],seconds:(performance.now()-started)/1000};}catch(e){return {path,round,error:String(e)};}}));results.push(...batch);}return results;}''',{'paths':paths,'expected':expected})
 browser.close()
report['server_errors']=[x for x in log if 'exception' in x or 'server_exception' in x];(OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'http_requests':40,'browser_requests':len(report['chromium_fetch']),'browser_failures':report['request_failures'],'server_errors':report['server_errors']},indent=2),flush=True);server.shutdown()
