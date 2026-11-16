# Galactic UI and synthetic atmosphere behavior

## Visual navigation

The horizontal workspace navigation remains in place. Each of the 22 current route tabs selects its own local SVG starfield, while the nebula palette follows a smooth 10-tab wave: blue at tabs 1, 11 and 21; violet near tabs 6 and 16; and an indigo transition between them. The palette returns to blue instead of progressing only once across the full navigation. The two background layers cross-fade, with a restrained scale change for depth. All 24 SVG assets are included in the static build manifest and are available to the existing offline cache. The original local backdrop remains a fallback. No live astronomical imagery or telemetry is implied.

The body map remains within Overview; there is no separate Human Anatomy navigation item. Recorded systemic values remain read-only in that view. The adjacent ECG panel says that recorded ECG samples are unavailable unless an authorized source provides compatible samples. In Synthetic Test Mode it shows a heart-rate-driven illustration, with a persistent `SYNTHETIC TEST MODE — NOT LIVE MEDICAL DATA` indicator. The illustration disappears when the mode exits or the profile is locked.

## Synthetic Test Mode

Physiological controls are hidden until the user explicitly enters Synthetic Test Mode. Simulator values are kept in page memory, reset on exit or profile lock, and never submitted to the clinical engine or written to the health-history store. The only generated notices are transition-based software training notices. `View details` opens Monitoring at the simulator. Changing an input within an already active training condition updates its displayed value without creating a new notice for every slider movement.

The heart-rate and SpO₂ training boundaries already present in the fixture remain software examples; they are not astronaut limits or validated clinical alert criteria. The engine remains the authority for genuine deterministic assessments.

## Cabin and spacesuit inputs

Cabin and spacesuit values are independent. Each has its own O₂ concentration slider and total-pressure input. The interface computes the simplified dry-gas quantity:

`oxygen partial pressure (kPa) = total pressure (kPa) × oxygen concentration (%) / 100`

For the nominal fixture values, cabin `101.3 kPa × 21%` is shown as `21.27 kPa`; spacesuit `29.6 kPa × 100%` is shown as `29.60 kPa`. These are arithmetic outputs from synthetic inputs, not life-support telemetry or inspired-oxygen values. The displayed concentration and partial pressure do not determine or modify astronaut SpO₂.

CO₂ concentration and partial pressure are explicitly unavailable. Spacesuit oxygen reserve/supply telemetry is also unavailable. No CO₂ state, remaining oxygen, EVA exposure or physiological coupling is inferred.

The separate atmosphere training fixture uses the illustrative boundaries `<10 kPa` and `>40 kPa` for calculated dry-gas oxygen partial pressure, version `atmosphere-training-fixture-1`. These boundaries were added solely to exercise warning transitions in software. They have no NASA or clinical authority and must not be used for mission operations. Exact equality to either boundary does not trigger that software warning. Missing inputs yield an insufficient-information notice; values outside the simulator's declared input bounds are marked invalid. A notice is not a determination of atmospheric safety.

The NASA OCHMO habitable-atmosphere technical brief is provided as background reading for atmospheric quantities: <https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-003-habitable-atmosphere.pdf>. It does not validate the illustrative training boundaries used by this simulator.

## Focused verification

The palette generator and its deterministic checks are `tools/cosmic_wave_palette.py` and `tools/test_cosmic_wave_palette.py`. The browser acceptance script `tools/browser_galaxy_simulator_acceptance.py` checks blue-to-violet-to-blue changes across the 10-tab period, per-route scene selection, cross-fade, overview layout, mode gating, independent cabin and spacesuit calculations, warning transitions, missing-pressure handling, SpO₂ independence, ECG labeling and heart-rate response, reset behavior, unchanged synthetic history, and a mobile viewport. `tools/browser_galaxy_offline_acceptance.py` installs the preview cache, disables browser connectivity, reloads the app and retrieves representative wave scenes from the service worker cache. In the 2026-11-15 Cloudflare preview run, 139 offline resources were verified and both scenes returned successfully after the offline reload. The related unit tests are in `web-local/tests/physiology-simulator.test.mjs`.

These software checks use synthetic inputs only. They do not constitute clinical validation, engineering qualification of a spacesuit atmosphere, sensor testing or flight certification.
