# EVA Monitoring (simulation) — module notes

Contribution branch: `feature/eva-monitoring` · base: `feature/asthral-autonomous-mission` (confirm SHA with the integrator).
Status: prototype, **synthetic data only**, not clinically, operationally or flight validated.

## What it does
`Start EVA` runs a deterministic synthetic EVA and shows four cards:

| Card | Content | Never shown as green when… |
|---|---|---|
| 🌡️ Core Temperature | synthetic **core** temperature (not skin), trend, source, rule | missing, invalid, out of range or stale |
| ❤️ Heart Rate | synthetic bpm vs **EVA-exertion baseline** (not resting), delta, trend | no baseline (`No baseline available`), invalid, stale |
| ☀️ Solar Weather · NASA DONKI | events from the **existing** DONKI cache (`space-weather.js`) with type, UTC time, source, link, cache age | `Data not available` (no cache) vs `No events recorded` vs `Events not evaluated for this mission` vs `TRAINING: synthetic particle event` |
| ⏱️ EVA Timer + Radiation Dose | UTC-based timer; `SIMULATED DOSE` = rate × elapsed hours (assumption shown) | `DOSIMETER NOT CONNECTED` when no simulated rate exists |

Also: `End EVA`, chronological event log, `Acknowledge advisory`, `Prepare handover report`, and a **training-only** `Trigger training critical` button.

## Safety boundaries (as required by the collaboration guide)
- Real DONKI events are **context only**; an ordinary flare never triggers the advisory by itself.
- Only an **explicitly marked synthetic training event** (`critical_training` scenario or manual training trigger) can produce the critical solar alert.
- Advisory text: **"Return to airlock — simulated EVA safety advisory"**, with the rule and time that fired it. It is a simulated recommendation; ASTHRAL does not control suits, navigation or communications.
- Dose is **never** computed from DONKI.
- The handover report is `PREPARED_LOCALLY_NOT_SENT`; nothing is sent to external services.
- All thresholds live in `EVA_RULES` (`eva-monitoring.js`) with units, source and justification. They are **prototype rules, not NASA-certified limits**.

## States and scenarios
States: `idle → active → warning → critical → completed`, plus `error`. One session at a time; one timer; alerts are not duplicated.
Scenarios (deterministic, 30 synthetic minutes): `nominal`, `thermal_warning`, `critical_training` (marked TRAINING EXERCISE).

## Files
New files only — no existing file was modified:
- `web-local/src/eva-monitoring.js` — rules, scenarios, classifiers, `EvaController` state machine, `buildHandoverReport`, `reportToText` (no DOM).
- `web-local/src/eva-view.js` — `mountEvaMonitoring(container, options)`; imports `cachedDonkiSnapshot` and `DONKI_HISTORICAL_FIXTURE` from the existing `space-weather.js` (no new HTTP client).
- `web-local/tests/eva-monitoring.test.mjs` — automated tests.
- `docs/asthral/EVA_MONITORING.md` — this file.

No new dependencies. No API keys. No personal or clinical data.

## Integration point (for the integrator)
1. In the mission-context view, add a container and mount the module:
   ```js
   import { mountEvaMonitoring } from './eva-view.js';
   mountEvaMonitoring(document.querySelector('#eva-monitoring'), { stepMs: 1000 });
   ```
2. Add an `EVA / Extravehicular Activity` entry to the existing navigation that shows that container.
3. If `build.py` / the service worker keep an explicit asset list, add `eva-monitoring.js` and `eva-view.js` so the module works offline.
4. DONKI refresh stays in the existing space-weather flow; EVA only reads its cache. Without a cache, the offline demo shows the existing fixed historical fixture, labelled as example data.
5. Optional: route `buildHandoverReport(controller)` (JSON) into the existing report/export system.

## Tests
```
cd web-local
node --test tests/eva-monitoring.test.mjs
```
Result in the contributor environment (Node 22): **13 tests, 13 pass, 0 fail**. Covered guide cases: 1–11 and 14, plus a state-machine/error test. A DOM smoke test (jsdom) verified Start EVA → critical training → advisory → acknowledge → End EVA → report.
Not yet verified by the contributor: case 12 (existing navigation unchanged after wiring) and case 13 (regression of existing DONKI/mission tests) — run the full suite after integration.

## References
- NASA (2026). Help NASA Find Practical Ways to Monitor Astronaut Body Temperature in Low Earth Orbit.
- NASA-STD-3001 Vol. 2, Section 11 — Spacesuits.
- NASA CCMC DONKI and NASA Open APIs (research/prototyping quality, not an operational safety system).
- NASA Space Apps forum, Datasets for Health Monitoring Software (13/11/2026).
- EVA thermal-monitoring research shared by Dr. Julio Valdivia (UTEC): T-EVA bio-sensorized upper-body temperature monitoring during EVAs; embedded temperature monitoring in spacesuits in analog missions.

AI assistance: code and documentation were drafted with an AI coding assistant and reviewed by the contributor.
