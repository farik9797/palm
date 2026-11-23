/* Palm · 3D-карта Бухары: прорисовка улиц → подъём зданий → метки с карточками.
   Метки читаются из разметки (#rows [data-pin]) — правьте список в index.html. */
(() => {
  const mapEl = document.getElementById('map');
  const rows = [...document.querySelectorAll('[data-pin]')];
  const $ = (id) => document.getElementById(id);
  if (!mapEl || !window.maplibregl) return;

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const CENTER = [64.4168, 39.7742];
  // карта на весь экран, текст поверх: p = 0 — текст виден, p = 1 — текст ушёл
  const hero = $('hero'), copy = $('hero-copy'), stage = mapEl.parentElement;
  const scrolly = !reduce && !!hero;
  let p = 0, inset = { top: 0, side: 0, bot: 0 };
  const pad = () => { const k = 1 - p; return { top: inset.top * k, right: inset.side * k, bottom: inset.bot * k, left: inset.side * k }; };
  const range = () => stage.clientHeight * 0.5;           // сколько прокрутки занимает исчезновение текста
  function measure() {
    if (!scrolly) return;
    inset = { top: copy.offsetHeight, side: 0, bot: 0 };      // камера держит центр города ниже текста
    hero.style.setProperty('--top', `${inset.top}px`);
  }
  if (scrolly) { document.documentElement.classList.add('js-scroll'); measure(); }
  const touch = matchMedia('(pointer: coarse)').matches;
  const flat = () => ({ center: CENTER, zoom: 13.0, pitch: 0, bearing: 0, padding: pad() });
  const tilted = () => ({ center: [64.4185, 39.7735], zoom: 14.5, pitch: 60, bearing: -24, padding: pad() });
  const RINGS = 6;

  // токены CSS → rgba для MapLibre (oklch он не понимает)
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', { willReadFrequently: true });
  const css = getComputedStyle(document.documentElement);
  const tok = (name, a = 1) => {
    cx.clearRect(0, 0, 1, 1); cx.fillStyle = css.getPropertyValue(name).trim(); cx.fillRect(0, 0, 1, 1);
    const [r, g, b] = cx.getImageData(0, 0, 1, 1).data;
    return `rgba(${r},${g},${b},${a})`;
  };
  const C = {
    paper: tok('--color-land'), roadCase: tok('--color-road-case'), sheet: tok('--color-sheet'), ink: tok('--color-ink'), ink2: tok('--color-ink-2'),
    contour: tok('--color-contour'), water: tok('--color-water'), green: tok('--color-green-soft'),
    building: tok('--color-building'), clear: tok('--color-ink', 0),
  };

  const MAJOR = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary'];
  const NAME = ['coalesce', ['get', 'name:ru'], ['get', 'name']];
  const HEIGHT = ['coalesce', ['get', 'render_height'], 5];
  const w = (a, b, c) => ['interpolate', ['exponential', 1.6], ['zoom'], 12, a, 15, b, 18, c];
  const isMajor = ['in', ['get', 'class'], ['literal', MAJOR]];
  const w2 = (M, m) => w(...[0, 1, 2].map((i) => ['case', isMajor, M[i], m[i]]));

  // [слой, свойство прозрачности, итоговое значение] — всё стартует с 0 и проявляется после прорисовки
  const REVEAL = [
    ['green', 'fill-opacity', 0.9], ['water', 'fill-opacity', 1], ['waterway', 'line-opacity', 1],
    ['road-case', 'line-opacity', 1], ['road', 'line-opacity', 1],
    ['buildings', 'fill-extrusion-opacity', 0.94], ['street-names', 'text-opacity', 1], ['place-names', 'text-opacity', 1],
  ];

  const map = new maplibregl.Map({
    container: mapEl,
    ...(reduce ? tilted() : flat()),
    minZoom: 12, maxZoom: 18.5, maxPitch: 70,
    maxBounds: [[64.30, 39.70], [64.53, 39.85]],
    scrollZoom: false,              // колесо всегда прокручивает страницу; масштаб — кнопками, двойным кликом, щипком
    cooperativeGestures: touch,     // на телефоне один палец листает страницу, два двигают карту
    locale: {
      'CooperativeGesturesHandler.WindowsHelpText': 'Чтобы приблизить карту, прокручивайте с зажатым Ctrl',
      'CooperativeGesturesHandler.MacHelpText': 'Чтобы приблизить карту, прокручивайте с зажатым ⌘',
      'CooperativeGesturesHandler.MobileHelpText': 'Двигайте карту двумя пальцами',
    },
    attributionControl: { compact: true },
    style: {
      version: 8,
      glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
      transition: { duration: 900, delay: 0 },
      sources: { omt: { type: 'vector', url: 'https://tiles.openfreemap.org/planet' } },
      layers: [
        { id: 'paper', type: 'background', paint: { 'background-color': C.paper } },
        { id: 'green', type: 'fill', source: 'omt', 'source-layer': 'landcover', filter: ['in', ['get', 'class'], ['literal', ['grass', 'wood', 'farmland']]], paint: { 'fill-color': C.green, 'fill-opacity': 0 } },
        { id: 'water', type: 'fill', source: 'omt', 'source-layer': 'water', paint: { 'fill-color': C.water, 'fill-opacity': 0 } },
        { id: 'waterway', type: 'line', source: 'omt', 'source-layer': 'waterway', paint: { 'line-color': C.water, 'line-width': w(0.6, 1.5, 4), 'line-opacity': 0 } },
        { id: 'road-case', type: 'line', source: 'omt', 'source-layer': 'transportation', filter: ['==', ['geometry-type'], 'LineString'], layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': C.roadCase, 'line-opacity': 0, 'line-width': w2([2.4, 7, 26], [1, 3.6, 15]) } },
        { id: 'road', type: 'line', source: 'omt', 'source-layer': 'transportation', filter: ['==', ['geometry-type'], 'LineString'], layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': C.sheet, 'line-opacity': 0, 'line-width': w2([1.4, 5.4, 23], [0.4, 2.4, 13]) } },
        { id: 'buildings', type: 'fill-extrusion', source: 'omt', 'source-layer': 'building', minzoom: 13,
          paint: { 'fill-extrusion-color': C.building, 'fill-extrusion-opacity': 0, 'fill-extrusion-height': 0, 'fill-extrusion-vertical-gradient': true } },
        { id: 'street-names', type: 'symbol', source: 'omt', 'source-layer': 'transportation_name', minzoom: 14.5,
          layout: { 'text-field': NAME, 'text-font': ['Noto Sans Regular'], 'symbol-placement': 'line', 'text-size': 12 },
          paint: { 'text-color': C.ink2, 'text-halo-color': C.paper, 'text-halo-width': 1.4, 'text-opacity': 0 } },
        { id: 'place-names', type: 'symbol', source: 'omt', 'source-layer': 'place', filter: ['in', ['get', 'class'], ['literal', ['suburb', 'neighbourhood', 'quarter']]],
          layout: { 'text-field': NAME, 'text-font': ['Noto Sans Regular'], 'text-size': 13 },
          paint: { 'text-color': C.ink2, 'text-halo-color': C.paper, 'text-halo-width': 1.6, 'text-opacity': 0 } },
      ],
    },
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
  window.palmMap = map;

  /* ---------- метки и карточки ---------- */
  let popup = null;
  const later0 = (fn) => setTimeout(fn, 4000);
  let pinned = null;

  const card = (row) => {
    const el = document.createElement('div'); el.className = 'card';
    const head = document.createElement('div'); head.className = 'card__head';
    head.textContent = row.querySelector('.row__kind').textContent;
    const ph = document.createElement('div'); ph.className = 'card__photo';
    if (row.dataset.photo) {
      ph.dataset.slot = 'card';
      const im = new Image(); im.src = row.dataset.photo; im.alt = row.querySelector('h3').textContent.trim(); im.onerror = () => ph.remove();
      ph.append(im);
    } else { ph.classList.add('card__photo--empty'); ph.textContent = 'Здесь будет фото объекта'; }
    el.append(ph, head);
    const body = document.createElement('div'); body.className = 'card__body';
    const name = document.createElement('p'); name.className = 'card__name'; name.textContent = row.querySelector('h3').textContent;
    body.append(name, row.querySelector('dl').cloneNode(true));
    el.append(body);
    return el;
  };

  const pins = rows.map((row, i) => {
    const lngLat = [Number(row.dataset.lng), Number(row.dataset.lat)];
    const name = row.querySelector('h3').textContent.trim();
    const b = document.createElement('button');
    b.type = 'button'; b.className = `pin pin--${row.dataset.kind} is-up`; b.setAttribute('aria-label', name);
    const inner = document.createElement('span'); inner.className = 'pin__in'; inner.style.transitionDelay = `${i * 70}ms`;
    const tag = document.createElement('span'); tag.className = 'pin__tag'; tag.textContent = name;
    const mark = document.createElement('span'); mark.className = 'pin__mark';
    inner.append(tag, mark); b.append(inner);
    new maplibregl.Marker({ element: b, anchor: 'bottom' }).setLngLat(lngLat).addTo(map);
    b.setAttribute('aria-label', name);   // MapLibre ставит своё «Map marker»
    const pin = { row, b, lngLat, kind: row.dataset.kind, text: row.textContent.toLowerCase() };

    b.addEventListener('mouseenter', () => open(pin));
    b.addEventListener('mouseleave', () => { if (pinned !== pin) close(); });
    b.addEventListener('focus', () => open(pin));
    b.addEventListener('blur', () => { if (pinned !== pin) close(); });
    b.addEventListener('click', (e) => {
      e.stopPropagation(); pinned = pinned === pin ? null : pin;
      if (!pinned) return close();
      // метку в центр видимой части, чтобы карточка не упиралась в край (важно на телефоне)
      map.easeTo({ center: pin.lngLat, padding: pad(), duration: reduce ? 0 : 500 });
      map.once('moveend', () => { if (pinned === pin) open(pin); });
      open(pin);
    });
    row.addEventListener('mouseenter', () => b.classList.add('is-hot'));
    row.addEventListener('mouseleave', () => b.classList.remove('is-hot'));
    row.querySelector('.row__go').addEventListener('click', () => goTo(pin));
    if (row.dataset.photo) later0(() => { new Image().src = row.dataset.photo; });
    return pin;
  });

  function open(pin) {
    pins.forEach((p) => { p.b.classList.toggle('is-open', p === pin); p.row.classList.toggle('is-hot', p === pin); });
    popup?.remove();
    // карточка открывается туда, где больше места: вверх от метки или вниз
    const y = map.project(pin.lngLat).y, above = y - pad().top, under = mapEl.clientHeight - y, CARD = 360;
    const below = above < CARD && under > above;
    popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, anchor: below ? 'top' : 'bottom', offset: below ? 12 : 34, maxWidth: 'none', className: 'pop' })
      .setLngLat(pin.lngLat).setDOMContent(card(pin.row)).addTo(map);
  }
  function close() {
    pins.forEach((p) => { p.b.classList.remove('is-open'); p.row.classList.remove('is-hot'); });
    popup?.remove();
    if (pinned) open(pinned);
  }
  function goTo(pin) {
    finish();
    if (scrolly) window.scrollTo({ top: hero.offsetTop + range() + 4, behavior: 'smooth' });   // карта на весь экран
    else hero.scrollIntoView();
    pinned = pin;
    map.flyTo({ center: pin.lngLat, padding: scrolly ? { top: 0, right: 0, bottom: 0, left: 0 } : pad(), zoom: 16.4, pitch: 60, bearing: map.getBearing() + 30, duration: reduce ? 0 : 2200, essential: true });
    open(pin);
  }
  map.on('click', () => { pinned = null; close(); });

  /* ---------- фильтр и поиск ---------- */
  let kind = 'all', query = '';
  function applyFilter() {
    let shown = 0;
    pins.forEach((p) => {
      const ok = (kind === 'all' || p.kind === kind) && (!query || p.text.includes(query));
      p.row.hidden = !ok; p.b.classList.toggle('is-off', !ok); if (ok) shown++;
    });
    $('rows-empty').hidden = shown > 0;
    if (pinned && pinned.row.hidden) { pinned = null; close(); }
  }
  document.querySelectorAll('.seg__b').forEach((btn) => btn.addEventListener('click', () => {
    kind = btn.dataset.filter;
    document.querySelectorAll('.seg__b').forEach((x) => x.setAttribute('aria-pressed', String(x === btn)));
    applyFilter();
  }));
  $('q').addEventListener('input', (e) => { query = e.target.value.trim().toLowerCase(); applyFilter(); });
  $('search').addEventListener('submit', (e) => {
    e.preventDefault();
    const first = pins.find((p) => !p.row.hidden);
    if (query && first) goTo(first);
  });

  /* ---------- интро: улицы рисуются от центра к окраинам ---------- */
  const sketchIds = [];
  let raf = 0, timers = [], state = 'idle';
  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  const ease = (t) => 1 - Math.pow(1 - t, 3);

  function buildSketch() {
    const seen = new Set(), feats = [];
    const d2 = (p) => { const dx = (p[0] - CENTER[0]) * 0.77, dy = p[1] - CENTER[1]; return dx * dx + dy * dy; };
    for (const f of map.querySourceFeatures('omt', { sourceLayer: 'transportation' })) {
      const g = f.geometry;
      const lines = g.type === 'LineString' ? [g.coordinates] : g.type === 'MultiLineString' ? g.coordinates : [];
      for (let line of lines) {
        if (line.length < 2) continue;
        const key = `${line[0]}|${line[line.length - 1]}|${line.length}`;
        if (seen.has(key)) continue; seen.add(key);
        if (d2(line[line.length - 1]) < d2(line[0])) line = line.slice().reverse();
        feats.push({ type: 'Feature', properties: { d: d2(line[0]), m: MAJOR.includes(f.properties.class) ? 1 : 0 }, geometry: { type: 'LineString', coordinates: line } });
      }
    }
    feats.sort((a, b) => a.properties.d - b.properties.d);
    feats.forEach((f, i) => { f.properties.r = Math.min(RINGS - 1, Math.floor((i / feats.length) * RINGS)); });
    return feats;
  }

  const gradient = (p, color) => {
    const t = Math.min(0.998, Math.max(0.002, p));
    return ['interpolate', ['linear'], ['line-progress'], 0, p <= 0 ? C.clear : color, t - 0.001, p <= 0 ? C.clear : color, t, p >= 1 ? color : C.clear, 1, p >= 1 ? color : C.clear];
  };

  function addSketch() {
    removeSketch();
    const feats = buildSketch();
    if (!feats.length) return false;
    map.addSource('sketch', { type: 'geojson', lineMetrics: true, data: { type: 'FeatureCollection', features: feats } });
    for (let r = 0; r < RINGS; r++) for (const m of [0, 1]) {
      const id = `sketch-${r}-${m}`;
      map.addLayer({ id, type: 'line', source: 'sketch', filter: ['all', ['==', ['get', 'r'], r], ['==', ['get', 'm'], m]],
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-width': m ? w(1.6, 3, 6) : w(0.7, 1.3, 3), 'line-gradient': gradient(0, m ? C.ink : C.contour), 'line-opacity': 1 } }, 'buildings');
      sketchIds.push(id);
    }
    return true;
  }
  function removeSketch() {
    sketchIds.splice(0).forEach((id) => map.getLayer(id) && map.removeLayer(id));
    if (map.getSource('sketch')) map.removeSource('sketch');
  }

  function reveal(on) {
    REVEAL.forEach(([id, prop, to]) => map.setPaintProperty(id, prop, on ? to : 0));
  }
  function rise(ms) {
    const t0 = performance.now();
    const step = (now) => {
      const k = ms ? ease(Math.min(1, (now - t0) / ms)) : 1;
      map.setPaintProperty('buildings', 'fill-extrusion-height', ['*', HEIGHT, k]);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    step(t0);
  }
  function landPins(on) { pins.forEach((p) => p.b.classList.toggle('is-up', !on)); }
  function interactive(on) {
    ['dragPan', 'dragRotate', 'touchZoomRotate', 'doubleClickZoom', 'keyboard'].forEach((h) => map[h][on ? 'enable' : 'disable']());
  }
  function stop() { cancelAnimationFrame(raf); timers.splice(0).forEach(clearTimeout); map.stop(); }

  // итоговое состояние без анимации (reduced motion, «пропустить», переход к метке)
  function finish() {
    if (state === 'done') return;
    stop(); state = 'done';
    removeSketch(); reveal(true); rise(0); landPins(true); interactive(true);
    if (map.getPitch() < 5) map.jumpTo(tilted());
  }

  function play() {
    stop(); state = 'playing';
    pinned = null; close(); landPins(false); interactive(false); reveal(false);
    map.setPaintProperty('buildings', 'fill-extrusion-height', 0);
    map.jumpTo(flat());
    map.once('idle', () => {
      if (state !== 'playing') return;
      if (!addSketch()) return finish();
      const DUR = 2200, GAP = 480, total = DUR + GAP * (RINGS - 1);
      const t0 = performance.now();
      const draw = (now) => {
        const t = now - t0;
        for (let r = 0; r < RINGS; r++) {
          const p = ease(Math.min(1, Math.max(0, (t - r * GAP) / DUR)));
          map.setPaintProperty(`sketch-${r}-0`, 'line-gradient', gradient(p, C.contour));
          map.setPaintProperty(`sketch-${r}-1`, 'line-gradient', gradient(p, C.ink));
        }
        if (t < total) raf = requestAnimationFrame(draw);
      };
      raf = requestAnimationFrame(draw);

      later(() => {                                   // карта проявляется под рисунком
        reveal(true);
        sketchIds.forEach((id) => map.setPaintProperty(id, 'line-opacity', 0));
      }, total + 200);
      later(() => {                                   // камера наклоняется, здания поднимаются
        map.easeTo({ ...tilted(), duration: 3200, easing: (t) => t * t * (3 - 2 * t), essential: true });
        rise(2600);
      }, total + 700);
      later(() => { removeSketch(); landPins(true); }, total + 3300);
      later(() => { state = 'done'; interactive(true); map.setPadding(pad()); }, total + 4100);
    });
  }

  /* ---------- прокрутка: заголовок уходит, карта раскрывается ---------- */
  let ticking = false;
  function onScroll() {
    ticking = false;
    const next = Math.min(1, Math.max(0, (window.scrollY - hero.offsetTop) / range()));
    if (next === p) return;
    p = next;
    hero.style.setProperty('--p', p.toFixed(4));
    copy.classList.toggle('is-gone', p > 0.72);
    if (state === 'done' && !map.isMoving()) map.setPadding(pad());
  }
  if (scrolly) {
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
    addEventListener('resize', () => { measure(); if (state === 'done') map.setPadding(pad()); });
    document.fonts?.ready.then(() => { measure(); onScroll(); });
    onScroll();
  }

  map.on('load', () => (reduce ? finish() : play()));
  mapEl.addEventListener('pointerdown', () => { if (state === 'playing') finish(); });   // клик по карте пропускает интро
})();
