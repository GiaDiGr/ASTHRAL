"""Real Chromium acceptance smoke test. A failure is recorded, never reclassified as success."""
import argparse,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8919/');parser.add_argument('--output',default='work/browser-acceptance-final');args=parser.parse_args()
out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
report={'status':'FAILED','page_errors':[],'console_errors':[],'request_failures':[],'checks':[]}
def capture(**options):
 try:page.screenshot(timeout=5000,**options)
 except Exception as error:report.setdefault('capture_errors',[]).append(str(error))
with sync_playwright() as p:
    matches=list((Path.home()/'AppData/Local/ms-playwright').glob('chromium-*/chrome-win/chrome.exe'))
    b=p.chromium.launch(headless=True,**({'executable_path':str(sorted(matches)[-1])} if matches else {}))
    page=b.new_page(viewport={'width':1440,'height':1000})
    page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
    page.on('console',lambda m:report['console_errors'].append(m.text) if m.type=='error' else None)
    page.on('requestfailed',lambda r:report['request_failures'].append({'url':r.url,'failure':r.failure}))
    try:
        page.goto(args.url,timeout=30000);capture(path=str(out/'login-desktop.png'),full_page=True);report['checks'].append('Login rendered')
        expect(page.locator('#runtime-status')).to_contain_text(re.compile('ready on this device|Local runtime failed|Local worker failed'),timeout=90000)
        report['runtime_status']=page.locator('#runtime-status').inner_text()
        if 'ready on this device' not in report['runtime_status']:raise RuntimeError(report['runtime_status'])
        page.get_by_role('button',name='Explore Synthetic Demo',exact=True).click();page.locator('#workspace').wait_for(state='visible',timeout=30000);expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready',timeout=30000)
        capture(path=str(out/'dashboard-desktop.png'),full_page=True);report['checks'].append('Demo entered')
        def visit(view):
            link=page.locator(f'#workspace-nav [data-view="{view}"]')
            if not link.is_visible():page.locator('#workspace-nav .more-nav > summary').click()
            link.click();page.locator('#'+view).wait_for(state='visible')
        visit('exercise');exercise=page.locator('#exercise');exercise.get_by_role('button',name='Start this example',exact=True).first.click()
        exercise.get_by_label('Completed sets (self-reported)',exact=True).fill('1');exercise.get_by_label('Completed repetitions (self-reported)',exact=True).fill('2')
        exercise.get_by_role('button',name='Pause and save',exact=True).click();exercise.get_by_role('button',name='Resume session',exact=True).click();exercise.get_by_role('button',name='Complete and save session',exact=True).click()
        exercise.get_by_text('Session saved:',exact=False).wait_for();capture(path=str(out/'exercise-desktop.png'),full_page=True);report['checks'].append('Exercise start/count/pause/resume/complete')
        visit('nutrition');nutrition=page.locator('#nutrition')
        nutrition.get_by_label('Search USDA foods',exact=True).fill('2262074');nutrition.get_by_label('USDA Foundation Foods item',exact=True).select_option('2262074');nutrition.get_by_label('Portion amount (g)',exact=True).fill('10')
        expect(nutrition.get_by_text('DECLARED_1008: not supplied for this method',exact=True)).to_be_visible();expect(nutrition.get_by_text('ATWATER_GENERAL_2047: 64.50 kcal estimated for the selected portion',exact=True)).to_be_visible();expect(nutrition.get_by_text('ATWATER_SPECIFIC_2048: 60.30 kcal estimated for the selected portion',exact=True)).to_be_visible()
        nutrition.get_by_role('button',name='Save meal estimate',exact=True).click();expect(nutrition.get_by_role('heading',name='Record a meal',exact=True).locator('..').get_by_role('status')).to_have_text('Choose an energy reference method before saving.');nutrition.get_by_label('USDA energy reference method',exact=True).select_option('ATWATER_SPECIFIC_2048');expect(nutrition.get_by_text('Selected energy method: ATWATER_SPECIFIC_2048. Distinct reference methods may differ; no value is inferred from other nutrients.',exact=True)).to_be_visible();capture(path=str(out/'nutrition-methods-desktop.png'),full_page=True);report['checks'].append('USDA original named energy alternatives and unknown legacy value displayed')
        nutrition.get_by_label('USDA energy reference method',exact=True).select_option('DECLARED_1008');nutrition.get_by_label('Portion amount (g)',exact=True).fill('100');nutrition.get_by_label('Search USDA foods',exact=True).fill('potato');nutrition.get_by_label('USDA Foundation Foods item',exact=True).select_option(index=0);nutrition.get_by_role('button',name='Save meal estimate',exact=True).click();nutrition.get_by_text('Saved USDA composition estimate',exact=False).wait_for()
        nutrition.get_by_label('Water / fluid amount (mL)',exact=True).fill('250');nutrition.get_by_role('button',name='Save fluid amount',exact=True).click();capture(path=str(out/'nutrition-desktop.png'),full_page=True);report['checks'].append('USDA search/portion/save/hydration')
        for view in ['sleep-recovery','wellbeing','space-weather','space-radiation','clinical','history']:
            visit(view);capture(path=str(out/(view+'-desktop.png')),full_page=True);report['checks'].append('Route opened: '+view)
        report['status']='PARTIAL_WORKFLOW_PASSED_NOT_FULL_ACCEPTANCE'

    except Exception as error:
        report['failure']=str(error);capture(path=str(out/'failure-desktop.png'),full_page=True)
    finally:
        page.set_viewport_size({'width':390,'height':844});capture(path=str(out/'current-state-mobile.png'),full_page=True)
        (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True);b.close()
if report['status']=='FAILED':raise SystemExit(1)
