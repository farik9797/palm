/* Форма «Обсудить проект». В макете заявка никуда не уходит. */
(() => {
  const form = document.getElementById('form'), note = document.getElementById('form-note');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const v = (n) => form.elements[n].value.trim();
    const ok = v('name') && (v('email') || v('phone'));
    note.textContent = ok ? form.dataset.ok : form.dataset.err;
    note.hidden = false;
    if (!ok) (v('name') ? form.elements.email : form.elements.name).focus();
  });
})();
