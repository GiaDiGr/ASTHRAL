# ASTHRAL integration review — 2026-11-15

Development worktree: `C:\Users\Gianni\Documents\Codex\ASTHRAL_AUTONOMOUS_MISSION_20261115`, branch `feature/asthral-autonomous-mission`. This continues commit 7cf17bbc and the original 5bd10377 directive; it does not merge main, deploy production, replace Ollama, change Norton or alter clinical criteria. Software completeness against the entire directive is **not established**.

## Implemented corrections and contracts

- Genuine optional browser CPU pose inference, reviewed attach-to-manual-session summary, 2D geometry, explicit tracking abstention, local video/camera lifecycle and plaintext export. Native Holistic remains separate. See MOTIONGUARD_BROWSER_20261115.md.
- USDA versioned energy references, 424 original foods, explicit method selection and provenance, v1 compatibility. The earlier 329 energy-missing count was the 1008 nutrient count; only 50 lack all three named energy references. See NUTRITION_REFERENCE_AUDIT_V2_20261115.md. No automatic choice, macro-based imputation or nutritional target.
- UTC grouping and instant-based session ordering, rejection of naive/invalid times, explicit UTC form parsing. Circular sleep-clock spread handles midnight and undefined/insufficient samples without clinical interpretation. Formula reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.circstd.html . Earlier intended manual observation timestamps are not retrospectively recoverable; no historical records were rewritten.
- DONKI acknowledgements bind normalized event revisions; changed notices and legacy unversioned acknowledgements require a new acknowledgement. Storage failure does not mark a notice acknowledged.
- A real WebGPU adapter check blocks unavailable Qwen loading before a large download. Deterministic Python and CPU retrieval remain available.
- Development HTTP mirrors build `_headers` CSP/Permissions Policy, explicit module MIME and persistent HTTP/1.1. Only an ordinary user camera prompt is permitted. Fixed official DONKI host is allowed; no unsafe-eval, fake camera, request interception or browser-security bypass.
- Public packaging excludes Python interpreter caches, retaining original bootstrap sources only inside engine.zip. A regression exercises the actual copy routine. Scientific registry integrity checks pass; original clinical modules are BYTE_IDENTICAL, with 254 frozen parity cases generated.

Integration field additions, allowed values, caveats and v1-to-v2 migration are in web-local/INTEGRATION_CONTRACTS.md. Model reports remain untrusted client estimates; manual values and deterministic clinical authority are independent. All therapy execution remains blocked.

## Acceptance matrix and actual evidence

| Component | Software / actual browser evidence | Remaining boundary |
|---|---|---|
| HTTP startup | Root experiment/keepalive and MIME regression in BLOCKER_RESOLUTION_20261115.md; repeated independent normal workflows succeeded | Three simultaneous Chromium acceptance processes on port 8945 later timed out at navigation/load without recorded requestfailed events. Cause unproven; final single-client successes do not establish load robustness. |
| Guided exercise | Actual temporary-demo start/count/pause/resume/complete and history; unit session/clock checks | All workout variants, interrupted persistent-profile recovery and physical use not accepted end-to-end |
| MotionGuard | Genuine CPU model, three licensed public clips, actual overlays/exports; 25/75/26 sampled frames with 1/42/26 missing joint angles | No annotated ground truth, biomechanical accuracy, physical camera or spaceflight validation |
| USDA / hydration | Real source-alternative preview, unknown 1008 value, selected method, lookup/portion save and hydration in demo; native lookup/version/null tests | No adequacy, mission-food mapping, correction UI or additional USDA categories |
| Sleep / wellbeing | Existing normalized duration/self-report logic plus UTC circular-clock summary tests; routes open | Expanded browser save test command was rejected by automatic approval review, without detailed reason; no alternate channel used to perform rejected actions |
| Radiation | Existing atomic preview/import/dosimetry restrictions and tests; route/chart implementation retained | Expanded browser mutation/CSV acceptance was rejected by automatic approval review; no detector validation or personalized risk claim |
| Clinical engine / mission | Original deterministic engine, rules, source traces and parity inputs preserved | Expanded browser computation/persistence/account test command was rejected before execution; do not report a complete astronaut mission |
| Public offline | Real installer, online controller reload, network disabled in Playwright, second reload, Python ready and local lexical retrieval | Private encrypted profile close/reopen/import/restore not included; earlier expanded private-profile automation was rejected |
| RAG | Genuine MiniLM CPU index: 586 verified-source vectors; actual source-labelled exercise retrieval, zero reported request/page errors | Eight-document curated/implementation corpus; no full scientific corpus or independently graded held-out retrieval/faithfulness evaluation |
| Qwen / WebLLM | Ordinary headless and headed Chromium have no adapter; actual UI disables load and reports UNSUPPORTED | No generation or current throughput measurements; no unsupported flags added and no inference replaced with Ollama |
| Voice | Real Vosk on six packaged synthetic WAVs, five exact transcript/structured matches; one sleep mismatch remains unresolved, no records saved | Physical microphone, speaker playback, accents and free speech accuracy not established |
| DONKI | Live official public sync, acknowledgement and reload; version-change/quota/legacy tests | Two ERR_ABORTED request log entries persisted despite 40 parsed records and zero endpoint issues; no background/personal alert claim |
| Ocular / Skin / Echo | Local intake/previews and native research adapters preserved | Browser OCT model not implemented; no licensed compatible held-out image set installed. Skin weights missing. Echo download/execution remains rights-blocked. |
| Mobile / resources | Actual desktop screenshots and 390px viewport screenshots; optional worker release policy retained | Viewports are not physical devices; no broad thermal/energy/GPU acceptance |

The parallel navigation failures are preserved in work/browser-acceptance-release-reviewed-1, work/browser-pose-release-reviewed and work/browser-public-offline-release-reviewed. Subsequent isolated reports use distinct directories; failures were not overwritten. One port-8945 offline run completed Python/retrieval but also recorded an aborted statistics fixture fetch and page error during transitions; that report remains evidence of a warning, not zero-error acceptance. The earlier port-8944 public offline test had no request/page errors. Final candidate results below supersede no historical failures.

## Reproducible commands

Existing environment:

```powershell
Set-Location 'C:\Users\Gianni\Documents\Codex\ASTHRAL_AUTONOMOUS_MISSION_20261115'
$enginePython = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe'
& $enginePython -m pytest engine/tests -q
node --test web-local/tests/*.test.mjs
& $enginePython tools/build_science_integrity.py --check
# A fresh path is required; previous build artifacts are preserved.
$env:ASTHRAL_BUILD_OUTPUT = Join-Path (Get-Location) 'web-local/build-output-team-reproduction'
& $enginePython web-local/build.py
python tools/serve_browser_build.py web-local/build-output-team-reproduction --port 8946
# Separate terminal, sequential browser runs (no parallel acceptance claim):
python tools/browser_acceptance.py --url http://127.0.0.1:8946/ --output work/team-browser-1
python tools/browser_pose_acceptance.py --url http://127.0.0.1:8946/ --output work/team-pose
python tools/browser_public_offline_acceptance.py --url http://127.0.0.1:8946/ --output work/team-offline
python tools/browser_embedding_acceptance.py http://127.0.0.1:8946/
python tools/browser_voice_acceptance.py http://127.0.0.1:8946/
python tools/browser_model_acceptance.py http://127.0.0.1:8946/
python tools/browser_donki_acceptance.py --url http://127.0.0.1:8946/
```

A clean machine needs Python >=3.11, the engine test/integration requirements from engine/pyproject.toml, Node 22+ and fake-indexeddb 6.2.4 (`npm ci` in web-local). Browser harnesses additionally need Python Playwright and a compatible Chromium; the current diagnostic scripts select the locally installed chromium-1181 explicitly. Install the supported Playwright browser or adapt that documented executable selection; no security flags are necessary. The build uses pinned Pyodide downloads with TLS verification when its vendor cache is absent. Tracked prepared voice chunks/runtime and permitted fixtures avoid a requirement to install native Vosk or Ollama for this browser build. Optional pose regeneration: `python tools/install_browser_pose.py`; it verifies the npm/model/license hashes and rejects conflicting assets. Native CV and native voice extras are separate optional dependencies, not core prerequisites.

Keep the browser's exact origin for profile storage; a different port/domain is a different vault. Existing user exports/profiles are never overwritten to repair public assets. Do not upload project-root databases or credentials to a static host. No publication is part of this feature-branch review.

## Priorities and validation limits

1. Trace/reproduce parallel navigation failures and quantify load/resource behavior without changing security controls; require declared concurrency acceptance before operational claims.
2. Complete the currently unaccepted private-profile/clinical/radiation/sleep browser workflows through an authorized execution path; preserve original rejection evidence.
3. Validate Qwen on an ordinary WebGPU-capable browser/device; retain unsupported fallback elsewhere.
4. Independently review and expand licensed primary-source retrieval with a held-out, human-graded relevance/faithfulness benchmark.
5. Acquire compatible licensed vision inputs and independent annotations; validate actual physical capture/playback and camera cleanup. Echo rights block remains.
6. Finish audited nutrition correction/supersession and additional reviewed dataset categories after current evidence review; do not silently rewrite history.
7. Independent biomedical, security and operational review. Software tests do not establish clinical validity, exercise safety, sensor authenticity or flight readiness.

Native SQLite remains unencrypted. Browser vault ciphertext protects stored private data under its existing design but labels/metadata remain visible, plaintext exports leave the vault, OS/same-origin compromise can expose memory, and an attacker controlling storage can rewrite/roll back an unauthenticated audit history. Worker fetch guards are not a process sandbox or OS firewall. Separate process isolation and trusted audit anchoring remain pending. Neither these tests nor Codex constitute independent clinical validation.


## Final candidate verification

- Build: web-local/build-output-integration-candidate-20261115, 104 assets / 140,660,076 bytes; every manifest size/SHA-256 and original source asset compared successfully. Both nutrition versions are byte-identical inside engine.zip, interpreter caches are excluded, MediaPipe license accompanies redistributable runtime/model. Manifest SHA-256 `d1b9f710cc199d9f0ecf7cce286a872304ac7f30e6fcf8d801dded44cbc3f644`. Report: work/integration-candidate-build-verification.json. The build verifies byte integrity, not bit-for-bit ZIP reproducibility across timestamps/toolchains.
- Complete final Python suite: **932 passed, 19 skipped, 1 warning, 184.02 s**, work/integration-candidate-pytest.txt. Skips are not passing optional-runtime acceptance. The warning is existing Starlette/httpx TestClient deprecation.
- Complete JavaScript suite: **91 passed, 0 failed**, work/integration-final-reviewed-node.txt (21.01 s during concurrent test activity). Earlier 90-test run predates the cross-offset checkpoint regression.
- Two independent final-candidate normal Chromium workflows: work/browser-acceptance-candidate-1 and -2; each has zero page, console and request errors. Engine readiness 2.43 / 2.24 s. Both cover the named USDA alternatives, meal/fluid demo save, exercise lifecycle and route opening. They are explicitly partial-workflow acceptance, not a complete mission or durable private-profile test.
- Final-candidate genuine CPU pose: work/browser-pose-candidate, three clips executed and exported, zero page errors; same tracking-loss outcomes shown above. No reference biomechanical accuracy or physical capture test.
- Final-candidate offline public test: work/browser-public-offline-candidate, **73 required public files verified**, controller reload, then network-disabled reload and genuine local lexical citations, zero page/request errors; Python readiness 1.72 s. Optional pose/model/voice caches are separate from these 73 required files. The test waits for in-flight navigation work to settle before disconnecting; older warning reports are retained.
- Screenshots are actual application states, including the full pose overlay, USDA method preview and network-disabled citation view. Viewport widths do not certify physical phones. Measured startup figures are observations, not mission latency/energy guarantees.

Screenshot capture in the three primary acceptance harnesses now records capture errors independently with a bounded timeout, so an unavailable font/screenshot cannot overwrite the original workflow failure report. No application response or model inference is intercepted.


Final-candidate optional-model reports: work/browser-embedding-acceptance/report.json confirms 586 real CPU vectors and source-labelled retrieval with no recorded page/request errors; work/browser-voice-acceptance/report.json confirms 73 required public files and the six real Vosk recognitions (five exact, sleep unresolved, zero records saved); work/browser-donki-acceptance/report.json records 40 live public records, 29 to 28 unacknowledged notices and acknowledgement persistence, with two ERR_ABORTED entries retained. Voice processing took 1.18–2.38 seconds per fixture in this run. No TTS or physical microphone claim is made. Model capability remains BLOCKED_NO_WEBGPU_ADAPTER in work/browser-model-acceptance/report.json; this is a demonstrated unavailable adapter, not a generation success.
