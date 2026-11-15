"""Actual optional-model UI check in a disposable synthetic demo."""
import re,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
out=Path('work/browser-model-acceptance-headed' if '--headed' in sys.argv else 'work/browser-model-acceptance');out.mkdir(exist_ok=True)
report={'status':'NOT_COMPLETED','errors':[]}
with sync_playwright() as p:
    exe=next((Path.home()/'AppData/Local/ms-playwright/chromium-1181').rglob('chrome.exe'))
    b=p.chromium.launch(headless='--headed' not in sys.argv,executable_path=str(exe));page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:report['errors'].append(str(e)))
    try:
        page.goto(next((arg for arg in sys.argv[1:] if arg.startswith('http')), 'http://127.0.0.1:8934/'));expect(page.locator('#runtime-status')).to_contain_text('ready on this device',timeout=60000);page.locator('#explore').click();page.locator('#workspace').wait_for(state='visible');expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready',timeout=30000)
        report['gpu']=page.evaluate('async()=>{if(!navigator.gpu)return {available:false};const a=await navigator.gpu.requestAdapter();return {available:!!a,features:a?[...a.features]:[]};}')
        if not report['gpu']['available']:
            page.locator('#workspace-nav [data-view="assistant"]').click();page.locator('.assistant-settings > summary').click();page.locator('#model-install').click();expect(page.locator('#model-load')).to_be_disabled(timeout=30000);expect(page.locator('#model-status')).to_contain_text('UNSUPPORTED');report['status']='BLOCKED_NO_WEBGPU_ADAPTER';report['model_status']=page.locator('#model-status').inner_text();report['load_disabled']=page.locator('#model-load').is_disabled();raise RuntimeError('WebGPU adapter unavailable under ordinary Chromium launch; UI blocks model download')
        link=page.locator('#workspace-nav [data-view="chat"]')
        print('NAV',page.locator('#workspace-nav [data-view]').evaluate_all('(xs)=>xs.map(x=>x.dataset.view)'),flush=True)
        if link.count()==0:link=page.locator('#workspace-nav [data-view="assistant"]')
        link.click();page.locator('.assistant-settings > summary').click();page.locator('#model-install').click();page.locator('#model-choice').select_option('Qwen2.5-0.5B-Instruct-q4f16_1-MLC');page.locator('#model-load').click()
        expect(page.locator('#model-status')).to_contain_text(re.compile('^READY|FAILED|UNSUPPORTED|ERROR|LOCAL_FALLBACK_AVAILABLE'),timeout=240000)
        report['model_status']=page.locator('#model-status').inner_text();report['benchmarks']=page.locator('#model-benchmark').inner_text()
        if not report['model_status'].startswith('READY'):raise RuntimeError(report['model_status'])
        page.locator('#question').fill('What does the local evidence say about exercise during a mission?');page.locator('#ask').click();page.wait_for_timeout(20000);report['assistant']=page.locator('#chat').inner_text();report['benchmarks']=page.locator('#model-benchmark').inner_text();report['status']='MODEL_READY_RESPONSE_REVIEW_REQUIRED'
    except Exception as error:report['failure']=str(error)
    finally:
        page.screenshot(path=str(out/'actual-state.png'),full_page=True);(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True);b.close()
