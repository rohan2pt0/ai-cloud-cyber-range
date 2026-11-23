/* SecuRAX shared water (reuse-first; natures-design, signature-perfect; owner 2026-11-23: "water in a glass must look and move
   like real water in real glass"). One engine behind SXWorld.vessel (the emergency fund: months of cover in the tank).
   - Physics: a 1D height field of 48 columns, a damped wave equation with a spring toward the tilted plane (gravity in the
     phone's frame). The mean level is held exactly, so the volume is conserved. A tilt of the phone, a tap or a drag on the
     glass, and a tiny ambient breath move it; it then settles on its own.
   - Look: depth tint, refraction of what is behind, a bright meniscus that curls up the wall, a surface seen from just
     above, glints from the wave facets and two moving highlights, caustic light on the floor, a few slow bubbles, thick glass
     with highlights, the rim and the shadow on the table.
   - Cost: ONE canvas per vessel, ONE shared animation frame, running only while a vessel is on screen and the page is
     visible; a calm surface is redrawn at 20 frames a second. Reduced motion, an automated browser and jsdom get one
     still frame (or, with no 2D canvas, the SVG that SXWorld drew, which always stays as the fallback). */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXWater) return;
  var N = 48, DT = 1 / 60, C = 0.3, K = 0.008, DAMP = 0.985, MAXLEAN = 8;
  var VW = 150, VH = 170, IX0 = 35, IX1 = 115, FLOOR = 152, AIMY = 32, DEPTH1 = FLOOR - AIMY;
  var PALETTE = { good: ["#5fd3c0", "#127a75", "#0a4a52"], watch: ["#9fd6c6", "#3e8f7a", "#5a5a2a"], low: ["#c9a98a", "#8a5a3c", "#5a3020"] };

  /* ---- physics (pure: no DOM, no animation frame; the tests drive it directly) ---- */
  function depth(f) { return Math.max(4, DEPTH1 * Math.max(0.04, Math.min(1, f || 0))); }
  function make(d) {
    var h = [], v = [], i; for (i = 0; i < N; i++) { h.push(d); v.push(0); }
    return { n: N, h: h, v: v, depth: d, acc: 0, tilt: 0 };
  }
  function mean(a) { var s = 0, i; for (i = 0; i < a.length; i++) s += a[i]; return s / a.length; }
  function tick(s, tilt) {
    var n = s.n, h = s.h, v = s.v, d = s.depth, amp = Math.min(MAXLEAN, d * 0.45), i, l, r, tg, m;
    for (i = 0; i < n; i++) {
      l = h[i > 0 ? i - 1 : 0]; r = h[i < n - 1 ? i + 1 : n - 1];
      tg = Math.max(-amp, Math.min(amp, tilt * 0.22 * ((i / (n - 1) - 0.5) * 80)));
      v[i] = (v[i] + C * (l + r - 2 * h[i]) + K * (d + tg - h[i])) * DAMP;
    }
    for (i = 0; i < n; i++) h[i] += v[i];
    m = mean(h) - d; for (i = 0; i < n; i++) h[i] -= m;     // the volume of water never changes
    m = mean(v); for (i = 0; i < n; i++) v[i] -= m;
  }
  // Advance by dt seconds in fixed 1/60 s steps (at most 6 at once, so a stalled page never explodes).
  function step(s, dt, tiltX) {
    var k = 0; s.acc += Math.max(0, dt || 0);
    while (s.acc >= DT && k < 6) { tick(s, tiltX || 0); s.acc -= DT; k++; }
    if (s.acc > DT * 6) s.acc = 0;
    return s;
  }
  function splash(s, col, amount) {
    var a = Math.min(amount, s.depth * 0.12), k, j, m;
    for (k = -4; k <= 4; k++) { j = Math.round(col) + k; if (j >= 0 && j < s.n) s.v[j] -= a * Math.exp(-(k * k) / 4); }
    m = mean(s.v); for (j = 0; j < s.n; j++) s.v[j] -= m;
  }
  function energy(s) {
    var e = 0, i, g; for (i = 0; i < s.n; i++) { g = i < s.n - 1 ? s.h[i + 1] - s.h[i] : 0; e += s.v[i] * s.v[i] + K * (s.h[i] - s.depth) * (s.h[i] - s.depth) + C * g * g; }
    return e;
  }

  /* ---- drawing ---- */
  function still() {
    try { if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return true; } catch (e) {}
    return !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
  }
  var vessels = [], raf = 0, last = 0, io = null, vis = null;

  function glassPath(c) {
    c.moveTo(30, 22); c.quadraticCurveTo(30, 16, 36, 16); c.lineTo(114, 16); c.quadraticCurveTo(120, 16, 120, 22);
    c.lineTo(120, 150); c.quadraticCurveTo(120, 160, 110, 160); c.lineTo(40, 160); c.quadraticCurveTo(30, 160, 30, 150); c.closePath();
  }
  function innerPath(c) {
    c.moveTo(IX0, 17); c.lineTo(IX0, FLOOR - 6); c.quadraticCurveTo(IX0, FLOOR, IX0 + 6, FLOOR); c.lineTo(IX1 - 6, FLOOR);
    c.quadraticCurveTo(IX1, FLOOR, IX1, FLOOR - 6); c.lineTo(IX1, 17); c.closePath();
  }
  function rgba(rgb, a) { return "rgba(" + rgb + "," + a + ")"; }
  function hex2rgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mix(a, b, t) { return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), Math.round(a[2] + (b[2] - a[2]) * t)]; }

  // What is behind the glass: pinstripes and a table edge. Drawn straight in the air, and shifted and stretched through the water.
  function makeBackdrop(S, dark, lamp) {
    var cv = document.createElement("canvas"), c; cv.width = Math.ceil(VW * S); cv.height = Math.ceil(VH * S); c = cv.getContext("2d"); if (!c) return null;
    c.setTransform(S, 0, 0, S, 0, 0);
    var ink = dark ? "255,255,255" : "20,40,60", x;
    for (x = 30; x < 125; x += 7) { c.fillStyle = rgba(ink, x % 14 === 2 ? 0.2 : 0.12); c.fillRect(x, 0, 2.6, 125); }
    c.fillStyle = rgba(ink, 0.22); c.fillRect(0, 125, VW, 1.4);
    c.fillStyle = rgba(ink, 0.06); c.fillRect(0, 126.4, VW, VH);
    if (lamp) { c.fillStyle = rgba(dark ? "255,220,160" : "255,200,120", dark ? 0.2 : 0.3); c.beginPath(); c.arc(100, 70, 9, 0, 7); c.fill(); }   // a warm lamp behind, seen only through the water
    return cv;
  }

  function surfaceY(v, i, t) {   // the drawn surface: the height field plus the meniscus curling up each wall
    var s = v.s, x = IX0 + (IX1 - IX0) * i / (s.n - 1), cur = 2.4 * Math.exp(-(x - IX0) / 3.4) + 2.4 * Math.exp(-(IX1 - x) / 3.4);
    return { x: x, y: FLOOR - s.h[i] - Math.min(cur, s.depth * 0.3) };
  }

  function render(v, t) {
    var c = v.ctx, S = v.S, s = v.s, d = s.depth, dark = v.dark, W = PALETTE[v.state] || PALETTE.low, i, k, p, x, y, g, pts = [];
    c.setTransform(S, 0, 0, S, 0, 0); c.clearRect(0, 0, VW, VH); c.lineJoin = "round"; c.lineCap = "round";
    var lx = (window.SXTouch && SXTouch.light ? SXTouch.light.x : 0) || 0;
    var w0 = hex2rgb(W[0]), w1 = hex2rgb(W[1]), w2 = hex2rgb(W[2]);
    for (i = 0; i < s.n; i++) pts.push(surfaceY(v, i, t));
    var top = FLOOR - d;

    // the table: a soft shadow, and the light the water throws on it
    c.fillStyle = "rgba(0,0,0,.10)"; c.beginPath(); c.ellipse(75, 164, 58, 7, 0, 0, 7); c.fill();
    c.fillStyle = "rgba(0,0,0,.20)"; c.beginPath(); c.ellipse(75, 162.5, 46, 4.2, 0, 0, 7); c.fill();
    g = c.createRadialGradient(92 - lx * 14, 164, 1, 92 - lx * 14, 164, 24); g.addColorStop(0, rgba(w0.join(","), 0.34)); g.addColorStop(1, rgba(w0.join(","), 0));
    c.fillStyle = g; c.beginPath(); c.ellipse(92 - lx * 14, 164, 24, 4.4, 0, 0, 7); c.fill();

    // inside the glass
    c.save(); c.beginPath(); innerPath(c); c.clip();
    c.fillStyle = dark ? "rgba(190,215,230,.07)" : "rgba(200,225,235,.12)"; c.fillRect(0, 0, VW, VH);
    if (v.air) { c.globalAlpha = 0.22; c.drawImage(v.air, 0, 0, v.air.width, v.air.height, 0, 0, VW, VH); c.globalAlpha = 1; }

    // the water body
    c.save(); c.beginPath(); c.moveTo(IX0 - 1, pts[0].y);
    for (i = 0; i < s.n; i++) c.lineTo(pts[i].x, pts[i].y);
    c.lineTo(IX1 + 1, pts[s.n - 1].y); c.lineTo(IX1 + 1, VH); c.lineTo(IX0 - 1, VH); c.closePath(); c.clip();
    g = c.createLinearGradient(0, top - 4, 0, FLOOR);
    g.addColorStop(0, rgba(w0.join(","), 0.94)); g.addColorStop(0.4, rgba(w1.join(","), 0.97)); g.addColorStop(1, rgba(w2.join(","), 1));
    c.fillStyle = g; c.fillRect(IX0 - 2, top - 14, IX1 - IX0 + 4, d + 30);
    // refraction: the backdrop, magnified and rippled by the surface, seen through the water
    if (v.back) {
      c.globalCompositeOperation = dark ? "screen" : "soft-light"; c.globalAlpha = dark ? 0.55 : 0.95;
      var sw = v.back.width, sh = v.back.height, st = 1.5, ym, col, off, mag = 1.10, sl;
      for (y = top - 4; y < FLOOR; y += st) {
        ym = y - top; col = Math.max(0, Math.min(s.n - 1, Math.round((75 - IX0) / (IX1 - IX0) * (s.n - 1))));
        sl = (s.h[Math.min(s.n - 1, col + 1)] - s.h[Math.max(0, col - 1)]) * 0.5;
        off = Math.sin(y * 0.11 + t * 1.1) * 0.55 + Math.sin(y * 0.05 - t * 0.6) * 1.0 + sl * 3 - 3.2;
        c.drawImage(v.back, 0, y * S, sw, st * S, 75 - 75 * mag + off, y, VW * mag, st + 0.3);
      }
      c.globalAlpha = 1; c.globalCompositeOperation = "source-over";
    }
    // water absorbs toward the walls and the floor, and glows just under the surface
    g = c.createLinearGradient(IX0, 0, IX1, 0); g.addColorStop(0, "rgba(0,25,35,.30)"); g.addColorStop(0.16, "rgba(0,25,35,0)"); g.addColorStop(0.84, "rgba(0,25,35,0)"); g.addColorStop(1, "rgba(0,25,35,.26)");
    c.fillStyle = g; c.fillRect(IX0, top - 14, IX1 - IX0, d + 30);
    g = c.createLinearGradient(0, top, 0, top + 20); g.addColorStop(0, "rgba(255,255,255,.30)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.fillStyle = g; c.fillRect(IX0, top - 6, IX1 - IX0, 26);
    // caustics: bright, slowly crawling networks of light on the floor, bent by the waves
    if (d > 12) {
      var cb = Math.min(34, d - 3), cw = 50, ch = 22, cell = 80 / cw, id, px, val, aa, hw, fy, cx, cy, q;
      if (!v.cau) { v.cau = document.createElement("canvas"); v.cau.width = cw; v.cau.height = ch; v.cauCtx = v.cau.getContext("2d"); v.cauData = v.cauCtx.createImageData(cw, ch); }
      id = v.cauData; px = id.data;
      for (cy = 0; cy < ch; cy++) {
        fy = cy / (ch - 1); y = fy * cb;
        for (cx = 0; cx < cw; cx++) {
          x = cx * cell; hw = (s.h[Math.round(cx / (cw - 1) * (s.n - 1))] - d) * 0.9;
          val = (Math.sin(x * 0.31 + t * 0.55 + hw + Math.sin(y * 0.37 - t * 0.4) * 1.3) + Math.sin(y * 0.29 + x * 0.17 - t * 0.5) + Math.sin(x * 0.13 - y * 0.23 + t * 0.35 + hw * 0.5)) / 3;
          aa = Math.max(0, (val - 0.3) / 0.7); q = (cy * cw + cx) * 4;
          px[q] = 235; px[q + 1] = 255; px[q + 2] = 248; px[q + 3] = Math.round(255 * Math.pow(aa, 1.6) * 0.62 * (0.2 + 0.8 * fy));
        }
      }
      v.cauCtx.putImageData(id, 0, 0);
      c.globalCompositeOperation = "lighter"; c.imageSmoothingEnabled = true; c.imageSmoothingQuality = "high";
      c.drawImage(v.cau, IX0, FLOOR - cb, 80, cb); c.globalCompositeOperation = "source-over";
    }
    // bubbles
    if (d > 22) for (k = 0; k < v.bub.length; k++) {
      p = v.bub[k]; if (p.y < top + 2 || p.y > FLOOR) continue;
      x = p.x + Math.sin(t * 1.3 + p.ph) * 1.2;
      c.beginPath(); c.arc(x, p.y, p.r, 0, 7); c.fillStyle = "rgba(255,255,255,.12)"; c.fill(); c.strokeStyle = "rgba(255,255,255,.6)"; c.lineWidth = 0.55; c.stroke();
      c.beginPath(); c.arc(x - p.r * 0.35, p.y - p.r * 0.35, Math.max(0.3, p.r * 0.28), 0, 7); c.fillStyle = "rgba(255,255,255,.9)"; c.fill();
    }
    c.restore();   // out of the water

    // the surface, seen from just above: the far edge, the lit band, the bright front line
    c.beginPath(); for (i = 0; i < s.n; i++) { if (i) c.lineTo(pts[i].x, pts[i].y - 2.6 * (0.55 + 0.45 * Math.sin(Math.PI * i / (s.n - 1)))); else c.moveTo(pts[i].x, pts[i].y - 0.4); }
    for (i = s.n - 1; i >= 0; i--) c.lineTo(pts[i].x, pts[i].y);
    c.closePath(); g = c.createLinearGradient(0, top - 4, 0, top + 1); g.addColorStop(0, rgba(mix(w0, [255, 255, 255], 0.55).join(","), 0.5)); g.addColorStop(1, rgba(mix(w0, [255, 255, 255], 0.3).join(","), 0.5)); c.fillStyle = g; c.fill();
    c.beginPath(); for (i = 0; i < s.n; i++) { if (i) c.lineTo(pts[i].x, pts[i].y + 1.3); else c.moveTo(pts[i].x, pts[i].y + 1.3); }
    c.strokeStyle = "rgba(0,40,50,.28)"; c.lineWidth = 1.6; c.stroke();
    g = c.createLinearGradient(IX0, 0, IX1, 0); g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.2, "rgba(255,255,255,.78)"); g.addColorStop(0.8, "rgba(255,255,255,.78)"); g.addColorStop(1, "rgba(255,255,255,1)");
    c.beginPath(); for (i = 0; i < s.n; i++) { if (i) c.lineTo(pts[i].x, pts[i].y); else c.moveTo(pts[i].x, pts[i].y); }
    c.strokeStyle = g; c.lineWidth = 1.5; c.stroke();
    // glints: wave facets that face the light, and two broad highlights that drift along the surface
    c.globalCompositeOperation = "lighter";
    var L1 = -0.3 + lx * 0.5, L2 = 0.45 + lx * 0.5, hx1 = 75 + 24 * Math.sin(t * 0.21) + lx * 18, hx2 = 75 + 30 * Math.sin(t * 0.13 + 2.2) - lx * 12;
    for (i = 1; i < s.n - 1; i++) {
      var sl2 = (s.h[i + 1] - s.h[i - 1]) / ((IX1 - IX0) * 2 / (s.n - 1)), a = Math.exp(-Math.pow((sl2 - L1) / 0.2, 2)) + Math.exp(-Math.pow((sl2 - L2) / 0.2, 2));
      a = Math.min(1, a * Math.min(1, Math.abs(sl2) * 6 + 0.1));
      if (a > 0.08) { c.fillStyle = "rgba(255,255,255," + (a * 0.9).toFixed(3) + ")"; c.beginPath(); c.ellipse(pts[i].x, pts[i].y - 0.3, 2.1, 0.7, 0, 0, 7); c.fill(); }
    }
    [[hx1, 11, 0.85], [hx2, 7, 0.55]].forEach(function (hl) {
      var gx = c.createLinearGradient(hl[0] - hl[1], 0, hl[0] + hl[1], 0); gx.addColorStop(0, "rgba(255,255,255,0)"); gx.addColorStop(0.5, "rgba(255,255,255," + hl[2] + ")"); gx.addColorStop(1, "rgba(255,255,255,0)");
      c.beginPath(); for (i = 0; i < s.n; i++) { if (i) c.lineTo(pts[i].x, pts[i].y - 0.2); else c.moveTo(pts[i].x, pts[i].y - 0.2); }
      c.strokeStyle = gx; c.lineWidth = 2.2; c.stroke();
    });
    c.globalCompositeOperation = "source-over";
    c.restore();   // out of the glass interior

    // the etched aim line
    c.save(); c.beginPath(); c.moveTo(30, AIMY); c.lineTo(120, AIMY); c.strokeStyle = "#c9a84c"; c.lineWidth = 1.5; c.setLineDash([4, 3]); c.stroke(); c.restore();

    // the glass: a thick wall, a thick base, lit from the side
    c.save(); c.beginPath(); glassPath(c); innerPath(c);
    g = c.createLinearGradient(30, 0, 120, 0);
    g.addColorStop(0, "rgba(205,235,240,.55)"); g.addColorStop(0.1, "rgba(205,235,240,.30)"); g.addColorStop(0.5, "rgba(205,235,240,.20)"); g.addColorStop(0.9, "rgba(205,235,240,.30)"); g.addColorStop(1, "rgba(205,235,240,.50)");
    c.fillStyle = g; c.fill("evenodd");
    c.restore();
    c.beginPath(); c.moveTo(35.5, 24); c.lineTo(35.5, FLOOR - 7); c.strokeStyle = "rgba(0,30,40,.28)"; c.lineWidth = 0.8; c.stroke();
    c.beginPath(); c.moveTo(114.5, 24); c.lineTo(114.5, FLOOR - 7); c.stroke();
    c.beginPath(); c.moveTo(IX0 + 6, FLOOR + 0.8); c.lineTo(IX1 - 6, FLOOR + 0.8); c.strokeStyle = "rgba(255,255,255,.55)"; c.lineWidth = 1.1; c.stroke();   // the floor of the glass catches light
    g = c.createLinearGradient(0, 22, 0, 148); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.15, "rgba(255,255,255,.85)"); g.addColorStop(0.8, "rgba(255,255,255,.7)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.beginPath(); c.moveTo(32.6, 22); c.lineTo(32.6, 148); c.strokeStyle = g; c.lineWidth = 2.4; c.stroke();
    c.beginPath(); c.moveTo(41, 30); c.lineTo(41, 112); c.strokeStyle = "rgba(255,255,255,.28)"; c.lineWidth = 2; c.stroke();
    g = c.createLinearGradient(0, 40, 0, 140); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,255,255,.5)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.beginPath(); c.moveTo(117.4, 40); c.lineTo(117.4, 140); c.strokeStyle = g; c.lineWidth = 1.5; c.stroke();
    c.beginPath(); glassPath(c); c.strokeStyle = "rgba(160,185,198,.9)"; c.lineWidth = 1.3; c.stroke();
    // the rim: the far half dim, the near half bright, and the wall's thickness between two ellipses
    c.beginPath(); c.ellipse(75, 16, 45, 3.5, 0, Math.PI, 2 * Math.PI); c.strokeStyle = "rgba(170,190,200,.5)"; c.lineWidth = 1.2; c.stroke();
    c.beginPath(); c.ellipse(75, 16, 45, 3.5, 0, 0, Math.PI); c.strokeStyle = "rgba(190,210,220,.95)"; c.lineWidth = 1.5; c.stroke();
    c.beginPath(); c.ellipse(75, 16.2, 40, 2.9, 0, 0, Math.PI); c.strokeStyle = "rgba(255,255,255,.6)"; c.lineWidth = 0.9; c.stroke();
    c.beginPath(); c.ellipse(75, 16, 41, 3.0, 0, Math.PI * 1.1, Math.PI * 1.9); c.strokeStyle = "rgba(255,255,255,.35)"; c.lineWidth = 0.8; c.stroke();

    // the label at the line
    c.fillStyle = v.ink; c.globalAlpha = 0.78; c.font = "10px " + v.font; c.textBaseline = "alphabetic"; c.fillText(v.aim, 124, AIMY + 4); c.globalAlpha = 1;
  }

  /* ---- vessels and the one shared loop ---- */
  function readTheme(v) {
    try {
      var cs = getComputedStyle(v.el), m = /rgba?\((\d+)[ ,]+(\d+)[ ,]+(\d+)/.exec(cs.color) || [0, 20, 20, 20], lum = (+m[1] * 299 + +m[2] * 587 + +m[3] * 114) / 1000;
      var dk = lum > 140; v.ink = cs.color || "#222"; v.font = cs.fontFamily || "sans-serif";
      if (dk !== v.dark || !v.back) { v.dark = dk; v.back = makeBackdrop(v.S, dk, true); v.air = makeBackdrop(v.S, dk, false); }
    } catch (e) { v.ink = v.ink || "#222"; v.font = v.font || "sans-serif"; }
  }
  function visible(v) { return !vis || vis.get(v.el) !== false; }
  function sleepy(v) { return energy(v.s) < 0.004 && Math.abs(v.s.tilt - v.tiltSeen) < 0.01; }

  function loopStart() { if (!raf && !still() && vessels.length && !document.hidden) { last = 0; raf = requestAnimationFrame(frame); } }
  function frame(now) {
    raf = 0; var dt = last ? Math.min(0.1, (now - last) / 1000) : DT, any = false, i, v, lx;
    last = now; vessels = vessels.filter(function (x) { if (x.el.isConnected) return true; if (io) io.unobserve(x.el); return false; });
    lx = (window.SXTouch && SXTouch.light ? SXTouch.light.x : 0) || 0;
    for (i = 0; i < vessels.length; i++) {
      v = vessels[i]; if (!visible(v)) continue; any = true;
      v.s.tilt = lx; v.clock += dt;
      if (v.clock > v.nextBreath) { splash(v.s, Math.random() * (N - 1), 0.05); v.nextBreath = v.clock + 2 + Math.random() * 3; }
      step(v.s, dt, lx); v.sinceDraw += dt;
      if (sleepy(v) && v.sinceDraw < 0.05) continue;   // calm: 20 frames a second is plenty
      v.tiltSeen = lx; v.sinceDraw = 0;
      for (var k = 0; k < v.bub.length; k++) { var b = v.bub[k]; b.y -= b.sp * 0.05; if (b.y < FLOOR - v.s.h[Math.max(0, Math.min(N - 1, Math.round((b.x - IX0) / (IX1 - IX0) * (N - 1))))] + 1) { b.y = FLOOR - 4; b.x = IX0 + 8 + Math.random() * (IX1 - IX0 - 16); } }
      if (++v.n % 90 === 1) readTheme(v);
      render(v, v.clock);
    }
    if (any && !document.hidden) raf = requestAnimationFrame(frame);
  }

  function vessel(el, f, state, aim, label) {
    if (!el || el.getAttribute("data-sxw")) return null;
    var cv, ctx; try { cv = document.createElement("canvas"); ctx = cv.getContext && cv.getContext("2d"); } catch (e) { ctx = null; }
    if (!ctx) return null;   // no 2D canvas: the SVG stays
    var S = Math.min(2, window.devicePixelRatio || 1), s = make(depth(f));
    cv.width = Math.ceil(VW * S); cv.height = Math.ceil(VH * S); cv.setAttribute("aria-hidden", "true");
    cv.style.cssText = "position:absolute;left:0;top:0;width:" + VW + "px;height:" + VH + "px;touch-action:pan-y;cursor:pointer";
    var v = { el: el, ctx: ctx, S: S, s: s, state: state || "low", aim: String(aim || "").replace(/[<>&"]/g, ""), bub: [], clock: 0, nextBreath: 1.5, sinceDraw: 0, n: 0, tiltSeen: 0, dark: null, back: null, ink: "#222", font: "sans-serif" };
    for (var k = 0; k < 6; k++) v.bub.push({ x: IX0 + 8 + Math.random() * (IX1 - IX0 - 16), y: FLOOR - Math.random() * s.depth, r: 0.8 + Math.random() * 1.1, sp: 7 + Math.random() * 6, ph: Math.random() * 6 });
    if (label && !el.getAttribute("aria-label")) el.setAttribute("aria-label", label);
    el.setAttribute("role", "img"); el.setAttribute("data-sxw", "1");
    var svg = el.querySelector("svg"); if (svg) svg.style.display = "none";
    el.appendChild(cv); readTheme(v); render(v, 0);
    var col = function (e) { var r = cv.getBoundingClientRect(); return Math.max(0, Math.min(N - 1, ((e.clientX - r.left) / (r.width || VW) * VW - IX0) / (IX1 - IX0) * (N - 1))); };
    var lastX = null;
    cv.addEventListener("pointerdown", function (e) { lastX = e.clientX; splash(s, col(e), 1.2); loopStart(); }, { passive: true });
    cv.addEventListener("pointermove", function (e) {
      if (!(e.buttons || e.pointerType === "touch") || lastX == null) return;
      var dx = e.clientX - lastX; lastX = e.clientX; splash(s, col(e), Math.min(0.8, Math.abs(dx) * 0.06 + 0.1)); loopStart();
    }, { passive: true });
    cv.addEventListener("pointerup", function () { lastX = null; }, { passive: true });
    if (still()) return v;   // one still frame, no loop
    vessels.push(v);
    if (io) io.observe(el);
    loopStart();
    return v;
  }

  function scan(root) {
    var list = (root || document).querySelectorAll ? (root || document).querySelectorAll(".sx-water[data-f]:not([data-sxw])") : [], i, e;
    for (i = 0; i < list.length; i++) { e = list[i]; try { vessel(e, parseFloat(e.getAttribute("data-f")), e.getAttribute("data-state"), e.getAttribute("data-aim"), e.getAttribute("aria-label")); } catch (x) {} }
  }

  window.SXWater = { make: make, depth: depth, step: step, splash: splash, energy: energy, mean: mean, vessel: vessel, scan: scan };

  // Upgrade every vessel the page draws, now and whenever a screen is redrawn.
  try {
    if (typeof document !== "undefined" && !/jsdom/i.test(navigator.userAgent || "")) {
      if (typeof IntersectionObserver === "function") { vis = new Map(); io = new IntersectionObserver(function (es) { es.forEach(function (e) { vis.set(e.target, e.isIntersecting); }); loopStart(); }, { rootMargin: "80px" }); }
      var pending = 0, go = function () { pending = 0; scan(document); };
      new MutationObserver(function () { if (!pending) pending = setTimeout(go, 40); }).observe(document.documentElement, { childList: true, subtree: true });
      document.addEventListener("visibilitychange", function () { if (!document.hidden) loopStart(); });
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else setTimeout(go, 0);
    }
  } catch (e) {}
})();
