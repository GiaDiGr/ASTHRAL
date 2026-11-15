// ASTHRAL · EVA Monitoring — view adapter.
// Integration point:  import { mountEvaMonitoring } from './eva-view.js';
//                     mountEvaMonitoring(document.querySelector('#eva-monitoring'));
// Reuses the existing DONKI client/cache from ./space-weather.js (no second HTTP client).
import { cachedDonkiSnapshot, DONKI_HISTORICAL_FIXTURE } from './space-weather.js';
import { EvaController, EVA_SCENARIOS, EVA_RULES, buildHandoverReport, reportToText } from './eva-monitoring.js';

const STYLE_ID = 'asthral-eva-style';
const CSS = `
.eva{--g:#16a34a;--y:#ca8a04;--r:#dc2626;--n:#64748b;font-family:inherit;color:inherit}
.eva .bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
.eva button,.eva select{font:inherit;padding:8px 14px;border-radius:10px;border:1px solid currentColor;background:transparent;color:inherit;cursor:pointer}
.eva button.primary{background:#2563eb;color:#fff;border-color:#2563eb;font-weight:700}
.eva button:disabled{opacity:.45;cursor:default}
.eva .sim{font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;background:#334155;color:#fff}
.eva .advisory{display:none;padding:16px;border-radius:12px;background:var(--r);color:#fff;font-size:20px;font-weight:800;margin-bottom:12px}
.eva .advisory.show{display:block}.eva .advisory small{display:block;font-size:13px;font-weight:500;margin-top:6px}
.eva .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.eva .card{border:1px solid #475569;border-left:8px solid var(--n);border-radius:12px;padding:14px}
.eva .card[data-level=NORMAL]{border-left-color:var(--g)}.eva .card[data-level=WARNING]{border-left-color:var(--y)}.eva .card[data-level=CRITICAL]{border-left-color:var(--r)}
.eva .card h3{margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.05em}
.eva .val{font-size:34px;font-weight:800}.eva .lvl{font-weight:700;font-size:13px}.eva .meta{font-size:12px;opacity:.8;margin-top:6px}
.eva .log{font-size:12px;max-height:160px;overflow:auto;margin-top:12px;border-top:1px solid #475569;padding-top:8px}
.eva pre{white-space:pre-wrap;font-size:12px;border:1px solid #475569;border-radius:10px;padding:10px;max-height:280px;overflow:auto}
`;
const LABEL = { NORMAL: 'Normal', WARNING: 'Caution', CRITICAL: 'Critical', NO_DATA: 'No information', STALE: 'Stale data', INVALID: 'Invalid data', NO_BASELINE: 'No baseline available', CONTEXT: 'Context only' };

function el(tag, attrs = {}, text) { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text !== undefined) e.textContent = text; return e; }

/** Offline demo: if there is no DONKI cache, show the existing historical fixture, clearly labelled. */
export function spaceWeatherProvider({ now = () => Date.now(), useFixtureWhenEmpty = true } = {}) {
  return () => {
    const snap = cachedDonkiSnapshot(now());
    if (snap.state === 'NO_CACHE' && useFixtureWhenEmpty) return { state: 'FIXTURE', events: [DONKI_HISTORICAL_FIXTURE], fetched_at: null, note: 'Example data: fixed historical DONKI fixture (offline demo)' };
    return snap;
  };
}

export function mountEvaMonitoring(container, { now = () => Date.now(), stepMs = 1000, spaceWeather = spaceWeatherProvider({ now }) } = {}) {
  if (!container) throw Error('EVA container not found');
  if (!document.getElementById(STYLE_ID)) { const s = el('style', { id: STYLE_ID }); s.textContent = CSS; document.head.appendChild(s); }
  const ctl = new EvaController({ now, spaceWeather });
  let timer = null;
  const root = el('section', { class: 'eva', 'aria-label': 'EVA Monitoring (simulation)' });

  const bar = el('div', { class: 'bar' });
  const scenarioSel = el('select', { 'aria-label': 'Synthetic EVA scenario' });
  for (const sc of Object.values(EVA_SCENARIOS)) scenarioSel.appendChild(el('option', { value: sc.id }, sc.label));
  const startBtn = el('button', { class: 'primary', type: 'button' }, 'Start EVA');
  const endBtn = el('button', { type: 'button' }, 'End EVA');
  const trainBtn = el('button', { type: 'button', title: 'Training exercise only' }, 'Trigger training critical');
  const ackBtn = el('button', { type: 'button' }, 'Acknowledge advisory');
  const reportBtn = el('button', { type: 'button' }, 'Prepare handover report');
  bar.append(scenarioSel, startBtn, endBtn, trainBtn, ackBtn, reportBtn, el('span', { class: 'sim' }, 'SIMULATION · synthetic data'));

  const advisory = el('div', { class: 'advisory', role: 'alert', 'aria-live': 'assertive' });
  const grid = el('div', { class: 'grid' });
  const cards = {};
  for (const [key, title] of [['temp', '🌡️ Core Temperature'], ['hr', '❤️ Heart Rate'], ['sw', '☀️ Solar Weather · NASA DONKI'], ['dose', '⏱️ EVA Timer + Radiation Dose']]) {
    const c = el('div', { class: 'card', 'data-level': 'NO_DATA' });
    c.append(el('h3', {}, title), el('div', { class: 'val' }, '—'), el('div', { class: 'lvl' }, LABEL.NO_DATA), el('div', { class: 'meta' }, ''));
    cards[key] = c; grid.appendChild(c);
  }
  const log = el('div', { class: 'log', 'aria-label': 'EVA event log' });
  const report = el('pre', { hidden: '' });
  root.append(bar, advisory, grid, log, report);
  container.replaceChildren(root);

  const setCard = (c, level, value, meta) => { c.dataset.level = level; c.children[1].textContent = value; c.children[2].textContent = LABEL[level] ?? level; c.children[3].textContent = meta; };
  const mmss = s => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  function render(snap) {
    const s = snap.session, L = s.latest, active = ['active', 'warning', 'critical'].includes(s.state);
    startBtn.disabled = active; endBtn.disabled = !active; scenarioSel.disabled = active;
    trainBtn.disabled = !(active && s.state !== 'critical'); ackBtn.disabled = !(s.state === 'critical' && !s.acknowledgement); reportBtn.disabled = !s.started_at_utc;
    if (!L) { for (const k of ['temp', 'hr', 'sw']) setCard(cards[k], 'NO_DATA', '—', 'Start EVA to begin.'); }
    else {
      const t = L.core_temperature, h = L.heart_rate, w = L.space_weather, d = L.dose;
      const trend = (hist) => hist.length > 1 ? (hist.at(-1).value > hist.at(-2).value ? '↑' : hist.at(-1).value < hist.at(-2).value ? '↓' : '→') : '';
      setCard(cards.temp, t.level, `${t.value ?? '—'} °C ${trend(s.temp_history)}`, `Core temperature (not skin) · source: ${t.source} · ${t.rule ?? 'within prototype range'}`);
      setCard(cards.hr, h.level, `${h.value ?? '—'} bpm ${trend(s.hr_history)}`, h.baseline ? `Δ ${h.value - h.baseline} bpm vs EVA-exertion baseline ${h.baseline} bpm · source: ${h.source}` : 'No baseline available');
      const swText = { DATA_UNAVAILABLE: 'Data not available', NO_EVENTS_RECORDED: 'No events recorded', EVENTS_NOT_EVALUATED_FOR_MISSION: `${w.real_events.length} event(s) — not evaluated for this mission`, DEMO_TRAINING_ALERT: 'TRAINING: synthetic particle event' }[w.status];
      const first = w.real_events[0];
      setCard(cards.sw, w.level, swText, `${first ? `${first.type} ${first.time_utc} · ${first.source}` : 'No real event listed'} · cache: ${w.cache_state}${w.fetched_at_utc ? ' updated ' + w.fetched_at_utc : ''}${w.stale ? ' (STALE)' : ''}`);
      setCard(cards.dose, d.value_msv === null ? 'NO_DATA' : d.level, d.value_msv === null ? 'DOSIMETER NOT CONNECTED' : `${d.value_msv} mSv`, `${d.value_msv === null ? '' : 'SIMULATED DOSE · ' + d.assumption + ' · '}EVA time ${mmss(snap.elapsed_s)}`);
    }
    const adv = snap.advisory;
    advisory.classList.toggle('show', !!adv);
    if (adv) { advisory.textContent = adv.text; advisory.appendChild(el('small', {}, `Rule: ${adv.rule} · at ${adv.at_utc}${s.acknowledgement ? ' · acknowledged ' + s.acknowledgement.at_utc : ' · awaiting acknowledgement'}`)); }
    log.replaceChildren(...snap.log.slice(-30).reverse().map(e => el('div', {}, `${e.at_utc} · ${e.kind} · ${e.detail}`)));
  }

  ctl.onChange(render);
  const stop = () => { if (timer) { clearInterval(timer); timer = null; } };
  startBtn.addEventListener('click', () => { ctl.setScenario(scenarioSel.value); ctl.start(); stop(); timer = setInterval(() => { if (!ctl.step()) stop(); }, stepMs); ctl.step(); });
  endBtn.addEventListener('click', () => { stop(); ctl.end('ended by astronaut'); });
  trainBtn.addEventListener('click', () => ctl.triggerTrainingCritical());
  ackBtn.addEventListener('click', () => ctl.acknowledge());
  reportBtn.addEventListener('click', () => { const r = buildHandoverReport(ctl); report.hidden = false; report.textContent = reportToText(r); report.dataset.json = JSON.stringify(r); });
  render(ctl.snapshot());
  return { controller: ctl, destroy: () => { stop(); container.replaceChildren(); }, rules: EVA_RULES };
}
