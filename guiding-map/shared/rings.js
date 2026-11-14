/* SecuRAX shared rings (a signature feature; principles signature-perfect and natures-design, owner 2026-11-14).
   Three rings a person closes every day, made of light and nature rather than flat lines:
   - each ring is a glowing tube of light in an engraved groove, coloured along its length by a natural palette:
     sunrise (dawn rose, coral, amber, the sun itself at the head), emerald (light deepening through the stone) and
     peacock (a feather's eye: sapphire, teal, bronze-green, gold), whose colours slide as the phone tilts, as a real
     feather's do (structural colour from thin-film interference);
   - the arc fills on a critically damped spring from where it last stood, never from zero on every redraw; a bright sun
     rides its leading tip and a slow pulse of light flows along it;
   - at zero a seed of light marks where to begin; closing a ring ignites it (a wave of light runs once round); closing
     all three brings a soft sunrise bloom behind them: a reward the eye can feel, never a sound or a nag.
   The SVG underneath stays: it carries the screen-reader label and is the look wherever a canvas cannot run.
   Reduced motion, an automated browser or a hidden page get one still, finished frame and no timer.
   Use: any svg.gm-rings (or [data-sx-rings]) with data-rings='[{"n":"Today","p":33,"k":"sunrise"},…]' is drawn by itself. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXRings) return;
  var doc = document, TAU = Math.PI * 2, last = {}, live = [], raf = 0, prev = 0, wake = 0;
  var calm = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  var still = calm || !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
  var PAL = {
    sunrise: ["#b0346a", "#e2475a", "#f2734a", "#f59e3b", "#fbc94a", "#fff1bf"],
    emerald: ["#064e3b", "#056b4f", "#0b8f63", "#15b47b", "#45d49a", "#c6f6dd"],
    peacock: ["#1e3a8a", "#1d4ed8", "#0e7490", "#0f9f8a", "#7e9a3a", "#d4af37", "#f3dc8f"]
  };
  function hex(h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; }
  var RGB = {}; Object.keys(PAL).forEach(function (k) { RGB[k] = PAL[k].map(hex); });
  function col(k, t, shift) {                              // the palette at t (0..1); shift slides it (iridescence)
    var p = RGB[k], x = Math.max(0, Math.min(1, t + (shift || 0))) * (p.length - 1), i = Math.min(p.length - 2, Math.floor(x)), f = x - i;
    return [p[i][0] + (p[i + 1][0] - p[i][0]) * f, p[i][1] + (p[i + 1][1] - p[i][1]) * f, p[i][2] + (p[i + 1][2] - p[i][2]) * f];
  }
  function rgba(c, a) { return "rgba(" + (c[0] | 0) + "," + (c[1] | 0) + "," + (c[2] | 0) + "," + a.toFixed(3) + ")"; }
  function tilt() { var v = parseFloat(getComputedStyle(doc.documentElement).getPropertyValue("--sx-tx")); return isNaN(v) ? 0 : v; }

  function mount(svg) {
    if (svg._sxRings) return;
    var data; try { data = JSON.parse(svg.getAttribute("data-rings") || "[]"); } catch (e) { return; }
    if (!data.length) return;
    var cv = doc.createElement("canvas"), ctx = cv.getContext && cv.getContext("2d");
    if (!ctx) return;
    // The drawing and its light share one small box, so the light moves with the drawing whatever the layout does
    // later (test campaign: a late font reflow left the light 38 px below the drawing it replaced).
    var parent = svg.parentNode; if (!parent) return;
    var box = doc.createElement("span"); box.className = "sx-rings-box";
    box.style.cssText = "position:relative;display:inline-block;line-height:0;flex:none;vertical-align:middle";
    parent.insertBefore(box, svg); box.appendChild(svg);
    cv.className = "sx-rings-cv"; cv.setAttribute("aria-hidden", "true");
    box.appendChild(cv);
    var st = { svg: svg, cv: cv, ctx: ctx, rings: data.map(function (r, i) {
      var from = last[r.n] !== undefined ? last[r.n] : 0;
      return { n: r.n, k: r.k || "sunrise", to: Math.max(0, Math.min(100, +r.p || 0)), v: from, vel: 0, ign: from < 100 && r.p >= 100 ? 0 : -1, i: i };
    }), t0: 0 };
    st.rings.forEach(function (r) { last[r.n] = r.to; });
    svg._sxRings = st; svg.classList.add("sx-rings-on");
    live.push(st); layout(st); draw(st, 0);
    if (!still) kick();
  }
  function layout(st) {
    var b = st.svg.getBoundingClientRect(), pad = Math.round(b.width * .18), d = Math.min(3, window.devicePixelRatio || 1);
    st.w = b.width; st.pad = pad; st.d = d;
    st.cv.style.cssText = "position:absolute;pointer-events:none;width:" + (b.width + 2 * pad) + "px;height:" + (b.height + 2 * pad) + "px;left:" + (-pad) + "px;top:" + (-pad) + "px";
    st.cv.width = Math.round((b.width + 2 * pad) * d); st.cv.height = Math.round((b.height + 2 * pad) * d);
  }
  function draw(st, t) {
    var c = st.ctx, d = st.d, W = st.cv.width / d, cx = W / 2, cy = W / 2, s = st.w / 68, dark = doc.documentElement.getAttribute("data-theme") === "dark" || (doc.documentElement.getAttribute("data-theme") !== "light" && window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches);
    c.setTransform(d, 0, 0, d, 0, 0); c.clearRect(0, 0, W, W);
    var radii = [28, 20.5, 13], lw = 5.6 * s, shift = tilt() * .12, all = st.rings.every(function (r) { return r.v >= 99.5; });
    if (all) {                                             // three closed: a soft sunrise behind them, breathing
      var br = .5 + .5 * Math.sin(t / 1600), g = c.createRadialGradient(cx, cy, 0, cx, cy, 40 * s);
      g.addColorStop(0, "rgba(255,196,120," + (.22 + .1 * br).toFixed(3) + ")"); g.addColorStop(1, "rgba(255,160,90,0)");
      c.fillStyle = g; c.beginPath(); c.arc(cx, cy, 40 * s, 0, TAU); c.fill();
    }
    st.rings.forEach(function (r, i) {
      var R = radii[i] * s, k = r.k, sh = k === "peacock" ? shift : 0, frac = Math.max(0, Math.min(1, r.v / 100)), a0 = -Math.PI / 2, a1 = a0 + frac * TAU;
      // The groove: an engraved channel, its lower wall catching the light.
      c.lineCap = "butt"; c.lineWidth = lw + 1.4 * s;
      c.strokeStyle = dark ? "rgba(0,0,0,.42)" : "rgba(11,31,53,.07)"; c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.stroke();
      c.lineWidth = .9 * s; c.strokeStyle = dark ? "rgba(255,255,255,.09)" : "rgba(255,255,255,.85)";
      c.beginPath(); c.arc(cx, cy, R + lw / 2 + .2 * s, Math.PI * .15, Math.PI * .85); c.stroke();
      c.strokeStyle = dark ? "rgba(255,255,255,.05)" : "rgba(11,31,53,.08)";
      c.beginPath(); c.arc(cx, cy, R - lw / 2 - .2 * s, Math.PI * 1.15, Math.PI * 1.85); c.stroke();
      if (frac <= 0.004) {                                 // a seed of light where the ring begins
        var p = .5 + .5 * Math.sin(t / 700 + i), sc = col(k, .5, sh), gx = cx, gy = cy - R, sg = c.createRadialGradient(gx, gy, 0, gx, gy, lw * 1.3);
        sg.addColorStop(0, rgba([255, 250, 235], .75 + .2 * p)); sg.addColorStop(.35, rgba(sc, .55)); sg.addColorStop(1, rgba(sc, 0));
        c.fillStyle = sg; c.beginPath(); c.arc(gx, gy, lw * 1.3, 0, TAU); c.fill();
        return;
      }
      // The light: a tube coloured along its length (the palette spans the whole circle, so progress IS the sunrise).
      var n = Math.max(2, Math.ceil(frac * 140));
      if (r.v >= 99.5) { c.shadowColor = rgba(col(k, .7, sh), .7); c.shadowBlur = lw * 1.6; }
      c.lineWidth = lw; c.lineCap = "butt";
      for (var j = 0; j < n; j++) {
        var u0 = j / n * frac, u1 = (j + 1) / n * frac + .002;
        c.strokeStyle = rgba(col(k, (u0 + u1) / 2, sh), 1); c.beginPath(); c.arc(cx, cy, R, a0 + u0 * TAU, a0 + u1 * TAU); c.stroke();
      }
      c.shadowBlur = 0;
      [[a0, 0], [a1, frac]].forEach(function (e) {           // round ends, each in its own colour
        c.fillStyle = rgba(col(k, e[1], sh), 1); c.beginPath(); c.arc(cx + Math.cos(e[0]) * R, cy + Math.sin(e[0]) * R, lw / 2, 0, TAU); c.fill();
      });
      // A glass sheen along the inner, lit side of the tube.
      c.lineWidth = lw * .26; c.strokeStyle = "rgba(255,255,255,.30)"; c.beginPath(); c.arc(cx, cy, R - lw * .16, a0, a1); c.stroke();
      // A pulse of light flowing along the arc.
      if (!still) {
        var fl = ((t / 5200 + i * .23) % 1) * frac, fa = a0 + fl * TAU, fx = cx + Math.cos(fa) * R, fy = cy + Math.sin(fa) * R, fg = c.createRadialGradient(fx, fy, 0, fx, fy, lw * 1.4);
        fg.addColorStop(0, "rgba(255,255,255,.42)"); fg.addColorStop(1, "rgba(255,255,255,0)"); c.fillStyle = fg; c.beginPath(); c.arc(fx, fy, lw * 1.4, 0, TAU); c.fill();
      }
      // The sun at the leading tip.
      var hc = col(k, frac, sh), hx = cx + Math.cos(a1) * R, hy = cy + Math.sin(a1) * R, pul = still ? .8 : .75 + .25 * Math.sin(t / 900 + i * 2);
      var hg = c.createRadialGradient(hx, hy, 0, hx, hy, lw * 1.5);
      hg.addColorStop(0, rgba([255, 252, 240], .95 * pul)); hg.addColorStop(.32, rgba(hc, .7 * pul)); hg.addColorStop(1, rgba(hc, 0));
      c.fillStyle = hg; c.beginPath(); c.arc(hx, hy, lw * 1.5, 0, TAU); c.fill();
      // Ignition: the moment a ring closes, a wave of light runs once round it.
      if (r.ign >= 0 && r.ign < 1) {
        var ia = a0 + r.ign * TAU, ig = c.createRadialGradient(cx + Math.cos(ia) * R, cy + Math.sin(ia) * R, 0, cx + Math.cos(ia) * R, cy + Math.sin(ia) * R, lw * 2.6);
        ig.addColorStop(0, "rgba(255,255,245,.85)"); ig.addColorStop(1, "rgba(255,255,245,0)"); c.fillStyle = ig;
        c.beginPath(); c.arc(cx + Math.cos(ia) * R, cy + Math.sin(ia) * R, lw * 2.6, 0, TAU); c.fill();
      }
    });
  }
  function step(t) {
    raf = 0;
    var dt = prev ? Math.min(.05, (t - prev) / 1000) : .016; prev = t;
    live = live.filter(function (st) { return st.svg.isConnected; });
    if (!live.length || doc.hidden) { prev = 0; return; }
    var settled = true;
    live.forEach(function (st) {
      st.rings.forEach(function (r) {
        var k = 90, c = 2 * Math.sqrt(k) * .82;             // a spring, just under critical: a whisper of overshoot
        r.vel += (k * (r.to - r.v) - c * r.vel) * dt; r.v += r.vel * dt;
        if (r.ign >= 0 && r.v >= 99.5) r.ign = Math.min(1.01, r.ign + dt / .9);
        if (Math.abs(r.to - r.v) > .05 || Math.abs(r.vel) > .05 || (r.ign >= 0 && r.ign < 1)) settled = false;
      });
      if (st.vis !== false) draw(st, t);
    });
    // Calm: alive while the person is engaged, then a still, finished frame (no motion that never ends, no battery spent).
    if (settled && t - wake > 20000) { prev = 0; live.forEach(function (st) { draw(st, t); }); return; }
    raf = requestAnimationFrame(function (tt) { if (tt - t < 30) { raf = requestAnimationFrame(step); } else step(tt); });
  }
  function kick() { wake = performance.now(); if (!raf && !still) raf = requestAnimationFrame(step); }
  function finish(st) { st.rings.forEach(function (r) { r.v = r.to; r.ign = -1; }); draw(st, 0); }
  function scan() {
    doc.querySelectorAll("svg.gm-rings[data-rings], [data-sx-rings][data-rings]").forEach(function (svg) {
      mount(svg); if (still && svg._sxRings) finish(svg._sxRings);
    });
  }
  window.SXRings = { scan: scan, palettes: PAL };
  if (/jsdom/i.test(navigator.userAgent || "")) return;
  function boot() {
    scan();
    if (window.MutationObserver) new MutationObserver(function () { if (!boot.q) boot.q = requestAnimationFrame(function () { boot.q = 0; scan(); }); }).observe(doc.body, { childList: true, subtree: true });
    doc.addEventListener("visibilitychange", function () { if (!doc.hidden) kick(); });
    doc.addEventListener("pointerdown", kick, { passive: true });
    window.addEventListener("resize", function () { live.forEach(function (st) { layout(st); draw(st, performance.now()); }); });
  }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", boot); else setTimeout(boot, 0);
})();
