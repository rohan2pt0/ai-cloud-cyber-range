/* SecuRAX shared world (reuse-first, immersive-real, natures-design; owner 2026-11-23). The real-world objects every app
   draws its numbers with: ONE engine here, any screen in any app uses it, never a private copy.

   Each object carries a fixed meaning (CATALOG), so a person learns it once and reads it everywhere:
     moon       time coming near: waxes as a date approaches, full on the day, a red ring when late
     goldBars   wealth held against an aim: one ingot per unit, outlined ghosts up to the aim
     vessel     a buffer that lasts: water in glass, the level is how long it lasts, the etched line the aim
     treeRings  a habit's history: one ring per period, a ring's width is how well that period went
     flag       a goal reached: real cloth on a pole, moved by the person's own wind
   Use one object per card, for its meaning only; the number it shows is always also given in words (screen readers, and
   anyone who prefers words). The canvas sky and lit metals live in sky.js and materials.js; this file holds the light ones
   (SVG, no WebGL) so they are safe on any phone.

   The flag is real cloth in real units, simulated and lit by shared/cloth.js (SXCloth): a 0.9 x 0.6 m polyester flag on
   two grommets, in the person's own wind with gusts and the pole's wake, rendered in WebGL with a fabric BRDF, sheen and
   back-lit translucency, under the mountain's own sky. This file keeps the API and the SVG fallback markup. Wind comes
   from SXWorld.windSource (the app sets it), else a soft default breeze. Standard browser APIs only. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXWorld) return;
  var uid = function (p) { return p + Math.random().toString(36).slice(2, 8); };

  var CATALOG = [
    { id: "moon", means: "a date coming near", use: "events, renewals, birthdays, deadlines", avoid: "amounts" },
    { id: "goldBars", means: "wealth held against an aim", use: "net worth, a corpus, savings against a benchmark", avoid: "spending, debts" },
    { id: "vessel", means: "a buffer and how long it lasts", use: "emergency fund, runway, cover in months", avoid: "growth over time" },
    { id: "treeRings", means: "a habit's history, period by period", use: "saving rate by month, streaks, years of practice", avoid: "a single number" },
    { id: "flag", means: "a goal reached, flying in your own wind", use: "a goal or key result at 100%, a summit", avoid: "warnings, progress below the goal" }
  ];

  /* ---- the moon: f = how full (0..1); late draws a red ring ---- */
  function moon(daysAway, horizon) {
    var n = daysAway, f = n <= 0 ? 1 : Math.max(0.08, 1 - n / (horizon || 14)), r = 14, id = uid("sxm");
    return '<svg width="38" height="38" viewBox="0 0 38 38" aria-hidden="true" class="gm-moon sx-moon"><defs><clipPath id="' + id + '"><circle cx="19" cy="19" r="' + r + '"/></clipPath>'
      + '<radialGradient id="' + id + 'f" cx=".38" cy=".35" r=".75"><stop offset="0" stop-color="#fbf7ea"/><stop offset=".6" stop-color="#e7e0cc"/><stop offset="1" stop-color="#b9b19c"/></radialGradient>'
      + '<radialGradient id="' + id + 'h" r=".5"><stop offset=".7" stop-color="#f6efd2" stop-opacity=".55"/><stop offset="1" stop-color="#f6efd2" stop-opacity="0"/></radialGradient>'
      + '<filter id="' + id + 'b" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.1"/></filter></defs>'
      + (f > 0.95 ? '<circle cx="19" cy="19" r="' + (r + 5) + '" fill="url(#' + id + 'h)"/>' : '')
      + '<g clip-path="url(#' + id + ')"><circle cx="19" cy="19" r="' + r + '" fill="url(#' + id + 'f)"/>'
      + '<circle cx="14" cy="14" r="4" fill="#9c9583" opacity=".35"/><circle cx="23" cy="21" r="3.2" fill="#9c9583" opacity=".3"/><circle cx="15.5" cy="24" r="2.2" fill="#8d8673" opacity=".35"/>'
      + '<circle cx="24" cy="12.5" r="1.4" fill="#8d8673" opacity=".45"/><circle cx="11" cy="20" r="1.1" fill="#8d8673" opacity=".45"/>'
      + '<circle cx="' + (19 + 2 * r * f) + '" cy="19" r="' + (r + 0.5) + '" fill="#0d1a2e" fill-opacity=".9" filter="url(#' + id + 'b)"/></g>'
      + '<circle cx="19" cy="19" r="' + (r + 1.5) + '" fill="none" stroke="' + (n < 0 ? "#c0392b" : "rgba(160,150,120,.35)") + '" stroke-width="' + (n < 0 ? 2.5 : 1) + '"/></svg>';
  }

  /* ---- gold bars: have solid ingots, want - have outlined ghosts, in a pyramid; label names one bar ---- */
  function goldBars(have, want, label) {
    have = Math.min(36, Math.max(0, Math.round(have || 0))); want = Math.min(36, Math.max(have, Math.round(want || 0))); if (!want) return "";   // the pyramid holds 36
    var per = 4; while (per < 8 && per * (per + 1) / 2 < want) per++;
    var bw = 42, bh = 16, dx = 6, dy = 7, rows = 0, cap = 0; while (cap < want && rows < per) { cap += per - rows; rows++; }
    var W = per * (bw + 4) + 12, H = rows * (bh + dy) + 20, id = uid("sxg"), g = "";
    var bar = function (i, ghost) {
      var r = 0, c = i; while (c >= per - r) { c -= per - r; r++; }
      var x = 6 + r * (bw + 4) / 2 + c * (bw + 4), y = H - 10 - (r + 1) * (bh + dy) + dy;
      var front = 'M' + x + ' ' + (y + dy) + ' h' + bw + ' v' + bh + ' h-' + bw + ' Z', top = 'M' + x + ' ' + (y + dy) + ' l' + dx + ' -' + dy + ' h' + (bw - 2 * dx) + ' l' + dx + ' ' + dy + ' Z';
      if (ghost) return '<path d="' + front + '" fill="none" stroke="#c9a84c" stroke-opacity=".55" stroke-dasharray="3 3"/><path d="' + top + '" fill="none" stroke="#c9a84c" stroke-opacity=".4" stroke-dasharray="3 3"/>';
      return '<path d="' + front + '" fill="url(#' + id + 'f)" stroke="#8f6619" stroke-width=".8"/><path d="' + top + '" fill="url(#' + id + 't)" stroke="#a87c22" stroke-width=".6"/>'
        + '<path d="M' + (x + 3) + ' ' + (y + dy + 3) + ' h' + (bw - 6) + '" stroke="#fff6dc" stroke-opacity=".7" stroke-width="1"/>';
    };
    for (var i = 0; i < want; i++) g += bar(i, i >= have);
    return '<svg class="sx-bars" data-have="' + have + '" data-want="' + want + '" data-label="' + String(label || "").replace(/[<>&"]/g, "") + '" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + have + ' gold bars of ' + (label || "one unit") + ', ' + (want - have) + ' more to the aim">'
      + '<defs><linearGradient id="' + id + 'f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff1c4"/><stop offset=".22" stop-color="#e9c873"/><stop offset=".5" stop-color="#b88a2e"/><stop offset=".62" stop-color="#a97c25"/><stop offset=".85" stop-color="#e0bb66"/><stop offset="1" stop-color="#c9a04a"/></linearGradient>'
      + '<linearGradient id="' + id + 't" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f3dc9a"/><stop offset=".45" stop-color="#fff6dc"/><stop offset="1" stop-color="#d9b25a"/></linearGradient></defs>'
      + '<ellipse cx="' + (W / 2) + '" cy="' + (H - 6) + '" rx="' + (W / 2 - 4) + '" ry="4" fill="#000" opacity=".15"/>' + g + '</svg>';
  }

  /* ---- water in a glass vessel: f = level 0..1, state good|watch|low, aim = label at the etched line ---- */
  function vessel(f, state, aim, label) {
    f = Math.max(0.04, Math.min(1, f || 0));
    var id = uid("sxv"), W = 150, H = 170, top = 26, bot = 156, lvl = bot - (bot - top - 6) * f, al = top + 6;
    var water = state === "good" ? ["#5fd3c0", "#127a75", "#0a4a52"] : state === "watch" ? ["#9fd6c6", "#3e8f7a", "#5a5a2a"] : ["#c9a98a", "#8a5a3c", "#5a3020"];
    var q = function (t) { return String(t == null ? "" : t).replace(/[<>&"]/g, ""); };
    // A wrapper SXWater upgrades to a living canvas where a 2D context exists; the SVG inside stays as the fallback.
    return '<span class="sx-water" data-f="' + f.toFixed(3) + '" data-state="' + q(state) + '" data-aim="' + q(aim) + '" role="img" aria-label="' + q(label) + '" style="display:inline-block;position:relative;flex:none;width:' + W + 'px;height:' + H + 'px;line-height:0;vertical-align:top">'
      + '<svg class="sx-vessel" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + (label || "") + '">'
      + '<defs><clipPath id="' + id + 'c"><path d="M30 22 Q30 16 36 16 H114 Q120 16 120 22 V150 Q120 160 110 160 H40 Q30 160 30 150 Z"/></clipPath>'
      + '<linearGradient id="' + id + 'w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + water[0] + '" stop-opacity=".95"/><stop offset=".45" stop-color="' + water[1] + '"/><stop offset="1" stop-color="' + water[2] + '"/></linearGradient>'
      + '<linearGradient id="' + id + 'g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".12" stop-color="#fff" stop-opacity=".08"/><stop offset=".8" stop-color="#fff" stop-opacity="0"/><stop offset=".93" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity=".05"/></linearGradient>'
      + '<radialGradient id="' + id + 'k" cx=".5" cy=".2" r=".8"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>'
      + '<ellipse cx="75" cy="163" rx="50" ry="5" fill="#000" opacity=".18"/>'
      + '<g clip-path="url(#' + id + 'c)"><rect x="0" y="0" width="' + W + '" height="' + H + '" fill="rgba(200,225,235,.10)"/>'
      + '<g class="gm-wave"><path d="M-60 ' + lvl + ' q15 -5 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 V170 H-60 Z" fill="url(#' + id + 'w)"/>'
      + '<path d="M-60 ' + lvl + ' q15 -5 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="1.2"/></g>'
      + '<rect x="30" y="' + lvl + '" width="90" height="' + (170 - lvl) + '" fill="url(#' + id + 'k)"/></g>'
      + '<line x1="30" y1="' + al + '" x2="120" y2="' + al + '" stroke="#c9a84c" stroke-width="1.5" stroke-dasharray="4 3"/>'
      + '<text x="124" y="' + (al + 4) + '" font-size="10" fill="currentColor" opacity=".75">' + String(aim || "").replace(/[<>&"]/g, "") + '</text>'
      + '<path d="M30 22 Q30 16 36 16 H114 Q120 16 120 22 V150 Q120 160 110 160 H40 Q30 160 30 150 Z" fill="url(#' + id + 'g)" stroke="rgba(170,190,200,.85)" stroke-width="2"/>'
      + '<path d="M38 26 V140" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round"/>'
      + '<ellipse cx="75" cy="16" rx="45" ry="3.5" fill="none" stroke="rgba(170,190,200,.9)" stroke-width="1.5"/></svg></span>';
  }

  /* ---- tree rings: rates = one number per period (0..60 counts), oldest first; the last ring is edged in gold ---- */
  function treeRings(rates, label) {
    var rings = (rates || []).map(function (r) { return Math.max(0, Math.min(60, +r || 0)); }); if (!rings.length) rings = [0];
    var id = uid("sxt"), cx = 80, cy = 80, rad = 6, paths = "";
    var wob = function (r, k) { var pts = []; for (var a = 0; a < 360; a += 12) { var t = a * Math.PI / 180, rr = r + Math.sin(t * 3 + k) * 0.9 + Math.cos(t * 5 + k * 1.7) * 0.6; pts.push((cx + rr * Math.cos(t)).toFixed(1) + " " + (cy + rr * Math.sin(t)).toFixed(1)); } return "M" + pts.join(" L") + " Z"; };
    var scale = 62 / Math.max(rings.reduce(function (a, x) { return a + 1 + x / 3; }, 0), 30);
    rings.forEach(function (x, i) {
      rad += (1 + x / 3) * scale;   // a lean period is a hairline, a strong one a broad band
      var last = i === rings.length - 1;
      paths = '<path d="' + wob(rad, i) + '" fill="' + (i % 2 ? "#d9b98a" : "#e6caa0") + '" stroke="' + (last ? "#c9a84c" : "#9a6f42") + '" stroke-width="' + (last ? 2.2 : 0.9) + '" stroke-opacity="' + (last ? 1 : 0.7) + '"/>' + paths;
    });
    var bark = '<path d="' + wob(rad + 7, 9) + '" fill="#5a3a22"/><path d="' + wob(rad + 3.5, 4) + '" fill="#7a5130"/>';
    var crack = '<path d="M' + cx + ' ' + cy + ' L' + (cx + rad * 0.85) + ' ' + (cy - rad * 0.35) + '" stroke="#8a5d36" stroke-opacity=".35" stroke-width="1"/>';
    return '<svg class="sx-rings" width="160" height="160" viewBox="0 0 160 160" role="img" aria-label="' + (label || "") + '">'
      + '<defs><radialGradient id="' + id + '" cx=".45" cy=".42" r=".7"><stop offset="0" stop-color="#fff" stop-opacity=".25"/><stop offset="1" stop-color="#000" stop-opacity=".12"/></radialGradient></defs>'
      + '<ellipse cx="80" cy="150" rx="62" ry="6" fill="#000" opacity=".14"/>' + bark + paths
      + '<circle cx="' + cx + '" cy="' + cy + '" r="3" fill="#8a5d36"/>' + crack + '<circle cx="' + cx + '" cy="' + cy + '" r="' + (rad + 7) + '" fill="url(#' + id + ')"/></svg>';
  }

  /* ---- the flag: cloth in the person's own wind. Physics and rendering live in shared/cloth.js (SXCloth) ---- */
  function wind() {
    var w = null; try { w = SXWorld.windSource ? SXWorld.windSource() : null; } catch (e) { w = null; }
    var sp = w && isFinite(+w.speed) ? Math.max(0, Math.min(120, +w.speed)) : 8, dir = w && isFinite(+w.dir) ? +w.dir : 270;
    return { speed: sp, from: dir, sign: (dir > 0 && dir < 180) ? -1 : 1 };
  }
  var C = window.SXCloth;
  if (C) C.setWind(wind);
  /* flag(x, y, opts): a pole of height h at (x, y) in the caller's SVG, the cloth flying downwind (mirrored for a wind from the
     east). opts: gold, h (pole height, default 18), scale (cloth size, default 0.55: the 0.9 m flag is 30 x scale units long).
     The markup is the fallback (shaded SVG faces settled by the real physics); where WebGL works, shared/cloth.js renders the
     same cloth with real optics over it, and moves it in the shared loop when motion is welcome. */
  function flag(x, y, o) {
    o = o || {}; var w = wind(), h = o.h || 18, sc = o.scale || 0.55, gold = !!o.gold;
    var faces = C ? C.svgFaces(C.settled(w.speed), gold).map(function (f) { return '<polygon points="' + f.pts + '" fill="' + f.fill + '" stroke="' + f.fill + '"/>'; }).join("") : "";
    if (C) C.scan();
    return '<g class="sx-flag" data-sx-x="' + x + '" data-sx-y="' + y + '" data-sx-h="' + h + '" data-sx-sc="' + sc + '" data-sx-sign="' + w.sign + '" data-sx-gold="' + (gold ? 1 : 0) + '" data-sx-kmh="' + w.speed.toFixed(1) + '">'
      + '<line x1="' + x + '" y1="' + (y + h) + '" x2="' + x + '" y2="' + y + '" stroke="#e9e2d3" stroke-width="1.2" stroke-linecap="round"/>'
      + '<circle cx="' + x + '" cy="' + (y - 0.9) + '" r="1.3" fill="#f3d991" stroke="#a87c22" stroke-width=".4"/>'
      + '<g transform="translate(' + x + ' ' + (y + 0.6) + ') scale(' + (w.sign * sc) + ' ' + sc + ')">'
      + '<g class="sx-cloth" data-gold="' + (gold ? 1 : 0) + '" data-kmh="' + w.speed.toFixed(0) + '" stroke-linejoin="round" stroke-width=".35">' + faces + '</g>'
      + '<rect x="0.3" y="-0.2" width="1.2" height="19.9" rx=".5" fill="#d8d0bd"/></g></g>';
  }

  window.SXWorld = { CATALOG: CATALOG, moon: moon, goldBars: goldBars, vessel: vessel, treeRings: treeRings, flag: flag,
    cloth: C || null, windSource: null, start: function () { if (C) C.start(); } };
})();
