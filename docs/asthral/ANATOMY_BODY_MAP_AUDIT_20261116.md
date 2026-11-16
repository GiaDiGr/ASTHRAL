# ASTHRAL external-body map repair and acceptance

**Review date:** 2026-11-15

**Branch:** `feature/asthral-final-integration-20261115`
**Validation scope:** software behavior with synthetic data only. This is not clinical, flight, accessibility-conformance or operational validation.

## Findings and corrections

The previous map treated human-body regions as regular-expression matches over muscular-atlas mesh names. Those names did not describe the visible external surface reliably. Its pointer-up path also retained the previous selection when a nearer intersected mesh could not be mapped, which explains why a click on an unmapped head surface could leave Chest in the context panel. The initial camera was not aimed at the model after its bounds were normalized, so the body could also appear severely cropped.

The replacement uses the smooth, rigged external-body asset listed in `web-local/src/vendor/anatomy/model-manifest.json`. Selection and highlighting now share face-level IDs. Each source vertex is assigned from explicit MakeHuman bone identifiers and source-model surface landmarks. An indexed triangle is assigned only when all three vertices agree on one supported region; mixed or ambiguous faces remain unassigned. Triangles are grouped by region and original material. The top raycast hit reads its face ID, and only the matching group receives the highlight material. A miss or an unassigned front face clears the dropdown, highlight and context together. No hit is followed through the visible surface.

The camera is explicitly positioned after model centering/scaling. The existing anterior/posterior buttons, 360-degree drag, wheel/pinch zoom, pan mode, region selector, local model cache and 2D fallback remain integrated. A 5-pixel mouse and 8-pixel touch movement threshold separates taps from camera gestures; pointer cancellation is handled without selecting a region.

## Region contract

The stable IDs and presentation labels are defined in `web-local/src/anatomy-regions.js`:

`head`, `face`, `left_eye`, `right_eye`, `neck`, `chest`, `abdomen`, `back`, `left_shoulder`, `right_shoulder`, `left_upper_arm`, `right_upper_arm`, `left_forearm`, `right_forearm`, `left_hand`, `right_hand`, `left_hip`, `right_hip`, `left_thigh`, `right_thigh`, `left_knee`, `right_knee`, `left_lower_leg`, `right_lower_leg`, `left_ankle`, `right_ankle`, `left_foot`, `right_foot`.

The mapping uses exact source rig names for paired limbs, hands, feet and eyes. Surface coordinates distinguish the head/face/eye subregions, chest/abdomen/back, hips and joint transitions. Laterality comes from exact left/right rig bone identifiers except the paired pelvis surface, where the source model's X orientation is used. Face groups with conflicting vertex assignments are deliberately not selectable. At runtime, `coverage()` counts assigned triangles (not merely labels or dropdown entries); the accepted build represented every ID on at least one triangle.

The region selector and contextual panel remain navigation-only. No assessment or health record is associated with a clicked region. Existing image/movement/history module links are destinations, not diagnoses or localized findings. The context copy continues to distinguish missing regional data from normality.

## Model provenance and limits

The active mesh is an Innerscene adaptation of MakeHuman CC0 assets, bundled as `makehuman-external-body.glb`. Its provider page describes a smooth adult male-morphology A-pose base mesh and states approximate dimensions of 119 × 49 × 179 cm. The bundle is 4,498,248 bytes with SHA-256 `86c7cdfa989924b45e2e5110c131a4a4e6251ceb4e71246be68e468f3a32ca86`. The source and license are documented at [Innerscene](https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89), [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) and [MakeHuman](https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md); local attribution is in `web-local/src/vendor/anatomy/ATTRIBUTION.md`.

The legacy Z-Anatomy muscle model remains in the original source tree with its prior hash, attribution and CC BY-SA notes. `web-local/build.py` excludes it from the app build, static asset manifest and offline package. The new model and renderer remain optional resources and are verified against `assets.json` before entering the optional cache.

The current model has one generic male morphology, no astronaut-specific proportions and no clinical validation. It lacks a female morphology option. Region boundaries are educational orientation zones tied to this mesh and rig; they must not be treated as lesion, pain, organ, sensor or diagnostic localization.

## Automated software verification

The anatomy-specific Node tests passed **7/7**. They cover stable IDs, exact rig mapping rather than muscle-name guessing, head/face/eyes, torso zones, laterality, joints, ambiguity/abstention and local model hash/license metadata.

The full browser acceptance test was run against an isolated local build with Chromium and software WebGL. Its representative coordinates are projected from triangle-interior points on the loaded surface; the test raycasts each coordinate, then dispatches actual mouse or touch input and verifies the resulting face ID, selector, context and highlighted triangle groups.

| Acceptance check | Result |
|---|---:|
| Desktop surface clicks, including Chest → Head → Abdomen → left arm → right arm → Head, all 28 IDs, posterior laterality, zoom/rotation/pan and empty-space clearing | 39/39 correct |
| Accessible region selector synchronized with context and highlighted groups | 1/1 correct |
| Ambiguous visible triangle cleared the previous region and highlight | 1/1 correct |
| Combined desktop pointer, empty-space, ambiguous-surface and selector checks | 42/42 correct |
| Mobile touch taps with a rotate swipe between taps | 2/2 correct |
| Offline head/chest reselection after application reload | 2/2 correct |
| Surface IDs represented | 28/28 |
| Chromium page errors / failed requests | 0 / 0 |

The final recorded run used build output `web-local/build-output-anatomy-map-20261116-r9` and wrote JSON plus screenshots to `work/anatomy-browser-acceptance-20261116-r14/`. The app and model loaded from the local build in 6.278 seconds; the complete browser run including offline installation and mobile checks took 48.647 seconds. The offline flow verified the model's exact 4,498,248 bytes and SHA-256, installed the app's 111 core resources, reloaded offline in 0.098 seconds, opened the local engine and rendered/select-tested the model. Chromium reported no page errors or failed requests.

The full Node test command executed **127 tests: 126 passed, 1 failed** on Node.js v24.22.1. The unrelated failure is `tests/reference-wasm.test.mjs`: Node 24 rejects the generated `dist/runtime/pyodide.asm.js` because it combines CommonJS `require()` and top-level `await` (`ERR_AMBIGUOUS_MODULE_SYNTAX`). The anatomy tests, the other test files and the browser acceptance passed. No medical data were used.

Build command used:

```powershell
$env:ASTHRAL_BUILD_OUTPUT = (Join-Path (Get-Location) 'web-local\build-output-anatomy-map-20261116-r9')
python web-local\build.py
```

Browser acceptance command:

```powershell
python tools\browser_anatomy_acceptance.py web-local\build-output-anatomy-map-20261116-r9 `
  --output work\anatomy-browser-acceptance-20261116-r14
```

The test requires Python Playwright and the local Chromium executable; `ASTHRAL_CHROMIUM` can override its default Windows Chromium path.

## Deployed preview and release state

Cloudflare Pages project `asthral-web` received the isolated build on preview branch `anatomy-body-map-20261116` with Wrangler 4.76.0. The immutable preview is [36e2dba8.asthral-web.pages.dev](https://36e2dba8.asthral-web.pages.dev/) and its branch alias is [anatomy-body-map-20261116.asthral-web.pages.dev](https://anatomy-body-map-20261116.asthral-web.pages.dev/). This was a Pages preview deployment; the stable production alias was not changed.

The final deployed Chromium run wrote its report and screenshots to `work/anatomy-browser-acceptance-preview-20261116-r4/`. It passed **39/39 desktop surface clicks**, **42/42 total desktop interactions**, **1/1 accessible selector**, **1/1 unclassified-surface clearing**, **2/2 mobile touch interactions**, and **2/2 offline reselections**. All **28/28** regions had selectable face groups. The model was cached offline at 4,498,248 bytes with the expected SHA-256; the PWA verified 111 core files and reloaded offline in 0.113 seconds. Browser load was 11.942 seconds and the full preview run took 69.310 seconds. Chromium recorded zero page errors and zero failed requests.

The first remote attempts exposed two acceptance-harness issues, not a passing result: navigation through the collapsed mobile overflow menu was not synchronized with the page change, and touch coordinates were calculated while the canvas remained below the viewport. The harness now dispatches the delegated route event after opening the menu and scrolls the canvas into view before measuring projected pointer coordinates. The corrected run exercised real mouse/touch input against the deployed canvas and passed the checks above.

The preview is ready for owner review. It has **not** been accepted by the owner, merged to `main`, or promoted to stable production. No remote Git commit or push was made in this audit. The release workflow remains gated on preview acceptance and repository checks.

Before clinical or flight use, a qualified reviewer must independently inspect the region boundaries, laterality, source-model rig and surface correspondence, body-morphology limitations, accessibility and intended scope. Passing unit, synthetic and browser tests establishes implementation behavior only; it does not validate anatomical or clinical accuracy.

Deployed preview acceptance command:

```powershell
python tools\browser_anatomy_acceptance.py web-local\build-output-anatomy-map-20261116-r9 `
  --url https://anatomy-body-map-20261116.asthral-web.pages.dev/ `
  --output work\anatomy-browser-acceptance-preview-20261116-r4
```

## Supplemental full-mission integration verification

The final mission-control browser acceptance was run against the same r9 local build after updating one stale harness assertion to match the current public status text (`3D external body map loaded`). The full flow completed with `result: PASS`, no browser console errors and no unexpected failed requests. Its report is `work/browser-mission-control-final-anatomy-review-20261115-r3/report.json`.

The run exercised WebGL2 Earth rendering; the NASA source registry; retrieval of 1,469 public historical NASA RadLab environmental records with provenance, chart/map points and CSV/JSON exports; correct stale-cache labeling offline; LOW_POWER and CRITICAL transitions with playback disabled in CRITICAL; restoration to FULL; explicitly synthetic orbital state; four EVA monitoring cards, simulated advisory acknowledgement, report generation and medical-handover disclosure labels; encrypted local profile persistence, lock/reload recovery and audit verification; anatomy navigation without clinical localization; existing monitoring, clinical, computer-vision and anatomy routes; 390-pixel mobile layout; and the WebGL-disabled 2D ground-track fallback. The synthetic EVA/profile data were synthetic; the RadLab observations were public historical environmental data, not medical data. The offline RadLab fetch failure was expected and reported as a stale cached result.

Measured in that Chromium run: clinical engine ready in 6.335 seconds, initial transfer 407,505 bytes over 37 resources, mission-control mount 1.263 seconds, and 2,342,675 decoded bytes for orbital renderer resources. These measurements are specific to this machine/browser/cache state and are not flight-computer or low-power qualification results.

The full Python suite completed with **956 passed, 19 skipped, 1 setup error, 1 warning** in 388.46 seconds. The error occurred before `test_dirty_local_edits_stop_before_updating_and_remain_intact` ran: its fixture's first push to a newly initialized local bare Git repository returned exit code 1. A direct retry of that same isolated temporary-repository push succeeded, and rerunning the exact pytest case then passed (**1 passed in 4.89 seconds**). The full suite must therefore be reported as having one transient setup error, with the affected test passing on targeted rerun, rather than as fully green. Skips were due to optional `argon2`, `cv2`, `torch` and real local voice dependencies being absent. The warning is a Starlette/httpx TestClient deprecation notice.

The complete JavaScript suite on Node.js v24.22.1 reported **126 passed, 1 failed**. The failing file is `tests/reference-wasm.test.mjs`; Node rejected the generated Pyodide runtime module because it combines CommonJS `require()` with top-level `await` (`ERR_AMBIGUOUS_MODULE_SYNTAX`). This Node compatibility failure is separate from the anatomy work. The browser-based engine and parity-dependent workflows were exercised in Chromium by the local, deployed-preview and full-mission browser acceptances above; those results do not convert the Node suite into a pass.

On 2026-11-15, `origin/main` was fetched and resolved to `5bc9ff964da716693f2d04a80504747603452693`, the same commit as the local feature branch base. No teammate changes were overwritten. The anatomy changes remain uncommitted and unpushed. Preview acceptance by the project owner is still pending; stable production remains unchanged.
