import {
  RADLAB_QUANTITIES, buildRadLabProxyRequest, cacheRadLabSnapshot,
  normalizeRadLabResponse, parseRadLabCache, validateRadLabFilters,
} from './radlab.js';

const svgNS = 'http://www.w3.org/2000/svg';
const el = (tag, text = '') => { const node = document.createElement(tag); if (text) node.textContent = text; return node; };
const svgEl = (tag, attrs = {}) => { const node = document.createElementNS(svgNS, tag); for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value)); return node; };
const valid = value => typeof value === 'number' && Number.isFinite(value);

function csvCell(value) {
  const text = value == null ? '' : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function download(name, type, content) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = el('a', 'Download'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function matchesFilter(snapshot, filterId) {
  const normalized = snapshot?.filters;
  return normalized && normalized.startDate === filterId.startDate && normalized.endDate === filterId.endDate &&
    normalized.spacecraft === filterId.spacecraft;
}

function makeChart(records, quantity, instrumentId) {
  const selected = records.filter(row => (!instrumentId || row.instrument_id === instrumentId) && valid(row.values[quantity]?.value));
  const svg = svgEl('svg', { viewBox: '0 0 860 270', role: 'img', 'aria-label': `${RADLAB_QUANTITIES[quantity].label} observations returned by NASA RadLab` });
  svg.append(svgEl('rect', { x: 42, y: 18, width: 790, height: 205, rx: 8, fill: '#081827', stroke: '#29465c' }));
  for (let i = 0; i <= 4; i++) {
    const y = 32 + i * 45;
    svg.append(svgEl('line', { x1: 42, y1: y, x2: 832, y2: y, stroke: '#29445a', 'stroke-width': 1 }));
  }
  if (!selected.length) {
    const text = svgEl('text', { x: 437, y: 130, 'text-anchor': 'middle', fill: '#c6d6e1', 'font-size': 14 });
    text.textContent = 'No reported values for this quantity in the returned observations.';
    svg.append(text);
    return { svg, count: 0, low: null, high: null };
  }
  const values = selected.map(row => row.values[quantity].value);
  const low = Math.min(...values), high = Math.max(...values), span = high - low || Math.max(Math.abs(high), 1);
  const times = selected.map(row => Date.parse(row.observed_at_utc));
  const first = Math.min(...times), last = Math.max(...times), duration = last - first || 1;
  for (let index = 0; index < selected.length; index++) {
    const row = selected[index], value = row.values[quantity].value;
    const point = svgEl('circle', {
      cx: 48 + ((Date.parse(row.observed_at_utc) - first) / duration) * 778,
      cy: 212 - ((value - low) / span) * 174,
      r: selected.length > 1000 ? 2 : 3.4,
      fill: '#53dec9', stroke: '#e5fbf7', 'stroke-width': 0.7,
      'data-observation-id': `${row.instrument_id ?? 'unknown'}-${row.observed_at_utc}`,
    });
    const title = svgEl('title');
    title.textContent = `${row.observed_at_utc} · ${row.instrument_id ?? 'instrument not identified'} · ${value} ${RADLAB_QUANTITIES[quantity].unit}`;
    point.append(title); svg.append(point);
  }
  const minLabel = svgEl('text', { x: 44, y: 247, fill: '#b3c7d6', 'font-size': 11 }); minLabel.textContent = `${new Date(first).toISOString().slice(0, 16)} · UTC`;
  const maxLabel = svgEl('text', { x: 830, y: 247, 'text-anchor': 'end', fill: '#b3c7d6', 'font-size': 11 }); maxLabel.textContent = `${new Date(last).toISOString().slice(0, 16)} · UTC`;
  svg.append(minLabel, maxLabel);
  return { svg, count: selected.length, low, high };
}

function makeCoordinatePlot(records, instrumentId) {
  const selected = records.filter(row => (!instrumentId || row.instrument_id === instrumentId) && row.location);
  const svg = svgEl('svg', { viewBox: '0 0 720 320', role: 'img', 'aria-label': 'Historical RadLab ISS measurement coordinates on a latitude and longitude graticule' });
  svg.append(svgEl('rect', { x: 58, y: 18, width: 630, height: 264, rx: 7, fill: '#081827', stroke: '#29465c' }));
  for (let lat = -60; lat <= 60; lat += 30) {
    const y = 150 - lat * 1.25;
    svg.append(svgEl('line', { x1: 58, y1: y, x2: 688, y2: y, stroke: '#29445a' }));
    const label = svgEl('text', { x: 51, y: y + 4, 'text-anchor': 'end', fill: '#a9bdcb', 'font-size': 10 }); label.textContent = `${lat}°`;
    svg.append(label);
  }
  for (let lon = -180; lon <= 180; lon += 60) {
    const x = 58 + (lon + 180) / 360 * 630;
    svg.append(svgEl('line', { x1: x, y1: 18, x2: x, y2: 282, stroke: '#29445a' }));
    const label = svgEl('text', { x, y: 300, 'text-anchor': 'middle', fill: '#a9bdcb', 'font-size': 10 }); label.textContent = `${lon}°`;
    svg.append(label);
  }
  selected.forEach((row, index) => {
    const location = row.location;
    const x = 58 + (location.longitude_deg + 180) / 360 * 630;
    const y = 150 - location.latitude_deg * 1.25;
    const point = svgEl('circle', { cx: x, cy: y, r: selected.length > 1500 ? 1.6 : 2.6, fill: '#f2bd6b', 'data-observation-index': index });
    const title = svgEl('title'); title.textContent = `${row.observed_at_utc} · ${row.instrument_id ?? 'unknown instrument'} · ${location.latitude_deg.toFixed(4)}°, ${location.longitude_deg.toFixed(4)}°`;
    point.append(title); svg.append(point);
  });
  return { svg, count: selected.length };
}

export function mountRadLabExplorer(container, { fetcher = globalThis.fetch, onObservations = () => {}, onContext = () => {}, now = () => new Date() } = {}) {
  if (!container) throw Error('RadLab explorer container is unavailable.');
  const root = el('div'); root.className = 'radlab-explorer';
  const form = el('div'); form.className = 'radlab-filters';
  const spacecraft = document.createElement('select'); spacecraft.setAttribute('aria-label', 'RadLab spacecraft');
  spacecraft.append(new Option('ISS · available coordinate records', 'ISS'));
  const start = document.createElement('input'); start.type = 'date'; start.setAttribute('aria-label', 'Start date in UTC');
  const end = document.createElement('input'); end.type = 'date'; end.setAttribute('aria-label', 'End date in UTC');
  const today = now().toISOString().slice(0, 10); const yesterday = new Date(Date.parse(`${today}T00:00:00Z`) - 86400000).toISOString().slice(0, 10);
  start.value = yesterday; end.value = today;
  const instrument = document.createElement('select'); instrument.setAttribute('aria-label', 'Instrument ID filter'); instrument.append(new Option('All returned instruments', ''));
  const quantity = document.createElement('select'); quantity.setAttribute('aria-label', 'Radiation measurement');
  for (const [key, value] of Object.entries(RADLAB_QUANTITIES)) quantity.append(new Option(`${value.label} · ${value.unit}`, key));
  const load = el('button', 'Load historical observations'); load.type = 'button'; load.className = 'primary-action';
  const example = el('button', 'Load verified archive example'); example.type = 'button';
  for (const [label, field] of [['Spacecraft', spacecraft], ['Start (UTC)', start], ['End (UTC)', end], ['Instrument', instrument], ['Quantity', quantity]]) {
    const wrapper = el('label', label); wrapper.append(field); form.append(wrapper);
  }
  form.append(load, example);
  const status = el('p', 'Choose a date range and load NASA RadLab public observations.'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const provenance = el('p', 'Public archived instrument observations · not live telemetry · not individual astronaut dosimetry. Missing values remain missing. NASA release notes identify some curated instrument data as preliminary; cadence is dataset-specific.'); provenance.className = 'radlab-provenance';
  const stats = el('div'); stats.className = 'radlab-stats';
  const chartHeading = el('h3', 'Returned observations · scatter plot');
  const chartMeta = el('p', 'Each point is an actual returned observation. Missing periods are not interpolated.');
  const chart = el('div'); chart.className = 'radlab-chart';
  const geoHeading = el('h3', 'ISS geospatial observations');
  const geoMeta = el('p', 'Latitude and longitude are shown only when supplied by RadLab for that timestamp. The plot is not a radiation heatmap.');
  const geo = el('div'); geo.className = 'radlab-map';
  const replay = el('section'); replay.className = 'radlab-replay';
  const replayLabel = el('label', 'Historical record selector');
  const slider = document.createElement('input'); slider.type = 'range'; slider.min = '0'; slider.max = '0'; slider.value = '0'; slider.setAttribute('aria-label', 'Select an archived RadLab observation');
  replayLabel.append(slider); const readout = el('p', 'No archived measurement selected.'); readout.setAttribute('aria-live', 'polite');
  replay.append(replayLabel, readout);
  const actions = el('div'); actions.className = 'radlab-actions';
  const exportJson = el('button', 'Export JSON'); exportJson.type = 'button'; exportJson.disabled = true;
  const exportCsv = el('button', 'Export CSV'); exportCsv.type = 'button'; exportCsv.disabled = true;
  const sourceLink = el('a', 'NASA RadLab API documentation'); sourceLink.href = 'https://visualization.osdr.nasa.gov/radlab/gui/data-api/'; sourceLink.target = '_blank'; sourceLink.rel = 'noopener noreferrer';
  const releaseLink = el('a', 'NASA RadLab release history'); releaseLink.href = 'https://visualization.osdr.nasa.gov/radlab/gui/knowledgebase/Release_history'; releaseLink.target = '_blank'; releaseLink.rel = 'noopener noreferrer';
  actions.append(exportJson, exportCsv, sourceLink, releaseLink);
  const tableWrap = el('div'); tableWrap.className = 'radlab-table-wrap';
  root.append(form, status, provenance, stats, chartHeading, chartMeta, chart, geoHeading, geoMeta, geo, replay, actions, tableWrap);
  container.replaceChildren(root);

  let snapshot = null, filteredRows = [], displayedRows = [], selectedIndex = 0, currentAbort = null;

  function draw() {
    if (!snapshot) return;
    displayedRows = filteredRows.filter(row => !instrument.value || row.instrument_id === instrument.value);
    const filtered = displayedRows;
    const selectedQuantity = quantity.value;
    const series = makeChart(filtered, selectedQuantity, instrument.value);
    chart.replaceChildren(series.svg);
    const geoPlot = makeCoordinatePlot(filtered, instrument.value);
    geo.replaceChildren(geoPlot.svg);
    stats.replaceChildren();
    const latest = snapshot.retrieved_at_utc ? new Date(snapshot.retrieved_at_utc).toISOString() : 'unknown';
    const valuesCount = filtered.filter(row => valid(row.values[selectedQuantity]?.value)).length;
    const missingCount = filtered.filter(row => row.values[selectedQuantity]?.value === null || row.values[selectedQuantity] === undefined).length;
    for (const text of [
      `${filtered.length.toLocaleString('en-US')} returned records · ${snapshot.cache_state ?? snapshot.retrieval_state ?? 'HISTORICAL QUERY'}`,
      `${valuesCount.toLocaleString('en-US')} ${RADLAB_QUANTITIES[selectedQuantity].label.toLowerCase()} values · ${missingCount.toLocaleString('en-US')} missing`,
      `${geoPlot.count.toLocaleString('en-US')} records with valid coordinates`,
      `Retrieved ${latest} UTC${snapshot.cache_state ? ` · ${snapshot.cache_state}` : ''}`,
    ]) stats.append(el('span', text));
    chartMeta.textContent = series.count
      ? `${series.count.toLocaleString('en-US')} actual value(s) · ${RADLAB_QUANTITIES[selectedQuantity].unit} · minimum ${series.low} · maximum ${series.high} · no interpolation.`
      : `No valid ${RADLAB_QUANTITIES[selectedQuantity].label.toLowerCase()} value in this filtered result. This is unknown, not zero.`;
    geoMeta.textContent = geoPlot.count
      ? `${geoPlot.count.toLocaleString('en-US')} timestamped coordinate(s) from ISS records. Points do not imply personal astronaut exposure and are not interpolated into a heatmap.`
      : 'No valid coordinates are present for this filter. Missing coordinates are not inferred.';
    filteredRows = filtered;
    const sortedForReplay = displayedRows;
    slider.max = String(Math.max(0, sortedForReplay.length - 1));
    slider.disabled = sortedForReplay.length === 0;
    selectedIndex = Math.min(selectedIndex, Math.max(0, sortedForReplay.length - 1));
    slider.value = String(selectedIndex);
    updateReplay();
    const table = el('table');
    const head = el('thead'), header = el('tr');
    for (const name of ['Observed at (UTC)', 'Instrument ID', 'Module', ...Object.keys(RADLAB_QUANTITIES).map(key => `${key} · ${RADLAB_QUANTITIES[key].unit}`)]) header.append(el('th', name));
    head.append(header); table.append(head);
    const body = el('tbody');
    for (const row of filtered.slice(0, 100)) {
      const tr = el('tr'); tr.append(el('td', row.observed_at_utc), el('td', row.instrument_id ?? 'Unknown'), el('td', row.module ?? 'Unknown'));
      for (const key of Object.keys(RADLAB_QUANTITIES)) tr.append(el('td', row.values[key]?.value == null ? 'Not reported' : String(row.values[key].value)));
      body.append(tr);
    }
    table.append(body); tableWrap.replaceChildren(table);
    exportJson.disabled = false; exportCsv.disabled = false;
    onObservations(snapshot.observations, sortedForReplay[selectedIndex] ?? null, snapshot);
  }

  function updateReplay() {
    if (!snapshot) return;
    const row = displayedRows[Number(slider.value)] ?? null;
    selectedIndex = Number(slider.value);
    if (!row) {
      readout.textContent = 'No archived measurement selected.';
      onObservations(displayedRows, null, snapshot);
      onContext(null, snapshot);
      return;
    }
    const coordinate = row.location ? `${row.location.latitude_deg.toFixed(4)}°, ${row.location.longitude_deg.toFixed(4)}°${row.location.altitude_km === null ? '' : ` · ${row.location.altitude_km} km altitude`}` : 'No coordinate reported';
    const val = row.values[quantity.value]?.value;
    readout.textContent = `${row.observed_at_utc} UTC · ${row.instrument_id ?? 'instrument unknown'} · ${val === null || val === undefined ? 'selected quantity not reported' : `${val} ${RADLAB_QUANTITIES[quantity.value].unit}`} · ${coordinate}. Historical environmental context only.`;
    onObservations(displayedRows, row, snapshot);
    onContext(row, snapshot);
  }

  function applySnapshot(value, { cached = false } = {}) {
    snapshot = value;
    if (cached) snapshot = { ...value, cache_state: value.cache_state ?? 'CACHED_HISTORICAL' };
    const ids = [...new Set(snapshot.observations.map(row => row.instrument_id).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    const previous = instrument.value;
    instrument.replaceChildren(new Option('All returned instruments', ''));
    for (const id of ids) instrument.append(new Option(id, id));
    if (ids.includes(previous)) instrument.value = previous;
    filteredRows = snapshot.observations;
    selectedIndex = 0;
    status.textContent = cached
      ? `NASA request unavailable. Showing ${snapshot.cache_state === 'STALE_CACHED_HISTORICAL' ? 'stale ' : ''}cached historical NASA RadLab observations retrieved ${snapshot.retrieved_at_utc} UTC.`
      : `NASA RadLab returned ${snapshot.observations.length.toLocaleString('en-US')} historical archive records · query retrieved ${snapshot.retrieved_at_utc} UTC · not live telemetry.`;
    draw();
  }

  async function query() {
    currentAbort?.abort(); currentAbort = new AbortController();
    load.disabled = true; status.textContent = 'Querying NASA RadLab through the same-origin proxy…';
    try {
      const filters = validateRadLabFilters({ spacecraft: spacecraft.value, startDate: start.value, endDate: end.value, quantities: Object.keys(RADLAB_QUANTITIES) });
      const response = await fetcher(buildRadLabProxyRequest(filters), { method: 'GET', cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer', redirect: 'error', signal: currentAbort.signal, headers: { Accept: 'application/json' } });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw Error(error.error || `RadLab proxy returned HTTP ${response.status}.`);
      }
      const payload = await response.json();
      const retrievedAt = response.headers.get('X-ASTHRAL-RadLab-Payload') === 'RAW' || payload.provider !== 'NASA_OSDR_RADLAB'
        ? new Date().toISOString() : payload.retrieved_at_utc;
      const normalized = payload.provider === 'NASA_OSDR_RADLAB'
        ? payload
        : normalizeRadLabResponse(payload, { requested: filters, retrievedAt });
      cacheRadLabSnapshot(normalized);
      applySnapshot(normalized);
    } catch (error) {
      if (error.name === 'AbortError') return;
      const cached = parseRadLabCache();
      const current = { spacecraft: spacecraft.value, startDate: start.value, endDate: end.value };
      if (cached && matchesFilter(cached, current)) applySnapshot(cached, { cached: true });
      else status(`${error.message} No matching cached query is available; no substitute or synthetic radiation data were created.`);
    } finally { load.disabled = false; }
  }

  load.addEventListener('click', () => { void query(); });
  example.addEventListener('click', () => { start.value = '2023-01-01'; end.value = '2023-01-01'; instrument.value = ''; void query(); });
  quantity.addEventListener('change', draw);
  instrument.addEventListener('change', () => { selectedIndex = 0; draw(); });
  slider.addEventListener('input', updateReplay);
  exportJson.addEventListener('click', () => { if (snapshot) download('asthral-radlab-historical.json', 'application/json', JSON.stringify(snapshot, null, 2)); });
  exportCsv.addEventListener('click', () => {
    if (!snapshot) return;
    const columns = ['source', 'classification', 'observed_at_utc', 'retrieved_at_utc', 'spacecraft', 'instrument_id', 'instrument_family', 'module', 'latitude_deg', 'longitude_deg', 'altitude_km', ...Object.keys(RADLAB_QUANTITIES).flatMap(key => [`${key}_value`, `${key}_unit`])];
    const lines = [columns.map(csvCell).join(',')];
    for (const row of filteredRows.filter(item => !instrument.value || item.instrument_id === instrument.value)) {
      const values = [row.source, row.classification, row.observed_at_utc, row.retrieved_at_utc, row.spacecraft, row.instrument_id, row.instrument_family, row.module, row.location?.latitude_deg, row.location?.longitude_deg, row.location?.altitude_km];
      for (const key of Object.keys(RADLAB_QUANTITIES)) values.push(row.values[key]?.value, row.values[key]?.unit);
      lines.push(values.map(csvCell).join(','));
    }
    download('asthral-radlab-historical.csv', 'text/csv;charset=utf-8', lines.join('\r\n'));
  });

  return {
    load: query,
    destroy() { currentAbort?.abort(); container.replaceChildren(); onObservations([], null, null); onContext(null, null); },
    getSnapshot: () => snapshot,
  };
}
