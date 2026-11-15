"""Real Chromium acceptance smoke test. A failure is recorded, never reclassified as success."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8919/');parser.add_argument('--output',default='work/browser-acceptance-final');args=parser.parse_args()
out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
report={'status':'FAILED','page_errors':[],'console_errors':[],'request_failures':[],'checks':[]}
with sync_playwright() as p:
    matches=list((Path.home()/'AppData/Local/ms-playwright').glob('chromium-*/chrome-win/chrome.exe'))
    b=p.chromium.launch(headless=True,**({'executable_path':str(sorted(matches)[-1])} if matches else {}))
    page=b.new_page(viewport={'width':1440,'height':1000})
    page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
    page.on('console',lambda m:report['console_errors'].append(m.text) if m.type=='error' else None)
    page.on('requestfailed',lambda r:report['request_failures'].append({'url':r.url,'failure':r.failure}))
    try:
        page.goto(args.url,timeout=30000);page.screenshot(path=str(out/'login-desktop.png'),full_page=True);report['checks'].append('Login rendered')
        page.wait_for_function("/ready on this device|Local runtime failed|Local worker failed/.test(document.getElementById('runtime-status').textContent)",timeout=90000,polling=1000)
        report['runtime_status']=page.locator('#runtime-status').inner_text()
        if 'ready on this device' not in report['runtime_status']:raise RuntimeError(report['runtime_status'])
        page.get_by_role('button',name='Explore Synthetic Demo',exact=True).click();page.locator('#workspace').wait_for(state='visible',timeout=30000)
        page.screenshot(path=str(out/'dashboard-desktop.png'),full_page=True);report['checks'].append('Demo entered')
        def visit(view):
            link=page.locator(f'#workspace-nav [data-view="{view}"]')
            if not link.is_visible():page.locator('#workspace-nav .more-nav > summary').click()
            link.click();page.locator('#'+view).wait_for(state='visible')
        visit('exercise');exercise=page.locator('#exercise');exercise.get_by_role('button',name='Start this example',exact=True).first.click()
        exercise.get_by_label('Completed sets (self-reported)',exact=True).fill('1');exercise.get_by_label('Completed repetitions (self-reported)',exact=True).fill('2')
        exercise.get_by_role('button',name='Pause and save',exact=True).click();exercise.get_by_role('button',name='Resume session',exact=True).click();exercise.get_by_role('button',name='Complete and save session',exact=True).click()
        exercise.get_by_text('Session saved:',exact=False).wait_for();page.screenshot(path=str(out/'exercise-desktop.png'),full_page=True);report['checks'].append('Exercise start/count/pause/resume/complete')
        visit('nutrition');nutrition=page.locator('#nutrition');nutrition.get_by_label('Search USDA foods',exact=True).fill('potato');nutrition.get_by_label('USDA Foundation Foods item',exact=True).select_option(index=0);nutrition.get_by_role('button',name='Save meal estimate',exact=True).click();nutrition.get_by_text('Saved USDA composition estimate',exact=False).wait_for()
        nutrition.get_by_label('Water / fluid amount (mL)',exact=True).fill('250');nutrition.get_by_role('button',name='Save fluid amount',exact=True).click();page.screenshot(path=str(out/'nutrition-desktop.png'),full_page=True);report['checks'].append('USDA search/portion/save/hydration')
        for view in ['sleep-recovery','wellbeing','space-weather','space-radiation','clinical','history']:
            visit(view);page.screenshot(path=str(out/(view+'-desktop.png')),full_page=True);report['checks'].append('Route opened: '+view)
        report['status']='PARTIAL_WORKFLOW_PASSED_NOT_FULL_ACCEPTANCE'

    except Exception as error:
        report['failure']=str(error);page.screenshot(path=str(out/'failure-desktop.png'),full_page=True)
    finally:
        page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'current-state-mobile.png'),full_page=True)
        (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True);b.close()
if report['status']=='FAILED':raise SystemExit(1)
