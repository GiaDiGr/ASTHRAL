# NASA data and anatomy integration

Reviewed: 2026-11-15. This describes a software integration boundary; it does not establish clinical, flight, radiation-safety, or NASA operational validation.

## NASA RadLab Radiation Explorer

The browser-only Radiation Explorer queries the public NASA OSDR RadLab API for ISS instrument records. The request uses RadLab's documented key-value syntax (`spacecraft`, a half-open UTC timestamp interval, requested instrument fields, and `format=json`). ASTHRAL keeps this syntax separate from the API's Boolean `query=` syntax because NASA documents them as mutually exclusive. App input is limited to seven inclusive UTC calendar dates per request to bound transfer and browser work; this is an ASTHRAL limit, not a NASA API limit.

NASA documents `absorbed_dose_rate` in μGy/hour, `dose_equivalent_rate` in μSv/hour, `flux` in cm⁻² sr⁻¹ s⁻¹, and location fields in degrees and kilometers where available. Its documentation says location fields are currently tracked for the ISS and can be blank for other spacecraft. RadLab instrument IDs and ISO timestamp strings are case-sensitive. The normalizer accepts the source's lower-case `b`/`l` fields as aliases for the documented magnetic-field and McIlwain-L values; source numeric values are otherwise preserved without unit conversion, averaging, interpolation, or personal-dose calculation. See the [NASA RadLab Data API](https://visualization.osdr.nasa.gov/radlab/gui/data-api/).

NASA release notes describe some newly curated RAD, REM, and TEPC data as preliminary, with a median cadence of 24 hours; that statement does not describe every RadLab dataset or guarantee an observation schedule. Users can open the [RadLab release history](https://visualization.osdr.nasa.gov/radlab/gui/knowledgebase/Release_history) from the explorer. ASTHRAL displays returned timestamps and retrieval timestamps separately, keeps missing values null, filters rows against the requested spacecraft, dates and instrument IDs, and rejects out-of-range coordinates. Each value is source-reported, not independently validated by ASTHRAL.

The user-facing provenance states are:

| State | Meaning |
|---|---|
| `HISTORICAL_QUERY_RESPONSE` | NASA returned a public archive query now; the observations remain historical, not live telemetry. |
| `HISTORICAL` | A timestamped public instrument record returned by NASA; not live telemetry. |
| `CACHED_HISTORICAL` | A prior public archive query shown from the local cache, less than 24 hours after retrieval. |
| `STALE_CACHED_HISTORICAL` | A prior archive query older than 24 hours, shown only as historical context. |
| `SIMULATED` | Not emitted by the RadLab adapter. EVA synthetic values stay in their own scenario and report fields. |

The default browser view queries NASA through the same-origin `/api/radlab` Cloudflare Pages Function. That GET-only function accepts a fixed parameter allowlist, rejects cross-origin requests when an `Origin` header is present, constructs only the fixed official NASA endpoint, requests upstream redirects in manual mode (the Workers runtime does not support `redirect: "error"`) and rejects every 3xx response, disables network/edge caching with `no-store`, and caps upstream and normalized responses at 2 MiB. It sends no ASTHRAL health/profile data, credentials, or authorization tokens. The local preview implements the same restricted upstream builder in `web-local/radlab_proxy.py` through `web-local/serve.py`. The browser also bounds its last-query localStorage cache to 2 MiB. If the network is unavailable, only a matching cached archive query can be shown; cache age remains visible.

The explorer renders actual returned observations as timestamped scatter points, plots only returned ISS coordinates on a graticule, places coordinate-bearing historical points on the existing 3D Earth, and exports the normalized source-attributed data as JSON or CSV. The chart is not a dose map. The globe markers are not cumulative exposure, crew coordinates, or current radiation. The view never feeds measurements into the EVA advisory or clinical engine. NASA describes curated instrument observations and source units; those records are not an individual astronaut dosimeter or operational EVA limit.

### Browser integration contract

- Frontend owner: mount `mountRadLabExplorer(container, { onObservations, onContext })` from `web-local/src/radlab-view.js` inside Mission Control. The callback receives normalized historical observations, the currently selected archive row, and the query snapshot. Do not reinterpret them as personal measurements.
- Mission Control: `web-local/src/mission-control.js` forwards valid historical ISS coordinates to the existing `mountOrbitalView` instance. The orbital marker count and selected timestamp stay visibly labeled as historical RadLab data.
- Local app: serve through `web-local/serve.py`; `/api/radlab` invokes the fixed-host local proxy. Do not open `index.html` with `file://`, which has no same-origin API endpoint.
- Cloudflare Pages: deploy the built static directory with `web-local/functions/` supplied as the Pages functions directory. The platform function is tested with the same client contract. No secret is required.
- LLM/RAG: may read the normalized, authorized public archive result and the source-register entries for explanation. It cannot write into the proxy, alter a measurement, create a dose estimate, or change a clinical/mission rule.

### Example request and response shape

```http
GET /api/radlab?startDate=2023-01-01&endDate=2023-01-01&spacecraft=ISS&quantities=absorbed_dose_rate%2Cdose_equivalent_rate%2Cflux
Accept: application/json
```

In the ASTHRAL proxy contract both selected dates are inclusive UTC calendar dates; when start and end are the same date this is a one-day query. The adapter converts that selection to NASA's half-open interval ending at the next UTC midnight.

```json
{
  "provider": "NASA_OSDR_RADLAB",
  "classification": "HISTORICAL_PUBLIC_ENVIRONMENTAL_OBSERVATIONS",
  "filters": { "spacecraft": "ISS", "startDate": "2023-01-01", "endDate": "2023-01-01", "quantities": ["absorbed_dose_rate", "dose_equivalent_rate", "flux"] },
  "retrieved_at_utc": "<request retrieval time>",
  "retrieval_state": "HISTORICAL_QUERY_RESPONSE",
  "observations": [
    {
      "source": "NASA_OSDR_RADLAB",
      "classification": "HISTORICAL",
      "observed_at_utc": "<NASA source timestamp>",
      "retrieved_at_utc": "<request retrieval time>",
      "location": null,
      "values": { "absorbed_dose_rate": { "value": null, "unit": "μGy/h" } },
      "quality": "SOURCE_REPORTED_NOT_INDEPENDENTLY_VALIDATED_BY_ASTHRAL"
    }
  ],
  "interpretation_limit": "Instrument readings are not individual astronaut dosimetry."
}
```

The response is schematic and contains no NASA observation; `null` demonstrates the missing-value contract.

## OSDR Biological Data API and Environmental Data App

The OSDR Biological Data API documentation was reviewed for its dataset/assay/sample REST interface and tabular metadata/data query interface. OSDR contains heterogeneous experiments; a dataset's population, assay, units, collection times, processing and reuse terms must be reviewed individually. ASTHRAL registers the API as `NASA_OSDR_BIODATA` but does not fetch it into current individual monitoring or clinical decisions. See the [NASA OSDR Biological Data API](https://visualization.osdr.nasa.gov/biodata/api/).

NASA's Environmental Data App is a portal for historical ISS cabin, hardware environmental telemetry, and radiation data. It is not a uniform public JSON API contract for ASTHRAL, and a hardware/cabin temperature is not astronaut body temperature. The current integration registers EDA as a reviewed link only; no EDA data is imported or used in clinical interpretation. See [NASA EDA](https://visualization.osdr.nasa.gov/eda/).

NASA's DONKI API remains the single existing space-weather client. The application uses the NASA CCMC base URL published for the September 2026 migration, while preserving the existing event schemas and cache behavior. DONKI context does not become a personal radiation measurement or clinical/operational alarm. The source notice is [NASA CCMC's API update](https://ccmc.gsfc.nasa.gov/news/major-updates/).

## Interactive anatomy view

The Human Anatomy route now lazy-loads a smooth external-body GLB from [Innerscene's model page](https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89). The provider describes it as an adaptation of MakeHuman assets and licenses it under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The bundled file is 4,498,248 bytes, SHA-256 `86c7cdfa989924b45e2e5110c131a4a4e6251ceb4e71246be68e468f3a32ca86`; the provider describes a neutral adult male base mesh in A-pose at approximately 119 × 49 × 179 cm. Attribution and integrity are recorded in `web-local/src/vendor/anatomy/ATTRIBUTION.md` and `web-local/src/vendor/anatomy/model-manifest.json`. The previous Z-Anatomy muscle mesh remains in the source tree with its license and attribution intact, but is excluded from application and offline bundles. See the [MakeHuman license](https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md), [Z-Anatomy license](https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/License.txt) and [conversion project attribution](https://github.com/ArianArsenal/anatomy-explorer#credits--license).

The interaction contract is defined by 28 stable IDs in `web-local/src/anatomy-regions.js`. Source-model bone identifiers and explicit head, eye, trunk and joint landmarks assign each vertex; a triangle receives a selectable region only when all three of its vertices agree. Indexed triangles are grouped by region and base material. The raycaster reads the nearest visible mesh face's region ID, and a region with ambiguous surface geometry clears the selection. The same face groups drive the highlight, preventing vertex-color interpolation from tinting adjacent regions. This does not use muscle-name regular expressions, does not raycast through the visible surface and does not keep a stale prior selection on an unresolved hit. The camera is aimed after model normalization. Anterior/posterior orientation, 360-degree rotation, zoom, pan, screen-reader-labelled region selector, mouse and touch gestures remain available.

This is an external-body navigation aid with generic male morphology, not a patient-specific model, diagnostic atlas, clinical localization system or validated astronaut representation. Region selection does not localize measurements or diagnoses; missing regional data do not imply normality. Any ambiguous mesh face remains unrecognized. The model and renderer can be integrity-checked into the optional offline cache; a 2D schematic remains available if WebGL/model loading fails. For the implementation audit and exact automated acceptance results, see `docs/asthral/ANATOMY_BODY_MAP_AUDIT_20261116.md`.

## Validation boundary

Automated unit and browser acceptance can verify request construction, parsing, state labels, source/time/unit preservation, filters, export, cache fallback, plot rendering, model loading and controls. It cannot validate the accuracy, completeness, meaning, health significance, operational relevance, medical threshold suitability or flight qualification of the upstream data or model. Independent specialist review is still required before any clinical or flight use.
