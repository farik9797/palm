// Галерея на странице объекта: клик по миниатюре меняет большое фото (без скрипта миниатюра открывает файл).
document.querySelectorAll('.thumbs a').forEach((a) => a.addEventListener('click', (e) => {
  const img = document.querySelector('#photo img'); if (!img) return;
  e.preventDefault(); img.src = a.href;
  document.querySelectorAll('.thumbs a').forEach((x) => x.toggleAttribute('aria-current', x === a));
}));
