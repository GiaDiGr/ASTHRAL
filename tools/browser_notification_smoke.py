"""Verify navigation to a real deterministic event in a synthetic profile."""
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

parser=argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable(),args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(args.url,wait_until='domcontentloaded')
    page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
    page.get_by_role('button',name='Explore Synthetic Demo').click()
    page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)
    page.get_by_role('button',name='Load synthetic mission observations').click()
    page.get_by_text('Synthetic mission calculated and frozen cycle reproduced exactly.',exact=False).wait_for(timeout=90000)
    if page.locator('.anatomy-notifications').get_attribute('open') is None:
        page.locator('.anatomy-notifications summary').click()
    card=page.locator('.anatomy-notification').filter(has=page.get_by_role('button',name='View details')).first
    card.wait_for(timeout=30000)
    event_text=card.inner_text()
    page.context.set_offline(True)
    card.get_by_role('button',name='View details').click()
    page.locator('#history:not([hidden])').wait_for()
    focused=page.locator('#history-list article:focus')
    assert focused.count()==1 and focused.locator('details').get_attribute('open') is not None
    record=focused.inner_text()
    assert '"evidence_ids"' in record and '"urgency"' in record
    assert 'Acknowledged' not in event_text
    page.screenshot(path=str(args.output/'notification-source.png'))
    page.locator('#workspace-nav [data-view="dashboard"]').click()
    if page.locator('.anatomy-notifications').get_attribute('open') is None:
        page.locator('.anatomy-notifications summary').click()
    card=page.locator('.anatomy-notification').filter(has=page.get_by_role('button',name='Acknowledge')).first
    card.get_by_role('button',name='Acknowledge').click()
    page.get_by_text('Acknowledged · finding remains in history.').first.wait_for(timeout=30000)
    page.context.set_offline(False)
    assert not errors,errors
    (args.output/'report.json').write_text(json.dumps({'result':'PASS','event':event_text,'source_record':record,'details_and_ack_offline':True,'page_errors':errors},indent=2))
    print(json.dumps({'result':'PASS','event':event_text,'page_errors':errors},indent=2))
    browser.close()
