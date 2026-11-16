"""Install the preview's offline core, then verify representative wave scenes offline."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

parser=argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
report={'url':args.url,'errors':[]}

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable(),args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    context=browser.new_context(viewport={'width':1440,'height':1000})
    page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.goto(args.url,wait_until='domcontentloaded')
    page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
    page.get_by_role('button',name='Explore Synthetic Demo').click()
    page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)
    page.locator('#workspace-nav [data-view="settings"]').click()
    page.locator('#install-offline').click()
    page.wait_for_function("() => document.querySelector('#offline-status')?.textContent.startsWith('Offline resources verified:')",timeout=180000)
    report['install_status']=page.locator('#offline-status').inner_text()

    manifest=page.evaluate("""async()=>{const r=await fetch('./assets.json',{cache:'no-store'});if(!r.ok)throw Error('asset manifest unavailable');const m=await r.json();return m.files.filter(x=>/^cosmic-scenes\\/scene-\\d+\\.svg$/.test(x.path)).length}""")
    assert manifest==24,manifest
    report['offline_manifest_scenes']=manifest
    context.set_offline(True)
    page.reload(wait_until='domcontentloaded',timeout=90000)
    page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
    assert page.evaluate('Boolean(navigator.serviceWorker.controller)'),'Offline service worker did not control the reloaded page.'
    page.get_by_role('button',name='Explore Synthetic Demo').click()
    page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)
    route_ids=page.locator('#workspace-nav [data-view]').evaluate_all('(items)=>items.map(x=>x.dataset.view)')
    last=route_ids[-1];last_scene=f'{len(route_ids)-1:02}'
    page.locator(f'#workspace-nav [data-view="{last}"]').click();page.wait_for_timeout(1000)
    state=page.evaluate("""async()=>{
      const layer=[...document.querySelectorAll('.cosmic-scene-layer')].find(x=>Number(getComputedStyle(x).opacity)>.9);
      const scene=(layer?.style.backgroundImage.match(/scene-(\\d+)\\.svg/)||[])[1]||null;
      const files=await Promise.all(['00','05','10','15','20','23'].map(async n=>{const r=await fetch(`./cosmic-scenes/scene-${n}.svg`);return {scene:n,status:r.status,type:r.headers.get('content-type'),svg:(await r.text()).startsWith('<svg')}}));
      return {controller:Boolean(navigator.serviceWorker.controller),scene,active:document.querySelector('#workspace-nav [aria-current=page]')?.dataset.view,files};
    }""")
    assert state['controller'] and state['active']==last and state['scene']==last_scene,state
    assert all(x['status']==200 and x['svg'] for x in state['files']),state
    report['offline_state']=state
    page.screenshot(path=str(args.output/'last-cosmic-scene-offline.png'))
    assert not report['errors'],report['errors']
    browser.close()

report['result']='PASS'
(args.output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
