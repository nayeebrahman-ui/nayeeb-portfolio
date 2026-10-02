/* Hero: a rendered, photoreal frame sequence (green beans -> roast -> Berlin cup) scrubbed by scroll.
   Frames load coarse-to-fine so scrubbing works before every frame has arrived; adjacent frames are
   cross-blended for motion between rendered frames. */
(() => {
  const section = document.getElementById('brew-section');
  const canvas = document.getElementById('brew');
  if (!section || !canvas) return;
  const ctx = canvas.getContext('2d', { alpha: false });
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const copy = section.querySelector('[data-hero-copy]');
  const chapters = [...section.querySelectorAll('[data-chapter]')];
  const finalEl = section.querySelector('[data-final]');
  const steps = [...section.querySelectorAll('[data-step]')];
  const tempEl = section.querySelector('[data-temp]');
  const scrim = section.querySelector('[data-scrim]');

  const N = 90;
  const src = i => `img/hero/f${String(i + 1).padStart(3, '0')}.webp`;
  const frames = new Array(N).fill(null);

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const seg = (p, a, b) => { const t = clamp((p - a) / (b - a)); return t * t * (3 - 2 * t); };

  // scroll progress -> frame position. Hold the first frame while the headline leaves.
  const P0 = 0.04, P1 = 0.97;
  const frameAt = p => clamp((p - P0) / (P1 - P0)) * (N - 1);

  // ---------- canvas ----------
  let W = 0, H = 0, dpr = 1;
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    paint(shown, true);
  }

  function nearestLoaded(i) {
    if (frames[i]) return i;
    for (let d = 1; d < N; d++) {
      if (i - d >= 0 && frames[i - d]) return i - d;
      if (i + d < N && frames[i + d]) return i + d;
    }
    return -1;
  }

  function cover(img, alpha) {
    const cw = canvas.width, ch = canvas.height;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    // portrait screens: keep the subject whole (image ~76% of the height) and feather the edges into the page
    const portrait = cw / ch < 0.9;
    const s = portrait ? Math.max(ch * 0.76 / ih, cw / iw) : Math.max(cw / iw, ch / ih);
    const w = iw * s, h = ih * s;
    const x = (cw - w) / 2, y = portrait ? (ch - h) * 0.46 : (ch - h) / 2;
    ctx.globalAlpha = alpha;
    ctx.drawImage(img, x, y, w, h);
    ctx.globalAlpha = 1;
    return portrait ? [y, y + h] : null;
  }

  function feather(top, bot) {
    const cw = canvas.width, f = 90 * dpr;
    let g = ctx.createLinearGradient(0, top, 0, top + f);
    g.addColorStop(0, 'rgba(13,10,8,1)'); g.addColorStop(1, 'rgba(13,10,8,0)');
    ctx.fillStyle = g; ctx.fillRect(0, top - 1, cw, f + 1);
    g = ctx.createLinearGradient(0, bot - f, 0, bot);
    g.addColorStop(0, 'rgba(13,10,8,0)'); g.addColorStop(1, 'rgba(13,10,8,1)');
    ctx.fillStyle = g; ctx.fillRect(0, bot - f, cw, f + 1);
  }

  let lastKey = '';
  function paint(p, force) {
    let fpos = frameAt(p);
    if (p === target) fpos = Math.round(fpos);
    const i0 = Math.floor(fpos), t = fpos - i0;
    const a = nearestLoaded(i0);
    if (a < 0) return;
    const b = (t > 0.02 && i0 + 1 < N && frames[i0 + 1] && a === i0) ? i0 + 1 : -1;
    const key = a + ':' + b + ':' + (b >= 0 ? t.toFixed(3) : '') + ':' + canvas.width;
    if (key === lastKey && !force) return;
    lastKey = key;
    ctx.fillStyle = '#0d0a08';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const band = cover(frames[a], 1);
    if (b >= 0) cover(frames[b], t);
    if (band) feather(band[0], band[1]);
  }

  // ---------- loading: first frame, then every 16th, 8th, 4th, 2nd, rest ----------
  function load(i) {
    return new Promise(res => {
      if (frames[i]) return res();
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => {
        const done = () => { frames[i] = img; lastKey = ''; kick(); res(); };
        img.decode ? img.decode().then(done, done) : done();
      };
      img.onerror = () => res();
      img.src = src(i);
    });
  }
  function order(firstOnly) {
    if (firstOnly) return [0];
    const seen = new Set([0]), out = [];
    for (const step of [16, 8, 4, 2, 1]) {
      for (let i = 0; i < N; i += step) if (!seen.has(i)) { seen.add(i); out.push(i); }
      if (!seen.has(N - 1)) { seen.add(N - 1); out.push(N - 1); }
    }
    return out;
  }
  async function loadAll() {
    const q = order(false);
    let k = 0;
    const worker = async () => { while (k < q.length) await load(q[k++]); };
    await Promise.all([worker(), worker(), worker(), worker()]);
  }

  // ---------- overlay copy ----------
  // chapter windows: [fade in start, fully in, fade out start, gone]
  const CH = [[0.07, 0.11, 0.2, 0.25], [0.27, 0.31, 0.5, 0.55], [0.56, 0.6, 0.68, 0.72]];
  function overlay(p) {
    const out = seg(p, 0.015, 0.065);
    if (copy) {
      copy.style.opacity = String(1 - out);
      copy.style.transform = `translate3d(0, ${-40 * out}px, 0)`;
      copy.style.filter = out > 0.01 ? `blur(${8 * out}px)` : 'none';
      copy.style.visibility = out >= 1 ? 'hidden' : 'visible';
    }
    if (scrim) scrim.style.opacity = String(1 - seg(p, 0.01, 0.08));
    chapters.forEach((el, i) => {
      const [a, b, c, d] = CH[i] || [2, 2, 2, 2];
      const vin = seg(p, a, b), vout = seg(p, c, d);
      const v = vin * (1 - vout);
      el.style.opacity = String(v);
      el.style.transform = `translate3d(0, ${24 * (1 - vin) - 24 * vout}px, 0)`;
      el.style.filter = v < 0.99 ? `blur(${8 * (1 - v)}px)` : 'none';
      el.style.visibility = v <= 0.001 ? 'hidden' : 'visible';
    });
    // drum temperature follows the rendered roast (frames 22-62)
    if (tempEl) tempEl.textContent = Math.round(lerp(150, 218, seg(p, 0.27, 0.69))) + '°';
    const f = seg(p, 0.88, 0.95);
    if (finalEl) {
      finalEl.style.opacity = String(f);
      finalEl.style.transform = `translate3d(0, ${24 * (1 - f)}px, 0)`;
      finalEl.style.filter = f < 0.99 ? `blur(${8 * (1 - f)}px)` : 'none';
      finalEl.style.visibility = f <= 0.001 ? 'hidden' : 'visible';
    }
    const stepIdx = p < 0.26 ? 0 : p < 0.555 ? 1 : p < 0.73 ? 2 : 3;
    steps.forEach((li, i) => li.classList.toggle('on', i === stepIdx && p > 0.02));
    const stepsEl = steps[0] && steps[0].parentElement;
    if (stepsEl) stepsEl.style.opacity = String(seg(p, 0.02, 0.08) * (1 - seg(p, 0.86, 0.92)));
  }

  // ---------- loop: runs only while the value is still settling ----------
  let target = 0, shown = 0, raf = 0;
  function tick() {
    raf = 0;
    // a little inertia so a wheel tick glides instead of jumping
    shown += (target - shown) * 0.16;
    if (Math.abs(target - shown) < 0.0003) shown = target;
    paint(shown);
    overlay(shown);
    if (shown !== target) raf = requestAnimationFrame(tick);
  }
  function kick() { if (!raf) raf = requestAnimationFrame(tick); }

  window.addEventListener('resize', resize);

  if (reduce) {
    // static: the finished cup, no scroll scene
    shown = target = 1;
    load(N - 1).then(() => { resize(); paint(1, true); });
    if (copy) { copy.style.opacity = '1'; copy.style.visibility = 'visible'; }
    resize();
    return;
  }

  function bind() {
    if (window.gsap && window.ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
      ScrollTrigger.create({
        trigger: section, start: 'top top', end: 'bottom bottom',
        onUpdate: self => { target = self.progress; kick(); },
      });
    } else {
      const read = () => { const r = section.getBoundingClientRect(); target = clamp(-r.top / (r.height - innerHeight)); kick(); };
      window.addEventListener('scroll', read, { passive: true });
      read();
    }
  }

  resize();
  overlay(0);
  load(0).then(() => { paint(shown, true); loadAll(); });
  bind();
  kick();
})();
