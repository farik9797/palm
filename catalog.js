/* Каталог: фильтр по городу и типу, поиск по названию. */
(() => {
  const tiles = [...document.querySelectorAll('.tile')];
  const empty = document.getElementById('tiles-empty'), q = document.getElementById('q');
  let kind = 'all', city = 'all';
  const apply = () => {
    const s = q.value.trim().toLowerCase();
    let shown = 0;
    tiles.forEach((t) => {
      const ok = (kind === 'all' || t.dataset.kind === kind) && (city === 'all' || t.dataset.city === city)
        && t.querySelector('.tile__go').textContent.toLowerCase().includes(s);
      t.hidden = !ok; shown += ok;
    });
    empty.hidden = shown > 0;
  };
  const replay = () => window.srReplay?.(tiles);
  const group = (sel, set) => {
    const bs = [...document.querySelectorAll(sel)];
    bs.forEach((b) => b.addEventListener('click', () => { set(b); bs.forEach((x) => x.setAttribute('aria-pressed', x === b)); apply(); replay(); }));
  };
  group('.seg__b[data-filter]', (b) => { kind = b.dataset.filter; });
  group('.seg__b[data-city]', (b) => { city = b.dataset.city; });
  q.addEventListener('input', apply);
  document.getElementById('search').addEventListener('submit', (e) => e.preventDefault());
})();
