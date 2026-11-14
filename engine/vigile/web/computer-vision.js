'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const state = { status: null, ocular: null, echo: null, motion: null, ocularHistory: [], echoHistory: [], motionHistory: [], objectUrls: {}, stream: null, recorder: null, cameraChunks: [], cameraBlob: null, cameraTimer: null };
  const labels = {
    MODEL_NOT_CONFIGURED: 'No compatible trained model is installed. No predictions are generated.',
    MODEL_NOT_AVAILABLE: 'The model asset is missing. Install it with the documented setup command.',
    DEPENDENCY_MISSING: 'The model file is present, but its optional runtime dependency is missing.',
    MODEL_INSTALLED_NOT_LOADED: 'Model weights and runtime are installed. They load on the first analysis.',
    MODEL_OPERATIVE: 'Model loaded and available for experimental inference.',
    INFERENCE_ERROR: 'The last inference failed. Check model and input compatibility before retrying.',
    MODEL_LOAD_ERROR: 'Model weights could not be loaded. Check the checkpoint and version manifest.'
  };
  const errorText = code => ({
    INVALID_IMAGE_DATA_URL: 'The image could not be read. Choose a valid image and try again.',
    INVALID_OR_CORRUPT_OCT_IMAGE: 'The selected OCT image is corrupt or unsupported.',
    IMAGE_TOO_LARGE: 'The image exceeds the 10 MB limit.',
    VIDEO_TOO_LARGE: 'The video exceeds the 9 MB limit.',
    VIDEO_DECODER_CANNOT_OPEN_FILE: 'The local video decoder could not open this file.',
    VIDEO_HAS_NO_VALID_FRAMES: 'The video contains no readable frames.',
    VIDEO_DURATION_OR_FRAME_LIMIT_EXCEEDED: 'The clip exceeds the 20 second or 600 frame limit.',
    REDUCE_VIDEO_LENGTH_OR_INCREASE_FRAME_STRIDE: 'Increase the frame interval or choose a shorter clip.',
    COMPUTER_VISION_BUSY: 'Another computer-vision analysis is in progress. Try again in a moment.',
    ECHOVISION_REQUIRES_USER_CONFIRMATION_OF_APICAL_4_CHAMBER_VIEW: 'Confirm that the video is an apical four-chamber echocardiogram (A4C).',
    SESSION_EXPIRED_OR_REQUIRED: 'The portal session expired. Sign in again before processing media.',
    OCT_MODEL_NOT_AVAILABLE: 'The OCT segmentation checkpoint is missing. See the model installation instructions.',
    ECHONET_SEGMENTATION_WEIGHTS_NOT_AVAILABLE: 'The EchoNet LV segmentation checkpoint is missing.',
    HOLISTIC_MODEL_ASSET_NOT_AVAILABLE: 'The MediaPipe Holistic model asset is missing.',
    INFERENCE_MEMORY_LIMIT_EXCEEDED: 'The analysis exceeded available memory. Choose a shorter clip or smaller image.',
    OPENCV_DEPENDENCY_MISSING: 'OpenCV is not installed in the project environment.'
  })[code] || `${code || 'The analysis failed.'}`;

  function setStatus(module, stateValue, detail) {
    const stateNode = $(`${module}-state`);
    const statusNode = $(`${module}-status`);
    if (!stateNode || !statusNode) return;
    stateNode.textContent = stateValue || 'UNKNOWN';
    statusNode.replaceChildren();
    const summary = document.createElement('p');
    summary.textContent = labels[stateValue] || (detail?.analysis_available ? 'Model runtime and weights are available for experimental analysis.' : 'Model status could not be confirmed.');
    statusNode.append(summary);
    if (detail?.name) {
      const line = document.createElement('small');
      line.textContent = `${detail.name}${detail.version ? ` · ${detail.version}` : ''}`;
      statusNode.append(line);
    }
    if (detail?.provenance || detail?.license) {
      const disclosure = document.createElement('details');
      const title = document.createElement('summary');
      title.textContent = 'Model provenance and terms';
      const text = document.createElement('p');
      text.textContent = [detail.provenance, detail.license, detail.input ? `Inputs: ${detail.input.join(', ')}` : '', detail.output ? `Output: ${detail.output}` : ''].filter(Boolean).join(' ');
      disclosure.append(title, text);
      statusNode.append(disclosure);
    }
  }

  async function refreshStatus() {
    try {
      const response = await fetch('/api/computer-vision/status', { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `STATUS_${response.status}`);
      state.status = data;
      for (const [key, panel] of [['skinguard', 'skinguard'], ['ocularvision', 'ocular'], ['echovision', 'echo'], ['motionguard', 'motion']]) {
        const detail = data.modules[key];
        setStatus(panel, detail?.state, detail);
      }
    } catch (error) {
      for (const panel of ['ocular', 'echo', 'motion']) setStatus(panel, 'STATUS_UNAVAILABLE', null);
    }
  }

  async function post(path, body) {
    const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, cache: 'no-store', body: JSON.stringify(body) });
    let result = {};
    try { result = await response.json(); } catch (_) {}
    if (response.status === 401) {
      $('login').hidden = false;
      $('workspace').hidden = true;
      throw new Error(errorText('SESSION_EXPIRED_OR_REQUIRED'));
    }
    if (!response.ok) throw new Error(errorText(result.detail) || `Analysis failed (${response.status}).`);
    return result;
  }

  function fileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const payload = String(reader.result).split(',').slice(1).join(',');
        const extension = file.name.split('.').pop()?.toLowerCase();
        const byExtension = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp', tif: 'image/tiff', tiff: 'image/tiff', mp4: 'video/mp4', webm: 'video/webm', mov: 'video/quicktime', avi: 'video/x-msvideo', mkv: 'video/x-matroska' };
        let mime = String(file.type || '').split(';')[0].toLowerCase();
        if (!mime || mime === 'application/octet-stream' || mime === 'video/avi') mime = byExtension[extension] || mime;
        if (mime === 'image/jpg') mime = 'image/jpeg';
        resolve(`data:${mime};base64,${payload}`);
      };
      reader.onerror = () => reject(new Error('The selected file could not be read.'));
      reader.readAsDataURL(file);
    });
  }

  function showFilePreview(file, videoId, key) {
    if (state.objectUrls[key]) URL.revokeObjectURL(state.objectUrls[key]);
    if (!file) return;
    const url = URL.createObjectURL(file);
    state.objectUrls[key] = url;
    const node = $(videoId);
    node.src = url;
    node.hidden = false;
  }

  function setImage(id, base64, type = 'image/png') {
    const node = $(id);
    if (!base64) { node.hidden = true; node.removeAttribute('src'); return; }
    node.src = `data:${type};base64,${base64}`;
    node.hidden = false;
  }

  function mediaBlob(base64, type) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new Blob([bytes], { type });
  }

  function showExportVideo(id, data) {
    const node = $(id);
    if (!data) { node.hidden = true; node.removeAttribute('src'); return; }
    const key = `${id}-export`;
    if (state.objectUrls[key]) URL.revokeObjectURL(state.objectUrls[key]);
    const url = URL.createObjectURL(mediaBlob(data, 'video/mp4'));
    state.objectUrls[key] = url;
    node.src = url;
    node.hidden = false;
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function downloadJSON(report, filename) {
    downloadBlob(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }), filename);
  }

  function cleanReport(report) {
    const output = { ...report };
    delete output.overlay_video_base64;
    delete output.overlay_frame_jpeg_base64;
    delete output.mask_png_base64;
    return output;
  }

  function addMetric(target, title, value, note = '') {
    const box = document.createElement('div');
    box.className = 'vision-metric';
    const strong = document.createElement('strong');
    strong.textContent = title;
    const content = document.createElement('span');
    content.textContent = value === null || value === undefined ? 'Not available' : String(value);
    box.append(strong, content);
    if (note) { const small = document.createElement('small'); small.textContent = note; box.append(small); }
    target.append(box);
  }

  function drawProfile(canvas, values, label) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !values?.length) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.floor(rect.width * ratio));
    canvas.height = Math.max(1, Math.floor(180 * ratio));
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height, pad = 24 * ratio;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = '#e1e3ec'; ctx.lineWidth = ratio;
    for (let i = 0; i < 4; i++) { const y = pad + (h - 2 * pad) * i / 3; ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke(); }
    const finite = values.map(Number).filter(Number.isFinite);
    if (!finite.length) return;
    let min = Math.min(...finite), max = Math.max(...finite);
    if (max === min) max = min + 1;
    ctx.strokeStyle = '#6854ce'; ctx.lineWidth = 2.2 * ratio; ctx.beginPath();
    values.forEach((value, index) => {
      const x = pad + (w - 2 * pad) * index / Math.max(1, values.length - 1);
      const y = h - pad - (h - 2 * pad) * (Number(value) - min) / (max - min);
      if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.fillStyle = '#565e70'; ctx.font = `${10 * ratio}px Segoe UI, Arial`;
    ctx.fillText(`${label} · ${max.toFixed(1)} max / ${min.toFixed(1)} min`, pad, 14 * ratio);
  }

  function compatibleOcular(a, b) {
    return a?.model === b?.model && a?.image?.width === b?.image?.width && a?.image?.height === b?.image?.height && a?.image?.pixel_spacing_um === b?.image?.pixel_spacing_um;
  }

  async function drawOcularOverlay() {
    if (!state.ocular) return;
    const result = state.ocular, sourceUrl = state.objectUrls.ocularOriginal;
    const canvas = $('ocular-overlay-canvas'), width = result.image.width, height = result.image.height;
    if (!sourceUrl || !width || !height) return;
    const source = new Image(), maskImage = new Image();
    const sourceReady = new Promise((resolve, reject) => { source.onload = resolve; source.onerror = reject; });
    const maskReady = new Promise((resolve, reject) => { maskImage.onload = resolve; maskImage.onerror = reject; });
    source.src = sourceUrl; maskImage.src = `data:image/png;base64,${result.mask_png_base64}`;
    await Promise.all([sourceReady, maskReady]);
    canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(source, 0, 0, width, height);
    const pixels = ctx.getImageData(0, 0, width, height);
    const maskCanvas = document.createElement('canvas'); maskCanvas.width = width; maskCanvas.height = height;
    const maskCtx = maskCanvas.getContext('2d', { willReadFrequently: true }); maskCtx.drawImage(maskImage, 0, 0, width, height);
    const mask = maskCtx.getImageData(0, 0, width, height).data;
    const enabled = new Set([...$('ocular-layer-controls').querySelectorAll('input:checked')].map(input => Number(input.value)));
    const colors = [[0, 0, 0], [230, 75, 75], [250, 155, 60], [230, 205, 65], [80, 180, 110], [65, 170, 210], [95, 110, 230], [180, 95, 205]];
    for (let offset = 0; offset < mask.length; offset += 4) {
      const klass = mask[offset];
      if (klass > 0 && klass < 8 && enabled.has(klass)) {
        const color = colors[klass];
        pixels.data[offset] = Math.round(.55 * pixels.data[offset] + .45 * color[0]);
        pixels.data[offset + 1] = Math.round(.55 * pixels.data[offset + 1] + .45 * color[1]);
        pixels.data[offset + 2] = Math.round(.55 * pixels.data[offset + 2] + .45 * color[2]);
      }
    }
    ctx.putImageData(pixels, 0, 0);
  }

  function renderOcularLayerControls() {
    const target = $('ocular-layer-controls'); target.replaceChildren();
    for (let index = 1; index <= 7; index++) {
      const label = document.createElement('label'); label.className = 'layer-toggle';
      const input = document.createElement('input'); input.type = 'checkbox'; input.value = String(index); input.checked = true;
      input.addEventListener('change', () => drawOcularOverlay().catch(() => {}));
      const text = document.createElement('span'); text.textContent = `Region ${index}`;
      label.append(input, text); target.append(label);
    }
  }

  function updateOcularComparison() {
    const select = $('ocular-compare');
    const old = select.value;
    select.replaceChildren(new Option('No comparison', ''));
    state.ocularHistory.forEach(item => select.append(new Option(`${new Date(item.created_at).toLocaleString()} · ${item.image.width}×${item.image.height}`, item.analysis_id)));
    if ([...select.options].some(option => option.value === old)) select.value = old;
    const target = $('ocular-comparison');
    target.replaceChildren();
    const previous = state.ocularHistory.find(item => item.analysis_id === select.value);
    if (!previous || !state.ocular) return;
    if (!compatibleOcular(previous, state.ocular)) {
      target.textContent = 'These analyses have different dimensions or pixel spacing; no quantitative longitudinal comparison is calculated.';
      return;
    }
    const before = previous.retinal_span_profile_px || [];
    const now = state.ocular.retinal_span_profile_px || [];
    if (before.length !== now.length || !before.length) return;
    const meanDelta = now.reduce((sum, value, index) => sum + value - before[index], 0) / now.length;
    target.textContent = `Descriptive profile difference: mean ${meanDelta.toFixed(2)} pixels across ${now.length} columns. This is an image comparison, not clinical change.`;
    target.className = 'vision-comparison';
    const previousImage = document.createElement('img');
    previousImage.alt = 'Previous analysis overlay stored in this browser session';
    previousImage.src = `data:image/png;base64,${previous.overlay_png_base64}`;
    previousImage.style.width = 'min(100%, 540px)';
    target.append(previousImage);
  }

  $('ocular-file').addEventListener('change', () => {
    const file = $('ocular-file').files?.[0];
    if (!file) return;
    if (state.objectUrls.ocularOriginal) URL.revokeObjectURL(state.objectUrls.ocularOriginal);
    state.objectUrls.ocularOriginal = URL.createObjectURL(file);
    $('ocular-original').src = state.objectUrls.ocularOriginal;
    $('ocular-original').hidden = false;
  });
  $('ocular-form').addEventListener('submit', async event => {
    event.preventDefault();
    const file = $('ocular-file').files?.[0];
    if (!file) return;
    const button = $('ocular-submit'); button.disabled = true;
    $('ocular-status').textContent = 'Validating the B-scan and loading the segmentation model on the local computer…';
    $('ocular-results').hidden = true;
    try {
      if (file.size > 10 * 1024 * 1024) throw new Error(errorText('IMAGE_TOO_LARGE'));
      const result = await post('/api/computer-vision/ocular/analyze', { image_data: await fileAsDataUrl(file), pixel_spacing_um: $('ocular-scale').value ? Number($('ocular-scale').value) : null });
      state.ocular = result;
      state.ocularHistory.unshift(result);
      setImage('ocular-overlay', result.overlay_png_base64);
      $('ocular-results').hidden = false;
      renderOcularLayerControls();
      await drawOcularOverlay();
      const metrics = $('ocular-metrics'); metrics.replaceChildren();
      addMetric(metrics, 'B-scan dimensions', `${result.image.width} × ${result.image.height}`, `Source: ${result.image.format} · orientation ${result.image.exif_orientation}`);
      addMetric(metrics, 'Mean retinal span', `${(result.retinal_span_profile_px.reduce((a, b) => a + b, 0) / result.retinal_span_profile_px.length).toFixed(2)} px`, result.image.pixel_spacing_um ? `Scale: ${result.image.pixel_spacing_um} µm/px` : 'No calibration supplied');
      for (const layer of result.layers) addMetric(metrics, layer.label, `${layer.mean_thickness_px} px`, layer.mean_thickness_um === null ? 'No physical scale supplied' : `${layer.mean_thickness_um} µm`);
      drawProfile($('ocular-profile'), result.retinal_span_profile_um || result.retinal_span_profile_px, result.retinal_span_profile_um ? 'Retinal span (µm)' : 'Retinal span (pixels)');
      updateOcularComparison();
      $('ocular-status').textContent = `Experimental segmentation completed with ${result.model}. No SANS or clinical diagnosis was inferred.`;
      $('ocular-report').onclick = () => {
        downloadJSON(cleanReport(result), `asthral-ocularvision-${result.analysis_id}.json`);
        downloadBlob(mediaBlob(result.mask_png_base64, 'image/png'), `asthral-ocularvision-${result.analysis_id}-mask.png`);
        downloadBlob(mediaBlob(result.overlay_png_base64, 'image/png'), `asthral-ocularvision-${result.analysis_id}-overlay.png`);
      };
    } catch (error) { $('ocular-status').textContent = error.message; }
    finally { button.disabled = false; }
  });
  $('ocular-compare').addEventListener('change', updateOcularComparison);
  $('ocular-clear').addEventListener('click', () => {
    if (state.objectUrls.ocularOriginal) URL.revokeObjectURL(state.objectUrls.ocularOriginal);
    state.objectUrls.ocularOriginal = null;
    $('ocular-form').reset(); $('ocular-original').hidden = $('ocular-overlay').hidden = true;
    $('ocular-results').hidden = true; $('ocular-compare').replaceChildren(new Option('No comparison', ''));
    $('ocular-comparison').replaceChildren(); state.ocular = null; state.ocularHistory = [];
    $('ocular-status').textContent = 'Files and analyses cleared from this browser session.';
  });

  $('echo-file').addEventListener('change', () => showFilePreview($('echo-file').files?.[0], 'echo-original', 'echoOriginal'));
  $('echo-form').addEventListener('submit', async event => {
    event.preventDefault();
    const file = $('echo-file').files?.[0];
    if (!file) return;
    const button = $('echo-submit'); button.disabled = true;
    $('echo-status').textContent = 'Decoding frames and running the local LV segmentation model…'; $('echo-results').hidden = true;
    try {
      if (file.size > 9 * 1024 * 1024) throw new Error(errorText('VIDEO_TOO_LARGE'));
      if (!$('echo-a4c').checked) throw new Error(errorText('ECHOVISION_REQUIRES_USER_CONFIRMATION_OF_APICAL_4_CHAMBER_VIEW'));
      const result = await post('/api/computer-vision/echo/analyze', {
        video_data: await fileAsDataUrl(file), filename: file.name, confirm_a4c: true,
        rotation: Number($('echo-rotation').value), mirror: $('echo-mirror').checked,
        frame_stride: Number($('echo-stride').value)
      });
      state.echo = result;
      state.echoHistory.unshift({ analysis_id: result.analysis_id, created_at: result.created_at, video: result.video, sampled_frames: result.sampled_frames, model: result.model });
      setImage('echo-overlay-frame', result.overlay_frame_jpeg_base64, 'image/jpeg');
      showExportVideo('echo-overlay-video', result.overlay_video_base64);
      $('echo-results').hidden = false;
      drawEchoProfile($('echo-profile'), result);
      const metrics = $('echo-metrics'); metrics.replaceChildren();
      addMetric(metrics, 'Decoded frames', result.video.decoded_frames, `${result.video.duration_seconds} seconds · ${result.video.fps.toFixed(2)} frames/s`);
      addMetric(metrics, 'Frames analyzed', result.sampled_frames.length, `Every ${result.parameters.frame_stride} frames`);
      addMetric(metrics, 'Mean segmented area', `${(result.sampled_frames.reduce((sum, row) => sum + row.lv_area_pixels_transformed, 0) / result.sampled_frames.length).toFixed(1)} px`, 'Image pixels only; not a volume');
      addMetric(metrics, 'Overlay video', result.overlay_video_exported ? 'Ready' : 'Too large to export', result.overlay_video_exported ? 'Generated in temporary storage and removed after response' : 'Still-frame mask and JSON report remain available');
      updateEchoComparison();
      $('echo-status').textContent = 'LV segmentation completed on selected frames. This is not a validated clinical measurement.';
      $('echo-report').onclick = () => {
        downloadJSON(cleanReport(result), `asthral-echovision-${result.analysis_id}.json`);
        if (result.mask_png_base64) downloadBlob(mediaBlob(result.mask_png_base64, 'image/png'), `asthral-echovision-${result.analysis_id}-mask.png`);
        if (result.overlay_video_base64) downloadBlob(mediaBlob(result.overlay_video_base64, 'video/mp4'), `asthral-echovision-${result.analysis_id}-overlay.mp4`);
      };
    } catch (error) { $('echo-status').textContent = error.message; }
    finally { button.disabled = false; }
  });
  $('echo-compare').addEventListener('change', updateEchoComparison);
  $('echo-overlay-toggle').addEventListener('change', () => {
    $('echo-overlay-video').hidden = !$('echo-overlay-toggle').checked || !state.echo?.overlay_video_base64;
    $('echo-overlay-frame').hidden = !$('echo-overlay-toggle').checked || !state.echo?.overlay_frame_jpeg_base64;
  });
  function updateEchoComparison() {
    const select = $('echo-compare'), old = select.value;
    select.replaceChildren(new Option('No comparison', ''));
    state.echoHistory.forEach(item => select.append(new Option(`${new Date(item.created_at).toLocaleString()} · ${item.video.decoded_frames} frames`, item.analysis_id)));
    if ([...select.options].some(option => option.value === old)) select.value = old;
    const previous = state.echoHistory.find(item => item.analysis_id === select.value);
    const target = $('echo-comparison'); target.replaceChildren();
    if (!previous || !state.echo) return;
    const previousAspect = previous.video.width / previous.video.height, currentAspect = state.echo.video.width / state.echo.video.height;
    const compatible = previous.model === state.echo.model && previous.video.user_confirmed_apical_4_chamber && state.echo.video.user_confirmed_apical_4_chamber
      && previous.video.rotation_degrees === state.echo.video.rotation_degrees
      && previous.video.mirrored_for_inference === state.echo.video.mirrored_for_inference
      && Math.abs(previousAspect - currentAspect) < 0.02;
    if (!compatible) { target.textContent = 'The two analyses do not share a compatible model/view. No sequence comparison is shown.'; return; }
    const means = item => item.sampled_frames.map(frame => frame.lv_area_pixels_transformed / (item.video.width * item.video.height));
    const oldMean = means(previous).reduce((a, b) => a + b, 0) / Math.max(1, previous.sampled_frames.length);
    const newMean = means(state.echo).reduce((a, b) => a + b, 0) / Math.max(1, state.echo.sampled_frames.length);
    target.className = 'vision-comparison';
    target.textContent = `Descriptive mean segmented-area fraction: earlier ${(oldMean * 100).toFixed(2)}% · current ${(newMean * 100).toFixed(2)}%. Different acquisition conditions can explain changes; this is not cardiac function or clinical change.`;
  }

  function drawEchoProfile(canvas, result) {
    const rect = canvas.getBoundingClientRect(); if (!rect.width || !result.sampled_frames?.length) return;
    const ratio = window.devicePixelRatio || 1; canvas.width = rect.width * ratio; canvas.height = 180 * ratio;
    const ctx = canvas.getContext('2d'), w = canvas.width, h = canvas.height, pad = 25 * ratio;
    ctx.clearRect(0, 0, w, h); ctx.strokeStyle = '#e1e3ec'; ctx.lineWidth = ratio;
    for (let i = 0; i < 4; i++) { const y = pad + (h - 2 * pad) * i / 3; ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke(); }
    const values = result.sampled_frames.map(frame => frame.lv_area_pixels_transformed / (result.video.width * result.video.height));
    const max = Math.max(...values, 0.001);
    ctx.strokeStyle = '#6854ce'; ctx.lineWidth = 2 * ratio; ctx.beginPath();
    values.forEach((value, index) => {
      const x = pad + (w - 2 * pad) * index / Math.max(1, values.length - 1);
      const y = h - pad - (h - 2 * pad) * value / max;
      if (!index) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }); ctx.stroke();
    ctx.fillStyle = '#565e70'; ctx.font = `${10 * ratio}px Segoe UI, Arial`;
    ctx.fillText('LV segmented-area fraction · not volume or ejection fraction', pad, 15 * ratio);
  }

  function renderMotionChart(result) {
    const canvas = $('motion-chart');
    const rect = canvas.getBoundingClientRect(); if (!rect.width) return;
    const ratio = window.devicePixelRatio || 1; canvas.width = rect.width * ratio; canvas.height = 200 * ratio;
    const ctx = canvas.getContext('2d'), w = canvas.width, h = canvas.height, pad = 28 * ratio;
    ctx.clearRect(0, 0, w, h); ctx.strokeStyle = '#e1e3ec'; ctx.lineWidth = ratio;
    for (let i = 0; i < 4; i++) { const y = pad + (h - pad * 2) * i / 3; ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke(); }
    const group = result.exercise === 'elbow_flexion' ? 'elbow' : result.exercise === 'arm_raise' ? 'shoulder' : 'knee';
    const colours = ['#6854ce', '#35a68b'];
    for (const [sideIndex, side] of ['left', 'right'].entries()) {
      const key = `${group}_${side}`;
      const values = result.frames.map(frame => frame.angles_2d?.[key]);
      const finite = values.filter(Number.isFinite); if (!finite.length) continue;
      let min = Math.min(...finite), max = Math.max(...finite); if (max === min) max = min + 1;
      ctx.strokeStyle = colours[sideIndex]; ctx.lineWidth = 2 * ratio; ctx.beginPath();
      values.forEach((value, i) => {
        if (!Number.isFinite(value)) return;
        const x = pad + (w - 2 * pad) * i / Math.max(1, values.length - 1), y = h - pad - (h - 2 * pad) * (value - min) / (max - min);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }); ctx.stroke();
    }
    ctx.fillStyle = '#565e70'; ctx.font = `${10 * ratio}px Segoe UI, Arial`;
    ctx.fillText(`${group} angle · projected degrees · purple left / green right`, pad, 15 * ratio);
  }

  function renderMotionHistory() {
    const target = $('motion-history'); target.replaceChildren();
    for (const item of state.motionHistory.slice(0, 8)) {
      const row = document.createElement('p'); row.className = 'caption';
      row.textContent = `${new Date(item.created_at).toLocaleString()} · ${item.exercise} · ${item.summary.repetitions ?? 'no count'} repetitions · ${item.video.decoded_frames} decoded frames`;
      target.append(row);
    }
  }

  $('motion-file').addEventListener('change', () => showFilePreview($('motion-file').files?.[0], 'motion-original', 'motionOriginal'));
  $('motion-form').addEventListener('submit', async event => {
    event.preventDefault();
    const file = $('motion-file').files?.[0];
    if (!file && !state.cameraBlob) { $('motion-status').textContent = 'Choose a video or record one with the webcam first.'; return; }
    const upload = file || new File([state.cameraBlob], state.cameraBlob.name || 'webcam-capture.webm', { type: state.cameraBlob.type || 'video/webm' });
    const button = $('motion-submit'); button.disabled = true; $('motion-results').hidden = true;
    $('motion-status').textContent = 'Decoding the clip and tracking holistic landmarks locally. Longer clips take more time…';
    try {
      if (upload.size > 9 * 1024 * 1024) throw new Error(errorText('VIDEO_TOO_LARGE'));
      const result = await post('/api/computer-vision/motion/analyze', {
        video_data: await fileAsDataUrl(upload), filename: upload.name, rotation: Number($('motion-rotation').value),
        mirror: $('motion-mirror').checked, frame_stride: Number($('motion-stride').value),
        exercise: $('motion-exercise').value, rep_prominence_degrees: Number($('motion-prominence').value)
      });
      state.motion = result;
      state.motionHistory.unshift({ analysis_id: result.analysis_id, created_at: result.created_at, exercise: result.exercise, video: result.video, summary: result.summary });
      setImage('motion-overlay-frame', result.overlay_frame_jpeg_base64, 'image/jpeg');
      showExportVideo('motion-overlay-video', result.overlay_video_base64);
      $('motion-results').hidden = false;
      const metrics = $('motion-metrics'); metrics.replaceChildren();
      addMetric(metrics, 'Repetitions', result.summary.repetitions, result.summary.repetition_rule);
      addMetric(metrics, 'Frames tracked', result.summary.processed_frames, `${result.summary.tracking_loss_frames} with tracking loss`);
      addMetric(metrics, 'Tracking visibility', result.summary.mean_pose_tracking_visibility_fraction === null ? null : `${(result.summary.mean_pose_tracking_visibility_fraction * 100).toFixed(1)}%`, 'Fraction of pose landmarks with visibility ≥ 0.5');
      addMetric(metrics, 'ROM · left knee', result.summary.range_of_motion_degrees_2d.knee_left === null ? null : `${result.summary.range_of_motion_degrees_2d.knee_left}°`, 'Projected 2D range; not calibrated');
      addMetric(metrics, 'Bilateral knee ROM symmetry', result.summary.bilateral_rom_symmetry_percent.knee === null ? null : `${result.summary.bilateral_rom_symmetry_percent.knee}%`, 'Descriptive range comparison');
      renderMotionChart(result); renderMotionHistory();
      $('motion-status').textContent = 'Landmark tracking and descriptive 2D kinematics completed. Review tracking quality and limitations.';
      $('motion-report').onclick = () => {
        downloadJSON(cleanReport(result), `asthral-motionguard-${result.analysis_id}.json`);
        if (result.overlay_video_base64) downloadBlob(mediaBlob(result.overlay_video_base64, 'video/mp4'), `asthral-motionguard-${result.analysis_id}-overlay.mp4`);
        downloadBlob(new Blob([landmarksCSV(result)], { type: 'text/csv' }), `asthral-motionguard-${result.analysis_id}-landmarks.csv`);
      };
    } catch (error) { $('motion-status').textContent = error.message; }
    finally { button.disabled = false; }
  });
  $('motion-overlay-toggle').addEventListener('change', () => {
    $('motion-overlay-video').hidden = !$('motion-overlay-toggle').checked || !state.motion?.overlay_video_base64;
    $('motion-overlay-frame').hidden = !$('motion-overlay-toggle').checked || !state.motion?.overlay_frame_jpeg_base64;
  });

  function landmarksCSV(result) {
    const rows = ['frame,time_seconds,group,landmark_index,x,y,z,visibility,presence'];
    for (const frame of result.frames) {
      for (const group of ['pose_landmarks', 'pose_world_landmarks', 'face_landmarks', 'left_hand_landmarks', 'right_hand_landmarks']) {
        (frame[group] || []).forEach((point, index) => rows.push([frame.frame, frame.time_seconds, group, index, point.x, point.y, point.z, point.visibility ?? '', point.presence ?? ''].join(',')));
      }
    }
    return rows.join('\r\n');
  }

  $('motion-camera-start').addEventListener('click', async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw new Error('This browser does not support local camera recording.');
      state.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      const preview = $('motion-camera-preview'); preview.srcObject = state.stream; preview.hidden = false; await preview.play();
      const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp8') ? 'video/webm;codecs=vp8' : '';
      state.recorder = new MediaRecorder(state.stream, mime ? { mimeType: mime } : undefined);
      state.cameraChunks = [];
      state.recorder.ondataavailable = event => { if (event.data?.size) state.cameraChunks.push(event.data); };
      state.recorder.onstop = () => {
        state.cameraBlob = new Blob(state.cameraChunks, { type: state.recorder.mimeType || 'video/webm' });
        state.cameraBlob.name = state.cameraBlob.type.includes('mp4') ? 'webcam-capture.mp4' : 'webcam-capture.webm';
        $('motion-camera-state').textContent = `Captured ${(state.cameraBlob.size / 1024 / 1024).toFixed(2)} MB · browser memory only.`;
        showFilePreview(new File([state.cameraBlob], state.cameraBlob.name, { type: state.cameraBlob.type }), 'motion-original', 'motionOriginal');
        stopCameraTracks();
      };
      state.recorder.start(500);
      $('motion-camera-state').textContent = 'Recording · maximum 20 seconds. The camera remains local until you submit the analysis.';
      $('motion-camera-start').disabled = true; $('motion-camera-stop').disabled = false;
      state.cameraTimer = setTimeout(() => state.recorder?.state === 'recording' && state.recorder.stop(), 20_000);
    } catch (error) { $('motion-camera-state').textContent = error.message; stopCameraTracks(); }
  });
  $('motion-camera-stop').addEventListener('click', () => { if (state.recorder?.state === 'recording') state.recorder.stop(); });
  function stopCameraTracks() {
    clearTimeout(state.cameraTimer); state.cameraTimer = null;
    if (state.stream) state.stream.getTracks().forEach(track => track.stop());
    state.stream = null; $('motion-camera-start').disabled = false; $('motion-camera-stop').disabled = true;
    const preview = $('motion-camera-preview'); preview.srcObject = null; preview.hidden = true;
  }

  document.querySelectorAll('[data-view="ocularvision"],[data-view="echovision"],[data-view="motionguard"]').forEach(button => button.addEventListener('click', refreshStatus));
  document.querySelector('[data-view="skinguard"]')?.addEventListener('click', refreshStatus);
  window.addEventListener('beforeunload', () => {
    stopCameraTracks();
    for (const url of Object.values(state.objectUrls)) URL.revokeObjectURL(url);
  });
})();
