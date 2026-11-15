// EVA monitoring integration by Marfe, contributed in ASTHRAL PR #2.
// The view reuses ASTHRAL's existing DONKI cache; all sensor and dose values remain synthetic.
import { cachedDonkiSnapshot, DONKI_HISTORICAL_FIXTURE } from './space-weather.js';
import { EvaController, EVA_SCENARIOS, EVA_RULES, buildHandoverReport, reportToText } from './eva-monitoring.js';

const LABEL = {
  NORMAL: 'Within demo range', WARNING: 'Demo caution', CRITICAL: 'Demo critical',
  NO_DATA: 'No information', STALE: 'Stale data', INVALID: 'Invalid data',
  NO_BASELINE: 'No reference available', CONTEXT: 'Context only',
};

function el(tag, attrs = {}, text) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  return element;
}

/** Offline demo: reuse the DONKI cache, otherwise label a fixed historical fixture. */
export function spaceWeatherProvider({ now = () => Date.now(), useFixtureWhenEmpty = true } = {}) {
  return () => {
    const snapshot = cachedDonkiSnapshot(now());
    if (snapshot.state === 'NO_CACHE' && useFixtureWhenEmpty) {
      return { state: 'FIXTURE', events: [DONKI_HISTORICAL_FIXTURE], fetched_at: null, note: 'Fixed historical example; not current.' };
    }
    return snapshot;
  };
}

export function mountEvaMonitoring(container, {
  now = () => Date.now(), stepMs = 1000, spaceWeather = spaceWeatherProvider({ now }),
  onScenarioChange = () => {}, onScenarioTime = () => {}, onScenarioActive = () => {}, onStart = () => null,
  onComplete = async () => {},
} = {}) {
  if (!container) throw Error('EVA container not found.');
  const controller = new EvaController({ now, spaceWeather });
  let timer = null, completionPromise = null, savedEvaId = null;
  const root = el('section', { class: 'eva-monitoring', 'aria-label': 'EVA monitoring simulation' });
  const bar = el('div', { class: 'eva-toolbar' });
  const scenarioLabel = el('label', {}, 'Synthetic scenario');
  const scenarioSelect = el('select', { 'aria-label': 'Synthetic EVA scenario' });
  for (const scenario of Object.values(EVA_SCENARIOS)) scenarioSelect.append(el('option', { value: scenario.id }, scenario.label));
  scenarioLabel.append(scenarioSelect);
  const startButton = el('button', { type: 'button', class: 'primary-action' }, 'Start EVA');
  const pauseButton = el('button', { type: 'button' }, 'Pause EVA');
  const resumeButton = el('button', { type: 'button' }, 'Resume EVA');
  const endButton = el('button', { type: 'button' }, 'End EVA');
  const trainingButton = el('button', { type: 'button', title: 'Training simulation only' }, 'Trigger training alert');
  const acknowledgeButton = el('button', { type: 'button' }, 'Acknowledge advisory');
  const reportButton = el('button', { type: 'button' }, 'Generate handover report');
  const simulationTag = el('span', { class: 'eva-simulation-tag' }, 'SIMULATION · SYNTHETIC DATA');
  bar.append(scenarioLabel, startButton, pauseButton, resumeButton, endButton, trainingButton, acknowledgeButton, reportButton, simulationTag);

  const intro = el('p', { class: 'eva-prototype-note' }, 'This software scenario is not flight telemetry. Configured advisory values are demonstration rules, not medically validated limits or autonomous EVA commands.');
  const advisory = el('div', { class: 'eva-advisory', role: 'alert', 'aria-live': 'assertive', hidden: '' });
  const cards = el('div', { class: 'eva-cards' });
  const indicators = {};
  for (const [key, title, detail] of [
    ['temperature', 'Core body temperature', 'Synthetic core-temperature series · °C'],
    ['heart-rate', 'Heart rate vs scenario reference', 'Synthetic heart-rate series · bpm'],
    ['space-weather', 'Solar-weather context', 'NASA CCMC DONKI cache or a labeled historical fixture'],
    ['time-dose', 'EVA time and radiation', 'Scenario clock · synthetic dose only · no dosimeter'],
  ]) {
    const card = el('article', { class: 'eva-card', 'data-level': 'NO_DATA' });
    const heading = el('p', { class: 'eva-card-label' }, title);
    const value = el('strong', { class: 'eva-card-value' }, '—');
    const state = el('span', { class: 'eva-card-state' }, LABEL.NO_DATA);
    const meta = el('p', { class: 'eva-card-meta' }, detail);
    card.append(heading, value, state, meta);
    indicators[key] = { card, value, state, meta };
    cards.append(card);
  }
  const logSection = el('section', { class: 'eva-log-panel' });
  const logTitle = el('h3', {}, 'Mission activity log');
  const log = el('ol', { class: 'eva-log', 'aria-label': 'Synthetic EVA event log' });
  const saveStatus = el('p', { role: 'status', 'aria-live': 'polite' }, 'Completed EVA reports are stored in the encrypted local profile.');
  logSection.append(logTitle, log, saveStatus);
  const reportSection = el('section', { class: 'eva-report-panel', hidden: '' });
  reportSection.append(el('h3', {}, 'Medical ground handover report'));
  const reportText = el('pre', { class: 'eva-report' });
  const reportActions = el('div', { class: 'row' });
  const downloadButton = el('button', { type: 'button' }, 'Download synthetic report JSON');
  reportActions.append(downloadButton);
  reportSection.append(reportText, reportActions);
  root.append(bar, intro, advisory, cards, logSection, reportSection);
  container.replaceChildren(root);

  const setIndicator = (key, level, value, meta) => {
    const item = indicators[key];
    item.card.dataset.level = level;
    item.value.textContent = value;
    item.state.textContent = LABEL[level] ?? level;
    item.meta.textContent = meta;
  };
  const formatClock = seconds => {
    const n = Math.max(0, Math.floor(seconds));
    return `${String(Math.floor(n / 3600)).padStart(2, '0')}:${String(Math.floor(n % 3600 / 60)).padStart(2, '0')}:${String(n % 60).padStart(2, '0')}`;
  };

  function render(snapshot) {
    const session = snapshot.session;
    const active = ['active', 'warning', 'critical'].includes(session.state);
    const paused = session.state === 'paused';
    const inProgress = active || paused;
    startButton.disabled = inProgress;
    endButton.disabled = !inProgress;
    pauseButton.disabled = !active;
    resumeButton.disabled = !paused;
    scenarioSelect.disabled = active || paused;
    onScenarioActive(inProgress);
    if (session.scenario_time_utc) onScenarioTime(session.scenario_time_utc, { active: inProgress, paused });
    trainingButton.disabled = !(active && session.state !== 'critical');
    acknowledgeButton.disabled = !(session.state === 'critical' && !session.acknowledgement);
    reportButton.disabled = !session.started_at_utc;
    if (!session.latest) {
      for (const key of Object.keys(indicators)) setIndicator(key, 'NO_DATA', '—', 'Start the synthetic EVA scenario to display data.');
    } else {
      const latest = session.latest;
      const trend = history => history.length > 1
        ? (history.at(-1).value > history.at(-2).value ? '↑' : history.at(-1).value < history.at(-2).value ? '↓' : '→') : '';
      const temperature = latest.core_temperature;
      setIndicator('temperature', temperature.level, `${temperature.value ?? '—'} °C ${trend(session.temp_history)}`.trim(),
        `Synthetic source · core temperature, not skin temperature · ${temperature.rule ?? 'no demonstration rule fired'}`);
      const heart = latest.heart_rate;
      setIndicator('heart-rate', heart.level, `${heart.value ?? '—'} bpm ${trend(session.hr_history)}`.trim(),
        heart.baseline === null ? 'No comparable personal EVA baseline is available; this demonstration uses a fixed synthetic scenario reference.'
          : `Δ ${heart.value - heart.baseline} bpm vs synthetic scenario exertion reference ${heart.baseline} bpm · not a personal measurement`);
      const weather = latest.space_weather;
      const weatherLabel = {
        DATA_UNAVAILABLE: 'Data unavailable', NO_EVENTS_RECORDED: 'No events recorded',
        EVENTS_NOT_EVALUATED_FOR_MISSION: `${weather.real_events.length} event(s) · context only`,
        DEMO_TRAINING_ALERT: 'Synthetic training event',
      }[weather.status] ?? 'Context only';
      const event = weather.real_events[0];
      setIndicator('space-weather', weather.level, weatherLabel,
        `${event ? `${event.type} · ${event.time_utc ?? 'UTC time not provided'}` : 'No event listed'} · ${weather.cache_state === 'FIXTURE' ? 'fixed historical fixture, not current' : `cache ${weather.cache_state}`}${weather.fetched_at_utc ? ` · retrieved ${weather.fetched_at_utc}` : ''}${weather.stale ? ' · stale cache' : ''} · no personal exposure inference`);
      const dose = latest.dose;
      setIndicator('time-dose', dose.value_msv === null ? 'NO_DATA' : dose.level,
        dose.value_msv === null ? 'No dosimeter connected' : `${dose.value_msv} mSv · simulated`,
        `Scenario elapsed ${formatClock(snapshot.scenario_elapsed_s)} · wall clock ${formatClock(snapshot.elapsed_s)} · ${dose.value_msv === null ? 'dose unknown' : 'synthetic model; no dose measurement'}`);
    }
    const notice = controller.advisory();
    advisory.hidden = !notice;
    advisory.replaceChildren();
    if (notice) {
      advisory.append(el('strong', {}, 'Return to airlock — simulated mission advisory'));
      advisory.append(el('p', {}, `Demonstration rule: ${notice.rule}`));
      advisory.append(el('small', {}, `${notice.at_utc} UTC scenario time · this software does not command an EVA or suit.`));
      if (session.acknowledgement) advisory.append(el('p', {}, `Acknowledged in simulation at ${session.acknowledgement.at_utc} UTC wall-clock time.`));
    }
    log.replaceChildren(...snapshot.log.slice(-40).map(entry => {
      const row = el('li');
      row.append(el('time', { dateTime: entry.at_utc }, `${entry.at_utc} UTC · ${entry.time_basis === 'SCENARIO_UTC' ? 'scenario clock' : 'wall clock'}`));
      row.append(el('span', {}, `${entry.kind.replaceAll('_', ' ')} · ${entry.detail}`));
      return row;
    }));
  }

  function stopTimer() { if (timer !== null) { clearInterval(timer); timer = null; } }
  function startTimer() { stopTimer(); timer = setInterval(() => { if (!controller.step()) stopTimer(); }, Math.max(100, stepMs)); }

  async function finalizeReport() {
    const session = controller.session;
    if (session.state !== 'completed' || savedEvaId === session.eva_id) return;
    if (completionPromise) return completionPromise;
    const report = buildHandoverReport(controller);
    const snapshot = controller.snapshot();
    reportSection.hidden = false;
    reportText.textContent = reportToText(report);
    reportSection.dataset.reportJson = JSON.stringify(report);
    saveStatus.textContent = 'Saving the completed synthetic report to local history…';
    completionPromise = Promise.resolve(onComplete({ report, snapshot })).then(result => {
      savedEvaId = session.eva_id;
      saveStatus.textContent = result?.storage_scope === 'ENCRYPTED_LOCAL_PROFILE'
        ? 'Synthetic EVA report saved in the encrypted local profile.'
        : 'Synthetic EVA report saved in temporary demo memory; it will be discarded when the demo closes.';
    }).catch(error => {
      saveStatus.textContent = `Report remains visible but could not be saved: ${error.message}`;
      completionPromise = null;
    });
    return completionPromise;
  }

  controller.onChange(snapshot => {
    render(snapshot);
    if (snapshot.session.state === 'completed') void finalizeReport();
  });
  startButton.addEventListener('click', () => {
    completionPromise = null; savedEvaId = null; reportSection.hidden = true; reportText.textContent = '';
    controller.setScenario(scenarioSelect.value);
    onScenarioChange(scenarioSelect.value);
    const simulationStartUtc = onStart();
    controller.start({ simulationStartUtc: typeof simulationStartUtc === 'string' ? simulationStartUtc : null });
    controller.step(); startTimer();
  });
  scenarioSelect.addEventListener('change', () => onScenarioChange(scenarioSelect.value));
  pauseButton.addEventListener('click', () => { if (controller.pause()) stopTimer(); });
  resumeButton.addEventListener('click', () => { if (controller.resume()) startTimer(); });
  endButton.addEventListener('click', () => { stopTimer(); controller.end('ended by user in synthetic mission demonstration'); });
  trainingButton.addEventListener('click', () => controller.triggerTrainingCritical());
  acknowledgeButton.addEventListener('click', () => controller.acknowledge('synthetic crew participant'));
  reportButton.addEventListener('click', () => {
    const report = buildHandoverReport(controller);
    reportSection.hidden = false;
    reportText.textContent = reportToText(report);
    reportSection.dataset.reportJson = JSON.stringify(report);
  });
  downloadButton.addEventListener('click', () => {
    const raw = reportSection.dataset.reportJson;
    if (!raw) return;
    const report = JSON.parse(raw);
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = el('a', { href: url, download: `asthral-synthetic-eva-${report.eva_id}.json` });
    link.click(); URL.revokeObjectURL(url);
  });
  render(controller.snapshot());
  return {
    controller,
    destroy() { stopTimer(); container.replaceChildren(); },
    async finalizeIfActive() {
      if (['active', 'warning', 'critical', 'paused'].includes(controller.session.state)) {
        stopTimer(); controller.end('profile locked; synthetic session finalized locally'); await finalizeReport();
      } else if (controller.session.state === 'completed') await finalizeReport();
    },
    rules: EVA_RULES,
  };
}
