# ASTHRAL prevention, radiation records, and DONKI integration

Review/build: 2026-11-15. These features are a research prototype. They do not validate clinical decisions, dosimeters, radiation models, mission safety, NASA requirements, or exercise prescriptions.

## Current interfaces

All private journal and radiation records are local-profile records written through `web-local/src/browser_bridge.py` to the same SQLite/audit store used by the browser engine. On persistent profiles the serialized database remains inside the existing encrypted browser-vault envelope in IndexedDB. The static service worker caches only build assets and the public DONKI cache is separate `localStorage` metadata; the DONKI cache schema rejects responses marked as containing personal data. The browser adapter assigns the unlocked owner ID and rejects imported database records scoped to another owner.

### Prevention self-report

Browser action: `prevention_add`, followed by `prevention_list` or the existing `history` action. Supported `entry_type` values:

| Type | Required data | Optional data | Meaning |
|---|---|---|---|
| `EXERCISE_SESSION` | timezone-qualified `occurred_at`, `duration_minutes` | `workout_type`, `perceived_exertion_0_10`, label/note | Self-described activity only; MotionGuard is unavailable here. |
| `HYDRATION` | `amount_ml` | label/note | User-entered volume; no hydration target or status. |
| `MEAL_NOTE` | nonempty label or note | — | User text; no nutrition composition inference. |
| `SLEEP` | `duration_minutes` | `subjective_quality_1_5` | Voluntary diary; no validated sleep measurement or impairment inference. |
| `WELLBEING` | at least one rating or note | `mood_rating_1_5`, `stress_rating_1_5` | Voluntary check-in; no screening, diagnosis or crisis classifier. |

Every normalized record has source `SELF_REPORTED`, `sensor_verified=false`, `clinical_interpretation=NOT_PROVIDED`, and `clinical_execution=BLOCKED`. The browser form collects only the fields for the selected entry type. Values are bounded and timestamps require an explicit timezone.

### Radiation record

Browser actions: `radiation_add`, `radiation_list`, `radiation_integrate`. There is no sensor adapter or automatic import. Each input declares a physical `quantity_kind`, unit, timestamp, `mode` (`MEASURED`, `MODELLED`, `SYNTHETIC`), quality, mission segment, location, source, optional instrument and model provenance, and optional same-unit uncertainty.

The service permits unit conversion only within the same quantity family. It never converts Gy to Sv. Trapezoidal rate integration includes only adjacent `MEASURED`, `VALID` records from the same nonempty instrument identifier, mission segment and location, with a user-specified maximum gap. A modelled or synthetic reading cannot enter this integral. Each accepted interval declares its linear-between-samples assumption. Ineligible intervals stay gaps; no interpolation is performed across them. Cumulative counter decreases are recorded as reset/rollover review items; no delta is assigned across a decrease. Duplicates are reported. All outputs have `clinical_interpretation=NOT_PROVIDED` and `execution=BLOCKED`.

The synthetic EVA widget is available only in the disposable demo. Its values are arbitrary UI fixtures, not radiation transport output, exposure measurements or an environment model; a fixture event and fixture readings are independent.

### NASA CCMC DONKI

`web-local/src/space-weather.js` calls `https://ccmc.gsfc.nasa.gov/DONKI-API/get/` with bounded UTC date parameters and fixed endpoints for FLR, CME, SEP, GST, IPS, RBE and notifications. Requests use GET, omit credentials and referrer, reject redirects, bound response size and validate the event-list shape. No profile identifier, health value or crew location is sent. Untrusted text is rendered with DOM `textContent`; links are accepted only for HTTPS links on `ccmc.gsfc.nasa.gov` below `/DONKI/`.

Partial endpoint failures are surfaced while valid endpoints remain usable; total endpoint failure is reported. The last valid public result is cached locally without a profile. Opening the view shows cached events without Internet access and marks records older than 24 hours stale; current conditions are still displayed as unknown. A fixed historical event fixture is clearly labeled historical, not live or current. No push alerts, personal exposure derivation, trajectory/location relevance, risk score, or clinical/operational warning is produced.

## Team integration contracts

- **Frontend:** use the existing local browser worker/bridge to call documented actions. Display provenance, mode, quality, units, gaps, stale state and blocked status. Do not infer personal dose or exercise/health conclusions in JavaScript.
- **Sensors/import:** implement a new separately reviewed adapter that validates device identity, unit, time, calibration/provenance, quality and owner. Keep a manual value explicitly unverified until verified provenance exists. Never re-label synthetic input as measured.
- **Local LLM/RAG:** may read only authorized local evaluation outputs and hash-verified references via existing read contracts. DONKI records and self-reports are not clinical evidence or instructions. Do not grant a writer action, credentials, or direct rule access.
- **Resource optimizer:** can benchmark this deterministic validation/integration code with synthetic fixtures, but must not suppress provenance checks, unit checks, audit writes or critical engine decisions. DONKI retrieval and model inference remain optional.

## Local verification commands

```powershell
$project = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_AUTONOMOUS_MISSION_20261115'
$python = 'C:\Users\Gianni\Documents\Codex\ASTHRAL_UNIFIED_WEB_20261115\engine\.venv\Scripts\python.exe'
$env:PYTHONPATH = "$project\engine;$project\web-local\src"
& $python -m pytest "$project\engine\tests\test_dosimetry.py" "$project\engine\tests\test_prevention.py" "$project\engine\tests\test_browser_mission_support.py" "$project\engine\tests\test_space_science_registry.py" -q
$env:ASTHRAL_BUILD_OUTPUT = "$project\web-local\build-output-mission-final-20261115"
& $python "$project\web-local\build.py"
```

To serve the isolated static build for your own browser review:

```powershell
Set-Location "$project\web-local\build-output-mission-final-20261115"
& $python -m http.server 8876 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8876/`. This turn's browser preview was not visually inspected because the desktop browser permission gate declined access.
