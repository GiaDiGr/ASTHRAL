"""Real Vosk recognition of packaged synthetic fixtures; no record writes."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('work/browser-voice-acceptance');out.mkdir(exist_ok=True);report={'status':'NOT_COMPLETED','errors':[]}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path=str(next((Path.home()/'AppData/Local/ms-playwright/chromium-1181').rglob('chrome.exe'))));page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:report['errors'].append(str(e)))
    def visit(view):
        link=page.locator(f'#workspace-nav [data-view="{view}"]')
        if not link.is_visible():page.locator('#workspace-nav .more-nav > summary').click()
        link.click();page.locator('#'+view).wait_for(state='visible')
    try:
        page.goto('http://127.0.0.1:8934/');page.wait_for_function("document.getElementById('runtime-status').textContent.includes('ready on this device')",timeout=60000);page.locator('#explore').click();page.wait_for_function("document.getElementById('operation').textContent.startsWith('Temporary synthetic demo ready')",timeout=30000)
        visit('settings');page.locator('#install-offline').click();page.wait_for_function("document.getElementById('offline-status').textContent.startsWith('Offline resources verified:') || document.getElementById('offline-status').textContent.startsWith('Offline installation failed:')",timeout=120000);report['public_offline_assets']=page.locator('#offline-status').text_content();assert report['public_offline_assets'].startswith('Offline resources verified:');page.reload();page.wait_for_function("document.getElementById('runtime-status').textContent.includes('ready on this device')",timeout=60000);page.locator('#explore').click();page.wait_for_function("document.getElementById('operation').textContent.startsWith('Temporary synthetic demo ready')",timeout=30000);visit('settings');page.locator('#advanced-settings > summary').click();page.get_by_label('Show Developer View',exact=True).check();visit('voice');page.locator('#voice-inspect').click();page.locator('#voice-install').click();page.wait_for_function("/READY|LOCAL_FALLBACK_AVAILABLE/.test(document.getElementById('voice-status').textContent)",timeout=90000)
        report['voice_status']=page.locator('#voice-status').inner_text()
        if not report['voice_status'].startswith('READY'):raise RuntimeError(report['voice_status'])
        page.get_by_role('button',name='Run synthetic offline speech regression',exact=True).click();page.wait_for_function("document.getElementById('operation').textContent.includes('Synthetic speech regression finished')",timeout=120000)
        report['results']=json.loads(page.locator('#speech-regression-report').text_content());report['status']='RECOGNITION_EXECUTED_REVIEW_MISMATCHES';assert all(r['record_saved'] is False for r in report['results'])
    except Exception as error:report['failure']=str(error)
    finally:page.screenshot(path=str(out/'actual-state.png'),full_page=True);(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True);b.close()
