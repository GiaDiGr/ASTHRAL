# ASTHRAL synthetic mission walkthrough

All values in this walkthrough are fabricated software fixtures. They are not measured astronaut data, dose predictions, physiological targets, care instructions or training prescriptions.

1. Open the browser-local app and choose **Explore Synthetic Demo**. This is a temporary in-memory profile; closing the page discards its records.
2. On Dashboard choose **Load synthetic mission observations**. The existing demo creates five observations, a baseline and a monitoring cycle from the checked-in deterministic fixtures. Review the timestamps, quality labels and engine-generated state.
3. Navigate to **Prevention & recovery**. Choose **Load synthetic prevention journal (temporary demo only)**. Five arbitrary entries appear as `SYNTHETIC FIXTURE`: exercise, hydration volume, meal note, sleep diary and voluntary well-being check-in. No goals or recommendations are calculated.
4. Navigate to **Space Weather**. Open **Fixed historical NASA fixture (offline reference; not current)**. It is an old official record presented only as a historical fixture. Current conditions remain unknown unless the optional online CCMC query succeeds.
5. Navigate to **Space Weather & Radiation**. Choose **Load synthetic timeline in this temporary demo**. Three arbitrary synthetic dose-rate rows are stored separately from the historical event. They cannot be integrated as measured readings, and no cause/effect or crew dose is inferred.
6. Review the offline source register within prevention, space weather and radiation views. It provides bibliographic metadata and official NASA links; only ASTHRAL-authored short summaries are stored locally.
7. Navigate to the existing **Medical Assistant** and **Clinical Assessment** routes. Use only for software demonstration. Assistant availability depends on the locally installed model. Review engine outputs and their data sufficiency/authorization states; do not enter real health data or treat output as clinical validation.

## Reset

Use **Lock** and close the temporary demo page. Start a new synthetic demo to get a clean, empty temporary profile. The runbook does not require deleting any saved or encrypted user profile.

## Verification boundary

The automated Node suite exercises the public DONKI parser/cache contracts, including stale cache states; Python tests exercise prevention/radiation normalization, local persistence, audit and profile ownership. The static build includes the feature code and local source registry. A desktop visual/browser test of this branch was not completed because the app's origin permission gate declined access. No physical-device or flight-operations test was performed.
