// ASTHRAL · EVA Monitoring — core logic (no DOM).
// Simulation-only prototype. Not clinically, operationally or flight validated.
// Rules below are PROTOTYPE rules for a hackathon demo, not NASA-certified medical limits.

export const EVA_MODULE_VERSION = 'eva-monitoring 0.1.0';

/* ---------------------------------------------------------------------------
 * Central prototype rule configuration (units, source and justification).
 * ------------------------------------------------------------------------- */
export const EVA_RULES = Object.freeze({
  sample_interval_s: 60,          // one synthetic sample = one simulated minute
  stale_after_s: 180,             // an observation older than this is shown as STALE, never green
  core_temperature_c: Object.freeze({
    unit: '°C', measurement: 'core body temperature (not skin temperature)',
    valid_range: [30, 43],
    warning_high: 38.0, critical_high: 39.0,
    warning_low: 36.0, critical_low: 35.0,
    sustained_samples: 3,
    source: 'Prototype rule for demonstration',
    justification: 'Illustrative software thresholds for a synthetic demonstration only. They are not derived or endorsed as NASA, clinical, spacesuit, or flight cutoffs.',
  }),
  heart_rate_bpm: Object.freeze({
    unit: 'bpm', valid_range: [25, 230],
    warning_over_exertion_baseline: 30, critical_over_exertion_baseline: 50,
    sustained_samples: 3,
    source: 'Prototype rule for demonstration',
    justification: 'Compared only with the scenario\'s explicitly synthetic EVA-exertion reference (not a personal measurement or resting rate). Offsets are illustrative and configurable.',
  }),
  dose: Object.freeze({
    unit: 'mSv', model: 'constant simulated dose rate x elapsed hours',
    eva_budget_msv: 0.5,
    source: 'Synthetic dose model for demonstration',
    justification: 'No dosimeter is connected. Values and the demonstration comparison value are SIMULATED and are never derived from DONKI; 0.5 mSv is not an EVA exposure limit.',
  }),
});

/* ---------------------------------------------------------------------------
 * Deterministic synthetic scenarios.
 * ------------------------------------------------------------------------- */
function series(n, f) { return Array.from({ length: n }, (_, m) => f(m)); }
const round1 = x => Math.round(x * 10) / 10;

export const EVA_SCENARIOS = Object.freeze({
  nominal: Object.freeze({
    id: 'nominal', label: 'Nominal EVA', training_condition: false,
    exertion_baseline_bpm: 105, dose_rate_msv_h: 0.02, synthetic_solar_event_at_min: null,
    samples: series(30, m => ({ minute: m, core_temperature_c: round1(37.0 + 0.01 * m), heart_rate_bpm: 100 + (m % 5) })),
  }),
  thermal_warning: Object.freeze({
    id: 'thermal_warning', label: 'Thermal warning (cooling degradation)', training_condition: false,
    exertion_baseline_bpm: 105, dose_rate_msv_h: 0.02, synthetic_solar_event_at_min: null,
    samples: series(30, m => ({ minute: m, core_temperature_c: round1(m < 10 ? 37.1 : 37.1 + (m - 10) * 0.08), heart_rate_bpm: 104 + Math.floor(m / 3) })),
  }),
  critical_training: Object.freeze({
    id: 'critical_training', label: 'Critical EVA — TRAINING EXERCISE (not a real flight assessment)', training_condition: true,
    exertion_baseline_bpm: 105, dose_rate_msv_h: 0.02, event_dose_rate_msv_h: 1.2,
    synthetic_solar_event_at_min: 15,
    samples: series(30, m => ({ minute: m, core_temperature_c: round1(m < 12 ? 37.2 + m * 0.03 : 37.56 + (m - 12) * 0.11), heart_rate_bpm: 106 + (m > 15 ? (m - 15) * 4 : 0) })),
  }),
});

/* ---------------------------------------------------------------------------
 * Classification helpers. Missing / invalid / stale data are NEVER green.
 * Levels: NO_DATA | STALE | INVALID | NORMAL | WARNING | CRITICAL
 * ------------------------------------------------------------------------- */
const isNum = v => typeof v === 'number' && Number.isFinite(v);

export function observationQuality(obs, nowMs, rules = EVA_RULES) {
  if (!obs || obs.value === null || obs.value === undefined) return 'NO_DATA';
  if (!isNum(obs.value)) return 'INVALID';
  const t = Date.parse(obs.timestamp_utc);
  if (!Number.isFinite(t)) return 'INVALID';
  if (nowMs - t > rules.stale_after_s * 1000) return 'STALE';
  return 'OK';
}

function sustained(values, predicate, n) {
  if (values.length < n) return false;
  return values.slice(-n).every(predicate);
}

export function classifyCoreTemperature(history, nowMs, rules = EVA_RULES) {
  const r = rules.core_temperature_c;
  const last = history[history.length - 1];
  const q = observationQuality(last, nowMs, rules);
  if (q !== 'OK') return { level: q, rule: null };
  if (last.value < r.valid_range[0] || last.value > r.valid_range[1]) return { level: 'INVALID', rule: 'core_temperature_out_of_valid_range' };
  const vals = history.map(h => h.value);
  if (sustained(vals, v => v >= r.critical_high, r.sustained_samples)) return { level: 'CRITICAL', rule: `core_temperature >= ${r.critical_high} °C for ${r.sustained_samples} samples` };
  if (sustained(vals, v => v <= r.critical_low, r.sustained_samples)) return { level: 'CRITICAL', rule: `core_temperature <= ${r.critical_low} °C for ${r.sustained_samples} samples` };
  if (sustained(vals, v => v >= r.warning_high, r.sustained_samples)) return { level: 'WARNING', rule: `core_temperature >= ${r.warning_high} °C for ${r.sustained_samples} samples` };
  if (sustained(vals, v => v <= r.warning_low, r.sustained_samples)) return { level: 'WARNING', rule: `core_temperature <= ${r.warning_low} °C for ${r.sustained_samples} samples` };
  return { level: 'NORMAL', rule: null };
}

export function classifyHeartRate(history, exertionBaseline, nowMs, rules = EVA_RULES) {
  const r = rules.heart_rate_bpm;
  const last = history[history.length - 1];
  const q = observationQuality(last, nowMs, rules);
  if (q !== 'OK') return { level: q, rule: null, baseline: exertionBaseline ?? null };
  if (!isNum(exertionBaseline)) return { level: 'NO_BASELINE', rule: null, baseline: null };
  if (last.value < r.valid_range[0] || last.value > r.valid_range[1]) return { level: 'INVALID', rule: 'heart_rate_out_of_valid_range', baseline: exertionBaseline };
  const over = history.map(h => h.value - exertionBaseline);
  if (sustained(over, d => d >= r.critical_over_exertion_baseline, r.sustained_samples)) return { level: 'CRITICAL', rule: `heart_rate >= exertion baseline + ${r.critical_over_exertion_baseline} bpm for ${r.sustained_samples} samples`, baseline: exertionBaseline };
  if (sustained(over, d => d >= r.warning_over_exertion_baseline, r.sustained_samples)) return { level: 'WARNING', rule: `heart_rate >= exertion baseline + ${r.warning_over_exertion_baseline} bpm for ${r.sustained_samples} samples`, baseline: exertionBaseline };
  return { level: 'NORMAL', rule: null, baseline: exertionBaseline };
}

/**
 * Space weather context. Real DONKI events are CONTEXT ONLY: they never produce CRITICAL by themselves.
 * Only an explicitly marked synthetic training event can produce CRITICAL.
 * States: DATA_UNAVAILABLE | NO_EVENTS_RECORDED | EVENTS_NOT_EVALUATED_FOR_MISSION | DEMO_TRAINING_ALERT
 */
export function evaluateSpaceWeather(snapshot, syntheticEventActive) {
  const real = Array.isArray(snapshot?.events) ? snapshot.events : [];
  const base = {
    source: 'NASA_CCMC_DONKI', cache_state: snapshot?.state ?? 'NO_CACHE', fetched_at_utc: snapshot?.fetched_at ?? null,
    stale: snapshot?.state === 'STALE',
    real_events: real.slice(0, 20).map(e => ({ type: e.type, id: e.id, time_utc: e.time, url: e.url ?? null, source: e.source ?? 'NASA_CCMC_DONKI', description: e.description ?? '' })),
  };
  if (syntheticEventActive) return { ...base, status: 'DEMO_TRAINING_ALERT', level: 'CRITICAL', rule: 'synthetic training solar particle event (scenario), explicitly marked as exercise' };
  if (!snapshot || snapshot.state === 'NO_CACHE') return { ...base, status: 'DATA_UNAVAILABLE', level: 'NO_DATA', rule: null };
  if (real.length === 0) return { ...base, status: 'NO_EVENTS_RECORDED', level: 'CONTEXT', rule: null };
  return { ...base, status: 'EVENTS_NOT_EVALUATED_FOR_MISSION', level: 'CONTEXT', rule: null };
}

export function simulatedDose(elapsedHoursQuiet, elapsedHoursEvent, scenario) {
  if (!scenario || !isNum(scenario.dose_rate_msv_h)) return { status: 'DOSIMETER_NOT_CONNECTED', value_msv: null };
  const v = scenario.dose_rate_msv_h * elapsedHoursQuiet + (scenario.event_dose_rate_msv_h ?? scenario.dose_rate_msv_h) * elapsedHoursEvent;
  return { status: 'SIMULATED_DOSE', value_msv: Math.round(v * 10000) / 10000, model: EVA_RULES.dose.model, assumption: `rate ${scenario.dose_rate_msv_h} mSv/h${scenario.event_dose_rate_msv_h ? `, ${scenario.event_dose_rate_msv_h} mSv/h during synthetic event` : ''}` };
}

/* ---------------------------------------------------------------------------
 * EVA controller (state machine). Time is injected for deterministic tests.
 * States: idle -> active -> warning -> critical -> completed ; error on failures.
 * ------------------------------------------------------------------------- */
export const EVA_STATES = Object.freeze(['idle', 'active', 'warning', 'critical', 'paused', 'completed', 'error']);
const LEVEL_RANK = { NORMAL: 0, CONTEXT: 0, NO_DATA: 0, STALE: 0, INVALID: 0, NO_BASELINE: 0, WARNING: 1, CRITICAL: 2 };
const RUNNING_STATES = new Set(['active', 'warning', 'critical']);

export class EvaController {
  constructor({ scenarioId = 'nominal', now = () => Date.now(), spaceWeather = () => ({ state: 'NO_CACHE', events: [], fetched_at: null }), missionId = 'demo-mission', crewId = 'synthetic-crew-01' } = {}) {
    this.now = now; this.spaceWeather = spaceWeather; this.missionId = missionId; this.crewId = crewId;
    this.setScenario(scenarioId);
    this.reset();
  }
  setScenario(id) {
    if (!EVA_SCENARIOS[id]) throw Error('Unknown EVA scenario: ' + id);
    if (this.session && [...RUNNING_STATES, 'paused'].includes(this.session.state)) throw Error('Cannot change scenario during an active EVA.');
    this.scenario = EVA_SCENARIOS[id];
  }
  reset() { this.session = { state: 'idle' }; this.log = []; this.listeners = this.listeners || []; }
  onChange(fn) { this.listeners.push(fn); return () => { this.listeners = this.listeners.filter(f => f !== fn); }; }
  _emit() { for (const fn of this.listeners) { try { fn(this.snapshot()); } catch { /* listener errors must not break the EVA */ } } }
  _event(kind, detail, atMs = this.now(), timeBasis = 'WALL_CLOCK_UTC') { this.log.push({ at_utc: new Date(atMs).toISOString(), time_basis: timeBasis, kind, detail }); }
  scenarioTimeMs() {
    const s = this.session;
    if (!s.started_at_utc) return this.now();
    if (Number.isFinite(s.scenario_time_ms)) return s.scenario_time_ms;
    return Date.parse(s.simulation_started_at_utc ?? s.started_at_utc);
  }

  start({ simulationStartUtc = null } = {}) {
    if ([...RUNNING_STATES, 'paused'].includes(this.session.state)) return this.session; // a single session only
    const startedMs = this.now();
    const requestedSimulationStart = simulationStartUtc === null ? startedMs : Date.parse(simulationStartUtc);
    const simulationStartMs = Number.isFinite(requestedSimulationStart) ? requestedSimulationStart : startedMs;
    this.sequence = (this.sequence ?? 0) + 1;
    this.session = {
      eva_id: `demo-eva-${new Date(startedMs).toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}-${String(this.sequence).padStart(3, '0')}`,
      mission_id: this.missionId, crew_id: this.crewId, mode: 'simulation',
      scenario: this.scenario.id, training_condition: this.scenario.training_condition,
      started_at_utc: new Date(startedMs).toISOString(), ended_at_utc: null,
      simulation_started_at_utc: new Date(simulationStartMs).toISOString(), scenario_time_utc: new Date(simulationStartMs).toISOString(), scenario_time_ms: simulationStartMs,
      state: 'active', sample_index: -1, manual_critical: false, paused_at_utc: null, paused_total_ms: 0,
      temp_history: [], hr_history: [], minutes_quiet: 0, minutes_event: 0,
      alerts: [], acknowledgement: null, latest: null,
    };
    this.log = [];
    this._event('EVA_STARTED', `scenario=${this.scenario.id}`);
    this._emit();
    return this.session;
  }

  /** Advance one synthetic sample. Returns false when the scenario is exhausted. */
  step() {
    const s = this.session;
    if (!RUNNING_STATES.has(s.state)) return false;
    try {
      const next = s.sample_index + 1;
      const sample = this.scenario.samples[next];
      if (!sample) { this.end('scenario data exhausted'); return false; }
      s.sample_index = next;
      const sampleTimeMs = Date.parse(s.simulation_started_at_utc) + sample.minute * EVA_RULES.sample_interval_s * 1000;
      s.scenario_time_ms = sampleTimeMs;
      const ts = new Date(sampleTimeMs).toISOString();
      s.scenario_time_utc = ts;
      s.temp_history.push({ value: sample.core_temperature_c, source: 'synthetic', timestamp_utc: ts });
      s.hr_history.push({ value: sample.heart_rate_bpm, source: 'synthetic', timestamp_utc: ts });
      const evtAt = this.scenario.synthetic_solar_event_at_min;
      const syntheticEvent = s.manual_critical || (evtAt !== null && sample.minute >= evtAt);
      if (syntheticEvent) s.minutes_event += 1; else s.minutes_quiet += 1;
      this._evaluate(syntheticEvent, sampleTimeMs);
      return true;
    } catch (err) {
      s.state = 'error'; this._event('ERROR', String(err?.message || err)); this._emit(); return false;
    }
  }

  /** Training only: manually force the explicitly marked synthetic critical condition. */
  triggerTrainingCritical() {
    const s = this.session;
    if (!['active', 'warning'].includes(s.state)) return false;
    s.manual_critical = true; this._event('TRAINING_CRITICAL_TRIGGERED', 'manual training trigger (simulation)', this.scenarioTimeMs(), 'SCENARIO_UTC');
    this._evaluate(true, this.scenarioTimeMs()); return true;
  }

  _evaluate(syntheticEvent, nowMs = this.scenarioTimeMs()) {
    const s = this.session;
    const temp = classifyCoreTemperature(s.temp_history, nowMs);
    const hr = classifyHeartRate(s.hr_history, this.scenario.exertion_baseline_bpm, nowMs);
    const sw = evaluateSpaceWeather(this.spaceWeather(), syntheticEvent && this.scenario.training_condition || s.manual_critical);
    const dose = simulatedDose(s.minutes_quiet / 60, s.minutes_event / 60, this.scenario);
    const doseLevel = dose.value_msv === null ? 'NO_DATA' : dose.value_msv >= EVA_RULES.dose.eva_budget_msv ? 'WARNING' : 'NORMAL';
    s.latest = { core_temperature: { ...s.temp_history.at(-1), ...temp }, heart_rate: { ...s.hr_history.at(-1), ...hr }, space_weather: sw, dose: { ...dose, level: doseLevel } };

    const findings = [['core_temperature', temp], ['heart_rate', hr], ['space_weather', sw], ['dose', { level: doseLevel, rule: doseLevel === 'WARNING' ? `simulated dose >= demonstration comparison value ${EVA_RULES.dose.eva_budget_msv} mSv (not an EVA limit)` : null }]];
    const worst = findings.reduce((m, [, f]) => Math.max(m, LEVEL_RANK[f.level] ?? 0), 0);
    for (const [name, f] of findings) {
      if ((f.level === 'WARNING' || f.level === 'CRITICAL') && !s.alerts.some(a => a.indicator === name && a.level === f.level)) {
        const alert = { indicator: name, level: f.level, rule: f.rule, at_utc: new Date(nowMs).toISOString(), time_basis: 'SCENARIO_UTC', simulated: true };
        s.alerts.push(alert); this._event(`ALERT_${f.level}`, `${name}: ${f.rule}`, nowMs, 'SCENARIO_UTC');
      }
    }
    const prev = s.state;
    if (prev !== 'critical') s.state = worst === 2 ? 'critical' : worst === 1 ? 'warning' : 'active';
    if (s.state !== prev) this._event('STATE_CHANGED', `${prev} -> ${s.state}`, nowMs, 'SCENARIO_UTC');
    this._emit();
  }

  /** Text of the advisory, only when a critical simulated rule fired. */
  advisory() {
    const s = this.session;
    if (s.state !== 'critical') return null;
    const cause = s.alerts.filter(a => a.level === 'CRITICAL')[0];
    return { text: 'Return to airlock — simulated EVA safety advisory', rule: cause?.rule ?? 'unknown', indicator: cause?.indicator ?? null, at_utc: cause?.at_utc ?? null };
  }

  acknowledge(by = 'synthetic-crew-01') {
    const s = this.session;
    if (s.state !== 'critical' || s.acknowledgement) return false;
    s.acknowledgement = { by, at_utc: new Date(this.now()).toISOString() };
    this._event('ADVISORY_ACKNOWLEDGED', by); this._emit(); return true;
  }

  pause() {
    const s = this.session;
    if (!RUNNING_STATES.has(s.state)) return false;
    s.paused_state = s.state; s.state = 'paused'; s.paused_at_utc = new Date(this.now()).toISOString();
    this._event('EVA_PAUSED', 'simulation paused by user'); this._emit(); return true;
  }

  resume() {
    const s = this.session;
    if (s.state !== 'paused' || !s.paused_at_utc) return false;
    const now = this.now();
    s.paused_total_ms += Math.max(0, now - Date.parse(s.paused_at_utc));
    s.paused_at_utc = null;
    const prior = s.paused_state;
    delete s.paused_state;
    s.state = RUNNING_STATES.has(prior) ? prior : 'active';
    this._event('EVA_RESUMED', 'simulation resumed'); this._emit(); return true;
  }

  end(reason = 'ended by astronaut') {
    const s = this.session;
    if (![...RUNNING_STATES, 'paused'].includes(s.state)) return false;
    s.ended_at_utc = new Date(this.now()).toISOString(); s.final_state = s.state; s.state = 'completed';
    this._event('EVA_ENDED', reason); this._emit(); return true;
  }

  elapsedSeconds() {
    const s = this.session; if (!s.started_at_utc) return 0;
    const end = s.ended_at_utc ? Date.parse(s.ended_at_utc) : this.now();
    const pausedNow = s.paused_at_utc ? Math.max(0, end - Date.parse(s.paused_at_utc)) : 0;
    return Math.max(0, Math.round((end - Date.parse(s.started_at_utc) - (s.paused_total_ms ?? 0) - pausedNow) / 1000));
  }

  scenarioElapsedSeconds() { return Math.max(0, (this.session.sample_index + 1) * EVA_RULES.sample_interval_s); }
  snapshot() { return { session: this.session, scenario: this.scenario, log: [...this.log], advisory: this.advisory(), elapsed_s: this.elapsedSeconds(), scenario_elapsed_s: this.scenarioElapsedSeconds() }; }
}

/* ---------------------------------------------------------------------------
 * EVA Medical Handover Report (prepared locally, never sent automatically).
 * ------------------------------------------------------------------------- */
function summary(hist) {
  const v = hist.map(h => h.value).filter(isNum);
  if (!v.length) return { samples: 0, min: null, max: null, last: null };
  return { samples: v.length, min: Math.min(...v), max: Math.max(...v), last: v.at(-1) };
}

export function buildHandoverReport(controller, generatedAtMs = controller.now()) {
  const s = controller.session, sc = controller.scenario;
  if (!s.started_at_utc) throw Error('No EVA session to report.');
  const sw = s.latest?.space_weather ?? evaluateSpaceWeather(controller.spaceWeather(), false);
  return {
    report_type: 'EVA Medical Handover Report',
    mode: 'SIMULATION',
    training_condition: sc.training_condition,
    software_version: EVA_MODULE_VERSION,
    generated_at_utc: new Date(generatedAtMs).toISOString(),
    delivery_status: 'PREPARED_LOCALLY_NOT_SENT',
    mission_id: s.mission_id, eva_id: s.eva_id, crew_id: s.crew_id,
    scenario: { id: sc.id, label: sc.label },
    started_at_utc: s.started_at_utc, ended_at_utc: s.ended_at_utc, duration_s: controller.elapsedSeconds(),
    timing: { wall_clock_duration_s: controller.elapsedSeconds(), scenario_elapsed_s: controller.scenarioElapsedSeconds(), scenario_time_utc: s.scenario_time_utc, event_time_basis: 'SCENARIO_UTC', started_and_ended_at_time_basis: 'WALL_CLOCK_UTC' },
    scenario_elapsed_s: controller.scenarioElapsedSeconds(), scenario_time_utc: s.scenario_time_utc,
    final_state: s.final_state ?? s.state,
    baseline: { heart_rate_exertion_bpm: sc.exertion_baseline_bpm ?? null, note: 'Synthetic demo profile' },
    core_temperature_c: { ...summary(s.temp_history), source: 'synthetic', note: 'Core temperature, not skin temperature' },
    heart_rate_bpm: { ...summary(s.hr_history), source: 'synthetic' },
    dose: s.latest?.dose ?? { status: 'DOSIMETER_NOT_CONNECTED', value_msv: null },
    space_weather: { status: sw.status, cache_state: sw.cache_state, fetched_at_utc: sw.fetched_at_utc, stale: sw.stale, real_events_consulted: sw.real_events, note: 'DONKI provides research/prototyping space-weather context only; it is not an EVA safety alert system nor a personal dosimeter.' },
    alerts: s.alerts, acknowledgement: s.acknowledgement, event_log: [...controller.log],
    rules_applied: EVA_RULES,
    limitations: [
      'Synthetic data only; no sensors, suit telemetry or dosimeter connected.',
      'Thresholds are illustrative configurable software rules, not medically or operationally validated cutoffs and not NASA-certified limits.',
      'Real DONKI events are shown as context and never trigger the advisory by themselves.',
      'The advisory is a simulated recommendation; ASTHRAL does not control suits, navigation or communications.',
      'Not clinically, operationally or flight validated.',
    ],
  };
}

export function reportToText(r) {
  const L = [];
  L.push(`${r.report_type} — MODE: ${r.mode}${r.training_condition ? ' (TRAINING EXERCISE)' : ''}`);
  L.push(`Generated: ${r.generated_at_utc} · ${r.software_version} · Delivery: ${r.delivery_status}`);
  L.push(`Mission ${r.mission_id} · EVA ${r.eva_id} · Crew ${r.crew_id} · Scenario: ${r.scenario.label}`);
  L.push(`Wall-clock start ${r.started_at_utc} · end ${r.ended_at_utc ?? 'in progress'} · duration ${Math.round(r.duration_s / 60)} min · final state ${r.final_state}`);
  L.push(`Scenario elapsed ${Math.round(r.scenario_elapsed_s / 60)} min · scenario time ${r.scenario_time_utc ?? 'not started'} UTC · accelerated simulation clock`);
  L.push(`Core temperature (synthetic): last ${r.core_temperature_c.last} °C, min ${r.core_temperature_c.min}, max ${r.core_temperature_c.max}`);
  L.push(`Heart rate (synthetic): last ${r.heart_rate_bpm.last} bpm, max ${r.heart_rate_bpm.max}; exertion baseline ${r.baseline.heart_rate_exertion_bpm} bpm`);
  L.push(`Dose: ${r.dose.status}${r.dose.value_msv !== null ? ` ${r.dose.value_msv} mSv (${r.dose.assumption}; demonstration comparison value is not an EVA limit)` : ''}`);
  L.push(`Space weather: ${r.space_weather.status} · cache ${r.space_weather.cache_state}${r.space_weather.fetched_at_utc ? ' fetched ' + r.space_weather.fetched_at_utc : ''} · real DONKI events consulted: ${r.space_weather.real_events_consulted.length}`);
  for (const e of r.space_weather.real_events_consulted.slice(0, 5)) L.push(`  - ${e.type} ${e.id} ${e.time_utc} ${e.url ?? ''} [${e.source}]`);
  L.push(`Alerts: ${r.alerts.length ? '' : 'none'}`);
  for (const a of r.alerts) L.push(`  - ${a.level} ${a.indicator} at ${a.at_utc}: ${a.rule} (simulated)`);
  L.push(`Acknowledgement: ${r.acknowledgement ? r.acknowledgement.by + ' at ' + r.acknowledgement.at_utc : 'none'}`);
  L.push('Limitations: ' + r.limitations.join(' '));
  return L.join('\n');
}
