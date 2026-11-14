/* SecuRAX shared night sky (reuse-first, owner 2026-11-14): ONE canvas engine every app mounts behind a full screen
   (the lock, a hero). A natural sky, not dots on a gradient:
   - stars by magnitude (most faint, a few bright) and colour temperature (blue-white to orange), each scintillating
     at its own pace; the brightest wear a soft glow and fine diffraction spikes;
   - the Milky Way: a curved band of glowing dust with a warm core, cool edges, dark lanes and thousands of faint stars;
   - one distant spiral galaxy, small and faint, as the eye sees one on a dark night;
   - meteors at an irregular pace, and now and then a slow comet with a glowing coma and a long soft tail.
   Decoration only: the canvas is aria-hidden and ignores pointers. Reduced motion, an automated browser or a hidden page
   gets one still frame and no timer; the loop ends by itself when its element leaves the page.
   Use: SXSky.mount(element) -> { stop() }. The element should be positioned and carry its own dark background colour. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXSky) return;
  var TAU = Math.PI * 2;
  function rng(seed) { var s = seed >>> 0 || 1; return function () { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
  function gauss(r) { return (r() + r() + r() + r() - 2) / 2; }   // about normal, -1..1 mostly
  var TEMPS = [[170, 196, 255], [204, 220, 255], [248, 247, 255], [255, 244, 222], [255, 222, 180], [255, 196, 150]];
  function tint(r) { var x = r(); return TEMPS[x < .12 ? 0 : x < .3 ? 1 : x < .62 ? 2 : x < .82 ? 3 : x < .94 ? 4 : 5]; }

  function mount(el, opts) {
    opts = opts || {};
    var doc = el.ownerDocument, cv = doc.createElement("canvas");
    var ctx = cv.getContext && cv.getContext("2d");
    if (!ctx) return { stop: function () {} };   // no canvas (a test DOM): the element's own background stays
    cv.setAttribute("aria-hidden", "true");
    cv.className = "sx-sky-cv";
    cv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0";
    el.insertBefore(cv, el.firstChild);
    var calm = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
    var still = calm || navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
    var W = 0, H = 0, D = 1, stars = [], bg = null, meteors = [], comet = null, alive = true, raf = 0, last = 0;
    var nextMeteor = 3000 + Math.random() * 5000, nextComet = 9000 + Math.random() * 20000, t0 = 0;
    var R = rng(opts.seed || 20261114);

    function layout() {
      var b = el.getBoundingClientRect();
      W = Math.max(1, Math.round(b.width)); H = Math.max(1, Math.round(b.height)); D = Math.min(2, window.devicePixelRatio || 1);
      cv.width = Math.round(W * D); cv.height = Math.round(H * D);
      R = rng(opts.seed || 20261114);
      bg = paintStatic();
      stars = [];
      var n = Math.round(W * H / 2600 * (opts.density || 1));
      for (var i = 0; i < n; i++) {
        var m = Math.pow(R(), 3.2);                     // magnitude: most stars faint, a few bright
        stars.push({ x: R() * W, y: R() * H, r: .35 + m * 1.55, a: .25 + m * .75, c: tint(R),
          f: .6 + R() * 2.2, p: R() * TAU, k: .18 + R() * .35, spike: m > .94 });
      }
    }
    // The still layers (Milky Way, its dust stars, the distant galaxy) are drawn once to an offscreen canvas.
    function paintStatic() {
      var off = doc.createElement("canvas"); off.width = cv.width; off.height = cv.height;
      var g = off.getContext("2d"); g.scale(D, D);
      // The band: a gentle curve from lower left to upper right.
      var pts = 46, ax = -.1 * W, ay = H * .86, bx = 1.1 * W, by = H * .08, cx = W * .62, cy = H * .62;
      function at(t) { var u = 1 - t; return [u * u * ax + 2 * u * t * cx + t * t * bx, u * u * ay + 2 * u * t * cy + t * t * by]; }
      var wide = Math.min(W, H) * .2;
      g.globalCompositeOperation = "lighter";
      for (var i = 0; i < pts * 4; i++) {
        var t = R(), p = at(t), core = Math.exp(-Math.pow((t - .55) / .22, 2));   // brighter toward the galactic core
        var s = wide * (.45 + R() * .9) * (.7 + core * .6), ox = gauss(R) * wide * .55, oy = gauss(R) * wide * .55;
        var warm = core > .5 && R() < .7, col = warm ? "255,226,190" : (R() < .5 ? "176,196,240" : "214,222,246");
        var gr = g.createRadialGradient(p[0] + ox, p[1] + oy, 0, p[0] + ox, p[1] + oy, s);
        var a = (.014 + core * .024) * (.6 + R() * .8);
        gr.addColorStop(0, "rgba(" + col + "," + a.toFixed(3) + ")"); gr.addColorStop(1, "rgba(" + col + ",0)");
        g.fillStyle = gr; g.beginPath(); g.arc(p[0] + ox, p[1] + oy, s, 0, TAU); g.fill();
      }
      // Dark dust lanes along the band.
      g.globalCompositeOperation = "destination-out";
      for (var j = 0; j < 60; j++) {
        var t2 = .2 + R() * .7, q = at(t2), s2 = wide * (.12 + R() * .3);
        var dx = q[0] + gauss(R) * wide * .18, dy = q[1] + gauss(R) * wide * .18;
        var d = g.createRadialGradient(dx, dy, 0, dx, dy, s2);
        d.addColorStop(0, "rgba(0,0,0," + (.25 + R() * .3).toFixed(2) + ")"); d.addColorStop(1, "rgba(0,0,0,0)");
        g.fillStyle = d; g.beginPath(); g.arc(dx, dy, s2, 0, TAU); g.fill();
      }
      // Thousands of faint stars crowded into the band.
      g.globalCompositeOperation = "lighter";
      var dust = Math.round(W * H / 260 * (opts.density || 1));
      for (var k = 0; k < dust; k++) {
        var t3 = R(), r3 = at(t3), sp = wide * (.35 + Math.exp(-Math.pow((t3 - .55) / .22, 2)) * .5);
        var x = r3[0] + gauss(R) * sp, y = r3[1] + gauss(R) * sp, c = tint(R);
        g.fillStyle = "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + (.08 + R() * .32).toFixed(2) + ")";
        g.fillRect(x, y, .6 + R() * .5, .6 + R() * .5);
      }
      // A distant spiral galaxy: two logarithmic arms of faint light round a bright nucleus, tilted into an ellipse.
      var gx = W * (opts.galaxyX || .24), gy = H * (opts.galaxyY || .2), gs = Math.min(W, H) * .07;
      g.save(); g.translate(gx, gy); g.rotate(-.5); g.scale(1, .42);
      var nuc = g.createRadialGradient(0, 0, 0, 0, 0, gs * .5);
      nuc.addColorStop(0, "rgba(255,240,214,.55)"); nuc.addColorStop(.4, "rgba(240,224,210,.16)"); nuc.addColorStop(1, "rgba(200,210,240,0)");
      g.fillStyle = nuc; g.beginPath(); g.arc(0, 0, gs * .5, 0, TAU); g.fill();
      for (var arm = 0; arm < 2; arm++) {
        for (var m2 = 0; m2 < 420; m2++) {
          var th = m2 / 420 * 3.4 * Math.PI, rr = gs * .08 * Math.exp(.2 * th), ang = th + arm * Math.PI;
          var px = Math.cos(ang) * rr + gauss(R) * gs * .05, py = Math.sin(ang) * rr + gauss(R) * gs * .05;
          g.fillStyle = "rgba(" + (R() < .5 ? "190,206,255" : "236,228,246") + "," + (.16 * (1 - m2 / 460)).toFixed(3) + ")";
          g.fillRect(px, py, 1.1, 1.1);
        }
      }
      g.restore();
      g.globalCompositeOperation = "source-over";
      return off;
    }
    function star(s, t) {
      var tw = still ? 1 : 1 - s.k * (.5 + .5 * Math.sin(s.p + t * s.f * .001 * TAU / 3)) * (.7 + .3 * Math.sin(t * .0023 * s.f + s.p * 2));
      var a = Math.max(.05, s.a * tw), c = s.c;
      if (s.r > 1.1) {
        var gl = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, s.r * 5);
        gl.addColorStop(0, "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + (a * .45).toFixed(3) + ")");
        gl.addColorStop(1, "rgba(" + c[0] + "," + c[1] + "," + c[2] + ",0)");
        ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(s.x, s.y, s.r * 5, 0, TAU); ctx.fill();
      }
      ctx.fillStyle = "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a.toFixed(3) + ")";
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, TAU); ctx.fill();
      if (s.spike) {
        ctx.strokeStyle = "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + (a * .28).toFixed(3) + ")"; ctx.lineWidth = .5;
        var L = s.r * 5 * (.8 + .2 * tw);
        ctx.beginPath(); ctx.moveTo(s.x - L, s.y); ctx.lineTo(s.x + L, s.y); ctx.moveTo(s.x, s.y - L); ctx.lineTo(s.x, s.y + L); ctx.stroke();
      }
    }
    function spawnMeteor() {
      var ang = (.12 + Math.random() * .5) + (Math.random() < .5 ? 0 : Math.PI - .74), sp = .5 + Math.random() * .5;
      meteors.push({ x: Math.random() * W, y: Math.random() * H * .5, vx: Math.cos(ang) * sp, vy: Math.abs(Math.sin(ang)) * sp,
        len: 70 + Math.random() * 120, life: 0, max: 700 + Math.random() * 600 });
    }
    function drawMeteor(m) {
      var k = m.life / m.max, a = k < .15 ? k / .15 : 1 - (k - .15) / .85, hx = m.x + m.vx * m.life, hy = m.y + m.vy * m.life;
      var n = Math.hypot(m.vx, m.vy), tx = hx - m.vx / n * m.len, ty = hy - m.vy / n * m.len;
      var g = ctx.createLinearGradient(hx, hy, tx, ty);
      g.addColorStop(0, "rgba(255,255,255," + (.95 * a).toFixed(3) + ")"); g.addColorStop(.25, "rgba(210,228,255," + (.45 * a).toFixed(3) + ")"); g.addColorStop(1, "rgba(160,190,255,0)");
      ctx.strokeStyle = g; ctx.lineWidth = 1.4; ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(tx, ty); ctx.stroke();
      var h = ctx.createRadialGradient(hx, hy, 0, hx, hy, 4); h.addColorStop(0, "rgba(255,255,255," + a.toFixed(3) + ")"); h.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = h; ctx.beginPath(); ctx.arc(hx, hy, 4, 0, TAU); ctx.fill();
    }
    function spawnComet() {
      var fromLeft = Math.random() < .5;
      comet = { x0: fromLeft ? -.1 * W : 1.1 * W, y0: H * (.1 + Math.random() * .25), x1: fromLeft ? 1.1 * W : -.1 * W,
        y1: H * (.15 + Math.random() * .3), life: 0, max: 38000 + Math.random() * 14000 };
    }
    function drawComet(c) {
      var k = c.life / c.max, a = Math.min(1, k * 8, (1 - k) * 8), x = c.x0 + (c.x1 - c.x0) * k, y = c.y0 + (c.y1 - c.y0) * k;
      var dx = c.x1 - c.x0, dy = c.y1 - c.y0, n = Math.hypot(dx, dy), ux = -dx / n, uy = -dy / n, L = Math.min(W, H) * .32;
      // The tail points away from travel, widening and fading; a faint second (ion) tail runs straighter.
      ctx.save(); ctx.globalCompositeOperation = "lighter";
      for (var i = 0; i < 2; i++) {
        var len = L * (i ? 1.25 : 1), bend = i ? 0 : .12, tx = x + ux * len - uy * len * bend, ty = y + uy * len + ux * len * bend;
        var g = ctx.createLinearGradient(x, y, tx, ty);
        var col = i ? "150,190,255" : "255,236,200";
        g.addColorStop(0, "rgba(" + col + "," + (.42 * a).toFixed(3) + ")"); g.addColorStop(1, "rgba(" + col + ",0)");
        ctx.strokeStyle = g; ctx.lineCap = "round";
        for (var w = 1; w <= 3; w++) { ctx.lineWidth = (i ? 1.2 : 2.6) * w; ctx.globalAlpha = .5 / w; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + ux * len * .5, y + uy * len * .5, tx, ty); ctx.stroke(); }
      }
      ctx.globalAlpha = 1;
      var co = ctx.createRadialGradient(x, y, 0, x, y, 9); co.addColorStop(0, "rgba(255,252,240," + a.toFixed(3) + ")"); co.addColorStop(.3, "rgba(220,236,255," + (.5 * a).toFixed(3) + ")"); co.addColorStop(1, "rgba(180,210,255,0)");
      ctx.fillStyle = co; ctx.beginPath(); ctx.arc(x, y, 9, 0, TAU); ctx.fill();
      ctx.restore();
    }
    function frame(t) {
      if (!alive) return;
      if (!el.isConnected) { stop(); return; }
      if (!t0) t0 = t;
      var dt = last ? Math.min(64, t - last) : 16; last = t;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.drawImage(bg, 0, 0); ctx.setTransform(D, 0, 0, D, 0, 0);
      for (var i = 0; i < stars.length; i++) star(stars[i], t);
      if (!still) {
        nextMeteor -= dt; if (nextMeteor <= 0) { spawnMeteor(); nextMeteor = 6000 + Math.random() * 9000; }
        nextComet -= dt; if (!comet && nextComet <= 0) { spawnComet(); nextComet = 90000 + Math.random() * 60000; }
        meteors = meteors.filter(function (m) { m.life += dt; if (m.life < m.max) { drawMeteor(m); return true; } return false; });
        if (comet) { comet.life += dt; if (comet.life < comet.max) drawComet(comet); else comet = null; }
        raf = requestAnimationFrame(frame);
      } else if (comet) drawComet(comet);
    }
    function onVis() { if (!alive || still) return; cancelAnimationFrame(raf); last = 0; if (!doc.hidden) raf = requestAnimationFrame(frame); }
    function onResize() { if (!alive) return; layout(); if (still) frame(0); }
    function stop() {
      alive = false; cancelAnimationFrame(raf);
      doc.removeEventListener("visibilitychange", onVis); window.removeEventListener("resize", onResize);
      if (cv.parentNode) cv.parentNode.removeChild(cv);
    }
    layout();
    if (opts.comet) { spawnComet(); comet.life = comet.max * .3; }   // a hero screen may open with the comet already in the sky
    if (still) frame(0); else raf = requestAnimationFrame(frame);
    doc.addEventListener("visibilitychange", onVis); window.addEventListener("resize", onResize);
    return { stop: stop };
  }
  // The gold seal for a lock or a hero: a polished turning ring, a breathing glow, a line-drawn padlock with a glowing
  // keyhole. Its look is .sx-seal in shared/lux.css. Decoration only (aria-hidden).
  // A round brilliant seen from above, as on a watch bezel: the table, star and kite facets in the cold greys and whites a
  // real diamond throws back, with a spectral flash (its fire) and a sparkle now and then (lux.css .sx-seal-gem).
  function gem() {
    var c = 11, R = 10, r = 5.2, pts = [], i, a, h = "";
    for (i = 0; i < 8; i++) { a = i / 8 * Math.PI * 2 - Math.PI / 8; pts.push([c + Math.cos(a) * R, c + Math.sin(a) * R, c + Math.cos(a) * r, c + Math.sin(a) * r]); }
    var shades = ["#ffffff", "#c9d3e0", "#eef3fa", "#8e9bb0", "#f7fbff", "#b4c0d2", "#e2e9f4", "#9aa6ba"];
    for (i = 0; i < 8; i++) {
      var p = pts[i], q = pts[(i + 1) % 8];
      h += '<path d="M' + p[0].toFixed(2) + " " + p[1].toFixed(2) + "L" + q[0].toFixed(2) + " " + q[1].toFixed(2) + "L" + q[2].toFixed(2) + " " + q[3].toFixed(2) + "L" + p[2].toFixed(2) + " " + p[3].toFixed(2) + 'Z" fill="' + shades[i] + '"/>';
    }
    var tbl = pts.map(function (p) { return p[2].toFixed(2) + " " + p[3].toFixed(2); }).join(" L");
    h += '<path d="M' + tbl + 'Z" fill="url(#sxGemT)"/>';
    return '<span class="sx-seal-gem"><svg viewBox="0 0 22 22" width="22" height="22"><defs><linearGradient id="sxGemT" x1="0" y1="0" x2="1" y2="1">'
      + '<stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#dfe7f2"/><stop offset="1" stop-color="#aab6c8"/></linearGradient></defs>'
      + '<circle cx="11" cy="11" r="10.6" fill="none" stroke="url(#sxSealG)" stroke-width="1.2"/>' + h + '</svg><i></i><b></b></span>';
  }
  function seal() {
    return '<div class="sx-seal" aria-hidden="true"><i class="sx-seal-ring"></i><i class="sx-seal-halo"></i>' + gem()
      + '<svg viewBox="0 0 64 64" width="72" height="72"><defs><linearGradient id="sxSealG" x1="0" y1="0" x2=".35" y2="1">'
      + '<stop offset="0" stop-color="#fff4d2"/><stop offset=".22" stop-color="#ecc979"/><stop offset=".48" stop-color="#a87b26"/><stop offset=".55" stop-color="#8a6118"/>'
      + '<stop offset=".68" stop-color="#d0a24a"/><stop offset=".88" stop-color="#f3d991"/><stop offset="1" stop-color="#a77a22"/></linearGradient></defs>'
      + '<path d="M21 29v-8a11 11 0 0 1 22 0v8" fill="none" stroke="url(#sxSealG)" stroke-width="4" stroke-linecap="round"/>'
      + '<rect x="14" y="28" width="36" height="26" rx="7" fill="#0d1a30" stroke="url(#sxSealG)" stroke-width="3"/>'
      + '<circle class="sx-seal-key" cx="32" cy="39" r="3.6" fill="#f7e7a8"/><path class="sx-seal-key" d="M30.6 41h2.8l1 6h-4.8z" fill="#f7e7a8"/></svg></div>';
  }
  window.SXSky = { mount: mount, seal: seal };
})();
