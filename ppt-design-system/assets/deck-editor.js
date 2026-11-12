(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const model = JSON.parse(byId('deck-model').textContent);
  const embedded = JSON.parse(byId('deck-edits').textContent);
  const articles = [...document.querySelectorAll('main > article')];
  const key = 'ppt-design-system:' + model.base + ':' + location.pathname;
  const record = value => value && typeof value === 'object' && !Array.isArray(value);
  const own = (obj, id) => Object.hasOwn(obj, id);
  const maxImage = 6 * 1024 * 1024;
  const asJson = value => JSON.stringify(value).replaceAll('<', '\\u003c');
  const outline = document.createElement('div');
  outline.className = 'edit-outline';
  outline.setAttribute('aria-hidden', 'true');
  const handle = outline.appendChild(document.createElement('div'));
  handle.className = 'edit-grip';
  const boxInputs = ['left', 'top', 'width', 'height'].map(byId);
  const labelNames = {
    title: '标题', kicker: '页眉', folio: '页码', setup: '背景说明', decision: '决策说明',
    party: '参与方', mechanism: '机制', constraint: '约束', flow: '流向说明',
    milestone: '阶段', action: '行动', check: '验收', image: '图片', caption: '图注',
    lead: '导语', body: '正文', feedback: '双向闭环', checkpoints: '三阶段验收',
  };

  let active = Math.max(0, articles.findIndex(slide => '#' + slide.id === location.hash));
  let editing = false;
  let selectedLayer = '';
  let selectedSlot = '';
  let drag;
  let pristineHtml;
  let edits = embedded;
  const page = () => articles[active];
  const spec = () => model.pages[page().id];
  const saved = () => edits.pages[page().id] || {};
  const editable = () => (edits.pages[page().id] ||= {});
  const boxOf = id => saved().boxes?.[id] || spec().boxes[id];
  const findLayer = (slide, name, group) => {
    const parent = group ? slide.querySelector(':scope > [data-layer="' + group + '"]') : slide;
    return parent.querySelector(':scope > [data-layer="' + name + '"]');
  };
  const originals = new Map();
  for (const slide of articles) {
    for (const entry of model.pages[slide.id].layers.filter(layer => layer.kind === 'image')) {
      const image = findLayer(slide, entry.layer, entry.group);
      image.draggable = false;
      originals.set(image, image.getAttribute('src'));
    }
  }

  function goodBox(box) {
    return Array.isArray(box) && box.length === 4 && box.every(v => Number.isFinite(v) && v >= 0 && v <= 100)
      && Math.min(box[2], box[3]) >= .5 && box[0] + box[2] <= 100.001 && box[1] + box[3] <= 100.001;
  }
  function goodText(text, entry) {
    return typeof text === 'string' && text.trim() && [...text].length <= entry.limit
      && !/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(text);
  }
  function goodImage(url) {
    return typeof url === 'string' && url.length <= maxImage * 4 / 3 + 128
      && /^data:image\/(?:png|jpeg|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(url);
  }
  function validate(candidate) {
    if (!record(candidate) || candidate.version !== 1 || candidate.base !== model.base || !record(candidate.pages)
        || Object.keys(candidate).some(k => !['version', 'base', 'pages'].includes(k))) return false;
    return Object.entries(candidate.pages).every(([id, patch]) => {
      if (!own(model.pages, id) || !record(patch)) return false;
      const pageModel = model.pages[id];
      return Object.entries(patch).every(([kind, items]) => {
        if (!record(items)) return false;
        if (kind === 'boxes') return Object.entries(items).every(([layer, box]) => own(pageModel.boxes, layer) && goodBox(box));
        if (kind !== 'slots' && kind !== 'images') return false;
        return Object.entries(items).every(([slot, value]) => {
          const entry = pageModel.layers.find(x => x.slot === slot);
          return kind === 'slots' ? entry?.kind === 'text' && goodText(value, entry)
            : entry?.kind === 'image' && goodImage(value);
        });
      });
    });
  }

  function status(text) { byId('save-status').textContent = text; }
  function persist() {
    try {
      localStorage.setItem(key, JSON.stringify(edits));
      status('已保存在此浏览器');
    } catch {
      status('请另存 HTML 或导出修改');
    }
  }
  function setBox(node, box) {
    ['left', 'top', 'width', 'height'].forEach((prop, i) => { node.style[prop] = box[i] + '%'; });
  }
  function showSlide(slide) {
    const { layers, boxes, slots, title, titleSlot } = model.pages[slide.id];
    const patch = edits.pages[slide.id] || {};
    for (const [id, box] of Object.entries(boxes)) setBox(findLayer(slide, id), patch.boxes?.[id] || box);
    for (const entry of layers) {
      const node = findLayer(slide, entry.layer, entry.group);
      if (entry.kind === 'image') {
        const url = patch.images?.[entry.slot] || originals.get(node);
        if (node.getAttribute('src') !== url) node.src = url;
        continue;
      }
      const text = patch.slots?.[entry.slot] ?? slots[entry.slot];
      const span = node.querySelector('span');
      const phrase = slots[entry.underline];
      const start = phrase ? text.indexOf(phrase) : -1;
      span.textContent = text;
      if (start >= 0 && text.indexOf(phrase, start + 1) < 0) {
        const u = document.createElement('u');
        u.style.cssText = 'text-underline-offset:.12em;text-decoration-thickness:.052em';
        u.textContent = phrase;
        span.replaceChildren(text.slice(0, start), u, text.slice(start + phrase.length));
      }
    }
    const index = articles.indexOf(slide);
    const label = patch.slots?.[titleSlot] || title;
    const option = byId('page-select').options[index];
    if (option) option.text = (index + 1) + ' · ' + label;
    if (slide === page()) byId('deck-title').textContent = label;
  }

  function warning() {
    let count = 0;
    for (const layer of page().querySelectorAll('.text')) {
      const rect = layer.getBoundingClientRect();
      const range = document.createRange();
      range.selectNodeContents(layer.querySelector('span'));
      if ([...range.getClientRects()].some(line => line.top < rect.top - 1 || line.bottom > rect.bottom + 1
        || line.left < rect.left - 1 || line.right > rect.right + 1)) count++;
    }
    byId('layout-warning').textContent = count ? count + ' 处文字可能超出槽位' : '';
  }

  function friendly(id) {
    const match = id.replace(/^(?:main|aside)-/, '').match(/^(.*?)(?:-(\d+))?$/);
    return (labelNames[match[1]] || match[1]) + (match[2] ? ' ' + match[2] : '');
  }
  function options(select, entries, placeholder) {
    select.replaceChildren(new Option(placeholder, ''), ...entries.map(([id, label]) => new Option(label, id)));
  }
  function refreshInspector() {
    byId('layer-select').value = selectedLayer;
    byId('slot-select').value = selectedSlot;
    const box = boxOf(selectedLayer);
    byId('geometry').hidden = !box;
    if (box) boxInputs.forEach((input, i) => { input.value = box[i]; });
    const entry = spec().layers.find(item => item.slot === selectedSlot);
    const textarea = byId('slot-text');
    textarea.hidden = entry?.kind !== 'text';
    byId('replace-image').hidden = entry?.kind !== 'image';
    if (entry?.kind === 'text') {
      textarea.maxLength = entry.limit;
      textarea.value = saved().slots?.[selectedSlot] ?? spec().slots[selectedSlot];
    }
    outline.remove();
    if (editing && box) {
      setBox(outline, box);
      page().append(outline);
    }
  }
  function showPage(index) {
    active = Math.max(0, Math.min(articles.length - 1, index));
    articles.forEach((slide, i) => { slide.hidden = i !== active; });
    byId('page-select').selectedIndex = active;
    byId('deck-title').textContent = saved().slots?.[spec().titleSlot] || spec().title;
    byId('page-intent').textContent = spec().intent;
    byId('page-counter').textContent = (active + 1) + ' / ' + articles.length;
    byId('previous').disabled = active === 0;
    byId('next').disabled = active === articles.length - 1;
    options(byId('layer-select'), Object.keys(spec().boxes).map(id => [id, friendly(id)]), '选择或点击图层');
    options(byId('slot-select'), spec().layers.map(item => [item.slot, friendly(item.slot)]), '选择文字或图片');
    selectedLayer = selectedSlot = '';
    refreshInspector();
    warning();
    try { history.replaceState(null, '', '#' + page().id); } catch { /* local browser restrictions */ }
  }

  function selectLayer(id, slot = '') {
    selectedLayer = own(spec().boxes, id) ? id : '';
    selectedSlot = slot || spec().layers.find(entry => entry.layer === id && !entry.group)?.slot || '';
    refreshInspector();
  }

  function updateBox(box, save = true) {
    if (!selectedLayer || !goodBox(box)) return false;
    (editable().boxes ||= {})[selectedLayer] = box;
    setBox(findLayer(page(), selectedLayer), box);
    setBox(outline, box);
    boxInputs.forEach((input, i) => { input.value = box[i]; });
    if (save) { persist(); warning(); }
    return true;
  }

  function download(name, type, value) {
    const url = URL.createObjectURL(new Blob([value], { type }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = name;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  document.addEventListener('DOMContentLoaded', () => {
    pristineHtml = document.documentElement.outerHTML;
    try {
      const stored = JSON.parse(localStorage.getItem(key));
      if (validate(stored)) edits = stored;
    } catch { /* portable state is embedded in the document */ }
    for (const slide of articles) {
      byId('page-select').add(new Option((byId('page-select').length + 1) + ' · ' + model.pages[slide.id].title, slide.id));
      showSlide(slide);
    }
    showPage(active);
    status(Object.keys(edits.pages).length ? '已加载修改' : '');
  });

  byId('previous').onclick = () => showPage(active - 1);
  byId('next').onclick = () => showPage(active + 1);
  byId('page-select').onchange = event => showPage(event.target.selectedIndex);
  byId('edit-mode').onclick = () => {
    editing = !editing;
    document.body.classList.toggle('is-editing', editing);
    byId('inspector').hidden = byId('download-html').hidden = !editing;
    byId('edit-mode').textContent = editing ? '返回演示' : '编辑';
    byId('edit-mode').setAttribute('aria-pressed', String(editing));
    refreshInspector();
    requestAnimationFrame(warning);
  };
  byId('full-screen').onclick = () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.body.requestFullscreen?.().catch(() => status('浏览器未开启全屏'));
  };
  document.addEventListener('keydown', event => {
    if (event.altKey || event.metaKey || event.ctrlKey || event.target.matches('input,select,textarea,button')) return;
    if (['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      showPage(active + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  byId('layer-select').onchange = event => selectLayer(event.target.value);
  byId('slot-select').onchange = event => {
    const entry = spec().layers.find(item => item.slot === event.target.value);
    selectLayer(entry?.group || entry?.layer || '', event.target.value);
  };
  boxInputs.forEach(input => {
    input.onchange = () => {
      const values = boxInputs.map(field => field.valueAsNumber);
      if (!updateBox(values)) { refreshInspector(); status('位置或尺寸超出画布'); }
    };
  });
  byId('slot-text').oninput = event => {
    const entry = spec().layers.find(item => item.slot === selectedSlot);
    if (!entry || !goodText(event.target.value, entry)) { status('保留上一次有效文字'); return; }
    (editable().slots ||= {})[selectedSlot] = event.target.value;
    showSlide(page());
    persist();
    warning();
  };
  byId('replace-image').onclick = () => byId('image-file').click();
  byId('image-file').onchange = event => {
    const file = event.target.files[0];
    event.target.value = '';
    if (!file) return;
    if (!/^image\/(?:png|jpeg|webp)$/.test(file.type) || file.size > maxImage) {
      status('请选择 6 MB 以内的 PNG、JPEG 或 WebP');
      return;
    }
    const id = page().id, slot = selectedSlot;
    const reader = new FileReader();
    reader.onload = () => {
      const image = new Image();
      image.onload = () => {
        if (image.width * image.height > 16000000) { status('图片尺寸过大'); return; }
        ((edits.pages[id] ||= {}).images ||= {})[slot] = reader.result;
        showSlide(articles.find(slide => slide.id === id));
        persist();
      };
      image.onerror = () => status('无法打开这张图');
      image.src = reader.result;
    };
    reader.onerror = () => status('无法读取图片');
    reader.readAsDataURL(file);
  };

  byId('reset-page').onclick = () => {
    if (!own(edits.pages, page().id)) return;
    if (!confirm('恢复本页原始文字和图层位置？')) return;
    delete edits.pages[page().id];
    showSlide(page());
    refreshInspector();
    persist();
    warning();
  };
  byId('download-edits').onclick = () => download('edits.json', 'application/json', JSON.stringify(edits, null, 2));
  byId('download-html').onclick = () => {
    const copy = new DOMParser().parseFromString(pristineHtml, 'text/html');
    copy.getElementById('deck-edits').textContent = asJson(edits);
    download('演示-已编辑.html', 'text/html;charset=utf-8', '<!doctype html>\n' + copy.documentElement.outerHTML);
  };
  byId('load-edits').onclick = () => byId('edits-file').click();
  byId('edits-file').onchange = async event => {
    const file = event.target.files[0];
    event.target.value = '';
    if (!file) return;
    try {
      const update = JSON.parse(await file.text());
      if (!validate(update)) throw new Error('Invalid edit file');
      edits = update;
      articles.forEach(showSlide);
      refreshInspector();
      persist();
      warning();
    } catch { status('修改文件无效或不属于这份演示'); }
  };

  const canvas = document.querySelector('main');
  canvas.addEventListener('dragstart', event => { if (editing) event.preventDefault(); });
  canvas.addEventListener('pointerdown', event => {
    if (!editing || event.button !== 0) return;
    const slide = page();
    const resize = event.target === handle;
    if (!resize) {
      const layers = [];
      for (let node = event.target; node && node !== slide; node = node.parentElement) {
        if (node.dataset?.layer) layers.push(node.dataset.layer);
      }
      const id = layers.at(-1);
      const entry = spec().layers.find(item => item.layer === layers[0] && (item.group || item.layer) === id);
      selectLayer(id, entry?.slot);
    }
    const start = boxOf(selectedLayer);
    if (!start) return;
    event.preventDefault();
    drag = { slide, id: event.pointerId, x: event.clientX, y: event.clientY, start, resize, changed: false };
    slide.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', event => {
    if (!drag || event.pointerId !== drag.id) return;
    const area = drag.slide.getBoundingClientRect();
    const dx = (event.clientX - drag.x) * 100 / area.width;
    const dy = (event.clientY - drag.y) * 100 / area.height;
    if (!drag.changed && Math.abs(dx) + Math.abs(dy) < .3) return;
    const [x, y, w, h] = drag.start;
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const values = drag.resize ? [x, y, clamp(w + dx, .5, 100 - x), clamp(h + dy, .5, 100 - y)]
      : [clamp(x + dx, 0, 100 - w), clamp(y + dy, 0, 100 - h), w, h];
    drag.changed = updateBox(values.map(v => Number(v.toFixed(3))), false) || drag.changed;
  });
  for (const eventName of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    canvas.addEventListener(eventName, event => {
      if (!drag || event.pointerId !== drag.id) return;
      const changed = drag.changed;
      drag = undefined;
      if (changed) { persist(); warning(); }
    });
  }
  canvas.addEventListener('dblclick', () => {
    if (editing && !byId('slot-text').hidden) byId('slot-text').focus();
  });
  window.addEventListener('resize', warning);
})();
