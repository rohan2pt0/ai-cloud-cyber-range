/* SecuRAX shared touch and light (reuse-first, owner 2026-11-14: "real world physics and motion"). Two small things that
   make a screen feel like an object in the hand:
   - a ripple of light that spreads from the finger on any button or key (the press and its spring-back are CSS in lux.css);
   - the light on polished metal follows the device: tilt the phone (or move the pointer on a laptop) and the horizon in
     gold and platinum, and the highlight on the seal, move with it. A damped spring smooths the motion, as a real
     reflection would move, and it settles back to rest when the hand is still.
   Writes only two CSS variables on <html> (--sx-tx, --sx-ty, each -1..1). No permission is asked: where a browser wants
   one for motion (iOS), the pointer still works and nothing nags. Reduced motion, an automated browser or a hidden page:
   no ripple and no light motion. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXTouch) return;
  var doc = document, root = doc.documentElement;
  var calm = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  var auto = !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
  window.SXTouch = { on: !calm && !auto };
  if (calm || auto) return;

  // Ripple: in a clip layer of its own, so the button's overflow and focus ring are never touched.
  doc.addEventListener("pointerdown", function (ev) {
    var b = ev.target && ev.target.closest && ev.target.closest("button,.sx-key,[role=button]");
    if (!b || b.disabled || b.hasAttribute("data-no-ripple")) return;
    try {
      var cs = getComputedStyle(b);
      if (cs.position === "static") b.style.position = "relative";
      var clip = doc.createElement("span"); clip.className = "sx-ripple-clip"; clip.setAttribute("aria-hidden", "true");
      var r = b.getBoundingClientRect(), d = Math.hypot(r.width, r.height) * 2;
      var w = doc.createElement("span"); w.className = "sx-ripple";
      w.style.cssText = "width:" + d + "px;height:" + d + "px;left:" + (ev.clientX - r.left - d / 2) + "px;top:" + (ev.clientY - r.top - d / 2) + "px";
      clip.appendChild(w); b.appendChild(clip);
      setTimeout(function () { if (clip.parentNode) clip.parentNode.removeChild(clip); }, 700);
    } catch (e) {}
  }, { passive: true });

  // Light: a target from the tilt or the pointer, followed by a critically damped spring.
  var tx = 0, ty = 0, x = 0, y = 0, vx = 0, vy = 0, raf = 0, last = 0, idle = 0;
  function aim(nx, ny) { tx = Math.max(-1, Math.min(1, nx)); ty = Math.max(-1, Math.min(1, ny)); idle = 0; if (!raf && !doc.hidden) raf = requestAnimationFrame(step); }
  function step(t) {
    var dt = last ? Math.min(.05, (t - last) / 1000) : .016; last = t;
    var k = 60, c = 2 * Math.sqrt(k);              // stiffness and critical damping: no wobble, no lag
    vx += (k * (tx - x) - c * vx) * dt; vy += (k * (ty - y) - c * vy) * dt; x += vx * dt; y += vy * dt;
    root.style.setProperty("--sx-tx", x.toFixed(3)); root.style.setProperty("--sx-ty", y.toFixed(3));
    idle += dt;
    if (idle > 4 && (tx || ty)) { tx = 0; ty = 0; }   // the hand is still: the light drifts home
    if (Math.abs(tx - x) + Math.abs(ty - y) + Math.abs(vx) + Math.abs(vy) > .002) raf = requestAnimationFrame(step);
    else { raf = 0; last = 0; }
  }
  var base = null;
  window.addEventListener("deviceorientation", function (e) {
    if (e.beta == null || e.gamma == null) return;
    if (!base) base = { b: e.beta, g: e.gamma };     // the way the phone is held now is "level"
    base.b += (e.beta - base.b) * .01; base.g += (e.gamma - base.g) * .01;   // and it slowly follows a new grip
    aim((e.gamma - base.g) / 25, (e.beta - base.b) / 25);
  }, { passive: true });
  window.addEventListener("pointermove", function (e) {
    if (e.pointerType !== "mouse") return;
    aim(e.clientX / (window.innerWidth || 1) * 2 - 1, e.clientY / (window.innerHeight || 1) * 2 - 1);
  }, { passive: true });
  doc.addEventListener("visibilitychange", function () { if (doc.hidden && raf) { cancelAnimationFrame(raf); raf = 0; last = 0; } });
})();
