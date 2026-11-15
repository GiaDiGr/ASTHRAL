# ASTHRAL local integration continuation — 2026-11-15

## Scope and checkout

This report records work performed only in the existing local checkout `C:\Users\Gianni\Documents\Codex\ASTHRAL_AUTONOMOUS_MISSION_20261115`, branch `feature/asthral-autonomous-mission`, at starting HEAD `256fef85` (`Require explicit selection of USDA energy method`). No remote Git operation, commit, push, deployment, reset, or deletion of existing project artifacts was performed. Existing builds, browser evidence, fixtures, model assets, and untracked work products were preserved.

The task attachment is an implementation directive, not scientific source evidence. This continuation uses `docs/asthral/INTEGRATION_REVIEW_20261115.md`, `docs/asthral/SYNTHETIC_MISSION_RUNBOOK_20261115.md`, `docs/asthral/COMPUTER_VISION.md`, `docs/asthral/MOTIONGUARD_BROWSER_20261115.md`, and the machine reports cited below as status evidence. No new clinical threshold, diagnosis, treatment, or flight protocol was added.

## Consolidated corrections

- NeuroGuard remains in the existing local prevention journal and same profile/store. The retired 1–5 legacy wellbeing form remains readable for old records; it no longer creates duplicate new mood/stress entries.
- Linked sleep data must resolve to a sleep record owned by the same local profile. A NeuroGuard session can be deleted only through the scoped, auditable prevention deletion path.
- The app now displays the actual selected sleep record state after rerendering; the previous selection-reset bug was reproduced in a browser and corrected.
- NASA-TLX stores the six official dimensions and validated pairwise choices. The pair order is randomized for each completion; scores are kept distinct from the 0–100 ratings and are described as self-report, not diagnosis.
- PVT-B lapse cutoffs remain limited to PVT-B. Generic reaction-time tasks no longer receive PVT-B-specific lapse labels. Median summaries use the conventional average of the middle pair for even sample sizes. 1-back sequence validation rejects boolean indexes and preserves the intended generated transition count. Go/No-Go output distinguishes no-go trials from correct rejections.
- NeuroGuard export quotes CSV cells and prefixes formula-like text to prevent spreadsheet formula injection. An active test can be stopped and discarded without saving incomplete measurements.
- Browser mission data export is a separate, opt-in, aggregate-only JSON for the disposable synthetic demo. It counts only explicitly marked synthetic measurements and rows linked to those measurements. It does not contain profile or record identifiers, values, notes, clinical findings, references, or treatment records. Persistent profiles continue to use the encrypted profile backup.
- Mission context, prevention, exercise, NeuroGuard, radiation, references, and deterministic monitoring remain in the existing app and storage architecture; no second health database or real LLM was added.

## Acceptance results

All figures below come from distinct machine runs dated 2026-11-15. Browser fixtures are synthetic unless identified as public NASA event metadata. Passing software tests do not validate a clinical or operational decision.

| Area | Actual result | Boundary |
|---|---|---|
| Static browser build | `web-local/build-output-neuroguard-mission-summary-final2-20261115`; **107 files / 140,710,182 bytes**, 254 parity cases, clinical modules `BYTE_IDENTICAL` | File integrity and engine parity fixtures; not bit-for-bit archive reproducibility or clinical validation. |
| Python suite with skip reasons | **947 passed, 19 skipped, 0 failed**, 1 Starlette/httpx deprecation warning, 200.81 s; `work/integration-final-pytest-skip-reasons-20261115.txt` | Run against current source with the Python environment at `C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv`; the system Python lacks FastAPI. The skipped tests remain unverified optional paths. |
| Node suite | **99 passed, 0 failed, 0 skipped**, 11.08 s; `work/integration-final-node-20261115.txt` | Includes six NeuroGuard regressions and two aggregate mission-summary filtering tests. Node emitted existing `MODULE_TYPELESS_PACKAGE_JSON` warnings because package metadata has no `type: module`. |
| Focused NeuroGuard Python tests | **48 passed** | Unit/API-level evidence only; see the full-suite result for the complete count. |
| Synthetic mission browser E2E | `SYNTHETIC_CROSS_MODULE_MISSION_FLOW_FOLLOWUP_AND_ENCRYPTED_EXPORT_PASSED`; **14 workflow steps**, 20.780 s total, Python runtime ready in 4.247 s, one personal-baseline control, two visible synthetic follow-up cards; report and screenshots in `work/browser-mission-integration-20261115-final3/` | Opens a disposable demo; no real clinical records. Confirms pending follow-up, not completion or recovery. No page errors, console errors, or failed requests. |
| Mission-summary export | Browser downloaded `synthetic-mission-summary.json`; counts were 5 synthetic measurements, 1 linked baseline, 1 monitoring cycle, 2 linked follow-up plans, 10 marked prevention entries and 3 marked radiation records. The report contained no measurement values or identifiers. | Aggregate software summary only; not a clinical report, not clinical validation. Only explicitly marked synthetic rows are counted. |
| Radiation export | Browser downloaded three synthetic records to `synthetic-radiation-export.json`, with `sensor_verified:false` | Plaintext and scoped to the synthetic fixture. This is not a personal dose report. |
| Encrypted backup | A separate ephemeral browser context created an empty local test profile and downloaded `ASTHRAL-ENCRYPTED-SQLITE-1` revision 1 with 600,000 PBKDF2-SHA-256 iterations and ciphertext/IV; test email and passphrase were absent from plaintext. Mission summary plaintext export was disabled for this persistent profile. | Confirms the empty-profile export contract only. It did not export the mission fixture or test restore in this run. |
| NeuroGuard browser E2E | `SYNTHETIC_NEUROGUARD_BROWSER_FLOW_PASSED`, 3.034 s; `work/browser-neuroguard-acceptance-final4-20261115/report.json` | Synthetic self-reports/tasks only; no clinical interpretation. |
| Main app browser workflow | `PARTIAL_WORKFLOW_PASSED_NOT_FULL_ACCEPTANCE`; 3.26 s engine readiness, zero page/console/request failures | Confirms demo, exercise lifecycle, USDA alternative selection/search/portion/hydration, and route opening. Not full acceptance. |
| Offline reload on final build | `PUBLIC_CACHE_OFFLINE_RELOAD_AND_LEXICAL_RETRIEVAL_VERIFIED`; **76 public resources** installed, offline engine ready in **2.27 s**, no page errors or failed requests; `work/browser-public-offline-mission-final2/report.json` | Browser public cache only; private-profile recovery was not part of this run. Storage eviction remains possible. |
| Local retrieval | `INDEX_READY_RELEVANCE_NOT_VALIDATED`; 586 source-labelled vectors loaded with no page/request failures | Eight curated implementation/evidence documents; no independently graded held-out relevance or faithfulness validation. |
| Voice | `RECOGNITION_EXECUTED_REVIEW_MISMATCHES`; five of six synthetic WAVs exactly matched transcript and parsed structure | Sleep fixture still transcribes an extra “a”; parser abstains and does not save. Manual review remains required. No physical-microphone claim. |
| WebGPU generation | `BLOCKED_NO_WEBGPU_ADAPTER`; load control disabled under ordinary Chromium | No generation/inference success. CPU retrieval and deterministic calculations remain available. Ollama configuration was not changed. |
| MotionGuard | `GENUINE_INFERENCE_EXECUTED_NOT_BIOMECHANICAL_VALIDATION`; CPU Pose Landmarker ran on three selected clips | 25/75/26 frames; missing angle counts 1/42/26; squat had zero valid knee-angle frames and correctly returned `INSUFFICIENT_TRACKING`. No ground truth, physical camera, or clinical validation. |
| NASA DONKI | `PUBLIC_EVENT_SYNC_ACK_RELOAD_VERIFIED`; 40 public records, acknowledgement persisted 29→28 | Two `ERR_ABORTED` requests remain in the report. DONKI is not personal dosimetry or a real-time crew alarm. |

The full machine reports are retained under `work/`. In particular: `work/browser-pose-neuroguard-final-20261115/report.json`, `work/browser-public-offline-mission-final2/report.json`, `work/browser-embedding-acceptance/report.json`, `work/browser-voice-acceptance/report.json`, `work/browser-model-acceptance/report.json`, `work/browser-donki-acceptance/report.json`, and `work/browser-mission-integration-20261115-final3/report.json`. Failed intermediate mission test attempts were caused by stale expected text, overly strict Playwright selectors, and an overly broad synthetic follow-up filter; the final export now counts follow-up rows only when their IDs and episodes are referenced by a synthetic monitoring run. The final mission E2E passed. The sleep-selector issue was an application defect and is included in the correction list.

The final pytest `-rs` pass identifies all 19 skipped cases: **2** personal-account cases lack `argon2`; **13** computer-vision cases require `cv2`; **2** computer-vision checkpoint cases require `torch`; and **2** native voice cases require local speech dependencies unavailable in the test environment. These are missing optional runtime dependencies, not passing model/inference tests. `numpy` and `vosk` are present, but OpenCV, PyTorch, and Argon2 are not. The separate browser Vosk fixture test did execute and is reported above.

## Files changed or added

- Engine and bridge: `engine/vigile/prevention.py`, `engine/vigile/store.py`, `web-local/src/browser_bridge.py`, `web-local/src/app.js`, `web-local/src/experience.js`, `web-local/src/mission-summary.js`, `web-local/src/neuroguard.js`, `web-local/src/neuroguard-metrics.js`, `web-local/src/preventive-experience.js`, `web-local/src/index.html`, and `web-local/src/style.css`.
- Tests and acceptance harnesses: `engine/tests/test_prevention.py`, `engine/tests/test_browser_mission_support.py`, `web-local/tests/neuroguard-metrics.test.mjs`, `web-local/tests/mission-summary.test.mjs`, `tools/browser_neuroguard_acceptance.py`, and `tools/browser_mission_integration_acceptance.py`.
- Documentation: `README.md` and this report. All prior build directories and reports remain present.

## Coverage and open boundaries

| Component | Implemented and exercised | Software coverage | Independent validation needed |
|---|---|---|---|
| Deterministic clinical engine | Existing clinical pathways, four-state evidence model, finding/episode/follow-up generation, frozen replay | Full Python suite; 254 parity cases in the browser build process; clinical modules remain byte-identical in the build | Clinician review of criteria, derivations, applicability, and use; no clinical/flight validation |
| Personal baselines and monitoring | Existing acquisition, quality checks, baseline, time series, context, replay and audit | Synthetic browser flow and full engine suite | Sensor calibration, deployment hardware and mission operations |
| NeuroGuard | Mood/energy/tension self-report, KSS, NASA-TLX, simple RT, PVT-B and 1-back/Go-No-Go research tasks through shared prevention history | Python and Node regression tests plus browser E2E | Task timing calibration, validated instruments/workflows, clinical interpretation |
| Local RAG / SLM | Source-hashed retrieval and CPU vector index; generation is separately gated | 586 vectors/retrieval executed | Larger curated corpus and independent relevance/faithfulness review; WebGPU device testing |
| Voice | Local Vosk model and explicit transcript review | Six synthetic fixture runs | Resolve sleep mismatch through UX/manual correction; accents, physical microphone and environment |
| Vision | MotionGuard CPU pose inference; image intake remains available | Three real CPU inferences with abstention on poor tracking | Skin lesion weights and dataset absent; browser Ocular OCT inference absent; Echo checkpoint rights unresolved; no physical/clinical labels |
| Space context | NASA public DONKI and synthetic radiation are separately labelled | 40 public records and isolated synthetic export | Verified crew dosimeter integration and mission data authority |
| Persistence/security | Browser encrypted local vault; scoped APIs; audit chain; ciphertext backup | New-profile export tested; existing unit/integration tests | Private-profile restore/migration acceptance; OS process isolation; trusted external audit anchoring |

## Security, reproducibility, and limitations

- SQLite used by the native engine is not encrypted at rest. Browser profile storage uses the existing PBKDF2-SHA-256/AES-GCM design, but profile labels and some metadata remain visible. Plaintext exports are intentionally possible for selected research modules and require careful handling.
- An attacker able to modify or roll back the local database can also rewrite an unanchored audit chain/checkpoint. Hash chaining detects ordinary accidental changes; it does not protect against a storage-controlling attacker.
- Browser worker boundaries are not OS process isolation, a hardware security boundary, or a firewall. A same-origin compromise can access decrypted in-memory data. Hardened process isolation remains future work.
- Offline browser cache is subject to eviction. Keep an encrypted profile backup before moving devices. No cloud sync is implemented.
- 19 Python tests were skipped. Full skip-reason breakdown is in the pytest log; a passing suite is not a replacement for optional model tests.
- Energy, peak memory, thermal load, battery use, low-resource mission operation, concurrency and physical-device behavior were not measured comprehensively. Browser timings are workstation observations only.
- The app is not clinically, operationally, or flight validated. No Codex activity constitutes independent medical review.

## Reproduction on this checkout

PowerShell, from the repository root. Use a fresh output directory; retain all previous outputs.

```powershell
$py = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe'
& $py -m pytest engine/tests -q -rs
$node = 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
& $node --test web-local\tests\*.test.mjs
& $py -m py_compile tools\browser_mission_integration_acceptance.py
$env:ASTHRAL_BUILD_OUTPUT = Join-Path (Get-Location) 'web-local\build-output-neuroguard-mission-summary-repro-20261115'
& $py web-local\build.py
python tools\serve_browser_build.py $env:ASTHRAL_BUILD_OUTPUT --port 8956
```

In a second PowerShell window:

```powershell
python tools\browser_mission_integration_acceptance.py `
  --url http://127.0.0.1:8956/ `
  --output work\browser-mission-integration-20261115-repro
```

The report JSON contains step results and local download artifacts. It does not contain an assistant-generated medical explanation. Existing browser scripts for offline, RAG, voice, model capability, DONKI, and pose are run separately so their statuses are not conflated.

## Integration recommendation

The local frontend can integrate with the existing deterministic engine and optional modules as a **software research prototype**, subject to the limits above. Treat each module according to its machine status; unavailable computer-vision weights and WebGPU generation remain unavailable. Any clinical or flight use requires independent clinical and operational review, criterion sign-off, validated sensors/data collection, privacy/security review, and mission-authority approval. No external publication or GitHub update was performed by this continuation.
