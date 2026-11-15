# ASTHRAL Mission Control and EVA integration

Status: local release candidate, 2026-11-15. This document records the implementation boundary and the acceptance procedure; it does not claim flight, clinical, or NASA validation.

The test and performance table later in this file is a historical snapshot from the preceding integration checkpoint. Current RadLab/anatomy acceptance must use the fresh report linked from the ultimate implementation traceability record and must not reuse historical results as a release pass.

## Integrated route

`Mission Control` is a route in the existing browser-local workspace and uses its existing profile, history, worker, DONKI cache, and navigation. The route is loaded on demand. Its 3D renderer, SGP4 propagation, NASA texture, and EVA scenario are packaged locally. The EVA integration retains Marfe's source module and tests from [Pull Request #2](https://github.com/GiaDiGr/ASTHRAL/pull/2); the original contribution commits remain in the branch history.

Completed synthetic EVA reports are validated by `vigile.eva_records.EvaActivityRecord` and appended as `eva_activity` records to the current browser profile's existing SQLite store. The browser's encrypted-profile Vault continues to persist serialized SQLite. Temporary demo records live only in the worker memory and are discarded when the demo closes. Report payloads must be simulations, have a completed session, match the mission/EVA/scenario IDs and remain below 400 kB. Profile ownership is assigned by the bridge rather than trusted from the browser payload. Existing profile restore checks scope for EVA records as for other profile data.

The route clock is a declared mission-scenario clock. EVA sample timestamps advance by one scenario minute per software sample; wall-clock start, end and elapsed duration remain separate fields. During an EVA, the orbital timeline follows the scenario UTC and its direct time controls are locked. Once the activity ends, the timeline can be moved independently again. The synthetic orbit uses locally defined elements; it is never identified as ISS.

## Orbital model and labels

- ISS mode requests a single public CelesTrak GP/OMM object with catalog ID 25544 and checks identity, epoch, orbital field ranges, element age, response size and HTTP redirect behavior. Valid mean elements are propagated locally with the vendored `satellite.js` SGP4 implementation.
- The result is an **estimated ISS position from orbital propagation**, not GPS or spacecraft telemetry. The element epoch, retrieval time, calculation UTC and stale/unavailable states are displayed. Requests are GET-only, omit credentials and referrers, use a 12-second timeout and have a six-hour refresh window. A valid last cache can be used offline with its age shown. Elements older than seven days disable the estimate.
- An ASTHRAL synthetic spacecraft uses separate demo elements and object identifier 990001. Its `YOU ARE HERE — SPACECRAFT · SIMULATED` label means only the simulated spacecraft marker; it never means the user's phone or computer location.
- The procedural spacecraft marker is schematic and radial. No attitude, vehicle dimensions, GPS, communications or station contact is inferred.
- Reference-city distance is a sampled great-circle surface distance across the next two propagated periods (30-second samples). It is not a ground-station or communications-contact prediction. No sourced station catalog is included, so contact is shown as unavailable.
- Sunlight, umbra and penumbra are computed from propagated geometry and the library's low-precision solar position model; they are not radiation measurements. NASA's Blue Marble texture is a July 2004 static composite, converted to WebP; credit: NASA Earth Observatory. It is not current imagery.
- The 2D equirectangular fallback draws the calculated ground track when WebGL is unavailable. It is a fallback view, not a static Earth image.

## EVA semantics

Marfe's temperature, heart-rate and synthetic-dose series and the explicit training scenario remain the contribution's demo inputs. Thresholds are presented as illustrative software rules, not NASA-certified, clinical, spacesuit or flight cutoffs. The 105 bpm scenario reference is synthetic and is not a personal EVA-exertion baseline. An empty DONKI query is shown as context only; a real DONKI flare cannot trigger the demo return advisory. Only an explicitly marked synthetic training event or the synthetic exercise button can fire that demonstration advisory.

No NOAA SWPC S-scale client is currently integrated. The UI does not derive an S-scale from DONKI records. DONKI events remain public environmental context, never personal exposure or dose. The dose value is simulated from a demonstration rate; the comparison value in code is not an exposure limit. There is no dosimeter, actual suit sensor, EVA risk engine or operational command interface. The generated English report distinguishes wall and scenario clocks, fixed/cached event data, synthetic readings, acknowledgements and limitations. It is prepared locally and is not transmitted automatically.

The Orbit UI may display historical DONKI cache records, a fixed historical example or no cached events. Each state is distinguished. Current space-weather conditions are unknown when a current source cannot be reached or has not supplied data. Surface UV, personal radiation estimates, radiation maps and line-of-sight ground-station schedules are not represented.

## NASA RadLab and anatomy additions

The integrated Radiation Explorer uses a same-origin `GET /api/radlab` contract and a fixed NASA RadLab upstream. The local preview's `web-local/serve.py` maps the same route to `web-local/radlab_proxy.py`; the deployed Pages build uses `web-local/functions/api/radlab.js`. Queries use NASA's documented key-value syntax, a seven-day ASTHRAL request bound, a 2 MiB transfer cap, `no-store` network caching, and no profile/health data. The last result may be stored locally for matching offline historical review; its state is marked `CACHED_HISTORICAL` or `STALE_CACHED_HISTORICAL`. An online archive query is `HISTORICAL_QUERY_RESPONSE`, and each instrument row remains `HISTORICAL`. Nothing is called live crew telemetry.

The view shows returned instrument values with NASA units, source/retrieval timestamps, nulls, valid coordinates, a timestamp scatter plot, an ISS coordinate graticule, replay selection, and JSON/CSV export. Coordinate-bearing historical points are overlaid on the existing Earth renderer and counted in its legend. The selected observation is contextual only; it cannot change the EVA alert, calculate personal dose, or enter clinical assessment. Some source release data are preliminary; cadence depends on the dataset and must be checked in NASA release notes.

The source registry also records NASA's OSDR Biological Data API, EDA, and the shared DONKI interface. OSDR biological experiments and EDA environmental/hardware tables are references, not imported current crew measurements. ASTHRAL does not claim a stable EDA JSON contract.

The Human Anatomy route lazy-loads one unmodified muscular-system GLB from pinned revision `8375d6ce7fec36e677c0eda66cae829ba55a4717` (4,003,932 bytes; SHA-256 `f8399ba12dedb7cd88de199eddf7e3f8a3de8373a69228fb9da7ce1b7981ffd2`). Attribution and CC BY-SA terms are in `web-local/src/vendor/anatomy/ATTRIBUTION.md`. The region selector and 3D controls provide orientation only; there is no model or data contract that anatomically localizes system-level medical findings. The 2D schematic is an explicit non-clinical fallback.

## Third-party data and licenses

- Three.js 0.187.0: [MIT license](https://github.com/mrdoob/three.js/blob/dev/LICENSE); renderer imported only after Mission Control is opened.
- satellite.js 7.1.0: [MIT license](https://github.com/shashwatak/satellite-js/blob/develop/LICENSE.md); only the needed JavaScript modules are vendored.
- ISS general perturbations source: [CelesTrak GP/OMM data formats](https://celestrak.org/NORAD/documentation/gp-data-formats.php); [ISS object 25544 query](https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON).
- SGP4 reference test: Vallado et al., *Revisiting Spacetrack Report #3*, [AIAA 2006-6753](https://celestrak.org/publications/AIAA/2006-6753/). The Node test uses its published object 00005 verification case and checks the propagated vector with an explicit tolerance.
- Earth texture: [NASA Blue Marble Next Generation](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/); use NASA attribution and do not imply NASA endorsement, mission partnership or operational approval. See [NASA image/media guidance](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Solar-event context: existing [NASA CCMC DONKI API](https://api.nasa.gov/); it remains the sole DONKI client used by ASTHRAL.

## Build, tests and browser acceptance

From the repository root, create an isolated engine environment and install only
the pinned, locally cached dependencies:

```powershell
py -3.13 -m venv engine\.venv
engine\.venv\Scripts\python.exe -m pip install --no-index --find-links engine\wheelhouse -r engine\requirements.lock
engine\.venv\Scripts\python.exe -m pytest engine\tests -q -rs
```

Run the complete browser-local Node suite against a fresh build. Set both output
directories to new, empty paths for each reproducible run:

```powershell
$node = 'C:\Users\Gianni\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$env:ASTHRAL_BUILD_OUTPUT = Join-Path $env:TEMP 'asthral-mission-control-build'
$env:ASTHRAL_TEST_DIST = $env:ASTHRAL_BUILD_OUTPUT
& engine\.venv\Scripts\python.exe web-local\build.py
Push-Location web-local
& $node --test tests\*.test.mjs
Pop-Location
```

Run the real Chromium acceptance against the same build. The Playwright Python
package must be available in the Python environment used for this browser test;
the test requires Chromium. For the optional live ISS estimate, Internet access
and CelesTrak availability are needed; the synthetic orbital scenario is offline.

```powershell
$browserPython = 'C:\Users\Gianni\AppData\Local\Programs\Python\Python313\python.exe'
& $browserPython -c "import playwright.async_api"
& $browserPython tools\browser_final_mission_control_acceptance.py --root $env:ASTHRAL_BUILD_OUTPUT --output work\browser-final-mission-control-acceptance --chrome "$env:LOCALAPPDATA\ms-playwright\chromium-1181\chrome-win\chrome.exe"
```

The browser flow uses a throwaway local profile and the synthetic demo only. It
checks that the actual WebGL renderer draws in Chromium, propagates the separate
simulated orbital mode, follows the EVA scenario UTC, provides the WebGL-denied
fallback, pauses and resumes, fires and acknowledges the training advisory,
writes the report through the existing encrypted profile store, locks and
reopens that profile to retrieve EVA history, verifies the existing Monitoring,
Clinical and Computer Vision routes, and captures desktop/mobile screenshots.
The report records actual route-mount timing and decoded on-demand orbital asset
sizes; Resource Timing may report zero wire bytes when transfer details are
unavailable. The test is software acceptance only, not flight, clinical or
hardware validation. Retain the JSON report and screenshots from the actual run
used for any release statement.

### Recorded local run — 15 November 2026

| Check | Result | Scope |
|---|---:|---|
| Python engine suite | **949 passed, 19 skipped, 0 failed**, 409.67 s | 2 skips for missing Argon2; 13 for missing OpenCV; 2 for missing PyTorch; 2 for real local voice dependencies not installed. One Starlette/httpx deprecation warning. |
| Browser-local Node suite | **123 passed, 0 failed, 0 skipped**, 17.73 s | Run against the fresh build below, including the full Pyodide clinical-reference comparisons. |
| Static build | **254 cases, 137 files, 143,257,352 bytes**; `clinical_modules: BYTE_IDENTICAL` | Total includes optional packs. The offline manifest has 106 required resources / 19,323,301 bytes and 31 optional resources / 123,934,051 bytes. Optional voice, motion, retrieval and parity resources are not required for the core offline install. |
| Chromium E2E | **PASS** | WebGL2 Earth renderer, four EVA cards, synchronized synthetic scenario, acknowledged training advisory, completed handover report, encrypted profile persistence/reload, existing core routes, visible mobile navigation, no overflow, WebGL fallback, no page/console errors and no required failed requests. |
| Cross-module mission browser flow | **14 synthetic steps passed**, 34.16 s | Baseline/replay, existing journal, prevention, pending follow-up, research retrieval, DONKI separation, exports and encrypted backup. No raw clinical identifiers or values in the aggregate summary. |
| NeuroGuard browser flow | **9 checks passed** | Shared self-report journal, linked sleep, NASA-TLX paired ratings, discard of incomplete PVT-B, scoped deletion, local exports; no page/console/request errors. |
| Voice browser flow | **Vosk READY; 5/6 synthetic phrases exact** | One sleep phrase was recognized with “a” instead of “as”; it remained `unresolved` and was not saved. All six tests had `record_saved: false`. Offline installer verified the 106-file required set. |
| MotionGuard browser inference | **Real CPU inference completed on 3 synthetic/fixture clips** | Wall-push: 24/25 valid angles; knee push-ups: 33/75; squat: 0/26 and `INSUFFICIENT_TRACKING`. There is no ground truth or accuracy claim, and no form/fitness interpretation. |
| Optional local generative model | **BLOCKED_NO_WEBGPU_ADAPTER** | Headless Chromium reported no adapter; the UI kept model loading disabled. Local deterministic computation and retrieval remain available. This is a hardware/browser limitation, not a model inference result. |

In the recorded headless Chromium session, engine readiness was **3.983 s**,
Mission Control mount to renderer-ready was **0.592 s**, the initial resource
timing total observed **351,245 bytes across 30 resources**, and on-demand
orbital assets decoded to **2,337,080 bytes**. Timing and the initial transfer
observation are workstation/cache dependent, not performance guarantees.
Resource Timing reported `transferSize: 0` for the orbital assets, so their
decoded sizes are reported instead of claiming wire-transfer bytes. The tested
Earth canvas was **502 × 590 px** at desktop; the mobile viewport was **390 px**
with a **282 px** globe stage and no horizontal overflow. The synthetic profile
record survived lock/reload and had an encrypted IndexedDB row (AES-GCM IV,
600,000 PBKDF2 iterations, encrypted email box); test credentials and health
records were not included in the report.

Artifacts from that exact run are in
`work/browser-final-mission-control-20261115-release-r4/`:
`report.json`, `mission-control-desktop.png`, and `mission-control-mobile.png`.
The build used was `%TEMP%\asthral-final-mission-control-20261115-r2` and the
source build report was `254 cases / 137 files / 143257352 bytes`.
Companion run artifacts are `work/browser-final-mission-cross-modules-20261115/`,
`work/browser-final-neuroguard-20261115/`, `work/browser-final-voice-20261115/`,
and `work/browser-final-motion-20261115/`. The model block report is in the
temporary acceptance directory
`%TEMP%\asthral-model-headless-acceptance-20261115\work\browser-model-acceptance\report.json`.

## Known limitations and review gates

1. Orbit propagation uses public general-perturbation elements and a simplified model. It is not precision navigation, live onboard telemetry, certified mission planning, operational tracking or a replacement for NASA/mission ephemeris.
2. The element source can be unavailable, stale, rate-limited or CORS-blocked. No result is fabricated in those states.
3. The offline texture is historical; cities are a small reference list, and no station network/contact data exists.
4. All EVA measurements and alerts in this implementation are synthetic. Thresholds, dose rates and any simulated comparison value require independent domain-owner/clinical/flight-operations review before being used beyond software demonstration.
5. EVA records are stored in the same encrypted browser profile as other local records; the SQLite data layer itself has no at-rest encryption. Browser encryption protects the serialized local Vault at rest, but not an unlocked process, compromised origin, operating system, browser extension, memory, or manipulated local storage.
6. DONKI is not dosimetry, NOAA S-scale is not integrated, and no solar-event-to-dose mapping exists.
7. Local testing on desktop Chromium cannot validate Android/iOS GPU behavior, battery draw, operational performance, flight hardware, medical safety, or offline install on an untested device.
