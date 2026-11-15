export const NASA_DATA_SOURCES = Object.freeze([
  Object.freeze({
    id: 'NASA_OSDR_RADLAB', institution: 'NASA Open Science Data Repository / RadLab',
    endpoint: 'https://visualization.osdr.nasa.gov/radlab/api/', documentation: 'https://visualization.osdr.nasa.gov/radlab/gui/data-api/',
    release_history: 'https://visualization.osdr.nasa.gov/radlab/gui/knowledgebase/Release_history',
    method: 'GET', parameters: Object.freeze(['spacecraft', 'instrument', 'instrument_id', 'timestamp>=', 'timestamp<', 'absorbed_dose_rate', 'dose_equivalent_rate', 'flux', 'latitude', 'longitude', 'altitude', 'B', 'L', 'format=json']),
    timestamps: 'Source timestamp is retained as UTC; retrieval timestamp is captured separately.',
    units: Object.freeze({ absorbed_dose_rate: 'μGy/h', dose_equivalent_rate: 'μSv/h', flux: 'cm⁻² sr⁻¹ s⁻¹', latitude: 'deg', longitude: 'deg', altitude: 'km', B: 'nT', L: 'unitless' }),
    provenance: 'HISTORICAL_PUBLIC_ENVIRONMENTAL_OBSERVATIONS', cache: 'Network responses: no-store. The latest normalized result may be cached locally for labeled historical offline review. Cadence and data status vary by dataset; consult NASA release history.',
    test_status: 'HTTP_200_AND_JSON_SCHEMA_OBSERVED_2026-11-15; LIVE BROWSER PROXY AND HISTORICAL LABEL ACCEPTANCE IN CURRENT TEST SUITE.',
    interpretation: 'Instrument-level environmental readings. Not an individual astronaut dosimeter, clinical threshold, EVA limit or inferred personal dose.',
  }),
  Object.freeze({
    id: 'NASA_CCMC_DONKI', institution: 'NASA Community Coordinated Modeling Center',
    endpoint: 'https://ccmc.gsfc.nasa.gov/DONKI-API/get/', documentation: 'https://ccmc.gsfc.nasa.gov/DONKI/',
    method: 'GET', parameters: Object.freeze(['event endpoint', 'startDate', 'endDate', 'notifications type']),
    timestamps: 'Event time and local retrieval time are separate UTC values.',
    units: Object.freeze({}), provenance: 'OBSERVED_PUBLIC_EVENT_OR_ANALYSIS_RECORD', cache: 'Existing app cache with freshness indication; no user or health data sent.',
    test_status: 'EXISTING_LIVE_AND_FIXTURE_COVERAGE_RECORDED_IN_MISSION_SUPPORT_DOCUMENTATION.',
    interpretation: 'Research/prototyping space-weather context; does not measure personal exposure or establish immediate spacecraft hazard.',
  }),
  Object.freeze({
    id: 'NASA_OSDR_BIODATA', institution: 'NASA Open Science Data Repository',
    endpoint: 'https://visualization.osdr.nasa.gov/biodata/api/v2/', documentation: 'https://visualization.osdr.nasa.gov/biodata/api/',
    method: 'GET', parameters: Object.freeze(['/datasets/', '/dataset/{accession}/', '/query/metadata/', '/query/data/']),
    timestamps: 'Collection, mission and experiment timestamps are dataset-specific metadata and must be interpreted per study.',
    units: 'Study-specific; no global physiological unit contract.', provenance: 'EXPERIMENTAL_BIOLOGICAL_DATASET', cache: 'Not fetched by the clinical application; record-specific caching/reuse requires dataset review.',
    test_status: 'DOCUMENTATION_REVIEWED; NOT CONNECTED TO CLINICAL EVALUATION.',
    interpretation: 'Multi-modal studies can include humans, animals, model organisms, cells, hardware and processed omics. Dataset metadata must be reviewed before use; never substitute for a current human health measurement.',
  }),
  Object.freeze({
    id: 'NASA_OSDR_EDA', institution: 'NASA Open Science Data Repository / Environmental Data App',
    endpoint: 'https://visualization.osdr.nasa.gov/eda/', documentation: 'https://visualization.osdr.nasa.gov/eda/',
    method: 'Web data tables and downloads; no stable public JSON API contract verified for ASTHRAL.', parameters: Object.freeze(['mission', 'telemetry/data tables', 'environmental and radiation data']),
    timestamps: 'Mission and hardware/experiment-specific timestamps; inspect the source table before interpreting.',
    units: 'Dataset-specific; examples include temperature, relative humidity, CO₂ and radiation tables.', provenance: 'HISTORICAL_MISSION_ENVIRONMENTAL_OR_HARDWARE_DATA', cache: 'No ASTHRAL integration or local cache.',
    test_status: 'EVALUATED_NOT_INTEGRATED_2026-11-15.',
    interpretation: 'Relevant as historical mission-environment research; the current surfaced examples include Rodent Research hardware/platform data. Not human body temperature, crew telemetry or an individual exposure record.',
  }),
]);

export function getNasaDataSource(id) {
  return NASA_DATA_SOURCES.find(source => source.id === id) ?? null;
}
