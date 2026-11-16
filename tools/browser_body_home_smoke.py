"""Exercise the body home with the existing synthetic monitoring cycle."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_anatomy_acceptance import browser_executable

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=browser_executable(), args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(args.url, wait_until='domcontentloaded')
    page.get_by_text('Reference Python engine ready on this device', exact=False).wait_for(timeout=180000)
    page.get_by_role('button', name='Explore Synthetic Demo').click()
    page.locator('#anatomy:not([hidden])').wait_for(timeout=60000)
    page.get_by_text('Temporary synthetic demo ready.', exact=False).wait_for(timeout=60000)
    page.get_by_text('3D external body map loaded', exact=False).wait_for(timeout=60000)
    assert page.locator('.brand img').evaluate('(img) => img.complete && img.naturalWidth > 0')
    card = page.locator('.anatomy-vital-card').filter(has=page.get_by_role('heading', name='Heart rate', exact=True))
    assert 'No data available' in card.inner_text()
    page.locator('#workspace-nav [data-view="monitoring"]').click()
    page.get_by_label('Reviewed synthetic device policy').select_option(value='mission-device-2')
    page.get_by_label('Synthetic measurement value').fill('7')
    page.get_by_label('Measurement timestamp (UTC)').fill('2026-07-25T12:00')
    page.get_by_role('button', name='Save synthetic measurement').click()
    page.get_by_text('Local record committed. Treatment execution remains blocked.').wait_for(timeout=60000)
    page.locator('#workspace-nav [data-view="dashboard"]').click()
    page.wait_for_function("() => document.querySelector('.anatomy-vitals')?.innerText.includes('sleep.duration:')", timeout=60000)
    sleep = page.locator('.anatomy-vital-card').filter(has=page.get_by_role('heading', name='Sleep duration', exact=True)).inner_text()
    assert 'Synthetic' in sleep and 'quality:' in sleep and '7 h' in sleep
    page.locator('.anatomy-notifications summary').click()
    notices = page.locator('.anatomy-notifications').inner_text()
    page.locator('#anatomy').screenshot(path=str(args.output / 'body-home-synthetic.png'))
    page.get_by_label('Select an anatomical region').select_option('head')
    assert page.get_by_text('Well-being and cognitive monitoring').is_visible()
    page.get_by_label('Select an anatomical region').select_option('chest')
    assert page.get_by_text('Cardiovascular monitoring', exact=True).is_visible()
    assert not errors, errors
    (args.output / 'report.json').write_text(json.dumps({'result':'PASS','sleep_card':sleep,'notifications':notices,'page_errors':errors,'synthetic_only':True}, indent=2))
    print(json.dumps({'result':'PASS','sleep_card':sleep,'page_errors':errors}, indent=2))
    browser.close()
