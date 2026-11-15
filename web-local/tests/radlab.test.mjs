import test from 'node:test';
import assert from 'node:assert/strict';
import {
  RADLAB_CACHE_KEY, RADLAB_MAX_WINDOW_DAYS, buildRadLabProxyRequest,
  buildRadLabUpstreamUrl, cacheRadLabSnapshot, normalizeRadLabResponse,
  parseRadLabCache, validateRadLabFilters,
} from '../src/radlab.js';
import { onRequest } from '../functions/api/radlab.js';

const filters = { spacecraft: 'ISS', startDate: '2023-01-01', endDate: '2023-01-01', quantities: ['flux', 'absorbed_dose_rate', 'dose_equivalent_rate'] };

test('RadLab request follows NASA key-value syntax and retains the half-open time window', () => {
  const url = new URL(buildRadLabUpstreamUrl({ ...filters, instrumentId: 'REM-Lid' }));
  assert.equal(url.origin, 'https://visualization.osdr.nasa.gov');
  assert.equal(url.pathname, '/radlab/api/');
  assert.equal(url.searchParams.get('spacecraft'), 'ISS');
  assert.equal(url.searchParams.get('timestamp>'), '2023-01-01');
  assert.equal(url.searchParams.get('timestamp<'), '2023-01-02');
  assert.equal(url.searchParams.get('instrument_id'), 'REM-Lid');
  assert.equal(url.searchParams.getAll('instrument_id').length, 1);
  assert.equal(url.searchParams.get('format'), 'json');
  assert.match(buildRadLabProxyRequest(filters), /^\/api\/radlab\?/);
});

test('RadLab filters reject invalid dates, oversized windows, unsafe filters and unknown quantities', () => {
  assert.throws(() => validateRadLabFilters({ ...filters, startDate: '2023-02-30' }), /valid RadLab/);
  assert.throws(() => validateRadLabFilters({ ...filters, endDate: '2023-01-09' }), new RegExp(`${RADLAB_MAX_WINDOW_DAYS} days`));
  assert.throws(() => validateRadLabFilters({ ...filters, instrument: 'REM&format=html' }), /unsupported characters/);
  assert.throws(() => validateRadLabFilters({ ...filters, quantities: ['dose'] }), /documented RadLab quantities/);
});

test('RadLab normalizer preserves original quantities, nulls and source timestamps without interpolation', () => {
  const payload = {
    columns: ['timestamp', 'spacecraft', 'instrument', 'instrument_family', 'instrument_id', 'module', 'absorbed_dose_rate', 'dose_equivalent_rate', 'flux', 'latitude', 'longitude', 'altitude', 'B', 'L'],
    index: [0, 1, 2],
    data: [
      ['2023-01-01T00:00:00', 'ISS', 'REM-Lid', 'Timepix', 'REM-Lid', 'Columbus', 2.5, null, 0.17, 30.14817, 3.48303, 422.3, 15220, 2.1],
      ['2023-01-01T01:00:00Z', 'ISS', 'DosTel', 'TEPC', 'DosTel1', 'Columbus', null, null, 0.2, 100, 200, null, null, null],
      ['2023-01-02T00:00:00', 'ISS', 'REM-Lid', 'Timepix', 'REM-Lid', 'Columbus', 7, 8, 0.3, 0, 0, 420, 5, 4],
    ],
  };
  const result = normalizeRadLabResponse(payload, { requested: filters, retrievedAt: '2023-01-03T00:00:00Z' });
  assert.equal(result.classification, 'HISTORICAL_PUBLIC_ENVIRONMENTAL_OBSERVATIONS');
  assert.equal(result.observations.length, 2);
  assert.equal(result.observations[0].observed_at_utc, '2023-01-01T00:00:00.000Z');
  assert.equal(result.observations[0].values.absorbed_dose_rate.value, 2.5);
  assert.equal(result.observations[0].values.absorbed_dose_rate.unit, 'μGy/h');
  assert.equal(result.observations[0].values.dose_equivalent_rate.value, null);
  assert.equal(result.observations[0].values.flux.unit, 'cm⁻² sr⁻¹ s⁻¹');
  assert.deepEqual(result.observations[0].location, { latitude_deg: 30.14817, longitude_deg: 3.48303, altitude_km: 422.3 });
  assert.deepEqual(result.observations[0].geomagnetic, { B_nT: 15220, L: 2.1 });
  assert.equal(result.observations[1].location, null);
  assert.equal(result.invalid_or_out_of_window_rows, 1);
  assert.equal(result.observations[0].quality, 'SOURCE_REPORTED_NOT_INDEPENDENTLY_VALIDATED_BY_ASTHRAL');
  assert.match(result.interpretation_limit, /not individual astronaut dosimetry/);
});

test('RadLab normalizer rejects rows outside the requested spacecraft, instrument and identifier filters', () => {
  const payload = {
    columns: ['timestamp', 'spacecraft', 'instrument', 'instrument_id', 'absorbed_dose_rate'],
    index: [0, 1, 2, 3],
    data: [
      ['2023-01-01T00:00:00', 'ISS', 'REM', 'REM-Lid', 1],
      ['2023-01-01T00:01:00', 'Mars', 'REM', 'REM-Lid', 2],
      ['2023-01-01T00:02:00', 'ISS', 'TEPC', 'REM-Lid', 3],
      ['2023-01-01T00:03:00', 'ISS', 'REM', 'rem-lid', 4],
    ],
  };
  const requested = { ...filters, instrument: 'REM', instrumentId: 'REM-Lid' };
  const result = normalizeRadLabResponse(payload, { requested, retrievedAt: '2023-01-03T00:00:00Z' });
  assert.deepEqual(result.observations.map(row => row.values.absorbed_dose_rate.value), [1]);
  assert.equal(result.invalid_or_out_of_window_rows, 3);
});

test('RadLab accepts lowercase source column names for magnetic context fields', () => {
  const payload = { columns: ['timestamp', 'spacecraft', 'b', 'l'], index: [0], data: [['2023-01-01T00:00:00', 'ISS', 15000, 2.4]] };
  const result = normalizeRadLabResponse(payload, { requested: filters, retrievedAt: '2023-01-03T00:00:00Z' });
  assert.deepEqual(result.observations[0].geomagnetic, { B_nT: 15000, L: 2.4 });
});

test('RadLab refuses an invalid retrieval timestamp and enforces cache bytes rather than characters', () => {
  assert.throws(() => normalizeRadLabResponse({ columns: [], index: [], data: [] }, { requested: filters, retrievedAt: 'unknown' }), /valid date-time/);
  const oversized = { provider: 'NASA_OSDR_RADLAB', observations: [], retrieved_at_utc: '2023-01-01T00:00:00Z', note: 'é'.repeat(1_100_000) };
  assert.equal(cacheRadLabSnapshot(oversized, { setItem() { throw Error('must not write an oversized cache'); } }), false);
});

test('RadLab local cache is size-bounded and exposes historical cache state', () => {
  const storage = { value: null, getItem(key) { assert.equal(key, RADLAB_CACHE_KEY); return this.value; }, setItem(key, value) { assert.equal(key, RADLAB_CACHE_KEY); this.value = value; } };
  const snapshot = normalizeRadLabResponse({ columns: ['timestamp', 'spacecraft', 'absorbed_dose_rate'], index: [0], data: [['2023-01-01T00:00:00', 'ISS', 1]] }, { requested: filters, retrievedAt: '2023-01-03T00:00:00Z' });
  assert.equal(cacheRadLabSnapshot(snapshot, storage), true);
  assert.equal(parseRadLabCache(storage, Date.parse('2023-01-03T00:01:00Z')).cache_state, 'CACHED_HISTORICAL');
  assert.equal(parseRadLabCache(storage, Date.parse('2023-01-05T00:00:00Z')).cache_state, 'STALE_CACHED_HISTORICAL');
});

test('Pages RadLab proxy only contacts the locked NASA endpoint and normalizes a successful response', async () => {
  const previousFetch = globalThis.fetch;
  let calledUrl = '';
  globalThis.fetch = async (url, options) => {
    calledUrl = String(url);
    assert.equal(options.redirect, 'manual');
    assert.equal(options.cf, undefined);
    return new Response(JSON.stringify({
      columns: ['timestamp', 'spacecraft', 'instrument_id', 'absorbed_dose_rate', 'latitude', 'longitude'],
      index: [0], data: [['2023-01-01T00:00:00', 'ISS', 'REM-Lid', 2.5, 30, 3]],
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
  };
  try {
    const requestUrl = 'https://demo.example/api/radlab?startDate=2023-01-01&endDate=2023-01-01&spacecraft=ISS&quantities=absorbed_dose_rate%2Cdose_equivalent_rate%2Cflux';
    const response = await onRequest({ request: new Request(requestUrl, { headers: { Origin: 'https://demo.example' } }) });
    const body = await response.json();
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('Cache-Control'), 'no-store');
    assert.match(calledUrl, /^https:\/\/visualization\.osdr\.nasa\.gov\/radlab\/api\//);
    assert.equal(body.provider, 'NASA_OSDR_RADLAB');
    assert.equal(body.observations.length, 1);
    assert.equal(body.observations[0].values.absorbed_dose_rate.value, 2.5);
    assert.equal(body.observations[0].values.dose_equivalent_rate.value, null);
  } finally { globalThis.fetch = previousFetch; }
});

test('Pages RadLab proxy refuses upstream redirects without following them', async () => {
  const previousFetch = globalThis.fetch;
  let calledUrl = '';
  globalThis.fetch = async (url, options) => {
    calledUrl = String(url);
    assert.equal(options.redirect, 'manual');
    return new Response(null, { status: 302, headers: { Location: 'https://example.invalid/collect' } });
  };
  try {
    const { onRequest } = await import('../functions/api/radlab.js');
    const response = await onRequest({ request: new Request('https://demo.example/api/radlab?startDate=2023-01-01&endDate=2023-01-01&spacecraft=ISS&quantities=flux') });
    assert.equal(response.status, 502);
    assert.match((await response.json()).error, /redirect/i);
    assert.match(calledUrl, /^https:\/\/visualization\.osdr\.nasa\.gov\//);
  } finally { globalThis.fetch = previousFetch; }
});

test('Pages RadLab proxy rejects cross-origin, non-GET and unsupported parameters before upstream access', async () => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw Error('upstream must not be called'); };
  try {
    const base = 'https://demo.example/api/radlab?startDate=2023-01-01&endDate=2023-01-01&spacecraft=ISS&quantities=flux';
    assert.equal((await onRequest({ request: new Request(base, { headers: { Origin: 'https://attacker.example' } }) })).status, 403);
    assert.equal((await onRequest({ request: new Request(base, { method: 'POST' }) })).status, 405);
    const invalid = new Request(base + '&url=https%3A%2F%2Fattacker.example');
    assert.equal((await onRequest({ request: invalid })).status, 400);
  } finally { globalThis.fetch = previousFetch; }
});
