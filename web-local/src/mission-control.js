import { mountOrbitalView } from './orbital-view.js';
import { mountEvaMonitoring } from './eva-view.js';
import { mountRadLabExplorer } from './radlab-view.js';

const ACTIVE = new Set(['active', 'warning', 'critical', 'paused']);

function activityRecord(report, snapshot) {
  const session = snapshot.session;
  return {
    id: `eva-${session.eva_id}-${crypto.randomUUID()}`,
    mission_id: session.mission_id,
    eva_id: session.eva_id,
    mode: 'SIMULATION',
    scenario_id: session.scenario,
    started_at_utc: session.started_at_utc,
    ended_at_utc: session.ended_at_utc,
    final_state: session.final_state ?? session.state,
    training_condition: Boolean(session.training_condition),
    report,
    session: {
      state: session.state,
      sample_index: session.sample_index,
      latest: session.latest,
      alerts: session.alerts,
      acknowledgement: session.acknowledgement,
      temp_history: session.temp_history,
      hr_history: session.hr_history,
      log: snapshot.log,
      scenario_time_utc: session.scenario_time_utc,
    },
  };
}

export async function mountMissionControl({ page, call, persist, status = () => {}, isTemporary = () => false } = {}) {
  if (!page || typeof call !== 'function' || typeof persist !== 'function') throw new Error('Mission Control dependencies are incomplete.');
  const orbitalHost = page.querySelector('#mission-orbital');
  const evaHost = page.querySelector('#mission-eva');
  const radlabHost = page.querySelector('#mission-radlab');
  const powerSelect = page.querySelector('#mission-power-mode');
  const evaRadLabContext = page.querySelector('#eva-radlab-context');
  const stateLine = page.querySelector('#mission-control-status');
  const scenario = { value: 'nominal' };
  let orbitalState = null;
  let eva = null;
  let saving = Promise.resolve();
  let radLabMapCount = 0;

  const orbital = await mountOrbitalView(orbitalHost, {
    scenario: () => scenario.value,
    onState: state => {
      orbitalState = state;
      if (!stateLine) return;
      if (!state) stateLine.textContent = 'Orbit status unavailable. Synthetic EVA scenarios remain separately available.';
      else stateLine.textContent = `${state.mode === 'SIMULATED' ? 'Synthetic' : 'Estimated'} orbital context · ${state.timestampUtc} UTC · EVA readings remain synthetic.`;
    },
  });

  eva = mountEvaMonitoring(evaHost, {
    onScenarioChange: id => {
      scenario.value = id;
      orbital.setScenario?.(id);
    },
    onStart: () => orbitalState?.timestampUtc ?? new Date().toISOString(),
    onScenarioTime: (timeUtc, { active } = {}) => {
      orbital.setMissionTime?.(timeUtc);
      if (active) orbital.setScenarioActive?.(true);
    },
    onScenarioActive: active => orbital.setScenarioActive?.(active),
    onComplete: ({ report, snapshot }) => {
      saving = saving.then(async () => {
        const record = activityRecord(report, snapshot);
        const saved = await call('eva_activity_add', record);
        await persist();
        const storageScope = isTemporary() ? 'TEMPORARY_DEMO_MEMORY' : 'ENCRYPTED_LOCAL_PROFILE';
        status(storageScope === 'TEMPORARY_DEMO_MEMORY'
          ? 'Synthetic EVA report is recorded in temporary demo memory and will be discarded when the demo closes.'
          : 'Synthetic EVA report saved in the encrypted local profile.');
        return { saved, storage_scope: storageScope };
      });
      return saving;
    },
  });

  const radlab = mountRadLabExplorer(radlabHost, {
    onObservations: (observations, selected) => {
      radLabMapCount = orbital.setRadLabObservations?.(observations, selected) ?? 0;
    },
    onContext: (row, snapshot) => {
      if (!evaRadLabContext) return;
      evaRadLabContext.textContent = row
        ? `Historical RadLab context selected · ${row.observed_at_utc} UTC · ${row.instrument_id ?? 'instrument not identified'} · ${snapshot?.observations?.length ?? 0} archive record(s) loaded · ${radLabMapCount} record(s) with valid coordinates shown on the globe. This does not enter the EVA assessment, calculate individual dose or trigger a safety alert.`
        : 'Historical NASA RadLab observations are not used to calculate individual EVA dose or produce safety alerts. Load an archive query below to review environmental context.';
    },
  });
  const applyPowerMode = mode => orbital.setPowerMode?.(mode || 'FULL');
  const onPowerMode = event => applyPowerMode(event.detail?.mode ?? powerSelect?.value);
  window.addEventListener('asthral:power-mode', onPowerMode);
  applyPowerMode(powerSelect?.value || document.querySelector('#mode')?.value || 'FULL');

  return {
    setVisible(visible) { orbital.setVisible?.(visible); },
    async destroy({ finalize = false } = {}) {
      window.removeEventListener('asthral:power-mode', onPowerMode);
      if (finalize && ACTIVE.has(eva.controller.session.state)) eva.controller.end('profile locked; synthetic session finalized locally');
      if (finalize) await eva.finalizeIfActive();
      radlab.destroy(); eva.destroy();
      orbital.destroy();
    },
    get controllers() { return { eva: eva.controller, orbital }; },
  };
}
