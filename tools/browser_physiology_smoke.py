"""Verify synthetic slider transitions do not create health-history records."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

out=Path('work/physiology-smoke-wip1');out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable(),args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(os.environ.get('ASTHRAL_SMOKE_URL','http://127.0.0.1:8995/'),wait_until='domcontentloaded')
    page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
    page.get_by_role('button',name='Explore Synthetic Demo').click()
    page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)
    page.locator('#workspace-nav [data-view="monitoring"]').click()
    root=page.locator('#physiology-simulator');root.wait_for()
    before=root.locator('canvas').evaluate('(c)=>c.toDataURL()')
    hr=page.get_by_label('Heart rate simulation');hr.fill('130')
    assert '130 bpm' in root.inner_text() and 'SIMULATION WARNING' in root.inner_text()
    page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').click()
    assert 'illustrative rule training-fixture-1' in page.locator('.floating-assistant-panel').inner_text()
    page.get_by_label('Oxygen saturation simulation').fill('89')
    assert page.get_by_role('button',name='ASTHRAL assistant · 2 simulation notices').is_visible()
    assert '21.27 kPa' in root.inner_text() and '29.60 kPa' in root.inner_text()
    after=root.locator('canvas').evaluate('(c)=>c.toDataURL()');assert before!=after
    page.get_by_role('button',name='Reset simulation').click()
    assert '72 bpm' in root.inner_text() and page.get_by_role('button',name='ASTHRAL assistant',exact=True).is_visible()
    page.locator('#workspace-nav [data-view="history"]').click()
    assert 'No local observations or evaluations saved.' in page.locator('#history-list').inner_text()
    page.locator('#workspace-nav [data-view="monitoring"]').click();root.screenshot(path=str(out/'monitor.png'))
    assert not errors,errors
    (out/'report.json').write_text(json.dumps({'result':'PASS','hr_slider':True,'waveform_changed':True,'reset':True,'history_unchanged':True,'page_errors':errors},indent=2))
    print('PASS: slider, waveform, reset and empty history')
    browser.close()
