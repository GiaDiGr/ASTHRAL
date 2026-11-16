"""Real Chromium acceptance for the current static ASTHRAL build.

Uses only the application's synthetic demo and public orbital endpoint. It never enters
personal or clinical data. Example:
  python tools/browser_final_mission_control_acceptance.py --root <build> --output work/mission-control-acceptance
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import secrets
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial
from threading import Thread
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web-local'))
from radlab_proxy import fetch_radlab


class StaticHandler(SimpleHTTPRequestHandler):
    # HTTP/1.1 with explicit content lengths avoids Chromium's observed resets
    # while fetching the large local Pyodide WASM runtime over loopback.
    protocol_version = 'HTTP/1.1'
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.wasm': 'application/wasm', '.webp': 'image/webp', '.mjs': 'text/javascript'}

    def handle(self):
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            # A browser teardown may interrupt a keep-alive read after all
            # required resources were delivered; it is recorded by Playwright
            # if it affected an application request.
            pass

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        source = Path(self.directory) / '_headers'
        if source.is_file():
            for line in source.read_text(encoding='utf-8').splitlines():
                if line.lstrip().startswith('Content-Security-Policy:'):
                    self.send_header('Content-Security-Policy', line.split(':', 1)[1].strip())
                elif line.lstrip().startswith(('X-Content-Type-Options:', 'Referrer-Policy:', 'Permissions-Policy:')):
                    name, _, value = line.strip().partition(':')
                    self.send_header(name, value.strip())
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path != '/api/radlab':
            return super().do_GET()
        try:
            _, payload = fetch_radlab(urlsplit(self.path).query)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('X-ASTHRAL-RadLab-Payload', 'RAW')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, ConnectionError) as error:
            body = json.dumps({'error': str(error), 'provider': 'NASA_OSDR_RADLAB'}).encode('utf-8')
            self.send_response(502)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            # Chromium may close a keep-alive connection after a large WASM
            # asset has loaded. This is a client disconnect, not a failed app
            # response, and the browser acceptance records required failures.
            pass


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--chrome', type=Path)
    parser.add_argument('--port', type=int, default=8978)
    parser.add_argument('--timeout-ms', type=int, default=180000)
    parser.add_argument('--simulate-celestrak-status', type=int, choices=range(400, 600), metavar='HTTP_STATUS',
                        help='return a marked test HTTP error for CelesTrak instead of making another provider request')
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if not (root / 'index.html').is_file():
        raise SystemExit(f'Build directory has no index.html: {root}')

    # Pass the build root to each handler instance. SimpleHTTPRequestHandler's
    # constructor otherwise overwrites a class-level ``directory`` with cwd,
    # which would accidentally serve the source repository instead of the build.
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(StaticHandler, directory=str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{args.port}/'
    report = {
        'build_root': str(root), 'base_url': base, 'synthetic_data_only': True,
        'screenshots': {}, 'checks': {}, 'errors': [], 'failed_requests': [], 'expected_offline_failures': [],
    }
    offline_state = {'value': False}
    browser = None
    try:
        async with async_playwright() as playwright:
            launch = {'headless': True, 'args': ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--disable-dev-shm-usage']}
            if args.chrome:
                launch['executable_path'] = str(args.chrome.resolve())
            browser = await playwright.chromium.launch(**launch)
            context = await browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1, reduced_motion='reduce')
            page = await context.new_page()
            page.set_default_timeout(args.timeout_ms)
            if args.simulate_celestrak_status is not None:
                await page.route(
                    re.compile(r'^https://celestrak\.org/NORAD/elements/gp\.php\?CATNR=25544&FORMAT=JSON$'),
                    lambda route: route.fulfill(status=args.simulate_celestrak_status, content_type='application/json', body='{"fixture":"SYNTHETIC_EXTERNAL_FAILURE_TEST"}'),
                )
                report['provider_test_fixtures'] = {'celestrak_status': args.simulate_celestrak_status, 'synthetic_fixture': True}
            page.on('pageerror', lambda error: report['errors'].append({'kind': 'pageerror', 'message': str(error)}))
            def record_console_error(message):
                if message.type != 'error':
                    return
                location = message.location or {}
                if offline_state['value'] and '/api/radlab?' in str(location.get('url', '')):
                    # The UI deliberately retries a historical query after offline
                    # installation; its network failure is an expected offline path.
                    return
                if 'celestrak.org/NORAD/elements/gp.php?CATNR=25544' in str(location.get('url', '')):
                    # Record this optional public source separately. HTTP failures
                    # must still be reflected by the unavailable/cached UI state.
                    report.setdefault('optional_orbit_source_errors', []).append({'message': message.text, 'location': location})
                    return
                report['errors'].append({'kind': 'console', 'message': message.text, 'location': location})
            page.on('console', record_console_error)
            def record_http_error(response):
                if response.status < 400:
                    return
                item = {'status': response.status, 'url': response.url}
                if 'celestrak.org/NORAD/elements/gp.php?CATNR=25544' in response.url:
                    report.setdefault('optional_orbit_http_failures', []).append(item)
                else:
                    report.setdefault('http_errors', []).append(item)
            page.on('response', record_http_error)
            page.on('requestfailed', lambda request: report['expected_offline_failures'].append({'url': request.url, 'failure': request.failure}) if '/api/radlab?' in request.url and offline_state['value'] else report['failed_requests'].append({'url': request.url, 'failure': request.failure}) if 'celestrak.org' not in request.url else report.setdefault('optional_orbit_request_failures', []).append({'url': request.url, 'failure': request.failure}))

            t0 = time.perf_counter()
            response = await page.goto(base, wait_until='domcontentloaded')
            if response is None or response.status != 200:
                raise AssertionError(f'App entry point did not return HTTP 200: {response.status if response else None}')
            report['initial_dom'] = await page.evaluate("""() => ({url:location.href,title:document.title,readyState:document.readyState,bodyText:document.body?.innerText?.slice(0,1600),explore:(()=>{const e=document.querySelector('#explore');if(!e)return null;const s=getComputedStyle(e),r=e.getBoundingClientRect();return {exists:true,hidden:e.hidden,disabled:e.disabled,display:s.display,visibility:s.visibility,opacity:s.opacity,width:r.width,height:r.height,text:e.innerText}})(),scripts:[...document.scripts].map(x=>({src:x.src,type:x.type}))})""")
            await page.screenshot(path=str(output / 'initial-state.png'), full_page=True)
            report['screenshots']['initial_state'] = str(output / 'initial-state.png')
            await page.locator('#explore').wait_for(state='visible')
            await page.get_by_text('Reference Python engine ready on this device', exact=False).wait_for(timeout=args.timeout_ms)
            report['measurements'] = {'engine_ready_s': round(time.perf_counter() - t0, 3)}
            entries = await page.evaluate("performance.getEntriesByType('resource').map(x=>({name:x.name,transferSize:x.transferSize,decodedBodySize:x.decodedBodySize,duration:x.duration}))")
            report['measurements']['initial_transfer_bytes_observed'] = sum(int(item.get('transferSize') or 0) for item in entries)
            report['measurements']['initial_loaded_resources'] = len(entries)

            # Use a throwaway local account with synthetic content. The email
            # and password are generated only in this isolated browser context
            # and are never printed or persisted in the acceptance report.
            test_email = f"mission-control-{time.time_ns()}@example.invalid"
            test_password = secrets.token_urlsafe(24)
            await page.locator('#create-account-toggle').click()
            await page.locator('#create-form').wait_for(state='visible')
            await page.locator('#profile-label').fill(test_email)
            await page.locator('#create-password').fill(test_password)
            await page.locator('#create-form button.primary-action').click()
            await page.locator('#workspace').wait_for(state='visible')
            await page.locator('#scope').filter(has_text='Encrypted synthetic local profile').wait_for()
            report['checks']['synthetic_encrypted_profile'] = {'created': True, 'credentials_logged': False, 'health_records': 'none; EVA software scenario only'}
            orbit_mount_started = time.perf_counter()
            await page.locator('[data-view="mission-control"]').click()
            await page.locator('#mission-control').wait_for(state='visible')
            await page.locator('.eva-monitoring').wait_for(state='visible')
            await page.locator('.orbit-console').wait_for(state='visible')
            await page.locator('.orbit-globe-canvas').wait_for(state='visible', timeout=30000)
            stage_message = await page.locator('.orbit-stage-notice').inner_text()
            await page.locator('.orbit-stage-notice').get_by_text('Interactive Earth renderer ready', exact=False).wait_for(timeout=30000)
            report['measurements']['mission_control_mount_s'] = round(time.perf_counter() - orbit_mount_started, 3)
            webgl_info = await page.locator('.orbit-globe-canvas').evaluate("canvas=>({width:canvas.width,height:canvas.height,rect:{width:canvas.getBoundingClientRect().width,height:canvas.getBoundingClientRect().height},webgl2:!!canvas.getContext('webgl2'),hidden:canvas.hidden})")
            report['checks']['three_dimensional_earth'] = {'stage_message': stage_message, **webgl_info}
            if webgl_info['hidden'] or not webgl_info['webgl2'] or webgl_info['rect']['width'] < 300 or webgl_info['rect']['height'] < 250:
                raise AssertionError(f'Three-dimensional Earth did not initialize: {webgl_info}; {stage_message}')
            await page.locator('.nasa-source-registry summary').click()
            source_registry_text = await page.locator('.nasa-source-list').inner_text()
            if not all(value in source_registry_text for value in ('NASA_OSDR_RADLAB', 'NASA_OSDR_BIODATA', 'NASA_OSDR_EDA', 'NOT CONNECTED TO CLINICAL EVALUATION', 'EVALUATED_NOT_INTEGRATED')):
                raise AssertionError(f'NASA data-source registry omitted provenance or non-integration boundaries: {source_registry_text}')
            report['checks']['nasa_data_source_registry'] = {'source_ids': ['NASA_OSDR_RADLAB', 'NASA_CCMC_DONKI', 'NASA_OSDR_BIODATA', 'NASA_OSDR_EDA'], 'osdr_biodata_clinical_use': False, 'eda_integrated': False}
            await page.get_by_role('button', name='Load verified archive example').click()
            await page.get_by_text('NASA RadLab returned', exact=False).wait_for(timeout=60000)
            radlab_snapshot = await page.evaluate("JSON.parse(localStorage.getItem('asthral.radlab.historical.v1'))")
            radlab_stats = await page.locator('.radlab-stats').inner_text()
            radlab_context = await page.locator('#eva-radlab-context').inner_text()
            radlab_marker = await page.locator('.orbit-legend-radlab').inner_text()
            radlab_plot_points = await page.locator('.radlab-chart svg circle[data-observation-id]').count()
            radlab_geo_points = await page.locator('.radlab-map svg circle[data-observation-index]').count()
            report['checks']['live_nasa_radlab'] = {
                'provider': radlab_snapshot.get('provider'), 'classification': radlab_snapshot.get('classification'),
                'returned_records': len(radlab_snapshot.get('observations', [])), 'stats': radlab_stats,
                'time_series_points': radlab_plot_points, 'geospatial_points': radlab_geo_points,
                'globe_legend': radlab_marker, 'eva_context': radlab_context,
                'dose_or_alert_inference': False,
            }
            if radlab_snapshot.get('provider') != 'NASA_OSDR_RADLAB' or radlab_snapshot.get('classification') != 'HISTORICAL_PUBLIC_ENVIRONMENTAL_OBSERVATIONS':
                raise AssertionError(f'RadLab response was not labeled as historical public data: {radlab_snapshot}')
            if not radlab_snapshot.get('observations') or radlab_plot_points < 1 or radlab_geo_points < 1:
                raise AssertionError(f'NASA RadLab data did not render in the plots: {report["checks"]["live_nasa_radlab"]}')
            if 'individual dose' not in radlab_context.lower() or 'does not enter the eva assessment' not in radlab_context.lower() or not radlab_marker.endswith(str(radlab_geo_points)):
                raise AssertionError(f'RadLab context or globe marker count is not visible/coherent: {radlab_context}; {radlab_marker}')
            async with page.expect_download() as json_download:
                await page.get_by_role('button', name='Export JSON').click()
            json_file = await json_download.value
            radlab_json_path = output / 'radlab-export.json'
            await json_file.save_as(radlab_json_path)
            radlab_export = json.loads(radlab_json_path.read_text(encoding='utf-8'))
            async with page.expect_download() as csv_download:
                await page.get_by_role('button', name='Export CSV').click()
            csv_file = await csv_download.value
            radlab_csv_path = output / 'radlab-export.csv'
            await csv_file.save_as(radlab_csv_path)
            radlab_csv_header = radlab_csv_path.read_text(encoding='utf-8').splitlines()[0]
            if radlab_export.get('provider') != 'NASA_OSDR_RADLAB' or not radlab_csv_header.startswith('"source","classification","observed_at_utc"'):
                raise AssertionError('RadLab exports did not retain the source and time provenance contract.')
            report['checks']['radlab_exports'] = {
                'json_filename': json_file.suggested_filename, 'json_provider': radlab_export.get('provider'),
                'csv_filename': csv_file.suggested_filename, 'csv_header': radlab_csv_header,
            }
            await page.screenshot(path=str(output / 'mission-control-historical-radlab.png'), full_page=True, animations='disabled')
            report['screenshots']['historical_radlab'] = str(output / 'mission-control-historical-radlab.png')

            # The only offline RadLab path is a visibly identified historical cache.
            await page.evaluate("""() => {const key='asthral.radlab.historical.v1';const value=JSON.parse(localStorage.getItem(key));value.retrieved_at_utc=new Date(Date.now()-48*3600*1000).toISOString();localStorage.setItem(key,JSON.stringify(value));}""")
            offline_state['value'] = True
            await context.set_offline(True)
            await page.get_by_role('button', name='Load historical observations').click()
            await page.get_by_text('stale cached historical NASA RadLab observations', exact=False).wait_for(timeout=15000)
            report['checks']['offline_radlab_cache'] = {'stale_label_visible': True, 'records_retained': len(radlab_snapshot.get('observations', []))}
            await context.set_offline(False)
            offline_state['value'] = False

            await page.locator('#mission-power-mode').select_option('LOW_POWER')
            await page.get_by_text('LOW POWER · 12 fps globe cap', exact=False).wait_for()
            await page.locator('#mission-power-mode').select_option('CRITICAL')
            await page.get_by_text('CRITICAL · 1 fps globe refresh', exact=False).wait_for()
            if not await page.get_by_role('button', name='Play timeline').is_disabled():
                raise AssertionError('Critical power profile did not suspend optional orbital playback.')
            await page.locator('#mission-power-mode').select_option('FULL')
            report['checks']['resource_profiles'] = {'low_power_applied': True, 'critical_applied': True, 'critical_playback_disabled': True, 'full_restored': True}

            report['checks']['eva_card_styles'] = await page.locator('.eva-card').first.evaluate("element=>({background:getComputedStyle(element).backgroundColor,labelColor:getComputedStyle(element.querySelector('.eva-card-label')).color,valueColor:getComputedStyle(element.querySelector('.eva-card-value')).color})")
            badge = page.locator('.orbit-source-badge')
            orbit_source_badge = await badge.inner_text()
            orbit_notice = await page.locator('.orbit-stage-notice').inner_text()
            orbit_source_unavailable = bool(report.get('optional_orbit_http_failures') or report.get('optional_orbit_source_errors') or report.get('optional_orbit_request_failures'))
            if orbit_source_unavailable:
                if orbit_source_badge != 'ISS ELEMENTS UNAVAILABLE' or 'ISS tracking is unavailable' not in orbit_notice:
                    raise AssertionError(f'Unavailable public GP source was not represented as unavailable: {orbit_source_badge}; {orbit_notice}')
            elif orbit_source_badge not in ('CELESTRAK · FETCHED', 'OFFLINE · CACHED ELEMENTS', 'STALE ORBIT ELEMENTS'):
                raise AssertionError(f'ISS orbital source has no explicit source state: {orbit_source_badge}; {orbit_notice}')
            report['checks']['iss_data_availability'] = {
                'badge': orbit_source_badge,
                'state': 'UNAVAILABLE_EXTERNAL_SOURCE' if orbit_source_unavailable else 'PUBLIC_ELEMENTS_OR_CACHED_ESTIMATE',
                'estimate_is_direct_telemetry': False,
                'provider_http_failures': report.get('optional_orbit_http_failures', []),
            }
            await page.locator('[aria-label="Spacecraft tracking mode"]').select_option('SIMULATED')
            await badge.get_by_text('SYNTHETIC ORBIT', exact=True).wait_for()
            position_time = await page.locator('#orbit-utc').inner_text()
            if not position_time.endswith('Z'):
                raise AssertionError(f'Orbit time is not displayed in UTC: {position_time}')
            report['checks']['synthetic_orbit'] = {'badge': await badge.inner_text(), 'position_utc': position_time,
                'latitude': await page.locator('#orbit-lat').inner_text(), 'longitude': await page.locator('#orbit-lon').inner_text(),
                'altitude': await page.locator('#orbit-alt').inner_text()}

            await page.screenshot(path=str(output / 'mission-control-desktop.png'), full_page=True, animations='disabled')
            report['screenshots']['desktop'] = str(output / 'mission-control-desktop.png')

            start = page.get_by_role('button', name='Start EVA')
            await start.click()
            await page.locator('.eva-card').count()
            if await page.locator('.eva-card').count() != 4:
                raise AssertionError('EVA view did not render four monitoring cards.')
            await page.locator('.orbit-time-readout').get_by_text('synchronized EVA scenario time', exact=False).wait_for()
            if not await page.locator('input[aria-label="Orbit calculation time offset in minutes"]').is_disabled():
                raise AssertionError('Orbit timeline is not locked to the running EVA scenario clock.')
            await page.get_by_role('button', name='Pause EVA').click()
            await page.get_by_role('button', name='Resume EVA').wait_for(state='visible')
            scenario_clock_paused = await page.locator('.eva-card').nth(3).inner_text()
            await page.wait_for_timeout(1300)
            scenario_clock_after = await page.locator('.eva-card').nth(3).inner_text()
            if scenario_clock_paused.split('Scenario elapsed')[1].split('·')[0].strip() != scenario_clock_after.split('Scenario elapsed')[1].split('·')[0].strip():
                raise AssertionError('EVA scenario clock advanced while paused.')
            await page.get_by_role('button', name='Resume EVA').click()
            await page.get_by_role('button', name='Trigger training alert').click()
            await page.get_by_text('Return to airlock — simulated mission advisory', exact=True).wait_for()
            await page.get_by_role('button', name='Acknowledge advisory').click()
            if 'Acknowledged in simulation' not in await page.locator('.eva-advisory').inner_text():
                raise AssertionError('EVA advisory acknowledgement was not rendered.')
            await page.get_by_role('button', name='End EVA').click()
            await page.locator('.eva-log-panel [role="status"]').get_by_text(
                'Synthetic EVA report saved in the encrypted local profile.', exact=True,
            ).wait_for(timeout=15000)
            report_block = page.locator('.eva-report')
            await report_block.wait_for(state='visible')
            report_text = await report_block.inner_text()
            required_report_labels = ['EVA Medical Handover Report', 'SIMULATION', 'scenario time', 'synthetic', 'DONKI', 'Not clinically, operationally or flight validated']
            report['checks']['completed_eva'] = {
                'cards': await page.locator('.eva-card').count(), 'advisory_acknowledged': True,
                'report_saved': True, 'report_labels_present': {label: label.lower() in report_text.lower() for label in required_report_labels},
            }
            if not all(report['checks']['completed_eva']['report_labels_present'].values()):
                raise AssertionError('Handover report omitted required provenance or limitation text.')

            await page.locator('[data-view="history"]').click()
            eva_history = page.locator('#history-list article').filter(has_text='EVA ·')
            await eva_history.first.wait_for(state='visible')
            history = await page.locator('#history-list').inner_text()
            eva_history_rows = await eva_history.all_inner_texts()
            matching_history = next((row for row in eva_history_rows if 'critical' in row.lower() and 'simulated' in row.lower()), None)
            if not matching_history:
                raise AssertionError(f'Completed synthetic EVA was not present in profile history: {eva_history_rows}')
            encrypted_rows = await page.evaluate("""() => new Promise((resolve, reject) => { const request=indexedDB.open('asthral-encrypted-profiles',1); request.onerror=()=>reject(request.error); request.onsuccess=()=>{const db=request.result; const tx=db.transaction('profiles','readonly'); const get=tx.objectStore('profiles').getAll(); get.onsuccess=()=>{const rows=get.result.map(row=>({revision:row.revision,encrypted:typeof row.ciphertext==='string'&&row.ciphertext.length>0,iv:typeof row.iv==='string'&&row.iv.length>0,iterations:row.iterations,email_box_encrypted:typeof row.email_box?.ciphertext==='string'})); db.close(); resolve(rows)}; get.onerror=()=>reject(get.error);}; })""")
            if not encrypted_rows or not encrypted_rows[0]['encrypted'] or not encrypted_rows[0]['email_box_encrypted']:
                raise AssertionError(f'Synthetic profile was not stored as encrypted Vault data: {encrypted_rows}')
            report['checks']['encrypted_profile_history_view'] = {'record_visible': True, 'history_label': matching_history.splitlines()[0],
                'vault_row': encrypted_rows[0], 'credentials_logged': False}

            # Lock and reload before signing in again. This proves the EVA
            # history survives the actual encrypted local-profile boundary.
            await page.locator('#lock').click()
            await page.locator('#workspace').wait_for(state='hidden')
            await page.reload(wait_until='domcontentloaded')
            await page.get_by_text('Reference Python engine ready on this device', exact=False).wait_for(timeout=args.timeout_ms)
            await page.locator('#signin-email').fill(test_email)
            await page.locator('#signin-password').fill(test_password)
            await page.locator('#signin-form button.primary-action').click()
            await page.locator('#workspace').wait_for(state='visible')
            await page.locator('[data-view="history"]').click()
            reloaded_rows = await page.locator('#history-list article').filter(has_text='EVA ·').all_inner_texts()
            if not any('critical' in row.lower() and 'simulated' in row.lower() for row in reloaded_rows):
                raise AssertionError(f'Encrypted EVA record did not survive profile lock and reload: {reloaded_rows}')
            audit_status = await page.locator('#profile-status').inner_text()
            report['checks']['encrypted_profile_reload'] = {'record_recovered': True, 'audit_status': audit_status}

            await page.locator('[data-view="monitoring"]').click()
            await page.locator('#monitoring').wait_for(state='visible')
            await page.locator('[data-view="clinical"]').click()
            await page.locator('#clinical').wait_for(state='visible')
            await page.locator('[data-view="dashboard"]').click()
            await page.locator('#anatomy').wait_for(state='visible')
            await page.get_by_text('3D external body map loaded', exact=False).wait_for(timeout=60000)
            anatomy_info = await page.locator('.anatomy-canvas').evaluate("canvas=>({width:canvas.width,height:canvas.height,webgl2:!!canvas.getContext('webgl2'),hidden:canvas.hidden,rect:{width:canvas.getBoundingClientRect().width,height:canvas.getBoundingClientRect().height}})")
            if anatomy_info['hidden'] or not anatomy_info['webgl2'] or anatomy_info['width'] < 100 or anatomy_info['height'] < 100:
                raise AssertionError(f'Interactive anatomy renderer did not initialize: {anatomy_info}')
            await page.get_by_label('Select an anatomical region').select_option('left_upper_arm')
            left_region = await page.locator('#anatomy-selected-region').inner_text()
            if 'left side' not in left_region.lower():
                raise AssertionError(f'Anatomy laterality selection failed: {left_region}')
            await page.get_by_role('button', name='Posterior view').click()
            if await page.get_by_role('button', name='Posterior view').get_attribute('aria-pressed') != 'true':
                raise AssertionError('Posterior anatomy view did not become active.')
            async with page.expect_download() as region_download:
                await page.get_by_role('button', name='Export region context').click()
            region_file = await region_download.value
            region_path = output / 'anatomy-region-context.json'
            await region_file.save_as(region_path)
            region_export = json.loads(region_path.read_text(encoding='utf-8'))
            if region_export.get('clinical_authority') is not False or region_export.get('localized_findings') != []:
                raise AssertionError(f'Anatomical region export introduced unsupported clinical localization: {region_export}')
            report['checks']['interactive_anatomy'] = {
                **anatomy_info, 'status': await page.locator('#anatomy-status').inner_text(),
                'selected_region': left_region, 'posterior_view_active': True,
                'context_export': region_file.suggested_filename, 'clinical_authority': region_export.get('clinical_authority'),
                'clinical_localization': False,
            }
            await page.locator('[data-view="vision"]').click()
            await page.locator('#vision').wait_for(state='visible')
            report['checks']['existing_routes'] = ['monitoring', 'clinical', 'computer vision', 'human anatomy']

            await page.locator('[data-view="mission-control"]').click()
            await page.wait_for_timeout(500)
            await page.set_viewport_size({'width': 390, 'height': 844})
            await page.screenshot(path=str(output / 'mission-control-mobile.png'), full_page=True, animations='disabled')
            report['screenshots']['mobile'] = str(output / 'mission-control-mobile.png')
            mobile = await page.evaluate("""() => { const viewport=innerWidth; const overflow=[...document.querySelectorAll('body *')].map(element=>{const rect=element.getBoundingClientRect();return {tag:element.tagName,id:element.id,className:typeof element.className==='string'?element.className:'',right:Math.round(rect.right),width:Math.round(rect.width),text:(element.innerText||'').slice(0,80)}}).filter(item=>item.width>0&&item.right>viewport+2).sort((a,b)=>b.right-a.right).slice(0,8);const nav=document.querySelector('.side-rail nav');const navLinks=[...nav.querySelectorAll(':scope > a')].filter(link=>getComputedStyle(link).display!=='none').map(link=>({text:link.innerText,color:getComputedStyle(link).color,visible:link.getBoundingClientRect().width>0&&link.getBoundingClientRect().height>0}));return {viewport,document:document.documentElement.scrollWidth,stage:document.querySelector('.orbit-stage')?.getBoundingClientRect().width,canvas:document.querySelector('.orbit-globe-canvas')?.getBoundingClientRect().width,nav:{height:nav.getBoundingClientRect().height,background:getComputedStyle(nav.parentElement).backgroundColor,links:navLinks},overflow} }""")
            report['checks']['mobile_layout'] = mobile
            if mobile['document'] > mobile['viewport'] + 2:
                raise AssertionError(f'Mission Control overflows at mobile viewport: {mobile}')
            if not mobile['nav']['links'] or not all(link['visible'] and link['text'].strip() for link in mobile['nav']['links']):
                raise AssertionError(f'Mobile navigation labels are not visible: {mobile["nav"]}')

            timing_after = await page.evaluate("performance.getEntriesByType('resource').map(x=>({name:x.name,transferSize:x.transferSize,decodedBodySize:x.decodedBodySize,duration:x.duration}))")
            orbital_resources = [entry for entry in timing_after if any(name in entry['name'] for name in ('orbital-view.js', 'orbital-engine.js', 'three.module.js', 'three.core.js', 'satellite.js', 'earth-blue-marble'))]
            report['measurements']['mission_control_resources'] = orbital_resources
            report['measurements']['orbital_resources_decoded_bytes'] = sum(int(x.get('decodedBodySize') or 0) for x in orbital_resources)
            report['measurements']['orbital_resource_timing_note'] = 'Resource Timing transferSize may be zero when served from cache or without transfer details; decodedBodySize is the observed decoded payload size. mission_control_mount_s is measured by wall clock from route activation through renderer-ready status.'
            report['checks']['browser_console_errors'] = report['errors']
            report['checks']['unexpected_failed_requests'] = report['failed_requests']
            if report['errors']:
                raise AssertionError(f'Browser reported console/page errors: {report["errors"][:8]}')
            if report['failed_requests']:
                raise AssertionError(f'Unexpected browser requests failed: {report["failed_requests"][:8]}')
            report['result'] = 'PASS'
            await context.close()

            # WebGL-denied context: initialization must expose the calculated 2D fallback.
            fallback_context = await browser.new_context(viewport={'width': 1280, 'height': 900}, device_scale_factor=1)
            fallback_page = await fallback_context.new_page()
            await fallback_page.add_init_script("""(() => { const original=HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext=function(type,...args){ if(this.classList?.contains('orbit-globe-canvas') && String(type).startsWith('webgl')) throw new Error('WebGL deliberately disabled for fallback acceptance'); return original.call(this,type,...args); }; })();""")
            await fallback_page.goto(base, wait_until='domcontentloaded')
            await fallback_page.get_by_text('Reference Python engine ready on this device', exact=False).wait_for(timeout=args.timeout_ms)
            await fallback_page.locator('#explore').click()
            await fallback_page.locator('#workspace').wait_for(state='visible')
            await fallback_page.locator('#anatomy:not([hidden])').wait_for(state='visible')
            await fallback_page.get_by_text('3D external body map loaded', exact=False).wait_for(timeout=60000)
            await fallback_page.locator('[data-view="mission-control"]').click()
            await fallback_page.locator('.orbit-map-canvas').wait_for(state='visible', timeout=30000)
            fallback_message = await fallback_page.locator('.orbit-stage-notice').inner_text()
            if '3D globe unavailable' not in fallback_message:
                raise AssertionError(f'WebGL-denied fallback was not identified: {fallback_message}')
            report['checks']['webgl_fallback'] = {'fallback_visible': True, 'message': fallback_message}
            await fallback_context.close()
            report['result'] = 'PASS'
    except Exception as error:
        report['result'] = 'FAIL'
        report['fatal_error'] = f'{type(error).__name__}: {error}'
        if browser:
            try:
                for context in browser.contexts:
                    for page in context.pages:
                        if page.url.startswith('http://127.0.0.1:'):
                            report['failure_page'] = await page.evaluate("""() => ({url:location.href,title:document.title,bodyText:document.body?.innerText?.slice(0,2500),state:document.readyState})""")
                            (output / 'failure.html').write_text(await page.content(), encoding='utf-8')
                            await page.screenshot(path=str(output / 'failure.png'), full_page=True)
                            report['screenshots']['failure'] = str(output / 'failure.png')
            except Exception:
                pass
        raise
    finally:
        if browser:
            await browser.close()
        server.shutdown()
        server.server_close()
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
