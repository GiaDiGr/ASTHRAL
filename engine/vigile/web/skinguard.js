(() => {
  const $ = id => document.getElementById(id);
  const maxBytes = 10 * 1024 * 1024;
  const allowed = new Set(['image/jpeg', 'image/png', 'image/webp']);
  let currentUrl = null;
  let previousUrl = null;
  let lastReport = null;
  let lastFiles = null;
  let photoHistory = [];
  let historyBytes = 0;
  const historyLimit = 5;
  const historyByteLimit = 30 * 1024 * 1024;

  function localDate() {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 10);
  }

  function clearBoxes() {
    const svg = $('sg-boxes');
    svg.replaceChildren();
    svg.hidden = true;
  }

  function preview(input, image, previous = false) {
    const file = input.files?.[0];
    const oldUrl = previous ? previousUrl : currentUrl;
    if (oldUrl) URL.revokeObjectURL(oldUrl);
    if (previous) previousUrl = null;
    else {
      currentUrl = null;
      clearBoxes();
    }
    image.removeAttribute('src');
    image.hidden = true;
    if (!file) return;
    if (!allowed.has(file.type) || file.size > maxBytes) {
      $('skinguard-status').textContent = file.size > maxBytes
        ? 'La imagen supera el límite de 10 MB.'
        : 'Formato no admitido. Elige JPEG, PNG o WebP.';
      input.value = '';
      return;
    }
    const url = URL.createObjectURL(file);
    if (previous) previousUrl = url;
    else currentUrl = url;
    image.src = url;
    image.hidden = false;
  }

  async function readStatus() {
    try {
      const response = await fetch('/api/skinguard/status', { cache: 'no-store' });
      if (response.status === 401) throw new Error('La sesión expiró. Vuelve a ingresar al portal.');
      if (!response.ok) throw new Error(`Estado del módulo no disponible (${response.status}).`);
      const status = await response.json();
      $('skinguard-state').textContent = status.analysis_available
        ? 'Detector local disponible'
        : 'Sin modelo dermatológico';
      $('skinguard-status').textContent = status.analysis_available
        ? `Modelo de localización: ${status.model_id}. Sólo investigación; los puntajes no son probabilidades calibradas.`
        : `Modo ${status.state}. Se pueden validar imágenes y preparar informes, pero no se ejecuta IA ni se generan hallazgos.`;
    } catch (error) {
      $('skinguard-state').textContent = 'Módulo no disponible';
      $('skinguard-status').textContent = error.message;
    }
  }

  function showBoxes(detections) {
    const svg = $('sg-boxes');
    svg.replaceChildren();
    for (const detection of detections || []) {
      const [x1, y1, x2, y2] = detection.box_xyxy_normalized;
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x1);
      rect.setAttribute('y', y1);
      rect.setAttribute('width', x2 - x1);
      rect.setAttribute('height', y2 - y1);
      rect.setAttribute('class', 'skinguard-box');
      rect.dataset.boxIndex = String(detections.indexOf(detection));
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = `Área candidata · puntaje ${Number(detection.score).toFixed(3)}; no es una probabilidad calibrada`;
      rect.append(title);
      svg.append(rect);
    }
    svg.hidden = !detections?.length;
  }

  function displayReport(report) {
    lastReport = report;
    showBoxes(report.detections);
    const target = $('sg-result');
    target.replaceChildren();
    const summary = document.createElement('p');
    summary.textContent = report.analysis_performed
      ? `${report.message} Cajas: ${report.detections.length}. No se emite diagnóstico ni inferencia causal.`
      : report.message;
    target.append(summary);
    const quality = report.quality_checks;
    if (quality) {
      const note = document.createElement('p');
      note.textContent = `Iluminación · heurística no validada: ${quality.state}. No determina la adecuación clínica de la foto.`;
      target.append(note);
    }
    if (report.analysis_performed && report.detections?.length) {
      const heading = document.createElement('h3');
      heading.textContent = 'Áreas candidatas · selecciona una caja';
      target.append(heading);
      const selected = document.createElement('p');
      selected.id = 'sg-selected';
      selected.textContent = 'La caracterización dermatológica no está disponible; el modelo sólo localiza regiones candidatas.';
      target.append(selected);
      report.detections.forEach((detection, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'secondary';
        button.textContent = `Área ${index + 1} · puntaje ${Number(detection.score).toFixed(3)} (no probabilidad)`;
        button.addEventListener('click', () => {
          document.querySelectorAll('.skinguard-box-selected').forEach(box => box.classList.remove('skinguard-box-selected'));
          const box = $('sg-boxes').querySelector(`[data-box-index="${index}"]`);
          box?.classList.add('skinguard-box-selected');
          selected.textContent = `Área candidata ${index + 1}. El puntaje es una salida del detector, no una probabilidad de malignidad. Una persona debe revisar la correspondencia visual.`;
        });
        target.append(button);
      });
    }
    const details = document.createElement('details');
    const caption = document.createElement('summary');
    caption.textContent = 'Ver contenido del informe';
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(report, null, 2);
    details.append(caption, pre);
    target.append(details);
    $('sg-download').hidden = false;
    $('sg-download-visual').hidden = false;
  }

  function renderHistory() {
    const target = $('sg-history');
    target.replaceChildren();
    if (!photoHistory.length) return;
    const heading = document.createElement('h3');
    heading.textContent = 'Seguimiento visual · sólo en esta sesión del navegador';
    const note = document.createElement('p');
    note.className = 'caption';
    note.textContent = 'Las fotografías se comparan a simple vista. No se calcula crecimiento, cambio clínico ni causalidad.';
    target.append(heading, note);
    const grid = document.createElement('div'); grid.className = 'skin-history-grid';
    for (const entry of photoHistory) {
      const card = document.createElement('article'); card.className = 'skin-history-card';
      const image = document.createElement('img'); image.src = entry.thumbnailUrl; image.alt = `Skin photo captured ${entry.date}`;
      const meta = document.createElement('small'); meta.textContent = `${entry.date} · ${entry.bodySite}`;
      const button = document.createElement('button'); button.type = 'button'; button.className = 'secondary'; button.textContent = 'Usar como foto anterior';
      button.addEventListener('click', () => {
        const currentDate = $('sg-date').value;
        if (currentDate && entry.date >= currentDate) {
          $('skinguard-status').textContent = 'La fecha de la foto actual debe ser posterior a la imagen de referencia.';
          return;
        }
        const transfer = new DataTransfer(); transfer.items.add(entry.file); $('sg-previous').files = transfer.files;
        $('sg-previous-date').value = entry.date;
        preview($('sg-previous'), $('sg-preview-previous'), true);
        $('skinguard-status').textContent = 'Referencia seleccionada. Revisa ambas imágenes lado a lado; no se ejecuta comparación automática.';
      });
      card.append(image, meta, button); grid.append(card);
    }
    target.append(grid);
  }

  function addHistory(file, report) {
    if (!file) return;
    const date = report.capture_date;
    if (!date) return;
    const entry = { id: report.analysis_id, file, date, bodySite: report.body_site || 'Zona no indicada', thumbnailUrl: URL.createObjectURL(file) };
    photoHistory.push(entry); historyBytes += file.size;
    while (photoHistory.length > historyLimit || historyBytes > historyByteLimit) {
      const removed = photoHistory.shift(); historyBytes -= removed.file.size; URL.revokeObjectURL(removed.thumbnailUrl);
    }
    renderHistory();
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
  }

  function fileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error('No se pudo leer la imagen seleccionada.'));
      reader.readAsDataURL(file);
    });
  }

  $('sg-image').addEventListener('change', () => preview($('sg-image'), $('sg-preview-current')));
  $('sg-previous').addEventListener('change', () => preview($('sg-previous'), $('sg-preview-previous'), true));
  document.querySelector('[data-view="skinguard"]')?.addEventListener('click', readStatus);
  $('sg-date').value = localDate();

  $('skinguard-form').addEventListener('submit', async event => {
    event.preventDefault();
    const file = $('sg-image').files?.[0];
    if (!file) return;
    const button = $('sg-submit');
    button.disabled = true;
    $('skinguard-status').textContent = 'Validando la imagen en el portal local…';
    $('sg-result').replaceChildren();
    $('sg-download').hidden = true;
    lastReport = null;
    try {
      if (file.size > maxBytes || !allowed.has(file.type)) throw new Error('El archivo debe ser JPEG, PNG o WebP y no superar 10 MB.');
      const imageData = await fileAsDataUrl(file);
      let previousFile = $('sg-previous').files?.[0] || null;
      let previousDate = $('sg-previous-date').value || null;
      if (!previousFile) {
        const prior = [...photoHistory].reverse().find(entry => entry.date < $('sg-date').value);
        if (prior) {
          previousFile = prior.file; previousDate = prior.date;
          const transfer = new DataTransfer(); transfer.items.add(previousFile); $('sg-previous').files = transfer.files;
          $('sg-previous-date').value = previousDate; preview($('sg-previous'), $('sg-preview-previous'), true);
        }
      }
      const response = await fetch('/api/skinguard/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
        body: JSON.stringify({
          image_data: imageData,
          capture_date: $('sg-date').value,
          body_site: $('sg-site').value,
          case_reference: $('sg-reference').value,
          earlier_photo_date: previousDate,
          user_observation: $('sg-observation').value,
          uv_context: $('sg-uv').value,
        }),
      });
      const result = await response.json();
      if (response.status === 401) throw new Error('La sesión expiró. Vuelve a ingresar al portal.');
      if (!response.ok) throw new Error(result.detail || `No se pudo procesar la imagen (${response.status}).`);
      result.longitudinal_visual_comparison = previousFile
        ? { reference_date: previousDate, comparison: 'Manual side-by-side visual review only; no automatic image comparison or change inference.' }
        : { reference_date: null, comparison: 'No earlier image was available in this browser session.' };
      lastFiles = { current: file, previous: previousFile, previousDate };
      displayReport(result);
      addHistory(file, result);
      $('skinguard-status').textContent = result.analysis_performed
        ? 'La localización de investigación terminó. Revisa las limitaciones del informe.'
        : 'Archivo válido. No se ejecutó análisis de IA; no se generaron cajas ni predicciones.';
    } catch (error) {
      $('skinguard-status').textContent = error.message;
      clearBoxes();
    } finally {
      button.disabled = false;
    }
  });

  $('sg-download').addEventListener('click', () => {
    if (!lastReport) return;
    const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `asthral-skinguard-${lastReport.analysis_id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  $('sg-download-visual').addEventListener('click', async () => {
    if (!lastReport || !lastFiles?.current) return;
    try {
      const current = await fileAsDataUrl(lastFiles.current);
      const previous = lastFiles.previous ? await fileAsDataUrl(lastFiles.previous) : null;
      const markup = `<!doctype html><html lang="es"><meta charset="utf-8"><title>ASTHRAL SkinGuard · informe experimental</title><style>body{font:15px Segoe UI,Arial,sans-serif;max-width:1000px;margin:32px auto;padding:0 18px;color:#202638}img{max-width:100%;height:auto;border-radius:8px;border:1px solid #ddd}section{margin:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f8;padding:14px;border-radius:8px;font-size:12px}.warning{padding:14px;background:#f0edfc;border-radius:8px}</style><h1>ASTHRAL SkinGuard · informe de investigación</h1><p class="warning">No es diagnóstico médico. La fotografía no permite atribuir causalidad UV o espacial. Este prototipo no generó hallazgos si no había un detector compatible configurado.</p><section><h2>Fotografía actual · ${escapeHtml(lastReport.capture_date)}</h2><img src="${current}" alt="Fotografía actual"></section>${previous ? `<section><h2>Fotografía de referencia · ${escapeHtml(lastFiles.previousDate || '')}</h2><img src="${previous}" alt="Fotografía anterior"></section>` : ''}<section><h2>Datos y resultados del análisis</h2><pre>${escapeHtml(JSON.stringify(lastReport, null, 2))}</pre></section></html>`;
      const blob = new Blob([markup], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url;
      anchor.download = `asthral-skinguard-${lastReport.analysis_id}-visual.html`; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { $('skinguard-status').textContent = error.message; }
  });

  $('sg-clear').addEventListener('click', () => {
    if (currentUrl) URL.revokeObjectURL(currentUrl);
    if (previousUrl) URL.revokeObjectURL(previousUrl);
    currentUrl = previousUrl = null;
    $('skinguard-form').reset();
    $('sg-date').value = localDate();
    $('sg-preview-current').removeAttribute('src');
    $('sg-preview-previous').removeAttribute('src');
    $('sg-preview-current').hidden = $('sg-preview-previous').hidden = true;
    $('sg-result').replaceChildren();
    $('sg-download').hidden = true;
    $('sg-download-visual').hidden = true;
    lastReport = null;
    lastFiles = null;
    photoHistory.forEach(entry => URL.revokeObjectURL(entry.thumbnailUrl));
    photoHistory = []; historyBytes = 0; renderHistory();
    clearBoxes();
    $('skinguard-status').textContent = 'Fotos y datos del formulario limpiados de esta sesión del navegador.';
  });
})();
