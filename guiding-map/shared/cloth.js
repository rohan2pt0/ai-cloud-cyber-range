/* SecuRAX shared cloth (signature-perfect, natures-design, reuse-first; owner 2026-11-23: "the flag is not realistic"). The
   summit flag's physics and its renderer, ONE engine for every app; shared/world.js draws the flag through it.

   Physics, in real units (metres, seconds, kilograms):
   - a flag 0.9 m x 0.6 m (3:2) of 110 g/m2 spun polyester, as 24 x 16 nodes, each massed by the cloth it stands for;
   - integrated by small-step XPBD (Macklin et al. 2019): 640 substeps a second whatever the frame rate (time is carried
     over between frames), so it is stable at any frame rate and the same physics settles the still frame;
   - stretch is stiff: tensile stiffness 30 kN/m, each row and column made inextensible at once by a tridiagonal solve
     (Goldenthal et al. 2007), plus long-range attachments to the grommets; each row stays within 2% of its length even
     at 50 km/h (a single 4 cm edge can still spike to a few per cent for a frame as the fly snaps);
   - shear is soft (28 N/m per radian); bending uses a rigidity B = 20 uN.m (a light woven polyester), a bending length
     (B / weight)^(1/3) of about 2.6 cm, so the folds are a few centimetres; the fabric's internal friction damps
     node-scale jitter that a 24 x 16 grid would otherwise show;
   - gravity 9.81 m/s2; air density 1.225 kg/m3; on each triangle the aerodynamic force F = 1/2 rho Cd A |vn| vn n, with
     vn the wind relative to the cloth along its normal and Cd = 1.2, plus a skin friction Cf = 0.02 along the cloth;
   - the wind: the person's own speed (km/h to m/s), with gusts as an Ornstein-Uhlenbeck process (20% of the mean,
     correlation time 2 s) carried down the flag at the wind's speed (frozen turbulence), a little cross and vertical
     turbulence, and the pole's wake: a vortex street at the Strouhal frequency f = St U / d (St 0.2, d 3 cm). Its vortices
     pair as they travel down the fly (about four pairings over the flag's 30 pole diameters), so the cloth feels
     f = St U / (16 d): about 4.6 Hz at 40 km/h, 1.7 Hz at 15 km/h, and it rises with the wind as a real flag's flutter does;
   - held by two grommets clipped to the halyard, not a rigid line: the hoist edge between them sways a little;
   - the cloth cannot pass through the pole.
   It hangs limp in still air, lifts partly near 10 km/h and streams out, flapping, at 30 km/h and more.

   Rendering, with real optics (WebGL, ONE context for every flag on the page; the SVG faces stay as the fallback):
   - fabric: Lambert diffuse with the dye's albedo, an Estevez-Kulla ("Charlie") sheen lobe at roughness 0.5 (as the velvet
     in shared/materials.js), and back-lit transmission (thin cloth passes about a quarter of the light, so it glows where
     the sun or the bright sky is behind it); the gold flag is gold-dyed satin, which adds the long lustre of its warp floats
     (a Kajiya-Kay lobe along the thread); the default is off-white polyester;
   - smooth per-vertex normals on a Catmull-Rom refinement of the simulated surface; folds darken by an ambient occlusion
     taken from the surface's curvature; the cloth casts a soft shadow on the pole;
   - a plain weave at thread scale (0.33 mm) and the yarn's unevenness as a procedural normal map, faded out where a pixel
     is larger than a thread; hems along the edges (a double layer that transmits less, with a stitch line), a canvas
     heading at the hoist with two brass grommets; a brushed aluminium pole with its cylindrical highlight, a polished gold
     finial and a halyard;
   - lit by the mountain's own sky (the dusk gradient of the Goals scene) and a low warm sun from the west, the side the
     mountain is lit from; Fresnel from measured F0 (aluminium, brass, gold); ACES tone mapping and the sRGB curve, as
     materials.js does.
   It runs at up to 60 frames a second, only while a flag is on screen and the page is visible. Under reduced motion, in
   tests and in audits, each flag draws one still frame settled by the same physics. Standard browser APIs only. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXCloth) return;
  var doc = document;
  var calm = function () { try { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); } catch (e) { return false; } };
  var jsdom = function () { return /jsdom/i.test(navigator.userAgent || ""); };
  var still = function () { return calm() || !!navigator.webdriver || jsdom(); };

  /* ---------------- the physics, in SI units ---------------- */
  var FW = 0.9, FH = 0.6, NX = 24, NY = 16, N = NX * NY, DX = FW / (NX - 1), DY = FH / (NY - 1);
  var AREAL = 0.11, GRAV = 9.81, RHO = 1.225, CD = 1.2, CF = 0.02;
  var ST = 0.2, POLE_D = 0.03, PAIRS = 16, WAKE_C = 0.5, WAKE_A = 0.18;
  var GUST = 0.2, GUST_TAU = 2.0, TURB = 0.06, TURB_TAU = 0.6;
  var BEND = 2e-5, FRICT = 0.06, TENS = 3e4, SHEAR = 28;
  var H = 1 / 640, POLE_R = POLE_D / 2, HOIST_X = POLE_R + 0.012, SLACK = 0.975, RMIN = POLE_R + 0.004;
  var PIN0 = 0, PIN1 = (NY - 1) * NX, PINS = [[HOIST_X, 0, 0], [HOIST_X, -FH * SLACK, 0]];
  var PHYS = { width: FW, height: FH, cols: NX, rows: NY, areal: AREAL, g: GRAV, rho: RHO, cd: CD, cf: CF, st: ST, poleD: POLE_D, pairs: PAIRS,
    gust: GUST, gustTau: GUST_TAU, bend: BEND, tensile: TENS, shear: SHEAR, substep: H,
    flutterHz: function (kmh) { return ST * (kmh / 3.6) / (PAIRS * POLE_D); }, sheddingHz: function (kmh) { return ST * (kmh / 3.6) / POLE_D; } };

  // the topology, shared by every flag
  var id = function (i, j) { return j * NX + i; };
  var IW = new Float64Array(N), DA = [], DB = [], DL = [], DC = [], BA = [], BM = [], BB = [], BC = [], TR = [], LR0 = new Float64Array(N), LR1 = new Float64Array(N);
  (function () {
    var i, j;
    for (j = 0; j < NY; j++) for (i = 0; i < NX; i++) {
      var ax = (i === 0 || i === NX - 1) ? DX / 2 : DX, ay = (j === 0 || j === NY - 1) ? DY / 2 : DY, m = AREAL * ax * ay * (i === 0 ? 1.6 : 1);   // the heading tape is heavier
      IW[id(i, j)] = 1 / m;
      LR0[id(i, j)] = Math.hypot(i * DX, j * DY); LR1[id(i, j)] = Math.hypot(i * DX, (NY - 1 - j) * DY);
    }
    IW[PIN0] = IW[PIN1] = 0;
    var dist = function (a, b, L, k) { DA.push(a); DB.push(b); DL.push(L); DC.push(1 / k); };
    var dg = Math.hypot(DX, DY), ksh = 2 * SHEAR * DX * DY / (dg * dg);
    // shear first, stretch last: the stiff constraints get the last word in each substep
    for (j = 0; j < NY - 1; j++) for (i = 0; i < NX - 1; i++) { dist(id(i, j), id(i + 1, j + 1), dg, ksh); dist(id(i + 1, j), id(i, j + 1), dg, ksh); }
    PHYS.nShear = DA.length;
    for (j = 0; j < NY; j++) for (i = 0; i < NX - 1; i++) dist(id(i, j), id(i + 1, j), DX, TENS * DY / DX);
    for (j = 0; j < NY - 1; j++) for (i = 0; i < NX; i++) dist(id(i, j), id(i, j + 1), DY, TENS * DX / DY);
    // bending: the second difference along each line of nodes, k = 4 B w / s^3 (stiffer in the heading and the hems)
    var bend = function (a, m, b, k) { BA.push(a); BM.push(m); BB.push(b); BC.push(1 / k); };
    for (j = 0; j < NY; j++) for (i = 1; i < NX - 1; i++) bend(id(i - 1, j), id(i, j), id(i + 1, j), 4 * BEND * DY / (DX * DX * DX) * ((j === 0 || j === NY - 1) ? 4 : 1));
    for (i = 0; i < NX; i++) for (j = 1; j < NY - 1; j++) bend(id(i, j - 1), id(i, j), id(i, j + 1), 4 * BEND * DX / (DY * DY * DY) * (i === 0 ? 30 : i === NX - 1 ? 4 : 1));
    for (j = 0; j < NY - 1; j++) for (i = 0; i < NX - 1; i++) { var k = id(i, j); TR.push(k, k + 1, k + NX, k + 1, k + NX + 1, k + NX); }
  })();
  DA = Int32Array.from(DA); DB = Int32Array.from(DB); DL = Float64Array.from(DL); DC = Float64Array.from(DC);
  BA = Int32Array.from(BA); BM = Int32Array.from(BM); BB = Int32Array.from(BB); BC = Float64Array.from(BC); TR = Int32Array.from(TR);
  var TC = new Int32Array(TR.length / 3), WX = new Float64Array(NX), WZ = new Float64Array(NX);
  for (var tq = 0; tq < TC.length; tq++) TC[tq] = Math.min(TR[3 * tq] % NX, TR[3 * tq + 1] % NX, TR[3 * tq + 2] % NX);
  var NT = TR.length / 3, NS = PHYS.nShear, CH_ROW = DX / (TENS * DY), CH_COL = DY / (TENS * DX);

  // One distance constraint, Gauss-Seidel (XPBD).
  function gsDist(X, n, ih2) {
    var w1 = IW[DA[n]], w2 = IW[DB[n]], dw = w1 + w2; if (!dw) return;
    var p = DA[n] * 3, r = DB[n] * 3, dx = X[r] - X[p], dy = X[r + 1] - X[p + 1], dz = X[r + 2] - X[p + 2], d = Math.sqrt(dx * dx + dy * dy + dz * dz); if (d < 1e-12) return;
    var kk = (d - DL[n]) / ((dw + DC[n] * ih2) * d);
    X[p] += w1 * kk * dx; X[p + 1] += w1 * kk * dy; X[p + 2] += w1 * kk * dz; X[r] -= w2 * kk * dx; X[r + 1] -= w2 * kk * dy; X[r + 2] -= w2 * kk * dz;
  }
  // A whole line of nodes (a row along the fly, or a column down the hoist) made inextensible at once: the linearised
  // distance constraints of the line form a tridiagonal system, solved exactly by the Thomas algorithm (Goldenthal et al.
  // 2007, "fast projection"). Line by line, the tension of a 24-node row reaches the hoist in one pass, not 24.
  var LN = new Float64Array(3 * 24), LC = new Float64Array(24), LA = new Float64Array(24), LB = new Float64Array(24), LL = new Float64Array(24), LW = new Float64Array(25);
  function line(X, start, stride, cnt, rest, at) {
    var m = cnt - 1, k, a, b;
    for (k = 0; k < cnt; k++) LW[k] = IW[start + k * stride];
    for (k = 0; k < m; k++) {
      a = (start + k * stride) * 3; b = a + stride * 3;
      var dx = X[b] - X[a], dy = X[b + 1] - X[a + 1], dz = X[b + 2] - X[a + 2], d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1e-12;
      LN[3 * k] = dx / d; LN[3 * k + 1] = dy / d; LN[3 * k + 2] = dz / d; LC[k] = rest - d;
      LA[k] = LW[k] + LW[k + 1] + at;
    }
    for (k = 0; k < m - 1; k++) LB[k] = -LW[k + 1] * (LN[3 * k] * LN[3 * k + 3] + LN[3 * k + 1] * LN[3 * k + 4] + LN[3 * k + 2] * LN[3 * k + 5]);
    // forward sweep (LA becomes the modified diagonal, LC the modified right-hand side)
    for (k = 1; k < m; k++) { var f = LB[k - 1] / LA[k - 1]; LA[k] -= f * LB[k - 1]; LC[k] -= f * LC[k - 1]; }
    LL[m - 1] = LC[m - 1] / LA[m - 1];
    for (k = m - 2; k >= 0; k--) LL[k] = (LC[k] - LB[k] * LL[k + 1]) / LA[k];
    for (k = 0; k < cnt; k++) {
      var w = LW[k]; if (!w) continue; a = (start + k * stride) * 3;
      var cx = 0, cy = 0, cz = 0;
      if (k < m) { cx -= LN[3 * k] * LL[k]; cy -= LN[3 * k + 1] * LL[k]; cz -= LN[3 * k + 2] * LL[k]; }
      if (k > 0) { cx += LN[3 * k - 3] * LL[k - 1]; cy += LN[3 * k - 2] * LL[k - 1]; cz += LN[3 * k - 1] * LL[k - 1]; }
      X[a] += w * cx; X[a + 1] += w * cy; X[a + 2] += w * cz;
    }
  }
  function rnd(s) { var t = (s.seed = (s.seed + 0x6D2B79F5) | 0); t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
  function gauss(s) { var u = rnd(s) || 1e-9, v = rnd(s); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.283185307 * v); }

  // make(seed, kmh): a new flag, laid out as it would roughly hang in that wind (flat out in a breeze, falling in still air)
  function make(seed, kmh) {
    var th = Math.max(0, Math.min(1, 1 - (+kmh || 0) / 12)) * 1.35, ct = Math.cos(th), sn = Math.sin(th);
    var s = { x: new Float64Array(3 * N), v: new Float64Array(3 * N), q: new Float64Array(3 * N), f: new Float64Array(3 * N),
      t: 0, ph: 0, g: 0, gy: 0, gz: 0, hist: new Float32Array(256), hi: 0, hacc: 0, seed: (seed >>> 0) || 0x5eed };
    for (var j = 0; j < NY; j++) for (var i = 0; i < NX; i++) {
      var k = id(i, j) * 3; s.x[k] = HOIST_X + i * DX * ct; s.x[k + 1] = -j * DY * SLACK - i * DX * sn; s.x[k + 2] = (rnd(s) - 0.5) * 1e-4 * i + (th > 0.5 ? 0.02 * Math.sin(i * 0.7) : 0);
    }
    return s;
  }
  function node(s, i, j) { var k = id(i, j) * 3; return [s.x[k], s.x[k + 1], s.x[k + 2]]; }

  function sub(s, U0, h) {
    s.t += h;
    var a = Math.exp(-h / GUST_TAU), b = Math.exp(-h / TURB_TAU), ra = Math.sqrt(1 - a * a), rb = Math.sqrt(1 - b * b);
    s.g = s.g * a + GUST * ra * gauss(s); s.gy = s.gy * b + TURB * rb * gauss(s); s.gz = s.gz * b + TURB * rb * gauss(s);
    s.hacc += h; if (s.hacc >= 1 / 30) { s.hacc -= 1 / 30; s.hi = (s.hi + 1) & 255; s.hist[s.hi] = s.g; }
    var Ue = Math.max(0, U0 * (1 + s.g)), kw = 2 * Math.PI * ST / (PAIRS * POLE_D * WAKE_C);   // f / c does not depend on U
    s.ph += 2 * Math.PI * ST * Ue / (PAIRS * POLE_D) * h;
    var X = s.x, V = s.v, F = s.f, Q = s.q, i, j, k, n;
    F.fill(0);
    if (U0 > 0) for (i = 0; i < NX - 1; i++) {                                   // per column of cells: the gust that reached it
      var cxr = HOIST_X + (i + 0.5) * DX, lag = Math.min(255, Math.round(cxr / Math.max(U0, 0.05) * 30));   // (frozen turbulence),
      WX[i] = U0 * (1 + s.hist[(s.hi - lag) & 255]); WZ[i] = U0 * (s.gz + WAKE_A * Math.sin(s.ph - kw * cxr));   // and the wake
    }
    if (U0 > 0) for (n = 0; n < NT; n++) {
      var ia = TR[3 * n] * 3, ib = TR[3 * n + 1] * 3, ic = TR[3 * n + 2] * 3;
      var e1x = X[ib] - X[ia], e1y = X[ib + 1] - X[ia + 1], e1z = X[ib + 2] - X[ia + 2], e2x = X[ic] - X[ia], e2y = X[ic + 1] - X[ia + 1], e2z = X[ic + 2] - X[ia + 2];
      var cx = e1y * e2z - e1z * e2y, cy = e1z * e2x - e1x * e2z, cz = e1x * e2y - e1y * e2x, l = Math.sqrt(cx * cx + cy * cy + cz * cz);
      if (l < 1e-12) continue;
      var A = l / 2; cx /= l; cy /= l; cz /= l;
      var col = TC[n], wx = WX[col], wy = U0 * s.gy, wz = WZ[col];               // the wind where this triangle's column is
      var rx = wx - (V[ia] + V[ib] + V[ic]) / 3, ry = wy - (V[ia + 1] + V[ib + 1] + V[ic + 1]) / 3, rz = wz - (V[ia + 2] + V[ib + 2] + V[ic + 2]) / 3;
      var vn = rx * cx + ry * cy + rz * cz, tx = rx - vn * cx, ty = ry - vn * cy, tz = rz - vn * cz, vt = Math.sqrt(tx * tx + ty * ty + tz * tz);
      var fn = 0.5 * RHO * CD * A * Math.abs(vn) * vn / 3, ft = 0.5 * RHO * CF * A * vt / 3;
      var fx = fn * cx + ft * tx, fy = fn * cy + ft * ty, fz = fn * cz + ft * tz;
      F[ia] += fx; F[ia + 1] += fy; F[ia + 2] += fz; F[ib] += fx; F[ib + 1] += fy; F[ib + 2] += fz; F[ic] += fx; F[ic + 1] += fy; F[ic + 2] += fz;
    }
    for (i = 0; i < N; i++) {
      k = 3 * i; Q[k] = X[k]; Q[k + 1] = X[k + 1]; Q[k + 2] = X[k + 2];
      var w = IW[i]; if (!w) continue;
      V[k] += h * F[k] * w; V[k + 1] += h * (F[k + 1] * w - GRAV); V[k + 2] += h * F[k + 2] * w;
      X[k] += h * V[k]; X[k + 1] += h * V[k + 1]; X[k + 2] += h * V[k + 2];
    }
    var ih2 = 1 / (h * h);
    for (n = 0; n < BA.length; n++) {                                             // bending
      var a3 = BA[n] * 3, m3 = BM[n] * 3, b3 = BB[n] * 3, wa = IW[BA[n]], wm = IW[BM[n]], wb = IW[BB[n]];
      var den = wm + 0.25 * wa + 0.25 * wb + BC[n] * ih2; if (den <= 0) continue;
      for (var c = 0; c < 3; c++) { var C = X[m3 + c] - 0.5 * (X[a3 + c] + X[b3 + c]), dl = -C / den; X[m3 + c] += wm * dl; X[a3 + c] -= 0.5 * wa * dl; X[b3 + c] -= 0.5 * wb * dl; }
    }
    for (i = 0; i < N; i++) {                                                     // the pole is solid
      k = 3 * i; var pr = Math.sqrt(X[k] * X[k] + X[k + 2] * X[k + 2]);
      if (IW[i] && pr < RMIN) { if (pr < 1e-9) { X[k] = RMIN; } else { X[k] *= RMIN / pr; X[k + 2] *= RMIN / pr; } }
    }
    for (n = 0; n < NS; n++) gsDist(X, n, ih2);                                  // shear, Gauss-Seidel
    for (j = 0; j < NY; j++) line(X, j * NX, 1, NX, DX, CH_ROW * ih2);            // stretch: each row along the fly exactly,
    for (i = 1; i < NX; i++) line(X, i, NX, NY, DY, CH_COL * ih2);                // each column down the hoist, and the hoist edge
    line(X, 0, NX, NY, DY, CH_COL * ih2 + 0.05 * IW[NX]);                         // (held at both grommets: a touch of give keeps it solvable),
    for (n = NS; n < DA.length; n++) gsDist(X, n, ih2);                           // then one smoothing pass over every edge
    for (i = 0; i < N; i++) {
      if (!IW[i]) continue; k = 3 * i;
      for (var g = 0; g < 2; g++) {                                               // long-range attachment to each grommet
        var P = PINS[g], L = g ? LR1[i] : LR0[i], qx = X[k] - P[0], qy = X[k + 1] - P[1], qz = X[k + 2] - P[2], ql = Math.sqrt(qx * qx + qy * qy + qz * qz);
        if (ql > L) { var f2 = L / ql; X[k] = P[0] + qx * f2; X[k + 1] = P[1] + qy * f2; X[k + 2] = P[2] + qz * f2; }
      }
    }
    var dmp = 1 - 0.05 * h;
    for (i = 0; i < 3 * N; i++) V[i] = (X[i] - Q[i]) / h * dmp;
    for (n = NS; n < DA.length; n++) {                                            // the fabric's internal friction: neighbours
      var ea = DA[n] * 3, eb = DB[n] * 3, wA = IW[DA[n]], wB = IW[DB[n]], ws = wA + wB; if (!ws) continue;   // shed their
      for (var d3 = 0; d3 < 3; d3++) { var dv = (V[eb + d3] - V[ea + d3]) * FRICT; V[ea + d3] += dv * wA / ws; V[eb + d3] -= dv * wB / ws; }  // relative motion
    }
    X[PIN0 * 3] = PINS[0][0]; X[PIN0 * 3 + 1] = PINS[0][1]; X[PIN0 * 3 + 2] = PINS[0][2];
    X[PIN1 * 3] = PINS[1][0]; X[PIN1 * 3 + 1] = PINS[1][1]; X[PIN1 * 3 + 2] = PINS[1][2];
  }
  // step(s, kmh, dt): advance dt seconds in a wind of kmh along +x, in fixed small substeps (any frame rate, same physics)
  function step(s, kmh, dt) {
    if (!(dt > 0)) return s;
    var U0 = Math.max(0, Math.min(120, +kmh || 0)) / 3.6;
    s.acc = Math.min((s.acc || 0) + dt, 0.1);                                     // a long pause is not caught up in one go
    while (s.acc >= H * 0.999) { sub(s, U0, H); s.acc -= H; }
    return s;
  }
  function strain(s) {                                                            // the worst stretch of any structural edge
    var m = 0; for (var n = NS; n < DA.length; n++) { var p = DA[n] * 3, r = DB[n] * 3, d = Math.hypot(s.x[r] - s.x[p], s.x[r + 1] - s.x[p + 1], s.x[r + 2] - s.x[p + 2]); m = Math.max(m, (d - DL[n]) / DL[n]); }
    return m;
  }
  var POSE = {};
  function settled(kmh) {        // a still pose from the same physics, cached by wind speed (reduced motion, tests, first paint)
    var key = Math.round(Math.max(0, +kmh || 0) / 2); if (POSE[key]) return POSE[key];
    var s = make(7, key * 2); for (var n = 0; n < 90; n++) step(s, key * 2, 1 / 60);
    return (POSE[key] = s);
  }
  function copy(dst, src) { dst.x.set(src.x); dst.v.set(src.v); dst.q.set(src.q); dst.t = src.t; dst.acc = src.acc; dst.ph = src.ph; dst.g = src.g; dst.gy = src.gy; dst.gz = src.gz; dst.hist.set(src.hist); dst.hi = src.hi; return dst; }

  /* ---------------- the SVG fallback: shaded faces on every other node ---------------- */
  var SCI = [], SRJ = [], i0;
  for (i0 = 0; i0 < NX; i0 += 2) SCI.push(i0); if (SCI[SCI.length - 1] !== NX - 1) SCI.push(NX - 1);
  for (i0 = 0; i0 < NY; i0 += 2) SRJ.push(i0); if (SRJ[SRJ.length - 1] !== NY - 1) SRJ.push(NY - 1);
  var UNIT = 30 / FW;                                                             // SVG cloth units per metre (the flag is 30 units long)
  var LS = (function () { var x = -0.6, y = 0.35, z = 0.7, l = Math.hypot(x, y, z); return [x / l, y / l, z / l]; })();
  function shade(base, lum) { return "rgb(" + base.map(function (v) { return Math.max(0, Math.min(255, Math.round(v * lum))); }).join(",") + ")"; }
  function svgFaces(s, gold) {
    var out = [], base = gold ? [226, 186, 98] : [236, 230, 216], back = gold ? [184, 142, 64] : [205, 198, 182];
    var pr = function (q) { return (q[0] * UNIT).toFixed(2) + "," + ((-q[1] + q[2] * 0.3) * UNIT).toFixed(2); };
    for (var b = 0; b < SRJ.length - 1; b++) for (var a = 0; a < SCI.length - 1; a++) {
      var A = node(s, SCI[a], SRJ[b]), B = node(s, SCI[a + 1], SRJ[b]), C = node(s, SCI[a + 1], SRJ[b + 1]), D = node(s, SCI[a], SRJ[b + 1]);
      var ux = C[0] - A[0], uy = C[1] - A[1], uz = C[2] - A[2], vx = D[0] - B[0], vy = D[1] - B[1], vz = D[2] - B[2];
      var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, nl = Math.hypot(nx, ny, nz) || 1;
      var facing = nz / nl, dot = (nx * LS[0] + ny * LS[1] + nz * LS[2]) / nl;
      out.push({ pts: pr(A) + " " + pr(B) + " " + pr(C) + " " + pr(D), fill: shade(facing >= 0 ? base : back, Math.min(1.25, 0.34 + 0.8 * Math.abs(dot) + (facing > 0 ? 0.06 : -0.06))) });
    }
    return out;
  }

  /* ---------------- the renderer: WebGL, one context for every flag ---------------- */
  var gl = null, glc = null, prog = null, U = {}, ok = null, LOC = {};
  var VS = [
    "attribute vec3 aP;attribute vec3 aN;attribute vec3 aT;attribute vec3 aX;",
    "uniform mat3 uV;uniform vec4 uO;varying vec3 vP;varying vec3 vN;varying vec3 vT;varying vec3 vX;",
    "void main(){vP=aP;vN=aN;vT=aT;vX=aX;vec3 q=uV*aP;gl_Position=vec4((q.x-uO.x)/uO.z,(q.y-uO.y)/uO.w,-q.z/3.,1.);}"
  ].join("\n");
  var FS = [
    "precision highp float;",
    "uniform int uM;uniform vec3 uE;uniform vec3 uL;uniform vec3 uSun;uniform vec3 uAlb;uniform vec3 uShc;uniform float uSat;uniform float uTr;",
    "uniform float uMpp;uniform float uExp;uniform vec2 uFlag;uniform vec3 uHo[32];",
    "varying vec3 vP;varying vec3 vN;varying vec3 vT;varying vec3 vX;",
    "#define PI 3.14159265",
    "float hash(vec2 p){p=fract(mod(p,289.)*vec2(.1031,.1030)*13.7);p+=dot(p,p+45.32);return fract(p.x*p.y);}",
    "float vnoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}",
    // The mountain's sky, as radiance: the Goals scene's own dusk gradient (zenith, mid sky, a warm horizon), the dark rock
    // below, and the glow of the low sun along the horizon on its side.
    "vec3 sky(vec3 d){float y=d.y;vec3 Z=vec3(.011,.042,.125),M=vec3(.11,.21,.38),Hz=vec3(.81,.58,.33),Gr=vec3(.020,.023,.028);",
    " vec3 c=mix(mix(Hz*.45,Gr,smoothstep(0.,-.3,y)),mix(mix(Hz,M,smoothstep(0.,.32,y)),Z,smoothstep(.32,1.,y)),smoothstep(-.05,.05,y));",
    " vec2 h=normalize(d.xz+1e-5),l=normalize(uL.xz);c+=Hz*.9*pow(max(dot(h,l),0.),6.)*exp(-abs(y)*5.);",
    " c+=uSun*.9*smoothstep(.9992,.99995,dot(d,uL));return c;}",
    // Irradiance from the dome around a normal (a five-tap cosine estimate), divided by pi: a Lambert surface of albedo a
    // under it shows a * irr(n).
    "vec3 irr(vec3 n){vec3 t=normalize(cross(n,abs(n.y)<.9?vec3(0,1,0):vec3(1,0,0))),b=cross(n,t);",
    " return .36*sky(n)+.16*(sky(normalize(n+t*.9))+sky(normalize(n-t*.9))+sky(normalize(n+b*.9))+sky(normalize(n-b*.9)));}",
    "vec3 tm(vec3 x){x=clamp(x*(2.51*x+.03)/(x*(2.43*x+.59)+.14),0.,1.);return pow(x,vec3(1./2.2));}",
    "float ggx(float nh,float a){float a2=a*a;float d=nh*nh*(a2-1.)+1.;return a2/(PI*d*d);}",
    // A metal: Schlick's Fresnel from the measured F0, the blurred sky in the mirror direction, and the sun as a GGX lobe.
    "vec3 metal(vec3 N,vec3 V,vec3 F0,float ro,float sh){float nv=max(dot(N,V),1e-3);vec3 R=reflect(-V,N);vec3 F=F0+(1.-F0)*pow(1.-nv,5.);",
    " vec3 e=mix(sky(R),irr(R),clamp(ro*2.5,0.,1.));vec3 H=normalize(uL+V);float nl=max(dot(N,uL),0.);float a=max(ro*ro,.003);float k=a*.5;",
    " float vis=1./(4.*(nv*(1.-k)+k)*(nl*(1.-k)+k));vec3 Fs=F0+(1.-F0)*pow(1.-max(dot(V,H),0.),5.);",
    " return F*e*mix(1.,sh,.5)+Fs*ggx(max(dot(N,H),0.),a)*vis*nl*uSun*sh;}",
    "float line(float x,float c,float hw,float m){return clamp((hw+.5*m-abs(x-c))/m,0.,1.)*min(1.,2.*hw/m);}",
    "void main(){vec3 V=normalize(uE);vec3 N=normalize(vN);vec3 c;float m=max(uMpp,1e-5);",
    " if(uM==0){",
    "  float sd=dot(N,V)>=0.?1.:-1.;N*=sd;vec2 uv=vX.xy;vec3 T=normalize(vT-N*dot(vT,N));vec3 B=cross(N,T);",
    "  vec3 alb=uAlb;float tr=uTr;float ao=1.;",
    "  float head=1.-smoothstep(.034-m*.5,.034+m*.5,uv.x);alb=mix(alb,vec3(.80,.77,.69),head);tr=mix(tr,.06,head);",   // the canvas heading
    "  float e=min(min(uv.y,uFlag.y-uv.y),uFlag.x-uv.x);float hem=(1.-smoothstep(.012-m*.5,.012+m*.5,e))*(1.-head);",   // the hems
    "  tr*=mix(1.,.45,hem);ao*=mix(1.,.93,hem);ao*=1.-.4*(line(e,.009,.0004,m)*(1.-head)+line(uv.x,.031,.0004,m));",
    "  float f1=clamp(1.-m/.00033,0.,1.),f2=clamp(1.-m/.0015,0.,1.);vec2 w=uv/.00033*6.2832;",                            // threads, yarn
    "  vec2 g=f1*.22*vec2(cos(w.x)*sin(w.y),sin(w.x)*cos(w.y))+f2*.025*(vec2(vnoise(uv*vec2(300.,900.)),vnoise(uv*vec2(900.,300.)+7.))-.5);",
    "  N=normalize(N+T*g.x+B*g.y);alb*=1.+f2*.05*(vnoise(uv*vec2(240.,700.))-.5);",
    "  float NL=dot(N,uL),NV=max(dot(N,V),1e-3),nl=max(NL,0.);float cv=vX.z*sd;",
    "  float aoF=1.-clamp(cv*.005,0.,.4),aoB=1.-clamp(-cv*.005,0.,.4);",
    "  vec3 tint=uAlb/max(max(uAlb.r,uAlb.g),uAlb.b);",
    "  c=(1.-tr)*alb*(uSun/PI*nl+irr(N))*aoF*ao+tr*tint*tint*(uSun/PI*max(-NL,0.)+irr(-N))*aoB*ao;",
    "  vec3 H=normalize(uL+V);float NH=dot(N,H);float sh=sqrt(max(1.-NH*NH,0.));float D=4.*sh*sh/(2.*PI);",              // Charlie, r=.5
    "  float vis=1./(4.*(nl+NV-nl*NV)+1e-3);c+=uShc*D*vis*nl*uSun*ao+uShc*irr(N)*.6*pow(1.-NV,3.)*ao*aoF;",
    "  if(uSat>0.){float th=dot(T,H);c+=uSat*mix(vec3(1.),alb,.55)*pow(sqrt(max(1.-th*th,0.)),14.)*nl*uSun*.10*ao*aoF;}",  // satin warp lustre
    "  for(int k=0;k<2;k++){vec2 gc=vec2(.017,k==0?.018:uFlag.y-.018);vec2 q=uv-gc;float d=length(q);",                    // brass grommets
    "   if(d<.0085){if(d<.0042&&m<.004)discard;float s=clamp((d-.0064)/.0022,-1.,1.);vec2 rd=q/max(d,1e-5);",
    "    vec3 Nr=normalize(N*sqrt(max(1.-s*s,.05))+(T*rd.x-B*rd.y)*s);c=mix(c,metal(Nr,V,vec3(.910,.778,.423),.22,1.),smoothstep(.0085,.0085-m,d));}}",
    " }else if(uM==1){",
    "  float occ=0.;for(int i=0;i<32;i++){vec3 q=uHo[i]-vP;float t=dot(q,uL);if(t>0.){float d=length(q-uL*t);occ+=smoothstep(.045,.008,d)*.3;}}",
    "  float sh=1.-.85*clamp(occ,0.,1.);vec3 Nb=normalize(N+vec3(0.,(vnoise(vec2(atan(N.z,N.x)*90.,vP.y*3.))-.5)*.03,0.));",
    "  c=metal(Nb,V,vec3(.913,.922,.924),.30,sh);",                                                                          // brushed aluminium
    " }else if(uM==2){c=metal(N,V,vec3(.944,.776,.373),.16,1.);",                                                            // polished gold
    " }else{float br=.88+.12*sin(vX.x*2200.+atan(N.z,N.x)*2.)*clamp(1.-m/.002,0.,1.);float nl=max(dot(N,uL),0.);",           // the halyard
    "  c=vec3(.74,.73,.70)*br*(uSun/PI*nl+irr(N));}",
    " gl_FragColor=vec4(tm(c*uExp),1.);}"
  ].join("\n");

  function glInit() {
    if (ok !== null) return ok;
    ok = false;
    try {
      if (jsdom() || doc.documentElement.hasAttribute("data-sx-cloth-off")) return ok;
      glc = doc.createElement("canvas"); glc.width = glc.height = 256;
      gl = glc.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: true, depth: true, preserveDrawingBuffer: false });
      if (!gl) return ok;
      var hp = gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
      if (!hp || hp.precision < 16) return ok;
      var sh = function (t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
      prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
      gl.useProgram(prog);
      ["aP", "aN", "aT", "aX"].forEach(function (n) { LOC[n] = gl.getAttribLocation(prog, n); gl.enableVertexAttribArray(LOC[n]); });
      ["uV", "uO", "uM", "uE", "uL", "uSun", "uAlb", "uShc", "uSat", "uTr", "uMpp", "uExp", "uFlag", "uHo"].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });
      gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL);
      glc.addEventListener("webglcontextlost", function (e) { e.preventDefault(); ok = false; fallBack(); });
      ok = true;
    } catch (e) { ok = false; if (window.console && console.warn) console.warn("SXCloth: the flag falls back to SVG", e && e.message); }
    return ok;
  }

  // The scene's light: a low, warm sun from the west (the side the mountain is lit from), a little in front of the flag.
  var SUN = (function () { var x = -0.86, y = 0.32, z = 0.28, l = Math.hypot(x, y, z); return [x / l, y / l, z / l]; })();
  var SUNC = [1.0 * 3.0, 0.74 * 3.0, 0.50 * 3.0], EXPOSE = 1.25;
  var YAW = 0.22, PITCH = 0.12;
  var VIEW = (function () {   // world to view: yaw about y, then pitch about x (column-major for GL)
    var cy = Math.cos(YAW), sy = Math.sin(YAW), cp = Math.cos(PITCH), sp = Math.sin(PITCH);
    var R = [[cy, 0, sy], [sp * sy, cp, -sp * cy], [-cp * sy, sp, cp * cy]];   // rows
    return { m: new Float32Array([R[0][0], R[1][0], R[2][0], R[0][1], R[1][1], R[2][1], R[0][2], R[1][2], R[2][2]]), eye: [R[2][0], R[2][1], R[2][2]], R: R };
  })();
  var FABRIC = {
    gold: { alb: [0.55, 0.32, 0.045], sheen: [0.90, 0.62, 0.22], sat: 1, tr: 0.22 },       // gold-dyed satin
    white: { alb: [0.86, 0.83, 0.75], sheen: [0.55, 0.55, 0.52], sat: 0, tr: 0.28 }        // off-white spun polyester
  };

  // Catmull-Rom refinement weights for R sub-steps per cell along a line of n nodes
  var REF = {};
  function refine(n, R) {
    var key = n + "x" + R; if (REF[key]) return REF[key];
    var m = (n - 1) * R + 1, I = new Int32Array(4 * m), W = new Float64Array(4 * m);
    for (var a = 0; a < m; a++) {
      var i = Math.min(Math.floor(a / R), n - 2), t = a / R - i, t2 = t * t, t3 = t2 * t;
      var w = [-0.5 * t3 + t2 - 0.5 * t, 1.5 * t3 - 2.5 * t2 + 1, -1.5 * t3 + 2 * t2 + 0.5 * t, 0.5 * t3 - 0.5 * t2];
      for (var q = 0; q < 4; q++) { I[4 * a + q] = Math.max(0, Math.min(n - 1, i - 1 + q)); W[4 * a + q] = w[q]; }
    }
    return (REF[key] = { m: m, I: I, W: W });
  }
  var GRIDIDX = {};
  function gridIndex(mx, my) {
    var key = mx + "x" + my; if (GRIDIDX[key]) return GRIDIDX[key];
    var out = [];
    for (var j = 0; j < my - 1; j++) for (var i = 0; i < mx - 1; i++) { var k = j * mx + i; out.push(k, k + 1, k + mx, k + 1, k + mx + 1, k + mx); }
    return (GRIDIDX[key] = out);
  }
  // a cylinder along y (radius r, from y0 down to y1, at x, z) and a sphere, in world metres; 12 floats a vertex
  function cylinder(V, I, x, z, r, y0, y1, seg) {
    var base = V.length / 12;
    for (var k = 0; k <= seg; k++) { var a = k / seg * 2 * Math.PI, nx = Math.cos(a), nz = Math.sin(a);
      V.push(x + r * nx, y0, z + r * nz, nx, 0, nz, 0, 1, 0, 0, 0, 0, x + r * nx, y1, z + r * nz, nx, 0, nz, 0, 1, 0, y0 - y1, 0, 0); }
    for (k = 0; k < seg; k++) { var b = base + 2 * k; I.push(b, b + 1, b + 2, b + 1, b + 3, b + 2); }
  }
  function sphere(V, I, cx, cy, cz, r, seg) {
    var base = V.length / 12, rows = seg / 2;
    for (var j = 0; j <= rows; j++) for (var k = 0; k <= seg; k++) {
      var th = j / rows * Math.PI, ph = k / seg * 2 * Math.PI, nx = Math.sin(th) * Math.cos(ph), ny = Math.cos(th), nz = Math.sin(th) * Math.sin(ph);
      V.push(cx + r * nx, cy + r * ny, cz + r * nz, nx, ny, nz, 0, 1, 0, 0, 0, 0);
    }
    for (j = 0; j < rows; j++) for (k = 0; k < seg; k++) { var a = base + j * (seg + 1) + k; I.push(a, a + seg + 1, a + 1, a + 1, a + seg + 1, a + seg + 2); }
  }

  var SVGNS = ["http", "//www.w3.org/2000/svg"].join(":");   // the SVG namespace name, not a network address
  var MAXPX = 1600, recs = [], seen = typeof WeakMap === "function" ? new WeakMap() : null, styled = false, stats = { sim: 0, draw: 0, n: 0 };
  function num(el, k, d) { var v = parseFloat(el.getAttribute(k)); return isFinite(v) ? v : d; }
  function upgrade(el) {
    if (!seen || seen.has(el) || !el.isConnected) return seen && seen.get(el);
    var rec = { el: el, x: num(el, "data-sx-x", 0), y: num(el, "data-sx-y", 0), h: num(el, "data-sx-h", 18), sc: num(el, "data-sx-sc", 0.55),
      sign: num(el, "data-sx-sign", 1) < 0 ? -1 : 1, gold: el.getAttribute("data-sx-gold") === "1", kmh: num(el, "data-sx-kmh", 8), vis: true };
    rec.S = 30 * rec.sc / FW;                                                     // SVG units per metre
    rec.sim = copy(make(1 + recs.length * 7919), settled(rec.kmh)); rec.sim.seed = 1 + recs.length * 7919;
    seen.set(el, rec);
    if (glInit()) {
      if (!styled) { styled = true; var st = doc.createElement("style"); st.textContent = ".sx-flag-gl>:not(foreignObject){visibility:hidden}.sx-flag-gl>foreignObject{overflow:visible}"; doc.head.appendChild(st); }
      var yTop = 0.6 / rec.S, yBot = -(rec.h - 0.6) / rec.S;
      rec.reg = rec.sign > 0 ? [-0.16, 1.0] : [-1.0, 0.16]; rec.reg.push(yBot - 0.03, yTop + 0.12); rec.yTop = yTop; rec.yBot = yBot;
      var fo = doc.createElementNS(SVGNS, "foreignObject");
      fo.setAttribute("x", (rec.x + rec.reg[0] * rec.S).toFixed(3)); fo.setAttribute("y", (rec.y + 0.6 - rec.reg[3] * rec.S).toFixed(3));
      fo.setAttribute("width", ((rec.reg[1] - rec.reg[0]) * rec.S).toFixed(3)); fo.setAttribute("height", ((rec.reg[3] - rec.reg[2]) * rec.S).toFixed(3));
      fo.setAttribute("aria-hidden", "true"); fo.setAttribute("class", "sx-flag-fo");
      var cv = doc.createElement("canvas"); cv.style.cssText = "display:block;width:100%;height:100%;pointer-events:none";
      fo.appendChild(cv); el.appendChild(fo);
      rec.fo = fo; rec.cv = cv; rec.cx = cv.getContext("2d");
      if (rec.cx && draw(rec)) el.classList.add("sx-flag-gl");
    }
    recs.push(rec);
    if (io) io.observe(el);
    return rec;
  }
  function fallBack() { recs.forEach(function (r) { r.el.classList.remove("sx-flag-gl"); }); }
  function layout(rec) {
    var r = rec.fo.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false;
    var q = Math.max(2, window.devicePixelRatio || 1), W = Math.round(r.width * q), Hh = Math.round(r.height * q), f = Math.min(1, MAXPX / Math.max(W, Hh));
    W = Math.max(8, Math.round(W * f)); Hh = Math.max(8, Math.round(Hh * f));
    if (rec.W === W && rec.H === Hh) return true;
    rec.W = W; rec.H = Hh; rec.cv.width = W; rec.cv.height = Hh;
    var mpp = (rec.reg[1] - rec.reg[0]) / W; rec.mpp = mpp;
    var flagPx = FW / mpp, R = flagPx < 120 ? 1 : flagPx < 360 ? 2 : flagPx < 800 ? 3 : 4;
    rec.R = R; rec.ru = refine(NX, R); rec.rv = refine(NY, R);
    var mx = rec.ru.m, my = rec.rv.m, idx = gridIndex(mx, my).slice(), V = [], I = [];
    rec.nCloth = idx.length; rec.nv = mx * my;
    var pr = Math.max(POLE_R, 0.75 * mpp), fr = Math.max(0.03, 2.2 * mpp);
    // the pole, the finial and the halyard, after the cloth's vertices
    for (var k = 0; k < rec.nv * 12; k++) V.push(0);
    var i0 = I.length; cylinder(V, I, 0, 0, pr, rec.yTop, rec.yBot, 20); rec.pole = [i0, I.length - i0];
    i0 = I.length; sphere(V, I, 0, rec.yTop + fr * 0.85, 0, fr, 20); rec.fin = [i0, I.length - i0];
    i0 = I.length; if (mpp < 0.004) { var hr = 0.003, hx = rec.sign * (POLE_R + 0.009); cylinder(V, I, hx, 0, hr, rec.yTop, rec.yBot, 8); } rec.hal = [i0, I.length - i0];
    rec.V = new Float32Array(V); var all = idx.concat(I);
    if (!rec.vbo) { rec.vbo = gl.createBuffer(); rec.ibo = gl.createBuffer(); }
    gl.bindBuffer(gl.ARRAY_BUFFER, rec.vbo); gl.bufferData(gl.ARRAY_BUFFER, rec.V, gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, rec.ibo); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(all), gl.STATIC_DRAW);
    // the static uv of the cloth
    for (var b = 0; b < my; b++) for (var a = 0; a < mx; a++) { var o = (b * mx + a) * 12; rec.V[o + 9] = a * DX / R; rec.V[o + 10] = b * DY / R; }
    rec.tmp = new Float64Array(mx * NY * 3); rec.P = new Float64Array(mx * my * 3);
    return true;
  }
  function fill(rec) {           // refine the simulated surface, then smooth normals, the warp tangent and the curvature
    var s = rec.sim, X = s.x, ru = rec.ru, rv = rec.rv, mx = ru.m, my = rv.m, T = rec.tmp, P = rec.P, V = rec.V, sg = rec.sign, a, b, q, c, o;
    for (b = 0; b < NY; b++) for (a = 0; a < mx; a++) for (c = 0; c < 3; c++) { var acc = 0; for (q = 0; q < 4; q++) acc += ru.W[4 * a + q] * X[(b * NX + ru.I[4 * a + q]) * 3 + c]; T[(b * mx + a) * 3 + c] = acc; }
    for (b = 0; b < my; b++) for (a = 0; a < mx; a++) for (c = 0; c < 3; c++) { var ac2 = 0; for (q = 0; q < 4; q++) ac2 += rv.W[4 * b + q] * T[(rv.I[4 * b + q] * mx + a) * 3 + c]; P[(b * mx + a) * 3 + c] = ac2; }
    var hu = DX / rec.R, hv = DY / rec.R, h2 = hu * hu + hv * hv;
    for (b = 0; b < my; b++) for (a = 0; a < mx; a++) {
      var k = (b * mx + a) * 3, al = a > 0 ? k - 3 : k, ar = a < mx - 1 ? k + 3 : k, bu = b > 0 ? k - 3 * mx : k, bd = b < my - 1 ? k + 3 * mx : k;
      var ux = P[ar] - P[al], uy = P[ar + 1] - P[al + 1], uz = P[ar + 2] - P[al + 2], vx = P[bd] - P[bu], vy = P[bd + 1] - P[bu + 1], vz = P[bd + 2] - P[bu + 2];
      var nx = vy * uz - vz * uy, ny = vz * ux - vx * uz, nz = vx * uy - vy * ux, nl = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1; nx /= nl; ny /= nl; nz /= nl;
      var tl = Math.sqrt(ux * ux + uy * uy + uz * uz) || 1, cu = 0;
      if (a > 0 && a < mx - 1 && b > 0 && b < my - 1) cu = 8 * (((P[al] + P[ar] + P[bu] + P[bd]) / 4 - P[k]) * nx + ((P[al + 1] + P[ar + 1] + P[bu + 1] + P[bd + 1]) / 4 - P[k + 1]) * ny + ((P[al + 2] + P[ar + 2] + P[bu + 2] + P[bd + 2]) / 4 - P[k + 2]) * nz) / h2;
      o = (b * mx + a) * 12;
      V[o] = sg * P[k]; V[o + 1] = P[k + 1]; V[o + 2] = P[k + 2]; V[o + 3] = sg * nx; V[o + 4] = ny; V[o + 5] = nz;
      V[o + 6] = sg * ux / tl; V[o + 7] = uy / tl; V[o + 8] = uz / tl; V[o + 11] = cu;
    }
  }
  var HO = new Float32Array(96);
  function draw(rec) {
    if (!ok || !rec.cx || !layout(rec)) return false;
    var t0 = performance.now(), W = rec.W, Hh = rec.H;
    if (glc.width < W || glc.height < Hh) { glc.width = Math.max(glc.width, W); glc.height = Math.max(glc.height, Hh); }
    fill(rec);
    for (var j = 0; j < NY; j++) for (var i = 0; i < 2; i++) { var k = (j * NX + i) * 3, o = (j * 2 + i) * 3; HO[o] = rec.sign * rec.sim.x[k]; HO[o + 1] = rec.sim.x[k + 1]; HO[o + 2] = rec.sim.x[k + 2]; }
    gl.viewport(0, 0, W, Hh); gl.clearColor(0, 0, 0, 0); gl.clearDepth(1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.bindBuffer(gl.ARRAY_BUFFER, rec.vbo); gl.bufferSubData(gl.ARRAY_BUFFER, 0, rec.V.subarray(0, rec.nv * 12));
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, rec.ibo);
    gl.vertexAttribPointer(LOC.aP, 3, gl.FLOAT, false, 48, 0); gl.vertexAttribPointer(LOC.aN, 3, gl.FLOAT, false, 48, 12);
    gl.vertexAttribPointer(LOC.aT, 3, gl.FLOAT, false, 48, 24); gl.vertexAttribPointer(LOC.aX, 3, gl.FLOAT, false, 48, 36);
    var r = rec.reg, fab = rec.gold ? FABRIC.gold : FABRIC.white;
    gl.uniformMatrix3fv(U.uV, false, VIEW.m);
    gl.uniform4f(U.uO, (r[0] + r[1]) / 2, (r[2] + r[3]) / 2, (r[1] - r[0]) / 2, (r[3] - r[2]) / 2);
    gl.uniform3fv(U.uE, VIEW.eye); gl.uniform3fv(U.uL, SUN); gl.uniform3fv(U.uSun, SUNC);
    gl.uniform3fv(U.uAlb, fab.alb); gl.uniform3fv(U.uShc, fab.sheen); gl.uniform1f(U.uSat, fab.sat); gl.uniform1f(U.uTr, fab.tr);
    gl.uniform1f(U.uMpp, rec.mpp); gl.uniform1f(U.uExp, EXPOSE); gl.uniform2f(U.uFlag, FW, FH); gl.uniform3fv(U.uHo, HO);
    var part = function (mode, rg, o) { if (!rg[1]) return; gl.uniform1i(U.uM, mode); gl.drawElements(gl.TRIANGLES, rg[1], gl.UNSIGNED_SHORT, (rg[0] + o) * 2); };
    part(1, rec.pole, rec.nCloth); part(2, rec.fin, rec.nCloth); part(3, rec.hal, rec.nCloth); part(0, [0, rec.nCloth], 0);
    rec.cx.clearRect(0, 0, W, Hh);
    rec.cx.drawImage(glc, 0, glc.height - Hh, W, Hh, 0, 0, W, Hh);
    stats.draw = stats.draw * 0.9 + (performance.now() - t0) * 0.1;
    return true;
  }
  function svgUpdate(rec) {
    var g = rec.el.querySelector(".sx-cloth"); if (!g) return;
    var f = svgFaces(rec.sim, rec.gold), polys = g.children;
    for (var k = 0; k < f.length && k < polys.length; k++) { polys[k].setAttribute("points", f[k].pts); polys[k].setAttribute("fill", f[k].fill); polys[k].setAttribute("stroke", f[k].fill); }
  }

  /* ---------------- the one loop for every flag on the page ---------------- */
  var running = false, last = 0, io = null, windFn = null, budget = 16;
  function prune() { recs = recs.filter(function (r) { if (r.el.isConnected) return true; if (io) io.unobserve(r.el); if (gl && r.vbo) { gl.deleteBuffer(r.vbo); gl.deleteBuffer(r.ibo); } return false; }); }
  function scan() {
    if (!seen || jsdom()) return;
    prune();
    var els = doc.querySelectorAll(".sx-flag[data-sx-x]"); for (var i = 0; i < els.length; i++) upgrade(els[i]);
    if (!still()) start();
  }
  function start() {
    if (running || still() || !seen || typeof requestAnimationFrame !== "function") return;
    if (!doc.querySelector(".sx-flag")) return;
    running = true; last = 0; requestAnimationFrame(tick);
  }
  function tick(now) {
    if (still()) { running = false; return; }
    prune();
    var els = doc.querySelectorAll(".sx-flag[data-sx-x]");
    if (!els.length) { running = false; return; }
    requestAnimationFrame(tick);
    if (doc.hidden || (last && now - last < budget)) return;
    var dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60; last = now;
    var w = windFn ? windFn() : null, kmh = w ? w.speed : 8, t0 = performance.now(), n = 0;
    for (var i = 0; i < els.length; i++) {
      var rec = upgrade(els[i]); if (!rec || (io && !rec.vis)) continue;
      var t1 = performance.now(); step(rec.sim, kmh, dt); stats.sim = stats.sim * 0.9 + (performance.now() - t1) * 0.1;
      if (!(rec.el.classList.contains("sx-flag-gl") && draw(rec))) svgUpdate(rec);
      n++;
    }
    var ms = performance.now() - t0; stats.frame = (stats.frame || ms) * 0.9 + ms * 0.1; stats.n = n;
    budget = stats.frame > 6 ? 30 : 14;                                           // 60 frames a second, 30 on a slow device
  }
  try { if (typeof IntersectionObserver === "function" && seen) io = new IntersectionObserver(function (es) { es.forEach(function (e) { var r = seen.get(e.target); if (r) r.vis = e.isIntersecting; }); if (!running) start(); }); } catch (e) { io = null; }
  try { doc.addEventListener("visibilitychange", function () { if (!doc.hidden) start(); }); } catch (e) {}
  try { window.addEventListener("resize", function () { recs.forEach(function (r) { if (r.fo) { r.W = 0; draw(r); } }); }); } catch (e) {}

  window.SXCloth = {
    PHYS: PHYS, make: make, step: step, node: node, strain: strain, settled: settled, svgFaces: svgFaces,
    cols: NX, rows: NY, svgCols: SCI.length, svgRows: SRJ.length, unit: UNIT,
    scan: function () { setTimeout(scan, 0); }, start: start, ready: function () { return glInit(); }, stats: stats,
    setWind: function (f) { windFn = f; },
    // advance(dt): move every flag on the page dt seconds and draw it once (an audit's or a test's frame-by-frame look)
    advance: function (dt) { var w = windFn ? windFn() : null; scan(); recs.forEach(function (r) { step(r.sim, w ? w.speed : 8, dt); if (!(r.el.classList.contains("sx-flag-gl") && draw(r))) svgUpdate(r); }); }
  };
})();
