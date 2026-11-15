"""Real public DONKI sync/notice acknowledgement under the app CSP; no health writes."""
import argparse,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8942/');args=parser.parse_args();out=Path('work/browser-donki-acceptance');out.mkdir(exist_ok=True);report={'status':'FAILED','errors':[],'requests_failed':[]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=str(next((Path.home()/'AppData/Local/ms-playwright/chromium-1181').rglob('chrome.exe'))));page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('requestfailed',lambda r:report['requests_failed'].append({'url':r.url,'failure':r.failure}))
 def visit():
  link=page.locator('#workspace-nav [data-view="space-weather"]')
  if not link.is_visible():page.locator('#workspace-nav .more-nav > summary').click()
  link.click()
 try:
  page.goto(args.url);expect(page.locator('#runtime-status')).to_contain_text('ready on this device',timeout=60000);page.locator('#explore').click();expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready',timeout=30000);visit();section=page.locator('#space-weather');sync=section.get_by_role('button',name='Synchronize NASA DONKI (optional online request)',exact=True);sync.click();expect(sync).to_be_enabled(timeout=60000);report['sync_status']=section.locator('[role=status]').first.inner_text();buttons=section.get_by_role('button',name='Acknowledge this notice',exact=True);report['unacknowledged_before']=buttons.count()
  if not buttons.count():raise RuntimeError('No live notice available; acknowledgement not tested. '+report['sync_status'])
  buttons.first.click();expect(section.get_by_text('Notice acknowledgement saved on this device.',exact=True)).to_be_visible();report['unacknowledged_after']=buttons.count();assert report['unacknowledged_after']==report['unacknowledged_before']-1;section.get_by_text('Acknowledgement history',exact=True).click();page.screenshot(path=str(out/'notice-acknowledged.png'),full_page=True)
  page.reload();expect(page.locator('#runtime-status')).to_contain_text('ready on this device',timeout=60000);page.locator('#explore').click();expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready',timeout=30000);visit();expect(page.locator('#space-weather').get_by_text(re.compile('Acknowledged locally at '))).to_be_visible();report['acknowledgement_survives_reload']=True;report['status']='PUBLIC_EVENT_SYNC_ACK_RELOAD_VERIFIED';page.screenshot(path=str(out/'cached-after-reload.png'),full_page=True)
 except Exception as error:report['failure']=str(error)
 finally:(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True);b.close()

if report["status"]=="FAILED":raise SystemExit(1)
