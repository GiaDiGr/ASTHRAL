# ASTHRAL preventive tracking and radiation import (2026-11-15)

## Scope and safety

These browser-local workflows are research and self-tracking features, not a fitness plan or clinical recommendation. Training examples are generic educational movement descriptions. The user selects whether to use them and records workload, sets, repetitions, time, and optional perceived exertion on a bounded self-rating scale. These records remain self-report. ASTHRAL does not set goals, infer fitness, assess exercise form, authorize activities, or execute treatment. MotionGuard remains unavailable in the browser release because no verified local pose model/runtime is packaged.

Entries go through `prevention_add`, are normalized by the local Python engine and are appended to the encrypted profile store with the existing hash-chained audit. Checkpoints are append-only; interrupted sessions are recovered as paused so time during application shutdown is not counted as exercise. Saves do not trigger a destructive UI refresh; the app's global history view remains current while open. The session progress fraction is `completed / started` and must not be presented as adherence to a schedule or as a health score.

Nutrition uses an offline compact subset generated from the official USDA FoodData Central Foundation Foods JSON release 2026-10. The source archive SHA-256 is `dd414cc9f1a132626bad354ef6655972c78b44aff14f16114dc899708663c579`; the bundled catalog is independently hash-checked using `foods.json.sha256` (`a09e222154963247cbb4f24b0a643385a6f2c5fac26d4aa0956dab34d1d6ad17`). It contains 424 entries. Energy is unavailable for 329 entries, protein for 17, carbohydrate for 50, fat for 31, and water for 8; missing source values remain null. Backend meal logging relooks up the FDC ID and computes the user-entered gram scale from the bundled dataset instead of trusting browser-supplied nutrient values. Values are composition estimates based on edible portions and do not represent mission-packaged food contents or intake measurement. Hydration is a separate self-entered fluid amount with no goal or interpretation.

Sleep duration is calculated from timezone-qualified start/end timestamps, capped at 24 hours, and validated server-side against the supplied duration. Sleep quality and fatigue remain subjective self-reports. Well-being notes and optional ratings are local-profile data; no screening instrument, passive surveillance, or diagnosis is performed.

Radiation CSV imports use an exact fixed header and validate each record through the existing unit, quantity, quality, provenance, and timezone rules. Batch insert is all-or-nothing; duplicate keys and malformed rows prevent the entire import. The `MEASURED` mode represents the source label, not ASTHRAL verification of hardware. No Gy-to-Sv conversion, exposure inference from DONKI, or operational warning is performed.

## USDA provenance and licensing

USDA FoodData Central states its data are public domain / CC0 and requests attribution. Suggested citation: U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, 2019. fdc.nal.usda.gov. Source release page: https://fdc.nal.usda.gov/download-datasets/ . This compact catalog is regenerated with `python tools/build_nutrition_catalog.py <official-foundation-json-zip> web-local/src/nutrition/foods.json`.

## Radiation CSV contract

The first row must exactly equal:

```text
quantity_kind,value,unit,timestamp,mode,quality,mission_segment,location,source,instrument_id,uncertainty_value,uncertainty_unit,note
```

Values use the existing `engine/vigile/dosimetry.py` accepted quantity and unit set. Timestamp must include an explicit timezone. If uncertainty is provided, its unit must match the measurement. Empty instrument IDs are allowed but then rates cannot be integrated as sensor-continuous data. Imported records remain sensor-unverified. File size is limited to 5 MB and 10,000 records.

## Tests added

`engine/tests/test_prevention.py` covers USDA nutrient lookup/scaling, unknown nutrient preservation, structured exercise session bounds, and sleep timestamp consistency. `engine/tests/test_browser_mission_support.py` verifies radiation batch atomicity and audit. `web-local/tests/exercise.test.mjs` covers movement example structure, elapsed-time/pause/resume behavior, sleep interval bounds, session checkpoint deduplication, and synthetic provenance. `web-local/tests/radiation-csv.test.mjs` covers strict schema parsing and malformed input.

## Current unverified areas

The previous browser local-origin permission request was denied, so this release change cannot claim visual acceptance or physical end-to-end browser testing. MotionGuard genuine inference remains blocked by absent model weights/runtime. No human-subject or astronaut data are included in these tests. SQLite encryption remains provided by the existing browser vault around the serialized database; exported plaintext database handling outside the vault is not covered by this change.
