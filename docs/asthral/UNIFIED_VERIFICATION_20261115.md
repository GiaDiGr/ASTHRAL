# ASTHRAL unified candidate verification

Date: 2026-11-15. This records software and interface checks only. It is not clinical, operational, security, or regulatory validation.

## Candidate scope

The candidate combines the preserved Python/FastAPI engine and contributed integrations with the browser-local PWA. The original `web-local/dist`, vendor assets, Windows/Ollama configuration, and local user data were left in place. A fresh static build was generated at `web-local/build-output-unified-20261115b` so the existing output would not be overwritten.

## Results

- Python engine/integration suite: **882 passed, 19 skipped, 0 failed, 1 warning** in 329.56 seconds. The skips are optional CV, vision, and voice runtime checks whose large model/runtime dependencies are not installed in this worktree. The warning is Starlette's deprecation notice for the current httpx test client.
- Browser test suite after the mobile navigation regression test: **53 passed, 0 skipped, 0 failed**.
- Static build: **254 synthetic parity cases**, six selected Python packages, 68 output files, 112,622,031 bytes; packaged clinical modules were reported byte-identical to their reference modules.
- Local browser walkthrough: synthetic demo entry, DKA assessment form, history route, and assistant evidence fallback were exercised. The assistant clearly said no model generation occurred and displayed verbatim engine evidence. This does not verify an actual LLM, microphone recognition, CV inference, or offline operation on a physical device.

## Findings and corrections

- At narrow mobile widths the CSS hid the fifth main navigation link (History), even though the route and history data existed. The hide rule was removed; constrained links can wrap, and a CSS/HTML contract test now protects the route's reachability.
- A manually entered synthetic pH used `SIMULATED_VENOUS_BLOOD`, while the engine requires the declared method `VENOUS_BLOOD_GAS` for venous pH. The engine correctly marked that evidence invalid, left DKA criteria unresolved, and kept protocol execution blocked for independently missing potassium and other safety/resource/authorization requirements. The UI did not fabricate a normal or valid pH. This is an input-quality finding, not a change to clinical rules.
- With method `VENOUS_BLOOD_GAS`, the existing stored synthetic HTTP example reproduces the criterion tree: known diabetes satisfies the first alternative; beta-hydroxybutyrate satisfies the ketone alternative; pH satisfies the acidosis alternative; unmeasured bicarbonate and urine ketones do not block criteria status. The protocol remains independently blocked by potassium, resources and authorization.
- Build output was redirected to a new isolated directory; the build refuses to overwrite a non-empty directory. The prior `dist` and local resources remain intact.

## Limits and required review

- Synthetic correctness and deterministic replay do not establish diagnostic accuracy or clinical safety. Each clinical rule and route requires independent clinician review against cited source versions, followed by intended-population and operational validation.
- Browser local accounts are encrypted at rest in IndexedDB, but an unlocked page, malicious same-origin code, compromised OS/extensions, or storage rollback remain threats. The Python SQLite backend is not encrypted. The local audit chain can be rewritten by an attacker controlling the storage.
- The browser assistant in this walkthrough used extractive fallback only. Actual model loading/generation was not verified. Vision intake did not perform inference. Microphone/voice acceptance and the 19 optional runtime tests remain pending. No treatment execution is enabled.
- Narrow layout was checked by automated CSS contract and desktop browser interaction. A physical-device screen-reader, keyboard and small-screen review is still required before accessibility acceptance.
