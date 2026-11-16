"""Check that starting a synthetic exercise reveals the running timer."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

out=Path('work/exercise-timer-scroll');out.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable(),args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    for width in (1440,390):
        context=browser.new_context(viewport={'width':width,'height':900 if width==1440 else 844},reduced_motion='reduce',is_mobile=width==390,has_touch=width==390)
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(os.environ.get('ASTHRAL_SMOKE_URL','http://127.0.0.1:8998/'),wait_until='domcontentloaded')
        page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
        page.get_by_role('button',name='Explore Synthetic Demo').click()
        page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)
        page.locator('#workspace-nav [data-view="exercise"]').click()
        page.get_by_role('button',name='Start this example').first.click()
        timer=page.locator('#exercise-session-timer');timer.wait_for(timeout=60000)
        page.wait_for_function("() => document.activeElement?.id === 'exercise-session-timer'")
        rect=timer.bounding_box();assert rect and rect['y']>=0 and rect['y']+rect['height']<=page.viewport_size['height'],rect
        initial=timer.inner_text();page.wait_for_timeout(2100);later=timer.inner_text();assert initial!=later,(initial,later)
        assert not errors,errors
        page.screenshot(path=str(out/f'timer-{width}.png'))
        results.append({'width':width,'timer_visible':True,'timer_focus':True,'timer_updates':True,'page_errors':errors})
        context.close()
    browser.close()
(out/'report.json').write_text(json.dumps({'result':'PASS','checks':results},indent=2))
print(json.dumps({'result':'PASS','checks':results},indent=2))
