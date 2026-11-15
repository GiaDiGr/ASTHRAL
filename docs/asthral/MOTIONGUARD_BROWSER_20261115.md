# Browser MotionGuard — genuine CPU inference, research scope

This optional pose-only browser adapter complements the existing native Holistic adapter; it does not replace its model or claim all its outputs. The UI is in Exercise, with manual session tracking independent of model availability. No clinical criteria, treatment authorization, diagnostic route or radiation threshold changes.

## Provenance

Google MediaPipe Tasks Vision 0.10.21, Apache-2.0, and Pose Landmarker Lite float16 version 1. Installer verifies npm archive SHA-512 and all installed file hashes; runtime verifies the pinned model SHA-256 `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a` before CPU model creation. Sources: https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker?tab=Web ; https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf ; https://registry.npmjs.org/@mediapipe/tasks-vision/-/tasks-vision-0.10.21.tgz . Installed runtime/model files total 25,346,572 bytes, plus manifest/license. No model output is fabricated.

`python tools/install_browser_pose.py` installs pinned assets when absent; a conflicting installed file is rejected. Optional runtime and three permitted fixture videos are included in the feature branch for reproduction. CDC public-domain push-up excerpts and CRiles23's CC BY-SA 3.0 squat excerpt retain attribution and transformations in web-local/src/test-motion/ATTRIBUTION.md and manifest.json. They are public prerecorded demonstrations, not synthetic astronaut recordings or endorsements. No restricted clinical dataset is distributed.

## Software behavior

Input is a user-selected local decoded video up to 20 seconds, 9 MiB, 2 megapixels/frame, sampled at 5 frames/source-second. The worker uses CPU VIDEO mode and monotonic timestamps. UI projects elbows/knees into the aspect-correct pixel plane. Missing/low-visibility/out-of-image joints yield null, not zero. User cycle boundaries are technical settings with no prescribed default. The high-low-high counter resets partial cycles across missing tracking. Missing frames force complete `cycles` to null; separately labelled observed complete sequences are retained.

Only a reviewed summary can be attached to an existing active manual session. The Python normalizer validates frame consistency, bounds, model identity and source hash but forces all execution/identity/sensor verification flags false; client claims are not trusted attestation. Manual repetitions are unchanged. Analysis time never substitutes for recording time.

Explicit camera acquisition is implemented with audio disabled, a 20-second hard stop and stream cleanup on stop/lock/hidden/pagehide/mode downgrade. It uses the normal permission prompt; no physical camera test or permission grant was performed. Raw media is transient memory, not journal storage. Derived JSON exports are plaintext. FULL mode is required; LOW_POWER/CRITICAL terminate optional inference. A worker GET guard permits only fixed local public runtime assets; it is not an OS-level egress firewall. CSP, nosniff and ordinary browser permissions remain enforced.

## Real Chromium acceptance

Latest report: work/browser-pose-candidate/report.json, plus actual overlay screenshots and exported per-frame JSON. All three videos executed genuine inference under the build's enforced CSP, with zero page errors:

| Fixture | Sampled frames | Usable joint angles | Missing | Output |
|---|---:|---:|---:|---|
| Wall push | 25 | 24 | 1 | Partial tracking, complete count null |
| Knee push-ups | 75 | 33 | 42 | Partial tracking, complete count null |
| Squat | 26 | 0 | 26 | Insufficient tracking, angles/count null |

The selected test boundaries 70/150 degrees are arbitrary software settings, not medical exercise targets. No annotated ground-truth counts or accuracy estimates exist. This result demonstrates abstention as well as actual model execution; it does not establish form assessment, strength, ROM accuracy, injury risk, displacement, SANS or spaceflight validity. A squat failure cannot be labelled normal movement.

Earlier failures remain recorded: this Chromium lacks H264 support, so licensed VP8 fixtures were used; direct video-to-ImageBitmap failed, corrected with a decoded canvas snapshot; a source-loading race was corrected; module-worker importScripts incompatibility was corrected using a classic worker and ESM import. No unsafe browser flags or CSP bypass were added.

Unit tests cover rectangular-angle math, visibility abstention, tracking gaps, strict counter boundaries, worker shutdown and the local fetch guard. Python tests cover untrusted attachment, forged flags, missing data, contradictory counts, invalid hashes/numbers and independent manual repetitions. Physical-device camera, long-session thermals, annotated vision accuracy and held-out astronaut applicability remain pending.
