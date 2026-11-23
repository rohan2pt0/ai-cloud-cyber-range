/* SecuRAX shared gold (reuse-first, immersive-real, natures-design; owner 2026-11-23): polished gold ingots that shine.
   The net-worth bars are drawn as real trapezoid prisms (a top face, a front face and two sloped sides), shaded per pixel
   with physically based gold: Fresnel reflectance F0 (0.944, 0.776, 0.373) in linear RGB with Schlick's approximation,
   a glossy mirror (roughness about 0.25) of a small studio (a dark room, one large soft box above, a light strip, a horizon
   line, a warm floor), an ACES tone map, a bright bevel, an embossed "999.9" hallmark, contact shadows and a soft
   reflection in the floor. The light follows the phone's tilt or the pointer (SXTouch.light) like the other metals,
   and a slow glint travels across the stack. It is one <canvas> per stack and one shared animation loop that runs only
   while a stack is on screen and the light moves or a glint runs. Under reduced motion, in tests and in audits it draws
   one still frame and never starts a loop. Where a 2D canvas is missing, the SVG from SXWorld.goldBars stays. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXGold) return;
  var doc = document;
  var F0 = [0.944, 0.776, 0.373];
  var EL = 38 * Math.PI / 180, SE = Math.sin(EL), CE = Math.cos(EL);   // the camera looks down at 38 degrees
  var PERIOD = 9000, GLINT = 0.17;                                      // a glint sweep every ~9 s, about 1.5 s long
  var BEVEL = 1.5;                                                      // css px of polished chamfer on the edges

  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function sstep(a, b, x) { var t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
  function norm(v) { var l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; }
  var calm = function () { try { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); } catch (e) { return false; } };
  var still = function () { return calm() || !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || ""); };

  /* ---- the studio: radiance (linear) seen along a reflected direction; az 0 = straight back, +-pi = towards the viewer ---- */
  var S = { ca: 0, ce: .78, sa: .12, lx: 0 }, ER = 0, EG = 0, EB = 0;
  function setLight(lx, ly) { S.lx = lx; S.ca = lx * .6; S.ce = .78 - ly * .3; S.sa = .12 + lx * .55; }
  function wrap(a) { return a > 0 ? a - Math.PI : a + Math.PI; }
  function env(az, el) {
    var r = .012, g = .010, b = .009, f, t;
    if (el < 0) { f = .05 + .8 * Math.exp(el / .2); r += f; g += f * .62; b += f * .30; }              // a warm floor, brightest at the horizon
    t = el / .045; f = 1.15 * Math.exp(-t * t * .5); r += f; g += f * .96; b += f * .88;                    // the horizon line
    var da = (az - S.ca) / .85, de = (el - S.ce) / .42, k = 1 - sstep(.7, 1.25, Math.sqrt(da * da + de * de));
    if (k > 0) { f = 1.55 * k * (.55 + .9 * Math.exp(-da * da * 1.6 - (de + .35) * (de + .35) * 2.2)); r += f; g += f * .92; b += f * .78; }    // the large soft box above
    var af = wrap(az), sa = af - S.sa;                                                                      // a tall light strip in front
    f = Math.exp(-sa * sa / (2 * .05 * .05)) * (1 - sstep(.12, .4, Math.abs(el - .05))) * 2.6;
    r += f; g += f * .94; b += f * .82;
    sa = af + .55 - S.lx * .5; f = Math.exp(-sa * sa / (2 * .12 * .12)) * (1 - sstep(.2, .5, Math.abs(el - .05))) * 1.2;   // a dim fill card on the other side
    r += f; g += f * .85; b += f * .65;
    ER = r; EG = g; EB = b;
  }
  var LUT = new Uint8ClampedArray(1024);
  for (var li = 0; li < 1024; li++) LUT[li] = Math.round(255 * Math.pow(li / 1023, 1 / 2.2));
  function aces(x) { x = x * (2.51 * x + .03) / (x * (2.43 * x + .59) + .14); return x < 0 ? 0 : x > 1 ? 1 : x; }
  var SAT = 1.32;   // a polished highlight stays yellow, not cream: push each channel away from grey after the tone map
function sat(r, g, b, o) { var l = .3 * r + .59 * g + .11 * b; o[0] = clamp(l + (r - l) * SAT, 0, 1); o[1] = clamp(l + (g - l) * SAT, 0, 1); o[2] = clamp(l + (b - l) * SAT, 0, 1); }
var TM = [0, 0, 0];
function fres(c, i) { var m = Math.pow(1 - c, 5); return F0[i] + (1 - F0[i]) * m; }

  /* shade(normal, view, light): the colour (0..255) of polished gold for a surface normal seen from `view` (both unit
     vectors, y up, z towards the viewer) with the light tilted by light.x, light.y (each -1..1). Pure, used by the tests. */
  function shade(n, v, light) {
    n = norm(n); v = norm(v); light = light || {};
    setLight(+light.x || 0, +light.y || 0);
    var c = Math.max(.02, n[0] * v[0] + n[1] * v[1] + n[2] * v[2]);
    var rx = 2 * c * n[0] - v[0], ry = 2 * c * n[1] - v[1], rz = 2 * c * n[2] - v[2];
    env(Math.atan2(rx, -rz), Math.asin(clamp(ry, -1, 1)));
    sat(aces(fres(c, 0) * ER), aces(fres(c, 1) * EG), aces(fres(c, 2) * EB), TM);
    return [LUT[Math.round(TM[0] * 1023)], LUT[Math.round(TM[1] * 1023)], LUT[Math.round(TM[2] * 1023)]];
  }
  /* the direction a ray must come from to show the middle of the soft box (a mirror faces half way between it and the viewer) */
  function lightDir(light) {
    setLight(+(light && light.x) || 0, +(light && light.y) || 0);
    return [Math.sin(S.ca) * Math.cos(S.ce), Math.sin(S.ce), -Math.cos(S.ca) * Math.cos(S.ce)];
  }

  /* ---- the hallmark: "999.9" as a small height map, so it can be embossed in the normal ---- */
  var HMS = {}, HM = null, HW = 300, HH = 90;
  function hallmark(text) {   // text: the clean "999.9"; otherwise a small rectangular stamp recess
    var key = text ? "t" : "r"; if (HMS[key]) { HM = HMS[key]; return HM; }
    HM = HMS[key] = new Float32Array(HW * HH);
    try {
      var c = doc.createElement("canvas"); c.width = HW; c.height = HH; var x = c.getContext("2d"); if (!x) return HM;
      x.fillStyle = "#000"; x.fillRect(0, 0, HW, HH); x.fillStyle = "#fff"; x.textAlign = "center"; x.textBaseline = "middle";
      if (text) { x.font = "bold 62px Helvetica, Arial, sans-serif"; x.fillText("999.9", HW / 2, HH / 2 + 3); }
      else x.fillRect(HW * .3, HH * .3, HW * .4, HH * .4);
      var d = x.getImageData(0, 0, HW, HH).data, i, j, t = new Float32Array(HW * HH);
      for (i = 0; i < HW * HH; i++) t[i] = d[i * 4] / 255;
      for (var p = 0; p < 3; p++) { for (j = 1; j < HH - 1; j++) for (i = 1; i < HW - 1; i++) { var q = j * HW + i; HM[q] = (t[q] * 4 + t[q - 1] + t[q + 1] + t[q - HW] + t[q + HW]) / 8; } t.set(HM); }
    } catch (e) {}
    return HM;
  }
  function hgrad(u, v) {   // gradient of the hallmark height at u,v in 0..1
    var i = clamp(Math.round(u * (HW - 1)), 2, HW - 3), j = clamp(Math.round(v * (HH - 1)), 2, HH - 3), q = j * HW + i;
    return [(HM[q + 2] - HM[q - 2]) * .25, (HM[q + 2 * HW] - HM[q - 2 * HW]) * .25];
  }

  /* ---- the geometry of one stack ---- */
  function build(have, want, dpr) {
    var per = 4; while (per < 8 && per * (per + 1) / 2 < want) per++;
    var rows = 0, cap = 0; while (cap < want && rows < per) { cap += per - rows; rows++; }   // the pyramid holds 36
    var bw = Math.min(70, Math.floor(300 / per)), pitch = bw + 6, D = bw * .46, Hh = bw * .25, ix = bw * .12, iz = D * .17, PAD = 10, mg = (D - 2 * iz) * .24;
    var Lt = bw - 2 * ix, Dt = D - 2 * iz;
    var idxOf = function (r, c) { var n = 0; for (var k = 0; k < r; k++) n += per - k; return n + c; };
    var proj = function (x, y, z) { return [x, -(y * CE - z * SE)]; };
    var ox = PAD + bw / 2, minY = 1e9, bars = [], i;
    for (i = 0; i < want; i++) {
      var r = 0, c = i; while (c >= per - r) { c -= per - r; r++; }
      var cx = ox + r * pitch / 2 + c * pitch, yb = r * Hh, zc = r * -(iz + mg);   // each row rests ON the row below: its front edge on their top faces, set back
      bars.push({ i: i, r: r, c: c, cx: cx, yb: yb, zc: zc, ghost: i >= have });
      minY = Math.min(minY, proj(cx, yb + Hh, zc - Dt / 2)[1]);
    }
    var W = per * pitch + 2 * PAD + rows * 0, refH = Math.round(Hh * CE * .9), top = 8 - minY, baseY = top + proj(0, 0, D / 2)[1];
    var H = Math.ceil(baseY + refH + 8);
    var textOk = Lt >= 28 && Dt * SE * .62 >= 7;   // a clean hallmark only where it is big enough to read
    var g = { text: textOk, per: per, rows: rows, bw: bw, W: Math.ceil(W), H: H, dpr: dpr, bars: bars, refH: refH, baseY: baseY, oy: top, D: D, Hh: Hh, L: bw, Lt: Lt, Dt: Dt, ix: ix, iz: iz, faces: [], idxOf: idxOf };
    var P = function (x, y, z) { var p = proj(x, y, z); return [p[0], p[1] + top]; };
    bars.forEach(function (b) {
      var x0 = b.cx - bw / 2, x1 = b.cx + bw / 2, t0 = b.cx - Lt / 2, t1 = b.cx + Lt / 2, y0 = b.yb, y1 = b.yb + Hh;
      var fz = b.zc + D / 2, bz = b.zc - D / 2, tf = b.zc + Dt / 2, tb = b.zc - Dt / 2;
      var nF = norm([0, iz, Hh]), nT = [0, 1, 0], nL = norm([-Hh, ix, 0]), nR = norm([Hh, ix, 0]), nB = norm([0, iz, -Hh]);
      b.q = { front: [P(x0, y0, fz), P(x1, y0, fz), P(t1, y1, tf), P(t0, y1, tf)], top: [P(t0, y1, tf), P(t1, y1, tf), P(t1, y1, tb), P(t0, y1, tb)] };   // outlines, for the ghosts
      if (b.ghost) return;
      var tint = .94 + .08 * (Math.sin(b.i * 12.9898) * .5 + .5), seed = b.i * 1.7;
      var up = [];   // the bars that rest on this one
      if (b.r + 1 < rows) { var a = idxOf(b.r + 1, b.c - 1), c2 = idxOf(b.r + 1, b.c); if (b.c - 1 >= 0 && a < have) up.push(bars[a]); if (b.c < per - b.r - 1 && c2 < have) up.push(bars[c2]); }
      g.faces.push({ type: "front", bar: b, pts: [P(x0, y0, fz), P(x1, y0, fz), P(t1, y1, tf), P(t0, y1, tf)], v0: [x0, y0, fz], n: nF, adj: [null, nR, nT, nL], tint: tint, seed: seed, up: up });
      g.faces.push({ type: "top", bar: b, pts: [P(t0, y1, tf), P(t1, y1, tf), P(t1, y1, tb), P(t0, y1, tb)], v0: [t0, y1, tf], n: nT, adj: [nF, nR, nB, nL], tint: tint, seed: seed, up: up });
      g.faces.push({ type: "side", bar: b, pts: [P(x0, y0, bz), P(x0, y0, fz), P(t0, y1, tf), P(t0, y1, tb)], v0: [x0, y0, bz], n: nL, adj: [null, null, nT, null], tint: tint, seed: seed, up: up });
      g.faces.push({ type: "side", bar: b, pts: [P(x1, y0, fz), P(x1, y0, bz), P(t1, y1, tb), P(t1, y1, tf)], v0: [x1, y0, fz], n: nR, adj: [null, null, nT, null], tint: tint, seed: seed, up: up });
    });
    return g;
  }

  /* Per face and per device pixel: coverage, the reflected direction, the Fresnel colour, occlusion. Built once. */
  function cacheFace(g, f) {
    var dpr = g.dpr, Wd = Math.ceil(g.W * dpr), Hd = Math.ceil(g.H * dpr), pts = f.pts, n = f.n, b = f.bar, hm = f.type === "top" ? hallmark(g.text) : null;
    var minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9, i, area = 0;
    for (i = 0; i < 4; i++) { var A = pts[i], B = pts[(i + 1) % 4]; minx = Math.min(minx, A[0]); maxx = Math.max(maxx, A[0]); miny = Math.min(miny, A[1]); maxy = Math.max(maxy, A[1]); area += A[0] * B[1] - B[0] * A[1]; }
    var sgn = area > 0 ? 1 : -1, x0 = Math.max(0, Math.floor((minx - 1) * dpr)), x1 = Math.min(Wd - 1, Math.ceil((maxx + 1) * dpr)), y0 = Math.max(0, Math.floor((miny - 1) * dpr)), y1 = Math.min(Hd - 1, Math.ceil((maxy + 1) * dpr));
    var D = g.D, Hh = g.Hh, den = n[1] * SE + n[2] * CE, ny0 = n[1] * CE - n[2] * SE;
    var d = n[0] * f.v0[0] + n[1] * f.v0[1] + n[2] * f.v0[2], cnt = 0, cap = (x1 - x0 + 1) * (y1 - y0 + 1);
    var idx = new Int32Array(cap), dat = new Float32Array(cap * 10);
    var bev = BEVEL * dpr, halfW = g.W / 2;
    for (var iy = y0; iy <= y1; iy++) for (var ixp = x0; ixp <= x1; ixp++) {
      var px = (ixp + .5) / dpr, py = (iy + .5) / dpr, dmin = 1e9, em = 0;
      for (i = 0; i < 4; i++) {
        var a = pts[i], c2 = pts[(i + 1) % 4], ex = c2[0] - a[0], ey = c2[1] - a[1], len = Math.hypot(ex, ey) || 1;
        var dd = sgn * (ex * (py - a[1]) - ey * (px - a[0])) / len * dpr; if (dd < dmin) { dmin = dd; em = i; }
      }
      var cov = clamp(dmin + .5, 0, 1); if (cov <= 0) continue;
      var vv = g.oy - py, s = (d - n[0] * px - vv * ny0) / den, Py = vv * CE + s * SE, Pz = -vv * SE + s * CE;
      var nx = n[0], ny = n[1], nz = n[2], ao = 1, gain = 1, tx, tz, fx, fy;
      var nse = Math.sin(px * .23 + Py * .17 + f.seed) * Math.sin(px * .11 - Pz * .29 + f.seed * 2.3) * .022;
      if (f.type === "front") {
        fx = clamp((px - b.cx) / (g.L / 2), -1, 1); fy = clamp((Py - b.yb) / Hh, 0, 1);
        nx += fx * .10 + nse; ny += (fy - .5) * .34 + nse * .6; ao = .74 + .26 * sstep(0, .4, fy); gain = .75;
      } else if (f.type === "top") {
        tx = clamp((px - b.cx) / (g.Lt / 2), -1, 1); tz = clamp((Pz - b.zc) / (g.Dt / 2), -1, 1);
        nx += -tx * .13 + nse; nz += -tz * .17 + nse * .6; gain = 1;
        if (hm) { var gr = hgrad((tx + 1) / 2, (tz + 1) / 2); nx -= gr[0] * 1.6; nz -= gr[1] * 1.6; }
        for (var u = 0; u < f.up.length; u++) {   // the bar resting above shades the top face in front of it
          var ub = f.up[u], dx = Math.max(0, Math.abs(px - ub.cx) - g.L / 2), dz = Pz - (ub.zc + D / 2);
          if (dz > -1) ao *= 1 - .62 * Math.exp(-Math.max(0, dz) / (D * .16)) * Math.exp(-dx / (g.L * .09));
        }
      } else {
        var sy = clamp((Py - b.yb) / Hh, 0, 1); ny += (sy - .5) * .2 + nse; ao = .62 + .3 * sstep(0, 1, sy); gain = .5;
      }
      var adjn = f.adj[em];
      if (adjn && dmin < bev) {   // the polished chamfer: the normal turns half way to the neighbour face
        var tt = 1 - dmin / bev, hx = nx + adjn[0], hy = ny + adjn[1], hz = nz + adjn[2], hl = Math.hypot(hx, hy, hz) || 1;
        nx = nx * (1 - tt) + hx / hl * tt; ny = ny * (1 - tt) + hy / hl * tt; nz = nz * (1 - tt) + hz / hl * tt; gain = 2.2;
      }
      var nl = Math.hypot(nx, ny, nz); nx /= nl; ny /= nl; nz /= nl;
      var vx = (px - halfW) / halfW * .2, vl = Math.hypot(vx, SE, CE), cx = vx / vl, cy = SE / vl, cz = CE / vl;   // a mild perspective
      var cs = Math.max(.02, nx * cx + ny * cy + nz * cz);
      var rx = 2 * cs * nx - cx, ry = 2 * cs * ny - cy, rz = 2 * cs * nz - cz, o = cnt * 10;
      idx[cnt] = iy * Wd + ixp; dat[o] = cov; dat[o + 1] = Math.atan2(rx, -rz); dat[o + 2] = Math.asin(clamp(ry, -1, 1));
      dat[o + 3] = fres(cs, 0) * ao * f.tint; dat[o + 4] = fres(cs, 1) * ao * f.tint; dat[o + 5] = fres(cs, 2) * ao * f.tint; dat[o + 6] = gain;
      dat[o + 7] = px / g.W; dat[o + 8] = py / g.H; cnt++;
    }
    f.cnt = cnt; f.idx = idx.subarray(0, cnt); f.dat = dat.subarray(0, cnt * 10);
  }

  /* ---- one stack on a canvas ---- */
  function floorBase(g, ctx) {
    var dpr = g.dpr, W = g.W * dpr, H = g.H * dpr, y = g.baseY * dpr, i, b;
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    var rw = g.per * (g.bw + 4) * dpr / 2, cxm = g.W * dpr / 2;
    ctx.translate(cxm, y); ctx.scale(1, .1); var rg = ctx.createRadialGradient(0, 0, 0, 0, 0, rw * 1.02); rg.addColorStop(0, "rgba(0,0,0,.55)"); rg.addColorStop(.7, "rgba(0,0,0,.3)"); rg.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(0, 0, rw * 1.02, 0, 6.2832); ctx.fill(); ctx.restore();
    for (i = 0; i < g.bars.length; i++) {   // a contact shadow under each bar that rests on the floor
      b = g.bars[i]; if (b.r || b.ghost) continue;
      ctx.save(); ctx.translate((b.cx + 3) * dpr, y + 1 * dpr); ctx.scale(1, .16);
      var sg = ctx.createRadialGradient(0, 0, 0, 0, 0, g.bw * .62 * dpr); sg.addColorStop(0, "rgba(0,0,0,.6)"); sg.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(0, 0, g.bw * .62 * dpr, 0, 6.2832); ctx.fill(); ctx.restore();
    }
  }

  function make(el, have, want) {
    var cv = doc.createElement("canvas"), ctx = null;
    try { ctx = cv.getContext("2d"); } catch (e) { ctx = null; }
    if (!ctx || typeof ctx.getImageData !== "function") return null;
    var dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1)), g = build(have, want, dpr);
    cv.width = Math.ceil(g.W * dpr); cv.height = Math.ceil(g.H * dpr);
    cv.style.cssText = "width:" + g.W + "px;max-width:100%;height:auto;aspect-ratio:" + g.W + "/" + g.H + ";display:block";
    cv.setAttribute("aria-hidden", "true");
    floorBase(g, ctx);
    var base = ctx.getImageData(0, 0, cv.width, cv.height);
    g.faces.forEach(function (f) { cacheFace(g, f); });
    var sil = new Float32Array(cv.width).fill(1e9);   // the top silhouette, where the glint sparkles
    g.faces.forEach(function (f) { for (var k = 0; k < f.cnt; k++) { var ix2 = f.idx[k] % cv.width, y2 = (f.idx[k] - ix2) / cv.width; if (y2 < sil[ix2]) sil[ix2] = y2; } });
    var tc = doc.createElement("canvas"); tc.width = cv.width; tc.height = Math.max(1, Math.round(g.refH * dpr));
    var inst = { el: el, cv: cv, ctx: ctx, g: g, base: base, out: ctx.createImageData(cv.width, cv.height), sil: sil, tc: tc, vis: true, lx: 9, ly: 9, glint: -1 };
    inst.draw = function (lx, ly, ph) { draw(inst, lx, ly, ph); };
    el.appendChild(cv);
    return inst;
  }

  function draw(inst, lx, ly, ph) {
    var g = inst.g, cv = inst.cv, ctx = inst.ctx, out = inst.out, od = out.data, W = cv.width, dpr = g.dpr;
    od.set(inst.base.data); setLight(lx, ly);
    var gl = ph >= 0 && ph < GLINT ? ph / GLINT : -1, sc = gl < 0 ? 0 : -.3 + 1.7 * gl, ca = Math.cos(.38), sa = Math.sin(.38);
    for (var fi = 0; fi < g.faces.length; fi++) {
      var f = g.faces[fi], idx = f.idx, dat = f.dat;
      for (var k = 0, o = 0; k < f.cnt; k++, o += 10) {
        env(dat[o + 1], dat[o + 2]);
        var r = ER, gg = EG, b = EB;
        if (gl >= 0) { var q = ((dat[o + 7] * ca + dat[o + 8] * sa * .5) - sc) / .06, gv = Math.exp(-q * q) * dat[o + 6] * 3; r += gv; gg += gv * .93; b += gv * .8; }
        sat(aces(r * dat[o + 3]), aces(gg * dat[o + 4]), aces(b * dat[o + 5]), TM); r = TM[0]; gg = TM[1]; b = TM[2];
        var p = idx[k] * 4, cov = dat[o], R = LUT[(r * 1023) | 0], G = LUT[(gg * 1023) | 0], B = LUT[(b * 1023) | 0];
        if (cov > .995) { od[p] = R; od[p + 1] = G; od[p + 2] = B; od[p + 3] = 255; }
        else {
          var ba = od[p + 3] / 255, oa = cov + ba * (1 - cov);
          od[p] = (R * cov + od[p] * ba * (1 - cov)) / oa; od[p + 1] = (G * cov + od[p + 1] * ba * (1 - cov)) / oa; od[p + 2] = (B * cov + od[p + 2] * ba * (1 - cov)) / oa; od[p + 3] = oa * 255;
        }
      }
    }
    ctx.putImageData(out, 0, 0);
    // the soft reflection in the polished floor under the first row
    var tc = inst.tc, tx = tc.getContext("2d"), rh = tc.height, by = Math.round(g.baseY * dpr);
    if (tx && rh > 1) {
      tx.save(); tx.globalCompositeOperation = "copy"; tx.translate(0, rh); tx.scale(1, -1); tx.drawImage(cv, 0, by - rh, W, rh, 0, 0, W, rh); tx.restore();
      tx.globalCompositeOperation = "destination-in"; var gr = tx.createLinearGradient(0, 0, 0, rh); gr.addColorStop(0, "rgba(0,0,0,.30)"); gr.addColorStop(1, "rgba(0,0,0,0)");
      tx.fillStyle = gr; tx.fillRect(0, 0, W, rh); tx.globalCompositeOperation = "source-over";
      ctx.drawImage(tc, 0, by + 1);
    }
    // ghosts: what is still missing to the aim, outlined
    ctx.save(); ctx.scale(dpr, dpr); ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
    g.bars.forEach(function (bar) {
      if (!bar.ghost) return;
      ["front", "top"].forEach(function (k) {
        var q = bar.q[k]; ctx.beginPath(); ctx.moveTo(q[0][0], q[0][1]); for (var i = 1; i < 4; i++) ctx.lineTo(q[i][0], q[i][1]); ctx.closePath();
        ctx.fillStyle = "rgba(201,168,76,.06)"; ctx.fill(); ctx.strokeStyle = k === "front" ? "rgba(201,168,76,.6)" : "rgba(201,168,76,.45)"; ctx.stroke();
      });
    });
    ctx.restore();
    if (gl >= 0) sparkle(inst, gl);
  }

  function sparkle(inst, gl) {   // a small star where the glint crosses the top edge of the stack
    var g = inst.g, ctx = inst.ctx, dpr = g.dpr, cvw = inst.cv.width, xs = (clamp((-.3 + 1.7 * gl) * .9, 0, 1) * cvw) | 0;
    var y = inst.sil[Math.min(cvw - 1, xs)]; if (!(y < 1e8)) return;
    var a = Math.sin(Math.PI * gl), r = (7 + g.bw * .12) * dpr * a;
    ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.translate(xs, y + 1.5 * dpr);
    var rg = ctx.createRadialGradient(0, 0, 0, 0, 0, r * .8); rg.addColorStop(0, "rgba(255,244,214," + (.85 * a) + ")"); rg.addColorStop(1, "rgba(255,214,120,0)");
    ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(0, 0, r * .8, 0, 6.2832); ctx.fill();
    [[1, 0], [0, 1]].forEach(function (d) {
      var lg = ctx.createLinearGradient(-d[0] * r * 1.6, -d[1] * r * 1.6, d[0] * r * 1.6, d[1] * r * 1.6);
      lg.addColorStop(0, "rgba(255,236,190,0)"); lg.addColorStop(.5, "rgba(255,248,226," + (.9 * a) + ")"); lg.addColorStop(1, "rgba(255,236,190,0)");
      ctx.strokeStyle = lg; ctx.lineWidth = Math.max(1, dpr * .9); ctx.beginPath(); ctx.moveTo(-d[0] * r * 1.6, -d[1] * r * 1.6); ctx.lineTo(d[0] * r * 1.6, d[1] * r * 1.6); ctx.stroke();
    });
    ctx.restore();
  }

  /* ---- one shared loop: only while a stack is on screen, the page is visible, and the light moves or a glint runs ---- */
  var insts = [], raf = 0, timer = 0, io = null, lastDraw = 0;
  function light() { var l = window.SXTouch && window.SXTouch.light; return l ? { x: +l.x || 0, y: +l.y || 0 } : { x: 0, y: 0 }; }
  function sched(fast) {
    if (raf || !insts.length || doc.hidden) return;
    if (fast) { if (timer) { clearTimeout(timer); timer = 0; } raf = requestAnimationFrame(tick); }
    else if (!timer) timer = setTimeout(function () { timer = 0; tick(); }, 180);
  }
  function tick() {
    raf = 0; var now = (window.performance && performance.now) ? performance.now() : Date.now(), L = light(), phase = (now % PERIOD) / PERIOD, active = false;
    insts = insts.filter(function (i) { return i.el.isConnected; });
    for (var k = 0; k < insts.length; k++) {
      var i = insts[k]; if (!i.vis) continue;
      var moved = Math.abs(L.x - i.lx) + Math.abs(L.y - i.ly) > .008, gl = phase < GLINT || i.glint >= 0;
      if (moved || phase < GLINT) active = true;
      if (i.lx === 9 || ((moved || gl) && now - lastDraw >= 28)) { i.draw(L.x, L.y, phase < GLINT ? phase : -1); i.lx = L.x; i.ly = L.y; i.glint = phase < GLINT ? phase : -1; lastDraw = now; }
    }
    sched(active);
  }
  function register(inst) {
    insts.push(inst);
    try { if (typeof IntersectionObserver === "function") { if (!io) io = new IntersectionObserver(function (es) { es.forEach(function (e) { for (var k = 0; k < insts.length; k++) if (insts[k].cv === e.target) insts[k].vis = e.isIntersecting; }); sched(false); }); inst.vis = false; io.observe(inst.cv); } } catch (e) { inst.vis = true; }
    sched(false);
  }
  try {
    doc.addEventListener("visibilitychange", function () { if (!doc.hidden) sched(false); });
    ["pointermove", "deviceorientation"].forEach(function (ev) { window.addEventListener(ev, function () { if (insts.length && !still()) sched(true); }, { passive: true }); });
  } catch (e) {}

  /* stack(el, have, want, label): draws the stack into el; true when a 2D canvas was available */
  function stack(el, have, want) {
    have = Math.min(36, Math.max(0, Math.round(have || 0))); want = Math.min(36, Math.max(have, Math.round(want || 0))); if (!want || !el) return false;
    var inst = make(el, have, want); if (!inst) return false;
    var L = light(); inst.draw(L.x, L.y, -1); inst.lx = L.x; inst.ly = L.y;
    if (!still()) register(inst);
    return true;
  }

  /* upgrade each .sx-bars SVG from SXWorld.goldBars to the canvas, keeping its aria-label; the SVG stays where canvas fails */
  var seen = (typeof WeakSet === "function") ? new WeakSet() : null;
  function upgrade(root) {
    var list = root && root.querySelectorAll ? Array.prototype.slice.call(root.querySelectorAll("svg.sx-bars")) : [];
    if (root && root.matches && root.matches("svg.sx-bars")) list.push(root);
    list.forEach(function (svg) {
      if (seen && seen.has(svg)) return; if (seen) seen.add(svg);
      var have = +svg.getAttribute("data-have"), want = +svg.getAttribute("data-want"); if (!(want > 0) || !svg.parentNode) return;
      var wrap = doc.createElement("span"); wrap.className = "sx-bars sx-ingots"; wrap.setAttribute("role", "img"); wrap.setAttribute("aria-label", svg.getAttribute("aria-label") || "");
      wrap.setAttribute("data-have", have); wrap.setAttribute("data-want", want); wrap.style.cssText = "display:block;max-width:100%;line-height:0";
      if (stack(wrap, have, want)) svg.parentNode.replaceChild(wrap, svg);
    });
  }
  function watch() {
    upgrade(doc.body);
    try { new MutationObserver(function (ms) { ms.forEach(function (m) { for (var k = 0; k < m.addedNodes.length; k++) if (m.addedNodes[k].nodeType === 1) upgrade(m.addedNodes[k]); }); }).observe(doc.body, { childList: true, subtree: true }); } catch (e) {}
  }
  if (doc.body) watch(); else doc.addEventListener("DOMContentLoaded", watch);

  window.SXGold = { stack: stack, shade: shade, lightDir: lightDir, upgrade: upgrade };
})();
