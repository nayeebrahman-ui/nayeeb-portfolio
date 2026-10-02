/* Mobile navigation sheet */
(function () {
  const btn = document.querySelector('.nav-toggle');
  const sheet = document.getElementById('sheet');
  if (!btn || !sheet) return;
  const setOpen = open => {
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    sheet.hidden = !open;
    btn.innerHTML = open ? btn.dataset.close : btn.dataset.open;
  };
  btn.dataset.open = btn.innerHTML;
  btn.dataset.close = '{{ICON_X}}';
  btn.addEventListener('click', () => setOpen(btn.getAttribute('aria-expanded') !== 'true'));
  sheet.addEventListener('click', e => { if (e.target.closest('a')) setOpen(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') setOpen(false); });
})();
