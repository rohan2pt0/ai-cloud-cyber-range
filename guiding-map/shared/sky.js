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
    // The live sky (below): the lock asks for the person's real sky; the stars, galaxy and meteors become its night layer.
    if (opts.live && !opts.offscreen) return liveMount(el, { face: "sun", lock: true, night: opts });
    var doc = el.ownerDocument, cv = doc.createElement("canvas");
    var ctx = cv.getContext && cv.getContext("2d");
    if (!ctx) return { stop: function () {} };   // no canvas (a test DOM): the element's own background stays
    if (!opts.offscreen) {                         // offscreen: a layer the live sky paints between its sky and its clouds
      cv.setAttribute("aria-hidden", "true");
      cv.className = "sx-sky-cv";
      cv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0";
      el.insertBefore(cv, el.firstChild);
    }
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
       recomputed four times a second into a cached image.
       Owner 2026-11-14: the first version read as a barcode on a phone. Its columns were drawn at half width with a
       high-frequency ray pattern, so each became a hard 6-pixel stripe on a 3x screen, and its 12 stacked bands stepped.
       Now: one column per device pixel (up to 2x), the colour up the curtain is ONE smooth profile (a gradient, so no
       steps), and the rays are smooth noise a few pixels wide on a curtain that is always partly lit, as in a photograph. */
    var AU = null;
    function auProfile() {
      // The curtain's colour from the bottom up, as light (premultiplied by its own strength): a thin nitrogen fringe,
      // the sharp bright base of oxygen green, a long fade, and oxygen red at the top.
      var cv = doc.createElement("canvas"); cv.width = 1; cv.height = 256;
      var g = cv.getContext("2d"), gr = g.createLinearGradient(0, 256, 0, 0);
      [[0, "rgba(110,60,255,0)"], [.025, "rgba(110,70,255,.22)"], [.06, "rgba(80,255,170,.95)"], [.12, "rgba(70,250,150,.78)"],
       [.3, "rgba(60,230,140,.42)"], [.52, "rgba(60,200,130,.20)"], [.7, "rgba(170,150,110,.10)"], [.84, "rgba(255,70,60,.09)"],
       [1, "rgba(255,60,50,0)"]].forEach(function (q) { gr.addColorStop(q[0], q[1]); });
      g.fillStyle = gr; g.fillRect(0, 0, 1, 256);
      return cv;
    }
    function smooth(x, seed) {                                          // value noise with a smooth (cubic) step, 0..1
      var i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
      function h(n) { var s = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453; return s - Math.floor(s); }
      return h(i) * (1 - u) + h(i + 1) * u;
    }
    function drawAurora(t) {
      if (!AU) { AU = { cv: doc.createElement("canvas"), prof: auProfile() }; AU.cx = AU.cv.getContext("2d"); }
      // One column per device pixel (up to 2x), and at most about 1.2 million pixels, so a large monitor stays cheap (#287).
      var sc = Math.min(D, 2); if (W * sc * H * .42 * sc > 1200000) sc = Math.sqrt(1200000 / (W * H * .42));
      var aw = Math.ceil(W * sc), ah = Math.ceil(H * .42 * sc);
      if (AU.cv.width !== aw || AU.cv.height !== ah) { AU.cv.width = aw; AU.cv.height = ah; AU.at = -1e9; }
      if (still || t - AU.at > 250 || t < AU.at) {
        AU.at = t; var g = AU.cx, x, k, px, base, hgt, ray, f, I;
        g.globalCompositeOperation = "source-over"; g.clearRect(0, 0, aw, ah); g.globalCompositeOperation = "lighter";
        for (var c = 0; c < 2; c++) {                                   // two curtains, one behind the other
          var amp = ah * (c ? .07 : .1), lift = ah * (c ? .62 : .8), str = c ? .5 : .9;
          for (x = 0; x < aw; x++) {
            k = x / aw; px = x / sc;                                     // px: CSS pixels, so a ray has the same size on every screen
            base = lift + amp * Math.sin(k * 5.2 + t / 9000 + c * 2) + amp * .5 * Math.sin(k * 13 - t / 6500 + c);
            // rays: fine (about 5 px) and broad (about 26 px) smooth noise drifting along the curtain, never a hard edge
            ray = .55 * smooth(px / 5 + t / 2600 + c * 50, 1 + c) + .45 * smooth(px / 26 - t / 5200 + c * 9, 7 + c);
            ray = Math.pow(ray, 1.6);
            f = Math.max(0, Math.sin(Math.PI * Math.min(1, Math.max(0, (k - .03) / .94))));     // fades at both ends
            f *= .35 + .65 * smooth(px / 140 + t / 15000 + c * 3, 13 + c);                       // brighter and fainter stretches
            I = str * f * (.3 + .7 * ray);
            if (I < .015) continue;
            hgt = ah * (.42 + .16 * Math.sin(k * 7 + t / 11000 + c)) * (.75 + .35 * ray);
            g.globalAlpha = Math.min(1, I);
            g.drawImage(AU.prof, 0, 0, 1, 256, x, base - hgt, 1.6, hgt * 1.04);
          }
        }
        g.globalAlpha = 1;
      }
      ctx.save(); ctx.globalCompositeOperation = "lighter";
      if ("filter" in ctx) ctx.filter = "blur(1.2px)";
      ctx.drawImage(AU.cv, 0, H - ah / sc, W, ah / sc); ctx.filter = "none"; ctx.restore();
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
      var v0 = TAU * R0 / P, k = 1 / Math.tan(24 * Math.PI / 180), rin = R0 * .2;   // pitch 24 deg: the arms wind about half a turn, as in M51 or M81, not a full ring
      G.om = function (r) { r = Math.max(r, R0 * .02); return v0 * (1 - Math.exp(-r / rc)) / r; };
      G.omp = G.om(R0 * .62);                                              // the pattern turns with the disc at corotation
      G.arm = function (r) { return -k * Math.log(Math.max(r, rin) / rin); };   // trailing arms
      function rdisc() { var r; do { r = -h * Math.log(Math.max(1e-6, R() * R())); } while (r > R0); return r; }
      var i, r;
      for (i = 0; i < 1500; i++) {                                         // the old disc: warm white, everywhere
        r = rdisc(); G.parts.push({ r: r, t0: R() * TAU, kind: 0, b: .14 + R() * .3, s: .6 + R() * .4 });   // unresolved, mostly: the smooth disc below carries its light
      }
      for (i = 0; i < 520; i++) {                                          // the bulge: old, golden, nearly solid-body
        r = R0 * .2 * Math.pow(-Math.log(Math.max(1e-6, R())), 1.6) * .5; if (r > R0 * .38) { i--; continue; }
        G.parts.push({ r: r, t0: R() * TAU, kind: 1, b: .35 + R() * .6, s: .8 + R() * .6 });
      }
      // Star formation is clumpy: clusters strung along each arm like beads, with dimmer gaps between them.
      var clumps = [];
      for (i = 0; i < 80; i++) clumps.push({ r: R0 * (.2 + .62 * Math.pow(R(), 1.25)), side: i % 2 ? Math.PI : 0, j: gauss(R) * .12, w: .4 + R() * .8 });
      for (i = 0; i < 520; i++) {                                          // the arms' own glow: unresolved young light and gas
        r = R0 * (.18 + .6 * Math.pow(R(), 1.3));
        G.parts.push({ r: r, kind: 3, side: R() < .5 ? 0 : Math.PI, j: gauss(R) * .3, b: .016 + R() * .022, s: 4.5 + R() * 5.5 });
      }
      for (i = 0; i < 1700; i++) {                                         // young stars, born in clusters on the arms
        var cl = clumps[(R() * clumps.length) | 0];
        if (R() > cl.w) { cl = { r: R0 * (.2 + .65 * Math.pow(R(), 1.2)), side: R() < .5 ? 0 : Math.PI, j: gauss(R) * .22 }; }
        r = Math.max(R0 * .18, Math.min(R0 * .9, cl.r + gauss(R) * R0 * .035));
        G.parts.push({ r: r, kind: 2, side: cl.side, j: cl.j + gauss(R) * .06, age: R(), b: .22 + R() * .42, s: .8 + R() * .8 });
      }
      for (i = 0; i < 620; i++) {                                          // dust on the inner edge of each arm
        r = R0 * (.18 + .5 * R());
        if (R() < .35) { i--; continue; }   // patchy, not a drawn line
        G.dust.push({ r: r, side: R() < .5 ? 0 : Math.PI, j: gauss(R) * .08 - .13, a: .006 + R() * .014, s: 3 + R() * 4 });   // dust dims the light behind it; it is never a black line
      }
      var sz = Math.ceil(R0 * 2.3 * D);
      G.cv = doc.createElement("canvas"); G.cv.width = G.cv.height = sz; G.cx2 = G.cv.getContext("2d");
      // The smooth light underneath the resolved stars: an exponential disc and a bright bulge.
      G.base = doc.createElement("canvas"); G.base.width = G.base.height = sz;
      var b = G.base.getContext("2d"), c = sz / 2, sc = D, gr;
      gr = b.createRadialGradient(c, c, 0, c, c, R0 * sc);
      [[0, .42], [.15, .26], [.35, .14], [.6, .05], [.85, .012], [1, 0]].forEach(function (q) { gr.addColorStop(q[0], "rgba(232,222,206," + q[1] + ")"); });
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
          g.fillStyle = "rgba(150,180,255," + (p.b * Math.max(0, 1.25 - 1.15 * p.r / G.R0)).toFixed(3) + ")"; g.beginPath(); g.arc(x, y, p.s * sc * .5, 0, TAU); g.fill();
          continue;
        }
        if (p.kind === 2) {
          // A young star: born on the arm (pattern angle then), carried by its own orbit since, fading with age.
          a = (p.age + t / 90000) % 1;
          th = G.arm(p.r) + p.side + p.j + G.omp * (t - a * 90000) + G.om(p.r) * a * 90000;
          life = Math.exp(-a * 3.2) * (1.15 - .75 * p.r / G.R0);   // young light fades with age and towards the rim, so the edge never reads as a ring
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
      draw(t, dt);
      if (!still) raf = requestAnimationFrame(frame);
    }
    function draw(t, dt) {
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
    if (opts.offscreen) return { cv: cv, resize: layout, stop: function () { alive = false; },
      paint: function (t) { var dt = last ? Math.min(150, Math.max(0, t - last)) : 16; last = t; draw(still ? 0 : t, dt); } };
    if (still) frame(0); else raf = requestAnimationFrame(frame);
    doc.addEventListener("visibilitychange", onVis); window.addEventListener("resize", onResize);
    return { stop: stop };
  }
  /* ─── The live sky (owner 2026-11-23: "show the person's ACTUAL sky right now") ─────────────────────────────────────────
     Every large surface that opts in (data-sx-sky, or SXSky.mount(el, {live: true}) for the lock) shows the sky outside the
     person's window, from real astronomy, a physical daylight model and the real weather:
     - the sun from the NOAA solar position equations (declination, equation of time, hour angle, refraction);
     - the moon from the low-precision lunar ephemeris of the Astronomical Almanac (Meeus ch. 47 truncated, about 0.3 deg),
       corrected for parallax, with its real phase and the bright limb turned toward the sun;
     - the daylight sky from Preetham, Shirley and Smits (1999), "A practical analytic model for daylight": the Perez
       distribution of luminance and chromaticity for a turbidity of 3 (clear) to 6 (haze), from the real sun position;
     - sunlight reddened by its path through the air (Kasten-Young air mass, Rayleigh optical depth by wavelength plus
       aerosol by the Angstrom law), which colours the sun, the glow around it and the lit side of every cloud;
     - twilight bands at -6, -12 and -18 deg; the Earth's shadow and the Belt of Venus opposite the sun at dusk and dawn;
       the stars (the night layer above) fading in with the real twilight; moonlight brightening the sky when it is up;
     - clouds, rain, drizzle, snow and fog from the Open-Meteo reading the wind already makes (with the person's consent,
       same host, same rounded place): cloud cover sets the density of a procedural cloud layer seen in perspective, lit
       from the real sun direction, drifting with the real wind.
     Place, in order: the rounded place the person allowed for the wind (placeSource), else the time zone's city, else 0,0.
     Never asks for anything. Re-solved every 60 s and interpolated between; drawn at most 10 times a second and only while
     visible; reduced motion, jsdom and an automated browser get one still frame. Text stays readable: on a surface that
     carries words, each pixel's luminance is held under a ceiling (a scrim that adapts to the sky), so white text keeps
     WCAG AA at every sun altitude, in both themes. One tap on a surface says what the sky is doing, in one line. */
  var API = {}, RAD = Math.PI / 180;
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function sstep(a, b, x) { var t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
  function n360(x) { x %= 360; return x < 0 ? x + 360 : x; }
  function adiff(a, b) { var d = n360(a - b); return d > 180 ? d - 360 : d; }
  function julian(ms) { return ms / 864e5 + 2440587.5; }
  function refraction(a) {                                   // NOAA's approximation, degrees
    if (a > 85) return 0;
    var te = Math.tan(a * RAD), r;
    if (a > 5) r = 58.1 / te - .07 / (te * te * te) + .000086 / Math.pow(te, 5);
    else if (a > -.575) r = 1735 + a * (-518.2 + a * (103.4 + a * (-12.79 + a * .711)));
    else r = -20.772 / te;
    return r / 3600;
  }
  function horizontal(dec, ha, lat) {                       // equatorial (dec, hour angle) -> altitude, azimuth from north
    var sd = Math.sin(dec * RAD), cd = Math.cos(dec * RAD), sl = Math.sin(lat * RAD), cl = Math.cos(lat * RAD), ch = Math.cos(ha * RAD);
    return { alt: Math.asin(clamp(sl * sd + cl * cd * ch, -1, 1)) / RAD, az: n360(Math.atan2(-Math.sin(ha * RAD) * cd, cl * sd - sl * cd * ch) / RAD) };
  }
  // The sun: the NOAA solar calculator's equations (after Meeus, Astronomical Algorithms).
  function sunAt(ms, lat, lon) {
    var T = (julian(ms) - 2451545) / 36525, s = function (d) { return Math.sin(d * RAD); };
    var L0 = n360(280.46646 + T * (36000.76983 + T * .0003032)), M = 357.52911 + T * (35999.05029 - .0001537 * T);
    var e = .016708634 - T * (.000042037 + .0000001267 * T);
    var C = s(M) * (1.914602 - T * (.004817 + .000014 * T)) + s(2 * M) * (.019993 - .000101 * T) + s(3 * M) * .000289;
    var om = 125.04 - 1934.136 * T, lam = L0 + C - .00569 - .00478 * s(om);
    var eps = 23 + (26 + (21.448 - T * (46.815 + T * (.00059 - T * .001813))) / 60) / 60 + .00256 * Math.cos(om * RAD);
    var dec = Math.asin(s(eps) * s(lam)) / RAD, y = Math.pow(Math.tan(eps * RAD / 2), 2);
    var eot = 4 / RAD * (y * s(2 * L0) - 2 * e * s(M) + 4 * e * y * s(M) * Math.cos(2 * L0 * RAD) - .5 * y * y * s(4 * L0) - 1.25 * e * e * s(2 * M));
    var tst = ((((ms % 864e5) + 864e5) % 864e5 / 6e4 + eot + 4 * lon) % 1440 + 1440) % 1440;   // true solar time, minutes
    var ha = tst / 4 - 180, h = horizontal(dec, ha, lat);
    return { alt: h.alt + refraction(h.alt), az: h.az, dec: dec, eot: eot, ha: ha, lam: n360(lam) };
  }
  // The moon: the Astronomical Almanac's low-precision series (Meeus ch. 47, truncated), topocentric.
  var PHASES = ["new moon", "waxing crescent", "first quarter", "waxing gibbous", "full moon", "waning gibbous", "last quarter", "waning crescent"];
  function moonAt(ms, lat, lon) {
    var d = julian(ms) - 2451545, T = d / 36525, s = function (x) { return Math.sin(x * RAD); }, c = function (x) { return Math.cos(x * RAD); };
    var lam = n360(218.32 + 481267.881 * T + 6.29 * s(135 + 477198.87 * T) - 1.27 * s(259.3 - 413335.36 * T) + .66 * s(235.7 + 890534.22 * T)
      + .21 * s(269.9 + 954397.74 * T) - .19 * s(357.5 + 35999.05 * T) - .11 * s(186.5 + 966404.03 * T));
    var bet = 5.13 * s(93.3 + 483202.02 * T) + .28 * s(228.2 + 960400.89 * T) - .28 * s(318.3 + 6003.15 * T) - .17 * s(217.6 - 407332.21 * T);
    var par = .9508 + .0518 * c(135 + 477198.87 * T) + .0095 * c(259.3 - 413335.36 * T) + .0078 * c(235.7 + 890534.22 * T) + .0028 * c(269.9 + 954397.74 * T);
    var eps = 23.4393 - .013 * T, x = c(bet) * c(lam), y = c(bet) * s(lam), z = s(bet);
    var ye = y * c(eps) - z * s(eps), ze = y * s(eps) + z * c(eps);
    var ra = Math.atan2(ye, x) / RAD, dec = Math.asin(clamp(ze, -1, 1)) / RAD;
    var gmst = 280.46061837 + 360.98564736629 * d + .000387933 * T * T;
    var h = horizontal(dec, n360(gmst + lon - ra), lat), alt = h.alt - par * Math.cos(h.alt * RAD);   // parallax: about 1 deg
    var sl = sunAt(ms, lat, lon).lam, el = n360(lam - sl), psi = Math.acos(clamp(c(bet) * c(lam - sl), -1, 1)) / RAD;
    var illum = (1 - Math.cos(psi * RAD)) / 2;               // phase angle ~ 180 - elongation
    var idx = el < 12 || el > 348 ? 0 : el < 84 ? 1 : el < 96 ? 2 : el < 168 ? 3 : el < 192 ? 4 : el < 264 ? 5 : el < 276 ? 6 : 7;
    return { alt: alt + refraction(alt), az: h.az, illum: illum, elong: el, waxing: el < 180, age: el / 360 * 29.530589, phase: PHASES[idx] };
  }
  function band(alt) { return alt >= -.833 ? "day" : alt >= -6 ? "civil" : alt >= -12 ? "nautical" : alt >= -18 ? "astronomical" : "night"; }
  function sunEvent(ms, lat, lon) {                        // the next sunrise or sunset, to two minutes, within a day
    var up = sunAt(ms, lat, lon).alt > -.833;
    for (var k = 1; k <= 720; k++) if ((sunAt(ms + k * 12e4, lat, lon).alt > -.833) !== up) return { kind: up ? "sunset" : "sunrise", inMin: k * 2 };
    return null;
  }
  // A representative city per time zone: the place when the person has not shared one (never asked here).
  var ZONES = { "Asia/Kolkata": [19, 72.8], "Asia/Calcutta": [19, 72.8], "Asia/Dubai": [25.2, 55.3], "Asia/Singapore": [1.4, 103.8], "Asia/Hong_Kong": [22.3, 114.2],
    "Asia/Shanghai": [31.2, 121.5], "Asia/Tokyo": [35.7, 139.7], "Asia/Seoul": [37.6, 127], "Asia/Bangkok": [13.8, 100.5], "Asia/Jakarta": [-6.2, 106.8],
    "Asia/Karachi": [24.9, 67], "Asia/Dhaka": [23.8, 90.4], "Asia/Kathmandu": [27.7, 85.3], "Asia/Colombo": [6.9, 79.9], "Asia/Riyadh": [24.7, 46.7],
    "Asia/Qatar": [25.3, 51.5], "Asia/Jerusalem": [31.8, 35.2], "Asia/Manila": [14.6, 121], "Asia/Taipei": [25, 121.6], "Asia/Kuala_Lumpur": [3.1, 101.7],
    "Europe/London": [51.5, -.1], "Europe/Dublin": [53.3, -6.3], "Europe/Paris": [48.9, 2.4], "Europe/Berlin": [52.5, 13.4], "Europe/Zurich": [47.4, 8.5],
    "Europe/Madrid": [40.4, -3.7], "Europe/Rome": [41.9, 12.5], "Europe/Amsterdam": [52.4, 4.9], "Europe/Stockholm": [59.3, 18.1], "Europe/Moscow": [55.8, 37.6],
    "Europe/Istanbul": [41, 29], "Africa/Johannesburg": [-26.2, 28], "Africa/Lagos": [6.5, 3.4], "Africa/Cairo": [30, 31.2], "Africa/Nairobi": [-1.3, 36.8],
    "America/New_York": [40.7, -74], "America/Chicago": [41.9, -87.6], "America/Denver": [39.7, -105], "America/Los_Angeles": [34.1, -118.2],
    "America/Toronto": [43.7, -79.4], "America/Vancouver": [49.3, -123.1], "America/Mexico_City": [19.4, -99.1], "America/Sao_Paulo": [-23.6, -46.6],
    "America/Argentina/Buenos_Aires": [-34.6, -58.4], "Australia/Sydney": [-33.9, 151.2], "Australia/Melbourne": [-37.8, 145], "Australia/Perth": [-31.9, 115.9],
    "Pacific/Auckland": [-36.8, 174.8], "UTC": [0, 0] };
  function place(zone) {
    try { var p = API.placeSource && API.placeSource();
      if (p && isFinite(+p.lat) && isFinite(+p.lon) && Math.abs(+p.lat) <= 90) return { lat: Math.round(+p.lat * 10) / 10, lon: Math.round(+p.lon * 10) / 10, src: "yours" }; } catch (e) {}
    try { var z = zone || Intl.DateTimeFormat().resolvedOptions().timeZone, c = ZONES[z]; if (c) return { lat: c[0], lon: c[1], src: "zone" }; } catch (e) {}
    return { lat: 0, lon: 0, src: "none" };
  }
  // The weather: WMO codes (Open-Meteo's weather_code) to what is drawn.
  function weatherKind(code) {
    code = +code || 0;
    return code === 45 || code === 48 ? "fog" : code >= 51 && code <= 57 ? "drizzle" : (code >= 61 && code <= 67) || (code >= 80 && code <= 82) ? "rain"
      : (code >= 71 && code <= 77) || code === 85 || code === 86 ? "snow" : code >= 95 ? "storm" : "clear";
  }
  function weather() {
    try { var w = API.weatherSource && API.weatherSource();
      if (w && isFinite(+w.cloud) && !(w.at && Date.now() - w.at > 12 * 3600e3)) {   // a reading older than 12 hours is not today's sky
        var k = weatherKind(w.code);
        return { cloud: clamp(+w.cloud, 0, 100), code: +w.code || 0, kind: k, speed: isFinite(+w.speed) ? +w.speed : 8, dir: isFinite(+w.dir) ? +w.dir : 270, real: true };
      } } catch (e) {}
    return { cloud: 0, code: 0, kind: "clear", speed: 8, dir: 270, real: false };
  }
  // The cloud field: periodic fractal noise, made once; cover (0-100 %) sets the threshold so that share of the sky is cloud.
  var CN = 256, CLD = null, CSORT = null;
  function cloudField() {
    if (CLD) return CLD;
    var f = new Float32Array(CN * CN), r = rng(77), oct = [4, 8, 16, 32, 64], amp = 1, i, x, y, o;
    for (o = 0; o < oct.length; o++, amp *= .5) {
      var n = oct[o], g = new Float32Array(n * n); for (i = 0; i < n * n; i++) g[i] = r();
      for (y = 0; y < CN; y++) { var fy = y / CN * n, y0 = Math.floor(fy), ty = fy - y0, uy = ty * ty * (3 - 2 * ty), y1 = (y0 + 1) % n;
        for (x = 0; x < CN; x++) { var fx = x / CN * n, x0 = Math.floor(fx), tx = fx - x0, ux = tx * tx * (3 - 2 * tx), x1 = (x0 + 1) % n;
          var a = g[y0 * n + x0] + (g[y0 * n + x1] - g[y0 * n + x0]) * ux, b = g[y1 * n + x0] + (g[y1 * n + x1] - g[y1 * n + x0]) * ux;
          f[y * CN + x] += amp * (a + (b - a) * uy); } }
    }
    var lo = 1e9, hi = -1e9; for (i = 0; i < f.length; i++) { lo = Math.min(lo, f[i]); hi = Math.max(hi, f[i]); }
    for (i = 0; i < f.length; i++) f[i] = (f[i] - lo) / (hi - lo);
    CSORT = Array.prototype.slice.call(f).sort(function (a, b) { return a - b; });
    return (CLD = f);
  }
  function cloudThreshold(cover) {                          // the field value above which a texel is cloud, for this cover
    cloudField(); var c = clamp(cover / 100, 0, 1);
    if (c <= 0) return 2; if (c >= 1) return -1;
    return CSORT[Math.min(CSORT.length - 1, Math.floor((1 - c) * CSORT.length))];
  }
  function cloudShare(cover) {                              // the share of the field that is cloud (opacity over a half)
    var f = cloudField(), th = cloudThreshold(cover), n = 0;
    for (var i = 0; i < f.length; i++) if (f[i] > th) n++;
    return n / f.length;
  }
  // Sunlight through the air: Kasten-Young air mass, Rayleigh optical depth at 650/550/450 nm, aerosol by turbidity.
  function airmass(h) { h = Math.max(h, -.5); return 1 / (Math.sin(h * RAD) + .50572 * Math.pow(h + 6.07995, -1.6364)); }
  function sunColour(h, T) {
    var m = airmass(h), b = .025 * (T - 1);
    return [Math.exp(-m * (.049 + b * 1.75)), Math.exp(-m * (.097 + b * 2.17)), Math.exp(-m * (.222 + b * 2.83))];
  }
  function lum(c) { return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; }
  // Preetham 1999: Perez coefficients for luminance Y and chromaticity x, y; zenith values from turbidity and sun zenith angle.
  function perez(th, g, c) { var cg = Math.cos(g); return (1 + c[0] * Math.exp(c[1] / Math.max(Math.cos(th), .02))) * (1 + c[2] * Math.exp(c[3] * g) + c[4] * cg * cg); }
  function preetham(T, ths) {
    var Y = [.1787 * T - 1.463, -.3554 * T + .4275, -.0227 * T + 5.3251, .1206 * T - 2.5771, -.067 * T + .3703];
    var x = [-.0193 * T - .2592, -.0665 * T + .0008, -.0004 * T + .2125, -.0641 * T - .8989, -.0033 * T + .0452];
    var y = [-.0167 * T - .2608, -.095 * T + .0092, -.0079 * T + .2102, -.0441 * T - 1.6537, -.0109 * T + .0529];
    var chi = (4 / 9 - T / 120) * (Math.PI - 2 * ths), t2 = ths * ths, t3 = t2 * ths, TT = T * T;
    return { Y: Y, x: x, y: y, ths: ths, Yz: (4.0453 * T - 4.971) * Math.tan(chi) - .2155 * T + 2.4192,
      xz: TT * (.00166 * t3 - .00375 * t2 + .00209 * ths) + T * (-.02903 * t3 + .06377 * t2 - .03202 * ths + .00394) + (.11693 * t3 - .21196 * t2 + .06052 * ths + .25886),
      yz: TT * (.00275 * t3 - .0061 * t2 + .00317 * ths) + T * (-.04214 * t3 + .0897 * t2 - .04153 * ths + .00516) + (.15346 * t3 - .26756 * t2 + .0667 * ths + .26688),
      n: [perez(0, ths, Y), perez(0, ths, x), perez(0, ths, y)] };
  }
  function sep(a1, z1, a2, z2) {                            // angle between two directions (alt, az in degrees), radians
    var c = Math.sin(a1 * RAD) * Math.sin(a2 * RAD) + Math.cos(a1 * RAD) * Math.cos(a2 * RAD) * Math.cos((z1 - z2) * RAD);
    return Math.acos(clamp(c, -1, 1));
  }
  // The state of the sky at one moment: what every surface draws from.
  function solve(ms) {
    var p = place(), s = sunAt(ms, p.lat, p.lon), m = moonAt(ms, p.lat, p.lon), w = weather();
    var T = w.kind === "fog" ? 6 : w.kind === "rain" || w.kind === "storm" || w.kind === "drizzle" ? 5 : 3 + w.cloud / 100;
    return { at: ms, place: p, sun: s, moon: m, w: w, T: T, band: band(s.alt), ev: sunEvent(ms, p.lat, p.lon) };
  }
  // Display brightness: the zenith's luminance compressed the way an adapted eye sees it (a power law), dimmed through twilight.
  function look(st) {
    var h = st.sun.alt, T = st.T, pre = preetham(T, (90 - Math.max(h, 0)) * RAD);
    var Yd = .065 * Math.pow(Math.max(pre.Yz, .5), .6), dim = h >= 0 ? 1 : Math.exp(h / 3.2);
    var sc = sunColour(Math.max(h, -.5), T), sl = lum(sc) || 1e-6;
    var m = st.moon, mb = m.alt > -1 ? Math.pow(m.illum, 1.5) * sstep(-1, 12, m.alt) * (1 - sstep(-14, -4, h)) : 0;
    return { h: h, saz: st.sun.az, pre: pre, Yd: Yd, dim: dim, sc: sc, scN: [sc[0] / sl, sc[1] / sl, sc[2] / sl], mb: mb, malt: m.alt, maz: m.az,
      stars: sstep(-4, -15, h) * (1 - .5 * mb), city: st.place.src === "none" ? 0 : 1 };
  }
  var OUT = [0, 0, 0];
  function skyAt(alt, az, L, out) {
    out = out || OUT;
    var h = L.h, p = L.pre, a = Math.max(alt, .4), th = (90 - a) * RAD, g = sep(a, az, Math.max(h, 0), L.saz);
    var Y = L.Yd * perez(th, g, p.Y) / p.n[0], x = p.xz * perez(th, g, p.x) / p.n[1], y = p.yz * perez(th, g, p.y) / p.n[2];
    var X = x / y * Y, Z = (1 - x - y) / y * Y;
    var r = 3.2406 * X - 1.5372 * Y - .4986 * Z, gg = -.9689 * X + 1.8758 * Y + .0415 * Z, b = .0557 * X - .204 * Y + 1.057 * Z;
    // the eye's (and a camera's) view of a clear sky is more saturated than the model's raw tristimulus: a modest chroma gain
    r = Math.min(r, gg);   // a clear sky is never purple: Rayleigh light falls off red-ward (Preetham's low-turbidity horizon drifts magenta)
    var l0 = .2126 * r + .7152 * gg + .0722 * b; r = Math.max(0, l0 + (r - l0) * 1.4); gg = Math.max(0, l0 + (gg - l0) * 1.4); b = Math.max(0, l0 + (b - l0) * 1.4);
    // the low sun colours the sky around it: forward (Mie) scattering of reddened sunlight
    var w = Math.exp(-g / .55) * sstep(24, 0, Math.max(h, 0)) * (1 - sstep(-2, -10, h)) * Math.exp(-alt / (7 + .5 * Math.max(h, 0)));
    if (w > .002) { var l = .2126 * r + .7152 * gg + .0722 * b, k = l * 1.7 * w; r = r * (1 - w) + L.scN[0] * k; gg = gg * (1 - w) + L.scN[1] * k; b = b * (1 - w) + L.scN[2] * k; }
    if (h < 0) {
      var z = sstep(0, -8, h) * sstep(0, 35, alt);           // ozone (Chappuis band) leaves the twilight zenith a deep blue
      r *= 1 - .5 * z; gg *= 1 - .25 * z;
      r *= L.dim; gg *= L.dim; b *= L.dim;
      var daz = Math.abs(adiff(az, L.saz)) * RAD, hb = 3 + 11 * Math.exp(h / 5);
      var ag = .085 * Math.exp(-Math.pow((h + 2.5) / 5, 2)) * Math.exp(-alt / hb) * (.3 + .7 * Math.exp(-daz * daz / 1.2));
      r += ag; gg += ag * .4; b += ag * .14;                  // the orange-red band along the horizon under the sun
    }
    // the Earth's shadow, a blue-grey band on the horizon opposite the sun, and the pink Belt of Venus above it
    var vis = sstep(2, -.5, h) * sstep(-8.5, -5, h);
    if (vis > .01) {
      var ga = Math.abs(adiff(az, L.saz + 180)) * RAD, wv = vis * Math.exp(-ga * ga / 1.6), sT = .6 + Math.max(0, -h) * .95;
      var sh = wv * sstep(sT + 1.2, sT - .8, alt); r *= 1 - .45 * sh; gg *= 1 - .4 * sh; b *= 1 - .3 * sh;
      var bv = wv * Math.exp(-Math.pow((alt - sT - 4) / 3.4, 2)) * L.Yd * L.dim * 1.3; r += bv; gg += bv * .52; b += bv * .62;
    }
    // night: airglow and starlight, the city's glow low down, and moonlight
    var hz = Math.exp(-alt / 9);
    r += .0034 * (1 + .6 * hz) + .0045 * hz * L.city; gg += .0072 * (1 + .6 * hz) + .0031 * hz * L.city; b += .021 * (1 + .5 * hz) + .002 * hz * L.city;
    if (L.mb > 0) {
      var gm = sep(alt, az, L.malt, L.maz), mk = L.mb * (.55 + .45 * Math.exp(-gm / .8)), au = L.mb * .05 * Math.exp(-gm / .05);
      r += .016 * mk + au; gg += .026 * mk + au * .96; b += .052 * mk + au * .88;
    }
    out[0] = r; out[1] = gg; out[2] = b; return out;
  }
  // Linear light to sRGB bytes, through a square-root table (fine steps in the darks, where banding shows).
  var ENC = new Uint8ClampedArray(4096);
  for (var ei = 0; ei < 4096; ei++) { var ev = Math.pow(ei / 4095, 2); ENC[ei] = Math.round(255 * (ev <= .0031308 ? 12.92 * ev : 1.055 * Math.pow(ev, 1 / 2.4) - .055)); }
  function enc(v) { return v <= 0 ? 0 : v >= 1 ? 255 : ENC[(Math.sqrt(v) * 4095) | 0]; }
  // The scrim that adapts to the sky: a pixel's luminance is held under a ceiling with a soft knee, so its hue stays.
  // White text (#fff, L = 1) on L <= 0.15 is 5.25:1 or better: WCAG AA for every size.
  var CAP = .15;
  function capped(c, cap) {
    var l = .2126 * c[0] + .7152 * c[1] + .0722 * c[2], knee = cap * .62;
    if (l > knee) { var l2 = knee + (cap - knee) * (1 - Math.exp(-(l - knee) / (cap - knee))), k = l2 / l; c[0] *= k; c[1] *= k; c[2] *= k; }
    return c;
  }
  function describe(st) {
    var t = API.t || function (s) { return s; }, s = st.sun, w = st.w, m = st.moon, a = Math.round(Math.abs(s.alt)), parts = [];
    parts.push(s.alt >= -.833 ? t("sun") + " " + a + "° " + t("above the horizon") : t("sun") + " " + a + "° " + t("below the horizon")
      + (st.band === "night" ? "" : " (" + t(st.band + " twilight") + ")"));
    parts.push(w.real ? (w.kind === "fog" ? t("fog") : Math.round(w.cloud) + "% " + t("cloud") + (w.kind === "clear" ? "" : ", " + t(w.kind))) : t("no weather reading, drawn clear"));
    parts.push(t(m.phase + " moon") + (m.alt > 0 ? "" : " " + t("(not up)")));
    var line = t("Your sky now") + ": " + parts.join(", ");
    if (st.ev && st.ev.inMin <= 180) line += " · " + t(st.ev.kind) + " " + t("in") + " " + (st.ev.inMin < 60 ? st.ev.inMin + " min" : Math.floor(st.ev.inMin / 60) + " h " + (st.ev.inMin % 60) + " min");
    return line;
  }
  function daypart(ms) {
    var st = solve(ms || Date.now()), h = st.sun.alt, am = st.sun.ha < 0;
    return h < -12 ? "night" : h < 6 ? (am ? "dawn" : "dusk") : "day";
  }

  // ── The renderer: one engine, one 10-frames-a-second loop, every surface a canvas of its own ──
  var SURF = [], ST0 = null, ST1 = null, LOOP = 0, LAST = 0, FT = [], SCAN = 0, MO = null;
  function isStill() {
    var calm = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
    return calm || !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
  }
  function stateNow(ms) {                                   // solved at whole minutes, interpolated between
    var m0 = Math.floor(ms / 6e4) * 6e4;
    if (!ST0 || ST0.at !== m0) { ST0 = ST1 && ST1.at === m0 ? ST1 : solve(m0); ST1 = solve(m0 + 6e4); }
    var f = (ms - m0) / 6e4, A = ST0, B = ST1, lerp = function (a, b) { return a + (b - a) * f; };
    var s = { alt: lerp(A.sun.alt, B.sun.alt), az: n360(A.sun.az + adiff(B.sun.az, A.sun.az) * f), ha: A.sun.ha };
    var mo = { alt: lerp(A.moon.alt, B.moon.alt), az: n360(A.moon.az + adiff(B.moon.az, A.moon.az) * f), illum: A.moon.illum, phase: A.moon.phase, waxing: A.moon.waxing };
    return { at: ms, place: A.place, sun: s, moon: mo, w: A.w, T: A.T, band: band(s.alt), ev: A.ev };
  }
  function liveMount(el, cfg) {
    if (el.__sxLive) return el.__sxLive;
    var doc = el.ownerDocument, cv = doc.createElement("canvas"), ctx = cv.getContext && cv.getContext("2d");
    if (!ctx) return { stop: function () {} };
    cv.setAttribute("aria-hidden", "true"); cv.className = "sx-live-cv";
    cv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:-1;border-radius:inherit";
    el.insertBefore(cv, el.firstChild); el.classList.add("sx-live");
    var face = cfg.face || el.getAttribute("data-sx-sky") || "sun";
    var S = { el: el, cv: cv, ctx: ctx, face: face, art: face === "art", lock: !!cfg.lock, cap: clamp(parseFloat(el.getAttribute("data-sx-cap")) || CAP, .05, CAP), nightOpts: cfg.night || null, night: null,
      W: 0, H: 0, D: 1, vis: true, az0: null, a0: 0, geoAz: null, geoA0: 0, skyAt: 0, lo: null, cl: null, rain: [], seed: Math.random() * 1000 };
    S.stop = function () { var i = SURF.indexOf(S); if (i >= 0) SURF.splice(i, 1); if (S.night) S.night.stop(); if (S.io) S.io.disconnect(); if (S.ro) S.ro.disconnect();
      if (cv.parentNode) cv.parentNode.removeChild(cv); el.classList.remove("sx-live"); el.__sxLive = null; };
    el.__sxLive = S; SURF.push(S);
    try { if (window.IntersectionObserver) { S.io = new IntersectionObserver(function (es) { S.vis = es[es.length - 1].isIntersecting; if (S.vis) kick(); }); S.io.observe(el); } } catch (e) {}
    try { if (window.ResizeObserver) { S.ro = new ResizeObserver(function () { S.W = -1; if (isStill()) paint(S, Date.now(), true); }); S.ro.observe(el); } } catch (e) {}
    layout(S); paint(S, Date.now(), true); kick();
    return S;
  }
  function layout(S) {
    var b = S.el.getBoundingClientRect(), W = Math.max(1, Math.round(b.width)), H = Math.max(1, Math.round(b.height)), D = Math.min(2, window.devicePixelRatio || 1);
    if (W === S.W && H === S.H && D === S.D) return;
    S.W = W; S.H = H; S.D = D; S.cv.width = Math.round(W * D); S.cv.height = Math.round(H * D);
    var cell = Math.max(4, Math.sqrt(W * H / 22000)); S.gw = Math.max(2, Math.ceil(W / cell)); S.gh = Math.max(2, Math.ceil(H / cell));
    S.hfov = S.lock ? 100 : 110; S.vfov = clamp(S.hfov * H / W, 12, 84);
    var doc = S.el.ownerDocument;
    S.lo = doc.createElement("canvas"); S.lo.width = S.gw; S.lo.height = S.gh; S.lx = S.lo.getContext("2d"); S.limg = S.lx.createImageData(S.gw, S.gh);
    S.cl = doc.createElement("canvas"); S.cl.width = S.gw; S.cl.height = S.gh; S.cx = S.cl.getContext("2d"); S.cimg = S.cx.createImageData(S.gw, S.gh);
    var n = S.gw * S.gh; S.alt = new Float32Array(n); S.az = new Float32Array(n); S.u = new Float32Array(n); S.v = new Float32Array(n); S.sky = new Float32Array(n * 3);
    S.geoAz = null; S.skyAt = 0;
    if (S.nightOpts || !S.art) {
      if (S.night) S.night.stop();
      var o = {}, k; for (k in (S.nightOpts || {})) o[k] = S.nightOpts[k];
      o.offscreen = true; o.live = false; if (!S.nightOpts) { o.galaxy = false; o.density = .8; }
      if (o.aurora) o.aurora = Math.abs(place().lat) >= 55;     // the aurora only where it really shows
      S.night = mount(S.el, o);
    }
  }
  function facing(S, st) {                                  // the direction this surface looks: the sun, away from it, or the moon
    var h = st.sun.alt, m = st.moon;
    // by day a high sun is above the view, so the window looks across it, where the sky is bluest (90 deg from the sun);
    // as the sun nears the horizon the window turns to face it (and the hero, away from it: the Earth's shadow, the Belt of Venus)
    if (h > -10) return [n360(st.sun.az + (S.face === "anti" ? 180 : 90 * sstep(8, 20, h))), 0];
    if (m.alt > 2) return [m.az, Math.max(0, m.alt + (S.lock ? .14 : .3) * S.vfov - S.vfov)];   // the lock's card fills the middle   // at night the view lifts to keep the moon in it
    return [st.place.lat >= 0 ? 180 : 0, 0];
  }
  function geometry(S) {                                    // each cell's direction, and where its line of sight meets the cloud layer
    var i = 0, gw = S.gw, gh = S.gh, a0 = S.a0, a1 = S.a0 + S.vfov;
    for (var y = 0; y < gh; y++) for (var x = 0; x < gw; x++, i++) {
      var az = S.az0 + ((x + .5) / gw - .5) * S.hfov, alt = a1 - (y + .5) / gh * (a1 - a0);
      if (alt > 90) { alt = 180 - alt; az += 180; }            // a view tipped past the zenith looks down the other side
      var r = 1 / Math.tan(Math.max(alt, 1.2) * RAD);
      r = Math.min(r, 30); S.alt[i] = alt; S.az[i] = az; S.u[i] = r * Math.sin(az * RAD) * 48; S.v[i] = -r * Math.cos(az * RAD) * 48;
    }
    S.geoAz = S.az0; S.geoA0 = S.a0;
  }
  function skyGrid(S, L) {
    var n = S.gw * S.gh, c = [0, 0, 0], cap = S.art ? 1 : S.cap, d = S.limg.data;
    for (var i = 0; i < n; i++) {
      skyAt(S.alt[i], S.az[i], L, c); S.sky[i * 3] = c[0]; S.sky[i * 3 + 1] = c[1]; S.sky[i * 3 + 2] = c[2];
      capped(c, cap);
      var dz = ((i * 2654435761) >>> 0) / 4294967296 - .5;      // a whisper of dither against banding in the dark blues
      d[i * 4] = enc(c[0]) + dz; d[i * 4 + 1] = enc(c[1]) + dz; d[i * 4 + 2] = enc(c[2]) + dz; d[i * 4 + 3] = 255;
    }
    S.lx.putImageData(S.limg, 0, 0);
  }
  // Clouds: the field seen in perspective, lit from the sun, drifting with the wind; fog and haze over everything.
  var SHADE = null, SHADEKEY = "";
  function shadeFor(saz) {                                  // light on the field: brighter where the sun side is thinner (a silver edge)
    var key = Math.round(saz / 4); if (SHADE && SHADEKEY === key) return SHADE;
    var f = cloudField(), out = new Float32Array(CN * CN), dx = Math.round(Math.sin(saz * RAD) * 3), dy = Math.round(-Math.cos(saz * RAD) * 3);
    for (var y = 0; y < CN; y++) for (var x = 0; x < CN; x++) {
      var i = y * CN + x, j = ((y + dy + CN) % CN) * CN + ((x + dx + CN) % CN);
      out[i] = clamp(1 - 2.4 * (f[j] - f[i]), .3, 1.35);
    }
    SHADEKEY = key; return (SHADE = out);
  }
  function cloudLayer(S, st, L, t) {
    var w = st.w, d = S.cimg.data, n = S.gw * S.gh, f = cloudField(), cap = S.art ? 1 : S.cap;
    var cover = w.kind === "rain" || w.kind === "storm" ? Math.max(w.cloud, 85) : w.kind === "drizzle" || w.kind === "snow" ? Math.max(w.cloud, 70) : w.cloud;
    var fog = w.kind === "fog" ? .72 : w.kind === "rain" || w.kind === "storm" ? .3 : w.kind === "drizzle" || w.kind === "snow" ? .2 : .04 + (st.T - 3) * .03;
    if (cover <= 0 && fog < .05) return false;
    var th = cloudThreshold(cover), sh = shadeFor(L.saz), wet = w.kind === "rain" || w.kind === "storm" ? .42 : w.kind === "drizzle" || w.kind === "snow" ? .62 : 1;
    // sunlight on the clouds: they stand higher than we do, so they keep the sun a little after it has set (pink undersides at dusk)
    var hc = L.h + 2.2, sI = sstep(-3, 5, hc), sc = sunColour(Math.max(hc, -.5), st.T), sl = lum(sc) || 1e-6, Ys = L.Yd * (hc >= 0 ? 1 : Math.exp(hc / 3)) * 2.3 * sI * wet;
    var lr = sc[0] / sl * Ys, lg = sc[1] / sl * Ys, lb = sc[2] / sl * Ys;
    var zen = skyAt(80, L.saz, L, [0, 0, 0]), am = .9 * wet;
    var nr = .0055 * L.city + .016 * L.mb, ng = .0045 * L.city + .017 * L.mb, nb = .0036 * L.city + .02 * L.mb;   // night: the city's glow underneath, moonlight
    var fogL = L.Yd * L.dim * 1.5 + .006 * L.city + .02 * L.mb, fr = fogL * .93, fgc = fogL * .96, fb = fogL;
    // drift: the field moves where the wind blows (from dir toward dir + 180), about three times the ground speed aloft
    var sp = w.speed * 3 / 2 / 3600 * 48, td = t / 1000, ox = -Math.sin((w.dir + 180) * RAD) * sp * td, oy = Math.cos((w.dir + 180) * RAD) * sp * td;
    var c = [0, 0, 0];
    for (var i = 0; i < n; i++) {
      var a = 0, cr = 0, cg = 0, cb = 0;
      if (cover > 0) {
        var u = S.u[i] - ox, v = S.v[i] - oy, x0 = Math.floor(u), y0 = Math.floor(v), tx = u - x0, ty = v - y0;
        x0 = ((x0 % CN) + CN) % CN; y0 = ((y0 % CN) + CN) % CN; var x1 = (x0 + 1) % CN, y1 = (y0 + 1) % CN;
        var i00 = y0 * CN + x0, i10 = y0 * CN + x1, i01 = y1 * CN + x0, i11 = y1 * CN + x1;
        var D = (f[i00] * (1 - tx) + f[i10] * tx) * (1 - ty) + (f[i01] * (1 - tx) + f[i11] * tx) * ty;
        var Sh = (sh[i00] * (1 - tx) + sh[i10] * tx) * (1 - ty) + (sh[i01] * (1 - tx) + sh[i11] * tx) * ty;
        var alt = S.alt[i], far = sstep(14, 1, alt);
        a = sstep(th - .03, th + .12, D); a = a + (cover / 100 * .9 - a) * far * .8;    // far away the layer blurs into a band
        var thick = 1 - .38 * sstep(th + .08, th + .45, D);                            // thick cores are darker underneath
        var j = i * 3;
        cr = (lr * Sh + zen[0] * am) * thick + nr; cg = (lg * Sh + zen[1] * am) * thick + ng; cb = (lb * Sh + zen[2] * am) * thick + nb;
        if (wet < 1) { var gy = (cr + cg + cb) / 3; cr = cr + (gy - cr) * .6; cg = cg + (gy - cg) * .6; cb = cb + (gy - cb) * .6; }
        cr += (S.sky[j] - cr) * far * .5; cg += (S.sky[j + 1] - cg) * far * .5; cb += (S.sky[j + 2] - cb) * far * .5;   // aerial perspective
      }
      var af = fog * (.55 + .45 * sstep(40, 0, S.alt[i])), A = af + a * (1 - af);
      if (A < .003) { d[i * 4 + 3] = 0; continue; }
      c[0] = (fr * af + cr * a * (1 - af)) / A; c[1] = (fgc * af + cg * a * (1 - af)) / A; c[2] = (fb * af + cb * a * (1 - af)) / A;
      capped(c, cap);
      d[i * 4] = enc(c[0]); d[i * 4 + 1] = enc(c[1]); d[i * 4 + 2] = enc(c[2]); d[i * 4 + 3] = Math.round(A * 255);
    }
    S.cx.putImageData(S.cimg, 0, 0);
    return true;
  }
  function toScreen(S, alt, az) { return [S.W * (.5 + adiff(az, S.az0) / S.hfov), S.H * (S.a0 + S.vfov - alt) / S.vfov]; }
  function drawSun(S, st, L) {
    var h = st.sun.alt; if (h < -1.2) return;
    var p = toScreen(S, h, st.sun.az), x = p[0], y = p[1], c = S.ctx, sc = L.scN, mx = Math.max(sc[0], sc[1], sc[2]);
    if (x < -80 || x > S.W + 80 || y < -80 || y > S.H + 80) return;
    var col = [Math.round(255 * sc[0] / mx), Math.round(255 * sc[1] / mx), Math.round(255 * sc[2] / mx)], soft = S.art ? 1 : .55;
    var R = Math.max(3.2, .267 / S.hfov * S.W), gl = c.createRadialGradient(x, y, 0, x, y, R * 14);
    gl.addColorStop(0, "rgba(" + col + "," + (.55 * soft) + ")"); gl.addColorStop(.25, "rgba(" + col + "," + (.16 * soft) + ")"); gl.addColorStop(1, "rgba(" + col + ",0)");
    c.fillStyle = gl; c.beginPath(); c.arc(x, y, R * 14, 0, TAU); c.fill();
    c.fillStyle = "rgba(" + Math.min(255, col[0] + 30) + "," + Math.min(255, col[1] + 40) + "," + Math.min(255, col[2] + 60) + "," + (S.art ? 1 : .9) + ")";
    c.beginPath(); c.arc(x, y, R, 0, TAU); c.fill();
  }
  function drawMoon(S, st, L) {
    var m = st.moon; if (m.alt < -1) return;
    var p = toScreen(S, m.alt, m.az), x = p[0], y = p[1], c = S.ctx;
    var R = Math.max(S.lock ? 9 : 6.5, .26 / S.hfov * S.W);
    if (x < -R || x > S.W + R || y < -R || y > S.H + R) return;
    // the bright limb faces the sun: the bearing from the moon to the sun on the sky, turned into screen angle
    var s = st.sun, dz = (s.az - m.az) * RAD, th = Math.atan2(Math.sin(dz) * Math.cos(s.alt * RAD),
      Math.cos(m.alt * RAD) * Math.sin(s.alt * RAD) - Math.sin(m.alt * RAD) * Math.cos(s.alt * RAD) * Math.cos(dz));
    var chi = Math.atan2(-Math.cos(th), Math.sin(th)), k = m.illum, day = sstep(-6, 4, s.alt);
    var tc = sunColour(Math.max(m.alt, -.5), 3), tm = Math.max(tc[0], tc[1], tc[2]);   // the moon low down is reddened too
    var col = [Math.round(255 * (.75 + .25 * tc[0] / tm)), Math.round(250 * (.6 + .4 * tc[1] / tm)), Math.round(235 * (.45 + .55 * tc[2] / tm))];
    c.save();
    var halo = c.createRadialGradient(x, y, R, x, y, R * 5); halo.addColorStop(0, "rgba(" + col + "," + (.16 * k * (1 - day)) + ")"); halo.addColorStop(1, "rgba(" + col + ",0)");
    c.fillStyle = halo; c.beginPath(); c.arc(x, y, R * 5, 0, TAU); c.fill();
    c.translate(x, y); c.rotate(chi);
    c.fillStyle = "rgba(120,132,160," + (.16 * (1 - day)) + ")"; c.beginPath(); c.arc(0, 0, R, 0, TAU); c.fill();   // earthshine on the dark part
    c.beginPath(); c.arc(0, 0, R, -Math.PI / 2, Math.PI / 2, false);
    c.ellipse(0, 0, Math.max(.01, R * Math.abs(2 * k - 1)), R, 0, Math.PI / 2, -Math.PI / 2, k < .5);
    c.closePath();
    var a = day ? .55 + .3 * (1 - day) : .97, g = c.createRadialGradient(-R * .3, -R * .3, R * .1, 0, 0, R);
    g.addColorStop(0, "rgba(" + col + "," + a + ")"); g.addColorStop(1, "rgba(" + Math.round(col[0] * .86) + "," + Math.round(col[1] * .86) + "," + Math.round(col[2] * .88) + "," + a + ")");
    c.fillStyle = g; c.fill(); c.clip();
    c.rotate(-chi);                                            // the maria keep their place on the face, whatever the phase
    c.fillStyle = "rgba(90,96,110," + (.22 * a) + ")";
    [[-.28, -.32, .3], [.18, -.2, .22], [.05, .2, .26], [-.35, .15, .16]].forEach(function (q) { c.beginPath(); c.arc(q[0] * R, q[1] * R, q[2] * R, 0, TAU); c.fill(); });
    c.restore();
  }
  function drawPrecip(S, st, t) {
    var k = st.w.kind; if (k !== "rain" && k !== "drizzle" && k !== "storm" && k !== "snow") return;
    var c = S.ctx, W = S.W, H = S.H, n = Math.round(W * H / (k === "storm" ? 650 : k === "rain" ? 900 : k === "snow" ? 1400 : 2400));
    var slant = clamp(Math.sin(adiff(st.w.dir + 180, S.az0) * RAD) * st.w.speed / 35, -.6, .6), r = rng((S.seed | 0) + (k === "snow" ? 0 : Math.floor(t / 100)));
    c.save();
    if (k === "snow") {
      c.fillStyle = "rgba(240,244,250," + (S.art ? .75 : .5) + ")";
      for (var i = 0; i < n; i++) { var x0 = r() * W, sp = 12 + r() * 16, y = (r() * H + t / 1000 * sp) % H, x = x0 + Math.sin(t / 1400 + i) * 6 + slant * y * .3;
        c.beginPath(); c.arc(((x % W) + W) % W, y, .8 + r() * 1.3, 0, TAU); c.fill(); }
    } else {
      c.strokeStyle = "rgba(220,230,245," + (S.art ? .28 : .11) + ")"; c.lineWidth = k === "drizzle" ? .6 : .9; c.beginPath();
      for (var j = 0; j < n; j++) { var px = r() * W, py = r() * H, len = (k === "drizzle" ? 6 : 12) + r() * 10; c.moveTo(px, py); c.lineTo(px + slant * len, py + len); }
      c.stroke();
    }
    c.restore();
  }
  function paint(S, ms, force) {
    if (!S.el.isConnected) { S.stop(); return; }
    if (S.W < 0 || force) layout(S);
    var still = isStill(), st = stateNow(ms), L = look(st), c = S.ctx, fa = facing(S, st);
    if (S.az0 === null || still || force) { S.az0 = fa[0]; S.a0 = fa[1]; }
    else { S.az0 = n360(S.az0 + adiff(fa[0], S.az0) * .02); S.a0 += (fa[1] - S.a0) * .02; }   // turn slowly toward a new subject
    if (S.geoAz === null || Math.abs(adiff(S.az0, S.geoAz)) > .25 || Math.abs(S.a0 - S.geoA0) > .25) { geometry(S); S.skyAt = 0; }
    if (force || !S.skyAt || ms - S.skyAt > 5000 || ms < S.skyAt) { skyGrid(S, L); S.skyAt = ms; }
    c.setTransform(1, 0, 0, 1, 0, 0); c.imageSmoothingEnabled = true; if ("imageSmoothingQuality" in c) c.imageSmoothingQuality = "high";
    c.drawImage(S.lo, 0, 0, S.cv.width, S.cv.height);
    if (S.night && L.stars > .01) { c.globalAlpha = L.stars; S.night.paint(still ? 0 : performance.now()); c.drawImage(S.night.cv, 0, 0, S.cv.width, S.cv.height); c.globalAlpha = 1; }
    c.setTransform(S.D, 0, 0, S.D, 0, 0);
    drawMoon(S, st, L); drawSun(S, st, L);
    c.setTransform(1, 0, 0, 1, 0, 0);
    if (cloudLayer(S, st, L, still ? 0 : ms)) c.drawImage(S.cl, 0, 0, S.cv.width, S.cv.height);
    c.setTransform(S.D, 0, 0, S.D, 0, 0);
    drawPrecip(S, st, still ? 0 : ms);
    S.state = st;
  }
  function kick() { if (LOOP || isStill() || !SURF.length) return; LOOP = setTimeout(function () { LOOP = 0; requestAnimationFrame(tick); }, Math.max(0, 100 - (Date.now() - LAST))); }
  function tick() {
    if (!SURF.length) return;
    var doc = document; if (doc.hidden) return;              // visibilitychange kicks it again
    var t0 = performance.now(), ms = Date.now(), any = false; LAST = ms;
    SURF.slice().forEach(function (S) { if (S.vis && S.el.isConnected && S.cv.offsetParent !== null) { paint(S, ms); any = true; } else if (!S.el.isConnected) S.stop(); });
    if (any) { FT.push(performance.now() - t0); if (FT.length > 60) FT.shift(); }
    kick();
  }
  function scan() {
    SCAN = 0;
    SURF.slice().forEach(function (S) { if (!S.el.isConnected) S.stop(); });
    var els = document.querySelectorAll("[data-sx-sky]");
    for (var i = 0; i < els.length; i++) if (!els[i].__sxLive) liveMount(els[i], {});
  }
  function boot() {
    if (/jsdom/i.test(navigator.userAgent || "") || !document.body) return;   // a test DOM has no canvas: the surfaces keep their colour
    scan();
    try { MO = new MutationObserver(function () { if (!SCAN) SCAN = requestAnimationFrame(scan); }); MO.observe(document.body, { childList: true, subtree: true }); } catch (e) {}
    document.addEventListener("visibilitychange", function () { if (!document.hidden) { SURF.forEach(function (S) { S.skyAt = 0; }); if (isStill()) SURF.forEach(function (S) { paint(S, Date.now()); }); kick(); } });
    window.addEventListener("resize", function () { SURF.forEach(function (S) { S.W = -1; }); if (isStill()) SURF.forEach(function (S) { paint(S, Date.now()); }); });
    // reduced motion: the still frame stays true to the sky, redrawn once a minute (an automated browser keeps its one frame)
    if (isStill() && !navigator.webdriver) setInterval(function () { SURF.forEach(function (S) { if (S.vis) paint(S, Date.now(), true); }); }, 6e4);
    // one tap on the sky (not on a control) says what it is doing
    document.addEventListener("click", function (e) {
      var t = e.target, s = t && t.closest && t.closest("[data-sx-sky]"); if (!s || !s.__sxLive) return;
      var it = t.closest("a,button,input,select,textarea,label,summary,details,[onclick],[role=button],[tabindex]");
      if (it && it !== s && s.contains(it)) return;
      API.tell(s);
    });
  }
  API.tell = function (s) {
    var S = s && s.__sxLive; if (!S) return "";
    var line = describe(solve(Date.now())), el = s.querySelector(":scope > .sx-sky-line");
    if (!el) { el = s.ownerDocument.createElement("div"); el.className = "sx-sky-line"; el.setAttribute("role", "status"); s.appendChild(el); }
    el.textContent = line; el.classList.add("on"); clearTimeout(el.__t); el.__t = setTimeout(function () { el.classList.remove("on"); }, 6000);
    return line;
  };
  API.stats = function () {
    var a = FT.length ? FT.reduce(function (x, y) { return x + y; }, 0) / FT.length : 0, st = ST0 || solve(Date.now());
    return { surfaces: SURF.length, frameMs: Math.round(a * 100) / 100, frames: FT.length, sunAlt: Math.round(st.sun.alt * 10) / 10, band: st.band, cloud: st.w.cloud,
      kind: st.w.kind, moon: st.moon.phase, place: st.place.src };
  };
  API.sun = sunAt; API.moon = moonAt; API.band = band; API.place = place; API.zones = ZONES; API.solve = solve; API.describe = describe;
  API.daypart = daypart; API.weatherKind = weatherKind; API.cloudThreshold = cloudThreshold; API.cloudShare = cloudShare;
  API.skyColour = function (alt, az, ms) { var c = skyAt(alt, az, look(solve(ms || Date.now())), [0, 0, 0]); return [enc(c[0]), enc(c[1]), enc(c[2])]; };
  API.capped = function (rgb, cap) { return capped(rgb.slice(), cap || CAP); }; API.CAP = CAP;
  API.sunColour = sunColour; API.preetham = preetham; API.mountLive = liveMount;
  if (typeof document !== "undefined") { if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else setTimeout(boot, 0); }

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
  API.mount = mount; API.seal = seal;
  window.SXSky = API;
})();
