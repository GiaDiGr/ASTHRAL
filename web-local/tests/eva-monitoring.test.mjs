import test from 'node:test';
import assert from 'node:assert/strict';
import { EvaController, EVA_SCENARIOS, EVA_RULES, classifyCoreTemperature, classifyHeartRate, evaluateSpaceWeather, simulatedDose, buildHandoverReport, reportToText } from '../src/eva-monitoring.js';
import { DONKI_HISTORICAL_FIXTURE } from '../src/space-weather.js';

// Deterministic clock: each step advances one simulated minute.
function clock(start = Date.parse('2026-11-15T18:00:00Z')) { let t = start; return { now: () => t, tick: (s = 60) => { t += s * 1000; } }; }
function run(ctl, c, n) { for (let i = 0; i < n; i++) { c.tick(); if (!ctl.step()) break; } }
const noCache = () => ({ state: 'NO_CACHE', events: [], fetched_at: null });
const withFlare = () => ({ state: 'CACHED', events: [DONKI_HISTORICAL_FIXTURE], fetched_at: '2026-11-15T17:00:00.000Z' });

test('1. Start EVA creates a single session and starts the timer', () => {
  const c = clock(), ctl = new EvaController({ now: c.now, spaceWeather: noCache });
  const s1 = ctl.start(); const id = s1.eva_id; const s2 = ctl.start();
  assert.equal(s2.eva_id, id); assert.equal(ctl.session.state, 'active');
  assert.equal(ctl.log.filter(e => e.kind === 'EVA_STARTED').length, 1);
  c.tick(120); assert.equal(ctl.elapsedSeconds(), 120);
});

test('2. End EVA stops the timer and closes the session', () => {
  const c = clock(), ctl = new EvaController({ now: c.now, spaceWeather: noCache });
  ctl.start(); run(ctl, c, 3); assert.equal(ctl.end(), true);
  assert.equal(ctl.session.state, 'completed'); const e = ctl.elapsedSeconds(); c.tick(600);
  assert.equal(ctl.elapsedSeconds(), e); assert.equal(ctl.step(), false); assert.equal(ctl.end(), false);
});

test('3. Nominal scenario shows four indicators with labelled synthetic data and no alerts', () => {
  const c = clock(), ctl = new EvaController({ scenarioId: 'nominal', now: c.now, spaceWeather: noCache });
  ctl.start(); run(ctl, c, 29);
  const L = ctl.session.latest;
  assert.equal(L.core_temperature.source, 'synthetic'); assert.equal(L.heart_rate.source, 'synthetic');
  assert.equal(L.dose.status, 'SIMULATED_DOSE'); assert.ok(L.space_weather);
  assert.equal(L.core_temperature.level, 'NORMAL'); assert.equal(L.heart_rate.level, 'NORMAL');
  assert.equal(ctl.session.alerts.length, 0); assert.equal(ctl.session.state, 'active');
});

test('4. Thermal warning fires from the configured sustained rule and is logged', () => {
  const c = clock(), ctl = new EvaController({ scenarioId: 'thermal_warning', now: c.now, spaceWeather: noCache });
  ctl.start(); run(ctl, c, 29);
  assert.equal(ctl.session.state, 'warning');
  const a = ctl.session.alerts.find(x => x.indicator === 'core_temperature' && x.level === 'WARNING');
  assert.ok(a); assert.match(a.rule, new RegExp(String(EVA_RULES.core_temperature_c.warning_high)));
  assert.ok(ctl.log.some(e => e.kind === 'ALERT_WARNING'));
  assert.equal(ctl.advisory(), null);
});

test('5. Critical state shows "Return to airlock — simulated" and records its cause', () => {
  const c = clock(), ctl = new EvaController({ scenarioId: 'critical_training', now: c.now, spaceWeather: noCache });
  ctl.start(); run(ctl, c, 20);
  assert.equal(ctl.session.state, 'critical');
  const adv = ctl.advisory();
  assert.equal(adv.text, 'Return to airlock — simulated EVA safety advisory');
  assert.ok(adv.rule && adv.at_utc);
  assert.equal(ctl.acknowledge(), true); assert.ok(ctl.session.acknowledgement); assert.equal(ctl.acknowledge(), false);
});

test('6. An ordinary DONKI flare does NOT trigger return by itself', () => {
  const c = clock(), ctl = new EvaController({ scenarioId: 'nominal', now: c.now, spaceWeather: withFlare });
  ctl.start(); run(ctl, c, 29);
  assert.equal(ctl.session.latest.space_weather.status, 'EVENTS_NOT_EVALUATED_FOR_MISSION');
  assert.notEqual(ctl.session.state, 'critical'); assert.equal(ctl.advisory(), null);
});

test('7. An explicitly marked synthetic training event does trigger the configured alert', () => {
  const sw = evaluateSpaceWeather(withFlare(), true);
  assert.equal(sw.status, 'DEMO_TRAINING_ALERT'); assert.equal(sw.level, 'CRITICAL');
  const c = clock(), ctl = new EvaController({ scenarioId: 'nominal', now: c.now, spaceWeather: noCache });
  ctl.start(); run(ctl, c, 2); assert.equal(ctl.triggerTrainingCritical(), true);
  assert.equal(ctl.session.state, 'critical'); assert.ok(ctl.log.some(e => e.kind === 'TRAINING_CRITICAL_TRIGGERED'));
  assert.equal(EVA_SCENARIOS.critical_training.training_condition, true);
});

test('8. Without DONKI data the panel distinguishes "unavailable" from "no events"', () => {
  assert.equal(evaluateSpaceWeather({ state: 'NO_CACHE', events: [], fetched_at: null }, false).status, 'DATA_UNAVAILABLE');
  assert.equal(evaluateSpaceWeather(null, false).level, 'NO_DATA');
  const noEvents = evaluateSpaceWeather({ state: 'CACHED', events: [], fetched_at: '2026-11-15T17:00:00Z' }, false);
  assert.equal(noEvents.status, 'NO_EVENTS_RECORDED');
  assert.equal(noEvents.level, 'CONTEXT', 'an empty query does not imply normal conditions');
  assert.equal(evaluateSpaceWeather({ state: 'STALE', events: [], fetched_at: '2026-11-10T17:00:00Z' }, false).stale, true);
});

test('9. Without a dosimeter no real dose is presented', () => {
  const d = simulatedDose(1, 0, null);
  assert.equal(d.status, 'DOSIMETER_NOT_CONNECTED'); assert.equal(d.value_msv, null);
  const s = simulatedDose(0.5, 0, EVA_SCENARIOS.nominal);
  assert.equal(s.status, 'SIMULATED_DOSE'); assert.equal(s.value_msv, 0.01);
});

test('10. Invalid, missing or stale values are never green', () => {
  const now = Date.parse('2026-11-15T18:10:00Z');
  assert.equal(classifyCoreTemperature([], now).level, 'NO_DATA');
  assert.equal(classifyCoreTemperature([{ value: 'x', timestamp_utc: '2026-11-15T18:10:00Z' }], now).level, 'INVALID');
  assert.equal(classifyCoreTemperature([{ value: 37, timestamp_utc: '2026-11-15T17:00:00Z' }], now).level, 'STALE');
  assert.equal(classifyCoreTemperature([{ value: 55, timestamp_utc: '2026-11-15T18:10:00Z' }], now).level, 'INVALID');
  assert.equal(classifyHeartRate([{ value: 100, timestamp_utc: '2026-11-15T18:10:00Z' }], undefined, now).level, 'NO_BASELINE');
  for (const lvl of ['NO_DATA', 'INVALID', 'STALE', 'NO_BASELINE']) assert.notEqual(lvl, 'NORMAL');
});

test('11. Handover report is traceable and separates real and synthetic sources', () => {
  const c = clock(), ctl = new EvaController({ scenarioId: 'critical_training', now: c.now, spaceWeather: withFlare });
  ctl.start(); run(ctl, c, 20); ctl.acknowledge(); c.tick(); ctl.end('returned to airlock');
  const r = buildHandoverReport(ctl);
  assert.equal(r.mode, 'SIMULATION'); assert.equal(r.delivery_status, 'PREPARED_LOCALLY_NOT_SENT');
  assert.equal(r.core_temperature_c.source, 'synthetic');
  assert.equal(r.space_weather.real_events_consulted[0].id, DONKI_HISTORICAL_FIXTURE.id);
  assert.ok(r.space_weather.real_events_consulted[0].url.startsWith('https://ccmc.gsfc.nasa.gov/'));
  assert.ok(r.alerts.length > 0 && r.alerts.every(a => a.simulated === true));
  assert.ok(r.acknowledgement); assert.ok(r.ended_at_utc); assert.ok(r.limitations.length >= 4);
  const txt = reportToText(r); assert.match(txt, /MODE: SIMULATION/); assert.match(txt, /TRAINING EXERCISE/);
});

test('State machine: scenario cannot change mid-EVA and errors move to "error" state', () => {
  const c = clock(), ctl = new EvaController({ now: c.now, spaceWeather: () => { throw Error('boom'); } });
  ctl.start(); assert.throws(() => ctl.setScenario('thermal_warning'));
  c.tick(); assert.equal(ctl.step(), false); assert.equal(ctl.session.state, 'error');
});

test('14. Offline demo is reproducible with no network access', () => {
  const saved = globalThis.fetch; globalThis.fetch = () => { throw Error('network must not be used'); };
  try {
    const out = [];
    for (let k = 0; k < 2; k++) { const c = clock(), ctl = new EvaController({ scenarioId: 'critical_training', now: c.now, spaceWeather: noCache }); ctl.start(); run(ctl, c, 30); out.push(JSON.stringify(ctl.session.alerts)); }
    assert.equal(out[0], out[1]);
  } finally { globalThis.fetch = saved; }
});

test('Pause and resume preserve the simulated scenario clock and exclude paused wall time', () => {
  const c = clock(), ctl = new EvaController({ now: c.now, spaceWeather: noCache });
  ctl.start({ simulationStartUtc: '2026-11-15T17:30:00.000Z' });
  assert.equal(ctl.step(), true);
  assert.equal(ctl.session.temp_history[0].timestamp_utc, '2026-11-15T17:30:00.000Z');
  c.tick(100); const elapsedBeforePause = ctl.elapsedSeconds();
  assert.equal(ctl.pause(), true);
  c.tick(900); assert.equal(ctl.step(), false); assert.equal(ctl.elapsedSeconds(), elapsedBeforePause);
  assert.throws(() => ctl.setScenario('thermal_warning'), /active EVA/);
  assert.equal(ctl.resume(), true);
  c.tick(5); assert.equal(ctl.step(), true);
  assert.equal(ctl.session.temp_history[1].timestamp_utc, '2026-11-15T17:31:00.000Z');
  assert.ok(ctl.log.every(row => row.at_utc && row.time_basis));
});

test('handover report distinguishes wall clock duration from accelerated scenario time', () => {
  const c = clock(), ctl = new EvaController({ now: c.now, spaceWeather: noCache });
  ctl.start({ simulationStartUtc: '2026-11-15T17:45:00.000Z' });
  ctl.step(); c.tick(4); ctl.step(); ctl.end();
  const report = buildHandoverReport(ctl);
  assert.equal(report.started_at_utc, '2026-11-15T18:00:00.000Z');
  assert.equal(report.scenario_time_utc, '2026-11-15T17:46:00.000Z');
  assert.equal(report.timing.event_time_basis, 'SCENARIO_UTC');
  assert.equal(report.scenario_elapsed_s, 120);
  assert.equal(report.duration_s, 4);
});
