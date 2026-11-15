"""End-to-end synthetic mission journey across the existing local ASTHRAL modules."""
import argparse
import json
import re
import time
import uuid
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8952/')
parser.add_argument('--output', default='work/browser-mission-integration-20261115')
args = parser.parse_args()
output = Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=True)
report = {'status': 'FAILED', 'synthetic_data_only': True, 'clinical_validation': False,
          'page_errors': [], 'console_errors': [], 'request_failures': [], 'steps': []}
run_started = time.perf_counter()


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
        started = time.perf_counter()
        page.goto(args.url, timeout=30000)
        expect(page.locator('#runtime-status')).to_contain_text(re.compile('ready on this device'), timeout=90000)
        report['local_runtime_ready_seconds'] = round(time.perf_counter() - started, 3)
        page.get_by_role('button', name='Explore Synthetic Demo', exact=True).click()
        page.locator('#workspace').wait_for(state='visible', timeout=30000)
        expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready', timeout=30000)
        report['steps'].append('Temporary synthetic profile opened')

        page.locator('#dashboard').get_by_role('button', name='Load synthetic mission observations', exact=True).click()
        expect(page.locator('#operation')).to_contain_text('Synthetic mission calculated and frozen cycle reproduced exactly', timeout=30000)
        report['steps'].append('Seeded synthetic observations processed into a personal baseline, monitoring cycle and deterministic replay')
        capture(page, 'mission-overview.png')

        visit('monitoring')
        monitoring = page.locator('#monitoring')
        expect(monitoring).to_contain_text('Monitoring cycle')
        expect(monitoring).to_contain_text('Use personal research baseline')
        cycle = monitoring.get_by_role('button', name='Reproduce this monitoring cycle', exact=True).first
        cycle.click()
        expect(monitoring.locator('p[role="status"]').first).to_contain_text('Frozen cycle reproduced exactly')
        report['baseline_controls'] = monitoring.locator('label').filter(has_text='Use personal research baseline').count()
        if report['baseline_controls'] < 1:
            raise AssertionError('No personal baseline controls were rendered for the synthetic measurements')
        report['steps'].append('Baseline and frozen monitoring replay visible in the same profile')
        capture(page, 'monitoring-baseline.png')

        visit('prevention')
        prevention = page.locator('#prevention')
        prevention.get_by_role('button', name='Load synthetic prevention journal (temporary demo only)', exact=True).click()
        expect(page.locator('#operation')).to_contain_text('Five arbitrary synthetic prevention entries saved in temporary memory')
        expect(prevention.locator('.mission-journal article')).to_have_count(5)
        report['steps'].append('Synthetic exercise, hydration, meal note, sleep and legacy wellbeing entries loaded into the shared local journal')

        visit('exercise')
        exercise = page.locator('#exercise')
        exercise.get_by_role('button', name='Start this example', exact=True).first.click()
        exercise.get_by_label('Completed sets (self-reported)', exact=True).fill('1')
        exercise.get_by_label('Completed repetitions (self-reported)', exact=True).fill('2')
        exercise.get_by_role('button', name='Pause and save', exact=True).click()
        exercise.get_by_role('button', name='Resume session', exact=True).click()
        exercise.get_by_role('button', name='Complete and save session', exact=True).click()
        expect(exercise).to_contain_text('Session saved:')
        report['steps'].append('Manual exercise example recorded through start, pause, resume and completion in the same profile')

        visit('neuroguard')
        neuro = page.locator('#neuroguard')
        neuro.locator('input[aria-label="I consent to voluntarily record selected NeuroGuard sessions locally"]').check()
        kss = neuro.locator('.ng-section').filter(has_text='2 · Fatigue Monitor')
        kss.get_by_label('Karolinska Sleepiness Scale · level over the past 5 minutes', exact=True).select_option('5')
        kss.get_by_role('button', name='Save KSS', exact=True).click()
        expect(kss.locator('.ng-status').first).to_contain_text('Saved KSS 5/9')
        report['steps'].append('Voluntary KSS self-report stored in the shared prevention journal; clinical interpretation remains disabled')

        visit('space-radiation')
        radiation = page.locator('#space-radiation')
        radiation.get_by_role('button', name='Load synthetic timeline in this temporary demo', exact=True).click()
        expect(radiation).to_contain_text('Three synthetic values stored in temporary memory only')
        expect(radiation).to_contain_text('independent timeline annotation')
        report['steps'].append('Synthetic dose-rate software fixtures shown separately from NASA public event annotations')
        with page.expect_download() as radiation_download:
            radiation.get_by_role('button', name='Export local radiation records (plaintext JSON)', exact=True).click()
        radiation_file = output / 'synthetic-radiation-export.json'
        radiation_download.value.save_as(str(radiation_file))
        radiation_export = json.loads(radiation_file.read_text(encoding='utf-8'))
        if radiation_export.get('sensor_verified') is not False or len(radiation_export.get('records', [])) != 3:
            raise AssertionError('Synthetic radiation export did not preserve its explicit unverified state and three fixture records')
        report['exports'] = {'radiation_json': str(radiation_file), 'records': len(radiation_export['records']),
                             'sensor_verified': radiation_export['sensor_verified'], 'plaintext_sensitive_data': False}
        report['steps'].append('Synthetic radiation export downloaded as plaintext JSON with the unverified-source flag intact')

        visit('followup')
        followup = page.locator('#followup')
        expect(followup).to_contain_text('Follow-up due')
        expect(followup).to_contain_text('Review pending')
        report['followup_plans_visible'] = followup.locator('article').count()
        report['steps'].append('Engine-created synthetic follow-up remains visibly pending; no completed review or recovery was recorded')
        with page.expect_download() as mission_download:
            followup.get_by_role('button', name='Export synthetic mission summary (aggregate JSON)', exact=True).click()
        mission_file = output / 'synthetic-mission-summary.json'
        mission_download.value.save_as(str(mission_file))
        mission_summary = json.loads(mission_file.read_text(encoding='utf-8'))
        summary_text = mission_file.read_text(encoding='utf-8')
        counts = mission_summary.get('counts', {})
        if (mission_summary.get('format') != 'ASTHRAL-SYNTHETIC-MISSION-SUMMARY-1'
                or mission_summary.get('synthetic_data_only') is not True
                or mission_summary.get('contains_personal_records') is not False
                or counts.get('synthetic_measurements', 0) < 5
                or counts.get('synthetic_baselines', 0) < 1
                or counts.get('synthetic_monitoring_cycles', 0) < 1
                or counts.get('synthetic_followup_plans', 0) < 1
                or any(token in summary_text for token in ['profile-', 'mission-device-', 'baseline-web-native', '49.5', '44.0'])):
            raise AssertionError('Mission summary export failed its synthetic-only, aggregate-only, or provenance contract')
        report['mission_summary_export'] = {'file': str(mission_file), 'counts': counts,
            'contains_personal_records': mission_summary['contains_personal_records'],
            'clinical_summary': mission_summary['clinical_summary'], 'raw_values_or_identifiers_present': False}
        report['steps'].append('Aggregate mission summary exported with synthetic-only counts; identifiers and clinical values were excluded')

        visit('mission-context')
        context = page.locator('#mission-context')
        context.get_by_label(re.compile('Gravity context')).select_option('MICROGRAVITY')
        context.get_by_label(re.compile('Mission phase')).select_option('IN_MISSION')
        context.get_by_label(re.compile('Context effective time')).fill('2026-11-16T12:00')
        context.get_by_role('button', name='Append mission context', exact=True).click()
        expect(monitoring.locator('p[role="status"]').first).to_contain_text('Local record committed', timeout=20000)
        report['steps'].append('Explicit microgravity and mission-phase context appended with an effective timestamp')

        visit('knowledge')
        knowledge = page.locator('#knowledge')
        knowledge.get_by_label('Research question', exact=True).fill('spaceflight sleep fatigue evidence')
        knowledge.get_by_role('button', name='Search local references', exact=True).click()
        expect(knowledge.locator('#citations')).not_to_be_empty()
        expect(knowledge.locator('#citations')).to_contain_text('SHA-256', timeout=15000)
        report['steps'].append('Local source retrieval returned source identifiers and content hashes without clinical generation')
        capture(page, 'mission-evidence.png')

        visit('space-weather')
        weather = page.locator('#space-weather')
        expect(weather).to_contain_text('Fixed historical official fixture')
        expect(weather).to_contain_text('not current')
        report['steps'].append('Historical public space-weather context displayed as non-current and not personal exposure')

        export_page = browser.new_page()
        export_page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
        export_page.on('console', lambda message: report['console_errors'].append(message.text) if message.type == 'error' else None)
        export_page.on('requestfailed', lambda request: report['request_failures'].append({'url': request.url, 'failure': request.failure}))
        export_page.goto(args.url, timeout=30000)
        expect(export_page.locator('#runtime-status')).to_contain_text(re.compile('ready on this device'), timeout=90000)
        export_page.get_by_role('button', name='Create an account', exact=True).click()
        test_email = f"synthetic-export-{uuid.uuid4().hex}@example.invalid"
        export_page.locator('#profile-label').fill(test_email)
        export_page.locator('#create-password').fill('ASTHRAL-Synthetic-Export-2026!')
        export_page.locator('#create-form').get_by_role('button', name='Create account', exact=True).click()
        expect(export_page.locator('#workspace')).to_be_visible(timeout=30000)
        followup_link = export_page.locator('#workspace-nav [data-view="followup"]')
        if not followup_link.is_visible():
            export_page.locator('#workspace-nav .more-nav > summary').click()
        followup_link.click()
        expect(export_page.locator('#followup').get_by_role('button', name='Export synthetic mission summary (aggregate JSON)', exact=True)).to_be_disabled()
        report['mission_summary_plaintext_export_disabled_for_persistent_profile'] = True
        history_link = export_page.locator('#workspace-nav [data-view="history"]')
        if not history_link.is_visible():
            export_page.locator('#workspace-nav .more-nav > summary').click()
        history_link.click()
        with export_page.expect_download() as backup_download:
            export_page.get_by_role('button', name='Download encrypted backup', exact=True).click()
        backup_file = output / 'encrypted-empty-profile-backup.json'
        backup_download.value.save_as(str(backup_file))
        backup_text = backup_file.read_text(encoding='utf-8')
        backup = json.loads(backup_text)
        if (backup.get('format') != 'ASTHRAL-ENCRYPTED-SQLITE-1' or backup.get('iterations') != 600000
                or backup.get('revision', 0) < 1 or not backup.get('ciphertext') or not backup.get('iv')
                or test_email in backup_text or 'ASTHRAL-Synthetic-Export-2026!' in backup_text):
            raise AssertionError('Persistent profile backup did not meet the encrypted-export contract')
        report['encrypted_profile_backup'] = {
            'file': str(backup_file), 'format': backup['format'], 'revision': backup['revision'],
            'pbkdf2_sha256_iterations': backup['iterations'], 'ciphertext_present': True,
            'test_email_or_passphrase_in_plaintext': False, 'mission_records_included': False,
        }
        report['steps'].append('Persistent plaintext summary export stayed disabled; an empty synthetic-test profile exported only as an encrypted backup in a separate ephemeral browser context')
        export_page.close()

        if report['page_errors'] or report['console_errors'] or report['request_failures']:
            raise RuntimeError('Browser errors or failed network requests were recorded')
        page.set_viewport_size({'width': 390, 'height': 844})
        capture(page, 'mission-mobile.png')
        report['status'] = 'SYNTHETIC_CROSS_MODULE_MISSION_FLOW_FOLLOWUP_AND_ENCRYPTED_EXPORT_PASSED'
    except Exception as error:
        report['failure'] = str(error)
        capture(page, 'failure.png')
    finally:
        report['total_runtime_seconds'] = round(time.perf_counter() - run_started, 3)
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2), flush=True)
        browser.close()

if report['status'] == 'FAILED':
    raise SystemExit(1)
