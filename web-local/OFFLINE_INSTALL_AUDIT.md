# Offline installation incident — 2026-11-14

## Report and observed defects
The owner reported that **Install offline resources** did nothing on Samsung Chrome, using immutable preview `499af8d6.asthral-web.pages.dev`. The exact physical-device failure has not been reproduced or diagnosed from a phone console. Code inspection found feedback outside the button area, unbounded waits, and a registration/update race. These are verified technical defects, not proof of the phone's complete root cause.

## Correction
`src/offline-install.js` bounds manifest registration, activation and cache acknowledgment waits. `src/app.js` disables the button while working, places live progress/errors beside it and restores the button after completion/failure. `src/sw.js` verifies the pinned manifest and every essential public resource before acknowledging readiness. A waiting update is distinct from a ready installation. Personal encrypted profiles are neither removed nor cached by this workflow. Persistent-storage permission is advisory: refusal, exceptions or timeout cannot convert an already verified cache into an apparent failed installation.

## Actual evidence
- Full browser/actual WASM suite before the last advisory-storage hardening: **35 passed, zero failed**, 6269.49 ms (`work/browser-local/browser-final-tests.txt`).
- Focused installer suite after hardening: **5 passed, zero failed**. Tests cover worker success, rejection and timeout, required cache acknowledgment, waiting-update state, permission exception and integrity-error propagation.
- Deployed HTTPS preview `https://f5887ce5.asthral-web.pages.dev/`: clicked Explore Synthetic Demo, expanded Settings and Developer View, clicked Install offline resources. The button immediately changed to disabled Installing offline resources; adjacent text displayed 15.4 MiB preparation. It then reported **Offline resources verified: 49 files**, followed by the eviction/backup warning. This preview precedes advisory-storage exception hardening only.
- Screenshot: `C:/Users/Gianni/Documents/Codex/offline-install-verified.jpg`.

## Release gate and phone retest
Samsung acceptance remains **PENDING**. The owner has been sent the new immutable URL; old immutable deployments do not receive this fix. Required test: install online, wait for verified readiness, reload online once, enable airplane mode and disable Wi-Fi, reload and compute a synthetic assessment. Browser installation success is not proof of actual network-disconnected operation. Do not promote this candidate on the strength of unit tests or desktop installation alone. No clinical validation is claimed.


## Follow-up: reload failed even while online
The owner clarified that the error occurred **with connectivity, in the same tab**. Reproduced on the deployed IAB page: after installing, reload yielded ERR_FAILED. Public HTTP verification showed `/index.html` returns **308 Location: /**. The service worker cached the followed redirect response and reused it for manual-mode document navigation. Redirected cached responses are incompatible with that navigation mode.

Correction: normalize integrity-verified resource responses with a fresh `Response` preserving status, headers and bytes before storing them; also normalize legacy redirected cache hits for navigation. No clinical/private content or security policy was changed. Two service-worker regressions exercise redirected HTML, root/query navigation, and a restarted worker with a simulated disconnected fetch transport. These simulations are not physical airplane-mode acceptance.

A second build defect was found while testing optional speech: `prepare_voice.py` used the invalid codec name `utf8-sig`, so the generated Vosk artifact had not received the reviewed CSP wrappers. Corrected to `utf-8-sig`, regenerated from the official integrity-pinned npm artifact and added a regression inspecting the actual embedded generated worker for dynamic string execution and explicit finalization. CSP remains unchanged.

After successful preparation/build and supplying the documented fake-indexeddb dependency path, **40/40 browser tests passed**, 6441.05 ms, including 254 exact clinical canonical hashes and the new cache/generated-artifact regressions. One earlier rerun failed because FAKE_INDEXEDDB_MODULE was omitted; the dependency configuration was corrected, not the application security checks. Candidate: https://decec363.asthral-web.pages.dev/ . Real HTTPS reload verification and Samsung offline acceptance are tracked separately.


## HTTPS result after redirect correction
On `decec363`, actual browser checks succeeded: installed/verified 49 files; reloaded the same tab online; landing rendered; Python worker restarted; entered temporary demo; evaluated the default diabetes synthetic input. Output: documented criteria and confirmation requirements satisfied, missing required information None, protocol BLOCKED_AUTHORIZATION. Repeated installation also verified all 49 files. Screenshot: `C:/Users/Gianni/Documents/Codex/offline-reload-fixed.jpg`. The corrected URL was sent to the owner for physical Samsung online and disconnected retests. No successful physical offline result has yet been reported.


## Physical owner report
On 2026-11-14 the owner replied **“funcionó sin internet”** to the Samsung retest for `decec363`. Record as OWNER_REPORTED_PHYSICAL_OFFLINE_SUCCESS. This is not an independent instrumented network trace, not clinical validation, and does not establish iPhone/Safari, every optional model, or all workflow acceptance. The exact synthetic assessment output was not supplied in that reply.
