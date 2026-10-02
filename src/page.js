/* Home page scroll choreography (desktop only where it pins). */
(function () {
  if (!window.gsap || !window.ScrollTrigger) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  gsap.registerPlugin(ScrollTrigger);
  const mm = gsap.matchMedia();

  mm.add('(min-width: 861px)', () => {
    // Signatures: vertical scroll pans the dish strip sideways
    const pin = document.querySelector('.sig-pin');
    const track = document.querySelector('.sig-track');
    if (pin && track) {
      const distance = () => Math.max(0, track.scrollWidth - window.innerWidth);
      gsap.to(track, {
        x: () => -distance(), ease: 'none',
        scrollTrigger: { trigger: '#signatures', start: 'top top', end: () => '+=' + distance(), pin: true, scrub: 0.8, invalidateOnRefresh: true },
      });
    }
    // Gallery columns drift at different speeds for depth
    document.querySelectorAll('.col[data-speed]').forEach(col => {
      gsap.fromTo(col, { y: 0 }, {
        y: Number(col.dataset.speed), ease: 'none',
        scrollTrigger: { trigger: '.gallery', start: 'top bottom', end: 'bottom top', scrub: true },
      });
    });
  });

  // Visit backdrop eases slower than the page
  const bg = document.querySelector('[data-visit-bg]');
  if (bg) gsap.fromTo(bg, { yPercent: -6 }, { yPercent: 6, ease: 'none', scrollTrigger: { trigger: '#visit', start: 'top bottom', end: 'bottom top', scrub: true } });

  window.addEventListener('load', () => ScrollTrigger.refresh());
})();
