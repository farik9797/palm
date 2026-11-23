/* Контакты: карта города и форма записи на показ (в макете заявка никуда не уходит). */
(() => {
  const form = document.getElementById('show'), note = document.getElementById('form-note');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const bad = [...form.querySelectorAll('[required]')].find((f) => !f.value.trim());
    if (bad) { note.textContent = 'Укажите имя и телефон.'; note.hidden = false; bad.focus(); return; }
    note.textContent = 'Это макет: заявка пока никуда не отправлена. Отправку подключим к почте или CRM.';
    note.hidden = false;
  });

  const el = document.getElementById('cmap');
  if (!el || !window.maplibregl) return;
  const css = getComputedStyle(document.documentElement);
  const c = (n) => css.getPropertyValue(n).trim();
  const NAME = ['coalesce', ['get', 'name:ru'], ['get', 'name']];
  const line = ['==', ['geometry-type'], 'LineString'];
  const map = new maplibregl.Map({
    container: el, center: [64.4168, 39.7742], zoom: 13.2, minZoom: 12, maxZoom: 18,
    maxBounds: [[64.30, 39.70], [64.53, 39.85]],
    scrollZoom: false, cooperativeGestures: matchMedia('(pointer: coarse)').matches,
    locale: { 'CooperativeGesturesHandler.MobileHelpText': 'Двигайте карту двумя пальцами' },
    attributionControl: { compact: true },
    style: {
      version: 8,
      glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
      sources: { omt: { type: 'vector', url: 'https://tiles.openfreemap.org/planet' } },
      layers: [
        { id: 'paper', type: 'background', paint: { 'background-color': c('--color-land') } },
        { id: 'green', type: 'fill', source: 'omt', 'source-layer': 'landcover', filter: ['in', ['get', 'class'], ['literal', ['grass', 'wood', 'farmland']]], paint: { 'fill-color': c('--color-green-soft') } },
        { id: 'water', type: 'fill', source: 'omt', 'source-layer': 'water', paint: { 'fill-color': c('--color-water') } },
        { id: 'road-case', type: 'line', source: 'omt', 'source-layer': 'transportation', filter: line, layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': c('--color-road-case'), 'line-width': ['interpolate', ['exponential', 1.6], ['zoom'], 12, 1.4, 15, 5, 18, 20] } },
        { id: 'road', type: 'line', source: 'omt', 'source-layer': 'transportation', filter: line, layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': c('--color-sheet'), 'line-width': ['interpolate', ['exponential', 1.6], ['zoom'], 12, 0.6, 15, 3.6, 18, 17] } },
        { id: 'buildings', type: 'fill', source: 'omt', 'source-layer': 'building', minzoom: 13, paint: { 'fill-color': c('--color-building') } },
        { id: 'street-names', type: 'symbol', source: 'omt', 'source-layer': 'transportation_name', minzoom: 14.5,
          layout: { 'text-field': NAME, 'text-font': ['Noto Sans Regular'], 'symbol-placement': 'line', 'text-size': 12 },
          paint: { 'text-color': c('--color-ink-2'), 'text-halo-color': c('--color-land'), 'text-halo-width': 1.4 } },
        { id: 'place-names', type: 'symbol', source: 'omt', 'source-layer': 'place', filter: ['in', ['get', 'class'], ['literal', ['suburb', 'neighbourhood', 'quarter']]],
          layout: { 'text-field': NAME, 'text-font': ['Noto Sans Regular'], 'text-size': 13 },
          paint: { 'text-color': c('--color-ink-2'), 'text-halo-color': c('--color-land'), 'text-halo-width': 1.6 } },
      ],
    },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
})();
