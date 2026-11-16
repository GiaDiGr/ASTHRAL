"""Real pointer/touch acceptance checks for ASTHRAL's external-body map.

Usage:
  python tools/browser_anatomy_acceptance.py web-local/build-output-anatomy-map-YYYYMMDD
  python tools/browser_anatomy_acceptance.py web-local/build-output-anatomy-map-YYYYMMDD --url https://preview.example.pages.dev/?anatomy-e2e=1

The test runs only against an isolated static build and uses the anatomy test
hook enabled by ?anatomy-e2e=1. No clinical records are created.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from serve_browser_build import Handler  # noqa: E402


class QuietHandler(Handler):
    def log_message(self, *args: object) -> None:
        pass


def browser_executable() -> str | None:
    configured = os.environ.get("ASTHRAL_CHROMIUM")
    if configured:
        return configured
    candidates = [
        Path.home() / "AppData/Local/ms-playwright/chromium-1181/chrome-win/chrome.exe",
        Path.home() / "AppData/Local/ms-playwright/chromium-1181/chrome-win64/chrome.exe",
    ]
    return str(next((path for path in candidates if path.is_file()), "")) or None


def click_position(page, x: float, y: float, *, touch: bool = False, cdp=None) -> None:
    if touch:
        if cdp is None:
            page.touchscreen.tap(x, y)
        else:
            cdp.send("Input.dispatchTouchEvent", {
                "type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}],
            })
            cdp.send("Input.dispatchTouchEvent", {
                "type": "touchEnd", "touchPoints": [],
            })
    else:
        page.mouse.click(x, y)


def locate_visible_region(page, region_id: str) -> dict:
    result = page.evaluate("""({regionId}) => {
      const test = window.__ASTHRAL_ANATOMY_TEST__;
      const canvas = document.querySelector('.anatomy-canvas');
      const rect = canvas.getBoundingClientRect();
      const points = test.surfacePointSamples(regionId, 80);
      const attempts = [];
      for (const source of points) {
        const screen = test.projectSourcePoint([source.x, source.y, source.z]);
        if (screen.x < rect.left || screen.x > rect.right || screen.y < rect.top || screen.y > rect.bottom) continue;
        const hit = test.resolveAtClientPoint(screen.x, screen.y);
        attempts.push({screen, hitRegion: hit?.regionId ?? null});
        if (hit?.regionId === regionId) return {source, ...screen, hit, attempts: attempts.length};
      }
      return {found: false, regionId, candidates: points.length, attempts};
    }""", {"regionId": region_id})
    if not result.get("x") and result.get("x") != 0:
        raise AssertionError(f"No frontmost visible surface sample resolved as {region_id}: {json.dumps(result)[:1200]}")
    return result


def locate_unclassified_surface(page) -> dict:
    result = page.evaluate("""() => {
      const test = window.__ASTHRAL_ANATOMY_TEST__;
      const rect = document.querySelector('.anatomy-canvas').getBoundingClientRect();
      const points = test.surfacePointSamples('unclassified', 120);
      const attempts = [];
      for (const source of points) {
        const screen = test.projectSourcePoint([source.x, source.y, source.z]);
        if (screen.x < rect.left || screen.x > rect.right || screen.y < rect.top || screen.y > rect.bottom) continue;
        const hit = test.resolveAtClientPoint(screen.x, screen.y);
        attempts.push({screen, hitRegion: hit?.regionId ?? null, hasSurfaceHit: Boolean(hit)});
        if (hit && hit.regionId === null) return {source, ...screen, hit, attempts: attempts.length};
      }
      return {found:false, candidates:points.length, attempts};
    }""")
    if not result.get("hit"):
        raise AssertionError(f"Could not find a frontmost ambiguous surface triangle: {json.dumps(result)[:1200]}")
    return result


def assert_selection(page, region_id: str, *, touch: bool = False, cdp=None) -> dict:
    page.locator('.anatomy-canvas').scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    target = locate_visible_region(page, region_id)
    page.evaluate("y => window.scrollBy({top: y < 80 ? y - 120 : y > innerHeight - 80 ? y - innerHeight + 120 : 0, behavior: 'instant'})", target['y'])
    target = locate_visible_region(page, region_id)
    click_position(page, target["x"], target["y"], touch=touch, cdp=cdp)
    page.wait_for_timeout(80)
    state = page.evaluate("""() => ({
      selection: window.__ASTHRAL_ANATOMY_TEST__.selection(),
      highlighted: window.__ASTHRAL_ANATOMY_TEST__.highlightedTriangles(),
      label: document.querySelector('#anatomy-selected-region').innerText,
      canvas: document.querySelector('.anatomy-frame').dataset.selectedRegion,
    })""")
    if state["selection"] != {"regionId": region_id, "dropdown": region_id, "context": region_id}:
        pointer = page.evaluate("window.__lastAnatomyPointer || null")
        raise AssertionError(f"Selection, selector and context diverged for {region_id}; projected={target}; actual={state['selection']}; pointer={pointer}")
    if state["highlighted"].get(region_id, 0) < 1:
        raise AssertionError(f"Selected region {region_id} has no highlighted surface vertices")
    wrong = {key: value for key, value in state["highlighted"].items() if key != region_id and value}
    if wrong:
        raise AssertionError(f"Unexpected other highlighted regions for {region_id}: {wrong}")
    if region_id.replace("_", " ") not in state["label"].lower():
        # The user-facing label is title case and turns identifiers into words.
        expected = page.locator(f"select[aria-label='Select an anatomical region'] option[value='{region_id}']").inner_text()
        if expected.lower() not in state["label"].lower():
            raise AssertionError(f"Context label does not match {region_id}: {state['label']}")
    return {"expected": region_id, "actual": state["selection"]["regionId"], "screen": [round(target["x"], 2), round(target["y"], 2)], "hit_mesh": target["hit"]["objectName"], "hit_point": target["hit"]["point"], "highlighted_triangles": state["highlighted"][region_id], "context": state["label"]}


def open_anatomy(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.get_by_role("button", name="Explore Synthetic Demo").click()
    page.locator("#workspace").wait_for(state="visible", timeout=60000)
    page.locator("#anatomy:not([hidden])").wait_for(state="visible", timeout=60000)
    # Anatomy is added to the overflow menu by the mission-support module.
    # Open its details container and dispatch the same delegated navigation
    # event; the browser acceptance is concerned with actual body pointer/touch
    # coordinates below, not a flaky animation in the navigation flyout.
    page.locator("#anatomy:not([hidden])").wait_for(state="visible", timeout=10000)
    page.locator("#anatomy-view").scroll_into_view_if_needed()
    page.locator(".anatomy-canvas").scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    page.wait_for_function("""() => {
      const canvas = document.querySelector('.anatomy-canvas');
      const rect = canvas?.getBoundingClientRect();
      return Boolean(window.__ASTHRAL_ANATOMY_TEST__ && canvas && rect.width > 0 && rect.height > 0);
    }""", timeout=60000)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path, help="isolated ASTHRAL build output")
    parser.add_argument("--output", type=Path, help="evidence directory (default: work/anatomy-browser-acceptance)")
    parser.add_argument("--url", help="run the same acceptance suite against a deployed HTTPS preview")
    args = parser.parse_args()
    build = args.build.resolve(strict=True)
    if not (build / "assets.json").is_file():
        parser.error("build must be an ASTHRAL public build containing assets.json")
    output = (args.output or ROOT / "work/anatomy-browser-acceptance").resolve()
    output.mkdir(parents=True, exist_ok=True)
    executable = browser_executable()
    if not executable:
        parser.error("Chromium executable unavailable; set ASTHRAL_CHROMIUM to its path")

    server = None
    if args.url:
        base_url = args.url
        if "anatomy-e2e=1" not in base_url:
            base_url += ("&" if "?" in base_url else "?") + "anatomy-e2e=1"
    else:
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(build)))
        Thread(target=server.serve_forever, daemon=True).start()
        base_url = f"http://127.0.0.1:{server.server_port}/?anatomy-e2e=1"
    report: dict = {"base_url": base_url, "build": str(build), "desktop_cases": [], "mobile_cases": [], "errors": [], "synthetic_only": True}
    started = time.perf_counter()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=executable,
                headless=True,
                args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            page_errors: list[str] = []
            failed_requests: list[dict] = []
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("requestfailed", lambda request: failed_requests.append({"url": request.url, "error": request.failure}))
            open_anatomy(page, base_url)
            page.evaluate("""() => {
              window.__lastAnatomyPointer = null;
              const canvas = document.querySelector('.anatomy-canvas');
              for (const type of ['pointerdown','pointerup']) canvas.addEventListener(type, event => {
                window.__lastAnatomyPointer = {type:event.type, clientX:event.clientX, clientY:event.clientY, pointerType:event.pointerType, hit:window.__ASTHRAL_ANATOMY_TEST__.resolveAtClientPoint(event.clientX,event.clientY)};
              }, true);
            }""")
            report["load_seconds"] = round(time.perf_counter() - started, 3)
            report["coverage"] = page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.coverage()")
            if len(report["coverage"]) != 28 or any(value < 1 for value in report["coverage"].values()):
                raise AssertionError(f"Expected all 28 regions represented by classified body surface: {report['coverage']}")

            # Regression for the reported stale head-versus-chest behavior.
            for region in ["chest", "head", "abdomen", "left_upper_arm", "right_upper_arm", "head"]:
                report["desktop_cases"].append(assert_selection(page, region))
            page.locator("#anatomy").screenshot(path=str(output / "desktop-head-selected.png"))

            # Exercise all supported IDs against visible surface geometry. The
            # posterior view is used only for the back surface.
            for region in ["head", "face", "left_eye", "right_eye", "neck", "chest", "abdomen", "left_shoulder", "right_shoulder", "left_upper_arm", "right_upper_arm", "left_forearm", "right_forearm", "left_hand", "right_hand", "left_hip", "right_hip", "left_thigh", "right_thigh", "left_knee", "right_knee", "left_lower_leg", "right_lower_leg", "left_ankle", "right_ankle", "left_foot", "right_foot"]:
                page.get_by_role("button", name="Anterior view").click()
                if region == "left_hip" or region == "right_hip":
                    # Hips are lateral landmarks. Rotate a quarter turn so
                    # their true side surface is frontmost instead of trying
                    # to pick through the abdomen or thigh from the front.
                    rect = page.locator(".anatomy-canvas").bounding_box()
                    x0, y0 = rect["x"] + rect["width"] * 0.5, rect["y"] + rect["height"] * 0.35
                    direction = -1 if region == "left_hip" else 1
                    page.mouse.move(x0, y0); page.mouse.down(); page.mouse.move(x0 + direction * 196, y0, steps=12); page.mouse.up()
                report["desktop_cases"].append(assert_selection(page, region))
            page.get_by_role("button", name="Posterior view").click()
            report["desktop_cases"].append(assert_selection(page, "back"))
            report["desktop_cases"].append(assert_selection(page, "left_hand"))
            report["desktop_cases"].append(assert_selection(page, "right_hand"))
            page.locator("#anatomy").screenshot(path=str(output / "desktop-back-selected.png"))

            # Zoom, rotation and pan must preserve truthful selection state.
            page.get_by_role("button", name="Reset camera").click()
            page.get_by_role("button", name="Zoom in").click()
            page.get_by_role("button", name="Zoom in").click()
            report["desktop_cases"].append(assert_selection(page, "left_eye"))
            before_drag = page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()")
            rect = page.locator(".anatomy-canvas").bounding_box()
            x0, y0 = rect["x"] + rect["width"] * 0.12, rect["y"] + rect["height"] * 0.22
            page.mouse.move(x0, y0); page.mouse.down(); page.mouse.move(x0 + 90, y0 + 24, steps=8); page.mouse.up()
            after_drag = page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()")
            if after_drag != before_drag:
                raise AssertionError(f"Mouse rotation changed selection without a tap: {before_drag} -> {after_drag}")
            report["desktop_cases"].append(assert_selection(page, "right_hand"))
            page.get_by_role("button", name="Pan mode off").click()
            before_pan = page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()")
            rect = page.locator(".anatomy-canvas").bounding_box()
            x0, y0 = rect["x"] + rect["width"] * 0.15, rect["y"] + rect["height"] * 0.18
            page.mouse.move(x0, y0); page.mouse.down(); page.mouse.move(x0 + 28, y0 + 16, steps=4); page.mouse.up()
            if page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()") != before_pan:
                raise AssertionError("Pan gesture changed the selected region")
            report["desktop_cases"].append(assert_selection(page, "chest"))

            # Empty canvas click must clear instead of retaining a stale hit.
            rect = page.locator(".anatomy-canvas").bounding_box()
            empty = page.evaluate("([x,y]) => window.__ASTHRAL_ANATOMY_TEST__.resolveAtClientPoint(x,y)", [rect["x"] + 8, rect["y"] + 8])
            if empty is not None:
                raise AssertionError(f"Chosen empty-space point unexpectedly raycast to body: {empty}")
            page.mouse.click(rect["x"] + 8, rect["y"] + 8)
            page.wait_for_timeout(80)
            if page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection().regionId !== ''"):
                raise AssertionError("Empty-space click retained the previous region")
            empty_state = page.evaluate("({selection:window.__ASTHRAL_ANATOMY_TEST__.selection(),highlighted:window.__ASTHRAL_ANATOMY_TEST__.highlightedTriangles()})")
            if any(empty_state["highlighted"].values()):
                raise AssertionError(f"Clearing an unresolved pick left a region highlighted: {empty_state['highlighted']}")
            report["desktop_cases"].append({"expected": "empty", "actual": "empty", "selection": empty_state["selection"]})

            # A visible but intentionally unclassified triangle must also
            # clear the old region. This reproduces the old stale-hit defect.
            page.get_by_role("button", name="Anterior view").click()
            assert_selection(page, "chest")
            ambiguous = locate_unclassified_surface(page)
            page.mouse.click(ambiguous["x"], ambiguous["y"])
            page.wait_for_timeout(80)
            unresolved_state = page.evaluate("({selection:window.__ASTHRAL_ANATOMY_TEST__.selection(),highlighted:window.__ASTHRAL_ANATOMY_TEST__.highlightedTriangles(),label:document.querySelector('#anatomy-selected-region').innerText})")
            if unresolved_state["selection"] != {"regionId":"","dropdown":"","context":""} or any(unresolved_state["highlighted"].values()):
                raise AssertionError(f"Unclassified visible surface retained stale region state: {unresolved_state}")
            if not unresolved_state["label"].startswith("No region selected"):
                raise AssertionError(f"Unclassified surface result was not described truthfully: {unresolved_state['label']}")
            report["desktop_cases"].append({"expected":"unclassified_surface","actual":"unclassified_surface","resolved_triangle":ambiguous["hit"]["faceIndex"]})

            # Keyboard/accessibility selector remains an alternate navigation path.
            page.locator("select[aria-label='Select an anatomical region']").select_option("left_foot")
            dropdown_state = page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()")
            if dropdown_state != {"regionId": "left_foot", "dropdown": "left_foot", "context": "left_foot"}:
                raise AssertionError(f"Accessible selector did not synchronize the context: {dropdown_state}")
            dropdown_highlight = page.evaluate("window.__ASTHRAL_ANATOMY_TEST__.highlightedTriangles()")
            if dropdown_highlight["left_foot"] < 1 or any(value for key, value in dropdown_highlight.items() if key != "left_foot"):
                raise AssertionError(f"Accessible selector did not synchronize the highlight: {dropdown_highlight}")
            page.locator("#anatomy").screenshot(path=str(output / "desktop-dropdown-foot-selected.png"))
            report["desktop_cases"].append({"expected": "left_foot", "actual": dropdown_state["regionId"], "input": "accessible_dropdown"})

            # Cache the optional model by hash, install the core PWA resources,
            # then reload and reselect body regions while the browser is offline.
            page.locator("button", has_text="Install 3D model for offline use").click()
            cache_status = page.locator(".anatomy-data-status")
            cache_deadline = time.monotonic() + 30
            while time.monotonic() < cache_deadline:
                cache_message = cache_status.inner_text()
                if cache_message.startswith("Anatomical model assets cached and hash-verified"):
                    break
                if cache_message.startswith("Offline anatomy install failed"):
                    raise AssertionError(cache_message)
                page.wait_for_timeout(250)
            else:
                raise AssertionError(f"Timed out caching the anatomy model: {cache_status.inner_text()}")
            optional_cache = page.evaluate("""async () => {
              const cache = await caches.open('asthral-optional-resources-v1');
              const url = new URL('./vendor/anatomy/makehuman-external-body.glb', location.href);
              const response = await cache.match(url);
              if (!response) return {found:false};
              const bytes = await response.arrayBuffer();
              const sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
              return {found:true, bytes:bytes.byteLength, sha256};
            }""")
            if optional_cache != {"found": True, "bytes": 4498248, "sha256": "86c7cdfa989924b45e2e5110c131a4a4e6251ceb4e71246be68e468f3a32ca86"}:
                raise AssertionError(f"Offline anatomy model cache failed integrity verification: {optional_cache}")
            report["offline_model_cache"] = optional_cache
            page.locator('#workspace-nav [data-view="settings"]').evaluate("node => node.click()")
            page.locator("#settings:not([hidden])").wait_for(state="visible")
            page.locator("#install-offline").click()
            offline_status = page.locator("#offline-status")
            offline_deadline = time.monotonic() + 120
            while time.monotonic() < offline_deadline:
                offline_message = offline_status.inner_text()
                if offline_message.startswith("Offline resources verified:"):
                    break
                if offline_message.startswith("Offline installation failed:"):
                    raise AssertionError(offline_message)
                page.wait_for_timeout(250)
            else:
                raise AssertionError(f"Timed out installing offline resources: {offline_status.inner_text()}")
            report["offline_core_install"] = page.locator("#offline-status").inner_text()
            page.context.set_offline(True)
            offline_reload_started = time.perf_counter()
            page.reload(wait_until="domcontentloaded", timeout=60000)
            report["offline_reload_seconds"] = round(time.perf_counter() - offline_reload_started, 3)
            if page.evaluate("navigator.onLine") is not False:
                raise AssertionError("Browser context did not enter offline mode")
            page.get_by_role("button", name="Explore Synthetic Demo").click()
            page.locator("#workspace").wait_for(state="visible", timeout=60000)
            page.locator("#anatomy:not([hidden])").wait_for(state="visible", timeout=60000)
            page.locator('#workspace-nav [data-view="anatomy"]').evaluate("node => node.click()")
            page.locator("#anatomy:not([hidden])").wait_for(state="visible", timeout=10000)
            page.get_by_text("3D external body map loaded", exact=False).wait_for(state="visible", timeout=30000)
            if page.evaluate("window.__ASTHRAL_ANATOMY_TEST__ === undefined"):
                raise AssertionError("Offline anatomy browser test hooks did not initialize")
            report["offline_cases"] = [assert_selection(page, "head"), assert_selection(page, "chest")]
            page.locator("#anatomy").screenshot(path=str(output / "offline-chest-selected.png"))
            page.context.set_offline(False)

            # A real mobile-emulated touch tap and swipe (Chromium CDP touch input).
            mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
            mobile = mobile_context.new_page()
            open_anatomy(mobile, base_url)
            mobile_cdp = mobile_context.new_cdp_session(mobile)
            report["mobile_cases"].append(assert_selection(mobile, "chest", touch=True, cdp=mobile_cdp))
            mobile_before = mobile.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()")
            mobile_rect = mobile.locator(".anatomy-canvas").bounding_box()
            tx, ty = mobile_rect["x"] + mobile_rect["width"] * 0.15, mobile_rect["y"] + mobile_rect["height"] * 0.2
            mobile_cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": tx, "y": ty, "id": 1}]})
            mobile_cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": tx + 50, "y": ty + 5, "id": 1}]})
            mobile_cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": tx + 85, "y": ty + 8, "id": 1}]})
            mobile_cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            if mobile.evaluate("window.__ASTHRAL_ANATOMY_TEST__.selection()") != mobile_before:
                raise AssertionError("Mobile rotate gesture changed selection without a tap")
            report["mobile_cases"].append(assert_selection(mobile, "right_hand", touch=True, cdp=mobile_cdp))
            mobile.locator("#anatomy").screenshot(path=str(output / "mobile-hand-selected.png"))
            mobile_context.close()
            browser.close()
            report["page_errors"] = page_errors
            report["failed_requests"] = failed_requests
            if page_errors or failed_requests:
                raise AssertionError(f"Browser runtime errors or failed requests: {page_errors} {failed_requests}")
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()

    anatomical_ids = set(report["coverage"])
    region_cases = [case for case in report["desktop_cases"] if case.get("expected") in anatomical_ids and case.get("input") != "accessible_dropdown"]
    report["desktop_region_click_accuracy"] = f"{sum(case.get('actual') == case.get('expected') for case in region_cases)}/{len(region_cases)}"
    report["desktop_interaction_accuracy"] = f"{sum(case.get('actual') == case.get('expected') for case in report['desktop_cases'] if 'expected' in case)}/{sum('expected' in case for case in report['desktop_cases'])}"
    selector_cases = [case for case in report["desktop_cases"] if case.get("input") == "accessible_dropdown"]
    report["accessible_selector_accuracy"] = f"{sum(case.get('actual') == case.get('expected') for case in selector_cases)}/{len(selector_cases)}"
    unresolved_cases = [case for case in report["desktop_cases"] if case.get("expected") == "unclassified_surface"]
    report["unclassified_surface_accuracy"] = f"{sum(case.get('actual') == case.get('expected') for case in unresolved_cases)}/{len(unresolved_cases)}"
    report["mobile_touch_accuracy"] = f"{sum(case.get('actual') == case.get('expected') for case in report['mobile_cases'])}/{len(report['mobile_cases'])}"
    report["offline_region_accuracy"] = f"{sum(case['actual'] == case['expected'] for case in report.get('offline_cases', []))}/{len(report.get('offline_cases', []))}"
    report["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["desktop_region_click_accuracy", "desktop_interaction_accuracy", "accessible_selector_accuracy", "unclassified_surface_accuracy", "mobile_touch_accuracy", "offline_region_accuracy", "offline_model_cache", "offline_core_install", "offline_reload_seconds", "coverage", "load_seconds", "elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
