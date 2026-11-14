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
    var W = 0, H = 0, D = 1, stars = [], bg = null, gal = null, meteors = [], comet = null, alive = true, raf = 0, last = 0;
    var nextMeteor = 3000 + Math.random() * 5000, nextComet = 9000 + Math.random() * 20000, t0 = 0;
    var R = rng(opts.seed || 20261114);

    function layout() {
      var b = el.getBoundingClientRect();
      W = Math.max(1, Math.round(b.width)); H = Math.max(1, Math.round(b.height)); D = Math.min(2, window.devicePixelRatio || 1);
      cv.width = Math.round(W * D); cv.height = Math.round(H * D);
      R = rng(opts.seed || 20261114);
      bg = paintStatic();
      gal = opts.galaxy === false ? null : makeGalaxy();
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
      g.globalCompositeOperation = "source-over";
      return off;
    }
    /* A spiral galaxy as astrophysics describes it (owner, 2026-11-14: "the galaxy must slowly rotate, rendered
       perfectly"). Not a picture turned on a pin:
       - a flat rotation curve, v(r) = v0 (1 - e^(-r/rc)), as measured in real galaxies (the sign of dark matter): every
         star moves at about the same speed, so the inner disc completes its orbit several times faster than the rim
         (differential rotation; the rim turns once in about four minutes here);
       - the arms are a density wave (Lin and Shu): a two-armed logarithmic pattern (pitch 18 degrees, trailing) that
         turns rigidly at its own slower pattern speed while the stars stream through it, so the arms never wind up;
       - gas is squeezed where it enters an arm, so young blue stars and pink H II regions are born there, drift
         downstream with their orbits and fade as they age; dark dust lanes line the inner edge of each arm;
       - an exponential disc of older, warmer stars and a golden central bulge, tilted 56 degrees to the line of sight.
       The disc is drawn face-on in its own layer and then projected, with a soft bloom, as a telescope would see it. */
    /* The aurora (governance/nature-atlas.json, doc 136), drawn from its physics: curtains of light low over the horizon,
       bright at the base where atomic oxygen emits at 557.7 nm (about 100 km up), streaked by vertical rays, fading upward
       into the faint red of oxygen's 630.0 nm line higher up, with a thin violet-blue fringe of nitrogen (427.8 nm) along
       the lower edge. Added as light over the blue night sky, as the eye and the camera see it; it drifts slowly, and is
       recomputed four times a second into a cached image. */
    var AU = null;
    function drawAurora(t) {
      if (!AU) { AU = { cv: doc.createElement("canvas") }; AU.cx = AU.cv.getContext("2d"); }
      var aw = Math.ceil(W / 2), ah = Math.ceil(H * .42);
      if (AU.cv.width !== aw || AU.cv.height !== ah) { AU.cv.width = aw; AU.cv.height = ah; AU.at = -1e9; }
      if (still || t - AU.at > 250 || t < AU.at) {
        AU.at = t; var g = AU.cx, x, k, base, hgt, ray, i, y, f;
        g.globalCompositeOperation = "source-over"; g.clearRect(0, 0, aw, ah); g.globalCompositeOperation = "lighter";
        for (var c = 0; c < 2; c++) {                                   // two curtains, one behind the other
          var amp = ah * (c ? .07 : .1), lift = ah * (c ? .55 : .72), str = c ? .55 : 1;
          for (x = 0; x < aw; x++) {
            k = x / aw;
            base = lift + amp * Math.sin(k * 5.2 + t / 9000 + c * 2) + amp * .5 * Math.sin(k * 13 - t / 6500 + c);
            ray = .42 + .3 * Math.sin(k * 97 + Math.sin(k * 23 + t / 4000) * 3 + c * 4) + .2 * Math.sin(k * 211 - t / 5200 + c) + .12 * Math.sin(k * 37 + t / 7000);   // irregular rays, as in a real curtain
            ray = Math.max(0, Math.min(1, ray));
            f = Math.max(0, Math.sin(Math.PI * Math.min(1, Math.max(0, (k - .04) / .92))));     // fades at both ends
            hgt = ah * (.32 + .14 * Math.sin(k * 7 + t / 11000 + c)) * (.7 + .3 * ray);
            var I = str * ray * f;
            if (I < .02) continue;
            for (i = 0; i < 12; i++) {                                    // up the curtain: green, then red at the top
              y = base - hgt * i / 12; var u = i / 11;
              var a = I * (.3 * Math.pow(1 - u, 1.6) + (i === 0 ? .25 : 0) + (u > .55 ? .07 * (u - .55) * 2 : 0));
              g.fillStyle = u < .6 ? "rgba(70,255,150," + a.toFixed(3) + ")" : "rgba(255,70,40," + (a * .9).toFixed(3) + ")";
              g.fillRect(x, y - hgt / 12, 1, hgt / 12 + .5);
            }
            g.fillStyle = "rgba(90,40,255," + (I * .07).toFixed(3) + ")"; g.fillRect(x, base, 1, ah * .03);   // the nitrogen fringe
          }
        }
      }
      ctx.save(); ctx.globalCompositeOperation = "lighter";
      if ("filter" in ctx) ctx.filter = "blur(2.4px)";
      ctx.drawImage(AU.cv, 0, H - ah, W, ah); ctx.filter = "none"; ctx.restore();
    }
    function makeGalaxy() {
      var G = { R0: Math.min(W, H) * (opts.galaxySize || .14), cx: W * (opts.galaxyX || .27), cy: H * (opts.galaxyY || .115),
        inc: Math.cos(56 * Math.PI / 180), pa: -0.42, parts: [], dust: [] };
      // Every device (principle every-device): the galaxy finds the open sky. Given the element it must not hide behind
      // (the lock card), it takes the larger free band above or below it and sizes itself to fit.
      try {
        var av = typeof opts.avoid === "function" ? opts.avoid() : opts.avoid;
        if (av && av.getBoundingClientRect) {
          var eb = el.getBoundingClientRect(), ab = av.getBoundingClientRect();
          var top = ab.top - eb.top, bot = eb.bottom - ab.bottom, band = Math.max(top, bot), left = ab.left - eb.left, right = eb.right - ab.right;
          if (band >= 70) {
            G.R0 = Math.min(G.R0, band * .44 / .62); G.cy = top >= bot ? top / 2 : ab.bottom - eb.top + bot / 2;
            G.cx = Math.max(G.R0 * 1.05, Math.min(W - G.R0 * 1.05, W * .3));
          } else if (Math.max(left, right) > 150) {                       // a short, wide screen: the side beside the card
            var sw = Math.max(left, right); G.R0 = Math.min(G.R0, sw * .36); G.cy = H * .3;
            G.cx = left >= right ? left / 2 : ab.right - eb.left + right / 2;
          }
        }
      } catch (e) {}
      var R0 = G.R0, h = R0 * .34, rc = R0 * .16, P = 240000;               // rim period, ms
      var v0 = TAU * R0 / P, k = 1 / Math.tan(18 * Math.PI / 180), rin = R0 * .14;
      G.om = function (r) { r = Math.max(r, R0 * .02); return v0 * (1 - Math.exp(-r / rc)) / r; };
      G.omp = G.om(R0 * .62);                                              // the pattern turns with the disc at corotation
      G.arm = function (r) { return -k * Math.log(Math.max(r, rin) / rin); };   // trailing arms
      function rdisc() { var r; do { r = -h * Math.log(Math.max(1e-6, R() * R())); } while (r > R0); return r; }
      var i, r;
      for (i = 0; i < 1500; i++) {                                         // the old disc: warm white, everywhere
        r = rdisc(); G.parts.push({ r: r, t0: R() * TAU, kind: 0, b: .25 + R() * .5, s: .8 + R() * .5 });
      }
      for (i = 0; i < 520; i++) {                                          // the bulge: old, golden, nearly solid-body
        r = R0 * .2 * Math.pow(-Math.log(Math.max(1e-6, R())), 1.6) * .5; if (r > R0 * .38) { i--; continue; }
        G.parts.push({ r: r, t0: R() * TAU, kind: 1, b: .35 + R() * .6, s: .8 + R() * .6 });
      }
      // Star formation is clumpy: clusters strung along each arm like beads, with dimmer gaps between them.
      var clumps = [];
      for (i = 0; i < 80; i++) clumps.push({ r: R0 * (.17 + .78 * Math.pow(R(), .9)), side: i % 2 ? Math.PI : 0, j: gauss(R) * .12, w: .4 + R() * .8 });
      for (i = 0; i < 520; i++) {                                          // the arms' own glow: unresolved young light and gas
        r = R0 * (.15 + .8 * Math.pow(R(), .85));
        G.parts.push({ r: r, kind: 3, side: R() < .5 ? 0 : Math.PI, j: gauss(R) * .2, b: .035 + R() * .05, s: 3 + R() * 3.5 });
      }
      for (i = 0; i < 1700; i++) {                                         // young stars, born in clusters on the arms
        var cl = clumps[(R() * clumps.length) | 0];
        if (R() > cl.w) { cl = { r: R0 * (.17 + .78 * R()), side: R() < .5 ? 0 : Math.PI, j: gauss(R) * .22 }; }
        r = Math.max(R0 * .15, Math.min(R0 * .97, cl.r + gauss(R) * R0 * .035));
        G.parts.push({ r: r, kind: 2, side: cl.side, j: cl.j + gauss(R) * .06, age: R(), b: .22 + R() * .42, s: .8 + R() * .8 });
      }
      for (i = 0; i < 620; i++) {                                          // dust on the inner edge of each arm
        r = R0 * (.16 + .74 * R());
        if (R() < .35) { i--; continue; }   // patchy, not a drawn line
        G.dust.push({ r: r, side: R() < .5 ? 0 : Math.PI, j: gauss(R) * .09 - .19, a: .035 + R() * .07, s: 2.4 + R() * 3.6 });
      }
      var sz = Math.ceil(R0 * 2.3 * D);
      G.cv = doc.createElement("canvas"); G.cv.width = G.cv.height = sz; G.cx2 = G.cv.getContext("2d");
      // The smooth light underneath the resolved stars: an exponential disc and a bright bulge.
      G.base = doc.createElement("canvas"); G.base.width = G.base.height = sz;
      var b = G.base.getContext("2d"), c = sz / 2, sc = D, gr;
      gr = b.createRadialGradient(c, c, 0, c, c, R0 * sc);
      [[0, .34], [.15, .2], [.35, .1], [.6, .04], [1, 0]].forEach(function (q) { gr.addColorStop(q[0], "rgba(232,222,206," + q[1] + ")"); });
      b.fillStyle = gr; b.fillRect(0, 0, sz, sz);
      gr = b.createRadialGradient(c, c, 0, c, c, R0 * .32 * sc);
      [[0, .95], [.08, .7], [.3, .28], [.65, .08], [1, 0]].forEach(function (q) { gr.addColorStop(q[0], "rgba(255,232,190," + q[1] + ")"); });
      b.fillStyle = gr; b.fillRect(0, 0, sz, sz);
      return G;
    }
    // The galaxy turns so slowly that a star near the core moves under a third of a pixel in a quarter of a second, so it is
    // recomputed four times a second into a cached image (bloom included) and only placed each frame: smooth motion at a
    // fraction of the cost (test campaign: 19 -> 7 frames a second on a slowed phone without the cache).
    function drawGalaxy(t) {
      var G = gal, hw = G.cv.width / 2 / D;
      if (!G.out || still || t - G.at > 250 || t < G.at) { renderGalaxy(t); G.at = t; }
      ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.drawImage(G.out, G.cx - hw, G.cy - hw, hw * 2, hw * 2); ctx.restore();
    }
    function renderGalaxy(t) {
      var G = gal, g = G.cx2, sz = G.cv.width, c = sz / 2, sc = D, i, p, th, x, y, a, life = 1, n;
      g.globalCompositeOperation = "source-over"; g.clearRect(0, 0, sz, sz); g.drawImage(G.base, 0, 0);
      g.globalCompositeOperation = "lighter";
      for (i = 0; i < G.parts.length; i++) {
        p = G.parts[i];
        if (p.kind === 3) {                                              // arm glow: moves with the pattern
          th = G.arm(p.r) + p.side + p.j + G.omp * t;
          x = c + Math.cos(th) * p.r * sc; y = c + Math.sin(th) * p.r * sc;
          g.fillStyle = "rgba(150,180,255," + p.b.toFixed(3) + ")"; g.beginPath(); g.arc(x, y, p.s * sc * .5, 0, TAU); g.fill();
          continue;
        }
        if (p.kind === 2) {
          // A young star: born on the arm (pattern angle then), carried by its own orbit since, fading with age.
          a = (p.age + t / 90000) % 1;
          th = G.arm(p.r) + p.side + p.j + G.omp * (t - a * 90000) + G.om(p.r) * a * 90000;
          life = Math.exp(-a * 2.3);
          x = c + Math.cos(th) * p.r * sc; y = c + Math.sin(th) * p.r * sc;
          if (a < .14 && p.b > .78) { g.fillStyle = "rgba(255,118,168," + (.7 * (1 - a / .14)).toFixed(3) + ")"; g.beginPath(); g.arc(x, y, 1.6 * sc, 0, TAU); g.fill(); }
          g.fillStyle = "rgba(168,196,255," + (p.b * life).toFixed(3) + ")";
        } else {
          th = p.t0 + G.om(p.r) * t;
          x = c + Math.cos(th) * p.r * sc; y = c + Math.sin(th) * p.r * sc;
          g.fillStyle = p.kind === 1 ? "rgba(255,226,176," + p.b.toFixed(3) + ")" : "rgba(238,228,212," + (p.b * .7).toFixed(3) + ")";
        }
        n = p.s * sc * .55; g.fillRect(x, y, n, n);
      }
      g.globalCompositeOperation = "source-over";
      for (i = 0; i < G.dust.length; i++) {
        p = G.dust[i]; th = G.arm(p.r) + p.side + p.j + G.omp * t;
        x = c + Math.cos(th) * p.r * sc; y = c + Math.sin(th) * p.r * sc;
        g.fillStyle = "rgba(6,9,18," + p.a.toFixed(3) + ")"; g.beginPath(); g.arc(x, y, p.s * sc * .5, 0, TAU); g.fill();
      }
      // Project into the cached image: the disc tilted to the line of sight, then a soft bloom as a lens would add.
      if (!G.out) { G.out = doc.createElement("canvas"); G.out.width = G.out.height = sz; G.oc = G.out.getContext("2d"); }
      var o = G.oc; o.setTransform(1, 0, 0, 1, 0, 0); o.clearRect(0, 0, sz, sz);
      o.translate(c, c); o.rotate(G.pa); o.scale(1, G.inc);
      if ("filter" in o) { o.globalCompositeOperation = "lighter"; o.globalAlpha = .55; o.filter = "blur(" + (G.R0 * .05 * D).toFixed(1) + "px)"; o.drawImage(G.cv, -c, -c); o.filter = "none"; o.globalAlpha = 1; }
      o.globalCompositeOperation = "lighter"; o.drawImage(G.cv, -c, -c);
      o.setTransform(1, 0, 0, 1, 0, 0);
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
      // 30 frames a second is plenty for twinkling and a slow comet, and halves the cost on a modest phone.
      if (!still && last && t - last < 30) { raf = requestAnimationFrame(frame); return; }
      var dt = last ? Math.min(64, t - last) : 16; last = t;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.drawImage(bg, 0, 0); ctx.setTransform(D, 0, 0, D, 0, 0);
      if (opts.aurora) drawAurora(still ? 52000 : t);
      if (gal) drawGalaxy(still ? 41000 : t);
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
