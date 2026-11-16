import { cachePublicResources } from './public-resources.js';
import {
  ANATOMY_MODEL, ANATOMY_REGIONS, anatomyRegionMatches, regionForAnatomyName,
  resolveAnatomySurfaceRegion, regionIdFromBoneName,
} from './anatomy-regions.js';

export {
  ANATOMY_MODEL, ANATOMY_REGIONS, anatomyRegionMatches, regionForAnatomyName,
  resolveAnatomySurfaceRegion, regionIdFromBoneName,
} from './anatomy-regions.js';

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
  regionSelect.append(new Option('No region selected', ''));
  for (const item of ANATOMY_REGIONS) regionSelect.append(new Option(item.label, item.id));
  selectLabel.append(regionSelect);
  toolbar.append(front, back, pan, zoomIn, zoomOut, reset, selectLabel);

  const frame = element('div'); frame.className = 'anatomy-frame'; frame.setAttribute('aria-label', 'Interactive 3D external body map'); frame.dataset.selectedRegion = '';
  const canvas = document.createElement('canvas'); canvas.className = 'anatomy-canvas'; canvas.setAttribute('aria-label', 'Rotate, zoom, and select regions on the external human body surface');
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
  const selectedLine = element('p', 'No region selected. Select a visible body area or use the accessible region selector.'); selectedLine.id = 'anatomy-selected-region'; selectedLine.dataset.regionId = '';
  const dataLine = element('p', 'No localized health assessments, findings or review decisions are mapped to this anatomical region in the current data contract. Missing regional data do not indicate normal health.'); dataLine.className = 'anatomy-no-data';
  const recordLine = element('p', 'System-wide physiological measurements remain in Health Monitoring and are not attributed to this body region by this view.'); recordLine.className = 'anatomy-system-context';
  const timelineHeading = element('h3', 'Regional history');
  const timeline = element('p', 'No anatomically localized records are available to plot. No timepoints or trends are inferred.');
  const moduleList = element('div'); moduleList.className = 'anatomy-modules';
  const history = element('a', 'Open Health History'); history.href = '#history'; history.dataset.view = 'history';
  const neuro = element('a', 'Open NeuroGuard context'); neuro.href = '#neuroguard'; neuro.dataset.view = 'neuroguard';
  const exportButton = element('button', 'Export region context'); exportButton.type = 'button'; exportButton.disabled = true;
  const cacheButton = element('button', 'Install 3D model for offline use'); cacheButton.type = 'button';
  const dataStatus = element('p', 'The model is educational orientation context, not a diagnostic atlas or clinical localization tool.'); dataStatus.className = 'anatomy-data-status'; dataStatus.setAttribute('role', 'status');
  moduleList.append(history, neuro);
  context.append(heading, selectedLine, dataLine, recordLine, timelineHeading, timeline, moduleList, exportButton, cacheButton, dataStatus);
  const source = element('aside'); source.className = 'anatomy-source';
  const sourceTitle = element('h3', 'Model source & limits');
  const sourceText = element('p', 'Smooth external adult body model with male morphology; CC0 MakeHuman-derived asset from Innerscene. Bone weights and visible surface landmarks power region selection. The rig is invisible. This model is a navigation aid, not a diagnostic atlas, patient-specific representation or clinically validated localization system.');
  const sourceLink = element('a', 'View model provenance and attribution'); sourceLink.href = ANATOMY_MODEL.source; sourceLink.target = '_blank'; sourceLink.rel = 'noopener noreferrer';
  const dataSourceLink = element('a', 'Open NASA OSDR environmental data portal'); dataSourceLink.href = 'https://visualization.osdr.nasa.gov/eda/'; dataSourceLink.target = '_blank'; dataSourceLink.rel = 'noopener noreferrer';
  source.append(sourceTitle, sourceText, sourceLink, dataSourceLink);
  layout.append(context, source);
  root.append(toolbar, frame, legend, layout);
  container.replaceChildren(root);

  let THREE = null, renderer = null, scene = null, camera = null, modelRoot = null, anatomyModel = null;
  let resizeObserver = null, raycaster = null, pointer = null, raf = 0, renderTotal = 0, visible = true, disposed = false;
  let selectedRegion = null, posterior = false, panMode = false, drag = null, yaw = 0, pitch = 0.03, zoom = 3.4;
  let target = null, originalMaterials = new Map(), bodyMeshes = [], lastRenderAt = null, testSurfaceSamples = null;

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
  function highlightRegion(item) {
    selectedRegion = item;
    const id = item?.id ?? '';
    regionSelect.value = id; frame.dataset.selectedRegion = id; selectedLine.dataset.regionId = id;
    exportButton.disabled = !item;
    selectedLine.textContent = item
      ? item.label + ' · ' + item.system + ' · ' + (item.laterality === 'midline' ? 'midline / unspecified side' : item.laterality + ' side') + '. Selection is a navigation aid only.'
      : 'No region selected. The surface could not be matched to a supported region, or the interaction was outside the body map.';
    for (const mesh of bodyMeshes) {
      for (let i = 0; i < mesh.regionGroups.length; i++) {
        const group = mesh.geometry.groups[i], metadata = mesh.regionGroups[i];
        group.materialIndex = item && metadata.regionId === item.id ? mesh.highlightMaterialIndex : metadata.baseMaterialIndex;
      }
    }
    scheduleRender();
  }
  function currentModules(item) {
    moduleList.replaceChildren();
    const add = (label, href, description) => { const a = element('a', label); a.href = href; a.title = description; moduleList.append(a); };
    if (!item) return;
    if (/eye/.test(item.id)) add('OcularVision · image intake', '#vision', 'Open ocular image intake; no model diagnosis is available.');
    if (item.id === 'head') add('Well-being and cognitive monitoring', '#neuroguard', 'Open cognitive monitoring and well-being context.');
    if (item.id === 'chest') add('Cardiovascular monitoring', '#monitoring', 'Open systemic health monitoring.');
    if (item.id === 'abdomen') add('Nutrition and hydration', '#nutrition', 'Open recorded nutrition and hydration context.');
    if (item.id === 'face' || item.id.startsWith('left_') || item.id.startsWith('right_')) add('MotionGuard · movement research', '#exercise', 'Open optional local motion analysis; outputs are not localized findings.');
    if (['chest'].includes(item.id)) add('EchoVision · model unavailable', '#vision', 'Open the computer-vision module status.');
    if (['face', 'head'].includes(item.id)) add('SkinGuard · image intake', '#vision', 'Open image quality intake; no skin lesion model is available.');
    add('NeuroGuard · separate context', '#neuroguard', 'Cognitive and behavioral results are not anatomically localized.');
    add('Health History', '#history', 'Open source records without anatomically attributing system-level measurements.');
  }
  function selectRegion(value) {
    const item = ANATOMY_REGIONS.find(row => row.id === value) ?? null;
    highlightRegion(item); currentModules(item);
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
  function sourcePointFromWorld(worldPoint) {
    const point = worldPoint.clone();
    anatomyModel?.worldToLocal(point);
    return { x: point.x, y: point.y, z: point.z };
  }
  function weightedBonesAtVertex(mesh, vertex) {
    const indices = mesh.geometry.getAttribute('skinIndex'), weights = mesh.geometry.getAttribute('skinWeight');
    if (!indices || !weights || !mesh.skeleton) return [];
    const components = [indices.getX(vertex), indices.getY(vertex), indices.getZ(vertex), indices.getW(vertex)];
    const amounts = [weights.getX(vertex), weights.getY(vertex), weights.getZ(vertex), weights.getW(vertex)];
    return components.map((index, i) => [mesh.skeleton.bones[index]?.name, amounts[i]]).filter(([name, weight]) => name && weight > 0);
  }
  function regionAtHit(hit) {
    if (!hit?.object?.isSkinnedMesh) return null;
    // Regions are baked onto disjoint indexed faces. Ambiguous faces remain
    // unclassified, and picking never passes through the visible surface.
    const regionId = hit.object.regionByFace?.[hit.faceIndex] ?? null;
    return ANATOMY_REGIONS.find(region => region.id === regionId) ?? null;
  }
  function classifyMeshVertices(mesh) {
    const geometry = mesh.geometry, position = geometry.getAttribute('position');
    const regions = new Array(position.count).fill(null);
    const counts = Object.fromEntries(ANATOMY_REGIONS.map(item => [item.id, 0]));
    for (let i = 0; i < position.count; i++) {
      const point = { x: position.getX(i), y: position.getY(i), z: position.getZ(i) };
      const regionId = resolveAnatomySurfaceRegion(point, weightedBonesAtVertex(mesh, i));
      regions[i] = regionId;
      if (regionId) counts[regionId]++;
    }
    geometry.deleteAttribute('color');
    mesh.regionByVertex = regions;
    mesh.regionCounts = counts;
    bodyMeshes.push(mesh);
    return counts;
  }
  function segmentMeshFaces(mesh) {
    const geometry = mesh.geometry, sourceIndex = geometry.index;
    if (!sourceIndex || sourceIndex.count % 3) throw Error('External body mesh is missing indexed triangle geometry.');
    const materialForOffset = new Uint16Array(sourceIndex.count);
    for (const group of geometry.groups) materialForOffset.fill(group.materialIndex, group.start, group.start + group.count);
    if (!geometry.groups.length) materialForOffset.fill(0);
    const buckets = new Map(), vertexRegions = mesh.regionByVertex;
    for (let offset = 0; offset < sourceIndex.count; offset += 3) {
      const a = sourceIndex.getX(offset), b = sourceIndex.getX(offset + 1), c = sourceIndex.getX(offset + 2);
      const candidate = vertexRegions[a];
      const regionId = candidate && vertexRegions[b] === candidate && vertexRegions[c] === candidate ? candidate : null;
      const baseMaterialIndex = materialForOffset[offset];
      const key = `${baseMaterialIndex}:${regionId ?? ''}`;
      let bucket = buckets.get(key);
      if (!bucket) { bucket = { baseMaterialIndex, regionId, indices: [] }; buckets.set(key, bucket); }
      bucket.indices.push(a, b, c);
    }
    const IndexArray = sourceIndex.array.constructor, reordered = new IndexArray(sourceIndex.count);
    const regionByFace = [], regionFaceCounts = Object.fromEntries(ANATOMY_REGIONS.map(item => [item.id, 0]));
    mesh.regionGroups = [];
    geometry.clearGroups();
    let cursor = 0;
    for (const bucket of buckets.values()) {
      reordered.set(bucket.indices, cursor);
      geometry.addGroup(cursor, bucket.indices.length, bucket.baseMaterialIndex);
      mesh.regionGroups.push({ regionId: bucket.regionId, baseMaterialIndex: bucket.baseMaterialIndex });
      const triangleCount = bucket.indices.length / 3;
      for (let i = 0; i < triangleCount; i++) regionByFace.push(bucket.regionId);
      if (bucket.regionId) regionFaceCounts[bucket.regionId] += triangleCount;
      cursor += bucket.indices.length;
    }
    geometry.setIndex(new THREE.BufferAttribute(reordered, 1));
    mesh.regionByFace = regionByFace;
    mesh.regionFaceCounts = regionFaceCounts;
    return regionFaceCounts;
  }
  function hitAtClientPoint(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height || clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) return null;
    pointer.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    camera.updateMatrixWorld(true);
    raycaster.setFromCamera(pointer, camera);
    return raycaster.intersectObject(modelRoot, true).find(hit => hit.object.isMesh) ?? null;
  }
  function installAnatomyTestHooks() {
    if (!new URLSearchParams(location.search).has('anatomy-e2e')) return;
    window.__ASTHRAL_ANATOMY_TEST__ = {
      regions: () => ANATOMY_REGIONS.map(item => item.id),
      coverage: () => Object.fromEntries(ANATOMY_REGIONS.map(item => [item.id,
        bodyMeshes.reduce((sum, mesh) => sum + mesh.regionFaceCounts[item.id], 0)])),
      highlightedTriangles: () => {
        const counts = Object.fromEntries(ANATOMY_REGIONS.map(item => [item.id, 0]));
        for (const mesh of bodyMeshes) {
          for (let i = 0; i < mesh.regionGroups.length; i++) {
            const group = mesh.geometry.groups[i], metadata = mesh.regionGroups[i];
            if (metadata.regionId && group.materialIndex === mesh.highlightMaterialIndex) counts[metadata.regionId] += group.count / 3;
          }
        }
        return counts;
      },
      surfacePointSamples: (regionId, limit = 24) => {
        if (!testSurfaceSamples) {
          testSurfaceSamples = Object.fromEntries([...ANATOMY_REGIONS.map(item => item.id), 'unclassified'].map(id => [id, []]));
          for (const mesh of bodyMeshes) {
            const index = mesh.geometry.index, regions = mesh.regionByVertex, faceRegions = mesh.regionByFace;
            if (!index) continue;
            const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
            for (let face = 0; face < faceRegions.length; face++) {
              const offset = face * 3, id = faceRegions[face] ?? 'unclassified';
              const ia = index.getX(offset), ib = index.getX(offset + 1), ic = index.getX(offset + 2);
              if (id !== 'unclassified' && (regions[ia] !== id || regions[ib] !== id || regions[ic] !== id)) continue;
              mesh.getVertexPosition(ia, a); mesh.localToWorld(a);
              mesh.getVertexPosition(ib, b); mesh.localToWorld(b);
              mesh.getVertexPosition(ic, c); mesh.localToWorld(c);
              const centroid = a.add(b).add(c).multiplyScalar(1 / 3);
              anatomyModel.worldToLocal(centroid);
              testSurfaceSamples[id].push({ x: centroid.x, y: centroid.y, z: centroid.z });
            }
          }
          for (const points of Object.values(testSurfaceSamples)) points.sort((a, b) => b.z - a.z);
        }
        const candidates = [...(testSurfaceSamples[regionId] ?? [])];
        camera.updateMatrixWorld(true);
        const eye = anatomyModel.worldToLocal(camera.getWorldPosition(new THREE.Vector3()));
        const visibility = point => point.x * eye.x + point.y * eye.y + point.z * eye.z;
        candidates.sort((a, b) => visibility(b) - visibility(a));
        const count = Math.min(Math.max(1, limit), candidates.length);
        return Array.from({ length: count }, (_, i) => candidates[Math.floor(i * (candidates.length - 1) / Math.max(count - 1, 1))]);
      },
      projectSourcePoint: ([x, y, z]) => {
        camera.updateMatrixWorld(true); anatomyModel.updateMatrixWorld(true);
        const projected = anatomyModel.localToWorld(new THREE.Vector3(x, y, z)).project(camera);
        const rect = canvas.getBoundingClientRect();
        return { x: rect.left + (projected.x + 1) * rect.width / 2, y: rect.top + (1 - projected.y) * rect.height / 2 };
      },
      resolveAtClientPoint: (x, y) => {
        const hit = hitAtClientPoint(x, y);
        return hit ? { regionId: regionAtHit(hit)?.id ?? null, objectName: hit.object.name, point: sourcePointFromWorld(hit.point), faceIndex: hit.faceIndex } : null;
      },
      selection: () => ({ regionId: frame.dataset.selectedRegion, dropdown: regionSelect.value, context: selectedLine.dataset.regionId }),
    };
  }

  try {
    const [{ GLTFLoader }, three] = await Promise.all([
      import('./vendor/anatomy/GLTFLoader.js'), import('./vendor/orbit/three.module.js'),
    ]);
    THREE = three;
    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: powerMode() === 'FULL', powerPreference: powerMode() === 'FULL' ? 'default' : 'low-power' });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, modelScale())); renderer.setClearColor(0x071522, 0);
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(33, 1, 0.01, 100);
    scene.add(new THREE.HemisphereLight(0xd9f1ff, 0x171e25, 1.65));
    const key = new THREE.DirectionalLight(0xffe6cf, 2.3); key.position.set(-2.7, 3.4, 3.6); scene.add(key);
    const fill = new THREE.DirectionalLight(0x7cb8d2, 1.1); fill.position.set(3.4, 0.9, -3); scene.add(fill);
    modelRoot = new THREE.Group(); scene.add(modelRoot);
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(ANATOMY_MODEL.asset);
    anatomyModel = gltf.scene; anatomyModel.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(anatomyModel), center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
    anatomyModel.position.set(-center.x, -center.y, -center.z);
    modelRoot.scale.setScalar(1.62 / Math.max(size.y, 0.01));
    modelRoot.add(anatomyModel);
    modelRoot.updateMatrixWorld(true);
    const regionCoverage = Object.fromEntries(ANATOMY_REGIONS.map(item => [item.id, 0]));
    anatomyModel.traverse(object => {
      if (!object.isSkinnedMesh || !object.geometry.getAttribute('skinIndex') || !object.geometry.getAttribute('skinWeight')) return;
      originalMaterials.set(object, object.material);
      const stylize = (material, color = '#bdcbd3') => {
        const clone = material.clone();
        clone.color?.set(color);
        clone.roughness = 0.84; clone.metalness = 0; clone.vertexColors = false;
        return clone;
      };
      const original = object.material;
      const baseMaterials = Array.isArray(original) ? original.map(material => stylize(material)) : [stylize(original)];
      const highlightMaterial = stylize(Array.isArray(original) ? original[0] : original, '#27b7d4');
      highlightMaterial.emissive?.set('#084455');
      highlightMaterial.emissiveIntensity = 0.3;
      object.material = [...baseMaterials, highlightMaterial];
      object.highlightMaterialIndex = baseMaterials.length;
      classifyMeshVertices(object);
      const counts = segmentMeshFaces(object);
      for (const item of ANATOMY_REGIONS) regionCoverage[item.id] += counts[item.id];
      object.frustumCulled = true;
    });
    target = new THREE.Vector3(0, 0, 0); raycaster = new THREE.Raycaster(); pointer = new THREE.Vector2();
    cameraUpdate();
    resizeObserver = new ResizeObserver(resize); resizeObserver.observe(frame); resize();
    fallback.hidden = true; canvas.hidden = false; notice.textContent = 'External body map loaded. Drag to rotate · wheel or pinch to zoom · pan mode moves the view.';
    selectRegion(regionSelect.value);
    installAnatomyTestHooks();
    const unmapped = Object.entries(regionCoverage).filter(([, count]) => count < 1).map(([id]) => id);
    status('3D external body map loaded · ' + ANATOMY_MODEL.name + ' · ' + (28 - unmapped.length) + '/28 regions represented in the surface mesh · orientation only; no clinical localization is inferred.');
    if (unmapped.length) dataStatus.textContent = 'Some regions have no mapped surface vertices in this model: ' + unmapped.join(', ') + '. Use the selector for navigation only.';
  } catch (error) {
    createFallback(error.message || '3D model loading failed.');
    status('3D anatomy unavailable · 2D region selector remains usable · no clinical result was produced.');
  }

  function pointerDown(event) {
    if (!renderer || !canvas) return;
    drag = { id: event.pointerId, pointerType: event.pointerType, startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY, moved: false, pan: panMode || event.shiftKey || event.button === 2 };
    canvas.setPointerCapture(event.pointerId);
  }
  function pointerMove(event) {
    if (!drag || event.pointerId !== drag.id) return;
    let dx = event.clientX - drag.x, dy = event.clientY - drag.y;
    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) >= (drag.pointerType === 'touch' ? 8 : 5)) {
      drag.moved = true; dx = event.clientX - drag.startX; dy = event.clientY - drag.startY;
    }
    if (!drag.moved) { drag.x = event.clientX; drag.y = event.clientY; return; }
    if (drag.pan && camera && target) {
      const scale = zoom / Math.max(frame.getBoundingClientRect().height, 1);
      target.x -= dx * scale; target.y += dy * scale;
    } else { yaw -= dx * 0.008; pitch = Math.max(-1.1, Math.min(1.1, pitch + dy * 0.006)); }
    drag.x = event.clientX; drag.y = event.clientY; cameraUpdate();
  }
  function pointerUp(event) {
    if (!drag || event.pointerId !== drag.id) return;
    const moved = drag.moved;
    try { if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId); } catch {}
    drag = null;
    if (moved || !renderer || !modelRoot || !camera || !raycaster) return;
    const hit = hitAtClientPoint(event.clientX, event.clientY);
    const matched = hit ? regionAtHit(hit) : null;
    selectRegion(matched?.id ?? '');
  }
  canvas.addEventListener('pointerdown', pointerDown);
  canvas.addEventListener('pointermove', pointerMove);
  canvas.addEventListener('pointerup', pointerUp);
  canvas.addEventListener('pointercancel', event => { if (drag?.id === event.pointerId) drag = null; });
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
    if (!selectedRegion) return;
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
  regionSelect.value = selectedRegion?.id ?? ''; currentModules(selectedRegion);
  const profileModeListener = event => { if (renderer) { renderer.setPixelRatio(Math.min(devicePixelRatio || 1, modelScale())); resize(); } else scheduleRender(); if (event.detail?.mode === 'CRITICAL') notice.textContent = 'CRITICAL resource profile · anatomy draws only on user interaction; essential monitoring and assessment remain available.'; };
  window.addEventListener('asthral:power-mode', profileModeListener);

  return {
    setVisible(value) { visible = Boolean(value); if (!visible && raf) { cancelAnimationFrame(raf); raf = 0; } else if (visible) scheduleRender(); },
    refresh: () => { resize(); scheduleRender(); },
    metrics: () => ({ render_calls: renderTotal, last_render_at_utc: lastRenderAt, mode: powerMode() }),
    destroy() {
      disposed = true; if (raf) cancelAnimationFrame(raf); resizeObserver?.disconnect(); window.removeEventListener('resize', resize); window.removeEventListener('asthral:power-mode', profileModeListener);
      scene?.traverse(object => { object.geometry?.dispose?.(); if (Array.isArray(object.material)) object.material.forEach(material => material.dispose?.()); else object.material?.dispose?.(); });
      for (const original of originalMaterials.values()) {
        if (Array.isArray(original)) original.forEach(material => material.dispose?.());
        else original?.dispose?.();
      }
      if (window.__ASTHRAL_ANATOMY_TEST__) delete window.__ASTHRAL_ANATOMY_TEST__;
      renderer?.renderLists?.dispose?.(); renderer?.dispose?.(); renderer?.forceContextLoss?.(); container.replaceChildren();
    },
  };
}
