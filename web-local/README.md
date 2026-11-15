> Current release-candidate evidence: see [Mission Control integration](../docs/asthral/MISSION_CONTROL_INTEGRATION.md), [NASA data and anatomy integration](../docs/asthral/NASA_DATA_AND_ANATOMY_INTEGRATION.md), and [integration contracts](INTEGRATION_CONTRACTS.md). This checkout is a local feature branch; release statements must use the fresh verification artifacts from the current run.

# ASTHRAL Web — browser-local integration prototype

> This application is a biomedical and mission-control research prototype. All health and EVA demonstration values are synthetic. NASA archive data are clearly marked as historical environmental instrument observations. Software tests do not constitute clinical, operational, radiation-safety, or flight validation.

Review date: 2026-11-15. The checked-out release branch is developed and tested locally before any deployment. Do not infer that a previous public static URL contains this candidate until a deployment has been independently checked.

## Architecture and boundaries

One browser-local HTML/CSS/JavaScript application. A dedicated Worker loads Pyodide 0.29.3 and runs byte-identical selected Python clinical modules with Pydantic and SQLite. The original Windows FastAPI backend, Ollama configuration and Git history remain intact. Clinical assessment does not require a remote clinical server. A narrowly scoped Cloudflare Pages Function proxies public, historical NASA RadLab GET queries through a fixed upstream; the local preview implements the same allowlisted proxy in Python. No D1 database or remote inference endpoint is used by the browser clinical engine. Static hosting does not require the owner's computer to remain powered on; device/offline checks must be reported for the device actually tested.

Seven pathways: diabetes, DKA, adult diabetes-related hypoglycemia, orthostatic hypotension, POTS, AKI and anaphylaxis; original differential logic is retained. Urgency, confirmation, missing/invalid data, alternative branches and protocol safety are separate original output fields. No therapeutic execution is exposed. The browser rejects measurement_bindings rather than pretending that full acquisition integration has been ported. Research baselines and trends use the original algorithms and quality checks. Full autonomous monitoring orchestration, device integration, episode/follow-up workflows and resource accounting remain on the reference backend; their complete browser migration is PENDING.

The demo uses an ephemeral in-memory SQLite profile. Persistent local profiles encrypt serialized SQLite with AES-256-GCM and PBKDF2-SHA256 (600,000 iterations, random salt/IV), storing ciphertext in IndexedDB. Keys are nonextractable and only retained while unlocked. Profile ownership is checked on restore; CAS revisions reject stale-tab writes. Export/recovery is encrypted and requires the passphrase. There is no remote account or password reset. A lost passphrase, eviction, cleared browser storage or lost device can cause permanent loss without a usable encrypted backup. Labels/identifiers and KDF metadata remain visible locally.

The original Windows SQLite database is NOT made encrypted by this browser implementation. Browser encryption does not protect an unlocked page against same-origin malicious scripts, compromised extensions/OS, memory inspection or a malicious future deployment. Audit chains detect accidental changes but an attacker controlling storage/code can rewrite a chain or roll it back. Independent security review and process/device isolation remain necessary.

## Earlier verification snapshot

The metrics immediately below are historical evidence from the 2026-11-14 browser candidate, not current release acceptance. Use the current dated Mission Control integration record and attached JSON artifacts for the latest run.

* Original backend: 782 passed, one Starlette/httpx deprecation warning; 688.39 seconds (existing full-suite log archived). Reference backend source unchanged.
* Browser tests: 12 passed, zero failed; actual WASM parity, serialized SQLite/ownership/audit, original statistical algorithms and voice parser; WebCrypto/IndexedDB isolation, encrypted recovery, tamper failure, stale-tab rejection and lock races; public-vector validation/version gates. IndexedDB unit tests use fake-indexeddb; they are not a physical browser restart test.
* 86/86 exact canonical clinical output hashes match CPython, in Node's actual WASM runtime AND in the deployed HTTPS IAB Chromium browser. Inputs: original 30 cases, six hypoglycemia boundary inputs, 50 frozen synthetic mission snapshots. Twelve baseline/trend fixtures match the native algorithms. No clinical criteria were changed.
* Deployed DKA regression: known diabetes, glucose 180 mg/dL, beta-hydroxybutyrate 4.2 mmol/L, venous pH 7.22 => CRITERIA_MET, missing_required empty; bicarbonate and urine ketones optional_not_measured; potassium independently required_for_protocol_safety and protocol BLOCKED_MISSING_DATA.
* Actual browser local model: Qwen2.5-0.5B-Instruct q4f16 via WebLLM 0.2.79, WebGPU. Download approximately 280 MiB; initialization after download 41.85 s; TTFT 2.915 s; response 10.159 s; runtime decoding 3.054 tokens/s, prefill 182.063 tokens/s. One verified exact source quotation accepted. These are desktop observations, not mobile guarantees. 22 streamed chunks are NOT 22 tokens.
* Qwen3-4B browser download interrupted at about 420 MiB (Failed fetch). Successful 4B browser load/inference remains PENDING. Windows Ollama vigile-qwen3-4b:latest is preserved and separate.
* Actual MiniLM-L6 q8 WASM model loaded; six public scientific vectors persisted. Warm-cache initialization 0.478 s, index build 0.556 s. No retrieval-quality or clinical validity conclusion follows from six chunks. Browser index is separate from the Windows L12 index.
* Installed local-origin app reloaded and recomputed 86/86 while its static server was stopped. Encrypted profile recovery and audit also worked. This proves origin-unavailable operation in that browser, NOT an OS airplane-mode/network-disconnection test. First installation/model downloads need connectivity.

## Retrieval, voice and fallback

Original BM25 verifies source excerpt hashes. Optional MiniLM reranks only verified lexical candidates using versioned RRF; absent/stale/malformed indexes fall back to lexical retrieval. Only six chunks from project-authored ASTHRAL_LOCAL_KNOWLEDGE.md are bundled. This is implementation documentation, NOT the full clinical literature or a guideline corpus. Broad multilingual/scientific retrieval acceptance, held-out evaluation and complete licensed evidence migration remain pending. The source citations point to preserved local source metadata; outputs never authorize treatment.

Optional local text generation is constrained to an exact substring of a verified retrieved source, otherwise hidden and replaced by extractive results. It cannot edit clinical rules, diagnoses, authorization or records. This deliberately limits conversational capability. No PubMed requests or cloud inference occur in this browser prototype.

Vosk English model chunks and a consent-based AudioWorklet capture path are implemented. Actual browser recognizer initialization FAILED in this review, with a visible local fallback. End-to-end microphone/file transcription is therefore NOT VERIFIED; automatic persistence is disabled pending recognizer-finalization review. Reviewed typed self-reports work and retain SELF_REPORTED_TYPED provenance, separate from sensor measurements. Voice, if enabled successfully later, remains SELF_REPORTED_VOICE and requires review. Browser speech synthesis/offline TTS acceptance is pending. Do not treat the native Windows voice stack as mobile support.

FULL enables explicit optional downloads. LOW_POWER/CRITICAL terminate optional inference and speech workers; clinical computation and lexical references remain. These policies are software controls, not measured thermal/energy optimization. Peak GPU/native memory, battery and thermal performance were not measured.

## Reproduce on Windows

From PowerShell at the ASTHRAL repository root, use the checked-out Python environment and Node 24+:

```powershell
$asthralNode = 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$env:ASTHRAL_BUILD_OUTPUT = Join-Path (Resolve-Path 'web-local').Path 'build-output-local-review'
$env:ASTHRAL_TEST_DIST = $env:ASTHRAL_BUILD_OUTPUT
& engine\.venv\Scripts\python.exe web-local\build.py
Push-Location web-local
& $asthralNode --test (Get-ChildItem tests -Filter '*.test.mjs' | ForEach-Object { $_.FullName })
Pop-Location
& engine\.venv\Scripts\python.exe -m pytest engine\tests -q -rs
# Start the local preview in another PowerShell window; it binds to loopback only.
& engine\.venv\Scripts\python.exe web-local\serve.py --root (Split-Path $env:ASTHRAL_BUILD_OUTPUT -Leaf)
```

Open http://127.0.0.1:8960/ . On another machine install Python 3.13, Node 24+, and the locked engine and browser-test dependencies. Build downloads use TLS verification and official pinned artifacts; runtime hashes fail closed. `prepare_voice.py` requires the separately obtained, pinned local English Vosk files; it does not download model weights automatically. Generated build output is excluded from Git. Frozen synthetic input JSON files are committed; builds do not read a development database.

```powershell
$browserPython = 'C:\Users\Gianni\AppData\Local\Programs\Python\Python313\python.exe'
$chrome = Join-Path $env:LOCALAPPDATA 'ms-playwright\chromium-1181\chrome-win\chrome.exe'
& $browserPython tools\browser_final_mission_control_acceptance.py --root $env:ASTHRAL_BUILD_OUTPUT --output work\browser-mission-control-review --chrome $chrome
# Local preview endpoint uses the same constrained NASA proxy contract.
& engine\.venv\Scripts\python.exe web-local\serve.py --root (Split-Path $env:ASTHRAL_BUILD_OUTPUT -Leaf)
# Cloudflare Pages requires Wrangler to publish the Functions directory. Check `whoami` first;
# deploy the reviewed build only, from the web-local project directory after local acceptance.
```

For a clean checkout, install pinned browser test dependencies with `npm ci` in `web-local`; install Wrangler in a separate local toolchain if deployment is authorized. Pages Functions must be deployed together with the static assets from the `web-local/functions/` directory. Never deploy the repository root, profiles, databases, tokens, or downloaded private model weights. Interactive OAuth credentials stay in Wrangler's user configuration and are never committed.
## Acceptance checklist for physical devices

PENDING on Samsung Galaxy S22 Ultra/Android Chrome, iPhone Safari, iPad Safari, macOS Safari and other physical tablets. Responsive Chromium viewports are visual tests, not those devices. No claim that all phones support WebGPU or have enough memory for 4B. Minimum essential capabilities: secure HTTPS, WebAssembly, Worker, WebCrypto and IndexedDB; service workers/storage availability are checked. The site can explain unsupported optional features without disabling clinical computation.

1. Open the stable URL; run feasibility and parity (expect 86/86). Explore synthetic demo; evaluate DM-05 and check independent potassium safety.
2. Create a synthetic persistent profile with a unique passphrase; save an evaluation and a reviewed typed report; verify audit. Export an encrypted backup.
3. Close ALL tabs and restart browser, unlock and verify saved history. Test a second profile and wrong passphrase. Recover exported synthetic data on an isolated browser/device; do not delete valuable profiles.
4. Install offline resources, wait for success, then use airplane mode and disable Wi-Fi. Reload, unlock, recompute and retrieve local references. Model assets must be installed separately beforehand.
5. Explicitly load the smaller model first if WebGPU is supported. Measure init/TTFT/tokens/s and resource/thermal behavior on that actual device. A failed model must leave the engine usable. Do not infer support from viewport size.
6. Switch LOW_POWER/CRITICAL; verify lexical and clinical fallback. Lock profile and verify private results disappear. Updates require a locked profile and explicit activation; old public caches may remain until browser cleanup.
7. Voice remains experimental/failed in desktop review: do not claim microphone acceptance until explicit consent, stop/cancel/lock, transcript accuracy/provenance and finalization tests pass. Typed input is the supported fallback.

## Team contracts and layout

`src/worker.js` serializes requests to `src/browser_bridge.py` dispatch. Actions: init_profile, evaluate, statistics, search, history, serialize, parse_observation, save_observation, parity. Clinical payload uses original ClinicalRequest and MissionContext models; output preserves original dictionaries, including criterion trace and knowledge hash. Ownership is assigned by the unlocked worker profile, never trusted from supplied subject identifiers. Browser adapter failures remain failures/inconclusive; they are not normal measurements. Do not change the original clinical rules in JavaScript.

Frontend: consume preserved output fields; no independent diagnostic calculations. RAG: public verified references and existing outputs only; never grant rule/therapy authority. Optimization: benchmark the same fixtures; optional workers may be terminated, deterministic engine remains critical. Sensors: full measurement acquisition is not yet a browser contract; add a separately reviewed adapter before enabling bindings. Mission Control exposes the existing orbital/EVA flow, historical RadLab adapter and labeled power profiles. `NASA_DATA_SOURCES` records the reviewed RadLab, OSDR Biological Data API, NASA EDA and DONKI boundaries. Original backend API/OpenAPI contracts remain available for existing integrations.

`build.py` packages original selected modules, fixed synthetic fixtures, NASA source registry and optional licensed anatomy model. `functions/api/radlab.js` is the fixed-host same-origin public-data proxy; `radlab_proxy.py` is its local-preview counterpart. `mission-control.js`, `radlab.js`, `radlab-view.js`, `orbital-view.js` and lazy `anatomy-view.js` compose the presentation layer. `runtime-lock.json` pins official runtimes; `src/models.json` pins public model revisions/hashes. `src/vault.js` owns encryption/IndexedDB; `vectors.js` public index; `ml-worker.js` optional inference; `offline-voice.js` experimental voice; `sw.js` public-only versioned caches; tests contain synthetic fixtures. No personal decrypted clinical data enter static caches.

Priorities: physical offline/restart/export acceptance; independent security review; recognizer startup/finalization and actual synthetic audio regression; broader licensed source retrieval evaluation; full monitored-measurement/episode/follow-up port; measured mobile model/resource feasibility. Clinical validation requires independent professionals and appropriate operational studies, not this parity suite.
