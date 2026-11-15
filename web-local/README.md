> Current feature-branch instructions and evidence (2026-11-15): see ../docs/asthral/INTEGRATION_REVIEW_20261115.md and INTEGRATION_CONTRACTS.md. The historical commands/results below predate the 254-case package, real CPU pose/voice checks and versioned USDA energy references. No main deployment is authorized by the current directive.

# ASTHRAL Web — browser-local integration prototype

> Current candidate: see [IMPLEMENTATION_STATUS_20261114.md](IMPLEMENTATION_STATUS_20261114.md) and [OFFLINE_INSTALL_AUDIT.md](OFFLINE_INSTALL_AUDIT.md). Feature counts and limitations below describe the earlier prototype, not the current working tree. The current candidate has 44 passing browser tests and 254-case parity; Samsung offline operation was owner-reported successful on preview decec363. Final release acceptance remains in progress.

Review date: 2026-11-13 (America/Lima). Public static URL: https://asthral-web.pages.dev/ . This is a research prototype using synthetic data only; software tests are not clinical or operational validation.

## Architecture and boundaries

One static HTML/CSS/JavaScript application. A dedicated Worker loads Pyodide 0.29.3 and runs byte-identical selected Python clinical modules with Pydantic and SQLite. The original Windows FastAPI backend, Ollama configuration and Git history remain intact. There is no mandatory clinical server, Cloudflare Function, D1 database or remote inference endpoint. Static hosting remains available independently of the owner's computer; actual powered-off-PC acceptance needs an external physical device.

Seven pathways: diabetes, DKA, adult diabetes-related hypoglycemia, orthostatic hypotension, POTS, AKI and anaphylaxis; original differential logic is retained. Urgency, confirmation, missing/invalid data, alternative branches and protocol safety are separate original output fields. No therapeutic execution is exposed. The browser rejects measurement_bindings rather than pretending that full acquisition integration has been ported. Research baselines and trends use the original algorithms and quality checks. Full autonomous monitoring orchestration, device integration, episode/follow-up workflows and resource accounting remain on the reference backend; their complete browser migration is PENDING.

The demo uses an ephemeral in-memory SQLite profile. Persistent local profiles encrypt serialized SQLite with AES-256-GCM and PBKDF2-SHA256 (600,000 iterations, random salt/IV), storing ciphertext in IndexedDB. Keys are nonextractable and only retained while unlocked. Profile ownership is checked on restore; CAS revisions reject stale-tab writes. Export/recovery is encrypted and requires the passphrase. There is no remote account or password reset. A lost passphrase, eviction, cleared browser storage or lost device can cause permanent loss without a usable encrypted backup. Labels/identifiers and KDF metadata remain visible locally.

The original Windows SQLite database is NOT made encrypted by this browser implementation. Browser encryption does not protect an unlocked page against same-origin malicious scripts, compromised extensions/OS, memory inspection or a malicious future deployment. Audit chains detect accidental changes but an attacker controlling storage/code can rewrite a chain or roll it back. Independent security review and process/device isolation remain necessary.

## Verified results

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

From PowerShell, use the full Node path when Node is absent from PATH:

```powershell
Set-Location C:\Users\Gianni\Desktop\Vigile
$asthralNode = 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
& engine/.venv/Scripts/python.exe web-local/prepare_models.py
# Requires the already-reviewed local English voice files under engine/local_ai/voice:
& engine/.venv/Scripts/python.exe web-local/prepare_voice.py
& engine/.venv/Scripts/python.exe web-local/build.py
# In a separate terminal; preview binds loopback only:
& engine/.venv/Scripts/python.exe web-local/serve.py
```

Open http://127.0.0.1:8960/ . On another machine install supported Node 22+ and the reference engine's Python requirements; use its node executable. Build downloads use TLS verification and official pinned artifacts; runtime hashes fail closed. prepare_voice.py currently requires the original local Vosk files; it does not download missing weights automatically. Binary runtimes/models/dist are intentionally excluded from Git. Frozen synthetic input JSON files are committed; builds do not read a development database.

```powershell
# Existing local toolchain (no global npm required):
$env:FAKE_INDEXEDDB_MODULE = 'file:///' + ((Resolve-Path 'work/browser-local/toolchain/node_modules/fake-indexeddb/build/esm/index.js').Path.Replace('\','/'))
& $asthralNode --test web-local/tests/*.test.mjs
# Clean checkout: install fake-indexeddb 6.2.4 with npm in web-local, then npm test after build.
& engine/.venv/Scripts/python.exe -m pytest engine/tests -q
# Authorized static deployment only; never upload the project root/database:
& $asthralNode --use-system-ca work/browser-local/toolchain/node_modules/wrangler/bin/wrangler.js whoami
& $asthralNode --use-system-ca work/browser-local/toolchain/node_modules/wrangler/bin/wrangler.js pages deploy web-local/dist --project-name asthral-web --branch main --commit-dirty=true
```

The existing local Wrangler is 4.76.0. For a clean checkout, install this version from npm in a separate toolchain. Login is interactive OAuth; no token belongs in source or commands committed to Git. Public deployment uses Direct Upload and does not expose the private repository.

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

Frontend: consume preserved output fields; no independent diagnostic calculations. RAG: public verified references and existing outputs only; never grant rule/therapy authority. Optimization: benchmark the same fixtures; optional workers may be terminated, deterministic engine remains critical. Sensors: full measurement acquisition is not yet a browser contract; add a separately reviewed adapter before enabling bindings. Original backend API/OpenAPI contracts remain available for existing integrations.

`build.py` packages original selected modules and source fixtures; `prepare_models.py`/`prepare_voice.py` prepare pinned public assets. `runtime-lock.json` pins official runtimes; `src/models.json` pins public model revisions/hashes. `src/vault.js` owns encryption/IndexedDB; `vectors.js` public index; `ml-worker.js` optional inference; `offline-voice.js` experimental voice; `sw.js` public-only versioned caches; tests contain synthetic fixtures. No personal decrypted clinical data enter static caches.

Priorities: physical offline/restart/export acceptance; independent security review; recognizer startup/finalization and actual synthetic audio regression; broader licensed source retrieval evaluation; full monitored-measurement/episode/follow-up port; measured mobile model/resource feasibility. Clinical validation requires independent professionals and appropriate operational studies, not this parity suite.
