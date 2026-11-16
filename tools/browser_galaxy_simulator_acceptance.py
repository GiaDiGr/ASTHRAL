"""Focused Chromium acceptance for the addendum's galactic and simulation behavior."""
import argparse
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

parser=argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
report={'url':args.url,'scenes':[],'simulation':{},'errors':[]}

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable(),args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.goto(args.url,wait_until='domcontentloaded')
    page.get_by_text('Reference Python engine ready on this device',exact=False).wait_for(timeout=180000)
    page.screenshot(path=str(args.output/'login-desktop.png'))
    page.get_by_role('button',name='Explore Synthetic Demo').click()
    page.get_by_text('Temporary synthetic demo ready.',exact=False).wait_for(timeout=60000)

    nav=page.locator('#workspace-nav [data-view]')
    route_ids=nav.evaluate_all('(items)=>items.map(x=>x.dataset.view)')
    labels=[item.inner_text().strip() for item in nav.all()]
    assert not any('human anatomy' in label.lower() for label in labels),labels
    assert len(route_ids)>=21, f'Expected enough tabs to show repeated color waves, found {len(route_ids)}'
    selected=[('blue-start',route_ids[0]),('violet-peak-a',route_ids[5]),('blue-return-a',route_ids[10]),
      ('violet-peak-b',route_ids[15]),('blue-return-b',route_ids[20]),('wave-end',route_ids[-1])]
    seen=[];crossfade_verified=False
    for position,(name,route) in enumerate(selected):
        page.locator(f'#workspace-nav [data-view="{route}"]').click()
        if position==1:
            page.wait_for_timeout(450)
            opacities=page.locator('.cosmic-scene-layer').evaluate_all('(items)=>items.map(x=>Number(getComputedStyle(x).opacity))')
            crossfade_verified=sum(.05<value<.95 for value in opacities)>=2
            assert crossfade_verified,opacities
            page.wait_for_timeout(600)
        else:page.wait_for_timeout(950)
        state=page.evaluate("""() => {
          const layer=[...document.querySelectorAll('.cosmic-scene-layer')].find(item=>Number(getComputedStyle(item).opacity)>.9);
          return {active:document.querySelector('#workspace-nav [aria-current=page]')?.dataset.view,
            image:layer?getComputedStyle(layer).backgroundImage:'',opacity:layer?getComputedStyle(layer).opacity:'0',
            dataScene:layer?.dataset.scene||null,
            scene:(layer?.style.backgroundImage.match(/scene-(\\d+)\\.svg/)||[])[1]||null,
            overflow:document.documentElement.scrollWidth>innerWidth};
        }""")
        assert state['active']==route and state['image'] and state['scene'] is not None and not state['overflow'],state
        assert int(state['scene'])==int(state['dataScene']),state
        state['position']=name;seen.append(state);report['scenes'].append(state)
        page.screenshot(path=str(args.output/f'galaxy-{name}-desktop.png'))
    assert len({item['scene'] for item in seen})==len(seen),seen
    assert [int(item['scene']) for item in seen]==[0,5,10,15,20,len(route_ids)-1],seen
    wave_colors=page.evaluate("""async()=>{
      const scenes=await Promise.all(Array.from({length:24},async(_,index)=>{
        const number=String(index).padStart(2,'0');
        const svg=await (await fetch(`./cosmic-scenes/scene-${number}.svg`)).text();
        const match=svg.match(/radialGradient id=\"a\"><stop stop-color=\"(#[0-9a-f]{6})\"/i);
        if(!match)throw Error(`Missing scene palette ${number}`);
        return match[1].toLowerCase();
      }));
      return scenes;
    }""")
    assert wave_colors[0]==wave_colors[10]==wave_colors[20],wave_colors
    assert wave_colors[5]==wave_colors[15],wave_colors
    assert wave_colors[0]!=wave_colors[5],wave_colors
    assert all(wave_colors[a]!=wave_colors[b] for a,b in ((1,2),(2,3),(3,4),(6,7),(7,8),(8,9))),wave_colors
    report['wave']={'period_tabs':10,'sample_scenes':[0,5,10,15,20,23],'palette_verified':True,'all_24_assets_checked':True}
    report['crossfade_verified']=crossfade_verified
    assert page.locator('#anatomy-ecg').count()==1
    page.locator('#workspace-nav [data-view="dashboard"]').click()
    page.get_by_text('3D external body map loaded',exact=False).wait_for(timeout=60000)
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    page.wait_for_timeout(80)
    frame=page.locator('#anatomy-view .anatomy-frame')
    frame_y=frame.bounding_box()['y'];ecg_y=page.locator('#anatomy-ecg').bounding_box()['y'];vitals_y=page.locator('.anatomy-vitals').bounding_box()['y']
    assert abs(ecg_y-frame_y)<45 and abs(vitals_y-frame_y)<45,{'body_y':frame_y,'ecg_y':ecg_y,'vitals_y':vitals_y}
    assert page.locator('#anatomy .page-intro h1').inner_text()=='Overview'
    frame.scroll_into_view_if_needed();page.screenshot(path=str(args.output/'overview-body-desktop.png'))

    page.locator('#workspace-nav [data-view="monitoring"]').click()
    root=page.locator('#physiology-simulator');root.wait_for()
    mode_button=root.get_by_role('button',name='Enter Synthetic Test Mode')
    assert mode_button.is_visible() and root.locator('.phys-simulator-grid input[type=range]').count()==8
    assert not root.locator('.phys-simulator-grid input[type=range]').first.is_visible()
    assert not page.locator('.synthetic-mode-indicator').is_visible()
    assert not page.locator('#anatomy-ecg canvas').is_visible()
    mode_button.click()
    assert root.locator('.phys-simulator-grid input[type=range]').first.is_visible()
    assert page.locator('.synthetic-mode-indicator').is_visible()
    assert 'SYNTHETIC TEST MODE — NOT LIVE MEDICAL DATA' in page.locator('.synthetic-mode-indicator').inner_text()

    cabin=page.get_by_label('Cabin O₂ Concentration (%)')
    suit=page.get_by_label('Spacesuit O₂ Concentration (%)')
    cabin_total=page.get_by_label('Cabin total pressure (kPa)')
    suit_total=page.get_by_label('Spacesuit total pressure (kPa)')
    assert '21.27 kPa' in root.inner_text() and '29.60 kPa' in root.inner_text()
    assert 'CO₂ concentration / partial pressure: not measured or configured.' in root.inner_text()
    assert 'Oxygen reserve / supply status: not instrumented.' in root.inner_text()
    assert 'illustrative' in root.inner_text().lower() and 'not nasa operational limits' in root.inner_text().lower()
    initial_suit=suit.input_value()
    cabin.evaluate("(el)=>{el.value='9';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert '9.12 kPa' in root.inner_text() and 'SIMULATION WARNING' in root.inner_text()
    assert page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').is_visible()
    cabin.evaluate("(el)=>{el.value='8';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').click()
    assert '8.10 kPa' in page.locator('.floating-assistant-panel').inner_text()
    assert page.get_by_role('button',name='View details').is_visible()
    page.get_by_role('button',name='View details').click()
    assert page.locator('#workspace-nav [aria-current="page"]').get_attribute('data-view')=='monitoring'
    assert root.get_by_role('button',name='Exit Synthetic Test Mode').is_visible()

    cabin.evaluate("(el)=>{el.value='50';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert '50.65 kPa' in root.inner_text()
    assert page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').is_visible()
    page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').click()
    assert '50.65 kPa' in page.locator('.floating-assistant-panel').inner_text() and 'above 40 kPa' in page.locator('.floating-assistant-panel').inner_text()
    page.locator('.floating-assistant>button').click()
    cabin_total.fill('');cabin_total.dispatch_event('input')
    assert 'insufficient information' in root.inner_text().lower()
    assert 'not entered' in root.inner_text().lower()
    cabin_total.fill('101.3')
    cabin.evaluate("(el)=>{el.value='21';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert '21.27 kPa' in root.inner_text()
    assert suit.input_value()==initial_suit and '29.60 kPa' in root.inner_text()

    suit.evaluate("(el)=>{el.value='20';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert '5.92 kPa' in root.inner_text()
    assert 'Cabin O₂ concentration: 21.0%' in root.inner_text()
    assert 'SpO₂' in root.inner_text() and 'Oxygen saturation' in root.inner_text()
    assert page.get_by_label('Oxygen saturation simulation').input_value()=='98'
    assert page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').is_visible()
    suit_total.fill('140')
    assert '28.00 kPa' in root.inner_text()
    assert page.get_by_role('button',name='ASTHRAL assistant',exact=True).is_visible()
    suit.evaluate("(el)=>{el.value='100';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert '140.00 kPa' in root.inner_text()
    page.get_by_role('button',name='ASTHRAL assistant · 1 simulation notice').click()
    assert 'above 40 kPa' in page.locator('.floating-assistant-panel').inner_text()
    page.locator('.floating-assistant>button').click()

    page.get_by_label('Heart rate simulation').evaluate("(el)=>{el.value='130';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert '130 bpm' in root.inner_text()
    page.locator('#workspace-nav [data-view="dashboard"]').click()
    ecg=page.locator('#anatomy-ecg canvas')
    assert ecg.is_visible(),page.locator('#anatomy-ecg').inner_text()
    assert 'SYNTHETIC TEST MODE' in page.locator('#anatomy-ecg').inner_text()
    image_before=ecg.evaluate('(canvas)=>canvas.toDataURL()')
    page.locator('#workspace-nav [data-view="monitoring"]').click()
    page.get_by_label('Heart rate simulation').evaluate("(el)=>{el.value='150';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    page.locator('#workspace-nav [data-view="dashboard"]').click()
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    page.locator('#anatomy-view .anatomy-frame').scroll_into_view_if_needed()
    image_after=ecg.evaluate('(canvas)=>canvas.toDataURL()')
    assert image_before!=image_after,'Heart rate did not update the overview ECG illustration.'
    page.screenshot(path=str(args.output/'overview-synthetic-ecg.png'))

    page.locator('#workspace-nav [data-view="monitoring"]').click()
    page.get_by_role('button',name='Reset simulation').click()
    assert '72 bpm' in root.inner_text() and '21.27 kPa' in root.inner_text() and '29.60 kPa' in root.inner_text()
    assert page.get_by_role('button',name='ASTHRAL assistant',exact=True).is_visible()
    page.get_by_role('button',name='Exit Synthetic Test Mode').click()
    assert root.locator('.phys-simulator-grid input[type=range]').first.is_hidden()
    assert page.locator('.synthetic-mode-indicator').is_hidden()
    page.locator('#workspace-nav [data-view="dashboard"]').click()
    assert page.locator('#anatomy-ecg canvas').is_hidden()
    page.locator('#workspace-nav [data-view="history"]').click()
    assert 'No local observations or evaluations saved.' in page.locator('#history-list').inner_text()
    report['simulation']={'sliders_hidden_by_default':True,'mode_indicator_persistent':True,'cabin_and_spacesuit_independent':True,
       'partial_pressure_and_notice_updates':True,'missing_data_stays_insufficient':True,'ecg_rate_driven_and_synthetic_only':True,
       'reset_and_history_unchanged':True,'test_mode_exit':True}
    assert not report['errors'],report['errors']
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#workspace-nav [data-view="dashboard"]').click();page.wait_for_timeout(250)
    mobile_overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not mobile_overflow,'Overview overflows the mobile viewport.'
    page.screenshot(path=str(args.output/'overview-mobile.png'))
    browser.close()

report['result']='PASS'
(args.output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
