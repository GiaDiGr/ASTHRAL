# ASTHRAL final integration candidate — 15 November 2026

## Scope

This candidate keeps the existing Python engine and `web-local/` browser application. It integrates the current 3D body map and astronaut dashboard, mission-control globe, EVA workflow, synthetic environment controls, existing health/vision/NeuroGuard/assistant/voice/exercise modules, and the offline static build. It does not replace those modules or introduce a real model service.

The workspace has 22 route tabs and 24 local starfield assets. Palette position follows a 10-tab smooth cycle: blue at scene indexes 0, 10 and 20, and violet at indexes 5 and 15, with gradual transitions between them. Star positions and nebula placement remain distinct per scene. The CSS cross-fade and asset set remain compatible with the existing offline installer.

The MakeHuman-derived generic exterior model is an orientation aid only. Its redistribution and CC0 provenance are recorded in `web-local/src/vendor/anatomy/ATTRIBUTION.md` and `model-manifest.json`. ASTHRAL does not claim clinical localization or validation from the model.

## Software verification performed locally

The tests used synthetic application records. No real astronaut or patient record was loaded.

| Check | Result | Scope |
|---|---|---|
| Python engine suite: `engine/tests` | **958 passed, 19 skipped, 0 failed** in 197.50 s | One Starlette/httpx deprecation warning; skips are optional-dependency cases. |
| Browser-local Node suite | **148 passed, 0 failed** in 12.27 s | Run from `web-local/` against `build-output-wave-20261115`. |
| Cosmic wave palette regression tests | **3 passed, 0 failed** | Ten-tab period, blue/violet extrema, return-to-blue, and all 24 generated asset palettes. |
| Chromium galactic and synthetic-control acceptance | **PASS** | Checked route scenes 0, 5, 10, 15, 20 and 21; all 24 palette assets; cross-fade; 8 training sliders; synthetic ECG response; cabin/suit inputs; alerts; and mobile overflow. |
| Chromium offline installation | **PASS** | Verified 139 resources; after disconnect/reload, the app remained controlled by the service worker and six representative scene SVGs returned HTTP 200. |

The separate full mission-control browser script did not finish successfully in this run. It confirmed a WebGL2 Earth, loaded 1,469 historical NASA RadLab records, completed the four-card synthetic EVA with alert acknowledgement, saved the handover report, and recovered the encrypted history after lock/reload. It then timed out at an obsolete anatomy navigation selector. The selector was corrected, but the user asked to stop further checks before the rerun completed. Do not report the full mission-control acceptance as PASS.

The live CelesTrak GP request returned HTTP 403 during the browser run. The application code treats a failed public element request as unavailable and keeps simulated orbit as a separately labelled option. This run did not verify a live ISS element response. CelesTrak's [GP data documentation](https://celestrak.org/NORAD/documentation/gp-data-formats.php) and [usage policy](https://celestrak.org/usage-policy.php) govern this optional feed; orbit positions are propagated estimates from mean elements, never direct telemetry.

## Limitations

- These checks establish software behavior on one local workstation. They are not independent clinical review, clinical validation, NASA certification, flight qualification, or evidence that any sensor is installed in a mission vehicle.
- Browser offline verification tested a local Chromium profile. Physical-device offline behavior is not re-verified here.
- Public orbital data may be unavailable or stale. The application must preserve the source state and may not silently substitute synthetic data for ISS elements.
- CelesTrak returned 403 during this run; no current public ISS estimate is asserted.
- The separately deferred 44-test mission program and demonstration video were not run or produced.

## Build and deployment

The static production build is created with `web-local/build.py` into a new output directory. The verified local build used during this integration is ignored under `web-local/build-output-wave-20261115/` and is not a source artifact for GitHub. The Cloudflare Pages project is `asthral-web`; the established production hostname is `https://asthral-web.pages.dev/`. Record the integrated `main` commit and successful production deployment identifier here only after those operations complete.
