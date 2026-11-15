export const RADLAB_API = 'https://visualization.osdr.nasa.gov/radlab/api/';
export const RADLAB_DOCS = 'https://visualization.osdr.nasa.gov/radlab/gui/data-api/';
export const RADLAB_CACHE_KEY = 'asthral.radlab.historical.v1';
export const RADLAB_MAX_WINDOW_DAYS = 7;
export const RADLAB_MAX_RESPONSE_BYTES = 2 * 1024 * 1024;

export const RADLAB_QUANTITIES = Object.freeze({
  absorbed_dose_rate: Object.freeze({ label: 'Absorbed-dose rate', unit: 'μGy/h' }),
  dose_equivalent_rate: Object.freeze({ label: 'Dose-equivalent rate', unit: 'μSv/h' }),
  flux: Object.freeze({ label: 'Particle flux', unit: 'cm⁻² sr⁻¹ s⁻¹' }),
});

const REQUESTED_FIELDS = Object.freeze([
  'instrument', 'instrument_family', 'instrument_id', 'module',
  'latitude', 'longitude', 'altitude', 'B', 'L',
  ...Object.keys(RADLAB_QUANTITIES),
]);
const SAFE_FILTER = /^[A-Za-z0-9][A-Za-z0-9 ._/-]{0,79}$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

function validDate(value) {
  if (typeof value !== 'string' || !DATE.test(value)) return false;
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function validateRadLabFilters(filters = {}) {
  if (!filters || typeof filters !== 'object' || Array.isArray(filters)) throw Error('RadLab filters must be an object.');
  const spacecraft = filters.spacecraft === '' || filters.spacecraft == null ? '' : String(filters.spacecraft);
  const instrument = filters.instrument === '' || filters.instrument == null ? '' : String(filters.instrument);
  const instrumentId = filters.instrumentId === '' || filters.instrumentId == null ? '' : String(filters.instrumentId);
  if (spacecraft && !SAFE_FILTER.test(spacecraft)) throw Error('RadLab spacecraft filter contains unsupported characters.');
  if (instrument && !SAFE_FILTER.test(instrument)) throw Error('RadLab instrument filter contains unsupported characters.');
  if (instrumentId && !SAFE_FILTER.test(instrumentId)) throw Error('RadLab instrument identifier contains unsupported characters.');
  if (!validDate(filters.startDate) || !validDate(filters.endDate) || filters.startDate > filters.endDate) {
    throw Error('Choose valid RadLab observation dates in UTC order.');
  }
  const days = (Date.parse(`${filters.endDate}T00:00:00Z`) - Date.parse(`${filters.startDate}T00:00:00Z`)) / 86400000 + 1;
  if (days > RADLAB_MAX_WINDOW_DAYS) throw Error(`RadLab queries are limited to ${RADLAB_MAX_WINDOW_DAYS} days per request.`);
  const quantities = filters.quantities == null ? Object.keys(RADLAB_QUANTITIES) : filters.quantities;
  if (!Array.isArray(quantities) || quantities.length < 1 || quantities.length > Object.keys(RADLAB_QUANTITIES).length ||
      quantities.some(name => !Object.hasOwn(RADLAB_QUANTITIES, name)) || new Set(quantities).size !== quantities.length) {
    throw Error('Choose one or more documented RadLab quantities.');
  }
  return { spacecraft, instrument, instrumentId, startDate: filters.startDate, endDate: filters.endDate, quantities: [...quantities].sort() };
}

function encoded(value) { return encodeURIComponent(value).replaceAll("'", '%27'); }

/**
 * Build the documented key-value RadLab request. `timestamp%3E=` and
 * `timestamp%3C=` are intentionally emitted in NASA's documented syntax;
 * the key-value syntax cannot be mixed with the separate boolean `query=` form.
 */
export function buildRadLabUpstreamUrl(filters) {
  const query = validateRadLabFilters(filters);
  const pairs = [];
  if (query.spacecraft) pairs.push(`spacecraft=${encoded(query.spacecraft)}`);
  if (query.instrument) pairs.push(`instrument=${encoded(query.instrument)}`);
  if (query.instrumentId) pairs.push(`instrument_id=${encoded(query.instrumentId)}`);
  const endExclusive = new Date(Date.parse(`${query.endDate}T00:00:00Z`) + 86400000).toISOString().slice(0, 10);
  pairs.push(`timestamp%3E=${encoded(query.startDate)}`, `timestamp%3C=${encoded(endExclusive)}`);
  for (const field of REQUESTED_FIELDS) {
    if (RADLAB_QUANTITIES[field] && !query.quantities.includes(field)) continue;
    if (field === 'instrument' && query.instrument) continue;
    if (field === 'instrument_id' && query.instrumentId) continue;
    pairs.push(`${encoded(field)}=`);
  }
  pairs.push('format=json');
  return `${RADLAB_API}?${pairs.join('&')}`;
}

function numberOrNull(value) {
  if (value == null || value === '' || (typeof value === 'string' && ['na', 'nan', 'null'].includes(value.trim().toLowerCase()))) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function utcTimestamp(value) {
  if (typeof value !== 'string' || value.length > 64) return null;
  const normalized = /Z$|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`;
  const epoch = Date.parse(normalized);
  return Number.isFinite(epoch) ? new Date(epoch).toISOString() : null;
}

function rawRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== 'object') throw Error('RadLab returned an unsupported JSON response.');
  if (Array.isArray(payload.records)) return payload.records;
  if (Array.isArray(payload.data) && Array.isArray(payload.columns)) {
    if (payload.data.length > 100_000) throw Error('RadLab response contains too many observations for this view.');
    return payload.data.map(row => {
      if (!Array.isArray(row) || row.length !== payload.columns.length) return null;
      return Object.fromEntries(payload.columns.map((name, index) => [name, row[index]]));
    }).filter(Boolean);
  }
  throw Error('RadLab response does not contain a recognized columns/data table.');
}

export function normalizeRadLabResponse(payload, { retrievedAt = new Date().toISOString(), requested = {} } = {}) {
  const filters = validateRadLabFilters(requested);
  if (!Number.isFinite(Date.parse(retrievedAt))) throw Error('RadLab retrieval timestamp must be a valid date-time.');
  const rows = rawRows(payload);
  const start = Date.parse(`${filters.startDate}T00:00:00Z`);
  const end = Date.parse(`${filters.endDate}T23:59:59.999Z`);
  const observations = [];
  let rejectedRows = 0;
  for (const raw of rows) {
    const observedAt = utcTimestamp(raw?.timestamp);
    if (!observedAt || Date.parse(observedAt) < start || Date.parse(observedAt) > end) { rejectedRows++; continue; }
    if (filters.spacecraft && String(raw?.spacecraft ?? '').toLowerCase() !== filters.spacecraft.toLowerCase()) { rejectedRows++; continue; }
    if (filters.instrument && String(raw?.instrument ?? '').toLowerCase() !== filters.instrument.toLowerCase()) { rejectedRows++; continue; }
    if (filters.instrumentId && raw?.instrument_id !== filters.instrumentId) { rejectedRows++; continue; }
    const latitude = numberOrNull(raw.latitude), longitude = numberOrNull(raw.longitude), altitude = numberOrNull(raw.altitude);
    const location = Number.isFinite(latitude) && latitude >= -90 && latitude <= 90 &&
      Number.isFinite(longitude) && longitude >= -180 && longitude <= 180
      ? { latitude_deg: latitude, longitude_deg: longitude, altitude_km: altitude }
      : null;
    const values = {};
    for (const [name, definition] of Object.entries(RADLAB_QUANTITIES)) {
      if (filters.quantities.includes(name)) values[name] = { value: numberOrNull(raw[name]), unit: definition.unit };
    }
    observations.push({
      source: 'NASA_OSDR_RADLAB',
      classification: 'HISTORICAL',
      observed_at_utc: observedAt,
      retrieved_at_utc: retrievedAt,
      spacecraft: typeof raw.spacecraft === 'string' ? raw.spacecraft.slice(0, 120) : null,
      instrument: typeof raw.instrument === 'string' ? raw.instrument.slice(0, 160) : null,
      instrument_family: typeof raw.instrument_family === 'string' ? raw.instrument_family.slice(0, 120) : null,
      instrument_id: typeof raw.instrument_id === 'string' ? raw.instrument_id.slice(0, 120) : null,
      module: typeof raw.module === 'string' ? raw.module.slice(0, 120) : null,
      location,
      geomagnetic: { B_nT: numberOrNull(raw.B ?? raw.b), L: numberOrNull(raw.L ?? raw.l) },
      values,
      quality: 'SOURCE_REPORTED_NOT_INDEPENDENTLY_VALIDATED_BY_ASTHRAL',
    });
  }
  observations.sort((a, b) => a.observed_at_utc.localeCompare(b.observed_at_utc));
  return {
    provider: 'NASA_OSDR_RADLAB',
    source_url: buildRadLabUpstreamUrl(filters),
    documentation_url: RADLAB_DOCS,
    filters,
    retrieved_at_utc: retrievedAt,
    retrieval_state: 'HISTORICAL_QUERY_RESPONSE',
    classification: 'HISTORICAL_PUBLIC_ENVIRONMENTAL_OBSERVATIONS',
    observations,
    missing_value_count: observations.reduce((total, row) => total + Object.values(row.values).filter(item => item.value === null).length, 0),
    invalid_or_out_of_window_rows: rejectedRows,
    interpretation_limit: 'Instrument readings are not individual astronaut dosimetry; ASTHRAL does not infer personal dose or EVA exposure from these data.',
  };
}

export function buildRadLabProxyRequest(filters) {
  const canonical = validateRadLabFilters(filters);
  const params = new URLSearchParams({
    startDate: canonical.startDate,
    endDate: canonical.endDate,
    quantities: canonical.quantities.join(','),
  });
  if (canonical.spacecraft) params.set('spacecraft', canonical.spacecraft);
  if (canonical.instrument) params.set('instrument', canonical.instrument);
  if (canonical.instrumentId) params.set('instrumentId', canonical.instrumentId);
  return `/api/radlab?${params.toString()}`;
}

export function parseRadLabCache(storage = globalThis.localStorage, now = Date.now()) {
  try {
    const raw = storage?.getItem(RADLAB_CACHE_KEY);
    if (!raw || new TextEncoder().encode(raw).byteLength > RADLAB_MAX_RESPONSE_BYTES) return null;
    const snapshot = JSON.parse(raw);
    if (snapshot?.provider !== 'NASA_OSDR_RADLAB' || !Array.isArray(snapshot.observations) || !Number.isFinite(Date.parse(snapshot.retrieved_at_utc))) return null;
    const ageMs = now - Date.parse(snapshot.retrieved_at_utc);
    return { ...snapshot, cache_state: ageMs < 0 || ageMs > 86400000 ? 'STALE_CACHED_HISTORICAL' : 'CACHED_HISTORICAL', age_ms: Math.max(0, ageMs) };
  } catch { return null; }
}

export function cacheRadLabSnapshot(snapshot, storage = globalThis.localStorage) {
  try {
    if (snapshot?.provider !== 'NASA_OSDR_RADLAB' || !Array.isArray(snapshot.observations)) return false;
    const serialized = JSON.stringify(snapshot);
    if (new TextEncoder().encode(serialized).byteLength > RADLAB_MAX_RESPONSE_BYTES) return false;
    storage?.setItem(RADLAB_CACHE_KEY, serialized);
    return true;
  } catch { return false; }
}
