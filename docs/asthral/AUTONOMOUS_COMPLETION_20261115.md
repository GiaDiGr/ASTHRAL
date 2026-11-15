> Update: the following historical inventory predates the versioned USDA energy-reference correction and CPU browser MotionGuard. Current scope and migration are in NUTRITION_REFERENCE_AUDIT_V2_20261115.md, MOTIONGUARD_BROWSER_20261115.md and INTEGRATION_REVIEW_20261115.md. The historical 329 energy-missing count refers to nutrient 1008 only.

# ASTHRAL software completion audit — 2026-11-15

## Scope and state

Continuation branch: `feature/asthral-autonomous-mission`. Base reference: `9ba4b63bbb2fcc03dc3322e4b8ba1834b5b3885e`. This pass adds local prevention experiences and data adapters to the existing application; it does not replace the reference clinical engine, expand disease routes, alter clinical thresholds, or modify stable deployment. The reference clinical Python modules remain byte-identical in the generated browser package.

The project is **not complete against the entire application prompt**. Synthetic/software checks establish implementation behavior only; they are not clinical, fitness, flight, model, or device validation.

## Software functionality implemented in this pass

- Guided, user-controlled examples for resistance, aerobic, mobility, and coordination; ordered movement cues, optional sets/repetitions/time/workload, optional self-rated exertion (0–10), pause/resume/stop/complete, append-only checkpoints and recovery as paused after an interrupted run. Counts and elapsed time are self-reported; no motion inference or adherence/fitness score is asserted.
- Exercise history and descriptive completion/time summary; offline descriptive charting. No target or clinical interpretation.
- USDA FoodData Central Foundation Foods local subset (424 records) with source-hash verification, server-side item lookup and portion scaling, provenance, and explicit null nutrient handling. Daily totals are marked incomplete when a logged food lacks a source value; partial sums and missing counts remain separate. These are reference-composition estimates, not mission-food intake measurements.
- Hydration entries and daily summed history without a prescribed target.
- Sleep interval validation, derived duration, optional subjective quality and fatigue, history and descriptive duration/fatigue charts. No timezone-based schedule regularity is inferred because source local-zone context is not reliably established.
- Voluntary private-profile mood/stress self-reports and local history; no validated screening scale or diagnosis.
- Strict radiation CSV parser and all-or-nothing audited import. Imported rows are sensor-unverified; Gy/Sv semantics remain separate. DONKI cache/event annotations remain independent and cannot change a radiation record.
- DONKI in-app event-type filters, deduplication, local acknowledgements and acknowledgement history. No background notification or personal exposure alert. Live endpoint coverage in this environment is limited to the documented FLR request; the general interface tests use fixtures.
- A shared chronological view is built from already recorded timeline entries; this does not infer causality or a global health score.
- Stable integration contracts document worker actions, provenance, checkpoint/recovery, missing nutrition values, self-reported exertion/fatigue, CSV import and assistant read-only boundary.

## Acceptance matrix

| Gate / area | Status | Evidence and remaining limit |
|---|---|---|
| A. Existing clinical functionality | IMPLEMENTED AND SOFTWARE-VERIFIED | Existing Python suite, Node/WASM parity suite, reference package byte-identity. No independent clinical validation. |
| B. Prevention | IMPLEMENTED AND SOFTWARE-VERIFIED, browser workflow not verified here | Local exercise, nutrition, hydration, sleep/recovery and voluntary wellbeing views; append-only profile storage contracts and utility/integration tests. No actual browser acceptance in this pass. Exercise guidance is generic project-authored educational material, not a NASA/mission plan. |
| C. Scientific AI/RAG | PARTIAL / BLOCKED BY MODEL AVAILABILITY | Existing bounded hybrid retrieval/corpus tests remain. Corpus is limited and does not satisfy the requested comprehensive evidence library or held-out relevance/accuracy evaluation. Ollama at `127.0.0.1:11434` refused connection during this pass; no genuine Qwen conversation, token timing, memory benchmark or citation UI acceptance is claimed. |
| D. Computer vision | BLOCKED BY RUNTIME/ASSET AVAILABILITY | MotionGuard inference and camera workflow not enabled; verified runtime/weights and exercise fixtures absent. OcularVision inference not verified. SkinGuard stays quality intake only. EchoVision remains disabled under existing rights/checkpoint restriction. |
| E. Space weather | SOFTWARE-PARTIAL; LIVE SOURCE CHECK LIMITED | Public DONKI UI/cache/notice behavior and failure cases tested. One fixed official FLR endpoint was successfully queried over a seven-day interval in the prior run (HTTP 200, five records). No all-endpoint/forecast operational guarantee, browser workflow, personal exposure calculation or background delivery. |
| F. Radiation | IMPLEMENTED FOR LOCAL FILE/RECORD WORKFLOW; HARDWARE BLOCKED | Strict CSV parser, bounded all-or-nothing audited import, quantity/unit validation, separate event annotation, existing integration/counter review. No supported CAD/HERA device interface/test device; no operational radiation safety. |
| G. User experience | NOT VERIFIED IN REAL BROWSER IN THIS PASS | Unit/integration test coverage exists; no visual screenshots, console inspection, or desktop/mobile real interaction evidence. Browser-origin access was denied earlier; no alternate-channel bypass was used. |
| H. Offline | IMPLEMENTED/SOFTWARE-TESTED; CURRENT BUILD NOT DEVICE-ACCEPTED | Service worker and restart/offline tests pass in Node harness. User previously reported offline operation on Samsung for a deployed earlier revision; this newly generated build has not been deployed or re-tested on that device. |
| I. Security | EXISTING CONTROLS RETAINED AND SOFTWARE-TESTED | Local encrypted browser vault and owner-bound actions remain. Risks remain: same-origin/OS compromise; plaintext SQLite outside the browser vault/native backend; audit-chain rewriting by storage controller; JavaScript memory erasure is not guaranteed; process isolation and independent security review are pending. |

## Scientific data and traceability

The added food source is the USDA FoodData Central Foundation Foods October 2026 JSON release. Official download/licensing references and source entry are in `docs/asthral/science/sources.json`. Source archive SHA-256: `dd414cc9f1a132626bad354ef6655972c78b44aff14f16114dc899708663c579`. Bundled catalog SHA-256: `a09e222154963247cbb4f24b0a643385a6f2c5fac26d4aa0956dab34d1d6ad17`. Catalog has 424 foods. Missing nutrient source values are preserved as null; counts are recorded in `PREVENTION_AND_RADIATION_INTEGRATION_20261115.md`.

No new clinical criterion or threshold was added. Exercise instructions are not claimed to be NASA-sourced. General health evidence summaries are educational context only and do not update deterministic rules.

## Verification performed

- Python full suite: **914 passed, 19 skipped, 0 failed, 1 warning** in 701.71 seconds. Warning: Starlette deprecation notice that `httpx` with `starlette.testclient` is deprecated and recommends `httpx2`.
- Node full suite: **76 passed, 0 failed**.
- Targeted perceived-exertion unit tests: **7 passed, 0 failed** (included in the full Node suite).
- Scientific source integrity: `SOURCE_INTEGRITY_OK`.
- `compileall` for `engine/vigile` and `engine/tests`: passed.
- Browser bundle: 86 assets, 112,924,146 bytes, 254 parity cases, `clinical_modules: BYTE_IDENTICAL`; engine ZIP integrity and inclusion of USDA data/hash verified. These are package checks, not browser acceptance.
- Browser-origin UI, current build on physical device, camera/microphone, current Ollama inference: not tested / unavailable; see gates above.

## Outstanding work, prioritized

1. Obtain authorized browser-origin access and perform real desktop/mobile workflows with screenshots, console review and persistence/reload/offline acceptance on this exact build.
2. Restore approved local Ollama availability, then test actual Qwen load, generated conversation, evidence citations, unsupported-question handling, and resource use. Do not infer success from model metadata.
3. Provide licensed MotionGuard/OcularVision weights, documented runtimes and reproducible permitted video/image fixtures; verify genuine inference before exposing controls.
4. Expand and independently evaluate the primary-source evidence corpus with a held-out question set; document relevance failures and memory/latency before describing scientific RAG as complete.
5. Test radiation import/history/export UX in a real browser and obtain a supported instrument schema/test device before hardware claims.
6. Have exercise, nutrition, sleep, psychological wellbeing, dosimetry and space-weather presentation reviewed by qualified domain professionals; keep all clinical/operational actions disabled unless separately authorized and validated.
7. Perform security review of encrypted exports, local storage, process isolation, audit integrity, account recovery and release supply chain.

## Reproduction

From repository root in PowerShell:

```powershell
& 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe' -m pytest engine/tests -q
node --test web-local/tests/*.test.mjs
& 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe' tools\build_science_integrity.py --check
$env:ASTHRAL_BUILD_OUTPUT = (Join-Path (Get-Location) 'web-local\build-output-autonomous-final2-20261115')
& 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe' web-local\build.py
```

The build directory is a local verification artifact. It does not deploy or change the production site.

