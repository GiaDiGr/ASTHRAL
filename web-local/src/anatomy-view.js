import { cachePublicResources } from './public-resources.js';

export const ANATOMY_MODEL = Object.freeze({
  name: 'Z-Anatomy muscular system layer',
  source: 'https://github.com/ArianArsenal/anatomy-explorer',
  upstreamModel: 'https://github.com/Z-Anatomy/Models-of-human-anatomy',
  upstreamDataset: 'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/',
  license: 'CC BY-SA 4.0 (model layer; derived from BodyParts3D CC BY-SA 2.1 Japan)',
  sha256: 'f8399ba12dedb7cd88de199eddf7e3f8a3de8373a69228fb9da7ce1b7981ffd2',
  clinical_validation: false,
});

const region = (id, label, system, laterality = 'midline', patterns = []) => Object.freeze({ id, label, system, laterality, patterns: patterns.map(value => new RegExp(value, 'i')) });

export const ANATOMY_REGIONS = Object.freeze([
  region('head', 'Head', 'Musculoskeletal', 'midline', ['head', 'frontalis', 'occipitalis', 'epicranial', 'temporoparietalis']),
  region('face', 'Face', 'Musculoskeletal', 'midline', ['nasalis', 'masseter', 'buccinator', 'zygomatic', 'orbicularis oris', 'facial']),
  region('left_eye', 'Left eye region', 'Ocular muscles', 'left', ['rectus muscle', 'oblique muscle', 'palpebra', 'tarsus', 'trochlea', 'orbicularis oculi']),
  region('right_eye', 'Right eye region', 'Ocular muscles', 'right', ['rectus muscle', 'oblique muscle', 'palpebra', 'tarsus', 'trochlea', 'orbicularis oculi']),
  region('neck', 'Neck', 'Musculoskeletal', 'midline', ['sternocleidomastoid', 'scalene', 'longus colli', 'longus capitis', 'neck']),
  region('chest', 'Chest', 'Musculoskeletal', 'midline', ['pectoral', 'intercostal', 'serratus anterior', 'thoracic']),
  region('abdomen', 'Abdomen', 'Musculoskeletal', 'midline', ['rectus abdominis', 'transversus abdominis', 'external oblique', 'internal oblique', 'abdominal']),
  region('back', 'Back', 'Musculoskeletal', 'midline', ['trapezius', 'latissimus dorsi', 'rhomboid', 'erector spinae', 'multifidus', 'back']),
  region('left_shoulder', 'Left shoulder', 'Musculoskeletal', 'left', ['deltoid', 'shoulder']),
  region('right_shoulder', 'Right shoulder', 'Musculoskeletal', 'right', ['deltoid', 'shoulder']),
  region('left_upper_arm', 'Left upper arm', 'Musculoskeletal', 'left', ['biceps brachii', 'triceps brachii', 'brachialis', 'coracobrachialis']),
  region('right_upper_arm', 'Right upper arm', 'Musculoskeletal', 'right', ['biceps brachii', 'triceps brachii', 'brachialis', 'coracobrachialis']),
  region('left_forearm', 'Left forearm', 'Musculoskeletal', 'left', ['forearm', 'pronator', 'supinator', 'flexor carpi', 'extensor carpi']),
  region('right_forearm', 'Right forearm', 'Musculoskeletal', 'right', ['forearm', 'pronator', 'supinator', 'flexor carpi', 'extensor carpi']),
  region('left_hand', 'Left hand', 'Musculoskeletal', 'left', ['hand', 'thenar', 'hypothenar', 'lumbrical', 'interossei']),
  region('right_hand', 'Right hand', 'Musculoskeletal', 'right', ['hand', 'thenar', 'hypothenar', 'lumbrical', 'interossei']),
  region('left_hip', 'Left hip', 'Musculoskeletal', 'left', ['gluteus', 'gluteal', 'hip']),
  region('right_hip', 'Right hip', 'Musculoskeletal', 'right', ['gluteus', 'gluteal', 'hip']),
  region('left_thigh', 'Left thigh', 'Musculoskeletal', 'left', ['quadriceps', 'hamstring', 'adductor', 'gracilis', 'sartorius', 'vastus', 'rectus femoris', 'biceps femoris']),
  region('right_thigh', 'Right thigh', 'Musculoskeletal', 'right', ['quadriceps', 'hamstring', 'adductor', 'gracilis', 'sartorius', 'vastus', 'rectus femoris', 'biceps femoris']),
  region('left_knee', 'Left knee', 'Musculoskeletal', 'left', ['patella', 'popliteus', 'knee']),
  region('right_knee', 'Right knee', 'Musculoskeletal', 'right', ['patella', 'popliteus', 'knee']),
  region('left_lower_leg', 'Left lower leg', 'Musculoskeletal', 'left', ['gastrocnemius', 'soleus', 'tibialis', 'fibularis', 'peroneus', 'lower leg']),
  region('right_lower_leg', 'Right lower leg', 'Musculoskeletal', 'right', ['gastrocnemius', 'soleus', 'tibialis', 'fibularis', 'peroneus', 'lower leg']),
  region('left_ankle', 'Left ankle', 'Musculoskeletal', 'left', ['ankle']),
  region('right_ankle', 'Right ankle', 'Musculoskeletal', 'right', ['ankle']),
  region('left_foot', 'Left foot', 'Musculoskeletal', 'left', ['foot', 'toe', 'plantar']),
  region('right_foot', 'Right foot', 'Musculoskeletal', 'right', ['foot', 'toe', 'plantar']),
]);

function bodySide(name) {
  const value = String(name ?? '').toLowerCase();
  if (/(?:^|[._\s-])(?:l|left)$/.test(value) || /\bleft\b/.test(value)) return 'left';
  if (/(?:^|[._\s-])(?:r|right)$/.test(value) || /\bright\b/.test(value)) return 'right';
  return null;
}

export function regionForAnatomyName(name) {
  const value = String(name ?? '');
  const side = bodySide(value);
  const candidates = ANATOMY_REGIONS.filter(item => item.patterns.some(pattern => pattern.test(value)));
  if (!candidates.length) return null;
  if (side) return candidates.find(item => item.laterality === side) ?? candidates.find(item => item.laterality === 'midline') ?? null;
  return candidates.find(item => item.laterality === 'midline') ?? null;
}

export function anatomyRegionMatches(regionId, objectName) {
  return regionForAnatomyName(objectName)?.id === regionId;
}

const svgNS = 'http://www.w3.org/2000/svg';
const element = (tag, text = '') => { const item = document.createElement(tag); if (text) item.textContent = text; return item; };
const svgElement = (tag, attrs = {}) => { const item = document.createElementNS(svgNS, tag); for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, String(value)); return item; };

export async function mountAnatomyView(container, { status = () => {}, powerMode = () => document.querySelector('#mode')?.value || 'FULL' } = {}) {
  if (!container) throw Error('Anatomy explorer container is unavailable.');
  const root = element('div'); root.className = 'anatomy-explorer';
  const toolbar = element('div'); toolbar.className = 'anatomy-toolbar';
  const front = element('button', 'Anterior view'); front.type = 'button'; front.setAttribute('aria-pressed', 'true');
  const back = element('button', 'Posterior view'); back.type = 'button'; back.setAttribute('aria-pressed', 'false');
  const pan = element('button', 'Pan mode off'); pan.type = 'button'; pan.setAttribute('aria-pressed', 'false');
  const zoomIn = element('button', 'Zoom in'); zoomIn.type = 'button';
  const zoomOut = element('button', 'Zoom out'); zoomOut.type = 'button';
  const reset = element('button', 'Reset camera'); reset.type = 'button';
  const selectLabel = element('label', 'Select an anatomical region');
  const regionSelect = document.createElement('select'); regionSelect.setAttribute('aria-label', 'Select an anatomical region');
  for (const item of ANATOMY_REGIONS) regionSelect.append(new Option(item.label, item.id));
  selectLabel.append(regionSelect);
  toolbar.append(front, back, pan, zoomIn, zoomOut, reset, selectLabel);

  const frame = element('div'); frame.className = 'anatomy-frame'; frame.setAttribute('aria-label', 'Interactive 3D anatomical model');
  const canvas = document.createElement('canvas'); canvas.className = 'anatomy-canvas'; canvas.setAttribute('aria-label', 'Rotate, zoom and select named muscle regions in the licensed 3D anatomy model');
  const fallback = element('div'); fallback.className = 'anatomy-fallback'; fallback.hidden = true;
  const notice = element('p', 'Loading the locally licensed 3D anatomical model…'); notice.className = 'anatomy-notice'; notice.setAttribute('role', 'status'); notice.setAttribute('aria-live', 'polite');
  frame.append(canvas, fallback, notice);
  const legend = element('div'); legend.className = 'anatomy-legend';
  for (const [key, label] of [['selected', 'Selected region'], ['assessed', 'Assessed region'], ['finding', 'Documented finding'], ['review', 'Review required'], ['empty', 'No available data']]) {
    const item = element('span', label); item.dataset.state = key; legend.append(item);
  }
  const layout = element('div'); layout.className = 'anatomy-layout';
  const context = element('section'); context.className = 'anatomy-context';
  const heading = element('h2', 'Region context');
  const selectedLine = element('p'); selectedLine.id = 'anatomy-selected-region';
  const dataLine = element('p', 'No localized health assessments, findings or review decisions are mapped to this anatomical region in the current data contract. Missing regional data do not indicate normal health.'); dataLine.className = 'anatomy-no-data';
  const recordLine = element('p', 'System-wide physiological measurements remain in Health Monitoring and are not attributed to this body region by this view.'); recordLine.className = 'anatomy-system-context';
  const timelineHeading = element('h3', 'Regional history');
  const timeline = element('p', 'No anatomically localized records are available to plot. No timepoints or trends are inferred.');
  const moduleList = element('div'); moduleList.className = 'anatomy-modules';
  const history = element('a', 'Open Health History'); history.href = '#history'; history.dataset.view = 'history';
  const neuro = element('a', 'Open NeuroGuard context'); neuro.href = '#neuroguard'; neuro.dataset.view = 'neuroguard';
  const exportButton = element('button', 'Export region context'); exportButton.type = 'button';
  const cacheButton = element('button', 'Install 3D model for offline use'); cacheButton.type = 'button';
  const dataStatus = element('p', 'The model is educational orientation context, not a diagnostic atlas or clinical localization tool.'); dataStatus.className = 'anatomy-data-status'; dataStatus.setAttribute('role', 'status');
  moduleList.append(history, neuro);
  context.append(heading, selectedLine, dataLine, recordLine, timelineHeading, timeline, moduleList, exportButton, cacheButton, dataStatus);
  const source = element('aside'); source.className = 'anatomy-source';
  const sourceTitle = element('h3', 'Model source & limits');
  const sourceText = element('p', 'Z-Anatomy muscular system layer derived from BodyParts3D. Asset is distributed under CC BY-SA 4.0. Only this model layer is included; the organ layer and its separately licensed kidney asset are not bundled. ASTHRAL has not clinically validated the model or the region mapping.');
  const sourceLink = element('a', 'View model provenance and attribution'); sourceLink.href = 'https://github.com/ArianArsenal/anatomy-explorer'; sourceLink.target = '_blank'; sourceLink.rel = 'noopener noreferrer';
  const dataSourceLink = element('a', 'Open NASA OSDR environmental data portal'); dataSourceLink.href = 'https://visualization.osdr.nasa.gov/eda/'; dataSourceLink.target = '_blank'; dataSourceLink.rel = 'noopener noreferrer';
  source.append(sourceTitle, sourceText, sourceLink, dataSourceLink);
  layout.append(context, source);
  root.append(toolbar, frame, legend, layout);
  container.replaceChildren(root);

  let THREE = null, renderer = null, scene = null, camera = null, modelRoot = null;
  let resizeObserver = null, raycaster = null, pointer = null, raf = 0, renderTotal = 0, visible = true, disposed = false;
  let selectedRegion = ANATOMY_REGIONS[0], posterior = false, panMode = false, drag = null, yaw = 0, pitch = 0.03, zoom = 3.4;
  let target = null, originalMaterials = new Map(), highlighted = [], lastRenderAt = null;

  function modelScale() { return powerMode() === 'FULL' ? 1.35 : powerMode() === 'LOW_POWER' ? 1 : 0.68; }
  function render() {
    raf = 0;
    if (!visible || disposed) return;
    if (renderer && scene && camera) { renderer.render(scene, camera); renderTotal++; lastRenderAt = new Date().toISOString(); }
  }
  function scheduleRender() { if (raf || !visible || disposed) return; raf = requestAnimationFrame(render); }
  function cameraUpdate() {
    if (!camera || !target) return;
    const effectiveYaw = yaw + (posterior ? Math.PI : 0);
    const horizontal = zoom * Math.cos(pitch);
    camera.position.set(target.x + Math.sin(effectiveYaw) * horizontal, target.y + Math.sin(pitch) * zoom, target.z + Math.cos(effectiveYaw) * horizontal);
    camera.lookAt(target); scheduleRender();
  }
  function resize() {
    if (!renderer || !camera) return;
    const box = frame.getBoundingClientRect(); if (box.width < 1 || box.height < 1) return;
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, modelScale()));
    renderer.setSize(box.width, box.height, false); camera.aspect = box.width / box.height; camera.updateProjectionMatrix(); scheduleRender();
  }
  function disposeHighlighted() {
    for (const [mesh, original, cloned] of highlighted) {
      mesh.material = original;
      for (const item of Array.isArray(cloned) ? cloned : [cloned]) item?.dispose?.();
    }
    highlighted = [];
  }
  function highlightRegion(item) {
    if (!modelRoot) return;
    disposeHighlighted();
    modelRoot.traverse(object => {
      if (!object.isMesh || !object.userData.astName || !anatomyRegionMatches(item.id, object.userData.astName)) return;
      const original = originalMaterials.get(object) ?? object.material;
      const cloneMaterial = material => {
        const clone = material.clone();
        if (clone.emissive) { clone.emissive.setHex(0x25bfb6); clone.emissiveIntensity = 0.72; }
        else if (clone.color) clone.color.lerp(new THREE.Color(0x3ddfd1), 0.52);
        return clone;
      };
      const clone = Array.isArray(original) ? original.map(cloneMaterial) : cloneMaterial(original);
      object.material = clone; highlighted.push([object, original, clone]);
    });
    selectedLine.textContent = `${item.label} · ${item.system} · ${item.laterality === 'midline' ? 'midline / unspecified side' : item.laterality + ' side'}. Selection is a navigation aid only.`;
    selectedRegion = item;
    scheduleRender();
  }
  function currentModules(item) {
    moduleList.replaceChildren();
    const add = (label, href, description) => { const a = element('a', label); a.href = href; a.title = description; moduleList.append(a); };
    if (/eye/.test(item.id)) add('OcularVision · image intake', '#vision', 'Open ocular image intake; no model diagnosis is available.');
    if (item.id === 'face' || item.id.startsWith('left_') || item.id.startsWith('right_')) add('MotionGuard · movement research', '#exercise', 'Open optional local motion analysis; outputs are not localized findings.');
    if (['chest'].includes(item.id)) add('EchoVision · model unavailable', '#vision', 'Open the computer-vision module status.');
    if (['face', 'head'].includes(item.id)) add('SkinGuard · image intake', '#vision', 'Open image quality intake; no skin lesion model is available.');
    add('NeuroGuard · separate context', '#neuroguard', 'Cognitive and behavioral results are not anatomically localized.');
    add('Health History', '#history', 'Open source records without anatomically attributing system-level measurements.');
  }
  function selectRegion(value) {
    const item = ANATOMY_REGIONS.find(row => row.id === value) ?? ANATOMY_REGIONS[0];
    regionSelect.value = item.id; highlightRegion(item); currentModules(item);
  }
  function createFallback(message) {
    canvas.hidden = true; fallback.hidden = false; fallback.replaceChildren();
    const svg = svgElement('svg', { viewBox: '0 0 320 430', role: 'img', 'aria-label': 'Two-dimensional schematic anatomical orientation fallback' });
    svg.append(svgElement('path', { d: 'M160 34 C137 34 125 53 125 76 C125 96 137 108 146 112 L146 131 C121 137 104 154 98 177 L74 263 L91 270 L119 203 L120 270 L116 355 L137 355 L151 278 L169 278 L183 355 L204 355 L200 270 L200 203 L229 270 L246 263 L222 177 C216 154 199 137 174 131 L174 112 C183 108 195 96 195 76 C195 53 183 34 160 34 Z', fill: '#72899a', stroke: '#a8bcc9', 'stroke-width': 3 }));
    const note = svgElement('text', { x: 160, y: 398, 'text-anchor': 'middle', fill: '#c9dbe5', 'font-size': 12 }); note.textContent = '2D schematic fallback · not a clinical atlas'; svg.append(note);
    fallback.append(svg);
    const help = element('p', message + ' Use the accessible region selector above.'); fallback.append(help);
    notice.textContent = 'Interactive 3D is unavailable; 2D schematic and region selection remain usable.';
  }
  function sideFromName(value) { return /(?:^|[._\s-])(?:l|left)$/.test(value.toLowerCase()) ? 'left' : /(?:^|[._\s-])(?:r|right)$/.test(value.toLowerCase()) ? 'right' : 'midline'; }

  try {
    const [{ GLTFLoader }, { MeshoptDecoder }, three] = await Promise.all([
      import('./vendor/anatomy/GLTFLoader.js'), import('./vendor/anatomy/meshopt_decoder.module.js'), import('./vendor/orbit/three.module.js'),
    ]);
    THREE = three;
    await MeshoptDecoder.ready;
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: powerMode() === 'FULL', powerPreference: powerMode() === 'FULL' ? 'default' : 'low-power' });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, modelScale())); renderer.setClearColor(0x071522, 0);
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(33, 1, 0.01, 100);
    scene.add(new THREE.HemisphereLight(0xd9f1ff, 0x171e25, 1.65));
    const key = new THREE.DirectionalLight(0xffe6cf, 2.3); key.position.set(-2.7, 3.4, 3.6); scene.add(key);
    const fill = new THREE.DirectionalLight(0x7cb8d2, 1.1); fill.position.set(3.4, 0.9, -3); scene.add(fill);
    modelRoot = new THREE.Group(); scene.add(modelRoot);
    const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync('./vendor/anatomy/zanatomy-muscles.glb');
    const model = gltf.scene; model.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(model), center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
    model.position.set(-center.x, -center.y, -center.z);
    modelRoot.scale.setScalar(1.62 / Math.max(size.y, 0.01));
    modelRoot.add(model);
    model.traverse(object => {
      if (!object.isMesh) return;
      object.userData.astName = `${object.name || ''} ${object.parent?.name || ''}`.trim();
      originalMaterials.set(object, object.material);
      object.frustumCulled = true;
    });
    target = new THREE.Vector3(0, 0, 0); raycaster = new THREE.Raycaster(); pointer = new THREE.Vector2();
    resizeObserver = new ResizeObserver(resize); resizeObserver.observe(frame); resize();
    fallback.hidden = true; canvas.hidden = false; notice.textContent = 'Interactive licensed model loaded. Drag to rotate · wheel or pinch to zoom · enable pan mode to move the view.';
    selectRegion(regionSelect.value);
    status(`3D anatomy loaded · ${ANATOMY_MODEL.name} · 513 named source meshes · model review only; no localized clinical findings are inferred.`);
  } catch (error) {
    createFallback(error.message || '3D model loading failed.');
    status('3D anatomy unavailable · 2D region selector remains usable · no clinical result was produced.');
  }

  function pointerDown(event) {
    if (!renderer || !canvas) return;
    drag = { x: event.clientX, y: event.clientY, moved: false, pan: panMode || event.shiftKey || event.button === 2 };
    canvas.setPointerCapture(event.pointerId);
  }
  function pointerMove(event) {
    if (!drag) return;
    const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 2) drag.moved = true;
    if (drag.pan && camera && target) {
      const scale = zoom / Math.max(frame.getBoundingClientRect().height, 1);
      target.x -= dx * scale; target.y += dy * scale;
    } else { yaw -= dx * 0.008; pitch = Math.max(-1.1, Math.min(1.1, pitch + dy * 0.006)); }
    drag.x = event.clientX; drag.y = event.clientY; cameraUpdate();
  }
  function pointerUp(event) {
    const moved = drag?.moved; drag = null;
    if (moved || !renderer || !modelRoot || !camera || !raycaster) return;
    const rect = canvas.getBoundingClientRect();
    pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObject(modelRoot, true).find(item => item.object.isMesh);
    const matched = hit ? regionForAnatomyName(hit.object.userData.astName || hit.object.name) : null;
    if (matched) selectRegion(matched.id);
  }
  canvas.addEventListener('pointerdown', pointerDown);
  canvas.addEventListener('pointermove', pointerMove);
  canvas.addEventListener('pointerup', pointerUp);
  canvas.addEventListener('contextmenu', event => event.preventDefault());
  canvas.addEventListener('wheel', event => { event.preventDefault(); zoom = Math.max(2.0, Math.min(6.0, zoom + event.deltaY * 0.003)); cameraUpdate(); }, { passive: false });
  window.addEventListener('resize', resize);
  front.addEventListener('click', () => { posterior = false; yaw = 0; front.setAttribute('aria-pressed', 'true'); back.setAttribute('aria-pressed', 'false'); cameraUpdate(); });
  back.addEventListener('click', () => { posterior = true; yaw = 0; front.setAttribute('aria-pressed', 'false'); back.setAttribute('aria-pressed', 'true'); cameraUpdate(); });
  pan.addEventListener('click', () => { panMode = !panMode; pan.setAttribute('aria-pressed', String(panMode)); pan.textContent = `Pan mode ${panMode ? 'on' : 'off'}`; });
  zoomIn.addEventListener('click', () => { zoom = Math.max(2, zoom - 0.35); cameraUpdate(); });
  zoomOut.addEventListener('click', () => { zoom = Math.min(6, zoom + 0.35); cameraUpdate(); });
  reset.addEventListener('click', () => { yaw = 0; pitch = 0.03; zoom = 3.4; target?.set(0, 0, 0); posterior = false; panMode = false; front.setAttribute('aria-pressed', 'true'); back.setAttribute('aria-pressed', 'false'); pan.setAttribute('aria-pressed', 'false'); pan.textContent = 'Pan mode off'; cameraUpdate(); });
  regionSelect.addEventListener('change', () => selectRegion(regionSelect.value));
  exportButton.addEventListener('click', () => {
    const report = {
      report_type: 'ASTHRAL_ANATOMICAL_REGION_CONTEXT', generated_at_utc: new Date().toISOString(),
      region: { id: selectedRegion.id, name: selectedRegion.label, laterality: selectedRegion.laterality, system: selectedRegion.system },
      available_assessment: 'NO_LOCALIZED_ASSESSMENT_DATA_IN_CURRENT_CONTRACT', localized_findings: [], review_required: [],
      model: ANATOMY_MODEL, clinical_authority: false,
      limits: ['Model and mapping are educational navigation aids only.', 'System-level measurements are not localized.', 'Absence of regional data is not a normal finding.'],
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    const a = element('a', 'Download'); a.href = url; a.download = `asthral-region-${selectedRegion.id}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  cacheButton.addEventListener('click', async () => {
    cacheButton.disabled = true; dataStatus.textContent = 'Checking integrity and caching the optional anatomy model and renderer…';
    try { await cachePublicResources(['vendor/anatomy/']); dataStatus.textContent = 'Anatomical model assets cached and hash-verified for offline use. The model remains a non-clinical orientation aid.'; }
    catch (error) { dataStatus.textContent = `Offline anatomy install failed: ${error.message}. The 2D selector remains available.`; }
    finally { cacheButton.disabled = false; }
  });
  regionSelect.value = selectedRegion.id; currentModules(selectedRegion);
  const profileModeListener = event => { if (renderer) { renderer.setPixelRatio(Math.min(devicePixelRatio || 1, modelScale())); resize(); } else scheduleRender(); if (event.detail?.mode === 'CRITICAL') notice.textContent = 'CRITICAL resource profile · anatomy draws only on user interaction; essential monitoring and assessment remain available.'; };
  window.addEventListener('asthral:power-mode', profileModeListener);

  return {
    setVisible(value) { visible = Boolean(value); if (!visible && raf) { cancelAnimationFrame(raf); raf = 0; } else if (visible) scheduleRender(); },
    refresh: () => { resize(); scheduleRender(); },
    metrics: () => ({ render_calls: renderTotal, last_render_at_utc: lastRenderAt, mode: powerMode() }),
    destroy() {
      disposed = true; if (raf) cancelAnimationFrame(raf); resizeObserver?.disconnect(); window.removeEventListener('resize', resize); window.removeEventListener('asthral:power-mode', profileModeListener);
      disposeHighlighted();
      scene?.traverse(object => { object.geometry?.dispose?.(); if (Array.isArray(object.material)) object.material.forEach(material => material.dispose?.()); else object.material?.dispose?.(); });
      renderer?.renderLists?.dispose?.(); renderer?.dispose?.(); renderer?.forceContextLoss?.(); container.replaceChildren();
    },
  };
}
