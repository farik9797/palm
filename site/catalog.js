/* Каталог: фильтр по типу и поиск по названию. */
(() => {
  const tiles = [...document.querySelectorAll('.tile')];
  const empty = document.getElementById('tiles-empty'), q = document.getElementById('q');
  let kind = 'all';
  const apply = () => {
    const s = q.value.trim().toLowerCase();
    let shown = 0;
    tiles.forEach((t) => {
      const ok = (kind === 'all' || t.dataset.kind === kind) && t.querySelector('.tile__go').textContent.toLowerCase().includes(s);
      t.hidden = !ok; shown += ok;
    });
    empty.hidden = shown > 0;
  };
  document.querySelectorAll('.seg__b').forEach((b) => b.addEventListener('click', () => {
    kind = b.dataset.filter;
    document.querySelectorAll('.seg__b').forEach((x) => x.setAttribute('aria-pressed', x === b));
    apply();
  }));
  q.addEventListener('input', apply);
  document.getElementById('search').addEventListener('submit', (e) => e.preventDefault());
})();
