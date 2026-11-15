> Startup update: see [BLOCKER_RESOLUTION_20261115.md](BLOCKER_RESOLUTION_20261115.md) for the HTTP/1.1 correction, repeated successful Chromium runs, MIME correction, CPU embeddings and real Vosk tests. Failed runs below remain historical evidence.

# ASTHRAL final integration checklist — 2026-11-15

Branch: `feature/asthral-autonomous-mission`; continuation from `d543cd8846c7a669a014b1c9e25ee07435a02ba8`. No production publication or merge into main. This checklist supersedes any previous implication that browser access itself is unavailable: the current directive authorizes isolated local Playwright execution and it was actually executed.

## Changes and verified scope

- Added fast USDA description/ID filtering without changing the food dataset, portion calculations or null nutrient semantics.
- Added radiation preview through `radiation_preview`. It invokes exactly the same normalizer, ownership and duplicate validation as commit, without writing database/audit state. `radiation_import` repeats validation at commit to detect intervening duplicate writes. Regression test verifies byte-identical database serialization before/after preview and duplicate rechecking.
- Added unit-aware radiation point charts. Separate series are retained for quantity, unit, mode, quality, instrument, segment and location. Invalid readings remain labelled INVALID; they are not used for dose calculations. No lines interpolate unobserved intervals; no new dose or Gy/Sv conversion is introduced.
- Added explicit plaintext JSON exports for radiation and preventive histories. Export is user initiated. The filename/button identifies plaintext output; exported files must be protected separately from the vault.
- Added descriptive sleep-duration range/mean for logged intervals. Missing sleep remains unknown; no recovery score or diagnosis is computed.
- Corrected Windows-1252 encoding in the prevention UI module to UTF-8.
- Hardened worker startup: Pyodide loadPackage can resolve despite failed downloads. Actual pydantic/sqlite3 imports are now required before ready; transient loading is retried twice, then the engine fails closed. Worker tests exercise both recovery and exhausted retries.
- Corrected atomic public resource loading: scenarios and corpus commit to UI state only after both transfers succeed; public JSON requests retry bounded transport/decode failures. This fixes partial initialization causing later attempts to skip an incomplete corpus.
- Added loopback-only public-build server (`tools/serve_browser_build.py`), refusing a directory without the public asset manifest; no repository root or profile database is served.
- Added real headless Chromium smoke acceptance (`tools/browser_acceptance.py`) with console errors, failed requests, desktop/mobile screenshots, nonzero failure exit. A smoke success alone is explicitly not full application acceptance.

## Requirement-by-requirement status

| Directive | Current status and unresolved work |
|---|---|
| 1 Independent workstreams | Ordinary local Playwright works under the new authorization. Do not conflate this with past desktop-control permission. Native Ollama and browser WebLLM are distinct; this pass does not verify generated WebLLM text. |
| 2 Exercise and MotionGuard | Guided manual session selection/sequence/counts/timer/pause/resume/stop/history exists. Browser acceptance pending. Historical workload/exertion comparisons, recovery integration, imported authorized plans and visual movement demonstrations remain incomplete. Genuine pose pipeline is not integrated into this static browser app. Native contributor code is `engine/vigile/computer_vision.py`; native Holistic Tasks model and Python runtime are not a verified browser JS runtime. Exact model/runtime licenses/hashes and install commands are in `COMPUTER_VISION.md`. Permitted representative movement videos and browser-compatible inference pipeline remain required. |
| 3 Nutrition/hydration | Offline 424-food dataset, lookup/scaling, incomplete nutrient totals, daily history and food search exist. Search acceptance pending. Audited correction/supersession and an additional USDA category have NOT been implemented. No food values were invented or source nulls filled. |
| 4 Sleep/recovery/wellbeing | Self-report histories/charts, quality/fatigue and descriptive duration comparison exist; export added. Browser acceptance pending. Combined exercise/recovery timeline analysis, contextual schedule consistency and audited corrections remain incomplete; no recovery/psychiatric score. |
| 5 Qwen | Existing WebLLM loader/cache/validators retained. Genuine current model load, streaming, multi-turn conversation, offline generation and benchmark NOT VERIFIED. Native Ollama unavailability is not proof of WebLLM unavailability. Current browser runtime initialization failure prevents testing app interactions in the present run. |
| 6 Scientific RAG | Existing hybrid retrieval and source hash tests remain; comprehensive source expansion, actual current browser embeddings and held-out scientific answer/faithfulness accuracy evaluation NOT COMPLETED. No accuracy claim is made from the vector index alone. |
| 7 Voice | Existing Vosk adapter, typed fallback and bounded parsing/saving policies retained. Actual voice-to-assistant workflow, current audio-fixture recognition quality, local playback and physical microphone acceptance NOT VERIFIED in this run. |
| 8 CV | Native OCT adapter/model hash `e085d37bc04f716ee3417bbd768fa4aa392a24fb62c0371e066279e6dd7d314a` and Holistic model hash `e2dab61191e2dcd0a15f943d8e3ed1dce13c82dfa597b9dd39f562975a50c3f8` documented in `COMPUTER_VISION.md`. Neither is packaged as a verified browser inference pipeline. Skin intake stays temporary-preview only: longitudinal image storage remains NOT IMPLEMENTED. EchoNet rights/checkpoint restriction preserved. |
| 9 DONKI | Existing categories/details/links/cache/staleness/filter/acknowledgement helpers and tests retained. Current browser acceptance pending. New beyond-FLR live endpoint verification and opt-in foreground browser notifications NOT IMPLEMENTED in this pass. No operational exposure warning is claimed. |
| 10 Radiation | Preview/commit, strict feedback, provenance, uncertainty text, point charts, history, existing gap-controlled integrations and JSON export exist. Browser acceptance pending. Physical CAD/HERA remains unverified. Rich EVA/event-overlaid common-time charts and hardware validation remain incomplete; DONKI annotations stay independent. |
| 11 Dashboard/navigation | Existing unified app retained. Actual login was rendered/captured; initialization failed before demo entry. Full principal-route/mobile interaction audit is NOT PASSED. |
| 12 Synthetic mission | Complete 20-step browser mission is NOT PASSED. No generated model response, pose result or sensor value was fabricated to complete it. |
| 13 Browser acceptance | Executed real local Chromium under new authorization. Package requests intermittently reset (`net::ERR_CONNECTION_RESET`) and initial run lacked pydantic/sqlite3. Exact transport cause is undetermined. No Norton configuration changes, asset renaming, request interception or security bypass were used. See actual run report/screenshots in `work/browser-acceptance-final` and bounded-retry run in `work/browser-acceptance-retry`. |
| 14 Build/tests | Python full suite: 915 passed, 19 skipped, one existing Starlette/httpx deprecation, 366.20 s. Final Node suite: 81 passed, zero failed (12.51 s); full output in `work/final-integration-node.txt`. Build r6: 88 resources, 112931880 bytes, 254 parity cases, clinical modules BYTE_IDENTICAL. Source integrity and final test logs supplied. |
| 15 Classification | Software utility/engine tests pass within their scope. Browser-integrated changes remain SOFTWARE IMPLEMENTED, BROWSER ACCEPTANCE PENDING. Model/voice/pose assertions remain unverified. Additional features explicitly marked incomplete above are SOFTWARE NOT IMPLEMENTED, not hidden behind clinical validation. CLINICAL OR FLIGHT VALIDATION NOT PERFORMED for any feature. |
| 16 Autonomous work | Source/test/report changes preserved on development branch. Stable deployment and main untouched. Outstanding software work remains; this is not a completed-application declaration. |

## Reproduction

Run at repository root with Python 3.13 and installed Playwright (the script can use the existing installed Chromium executable). The engine test environment used here is the existing `ASTHRAL_UNIFIED_WEB_20261115/engine/.venv`, and Node uses the existing pinned fake-indexeddb development dependency.

```powershell
$pythonEngine = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe'
& $pythonEngine -m pytest engine/tests -q
node --test web-local/tests/*.test.mjs
& $pythonEngine tools/build_science_integrity.py --check
$env:ASTHRAL_BUILD_OUTPUT = Join-Path (Get-Location) 'web-local/build-output-final-integration-r6'
# For a new build choose a NEW output directory; build.py protects existing artifacts.
& $pythonEngine web-local/build.py
python tools/serve_browser_build.py web-local/build-output-final-integration-r6 --port 8922
# In a second terminal:
python tools/browser_acceptance.py --url http://127.0.0.1:8922/ --output work/browser-acceptance-retry
```

Next release priority is to identify the actual local .whl connection resets, rerun the honest browser test, then exercise the real flows and optional browser models. Until that succeeds the complete integration gate is failed. Absence of clinical validation does not excuse unrelated unfinished software listed above.

## Browser run observations

The bounded-retry r4 run reached Reference Python engine ready in 22.99 s after a pydantic transfer reset, then failed demo entry when corpus.json reset. A later r5 run failed earlier at pyodide-lock.json. Thus network failures vary across package and public-data requests; a particular missing model or native Ollama is not the diagnosed cause. Transport cause remains undetermined. Final r6 report is recorded separately in work/browser-acceptance-r6; no failed attempt is counted as successful acceptance. No network request interception or alternate transport supplied fake assets.

Final r6 Chromium smoke test: FAILED. Login rendered and desktop/mobile screenshots were captured, but pydantic .whl and engine.zip transfers reset before demo entry. This is a genuine browser integration failure, not a passed software acceptance. The final package hashes and ZIP integrity were independently checked for all 88 manifest entries.
