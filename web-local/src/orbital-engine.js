/* Deterministic browser orbit pipeline. All propagated positions are estimates from GP mean elements. */
import { json2satrec } from './vendor/orbit/satellite-js/io.js';
import { jday } from './vendor/orbit/satellite-js/ext.js';
import { propagate, gstime } from './vendor/orbit/satellite-js/propagation.js';
import { degreesLat, degreesLong, eciToEcf, eciToGeodetic } from './vendor/orbit/satellite-js/transforms.js';
import { sunPos } from './vendor/orbit/satellite-js/sun.js';
import { shadowFraction } from './vendor/orbit/satellite-js/shadow.js';

export const CELESTRAK_ISS_URL = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON';
export const ORBIT_CACHE_KEY = 'asthral.public.iss.omm.v1';
export const ORBIT_CACHE_REFRESH_MS = 6 * 60 * 60 * 1000;
export const ORBIT_STALE_NOTICE_MS = 24 * 60 * 60 * 1000;
export const ORBIT_MAX_ELEMENT_AGE_MS = 7 * 24 * 60 * 60 * 1000;
export const EARTH_RADIUS_KM = 6378.137;

const REQUIRED = Object.freeze([
  'OBJECT_NAME', 'OBJECT_ID', 'EPOCH', 'MEAN_MOTION', 'ECCENTRICITY', 'INCLINATION',
  'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY', 'NORAD_CAT_ID',
]);

function finite(value, name, min = -Infinity, max = Infinity) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < min || number > max) throw new Error(`ISS orbital field ${name} is invalid.`);
  return number;
}

export function validateIssOmm(raw, { fetchedAt = Date.now(), source = 'CELESTRAK_GP_JSON' } = {}) {
  const rows = Array.isArray(raw) ? raw : [raw];
  if (rows.length !== 1 || !rows[0] || typeof rows[0] !== 'object' || Array.isArray(rows[0])) throw new Error('Expected one ISS OMM object.');
  const omm = rows[0];
  for (const key of REQUIRED) if (!(key in omm) || omm[key] === null || omm[key] === '') throw new Error(`ISS OMM is missing ${key}.`);
  if (Number(omm.NORAD_CAT_ID) !== 25544) throw new Error('The orbital source did not return catalog object 25544.');
  if (String(omm.OBJECT_NAME).toUpperCase().includes('ISS') !== true) throw new Error('The orbital source object name is not identified as ISS.');
  const epochMs = Date.parse(String(omm.EPOCH).endsWith('Z') ? omm.EPOCH : `${omm.EPOCH}Z`);
  if (!Number.isFinite(epochMs)) throw new Error('ISS OMM epoch is not a valid UTC timestamp.');
  const meanMotion = finite(omm.MEAN_MOTION, 'MEAN_MOTION', 10, 20);
  const eccentricity = finite(omm.ECCENTRICITY, 'ECCENTRICITY', 0, 0.2);
  finite(omm.INCLINATION, 'INCLINATION', 0, 180);
  finite(omm.RA_OF_ASC_NODE, 'RA_OF_ASC_NODE', 0, 360);
  finite(omm.ARG_OF_PERICENTER, 'ARG_OF_PERICENTER', 0, 360);
  finite(omm.MEAN_ANOMALY, 'MEAN_ANOMALY', 0, 360);
  if (meanMotion < 14 || meanMotion > 17 || eccentricity > 0.02) throw new Error('ISS OMM is outside the supported low-Earth-orbit envelope.');
  const normalized = { ...omm, NORAD_CAT_ID: 25544, EPOCH: new Date(epochMs).toISOString() };
  const satrec = json2satrec(normalized);
  if (!satrec || satrec.error) throw new Error('SGP4 could not initialize the ISS OMM.');
  const ageMs = Number(fetchedAt) - epochMs;
  if (!Number.isFinite(ageMs) || ageMs < -24 * 60 * 60 * 1000) throw new Error('ISS orbital element epoch is implausibly in the future.');
  return Object.freeze({
    omm: Object.freeze(normalized), satrec, epochMs, fetchedAtMs: Number(fetchedAt), source,
    ageMs: Math.max(0, ageMs),
    freshness: ageMs > ORBIT_MAX_ELEMENT_AGE_MS ? 'UNAVAILABLE_STALE' : ageMs > ORBIT_STALE_NOTICE_MS ? 'STALE' : 'AVAILABLE',
    periodSeconds: 86400 / meanMotion,
  });
}

export function makeSyntheticOmm(epoch = new Date()) {
  return {
    OBJECT_NAME: 'ASTHRAL SYNTHETIC CREW DEMO', OBJECT_ID: 'ASTHRAL-DEMO-LEO',
    EPOCH: epoch.toISOString(), MEAN_MOTION: 15.5, ECCENTRICITY: 0.0005,
    INCLINATION: 51.6, RA_OF_ASC_NODE: 35.0, ARG_OF_PERICENTER: 0.0,
    MEAN_ANOMALY: 145.0, EPHEMERIS_TYPE: 0, CLASSIFICATION_TYPE: 'S',
    NORAD_CAT_ID: 990001, ELEMENT_SET_NO: 1, REV_AT_EPOCH: 1,
    BSTAR: 0, MEAN_MOTION_DOT: 0, MEAN_MOTION_DDOT: 0,
  };
}

export function createOrbitModel(omm, { mode = 'ISS_TRACKED', fetchedAt = Date.now(), source = 'CELESTRAK_GP_JSON' } = {}) {
  if (mode === 'SIMULATED') {
    const synthetic = { ...omm, NORAD_CAT_ID: 25544, OBJECT_NAME: 'ISS SIMULATION PLACEHOLDER' };
    const result = validateIssOmm(synthetic, { fetchedAt, source: 'ASTHRAL_SYNTHETIC_ELEMENTS' });
    return Object.freeze({ ...result, omm: Object.freeze({ ...result.omm, NORAD_CAT_ID: 990001, OBJECT_NAME: 'ASTHRAL SYNTHETIC CREW DEMO' }), source: 'ASTHRAL_SYNTHETIC_ELEMENTS', mode });
  }
  return Object.freeze({ ...validateIssOmm(omm, { fetchedAt, source }), mode });
}

function julianDate(date) { return jday(date); }

export function propagateOrbit(orbit, timestamp) {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  if (!Number.isFinite(date.getTime())) throw new Error('Orbit calculation time must be a valid timestamp.');
  if (orbit.freshness === 'UNAVAILABLE_STALE') throw new Error('ISS orbital elements are more than seven days past epoch; tracked position disabled.');
  const state = propagate(orbit.satrec, date);
  if (!state?.position || !state?.velocity) throw new Error(`SGP4 propagation failed (error ${orbit.satrec.error ?? 'unknown'}).`);
  const gmst = gstime(date);
  const geographic = eciToGeodetic(state.position, gmst);
  const sun = sunPos(julianDate(date));
  const obscuredFraction = shadowFraction(sun.rsun, state.position);
  const sunEcf = eciToEcf(sun.rsun, gmst);
  const altitudeKm = geographic.height;
  if (![altitudeKm, geographic.latitude, geographic.longitude, state.velocity.x, state.velocity.y, state.velocity.z].every(Number.isFinite)) throw new Error('SGP4 returned non-finite position data.');
  return Object.freeze({
    timestampUtc: date.toISOString(),
    latitudeDeg: degreesLat(geographic.latitude), longitudeDeg: degreesLong(geographic.longitude),
    altitudeKm, velocityKms: Math.hypot(state.velocity.x, state.velocity.y, state.velocity.z),
    eciKm: state.position, ecefKm: eciToEcf(state.position, gmst),
    sunEcfUnit: normalize(sunEcf), shadowFraction: obscuredFraction,
    sunlight: obscuredFraction < 0.01 ? 'SUNLIT' : obscuredFraction > 0.99 ? 'ECLIPSED' : 'PENUMBRA',
  });
}

export function normalize(vector) {
  const length = Math.hypot(vector.x, vector.y, vector.z);
  if (!Number.isFinite(length) || length === 0) return { x: 1, y: 0, z: 0 };
  return { x: vector.x / length, y: vector.y / length, z: vector.z / length };
}

export function earthFixedToScene({ x, y, z }, earthRadius = 1) {
  const scale = earthRadius / EARTH_RADIUS_KM;
  return { x: x * scale, y: z * scale, z: -y * scale };
}

export function geodeticToScene(latitudeDeg, longitudeDeg, radius = 1) {
  const lat = latitudeDeg * Math.PI / 180, lon = longitudeDeg * Math.PI / 180;
  return { x: radius * Math.cos(lat) * Math.cos(lon), y: radius * Math.sin(lat), z: -radius * Math.cos(lat) * Math.sin(lon) };
}

export function greatCircleDistanceKm(a, b) {
  const rad = Math.PI / 180;
  const lat1 = a.latitudeDeg * rad, lat2 = b.latitudeDeg * rad;
  const dLat = (b.latitudeDeg - a.latitudeDeg) * rad, dLon = wrapRadians((b.longitudeDeg - a.longitudeDeg) * rad);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

function wrapRadians(value) { return ((value + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI; }

export const REFERENCE_CITIES = Object.freeze([
  { name: 'Lima', latitudeDeg: -12.0464, longitudeDeg: -77.0428 },
  { name: 'New York', latitudeDeg: 40.7128, longitudeDeg: -74.0060 },
  { name: 'London', latitudeDeg: 51.5072, longitudeDeg: -0.1276 },
  { name: 'Nairobi', latitudeDeg: -1.2921, longitudeDeg: 36.8219 },
  { name: 'Tokyo', latitudeDeg: 35.6762, longitudeDeg: 139.6503 },
  { name: 'Sydney', latitudeDeg: -33.8688, longitudeDeg: 151.2093 },
  { name: 'Los Angeles', latitudeDeg: 34.0522, longitudeDeg: -118.2437 },
]);

export function nearestListedCityApproach(orbit, startTime, { stepSeconds = 30, horizonSeconds = orbit.periodSeconds * 2 } = {}) {
  if (!Number.isFinite(stepSeconds) || stepSeconds < 1 || stepSeconds > 600) throw new Error('City-approach sampling step is outside the supported range.');
  let best = null;
  const start = new Date(startTime).getTime();
  for (let offset = 0; offset <= horizonSeconds; offset += stepSeconds) {
    const position = propagateOrbit(orbit, start + offset * 1000);
    for (const city of REFERENCE_CITIES) {
      const distanceKm = greatCircleDistanceKm(position, city);
      if (!best || distanceKm < best.distanceKm) best = { city: city.name, distanceKm, timeUtc: position.timestampUtc, offsetSeconds: offset, sampleStepSeconds: stepSeconds };
    }
  }
  return best;
}

export function buildOrbitTrack(orbit, centerTime, { beforeSeconds = 45 * 60, afterSeconds = 45 * 60, stepSeconds = 30 } = {}) {
  const center = new Date(centerTime).getTime();
  const past = [], future = [];
  for (let offset = -beforeSeconds; offset <= afterSeconds; offset += stepSeconds) {
    const state = propagateOrbit(orbit, center + offset * 1000);
    (offset < 0 ? past : future).push(state);
  }
  return { past, future };
}

export function cacheOrbitSnapshot(snapshot, storage = globalThis.localStorage) {
  try {
    const value = JSON.stringify(snapshot);
    if (value.length > 20000) return false;
    storage?.setItem(ORBIT_CACHE_KEY, value);
    return true;
  } catch { return false; }
}

export function readOrbitSnapshot(storage = globalThis.localStorage) {
  try {
    const raw = storage?.getItem(ORBIT_CACHE_KEY);
    if (!raw || raw.length > 20000) return null;
    const snapshot = JSON.parse(raw);
    if (snapshot?.source !== 'CELESTRAK_GP_JSON' || !Number.isFinite(Date.parse(snapshot.fetched_at)) || !Array.isArray(snapshot.data)) return null;
    return snapshot;
  } catch { return null; }
}

export async function fetchIssOmm({ fetcher = globalThis.fetch, now = () => Date.now(), signal } = {}) {
  const request = new AbortController();
  const forwardAbort = () => request.abort(signal?.reason);
  if (signal?.aborted) forwardAbort();
  else signal?.addEventListener('abort', forwardAbort, { once: true });
  const timeout = setTimeout(() => request.abort(new Error('CelesTrak request timed out after 12 seconds.')), 12000);
  try {
    const response = await fetcher(CELESTRAK_ISS_URL, {
      method: 'GET', credentials: 'omit', referrerPolicy: 'no-referrer', redirect: 'error', signal: request.signal,
      headers: { Accept: 'application/json' }, cache: 'no-store',
    });
    if (!response.ok) throw new Error(`CelesTrak GP data request failed (HTTP ${response.status}).`);
    const contentLength = Number(response.headers?.get?.('content-length'));
    if (Number.isFinite(contentLength) && contentLength > 20000) throw new Error('CelesTrak ISS response exceeded the 20 kB limit.');
    const text = await response.text();
    if (text.length > 20000) throw new Error('CelesTrak ISS response exceeded the 20 kB limit.');
    const data = JSON.parse(text);
    const checked = validateIssOmm(data, { fetchedAt: now() });
    if (checked.freshness === 'UNAVAILABLE_STALE') throw new Error('CelesTrak returned orbital elements older than seven days.');
    return { source: 'CELESTRAK_GP_JSON', fetched_at: new Date(now()).toISOString(), data: [checked.omm] };
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener('abort', forwardAbort);
  }
}
