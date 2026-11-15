import {
  ORBIT_CACHE_REFRESH_MS, ORBIT_STALE_NOTICE_MS, CELESTRAK_ISS_URL,
  buildOrbitTrack, cacheOrbitSnapshot, createOrbitModel, earthFixedToScene,
  fetchIssOmm, geodeticToScene, makeSyntheticOmm, nearestListedCityApproach,
  propagateOrbit, readOrbitSnapshot, validateIssOmm,
} from './orbital-engine.js';
import { cachedDonkiSnapshot } from './space-weather.js';

const TEXTURE_URL = './vendor/orbit/earth-blue-marble-july-2004.webp';
const TEXTURE_CREDIT_URL = 'https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/';

function node(tag, attrs = {}, text = '') {
  const result = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) result.setAttribute(key, value);
  if (text !== '') result.textContent = text;
  return result;
}

function validRadLabLocation(row) {
  const location = row?.location;
  return row?.source === 'NASA_OSDR_RADLAB' && row?.classification === 'HISTORICAL' &&
    Number.isFinite(location?.latitude_deg) && location.latitude_deg >= -90 && location.latitude_deg <= 90 &&
    Number.isFinite(location?.longitude_deg) && location.longitude_deg >= -180 && location.longitude_deg <= 180;
}

function formatDegrees(value, digits = 2) { return `${Number(value).toFixed(digits)}°`; }
function formatUtc(value) { return new Date(value).toISOString().replace('.000Z', 'Z'); }
function formatDuration(seconds) {
  const minutes = Math.max(0, Math.round(seconds / 60));
  return `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, '0')} min`;
}

export async function mountOrbitalView(container, { onState = () => {}, scenario = () => 'nominal' } = {}) {
  if (!container) throw new Error('Orbital mission-control container is unavailable.');
  const root = node('section', { class: 'orbit-console', 'aria-label': 'Orbital mission control' });
  const mast = node('div', { class: 'orbit-mast' });
  const modePanel = node('div', { class: 'orbit-mode-panel' });
  const modeLabel = node('label', {}, 'Tracking mode');
  const modeSelect = node('select', { 'aria-label': 'Spacecraft tracking mode' });
  modeSelect.append(
    node('option', { value: 'ISS_TRACKED' }, 'ISS · orbital estimate'),
    node('option', { value: 'SIMULATED' }, 'ASTHRAL spacecraft · simulated'),
  );
  modeLabel.append(modeSelect);
  const sourceBadge = node('span', { class: 'orbit-source-badge', role: 'status' }, 'ORBIT DATA NOT LOADED');
  const refreshButton = node('button', { type: 'button' }, 'Refresh ISS elements');
  modePanel.append(modeLabel, sourceBadge, refreshButton);
  const missionTag = node('span', { class: 'orbit-mission-tag' }, 'SYNTHETIC MISSION · NO CREW TELEMETRY');
  mast.append(modePanel, missionTag);

  const frame = node('div', { class: 'orbit-layout' });
  const visual = node('section', { class: 'orbit-visual', 'aria-label': 'Interactive three-dimensional Earth and propagated orbital track' });
  const stageHeader = node('div', { class: 'orbit-stage-header' });
  const stageTitle = node('div');
  stageTitle.append(node('p', { class: 'orbit-kicker' }, 'LOW EARTH ORBIT'), node('h2', {}, 'Earth · orbital context'));
  const cameraTools = node('div', { class: 'orbit-camera-tools', 'aria-label': 'Globe camera controls' });
  const follow = node('button', { type: 'button', 'aria-pressed': 'false' }, 'Follow spacecraft');
  const reset = node('button', { type: 'button' }, 'Reset view');
  const powerNote = node('span', { class: 'orbit-power-note' }, 'Render profile follows Mission Control settings');
  cameraTools.append(follow, reset, powerNote);
  stageHeader.append(stageTitle, cameraTools);

  const stage = node('div', { class: 'orbit-stage' });
  const webglCanvas = node('canvas', { class: 'orbit-globe-canvas', 'aria-label': 'Interactive three-dimensional Earth with orbital track; drag to rotate, scroll to zoom, click the Earth to inspect coordinates' });
  const mapCanvas = node('canvas', { class: 'orbit-map-canvas', hidden: '', 'aria-label': 'Two-dimensional equirectangular Earth ground-track fallback' });
  const stageNotice = node('div', { class: 'orbit-stage-notice', role: 'status', 'aria-live': 'polite' }, 'Loading local globe resources…');
  const markerLegend = node('div', { class: 'orbit-marker-legend' });
  const radLabLegend = node('span', { class: 'orbit-legend-radlab' }, 'HISTORICAL RADLAB · 0');
  radLabLegend.setAttribute('aria-label', 'Zero historical RadLab records with mapped ISS coordinates');
  markerLegend.append(node('span', { class: 'orbit-legend-satellite' }, 'SPACECRAFT'), node('span', { class: 'orbit-legend-groundtrack' }, 'GROUND TRACK'), node('span', { class: 'orbit-legend-sun' }, 'SUN VECTOR'), radLabLegend);
  stage.append(webglCanvas, mapCanvas, stageNotice, markerLegend);

  const timeline = node('div', { class: 'orbit-timeline' });
  const timelineButtons = node('div', { class: 'orbit-timeline-controls' });
  const playbackButton = node('button', { type: 'button' }, 'Play timeline');
  const speed = node('select', { 'aria-label': 'Orbital timeline playback speed' });
  for (const [value, label] of [['1', '1×'], ['10', '10×'], ['60', '60×']]) speed.append(node('option', { value }, label));
  const nowButton = node('button', { type: 'button' }, 'Return to current UTC');
  timelineButtons.append(playbackButton, speed, nowButton);
  const timeSliderLabel = node('label', { class: 'orbit-time-slider' }, 'Mission timeline · ±90 minutes');
  const timeSlider = node('input', { type: 'range', min: '-90', max: '90', step: '1', value: '0', 'aria-label': 'Orbit calculation time offset in minutes' });
  timeSliderLabel.append(timeSlider);
  const timeReadout = node('output', { class: 'orbit-time-readout', 'aria-live': 'polite' }, 'UTC position time pending');
  timeline.append(timelineButtons, timeSliderLabel, timeReadout);
  visual.append(stageHeader, stage, timeline);

  const telemetry = node('aside', { class: 'orbit-telemetry', 'aria-label': 'Orbital position and source details' });
  const positionCard = node('section', { class: 'orbit-position-card' });
  const estimateHeading = node('p', { class: 'orbit-kicker' }, 'ESTIMATED ISS POSITION (ORBITAL PROPAGATION)');
  const positionTitle = node('h2', {}, 'Waiting for orbital elements');
  const coordinateGrid = node('dl', { class: 'orbit-coordinate-grid' });
  const coord = (id, label, value = '—') => {
    const wrap = node('div'); wrap.append(node('dt', {}, label), node('dd', { id }, value)); coordinateGrid.append(wrap);
  };
  coord('orbit-lat', 'SUBSATELLITE LATITUDE');
  coord('orbit-lon', 'SUBSATELLITE LONGITUDE');
  coord('orbit-alt', 'ORBITAL ALTITUDE');
  coord('orbit-utc', 'CALCULATION TIME · UTC');
  const illumination = node('div', { class: 'orbit-illumination' });
  const sourceInfo = node('div', { class: 'orbit-source-info' });
  const freshness = node('p', { class: 'orbit-freshness', role: 'status' }, 'Orbital source has not been queried.');
  const sourceLine = node('p', {}, 'Source: CelesTrak GP/OMM · NORAD catalog 25544. Position is an SGP4-propagated estimate, not onboard GPS or live telemetry.');
  const epochLine = node('p', {}, 'Element epoch: not available.');
  const fetchedLine = node('p', {}, 'Retrieved at: not available.');
  const viewPoint = node('p', { class: 'orbit-selected-point', 'aria-live': 'polite' }, 'Click the globe to inspect a surface coordinate.');
  sourceInfo.append(freshness, sourceLine, epochLine, fetchedLine, viewPoint);
  positionCard.append(estimateHeading, positionTitle, coordinateGrid, illumination, sourceInfo);

  const derivedCard = node('section', { class: 'orbit-derived-card' });
  derivedCard.append(node('h3', {}, 'Trajectory context'));
  const cityApproach = node('p', {}, 'Nearest listed city approach: calculating from propagated orbit…');
  const contactUnavailable = node('p', { class: 'orbit-unavailable' }, 'Ground-station contact data unavailable. No station catalog, antenna geometry, or contact schedule is integrated.');
  const illuminationNote = node('p', {}, 'Sunlight/eclipsed state is computed from orbital geometry. It is not an ionizing-radiation measurement, personal dose, or EVA exposure estimate.');
  derivedCard.append(cityApproach, contactUnavailable, illuminationNote);
  const weatherCard = node('section', { class: 'orbit-weather-card' });
  weatherCard.append(node('h3', {}, 'Space-weather context'));
  const weatherRows = node('div', { class: 'orbit-weather-rows' });
  weatherCard.append(weatherRows);
  telemetry.append(positionCard, derivedCard, weatherCard);
  frame.append(visual, telemetry);

  const footer = node('div', { class: 'orbit-footnotes' });
  const textureCredit = node('a', {}, 'Earth texture: NASA Earth Observatory Blue Marble · July composite · 2004');
  textureCredit.href = TEXTURE_CREDIT_URL; textureCredit.target = '_blank'; textureCredit.rel = 'noopener noreferrer';
  footer.append(textureCredit, node('p', {}, 'Displayed surface imagery is a static historical composite. The globe geometry and lighting are rendered locally. Coordinates and paths are derived from the selected element set and the displayed UTC time. No communications availability is inferred.'));
  root.append(mast, frame, footer);
  container.replaceChildren(root);

  let THREE = null, renderer = null, scene = null, camera = null, earth = null, sunLight = null, atmosphere = null;
  let orbitGroup = null, spacecraft = null, raycaster = null, pointer = null, texture = null;
  let resizeObserver = null, animationId = 0, renderTimer = 0, clockTimer = null, lastDraw = 0, lastClock = performance.now(), lastPositionUpdate = 0, renderTotal = 0;
  const renderedAt = [];
  let orbit = null, orbitModelSource = null, displayedState = null, playback = false, followEnabled = false, orbitRequest = null;
  let followNow = true, timelineOffsetMinutes = 0, simulatedTime = Date.now(), isDestroyed = false, viewVisible = true;
  let missionTimeOverride = null, scenarioClockLocked = false;
  let powerMode = 'FULL', radiationObservations = [], selectedRadiationObservation = null;
  let cameraAzimuth = 0.55, cameraElevation = 0.26, cameraDistance = 3.65;
  let drag = null;
  const aborter = new AbortController();

  function updateWeather() {
    weatherRows.replaceChildren();
    const snap = cachedDonkiSnapshot();
    if (snap.state === 'NO_CACHE') {
      weatherRows.append(node('p', {}, 'No cached NASA CCMC DONKI event data is saved on this device. Current conditions are unknown.'));
      return;
    }
    const label = snap.state === 'STALE' ? 'STALE CACHED PUBLIC EVENTS' : 'CACHED PUBLIC EVENTS';
    weatherRows.append(node('p', { class: 'orbit-freshness' }, `${label} · synchronized ${snap.fetched_at} · not a personal dosimeter or crew-exposure alert.`));
    const rows = snap.events.slice(0, 4);
    if (!rows.length) weatherRows.append(node('p', {}, 'No events were recorded in the cached query. This does not establish benign space-weather conditions.'));
    for (const event of rows) {
      const article = node('article');
      article.append(node('strong', {}, `${event.type ?? 'NASA DONKI'} · ${event.id ?? 'event'}`), node('p', {}, `${event.description ?? event.type ?? 'NASA CCMC DONKI event'} · ${event.time ?? event.time_utc ?? 'time not supplied'} UTC`));
      const link = event.url;
      if (typeof link === 'string' && link.startsWith('https://ccmc.gsfc.nasa.gov/DONKI/')) {
        const a = node('a', {}, 'Open source event'); a.href = link; a.target = '_blank'; a.rel = 'noopener noreferrer'; article.append(a);
      }
      weatherRows.append(article);
    }
  }

  function setSourceState(text, tone = '') {
    sourceBadge.textContent = text;
    sourceBadge.dataset.tone = tone;
  }

  function setUnavailable(message) {
    orbit = null; orbitModelSource = null; displayedState = null;
    setSourceState(modeSelect.value === 'SIMULATED' ? 'SIMULATION UNAVAILABLE' : 'ISS ELEMENTS UNAVAILABLE', 'warning');
    positionTitle.textContent = modeSelect.value === 'SIMULATED' ? 'Synthetic orbit unavailable' : 'ISS estimate unavailable';
    stageNotice.textContent = message;
    stageNotice.hidden = false;
    estimateHeading.textContent = modeSelect.value === 'SIMULATED' ? 'ASTHRAL SIMULATED SPACECRAFT' : 'ESTIMATED ISS POSITION (ORBITAL PROPAGATION)';
    cityApproach.textContent = 'Nearest listed city approach unavailable because no valid orbit is loaded.';
    renderEmptyCoordinates();
    onState(null);
  }

  function renderEmptyCoordinates() {
    for (const id of ['orbit-lat', 'orbit-lon', 'orbit-alt', 'orbit-utc']) document.getElementById(id)?.replaceChildren(document.createTextNode('—'));
    illumination.replaceChildren(node('span', { class: 'orbit-sun-badge' }, 'ILLUMINATION UNKNOWN'), node('span', {}, 'No valid orbit state to compute illumination.'));
  }

  function installOrbitModel(raw, { mode, fetchedAt = Date.now(), source } = {}) {
    try {
      orbit = createOrbitModel(raw, { mode, fetchedAt, source });
      orbitModelSource = source ?? orbit.source;
      simulatedTime = missionTimeOverride ?? Date.now();
      timelineOffsetMinutes = 0;
      followNow = missionTimeOverride === null;
      setSourceState(mode === 'SIMULATED' ? 'SYNTHETIC ORBIT' : orbit.freshness === 'STALE' ? 'STALE ORBIT ELEMENTS' : 'CELESTRAK ELEMENTS', mode === 'SIMULATED' ? 'simulated' : orbit.freshness === 'STALE' ? 'warning' : '');
      const ageHours = Math.max(0, (Date.now() - orbit.epochMs) / 3600000);
      freshness.textContent = mode === 'SIMULATED'
        ? 'SIMULATED · synthetic orbital elements; no operational spacecraft is represented.'
        : `Estimated from GP mean elements · element epoch age ${ageHours < 1 ? `${Math.round(ageHours * 60)} min` : `${ageHours.toFixed(1)} h`}${orbit.freshness === 'STALE' ? ' · STALE AGE WARNING' : ''}.`;
      sourceLine.textContent = mode === 'SIMULATED'
        ? 'Source: ASTHRAL synthetic orbital elements · deterministic demonstration only; no real spacecraft is represented.'
        : 'Source: CelesTrak GP/OMM · NORAD catalog 25544 · propagated with SGP4. This is not onboard GPS or direct telemetry.';
      epochLine.textContent = `Element epoch (UTC): ${formatUtc(orbit.epochMs)} · mean elements and propagation are model-dependent.`;
      fetchedLine.textContent = mode === 'SIMULATED'
        ? 'Retrieved at: not applicable · synthetic elements generated locally.'
        : `Retrieved at (UTC): ${new Date(orbit.fetchedAtMs).toISOString()} · cache status: ${new Date().getTime() - orbit.fetchedAtMs > ORBIT_CACHE_REFRESH_MS ? 'refresh due' : 'within 6-hour refresh interval'}.`;
      estimateHeading.textContent = mode === 'SIMULATED' ? 'ASTHRAL SIMULATED SPACECRAFT' : 'ESTIMATED ISS POSITION (ORBITAL PROPAGATION)';
      positionTitle.textContent = mode === 'SIMULATED' ? 'ASTHRAL crew vehicle · SIMULATED' : 'International Space Station · estimated';
      stageNotice.hidden = false;
      stageNotice.textContent = mode === 'SIMULATED'
        ? `SIMULATED MISSION · ${scenario().replaceAll('_', ' ').toUpperCase()} · this marker is not the user's device location.`
        : 'SGP4 estimate from public mean elements · no direct spacecraft telemetry.';
      const approach = nearestListedCityApproach(orbit, simulatedTime);
      cityApproach.textContent = approach
        ? `Closest approach to listed reference cities within the next ${formatDuration(orbit.periodSeconds * 2)} (30 s samples): ${approach.city} · ${Math.round(approach.distanceKm).toLocaleString('en-US')} km surface distance at ${approach.timeUtc} UTC. This is a sampled geographic comparison, not a ground-station contact prediction.`
        : 'No listed-city approach could be computed.';
      updateCurrentPosition(true);
      renderOrbitGraphics();
    } catch (error) {
      setUnavailable(error.message);
    }
  }

  async function loadTracked({ force = false } = {}) {
    orbitRequest?.abort();
    const request = new AbortController(); orbitRequest = request;
    refreshButton.disabled = true;
    if (!force) {
      const cached = readOrbitSnapshot();
      if (cached) {
        try {
          const candidate = validateIssOmm(cached.data, { fetchedAt: Date.parse(cached.fetched_at) });
          const cacheAge = Date.now() - Date.parse(cached.fetched_at);
          if (candidate.freshness !== 'UNAVAILABLE_STALE' && cacheAge < ORBIT_CACHE_REFRESH_MS) {
            installOrbitModel(cached.data, { mode: 'ISS_TRACKED', fetchedAt: Date.parse(cached.fetched_at), source: cached.source });
            refreshButton.disabled = false;
            if (orbitRequest === request) orbitRequest = null;
            return;
          }
        } catch { /* Corrupt, wrong-object, or expired cache is ignored. */ }
      }
    }
    try {
      const snapshot = await fetchIssOmm({ signal: request.signal });
      if (request.signal.aborted || modeSelect.value !== 'ISS_TRACKED' || isDestroyed) return;
      cacheOrbitSnapshot(snapshot);
      installOrbitModel(snapshot.data, { mode: 'ISS_TRACKED', fetchedAt: Date.parse(snapshot.fetched_at), source: snapshot.source });
      if (orbit) setSourceState('CELESTRAK · FETCHED', 'fresh');
    } catch (error) {
      if (request.signal.aborted || modeSelect.value !== 'ISS_TRACKED' || isDestroyed) return;
      const cached = readOrbitSnapshot();
      if (cached) {
        try {
          const candidate = validateIssOmm(cached.data, { fetchedAt: Date.parse(cached.fetched_at) });
          if (candidate.freshness !== 'UNAVAILABLE_STALE') {
            installOrbitModel(cached.data, { mode: 'ISS_TRACKED', fetchedAt: Date.parse(cached.fetched_at), source: cached.source });
            setSourceState('OFFLINE · CACHED ELEMENTS', 'warning');
            freshness.textContent = `ONLINE REFRESH UNAVAILABLE: ${error.message} Cached GP elements fetched at ${cached.fetched_at} · ${candidate.freshness === 'STALE' ? 'STALE ELEMENT EPOCH; estimate retained with warning.' : 'cached estimate only.'}`;
            refreshButton.disabled = false;
            return;
          }
        } catch { /* Invalid cache cannot support tracked mode. */ }
      }
      setUnavailable(`ISS tracking is unavailable: ${error.message} Select the separate synthetic mode to explore the offline mission demonstration.`);
    } finally { if (orbitRequest === request) orbitRequest = null; refreshButton.disabled = false; }
  }

  function positionAt(timestamp) {
    if (!orbit) return null;
    try { return propagateOrbit(orbit, timestamp); }
    catch (error) { setUnavailable(error.message); return null; }
  }

  function updateCurrentPosition(force = false) {
    if (!orbit) return;
    const now = Date.now();
    if (missionTimeOverride !== null && !playback) simulatedTime = missionTimeOverride;
    else if (followNow && !playback) simulatedTime = now;
    else if (!followNow && !playback) simulatedTime = now + timelineOffsetMinutes * 60000;
    const state = positionAt(simulatedTime);
    if (!state) return;
    displayedState = state;
    timeReadout.textContent = `${state.timestampUtc} · UTC ${playback ? '· timeline playback' : missionTimeOverride !== null ? '· synchronized EVA scenario time' : followNow ? '· current estimate' : '· selected offset'}`;
    document.getElementById('orbit-lat').textContent = formatDegrees(state.latitudeDeg);
    document.getElementById('orbit-lon').textContent = formatDegrees(state.longitudeDeg);
    document.getElementById('orbit-alt').textContent = `${state.altitudeKm.toFixed(1)} km`;
    document.getElementById('orbit-utc').textContent = state.timestampUtc;
    const illuminationLabel = state.sunlight === 'SUNLIT' ? 'SUNLIT' : state.sunlight === 'ECLIPSED' ? 'EARTH UMBRA' : 'PENUMBRA';
    illumination.replaceChildren(node('span', { class: `orbit-sun-badge ${state.sunlight.toLowerCase()}` }, illuminationLabel), node('span', {}, `Earth shadow obscures ${(state.shadowFraction * 100).toFixed(0)}% of the solar disc at the propagated spacecraft position.`));
    if (modeSelect.value === 'SIMULATED') {
      positionTitle.textContent = 'YOU ARE HERE — SPACECRAFT · SIMULATED';
      freshness.textContent = `SIMULATED orbital estimate · ${scenario().replaceAll('_', ' ').toUpperCase()} · not the user's physical location or device telemetry.`;
      stageNotice.textContent = `YOU ARE HERE — SPACECRAFT · SIMULATED · ${scenario().replaceAll('_', ' ').toUpperCase()} · no real spacecraft or crew telemetry is represented.`;
    }
    onState({ ...state, mode: modeSelect.value, source: orbitModelSource, elementEpochUtc: orbit.omm.EPOCH, scenario: scenario(), freshness: orbit.freshness });
    if (force) renderOrbitGraphics();
  }

  function renderOrbitGraphics() {
    if (!orbit || !THREE) { drawFallback(); return; }
    if (orbitGroup) {
      for (const child of [...orbitGroup.children]) {
        orbitGroup.remove(child);
        child.geometry?.dispose?.();
        if (Array.isArray(child.material)) child.material.forEach(material => material.dispose?.());
        else child.material?.dispose?.();
      }
    } else {
      orbitGroup = new THREE.Group(); scene.add(orbitGroup);
    }
    const track = buildOrbitTrack(orbit, simulatedTime);
    const addLine = (states, color, opacity, surface = false) => {
      const points = states.map(item => {
        const point = surface ? geodeticToScene(item.latitudeDeg, item.longitudeDeg, 1.006) : earthFixedToScene(item.ecefKm);
        return new THREE.Vector3(point.x, point.y, point.z);
      });
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false });
      orbitGroup.add(new THREE.Line(geometry, material));
    };
    addLine(track.past, 0x69aeb7, 0.55);
    addLine(track.future, 0x64e4d0, 0.96);
    addLine(track.past, 0x4d8992, 0.62, true);
    const current = positionAt(simulatedTime);
    if (current) {
      const point = earthFixedToScene(current.ecefKm);
      const marker = new THREE.Group();
      marker.position.set(point.x, point.y, point.z);
      const direction = new THREE.Vector3(point.x, point.y, point.z).normalize();
      const body = new THREE.Mesh(new THREE.OctahedronGeometry(0.025, 0), new THREE.MeshBasicMaterial({ color: 0xf8fbff }));
      body.scale.set(0.75, 1.5, 0.75);
      marker.add(body);
      const panelMaterial = new THREE.MeshBasicMaterial({ color: 0x54d5e5, side: THREE.DoubleSide });
      for (const sign of [-1, 1]) {
        const panel = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.011, 0.042), panelMaterial);
        panel.position.set(sign * 0.067, 0, 0);
        marker.add(panel);
      }
      marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
      const halo = new THREE.Mesh(new THREE.SphereGeometry(0.046, 10, 8), new THREE.MeshBasicMaterial({ color: 0x53e0d0, transparent: true, opacity: 0.22 }));
      marker.add(halo);
      spacecraft = marker;
      orbitGroup.add(marker);
    }
    const locatedRadiation = radiationObservations.filter(validRadLabLocation);
    if (locatedRadiation.length) {
      const geometry = new THREE.SphereGeometry(0.011, 6, 4);
      const material = new THREE.MeshBasicMaterial({ color: 0x53dec9, depthWrite: false });
      const markers = new THREE.InstancedMesh(geometry, material, locatedRadiation.length);
      const dummy = new THREE.Object3D(), normalColor = new THREE.Color(0x53dec9), selectedColor = new THREE.Color(0xffc26e);
      locatedRadiation.forEach((row, index) => {
        const point = geodeticToScene(row.location.latitude_deg, row.location.longitude_deg, 1.012);
        dummy.position.set(point.x, point.y, point.z); dummy.scale.setScalar(1); dummy.updateMatrix();
        markers.setMatrixAt(index, dummy.matrix);
        const selected = selectedRadiationObservation &&
          selectedRadiationObservation.instrument_id === row.instrument_id &&
          selectedRadiationObservation.observed_at_utc === row.observed_at_utc;
        markers.setColorAt(index, selected ? selectedColor : normalColor);
      });
      markers.instanceMatrix.needsUpdate = true;
      if (markers.instanceColor) markers.instanceColor.needsUpdate = true;
      orbitGroup.add(markers);
    }
    stageNotice.hidden = false;
    if (modeSelect.value === 'ISS_TRACKED') stageNotice.textContent = 'Estimated spacecraft position from propagated mean elements · track is computed at the displayed UTC timeline.';
    if (modeSelect.value === 'SIMULATED') stageNotice.textContent = `YOU ARE HERE — SPACECRAFT · SIMULATED · ${scenario().replaceAll('_', ' ').toUpperCase()}. This marker does not show the user's physical or device location.`;
    drawFallback();
  }

  function drawFallback() {
    if (!mapCanvas || !orbit || mapCanvas.hidden) return;
    const rect = mapCanvas.getBoundingClientRect();
    const pixelRatio = powerMode === 'FULL' ? 1.5 : powerMode === 'LOW_POWER' ? 1 : 0.75;
    const width = Math.max(320, Math.floor(rect.width * Math.min(devicePixelRatio || 1, pixelRatio)));
    const height = Math.max(180, Math.floor(rect.height * Math.min(devicePixelRatio || 1, pixelRatio)));
    mapCanvas.width = width; mapCanvas.height = height;
    const ctx = mapCanvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#081525'; ctx.fillRect(0, 0, width, height);
    const x = lon => (lon + 180) / 360 * width, y = lat => (90 - lat) / 180 * height;
    ctx.strokeStyle = 'rgba(140,180,200,.18)'; ctx.lineWidth = 1;
    for (let lon = -180; lon <= 180; lon += 30) { ctx.beginPath(); ctx.moveTo(x(lon), 0); ctx.lineTo(x(lon), height); ctx.stroke(); }
    for (let lat = -60; lat <= 60; lat += 30) { ctx.beginPath(); ctx.moveTo(0, y(lat)); ctx.lineTo(width, y(lat)); ctx.stroke(); }
    const track = buildOrbitTrack(orbit, simulatedTime, { beforeSeconds: 45 * 60, afterSeconds: 45 * 60, stepSeconds: 30 });
    const drawPath = (states, color) => {
      ctx.strokeStyle = color; ctx.lineWidth = Math.max(2, width / 550); ctx.beginPath();
      let previous = null;
      for (const state of states) {
        const px = x(state.longitudeDeg), py = y(state.latitudeDeg);
        if (previous && Math.abs(state.longitudeDeg - previous.longitudeDeg) > 180) ctx.moveTo(px, py);
        else if (previous) ctx.lineTo(px, py); else ctx.moveTo(px, py);
        previous = state;
      }
      ctx.stroke();
    };
    drawPath(track.past, '#89aab0'); drawPath(track.future, '#65e5d0');
    const current = positionAt(simulatedTime);
    if (current) {
      ctx.fillStyle = '#fbfbff'; ctx.beginPath(); ctx.arc(x(current.longitudeDeg), y(current.latitudeDeg), Math.max(5, width / 180), 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#d9f2ee'; ctx.font = `${Math.max(11, width / 52)}px system-ui`;
      ctx.fillText(modeSelect.value === 'SIMULATED' ? 'SIMULATED SPACECRAFT' : 'ISS ESTIMATE', x(current.longitudeDeg) + 10, y(current.latitudeDeg) - 10);
    }
    for (const row of radiationObservations) {
      const location = row?.location;
      if (!validRadLabLocation(row)) continue;
      const selected = selectedRadiationObservation && selectedRadiationObservation.instrument_id === row.instrument_id && selectedRadiationObservation.observed_at_utc === row.observed_at_utc;
      ctx.fillStyle = selected ? '#ffc26e' : '#53dec9'; ctx.beginPath();
      ctx.arc(x(location.longitude_deg), y(location.latitude_deg), selected ? Math.max(4, width / 250) : Math.max(2, width / 550), 0, Math.PI * 2); ctx.fill();
    }
  }

  async function initThree() {
    try {
      stageNotice.textContent = 'Loading the local 3D renderer and attributed Earth texture…';
      THREE = await import('./vendor/orbit/three.module.js');
      renderer = new THREE.WebGLRenderer({ canvas: webglCanvas, antialias: powerMode === 'FULL', alpha: false, powerPreference: powerMode === 'FULL' ? 'default' : 'low-power' });
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, powerMode === 'FULL' ? 1.5 : powerMode === 'LOW_POWER' ? 1 : 0.75));
      renderer.setClearColor(0x06111e, 1);
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(36, 1, 0.01, 200);
      scene.add(new THREE.AmbientLight(0x8baac6, 0.26));
      sunLight = new THREE.DirectionalLight(0xfff4d7, 2.25); scene.add(sunLight);
      const textureLoader = new THREE.TextureLoader();
      texture = await textureLoader.loadAsync(TEXTURE_URL);
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
      earth = new THREE.Mesh(
        new THREE.SphereGeometry(1, powerMode === 'FULL' ? 96 : 48, powerMode === 'FULL' ? 64 : 32),
        new THREE.MeshStandardMaterial({ map: texture, roughness: 1, metalness: 0, color: 0xdbe9f6 }),
      );
      scene.add(earth);
      const atmosphereGeometry = new THREE.SphereGeometry(1.035, powerMode === 'FULL' ? 48 : 32, powerMode === 'FULL' ? 32 : 24);
      const atmosphereMaterial = new THREE.ShaderMaterial({
        transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
        vertexShader: 'varying vec3 vNormal; varying vec3 vView; void main(){ vec4 mv=modelViewMatrix*vec4(position,1.0); vNormal=normalize(normalMatrix*normal); vView=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }',
        fragmentShader: 'varying vec3 vNormal; varying vec3 vView; void main(){ float rim=pow(1.0-max(dot(normalize(vNormal),normalize(vView)),0.0),2.0); gl_FragColor=vec4(0.20,0.64,0.90,0.31*rim); }',
      });
      atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial); scene.add(atmosphere);
      const starPositions = new Float32Array((powerMode === 'FULL' ? 620 : 260) * 3);
      let seed = 19410615;
      const random = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
      for (let i = 0; i < starPositions.length; i += 3) {
        const z = random() * 2 - 1, theta = random() * Math.PI * 2, radius = 15 + random() * 50, planar = Math.sqrt(1 - z * z);
        starPositions[i] = radius * planar * Math.cos(theta); starPositions[i + 1] = radius * z; starPositions[i + 2] = radius * planar * Math.sin(theta);
      }
      const starsGeometry = new THREE.BufferGeometry(); starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
      const stars = new THREE.Points(starsGeometry, new THREE.PointsMaterial({ color: 0xb9d1e4, size: 0.09, transparent: true, opacity: 0.62, sizeAttenuation: true }));
      scene.add(stars);
      raycaster = new THREE.Raycaster(); pointer = new THREE.Vector2();
      mapCanvas.hidden = true; webglCanvas.hidden = false;
      stageNotice.hidden = false;
      stageNotice.textContent = 'Interactive Earth renderer ready. Drag to rotate · scroll to zoom · click a surface point to inspect its coordinates.';
      resizeObserver = new ResizeObserver(resize); resizeObserver.observe(stage);
      resize(); renderLoop();
      if (orbit) renderOrbitGraphics();
    } catch (error) {
      if (renderer) { renderer.dispose(); renderer = null; }
      webglCanvas.hidden = true; mapCanvas.hidden = false;
      stageNotice.hidden = false;
      stageNotice.textContent = `3D globe unavailable (${error.message}). The calculated 2D ground-track fallback remains available.`;
      resizeObserver?.disconnect(); resizeObserver = null;
      drawFallback();
    }
  }

  function resize() {
    if (!renderer || !camera) return;
    const rect = stage.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / rect.height; camera.updateProjectionMatrix();
    drawFallback();
  }

  function setCamera() {
    if (!camera) return;
    const cosElevation = Math.cos(cameraElevation);
    camera.position.set(cameraDistance * cosElevation * Math.sin(cameraAzimuth), cameraDistance * Math.sin(cameraElevation), cameraDistance * cosElevation * Math.cos(cameraAzimuth));
    camera.lookAt(0, 0, 0);
  }

  function stopRenderSchedule() {
    if (animationId) cancelAnimationFrame(animationId);
    if (renderTimer) clearTimeout(renderTimer);
    animationId = 0; renderTimer = 0;
  }

  function scheduleRender() {
    if (isDestroyed || !viewVisible || animationId || renderTimer) return;
    if (powerMode === 'CRITICAL' || powerMode === 'LOW_POWER') {
      const delay = powerMode === 'CRITICAL' ? 1000 : 1000 / 12;
      renderTimer = window.setTimeout(() => { renderTimer = 0; renderLoop(performance.now()); }, delay);
    } else animationId = requestAnimationFrame(renderLoop);
  }

  function renderLoop(now = performance.now()) {
    if (isDestroyed || !viewVisible) { animationId = 0; renderTimer = 0; return; }
    animationId = 0; renderTimer = 0;
    scheduleRender();
    const maxFrameMs = powerMode === 'FULL' ? 1000 / 24 : powerMode === 'LOW_POWER' ? 1000 / 12 : 1000;
    if (document.hidden || now - lastDraw < maxFrameMs) return;
    lastDraw = now;
    const elapsed = Math.max(0, Math.min(1000, now - lastClock)); lastClock = now;
    if (playback && orbit) simulatedTime += elapsed * Number(speed.value || 1);
    else if (missionTimeOverride !== null && orbit) simulatedTime = missionTimeOverride;
    else if (followNow && orbit) simulatedTime = Date.now();
    if (orbit && (playback || followNow) && now - lastPositionUpdate > 950) {
      lastPositionUpdate = now; updateCurrentPosition(false); renderOrbitGraphics();
    }
    if (renderer && scene && camera) {
      if (sunLight && displayedState?.sunEcfUnit) {
        const sun = displayedState.sunEcfUnit;
        sunLight.position.set(sun.x, sun.z, -sun.y).multiplyScalar(8);
      }
      if (followEnabled && spacecraft) {
        const point = spacecraft.position.clone().normalize();
        const target = point.clone().multiplyScalar(1.12);
        const cameraPoint = point.clone().multiplyScalar(cameraDistance);
        camera.position.lerp(cameraPoint, 0.08); camera.lookAt(target);
      } else setCamera();
      renderer.render(scene, camera); renderTotal++; renderedAt.push(now);
      while (renderedAt.length && now - renderedAt[0] > 10_000) renderedAt.shift();
    } else if (!mapCanvas.hidden && orbit) drawFallback();
  }

  function onPointerDown(event) {
    if (!renderer) return;
    drag = { x: event.clientX, y: event.clientY, moved: false };
    webglCanvas.setPointerCapture(event.pointerId);
  }
  function onPointerMove(event) {
    if (drag) {
      const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 2) drag.moved = true;
      cameraAzimuth -= dx * 0.006; cameraElevation = Math.max(-1.35, Math.min(1.35, cameraElevation + dy * 0.005));
      drag.x = event.clientX; drag.y = event.clientY;
    }
  }
  function onPointerUp(event) {
    const wasDrag = drag?.moved; drag = null;
    if (wasDrag || !renderer || !earth) return;
    const rect = webglCanvas.getBoundingClientRect();
    pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObject(earth, false)[0];
    if (!hit) return;
    const p = hit.point.clone().normalize();
    const latitude = Math.asin(p.y) * 180 / Math.PI;
    const longitude = ((Math.atan2(-p.z, p.x) * 180 / Math.PI + 540) % 360) - 180;
    viewPoint.textContent = `Selected surface coordinate · latitude ${formatDegrees(latitude, 3)} · longitude ${formatDegrees(longitude, 3)}. This is a map coordinate, not a crew or device location.`;
  }
  webglCanvas.addEventListener('pointerdown', onPointerDown, { signal: aborter.signal });
  webglCanvas.addEventListener('pointermove', onPointerMove, { signal: aborter.signal });
  webglCanvas.addEventListener('pointerup', onPointerUp, { signal: aborter.signal });
  webglCanvas.addEventListener('wheel', event => { event.preventDefault(); cameraDistance = Math.max(1.35, Math.min(7, cameraDistance + event.deltaY * 0.003)); }, { passive: false, signal: aborter.signal });
  playbackButton.addEventListener('click', () => {
    if (scenarioClockLocked) return;
    missionTimeOverride = null;
    playback = !playback; followNow = false;
    playbackButton.textContent = playback ? 'Pause timeline' : 'Play timeline';
    stageNotice.textContent = playback ? 'Mission timeline is propagating locally from the selected element epoch.' : 'Timeline paused at the displayed UTC calculation time.';
  }, { signal: aborter.signal });
  timeSlider.addEventListener('input', () => {
    if (scenarioClockLocked) return;
    missionTimeOverride = null;
    playback = false; followNow = false; timelineOffsetMinutes = Number(timeSlider.value); simulatedTime = Date.now() + timelineOffsetMinutes * 60000;
    playbackButton.textContent = 'Play timeline'; updateCurrentPosition(true);
  }, { signal: aborter.signal });
  nowButton.addEventListener('click', () => {
    if (scenarioClockLocked) return;
    missionTimeOverride = null;
    playback = false; followNow = true; timelineOffsetMinutes = 0; simulatedTime = Date.now(); timeSlider.value = '0';
    playbackButton.textContent = 'Play timeline'; updateCurrentPosition(true);
  }, { signal: aborter.signal });
  follow.addEventListener('click', () => { followEnabled = !followEnabled; follow.setAttribute('aria-pressed', String(followEnabled)); follow.textContent = followEnabled ? 'Stop following' : 'Follow spacecraft'; }, { signal: aborter.signal });
  reset.addEventListener('click', () => { cameraAzimuth = 0.55; cameraElevation = 0.26; cameraDistance = 3.65; followEnabled = false; follow.setAttribute('aria-pressed', 'false'); follow.textContent = 'Follow spacecraft'; }, { signal: aborter.signal });
  refreshButton.addEventListener('click', () => loadTracked({ force: true }), { signal: aborter.signal });
  modeSelect.addEventListener('change', async () => {
    if (modeSelect.value === 'SIMULATED') {
      orbitRequest?.abort();
      const omm = makeSyntheticOmm(new Date());
      installOrbitModel(omm, { mode: 'SIMULATED', fetchedAt: Date.now(), source: 'ASTHRAL_SYNTHETIC_ELEMENTS' });
    } else await loadTracked();
  }, { signal: aborter.signal });
  document.addEventListener('visibilitychange', () => { lastClock = performance.now(); }, { signal: aborter.signal });
  updateWeather();
  await initThree();
  const cached = readOrbitSnapshot();
  if (cached && modeSelect.value === 'ISS_TRACKED') {
    try { installOrbitModel(cached.data, { mode: 'ISS_TRACKED', fetchedAt: Date.parse(cached.fetched_at), source: cached.source }); }
    catch { setUnavailable('Cached ISS mean elements are invalid or too old. Fetch current elements or select simulated mode.'); }
  }
  void loadTracked();
  function resetPositionTimer() {
    clearInterval(clockTimer);
    const interval = powerMode === 'FULL' ? 1000 : powerMode === 'LOW_POWER' ? 5000 : 30000;
    clockTimer = window.setInterval(() => {
      if (!viewVisible || !orbit || playback || !followNow) return;
      updateCurrentPosition(false);
    }, interval);
  }
  resetPositionTimer();

  return {
    setVisible(visible) {
      viewVisible = Boolean(visible);
      if (!viewVisible) { stopRenderSchedule(); return; }
      lastClock = performance.now(); lastDraw = 0;
      if (renderer && !animationId && !renderTimer && !isDestroyed) renderLoop();
      if (followNow && orbit) updateCurrentPosition(true);
    },
    setPowerMode(mode) {
      const next = ['FULL', 'LOW_POWER', 'CRITICAL'].includes(mode) ? mode : 'FULL';
      if (next === powerMode) return;
      powerMode = next;
      powerNote.textContent = `${powerMode.replace('_', ' ')} · ${powerMode === 'FULL' ? '24 fps' : powerMode === 'LOW_POWER' ? '12 fps' : '1 fps'} render cap`;
      renderer?.setPixelRatio(Math.min(devicePixelRatio || 1, powerMode === 'FULL' ? 1.5 : powerMode === 'LOW_POWER' ? 1 : 0.75));
      if (powerMode === 'CRITICAL') { playback = false; playbackButton.textContent = 'Play timeline'; }
      playbackButton.disabled = scenarioClockLocked || powerMode === 'CRITICAL';
      speed.disabled = scenarioClockLocked || powerMode === 'CRITICAL';
      stopRenderSchedule(); lastDraw = 0; resetPositionTimer();
      if (!mapCanvas.hidden) drawFallback();
      if (viewVisible && renderer && !isDestroyed) renderLoop(performance.now());
      stageNotice.textContent = `${powerMode.replace('_', ' ')} profile applied · ${powerMode === 'FULL' ? '24 fps' : powerMode === 'LOW_POWER' ? '12 fps' : '1 fps'} globe render cap · actual electrical energy is not measured.`;
    },
    setRadLabObservations(observations = [], selected = null) {
      radiationObservations = Array.isArray(observations) ? observations.filter(row => row?.source === 'NASA_OSDR_RADLAB' && row?.classification === 'HISTORICAL') : [];
      selectedRadiationObservation = selected?.source === 'NASA_OSDR_RADLAB' ? selected : null;
      const mappedCount = radiationObservations.filter(validRadLabLocation).length;
      radLabLegend.textContent = `HISTORICAL RADLAB · ${mappedCount}`;
      radLabLegend.setAttribute('aria-label', `${mappedCount} historical RadLab records with mapped ISS coordinates`);
      if (orbit) renderOrbitGraphics(); else drawFallback();
      return mappedCount;
    },
    renderMetrics() {
      const now = performance.now();
      while (renderedAt.length && now - renderedAt[0] > 10_000) renderedAt.shift();
      const observedSeconds = renderedAt.length > 1 ? Math.min(10_000, renderedAt.at(-1) - renderedAt[0]) / 1000 : 0;
      return { mode: powerMode, target_fps_cap: powerMode === 'FULL' ? 24 : powerMode === 'LOW_POWER' ? 12 : 1,
        renders_in_window: renderedAt.length, measurement_window_seconds: Number(observedSeconds.toFixed(2)),
        observed_fps: observedSeconds > 0 ? Number(((renderedAt.length - 1) / observedSeconds).toFixed(2)) : 0,
        render_total: renderTotal, physical_power_measurement: false };
    },
    setScenario: value => { if (modeSelect.value === 'SIMULATED') { const selected = value; stageNotice.textContent = `SIMULATED MISSION · ${selected.replaceAll('_', ' ').toUpperCase()} · no real spacecraft or crew telemetry.`; updateCurrentPosition(true); } },
    setMissionTime(value) {
      const timestamp = Date.parse(value);
      if (!Number.isFinite(timestamp)) return false;
      missionTimeOverride = timestamp; playback = false; followNow = false; simulatedTime = timestamp;
      timelineOffsetMinutes = Math.round((timestamp - Date.now()) / 60000);
      timeSlider.value = String(Math.max(-90, Math.min(90, timelineOffsetMinutes)));
      updateCurrentPosition(false);
      if (viewVisible && orbit) renderOrbitGraphics();
      return true;
    },
    setScenarioActive(active) {
      scenarioClockLocked = Boolean(active);
      timeSlider.disabled = scenarioClockLocked;
      nowButton.disabled = scenarioClockLocked;
      if (scenarioClockLocked && missionTimeOverride !== null) updateCurrentPosition(false);
      playbackButton.disabled = scenarioClockLocked || powerMode === 'CRITICAL';
      speed.disabled = scenarioClockLocked || powerMode === 'CRITICAL';
    },
    currentState: () => displayedState ? { ...displayedState, mode: modeSelect.value, source: orbitModelSource, scenario: scenario() } : null,
    refresh: () => modeSelect.value === 'ISS_TRACKED' ? loadTracked({ force: true }) : Promise.resolve(),
    destroy() {
      isDestroyed = true; clearInterval(clockTimer); stopRenderSchedule(); aborter.abort(); resizeObserver?.disconnect();
      orbitRequest?.abort();
      if (scene) {
        scene.traverse(object => { object.geometry?.dispose?.(); if (Array.isArray(object.material)) object.material.forEach(material => material.dispose?.()); else object.material?.dispose?.(); });
        texture?.dispose?.();
      }
      if (renderer) { renderer.renderLists?.dispose?.(); renderer.dispose(); renderer.forceContextLoss?.(); renderer = null; }
      container.replaceChildren();
    },
  };
}
