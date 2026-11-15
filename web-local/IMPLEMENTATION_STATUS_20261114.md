# Browser candidate status — 2026-11-14

This document supersedes old prototype feature/test counts in README.md for the current **uncommitted feature/browser-complete-release** candidate. It is not a final release declaration. Original Python clinical source, Ollama and Norton remain unchanged.

## Verified software
- Original backend suite: 782 passed, one warning, 264.77 s; log `work/browser-local/backend-final-regression.txt`.
- Current browser suite: 44 passed, zero failed, 5728.86 ms; log `work/browser-local/browser-final-tests.txt`. Tests run in Node with actual Pyodide/WASM; encryption tests use fake-indexeddb. These are not physical-device tests.
- 254 exact canonical clinical hashes match native CPython, including original 30 cases, six hypoglycemia boundaries, frozen mission snapshots and insufficient/invalid/contradictory variants. Twelve descriptive statistical fixtures retain native behavior.
- Full original monitoring cycle, personal baseline, trends, events, episode/follow-up, resource/context versions and frozen replay run through a thin browser adapter using original Python services and SQLite. Native monitoring output hash matches WASM. Foreign ownership, immutable device changes and failed-restore locking are tested.
- Missing/optional/invalid/protocol-safety fields remain separate. Authorization and clinical execution remain blocked. Human management reports do not establish treatment, verification or recovery.
- Explicit UTC input parsing avoids local-device timezone shifts. Invalid timestamps reject before persistence.
- Expanded original approved retrieval source set: seven documents, 566 raw chunks, integrity verified; original English presentation/generation guards apply. Raw chunks are not equivalent to primary clinical papers. Model-based retrieval quality review remains pending.
- Original assistant safety contracts and typed numeric finite grammar validate read-only generated explanations against existing engine facts; changed patient values and unsupported clinical claims reject. Model execution acceptance is a separate gate. A live 0.5B inference completed (36.51 s model initialization; TTFT 2.05 s; generation 4.26 s; runtime decoding 7.76 tokens/s), but that answer failed deterministic validation and was withheld. Inspection then found the original response schema/token budget were not forwarded to WebLLM; corrected and covered by two worker-contract regressions. The subsequent cold load failed in WebLLM Cache.add(), which bypasses the overridden fetch and attempted a duplicate download. The current worker seeds the original WebLLM model/config/WASM cache scopes exclusively with just-verified pinned bytes before initialization. Two regressions verify correct cache admission and failure before initialization for corrupted bytes. Corrected live inference acceptance remains in progress. API reference: https://webllm.mlc.ai/docs/user/api_reference.html ; bundled 0.2.79 runtime was also inspected for schema support.
- Cache installation shows adjacent progress/errors and bounded waits, and requires verified worker acknowledgment. Cloudflare's index redirect response is normalized for cached navigation. Actual HTTPS install, online reload and local assessment succeeded on preview `https://decec363.asthral-web.pages.dev/`.

## Implemented, acceptance pending
- Structured astronaut UI for measurements, monitoring, episodes, follow-up, mission context, resources and unverified management reports; Developer View retains raw trace. Comprehensive visual/manual workflow review remains in progress.
- Encrypted local profiles, lock, export/recovery and revision conflict protection: software tests pass; physical restart/device recovery and eviction behavior need owner acceptance. No remote identity or password reset.
- Genuine optional WebLLM Qwen2.5-0.5B and Qwen3-4B support; public downloads now resumable and integrity checked. Prior prototype 0.5B desktop inference succeeded, but new-context/resumable candidate benchmarks remain pending. No current 4B success is claimed. Windows Ollama model is separate and preserved.
- MiniLM L6 public-document vectors plus independent verified vector retrieval and lexical fusion. Actual MiniLM index build completed with 566 scientific vectors: initialization 0.556 s, index 35.570 s in the desktop browser. A DKA safety query retrieved the implementation contract plus the distinct clinical research synthesis with verified hashes. This is a source-hit example, not broad clinical retrieval validation.
- Vosk local English runtime: corrected generated CSP wrappers and explicit finalization, original parser and guarded duration-only automatic-save policy. Actual HTTPS CSP-safe Vosk initialization succeeded. Six synthetic audio fixtures ran in the real browser: heart rate 82 beats/min, temperature 37.2 Cel, blood pressure 120/80 mmHg, negation and question preserved expected parsing; sleep misrecognized “as” as “a”, remained unresolved and was not saved. All six had explicit worker finalization and saved no observations. Physical microphone acceptance is pending. Typed reviewed self-reports are the fallback. No real audio or clinical data are used.
- Local browser English TTS only; disconnected playback/device voice availability remains pending.
- Optional fixed-topic PubMed metadata with consent, bounded output and mode cancellation; private questions never become search queries. Actual live browser CORS retrieval succeeded for the fixed 2024 hyperglycemic-crises topic, returning three clearly unreviewed metadata entries. Independent network capture acceptance remains pending.
- Fetch instrumentation blocks private synthetic sentinel transmission on its covered paths. It is not independent packet capture or an OS privacy guarantee.

## Release blockers and remaining delivery
Samsung previously reported an unresponsive installer and then a failed online reload. The online reload defect was reproduced and fixed. The owner has the new immutable URL for retest. The owner subsequently reported **“funcionó sin internet”** for corrected preview decec363. Physical Samsung offline loading is therefore owner-reported successful; no instrumented trace or specific assessment output was supplied. iPhone/Safari and optional-model offline acceptance remain pending. No candidate promotion is justified by test counts alone.

Actual deployed HTTPS 254/254 parity, seeded monitoring replay, a human follow-up plan and a reviewed typed heart-rate report succeeded on decec363. Reports and captures are being preserved under C:/Users/Gianni/Documents/Codex/ASTHRAL_WEB_FINAL_REVIEW_20261114.

The final screenshot gallery, complete functional/security reports, current model benchmarks, final review ZIP and audited Git commit/push are not yet complete. Do not present older artifacts as evidence for this candidate. Compatibility emulation is not a physical Samsung/iPhone test.

Security/clinical limits: original Windows SQLite remains unencrypted; browser ciphertext does not protect an unlocked compromised origin/OS; storage attackers can rewrite/rollback audit chains; browser storage may be evicted; retain encrypted backups and passphrases. No clinical or operational validation follows from synthetic software tests. Independent professional review and appropriate studies remain necessary.

## Repeat tests
From `C:/Users/Gianni/Desktop/Vigile` in PowerShell:

```powershell
$asthralNode = 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
& engine/.venv/Scripts/python.exe web-local/prepare_voice.py
if ($LASTEXITCODE -ne 0) { throw 'Voice preparation failed' }
& engine/.venv/Scripts/python.exe web-local/build.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$env:FAKE_INDEXEDDB_MODULE = 'file:///' + ((Resolve-Path 'work/browser-local/toolchain/node_modules/fake-indexeddb/build/esm/index.js').Path.Replace('\','/'))
& $asthralNode --test web-local/tests/*.test.mjs
& engine/.venv/Scripts/python.exe web-local/serve.py
```

Local preview binds loopback only (see serve.py for port). A clean checkout needs the documented pinned public runtime/model preparation and fake-indexeddb 6.2.4; large generated assets are intentionally excluded from Git. Never publish the project root or personal databases. Installation first needs connectivity; optional speech/AI assets are separate explicit downloads. Exact incident details and test distinctions are in OFFLINE_INSTALL_AUDIT.md.

Actual alias migration recovered a previously broken cached root: install update → waiting state → lock temporary profile → activate → reload succeeded. The preexisting encrypted Synthetic final acceptance A profile remained listed and locked; its passphrase/database were not altered. One manifest request initially timed out under concurrent optional loads; retry after releasing test workers succeeded.
