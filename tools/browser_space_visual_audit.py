"""Capture real rendered space-theme routes without private or clinical data."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

parser=argparse.ArgumentParser();parser.add_argument('url');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
report={'routes':[],'errors':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable(),args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    for width in (1440,390):
        context=browser.new_context(viewport={'width':width,'height':1000 if width==1440 else 844},reduced_motion='reduce')
        page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
        page.goto(args.url,wait_until='domcontentloaded');page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
        page.screenshot(path=str(args.output/f'login-{width}.png'))
        page.get_by_role('button',name='Explore Synthetic Demo').click();page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)
        for route in (['dashboard','mission-control','monitoring','clinical','assistant','prevention','space-radiation','history','settings'] if width==1440 else ['dashboard']):
            page.locator(f'#workspace-nav [data-view="{route}"]').click();page.wait_for_timeout(500)
            if route=='dashboard':page.get_by_text('3D external body map loaded',exact=False).wait_for(timeout=60000)
            if route=='mission-control':page.locator('.orbit-stage').wait_for(timeout=60000)
            info=page.evaluate("""() => ({background:getComputedStyle(document.documentElement).backgroundImage, bodyBackground:getComputedStyle(document.body).backgroundColor, overflow:document.documentElement.scrollWidth>innerWidth, active:document.querySelector('#workspace-nav [aria-current=page]')?.dataset.view})""")
            assert 'space-background.svg' in info['background'] and not info['overflow'],info
            page.screenshot(path=str(args.output/f'{route}-{width}.png'))
            report['routes'].append({'width':width,'route':route,**info})
        context.close()
    browser.close()
assert not report['errors'],report['errors']
report['result']='PASS';(args.output/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
