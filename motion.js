/* Анимации появления: IntersectionObserver добавляет .is-in, всё движение описано в styles.css.
   Без обработчиков прокрутки. При prefers-reduced-motion ничего не прячется и не двигается. */
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;
  const root = document.documentElement;
  root.classList.add('js-motion');

  // группы, которые появляются лесенкой: индекс внутри группы задаёт задержку
  const GROUPS = ['.services__list > li', '.steps > li', '.cities > li', '.facts > div', '.thumbs > *'];
  const SINGLE = ['.sec h2', '.services__lead', '.index__head', '.page__head', '.about__text > *', '.about__photo',
                  '.company h2', '.how h2', '.contacts__info > *', '.form', '.obj__media', '.obj__info > :not(.facts)', '.band__in > *'];
  const els = new Set();
  GROUPS.forEach((sel) => document.querySelectorAll(sel).forEach((el) => {
    el.style.setProperty('--i', Math.min([...el.parentElement.children].indexOf(el), 8));
    els.add(el);
  }));
  SINGLE.forEach((sel) => document.querySelectorAll(sel).forEach((el, i) => {
    if (!el.style.getPropertyValue('--i')) el.style.setProperty('--i', el.parentElement.matches('.band__in, .about__text, .contacts__info, .obj__info') ? [...el.parentElement.children].indexOf(el) : 0);
    els.add(el);
  }));
  document.querySelectorAll('.steps').forEach((el) => els.add(el));
  els.forEach((el) => el.classList.add('rv'));
  // списки с фильтром: появляется весь список, строки внутри идут лесенкой (скрытые фильтром не застревают)
  document.querySelectorAll('.rows, .tiles').forEach((list) => {
    [...list.children].forEach((li, i) => li.style.setProperty('--i', Math.min(i, 8)));
    list.classList.add('rv-list'); els.add(list);
  });

  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('is-in');
    io.unobserve(e.target);
  }), { rootMargin: '0px 0px -10% 0px', threshold: 0 });
  els.forEach((el) => io.observe(el));

  // после смены фильтра показанные строки и карточки появляются заново: видно, что фильтр сработал
  window.srReplay = (nodes) => {
    nodes.filter((n) => !n.hidden).slice(0, 12).forEach((n, i) => {
      n.animate([{ opacity: 0, transform: 'translateY(12px)' }, { opacity: 1, transform: 'none' }],
        { duration: 420, delay: i * 35, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', fill: 'backwards' });
    });
  };
})();
