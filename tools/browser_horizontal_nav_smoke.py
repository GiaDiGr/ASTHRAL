"""Browser checks of ASTHRAL's single scrollable workspace navigation."""
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=browser_executable(), args=['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    for width in (1440, 390):
        context = browser.new_context(viewport={'width': width, 'height': 900}, has_touch=width == 390, is_mobile=width == 390, reduced_motion='reduce')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.url, wait_until='domcontentloaded')
        page.get_by_text('Reference Python engine ready on this device', exact=False).wait_for(timeout=180000)
        page.get_by_role('button', name='Explore Synthetic Demo').click()
        page.get_by_text('Temporary synthetic demo ready.', exact=False).wait_for(timeout=60000)
        nav = page.locator('#workspace-nav')
        assert page.locator('.more-nav').count() == 0
        routes = nav.locator('a[data-view]').evaluate_all('(links) => links.map(x => ({id:x.dataset.view,visible:getComputedStyle(x).display!=="none"}))')
        assert len(routes) >= 18 and all(r['visible'] for r in routes), routes
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        box = nav.bounding_box()
        page.mouse.move(box['x'] + 40, box['y'] + 20)
        before = nav.evaluate('(n) => n.scrollLeft')
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(200)
        after = nav.evaluate('(n) => n.scrollLeft')
        assert after > before, (before, after)
        nav.evaluate('(n) => n.scrollLeft = 0')
        if width == 390:
            cdp=context.new_cdp_session(page)
            x,y=box['x']+box['width']-25,box['y']+box['height']/2
            cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
            cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-130,'y':y,'id':1}]})
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            page.wait_for_timeout(250)
            assert nav.evaluate('(n) => n.scrollLeft') > 0
            assert page.locator('#anatomy').is_visible(), 'Swiping activated a route'
        else:
            link=nav.locator('[data-view="monitoring"]')
            link.focus()
            page.keyboard.press('Enter')
            assert page.locator('#monitoring').is_visible()
        nav.locator('[data-view="settings"]').click()
        assert page.locator('#settings').is_visible()
        assert nav.locator('[data-view="settings"]').get_attribute('aria-current') == 'page'
        nav.locator('[data-view="dashboard"]').click()
        assert page.locator('#anatomy').is_visible()
        page.screenshot(path=str(args.output / f'home-{width}.png'))
        assert not errors, errors
        results.append({'width':width,'routes':len(routes),'mouse_wheel_scroll':True,'touch_swipe':width==390,'keyboard_activation':width==1440,'active_route':True,'page_errors':errors})
        context.close()
    browser.close()
(args.output / 'report.json').write_text(json.dumps({'result':'PASS','checks':results},indent=2))
print(json.dumps({'result':'PASS','checks':results},indent=2))
