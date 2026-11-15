import test from 'node:test';
import assert from 'node:assert/strict';
import { twoline2satrec } from '../src/vendor/orbit/satellite-js/io.js';
import { propagate as sgp4 } from '../src/vendor/orbit/satellite-js/propagation.js';
import {
  ORBIT_CACHE_KEY, buildOrbitTrack, cacheOrbitSnapshot, createOrbitModel, fetchIssOmm,
  geodeticToScene, greatCircleDistanceKm, makeSyntheticOmm, nearestListedCityApproach,
  propagateOrbit, readOrbitSnapshot, validateIssOmm,
} from '../src/orbital-engine.js';

const FIXTURE_TIME = '2026-11-15T12:00:00.000Z';
const issLike = (epoch = FIXTURE_TIME) => ({
  ...makeSyntheticOmm(new Date(epoch)),
  OBJECT_NAME: 'ISS (ZARYA)', OBJECT_ID: '1998-067A', NORAD_CAT_ID: 25544,
});

test('vendored Three.js r187 ESM renderer and core resolve as a local pair', async () => {
  const three = await import(new URL('../src/vendor/orbit/three.module.js', import.meta.url));
  assert.equal(three.REVISION, '187');
  assert.equal(typeof three.WebGLRenderer, 'function');
});

test('Vallado verification TLE propagates near the published SGP4 reference vector at its UTC epoch', () => {
  // Vallado et al., AIAA 2006-6753 verification case 00005; metre-scale tolerance.
  const satrec = twoline2satrec(
    '1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753',
    '2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667',
  );
  const result = sgp4(satrec, new Date('2000-06-27T18:50:19.733568Z'));
  assert.equal(satrec.error, 0);
  assert.ok(Math.abs(result.position.x - 7022.465) < 0.02);
  assert.ok(Math.abs(result.position.y + 1400.083) < 0.02);
  assert.ok(Math.abs(result.position.z - 0.03995) < 0.02);
  assert.ok(Math.abs(result.velocity.x - 1.89384) < 0.00002);
  assert.ok(Math.abs(result.velocity.y - 6.40589) < 0.00002);
  assert.ok(Math.abs(result.velocity.z - 4.53481) < 0.00002);
});

test('ISS OMM validator binds object 25544, validates the epoch and blocks elements older than seven days', () => {
  const row = issLike();
  const checked = validateIssOmm([row], { fetchedAt: Date.parse(FIXTURE_TIME) });
  assert.equal(checked.omm.NORAD_CAT_ID, 25544);
  assert.equal(checked.freshness, 'AVAILABLE');
  assert.throws(() => validateIssOmm([{ ...row, NORAD_CAT_ID: 25543 }], { fetchedAt: Date.parse(FIXTURE_TIME) }), /catalog object 25544/);
  assert.throws(() => validateIssOmm([{ ...row, EPOCH: 'invalid' }], { fetchedAt: Date.parse(FIXTURE_TIME) }), /valid UTC timestamp/);
  assert.equal(validateIssOmm([row], { fetchedAt: Date.parse(FIXTURE_TIME) + 8 * 86400_000 }).freshness, 'UNAVAILABLE_STALE');
});

test('synthetic orbit is separately identified and produces a plausible low-Earth estimate at the shown UTC time', () => {
  const model = createOrbitModel(makeSyntheticOmm(new Date(FIXTURE_TIME)), { mode: 'SIMULATED', fetchedAt: Date.parse(FIXTURE_TIME) });
  const state = propagateOrbit(model, FIXTURE_TIME);
  assert.equal(model.mode, 'SIMULATED');
  assert.equal(model.source, 'ASTHRAL_SYNTHETIC_ELEMENTS');
  assert.equal(model.omm.NORAD_CAT_ID, 990001);
  assert.equal(state.timestampUtc, FIXTURE_TIME);
  assert.ok(state.latitudeDeg >= -90 && state.latitudeDeg <= 90);
  assert.ok(state.longitudeDeg >= -180 && state.longitudeDeg <= 180);
  assert.ok(state.altitudeKm >= 350 && state.altitudeKm <= 500);
  assert.ok(state.velocityKms >= 7 && state.velocityKms <= 8.5);
  assert.ok(['SUNLIT', 'ECLIPSED', 'PENUMBRA'].includes(state.sunlight));
  assert.ok(state.shadowFraction >= 0 && state.shadowFraction <= 1);
});

test('ground track is split into past and future at the displayed time and every point is UTC ordered', () => {
  const model = createOrbitModel(makeSyntheticOmm(new Date(FIXTURE_TIME)), { mode: 'SIMULATED', fetchedAt: Date.parse(FIXTURE_TIME) });
  const track = buildOrbitTrack(model, FIXTURE_TIME, { beforeSeconds: 120, afterSeconds: 180, stepSeconds: 30 });
  assert.equal(track.past.length, 4);
  assert.equal(track.future.length, 7);
  assert.ok(Date.parse(track.past.at(-1).timestampUtc) < Date.parse(FIXTURE_TIME));
  assert.equal(track.future[0].timestampUtc, FIXTURE_TIME);
  assert.ok(Date.parse(track.future.at(-1).timestampUtc) > Date.parse(FIXTURE_TIME));
});

test('Earth coordinate utilities handle poles and antimeridian distance', () => {
  const north = geodeticToScene(90, 0);
  assert.ok(Math.abs(north.y - 1) < 1e-12);
  assert.ok(Math.abs(north.x) < 1e-12);
  assert.ok(greatCircleDistanceKm({ latitudeDeg: 0, longitudeDeg: 179 }, { latitudeDeg: 0, longitudeDeg: -179 }) < 230);
  assert.ok(greatCircleDistanceKm({ latitudeDeg: 10, longitudeDeg: 20 }, { latitudeDeg: 10, longitudeDeg: 20 }) < 1e-9);
});

test('nearest listed city output is computed from propagated positions and reports sampling resolution', () => {
  const model = createOrbitModel(makeSyntheticOmm(new Date(FIXTURE_TIME)), { mode: 'SIMULATED', fetchedAt: Date.parse(FIXTURE_TIME) });
  const result = nearestListedCityApproach(model, FIXTURE_TIME, { horizonSeconds: 180, stepSeconds: 30 });
  assert.ok(result.city);
  assert.ok(result.distanceKm >= 0);
  assert.equal(result.sampleStepSeconds, 30);
  assert.equal(result.offsetSeconds % 30, 0);
});

test('ISS cache is bounded, source-bound and rejects arbitrary storage content', () => {
  const saved = new Map();
  const storage = { setItem: (key, value) => saved.set(key, value), getItem: key => saved.get(key) ?? null };
  const snapshot = { source: 'CELESTRAK_GP_JSON', fetched_at: FIXTURE_TIME, data: [issLike()] };
  assert.equal(cacheOrbitSnapshot(snapshot, storage), true);
  assert.deepEqual(readOrbitSnapshot(storage), snapshot);
  saved.set(ORBIT_CACHE_KEY, JSON.stringify({ ...snapshot, source: 'UNKNOWN' }));
  assert.equal(readOrbitSnapshot(storage), null);
  saved.set(ORBIT_CACHE_KEY, 'x'.repeat(20001));
  assert.equal(cacheOrbitSnapshot(snapshot, { setItem: () => { throw Error('quota'); } }), false);
  assert.equal(readOrbitSnapshot(storage), null);
});

test('fetch rejects redirects and malformed responses instead of accepting another object', async () => {
  await assert.rejects(fetchIssOmm({ fetcher: async (_url, init) => {
    assert.equal(init.method, 'GET');
    assert.equal(init.credentials, 'omit');
    assert.equal(init.redirect, 'error');
    return { ok: true, text: async () => JSON.stringify([{ ...issLike(), NORAD_CAT_ID: 42 }]) };
  }, now: () => Date.parse(FIXTURE_TIME) }), /catalog object 25544/);
});
