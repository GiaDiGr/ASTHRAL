const list = value => Array.isArray(value) ? value : [];
const containsSyntheticMarker = value => typeof value === 'string' && /SYNTHETIC/i.test(value);

/** Produce an aggregate-only, synthetic demo report. Never returns clinical values or identifiers. */
export function createSyntheticMissionSummary(timeline, history = null, generatedAt = new Date().toISOString()) {
  const measurements = list(timeline?.measurement).map(row => row?.measurement)
    .filter(row => row && row.synthetic === true);
  const measurementIds = new Set(measurements.map(row => row.id).filter(id => typeof id === 'string'));
  const baselines = list(timeline?.baseline).filter(row => {
    const ids = row?.input_ids ?? row?.request?.measurement_ids ?? row?.measurement_ids;
    return Array.isArray(ids) && ids.length > 0 && ids.every(id => measurementIds.has(id));
  });
  const baselineIds = new Set(baselines.map(row => row.id).filter(id => typeof id === 'string'));
  const monitoringRuns = list(timeline?.monitoring_run).filter(row => {
    const source = row?.policy_reference ?? row?.request?.policy_reference ?? row?.protocol_reference;
    const ids = list(row?.baseline_ids ?? row?.request?.baseline_ids);
    return containsSyntheticMarker(source) && ids.length > 0 && ids.every(id => baselineIds.has(id));
  });
  const syntheticEpisodeIds = new Set(monitoringRuns.flatMap(row => Object.values(row?.episode_ids ?? {}))
    .filter(id => typeof id === 'string'));
  const syntheticFollowupIds = new Set(monitoringRuns.flatMap(row => list(row?.followup_ids))
    .filter(id => typeof id === 'string'));
  const followupPlans = list(timeline?.followup).filter(row =>
    syntheticFollowupIds.has(row?.id) && syntheticEpisodeIds.has(row?.episode_id));
  const preventionEntries = list(history?.prevention_entries).filter(row => row?.synthetic_data === true);
  const radiationRecords = list(history?.radiation_records).filter(row => row?.synthetic_data === true);

  return {
    format: 'ASTHRAL-SYNTHETIC-MISSION-SUMMARY-1',
    generated_at: generatedAt,
    synthetic_data_only: true,
    clinical_validation: false,
    clinical_summary: false,
    contains_personal_records: false,
    contents: 'Aggregate software counts only. No identifiers, measurements, clinical findings, notes, citations, or treatment records are included.',
    provenance_rule: 'Only rows with explicit synthetic source markers are counted; unmarked rows are excluded.',
    counts: {
      synthetic_measurements: measurements.length,
      synthetic_baselines: baselines.length,
      synthetic_monitoring_cycles: monitoringRuns.length,
      synthetic_followup_plans: followupPlans.length,
      synthetic_prevention_entries: preventionEntries.length,
      synthetic_radiation_records: radiationRecords.length,
    },
    authority: {
      deterministic_engine_is_clinical_authority: true,
      diagnosis_or_treatment_generated_by_report: false,
      treatment_execution_enabled: false,
      public_space_weather_is_personal_dosimetry: false,
    },
  };
}
