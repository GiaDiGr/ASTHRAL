> Continuation update: INTEGRATION_REVIEW_20261115.md records subsequent CPU browser MotionGuard, USDA v2, DONKI acknowledgement and public offline checks, and a later parallel-navigation timeout. Historical results below are retained; they are not a claim of comprehensive load or clinical acceptance. The dev server now mirrors the build _headers policy.

# ASTHRAL startup transport resolution â€” 2026-11-15

## Outcome and evidence boundary

Development branch `feature/asthral-autonomous-mission`, continuation from `5bd10377`. The demonstrated trigger is immediate HTTP connection closure on this Windows loopback path. Persistent HTTP/1.1 responses eliminate the reproduced browser startup failures in the measured runs. This identifies the transport behavior and a tested correction; it does not identify a particular Windows driver/security product as the underlying agent. HTTP/1.0 is a legal protocol; these observations do not imply that Python or the served biomedical packages are generally defective.

No security controls, proxy settings, certificates, clinical modules or model manifests were changed. No request interception, renamed asset, synthetic HTTP response or fake inference was used. The Node comparison served the exact same public build bytes through ordinary HTTP.

## Investigation

All 88 public-build assets existed and matched their manifest sizes/hashes. Previous artifacts/logs remain preserved. Unchanged original Python HTTP/1.0 behavior was instrumented with request timing and exception capture. Five problematic assets were requested repeatedly: Pydantic wheel, SQLite wheel, Pyodide lock, engine ZIP and corpus JSON.

| Experiment | Observed result |
|---|---|
| Python HTTP/1.0, sequential urllib | 13/15 complete and hash-matching; 2 timeouts |
| Python HTTP/1.0, concurrent urllib | 23/25 complete and hash-matching; 2 timeouts |
| Python HTTP/1.0, real Chromium fetch | 21/25 complete; 4 connection resets; no server exceptions |
| Node HTTP/1.1, urllib requests with Connection: close | 13/40 requests timed out; remaining responses complete; close-trigger behavior reproduced on a different implementation |
| Node HTTP/1.1, real Chromium fetch | 25/25 complete and hash-matching, zero request failures |
| Same Node engine.zip, explicit keep-alive vs close | keep-alive 3/3 complete/hash match; close 1/3 complete and 2 timeouts |
| Corrected Python HTTP/1.1, concurrent keep-alive downloads | 60/60 complete and hash-matching, status 200, HTTP version 1.1 and declared length checked |
| Corrected Python HTTP/1.1, independent browser workflows | three independent Chromium runs passed recorded scope with zero failed requests and zero page errors; engine ready 3.74, 3.63, 3.71 seconds |

Chromium netlog records socket read errors `net_error=-101`, Windows socket error `10054`, on `127.0.0.1` sockets after about 19 seconds, with no recorded response bytes for the failed sockets. The server completed the corresponding handler without an exception. There were no configured environment/urllib proxies and WinHTTP reported direct access. Read-only Windows network/security checks did not establish a responsible security product. Do not infer Norton causation from these results.

Detailed reports: `work/transport-investigation/report.json`, `server.json`, `chromium-netlog.json`, `connection-close-comparison.json`, `http11-downloads.json`; Node comparison in `work/transport-comparison-node/report.json` and its netlog. Only synthetic/public asset requests were made in these traces; treat browser background metadata in raw traces as local diagnostic data rather than clinical evidence.

## Correction and regression

`tools/serve_browser_build.py` now sets `Handler.protocol_version = "HTTP/1.1"`. The standard static handler supplies Content-Length, MIME types and complete original bytes, retaining connections until the client completes the response. Existing bounded startup retries, actual Python import checks, atomic corpus/scenario initialization, local-source hashes and treatment restrictions remain intact. A favicon declaration prevents an unrelated missing favicon request from polluting the final browser console.

`engine/tests/test_browser_static_transport.py` requests a 512 KiB fixture six times over the same HTTP connection; it asserts HTTP/1.1, exact Content-Length and SHA-256, and that the client socket/port is preserved across requests. The diagnostic HTTP/1.0 negative control is explicit in `tools/diagnose_browser_transport.py`; never use it as the application server.

## Current acceptance matrix

| Subsystem | Classification and actual scope |
|---|---|
| Startup/public asset transport | SOFTWARE IMPLEMENTED AND VERIFIED for corrected dev server, download tests and repeated real Chromium startup. Exact Windows intermediary responsible for premature-close loss remains unidentified. |
| Guided exercise | SOFTWARE IMPLEMENTED AND VERIFIED for tested demo controls: selection/start, manual sets/repetitions, pause/resume/complete, visible history/summary. Other workout types, interrupted-session recovery and durable profile restoration still need full browser coverage. |
| USDA nutrition/hydration | SOFTWARE IMPLEMENTED AND VERIFIED for tested food search/selection/portion save and hydration action in temporary demo. Full nutrient accuracy/missing-value logic has separate engine/Node tests. Audited corrections/additional data category remain NOT IMPLEMENTED. |
| Sleep/wellbeing | SOFTWARE IMPLEMENTED, BROWSER ACCEPTANCE PENDING for save/review flows. Routes opened successfully. New automated save-flow commands were rejected by automatic approval review with `blocked by policy`, without a stated reason; no alternate channel was used to execute rejected actions. |
| Radiation | SOFTWARE IMPLEMENTED, BROWSER ACCEPTANCE PENDING for preview/commit/export through real controls. Unit/atomic-preview logic and plots have passing software tests. Expanded real-browser mutation test was rejected by automatic approval review; no physical sensor claim. |
| Deterministic clinical computation | Reference code preserved, native/WASM parity tests pass. Real browser assessment route opened. New computation/persistence test command was rejected before execution; do not claim the expanded workflow passed. |
| Encrypted profile reload/offline restoration | Existing vault and service-worker software tests retained. Expanded account creation/encryption/reload/offline automation was rejected before execution by automatic approval review, no detailed reason supplied. Current build device acceptance remains PENDING. |
| Qwen/WebLLM | SOFTWARE BLOCKED BY IDENTIFIED RUNTIME CAPABILITY in tested ordinary Chromium launches: navigator.gpu.requestAdapter returned null in both headless and headed sessions. No unsafe GPU flags or validator bypass. Native Ollama was not used as a prerequisite or explanation. No generated response or inference benchmark claimed. |
| Scientific RAG | Existing lexical/hybrid contracts retained. CPU MiniLM built 586 genuine vectors and retrieved source-labelled exercise excerpts in real Chromium; comprehensive corpus expansion and held-out faithfulness/relevance evaluation remain NOT COMPLETED. WebGPU/Qwen limits do not by themselves prove CPU semantic retrieval impossible. |
| MotionGuard/OcularVision | Native contributor code/licenses/hashes remain in COMPUTER_VISION.md. Browser inference, representative permitted fixtures and exercise integration NOT IMPLEMENTED/VERIFIED; no invented angles, repetitions or segmentation. |
| Voice | Local Vosk recognized all six packaged synthetic audio fixtures: five exact transcripts/structured matches, one sleep mismatch left unresolved; no records saved. Physical microphone/playback remain NOT VERIFIED. |
| DONKI | Live public endpoint checks now cover CME, GST, IPS, SEP and FLR; HTTP 200 each. 21 CME and 5 FLR records, zero GST/IPS/SEP for 2026-11-08..15. These empty sets are valid responses, not proof of benign conditions. Browser notice acknowledgement and foreground permission workflow still need real acceptance; no background-warning claim. |
| Unified/mobile UI | Real screenshots cover login, dashboard, exercise, nutrition and opened routes; mobile screenshot reflects actual current page. No claim of exhaustive mobile usability, full mission, model conversation or all control acceptance. |
| Clinical/flight validity | CLINICAL OR FLIGHT VALIDATION NOT PERFORMED. Software acceptance does not authorize treatment or establish medical/biomechanical/dosimetry accuracy. |

## Final verification

Full Python suite result is recorded in `work/blocker-resolution-pytest.txt`; full Node suite in `work/blocker-resolution-node.txt` (81 passed). Final build directory: `web-local/build-output-blocker-resolved-20261115`, 88 resources, 112931939 bytes, 254 parity cases, clinical modules BYTE_IDENTICAL. Every source manifest hash is checked separately. Final fresh-context browser reports/screenshots in `work/browser-acceptance-final-http11-1` and `...-2` supplement the first three repeated runs.

## Reproduction

```powershell
Set-Location 'C:\Users\Gianni\Documents\Codex\ASTHRAL_AUTONOMOUS_MISSION_20261115'
$enginePython = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe'
& $enginePython -m pytest engine/tests -q
node --test web-local/tests/*.test.mjs
& $enginePython tools/build_science_integrity.py --check
# Select a NEW output path for each build; existing build artifacts are preserved.
$env:ASTHRAL_BUILD_OUTPUT = Join-Path (Get-Location) 'web-local/build-output-blocker-resolved-reproduction'
& $enginePython web-local/build.py
python tools/serve_browser_build.py web-local/build-output-blocker-resolved-reproduction --port 8933
# In another terminal:
python tools/browser_acceptance.py --url http://127.0.0.1:8933/ --output work/browser-reproduction
python tools/browser_model_acceptance.py
```

The model-capability probe accepts an explicit loopback URL argument; embedding and voice probes use the corrected server on port 8934 by default. No stable production deployment or main merge was performed.

## Additional independent integration checks

A second concrete server defect was reproduced: Windows MIME associations made SimpleHTTPRequestHandler serve `.mjs` as `text/plain; charset=utf-8` with `nosniff`. Chromium correctly refused the ONNX Runtime module. The development server now explicitly serves `.js`/`.mjs` as JavaScript and `.wasm` as application/wasm, retaining nosniff; the regression checks these headers. No MIME security check was disabled.

The current corpus inventory is 8 verified documents / 586 sparse blocks; the older 7/566 corpus and six-fragment semantic index are historical artifacts. `work/current-corpus-inventory.json` records the actual hashes/authority metadata. This reconciliation is not a scientific coverage or retrieval-accuracy claim. CPU MiniLM acceptance is recorded separately in `work/browser-embedding-acceptance/report.json`.

Final tests after the MIME regression are recorded in `work/blocker-resolution-final-pytest.txt`. The prior full run passed 916 tests with 19 skips and one Starlette/httpx deprecation warning in 364.65 s. The full Node suite passed 81 tests in 9.71 s.

## Final verification and independent model checks

Final Python suite after the MIME regression: 916 passed, 19 skipped, one existing Starlette/httpx deprecation, 228.39 seconds. Final Node suite: 81 passed. Two fresh final-build Chromium runs had zero request, page or console errors; startup 3.70 and 3.44 seconds.

CPU MiniLM actually generated 586 vectors and retrieved source-labelled exercise material. One retrieval example does not establish held-out relevance accuracy or answer faithfulness. See work/browser-embedding-acceptance/report.json.

Vosk executed six permitted synthetic waveforms: five exact matches including quantities/units/negation; sleep changed "as seven hours" to "a seven hours" and remained unresolved. None saved a record. Final processing times: 0.82–1.66 seconds per fixture. Public offline installation verified 70 files, followed by an online page reload and genuine recognition. Offline-network operation and encrypted profile restoration are separate pending acceptance. See work/browser-voice-acceptance/report.json.

The development server does not emulate every Cloudflare production header; localhost results do not replace deployment/CSP/device acceptance. All reference clinical modules remain byte-identical.

The final Vosk run waited for the actual offline installer completion message: 70 files verified. Only then did it reload the online page and run recognition. This is not a claim that network-disconnected encrypted profile restoration was tested.
