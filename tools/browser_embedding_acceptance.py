"""CPU MiniLM scientific embedding check; no clinical record writes."""
import re,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
out=Path('work/browser-embedding-acceptance');out.mkdir(exist_ok=True);report={'status':'NOT_COMPLETED','errors':[],'requests_failed':[]}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path=str(next((Path.home()/'AppData/Local/ms-playwright/chromium-1181').rglob('chrome.exe'))));page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('requestfailed',lambda r:report['requests_failed'].append({'url':r.url,'error':r.failure}))
    try:
        page.goto(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8934/');expect(page.locator('#runtime-status')).to_contain_text('ready on this device',timeout=60000);page.locator('#explore').click();page.locator('#workspace').wait_for(state='visible');expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready',timeout=30000);page.locator('#workspace-nav [data-view="assistant"]').click();page.locator('.assistant-settings > summary').click();page.locator('#embed-install').click();page.locator('#embed-load').click()
        expect(page.locator('#embedding-status')).to_contain_text(re.compile('^READY|LOCAL_FALLBACK_AVAILABLE'),timeout=240000)
        report['embedding_status']=page.locator('#embedding-status').inner_text();report['operation']=page.locator('#operation').inner_text();report['benchmarks']=page.locator('#model-benchmark').inner_text()
        if not report['embedding_status'].startswith('READY'):raise RuntimeError(report['operation'])
        page.locator('#workspace-nav .more-nav > summary').click();page.locator('#workspace-nav [data-view="knowledge"]').click();page.locator('#search-question').fill('exercise countermeasures during spaceflight');page.locator('#search').click();page.wait_for_timeout(2000);report['citations']=page.locator('#citations').inner_text();report['status']='INDEX_READY_RELEVANCE_NOT_VALIDATED'
    except Exception as error:report['failure']=str(error)
    finally:page.screenshot(path=str(out/'actual-state.png'),full_page=True);(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True);b.close()

if report["status"] in {"FAILED","NOT_COMPLETED"}:raise SystemExit(1)
