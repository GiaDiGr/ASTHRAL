# ASTHRAL ultimate implementation traceability

This register maps the 2026-11-15 attached implementation directive and the supplied astronaut-health demo to the existing local release candidate. It records software behavior and external evidence separately from medical, flight, security, or operational validation. Current full-suite and browser results are to be filled from the final fresh run; earlier runs are not release evidence.

## Directive sections 1–29

| § | Requirement area | Status in this candidate | Evidence and material limit |
|---:|---|---|---|
| 1 | Mission objective and preserve current application | Implemented in existing architecture | Existing browser-local workspace and clinical engine remain the host; this is an integration candidate, not a replacement project. |
| 2 | Treat supplied HTML as visual inspiration | Reviewed | Its logging, trend, contextual help and anatomy ideas are inspiration only. The embedded 8.34 MB third-party mesh is not reused; hardcoded clinical labels/thresholds are not adopted. |
| 3 | Prioritize protection, NASA data, 3D, audit and release | Implemented, verified, merged and deployed | Existing encrypted local profile and authorization boundaries remain. Fresh browser, Python, Node, Pages Function and source-manifest checks passed before the GitHub merge and production Pages deploy. |
| 4 | Audit local project and existing implementation | Completed for this task's integration scope | Current branch/work tree was inspected. Historical generated `work/` evidence is preserved and not treated as a current test result. |
| 5 | Modernize a coherent English UI | Existing foundation plus Mission Control integration | Mission Control, source register, power controls, RadLab and anatomy are integrated into existing navigation. A full redesign of every existing route was not repeated in this pass. |
| 6 | Integrate NASA RadLab | Implemented and browser accepted | Fixed-host GET proxy, documented query form, units, timestamps, missing values, filter/range validation, historical/cache labels, plots, ISS coordinates, 3D markers, replay and CSV/JSON exports. The fresh acceptance rendered 1,469 returned records for a one-day historical ISS query. Not individual dosimetry. |
| 7 | NASA DONKI | Existing shared integration retained | Uses the one existing client/cache and the official CCMC base migration. Real events remain context; they do not independently trigger the synthetic EVA alert. |
| 8 | NASA OSDR and other scientific datasets | Evaluated, not imported into clinical monitoring | Biological Data API and EDA are in the source registry. No dataset-specific EDA API was verified; experimental/hardware data are not crew physiology. |
| 9 | Unified scientific source layer | Implemented | `sources.json`, source-integrity hashes, runtime NASA data-source registry, visible source cards, release notes and units/limitations. |
| 10 | Interactive Earth, ISS tracking and mission simulation | Existing implementation retained | Three.js globe and local SGP4 estimate remain separate from simulated spacecraft. No GPS, live vehicle telemetry, station contacts or real ground-station schedule are inferred. |
| 11 | Interactive 3D anatomy | Implemented and browser accepted | Pinned licensed Z-Anatomy muscular GLB, local GLTF/meshopt modules, region selection, laterality, camera controls, export and schematic fallback. Chromium loaded 513 named meshes and verified region selection and export. No clinical localization or anatomy-wide organ model. |
| 12 | EVA Monitoring teammate contribution | Integrated | Marfe/PR #2 implementation and attribution retained; four cards, synthetic scenarios, training alert, completion, report and encrypted local storage use existing services. RadLab context remains separate from EVA alert and dose. |
| 13 | Complete health-monitoring experience | Existing modules preserved; mission E2E coverage partial | Existing health history, deterministic assessment, baseline/trend and reports remain in the app. Anatomical region associations are unavailable unless an explicit localized data contract is added and clinically reviewed. |
| 14 | Astra assistant | Existing read-only assistant retained | This pass does not add LLM/RAG features. Assistant cannot mutate deterministic rules or provide independent clinical authority. |
| 15 | Resource/power modes | Implemented for mission rendering | FULL/LOW_POWER/CRITICAL adjust orbital render caps, pixel ratio, position-update cadence and optional playback. No watts, battery life, thermal load or device energy savings are claimed. |
| 16 | Motivation and engagement | Existing implementation preserved | Existing activity/prevention surfaces are unchanged by this integration; engagement features do not establish health outcomes. |
| 17 | Computer vision, NeuroGuard, local AI and voice | Existing modules preserved | This pass does not retrain, expand or clinically validate these systems. Existing model, hardware, privacy and voice limitations remain in their module documentation. |
| 18 | Complete mission demonstration | Core integration walkthrough passed | Fresh E2E exercised synthetic local profile, Earth/orbit, public historical RadLab and exports, offline cache, resource modes, EVA pause/resume and training alert, end/report, encrypted history recovery, existing health/CV/anatomy routes and mobile layout. It does not automate every cross-module voice, local-LLM or clinical workflow. |
| 19 | Architecture consolidation | Implemented without removing retained capability | Reuses one orbital view, one DONKI client/cache, existing EVA contribution, encrypted profile/history and route system. New RadLab client is limited to its distinct NASA archive API. |
| 20 | Performance optimization | Implemented and measured in browser | Anatomy is lazy-loaded and optional for offline caching; mission renderer rates are capped. On this local Chromium run, the Python engine became ready in 8.99 s, initial observed transfer was 407,501 bytes, Mission Control mount took 1.51 s, and decoded orbital resources totaled 2,342,675 bytes (some Resource Timing transfer sizes were zero due to cache/local serving). Complete static build is 147,551,489 bytes; most optional voice, embedding, vision and parity assets are fetched/used on demand. No physical-power result. |
| 21 | Scientific/editorial review | Implemented for new claims | NASA documentation is cited for units, field coverage, dataset status, DONKI migration and OSDR boundaries. T-EVA/space-agriculture evidence is not used to establish clinical thresholds. |
| 22 | Independent functional/visual audit | Automated visual/browser acceptance passed | Chromium rendered desktop and 390 px mobile views, interactive WebGL2 Earth/anatomy, real historical RadLab query, EVA completion and offline stale-cache behavior with zero unexpected console/page errors or failed requests. This remains a software audit only; no independent clinical review or flight certification was performed. |
| 23 | Requirements traceability | This document | Final run artifacts and residual/pending status are recorded in the release report. |
| 24 | Public deployment | Deployed and remotely smoke-tested | Cloudflare production alias `https://asthral-web.pages.dev/` serves the release; its RadLab Function returned 1,469 historical observations with `no-store`, denied an untrusted Origin with 403 and rejected POST with 405. The deployment-specific URL is recorded in the release record below. |
| 25 | FortiGuard classification | Not submitted | It requires a separate external request and a final stable URL; no request is fabricated or reported as completed. |
| 26 | GitHub consolidation | Merged through a pull request | Commit `9d8e54ad` was pushed without force to the release branch and merged through PR #3 as merge commit `7972e07a`; existing contributor commits remain in history. GitHub exposed no Actions workflows or commit check-runs for the repository. |
| 27 | Final documentation | Updated for local verification | See mission integration, NASA data/anatomy contract, this traceability matrix, current browser report, source registry and third-party notices. |
| 28 | Required deliverables | Local deliverables ready | Features, tests, screenshots, measured performance, release status, limitations and prioritized follow-up are recorded here. |
| 29 | Acceptance gates | Local gates passed; remote gates pending | Local automated/software gates below passed. Deployment and GitHub release gates remain separate and are not claimed complete. |

## Acceptance gates

| Gate | Target evidence | Current result |
|---|---|---|
| App loads and stays in English | Chromium desktop/mobile, no overflow, console and request checks | PASS; 390 px viewport, 390 px document width, zero unexpected console/page errors or failed requests. |
| Interactive Earth renders | Actual WebGL2 canvas and screenshot | PASS; WebGL2 canvas drawing buffer 501×590 px in the tested desktop layout. |
| Orbital estimate is scientifically labeled | ISS propagated estimate versus synthetic vehicle labels | PASS; test surfaced the explicit `SYNTHETIC ORBIT` badge and UTC calculation time. |
| Anatomy operates interactively | Licensed GLB loaded, region selector, anterior/posterior and context export | PASS; 513 named meshes, left upper-arm selector, posterior camera and non-clinical JSON export. |
| NASA RadLab returns and renders data | HTTP query through local fixed-host proxy, historical response, points/coordinates, exports | PASS; local Wrangler Pages Function returned HTTP 200 and 1,469 observations for 2023-01-01; browser chart and globe rendered the 1,469 records with JSON/CSV exports. |
| DONKI stays contextual | Existing shared client and no automatic EVA alert from a real event | PASS in existing automated regression; synthetic training alert remained separately marked. NASA archive context did not enter EVA safety logic. |
| Historical, cached and synthetic data stay distinct | UI labels; offline stale-cache path; synthetic EVA tags | PASS; one expected offline RadLab request failure produced a visibly stale historical cache; synthetic EVA labels remained explicit. |
| EVA ends and stores its report | Start, cards, training alert, end, export/history and encrypted-profile reload | PASS; four cards; pause/resume; report persisted and recovered after reload with encrypted audit verified. |
| Health/baseline/trend paths remain available | Existing route checks and original backend/browser suites | PASS at software level; full Python and browser Node suites succeeded. This is not clinical validation. |
| Power modes apply their documented behavior | 24/12/1 fps caps, lower position-update rate, critical playback disabled | PASS in unit and browser tests; FULL restored after CRITICAL. |
| Existing assistant/CV/NeuroGuard/voice behavior is retained | Existing route and suite regressions | PASS for included tests and route visibility. Optional inference dependencies were absent, so skipped tests do not validate local voice or vision model execution. |
| No unsupported clinical inference is created | Source/result boundary checks | PASS in software contracts; RadLab is excluded from personal dose and EVA alert paths; anatomy export has no localized clinical findings. |
| Public deployment and source URL match tested build | Live public endpoint, Pages Function and build fingerprint | PASS; `https://asthral-web.pages.dev/` and the deployment URL responded with the ASTHRAL title; the production RadLab Function returned 200/1,469 records and preserved its security headers and rejection behavior. |
| FortiGuard status is accurate | No submission is claimed | Not submitted; requires final URL and separate external workflow |
| GitHub release matches tested code | Branch/revision, checks and non-force remote workflow | PASS; PR #3 merged to `main` as `7972e07a`; no force push. There are no configured GitHub Actions workflows/check-runs, so remote CI did not run. |

## Fresh local verification — 2026-11-15

| Check | Result |
|---|---|
| `engine/.venv/Scripts/python.exe -m pytest engine/tests -q -rs` | **957 passed, 19 skipped, 0 failed** in 523.56 s. Skips reflect absent optional `argon2`, OpenCV (`cv2`), PyTorch and local voice dependencies. One Starlette `TestClient`/`httpx` deprecation warning was emitted. |
| Browser Node suite | **137 passed, 0 failed** in 22.18 s using the bundled Node runtime and fresh build directory. All 254 browser/Python deterministic fixtures matched exactly. |
| Fresh build | **254 synthetic cases; 148 files; 147,551,489 bytes; clinical modules BYTE_IDENTICAL** to the reference engine. |
| Chromium mission E2E | **PASS**; zero unexpected console/page errors or failed requests; one expected offline RadLab request failure. The sanitized report and desktop/mobile screenshots are in `docs/asthral/evidence/mission-control-20261115/`. |
| Local Cloudflare Pages Function | **PASS** through Wrangler 4.76.0; HTTP 200, 1,469 normalized RadLab observations for the one-day ISS archive request, `HISTORICAL_QUERY_RESPONSE`, `Cache-Control: no-store`, source header `NASA_OSDR_RADLAB`. |
| Scientific source integrity | `SOURCE_INTEGRITY_OK` with `tools/build_science_integrity.py --check`. |

The local Node runtime was invoked directly because `npm` is not available in this shell's `PATH`. Browser results were collected against a local build, not a public deployment. Timings and payload measurements are observations from this one Windows/Chromium machine; they do not establish performance on Android, flight computers or other hardware.

## Release record — 2026-11-15

- Tested source commit: `9d8e54ad691451eff96f803661d7450103be41c6` on `feature/asthral-mission-control-release-20261115`.
- GitHub PR: [#3 — ASTHRAL release: Mission Control, EVA, NASA data and anatomy integration](https://github.com/GiaDiGr/ASTHRAL/pull/3), merged to `main` with merge commit `7972e07a4530bbe0f3cd32cd61c2d3c24e253407` using the normal merge workflow.
- Cloudflare Pages deployment: `https://7ab50bba.asthral-web.pages.dev/`; production alias: [https://asthral-web.pages.dev/](https://asthral-web.pages.dev/). The feature preview remains at [https://feature-asthral-mission-cont.asthral-web.pages.dev/](https://feature-asthral-mission-cont.asthral-web.pages.dev/).
- Production smoke test: root HTTP 200; RadLab endpoint HTTP 200 with 1,469 observations for 2023-01-01 ISS archive data, `HISTORICAL_QUERY_RESPONSE`, `Cache-Control: no-store`, and `NASA_OSDR_RADLAB` source header; untrusted `Origin` returned 403 and POST returned 405.
- GitHub reported zero configured Actions workflows and zero commit check-runs for this repository. The PR was mergeable and clean; local Python, Node, Chromium, Pages Function and source-integrity gates above are the executed verification evidence. The repository still lacks remote CI checks for future changes.

## Sources

- [NASA RadLab Data API](https://visualization.osdr.nasa.gov/radlab/gui/data-api/) and [RadLab release history](https://visualization.osdr.nasa.gov/radlab/gui/knowledgebase/Release_history).
- [NASA CCMC DONKI API migration notice](https://ccmc.gsfc.nasa.gov/news/major-updates/).
- [NASA OSDR Biological Data API](https://visualization.osdr.nasa.gov/biodata/api/) and [NASA Environmental Data App](https://visualization.osdr.nasa.gov/eda/).
- [Z-Anatomy license](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/License.txt) and pinned-model attribution in `web-local/src/vendor/anatomy/ATTRIBUTION.md`.
- Additional EVA sensor engineering papers and their evidence limits are in `docs/asthral/science/SPACE_HEALTH_EVIDENCE.md` and the local source registry. They do not support the demonstration thresholds or flight qualification.
