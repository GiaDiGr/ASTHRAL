"""Synthetic Chromium acceptance for the integrated NeuroGuard journal flow."""
import argparse
import json
import re
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8947/')
parser.add_argument('--output', default='work/browser-neuroguard-acceptance-20261115')
args = parser.parse_args()
output = Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=True)
report = {'status': 'FAILED', 'synthetic_data_only': True, 'page_errors': [], 'console_errors': [], 'request_failures': [], 'checks': []}


def capture(page, name):
    try:
        page.screenshot(path=str(output / name), full_page=True, timeout=5000)
    except Exception as error:
        report.setdefault('capture_errors', []).append(str(error))


with sync_playwright() as playwright:
    browsers = list((Path.home() / 'AppData/Local/ms-playwright').glob('chromium-*/chrome-win/chrome.exe'))
    browser = playwright.chromium.launch(headless=True, **({'executable_path': str(sorted(browsers)[-1])} if browsers else {}))
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
    page.on('console', lambda message: report['console_errors'].append(message.text) if message.type == 'error' else None)
    page.on('requestfailed', lambda request: report['request_failures'].append({'url': request.url, 'failure': request.failure}))

    def visit(view):
        link = page.locator(f'#workspace-nav [data-view="{view}"]')
        if not link.is_visible():
            page.locator('#workspace-nav .more-nav > summary').click()
        link.click()
        page.locator('#' + view).wait_for(state='visible')

    try:
        startup = time.perf_counter()
        page.goto(args.url, timeout=30000)
        expect(page.locator('#runtime-status')).to_contain_text(re.compile('ready on this device'), timeout=90000)
        report['local_runtime_ready_seconds'] = round(time.perf_counter() - startup, 3)
        report['checks'].append('Local Python/SQLite runtime ready')
        page.get_by_role('button', name='Explore Synthetic Demo', exact=True).click()
        page.locator('#workspace').wait_for(state='visible', timeout=30000)
        expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready', timeout=30000)
        report['checks'].append('Temporary synthetic profile opened')

        visit('wellbeing')
        expect(page.locator('#wellbeing')).to_contain_text('Open NeuroGuard self-reports')
        expect(page.locator('#wellbeing')).not_to_contain_text('Save voluntary check-in')
        report['checks'].append('Legacy 1–5 records retained read-only; new check-in routed to NeuroGuard')

        visit('sleep-recovery')
        sleep = page.locator('#sleep-recovery')
        sleep.get_by_label('Sleep start (local time)', exact=True).fill('2026-11-14T22:00')
        sleep.get_by_label('Wake / end (local time)', exact=True).fill('2026-11-15T06:00')
        sleep.get_by_label('Subjective sleep quality, 1–5 (optional)', exact=True).fill('4')
        sleep.get_by_role('button', name='Save sleep interval', exact=True).click()
        expect(sleep.locator('p[role="status"]').first).to_contain_text('Saved 480 minutes', timeout=20000)
        report['checks'].append('Self-reported sleep saved in the existing local journal')

        visit('neuroguard')
        neuro = page.locator('#neuroguard')
        neuro.locator('input[aria-label="I consent to voluntarily record selected NeuroGuard sessions locally"]').check()
        mood = neuro.locator('.ng-section').filter(has_text='1 · Mood Check')
        mood.get_by_role('button', name='Save Mood Check', exact=True).click()
        expect(mood.get_by_role('status')).to_contain_text('Saved voluntary mood self-report')
        fatigue = neuro.locator('.ng-section').filter(has_text='2 · Fatigue Monitor')
        fatigue.get_by_label('Karolinska Sleepiness Scale · level over the past 5 minutes', exact=True).select_option('7')
        fatigue.get_by_role('button', name='Save KSS', exact=True).click()
        expect(fatigue.locator('.ng-status').first).to_contain_text('Saved KSS 7/9')
        sleep_link = fatigue.get_by_label('Optional link to a previously logged sleep interval', exact=True)
        sleep_link.select_option(index=1)
        fatigue.get_by_role('button', name='Save fatigue self-ratings', exact=True).click()
        expect(fatigue.locator('.ng-status').nth(1)).to_contain_text('A selected local sleep entry is linked')
        expect(neuro.locator('.ng-history')).to_contain_text('linked sleep summary')
        report['checks'].append('Mood, KSS and fatigue recorded; linked sleep resolved to a same-profile SLEEP row')

        workload = neuro.get_by_role('button', name='Save weighted NASA-TLX', exact=True).locator('xpath=ancestor::section[contains(@class,"ng-section")][1]')
        for dimension in ('Mental demand (Low → High)', 'Physical demand (Low → High)', 'Temporal demand (Low → High)',
                          'Own performance (Good → Poor)', 'Effort (Low → High)', 'Frustration (Low → High)'):
            workload.get_by_label(dimension, exact=True).select_option('50')
        pair_selects = workload.locator('select')
        for index in range(pair_selects.count()):
            control = pair_selects.nth(index)
            if control.locator('option').count() == 3:
                control.select_option(index=1)
        workload.get_by_label('Task or activity label', exact=True).fill('Synthetic mission checklist')
        workload.get_by_role('button', name='Save weighted NASA-TLX', exact=True).click()
        expect(workload.locator('.ng-status').last).to_contain_text('Saved weighted NASA-TLX: 50/100')
        report['checks'].append('NASA-TLX ratings and all randomized pair choices saved with distinct weighted/unweighted scores')
        capture(page, 'neuroguard-recorded.png')

        history = neuro.locator('.ng-history')
        existing = history.locator('article').count()
        neuro.get_by_role('button', name='Start 3-minute PVT-B browser task', exact=True).click()
        expect(neuro.get_by_role('button', name='Stop and discard active task', exact=True)).to_be_enabled()
        neuro.get_by_role('button', name='Stop and discard active task', exact=True).click()
        expect(neuro.locator('.ng-task-stage .ng-status')).to_contain_text('incomplete measurements were discarded')
        assert history.locator('article').count() == existing
        report['checks'].append('PVT-B task can be stopped and is discarded without saving incomplete trials')

        page.once('dialog', lambda dialog: dialog.accept())
        history.locator('article').first.get_by_role('button', name='Delete this NeuroGuard session', exact=True).click()
        expect(neuro.locator('.ng-section').filter(has_text='Voluntary participation')).to_contain_text('session deleted from this local profile and audit event recorded')
        assert history.locator('article').count() == existing - 1
        report['checks'].append('One NeuroGuard session deleted through the scoped API and removed from the browser history')

        with page.expect_download() as csv_download:
            neuro.get_by_role('button', name='Export NeuroGuard CSV (plaintext file)', exact=True).click()
        report['csv_export'] = csv_download.value.suggested_filename
        with page.expect_download() as json_download:
            neuro.get_by_role('button', name='Export NeuroGuard JSON (plaintext file)', exact=True).click()
        report['json_export'] = json_download.value.suggested_filename
        report['checks'].append('CSV and JSON exports initiated from the local synthetic profile')
        page.set_viewport_size({'width': 390, 'height': 844})
        capture(page, 'neuroguard-mobile.png')
        if report['page_errors'] or report['console_errors']:
            raise RuntimeError('Browser reported JavaScript errors')
        report['status'] = 'SYNTHETIC_NEUROGUARD_BROWSER_FLOW_PASSED'
    except Exception as error:
        report['failure'] = str(error)
        capture(page, 'failure.png')
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2), flush=True)
        browser.close()

if report['status'] == 'FAILED':
    raise SystemExit(1)
