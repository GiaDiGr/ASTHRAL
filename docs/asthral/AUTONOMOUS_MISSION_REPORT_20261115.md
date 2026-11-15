# ASTHRAL autonomous mission — implementation and verification report

Review date: 2026-11-15
Branch: `feature/asthral-autonomous-mission`
Base: `b708df456e504d9e486236915f878ec088e4f2f9`
Purpose: continue the existing integration in an isolated worktree; no reset or edits to the original project tree or stable deployment.

## Summary

Added bounded self-reported prevention records, radiation observation storage and unit-safe calculations, NASA CCMC DONKI retrieval with offline cache display, and an offline NASA source registry. These additions keep readings, environment events and self-reports separate. The deterministic clinical rules, thresholds, and seven existing pathways were not changed. New records and computed dose intervals remain nonclinical and blocked from treatment or flight action.

## Feature matrix

| Area | Implemented in this branch | Software verified | Evidence/source status | Hardware/clinical status |
|---|---|---|---|---|
| Existing seven deterministic pathways and differential engine | Preserved unchanged in reference modules and packaged byte-identically | Full Python suite and browser parity tests; 254 build fixtures | Existing criteria/source inventory unchanged | Not clinically or flight validated |
| Prevention journal | Exercise, hydration, meal notes, sleep and voluntary well-being entries; owner-bound local persistence | Bounds, timezones, audit/profile isolation, Node integration suite | NASA HRP catalogue and selected report links/summaries | User-reported only; no validated sensors, target values, diagnoses, or prescriptions |
| Radiation records | Separate quantity families, units, mode, quality, source, timestamps, model provenance and uncertainty; explicit rate integration; counter reset/duplicate review | Unit, gap, quality, mode, duplicate, reset and owner-scope tests | NASA SRAG CAD description, NESC HERA/CAD report and NASA standard catalogue links | No verified dosimeter or transport model; no Gy→Sv conversion, exposure limits, risk interpretation, treatment or flight decision |
| DONKI | Bounded official API queries for six event classes plus notifications; partial failure handling, event validation, safe links, public cache and stale/offline display | Request, schema, link, cache, date and missing-network Node tests; one live API request observation | CCMC documents state research/prototyping use and no warranty; no clinical relevance mapping | Not real-time service assurance, personal exposure or crew warning |
| Offline evidence | Eight hash-addressed files, 586 sparse lexical blocks, source registry copied into static build; optional MiniLM vector index remains six project-authored chunks | Source hash check, offline build, sparse retrieval and citation metadata tests | 12 official bibliography records; source summaries authored by ASTHRAL; no full report redistribution | Not a systematic review; scientific interpretation needs independent review |
| Existing local AI, voice, vision, encryption | Preserved; no new model or medical authority added | Existing automated tests only | Local verified corpus remains bounded; external PubMed remains title metadata | Qwen3-4B successful inference, voice, physical cameras and target devices were not tested in this cycle |
| Frontend | Small responsive Prevention & recovery, Space Weather & Radiation, Space Weather routes and collapsed source register added | Module tests and static production-style build; browser visual inspection unavailable | Source labels, quality/mode, stale state and caveats are exposed | Manual visual/mobile acceptance remains pending |

## Implementation detail

### Prevention records

`EXERCISE_SESSION`, `HYDRATION`, `MEAL_NOTE`, `SLEEP`, and `WELLBEING` are normalized in `engine/vigile/prevention.py`. Inputs require a timezone-aware date, bounded values, and meaningful text where applicable. Every record is `SELF_REPORTED`, not sensor-verified, with no clinical interpretation or execution. The UI uses the existing local worker and audit store, and only displays optional fields appropriate to the chosen record type. MotionGuard remains unavailable in this browser build; no camera is opened or video captured.

### Radiation

`engine/vigile/dosimetry.py` keeps absorbed dose, absorbed-dose rate, cumulative absorbed dose, dose equivalent, dose-equivalent rate, and effective dose as distinct quantity types. Conversion is restricted to units within one declared quantity family. Rate integration requires a positive explicit maximum gap and adjacent valid measured values sharing instrument ID, segment, and location. The linear-between-samples assumption is recorded in every interval; excluded intervals remain gaps. Counter decreases generate reset/rollover review rather than a guessed delta. User input cannot assert ASTHRAL sensor verification. All integration outputs state that clinical interpretation is absent and execution is blocked.

### Space weather and references

`web-local/src/space-weather.js` sends only date windows to the CCMC public endpoint with credentials and referrer omitted. API payloads are bounded, item shapes checked, and external URLs restricted to official CCMC paths. Partial endpoint failures remain visible. Public event data are cached separately from the private profile. On opening the route, cached events display offline; entries older than 24 hours display `STALE` and current conditions remain unknown. A fixed historical fixture is marked historical and separate from both live feeds and the synthetic radiation timeline.

The local source registry stores 12 bibliography records and is included in the app build under `research/`. The static build contains 8 source documents and 586 sparse text blocks. Its optional MiniLM index is unchanged at six chunks, so no comprehensive semantic biomedical library is claimed. The registry currently includes the active NASA-STD-3001 Volume 2 Revision F catalogue record (document date July 14, 2026); Revision D is retained as history. The summaries and catalog links do not implement standard requirements as clinical thresholds.

## Errors and corrections

1. An ownership regression test expected a foreign-owner restore to fail only during history access. The bridge correctly rejects during `init_profile`; the test now asserts at restore time.
2. The new evidence summary changed the most relevant retrieved document for the English radiation-limitation evaluation case. The fixed evaluation now accepts either the existing implementation note or the new curated summary, without changing query results or engine criteria.
3. Malformed list-valued prevention/rate-kind fields could raise a Python `TypeError` instead of a stable validation error. Type checks now reject them using the existing domain error path.
4. Offline cached DONKI events were available only after a failed manual sync or button press. The route now shows its local cache at entry and labels age/staleness; it never implies current conditions.
5. The bibliography initially marked NASA-STD-3001 Volume 2 Rev D alongside a then-current catalogue check. The NASA catalogue reports Rev F active as of July 14, 2026. Registry and summaries now list Rev F as active and Rev D as historical.

No new clinical diagnostic criteria, doses, treatment protocols, mission alert thresholds, or sensor assumptions were added.

## Actual verification results

- Full Python suite: **906 passed, 19 skipped, 0 failed** in 193.01 seconds; one existing Starlette/httpx TestClient deprecation warning.
- Full Node/browser test suite: **61 passed, 0 failed** in 10.12 seconds; Node prints a module-type reparsing warning because the existing `web-local/package.json` does not set `type=module`.
- Targeted source registry tests: **3 passed** after the final NASA standards metadata update.
- Static build: **254 synthetic parity cases**, **78 assets**, **112,736,532 bytes**, **8 source documents**, **586 sparse blocks**; builder confirms byte-identical clinical modules.
- Source integrity: `tools/build_science_integrity.py --check` returned `SOURCE_INTEGRITY_OK`; the static build includes the same integrity JSON.
- Previous full run during correction had 904 passing and 2 failures. The updated RAG expectation passed in isolation; a separate replay test passed on rerun. The final full suite above has no failures.
- One live NASA CCMC API check during implementation returned HTTP 200, CORS for the static site, and 9 FLR rows for November 1–15, 2026. Automated API tests use mocked responses, not live NASA dependencies.
- Desktop browser visual smoke test was blocked when the app's origin permission gate declined access to `http://127.0.0.1:8876/`. No alternate browser/CDP route was attempted. No screenshot or physical-device claim is made.
- The stable Cloudflare site was not changed. No preview was deployed because this continuation had no authenticated Cloudflare session.

Detailed structured status is in `MISSION_VERIFICATION_20261115.json`.

## Security and known limitations

- Browser profile records use the pre-existing encrypted IndexedDB vault. The Python reference backend still uses unencrypted SQLite at rest unless its containing volume is protected. The new manual and synthetic entries do not change this.
- A process or attacker able to modify storage, application code or unlocked memory may manipulate local records and audit history. Existing audit hashes are integrity indicators, not a hardware-backed signature or remote tamper-proof log.
- No actual CAD/HERA adapter, sensor calibration registry, dose reconstruction, location/trajectory relevance, radiation risk model, standards compliance, radiation warning, or medical action exists.
- Exercise/hydration/nutrition/sleep/well-being features only capture self-report. They do not implement NASA-approved countermeasure plans, estimate intake adequacy, diagnose mood disorders, infer sleep impairment, or rehabilitate injury.
- The new synthetic EVA values are arbitrary test data. They are not representative environmental or biomedical values and cannot be used to validate scientific behavior.
- DONKI records can be delayed, incomplete, revised, or unavailable. CCMC explicitly characterizes its data as research/prototyping quality and provides them without warranty. It is not a flight warning channel.
- Sources were selected and summarized for software provenance; no systematic review or independent grading was done. NASA standards are program-tailored; consult the full current controlled source for any real mission decision.
- No independent clinical validation, NASA operational approval, certification or flight readiness is claimed.

## Review-package and integration state

`PREVENTION_DOSIMETRY_AND_DONKI.md` documents action contracts and payload requirements. The static build is reproducible with `ASTHRAL_BUILD_OUTPUT` pointing to a new empty output directory. Build output stays ignored by Git. A zip review bundle contains changed source/tests/docs plus the verification report; screenshots are absent because browser access was declined. Development branch push remains allowed by the attached mission, but production/stable deployment is not.

## Independent follow-up needed

1. Have a space-medicine clinician, dosimetrist and NASA standards/program authority review the source mappings, terminology, units and intended populations.
2. Have an independent radiation instrumentation expert define instrument provenance, calibration, uncertainty and mission-specific acquisition contracts before sensor ingestion.
3. Complete browser visual, offline airplane-mode, profile persistence, and mobile storage acceptance with owner-approved browser access and actual target devices.
4. Validate DONKI API payloads against its live OpenAPI contract and add backoff/availability monitoring before any field use.
5. Build a separately licensed, governed literature corpus with source-specific evidence grading; do not increase coverage by treating project summaries as primary studies.
6. Implement sensor acquisition, MotionGuard or alternatives only after device availability and validation; keep activities and recorded results independent from prescriptions.
7. Conduct independent privacy/threat-model and storage-encryption review before using any real biomedical record.
