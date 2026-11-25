/* The product site's one script, shared by every storefront page (website-v2: home, personal, nbfc, assess). A separate file, because the site's policy allows scripts from itself only
   (website/_headers: script-src 'self'), so an inline script would never run on the hosted site.
   1. Copy the install sentence (only where the page has one).
   2. A link to something folded away (Products, Readiness) opens its fold first, so it never lands on nothing.
   3. The hero's night sky and gold seal: the shared engines (guiding-map/shared/sky.js for the sky, materials.js to light the
      seal and the gold call with real optics, touch.js so the light follows the pointer or the phone), copied in by
      website/build.sh, loaded only after the page has loaded, drawn only while on screen. The stars drift a little slower than
      the page (a damped spring), never under reduced motion. Reduced motion, a hidden tab or an automated browser get one still
      frame (each engine decides). Without the files, the hero keeps its plain night colour and the CSS seal.
   4. One material per card, for its meaning (shared/world.js CATALOG): gold bars, water in glass and the breathing sea, each
      drawn by its own engine only when its card comes near the screen. The number is always in words beside it. */
(function () {
  "use strict";

  // 1. copy the install sentence
  var button = document.getElementById("copy-install"), prompt = document.getElementById("install-prompt");
  if (button && prompt) {
    button.addEventListener("click", function () {
      var text = prompt.value;
      function done() { button.textContent = "Copied"; }
      // When the clipboard is refused (some in-app browsers), copy the selected text the older way, or say what to do.
      function fallback() {
        prompt.focus(); prompt.select();
        var ok = false; try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
        button.textContent = ok ? "Copied" : "Selected: press copy";
      }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    });
  }

  // 2. open the folds around a linked section
  function reveal(hash) {
    if (!hash || hash.length < 2) return;
    var el = null; try { el = document.getElementById(decodeURIComponent(hash.slice(1))); } catch (e) { el = null; }
    if (!el) return;
    var opened = false;
    for (var d = el.closest("details"); d; d = d.parentElement && d.parentElement.closest("details")) {
      if (!d.open) { d.open = true; opened = true; }
    }
    if (opened) el.scrollIntoView();
  }
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href^="#"]');
    if (a) reveal(a.getAttribute("href"));
    var menu = document.querySelector("details.menu");
    if (a && menu && menu.contains(a)) menu.open = false;
  });
  document.addEventListener("keydown", function (e) {
    var menu = document.querySelector("details.menu[open]");
    if (menu && e.key === "Escape") { menu.open = false; menu.querySelector("summary").focus(); }
  });
  window.addEventListener("hashchange", function () { reveal(location.hash); });
  reveal(location.hash);

  // 3 and 4. the engines, lazily
  var hero = document.getElementById("hero"), slot = document.getElementById("seal");
  var here = document.currentScript && document.currentScript.src;   // sky.js sits next to this file, whatever the page's depth
  var base = here ? here.replace(/[^\/]*$/, "") + "shared/" : "shared/";
  var skyUrl = base + "sky.js";
  if (!hero || !("IntersectionObserver" in window)) return;
  var calm = false; try { calm = matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { calm = false; }
  var loaded = {};
  function load(name, cb) {
    if (loaded[name] === true) { cb(); return; }
    if (loaded[name]) { loaded[name].push(cb); return; }
    loaded[name] = [cb];
    var s = document.createElement("script");
    s.src = name === "sky" ? skyUrl : base + name + ".js"; s.async = false;
    s.onload = s.onerror = function () { var q = loaded[name]; loaded[name] = true; q.forEach(function (f) { try { f(); } catch (e) {} }); };
    document.head.appendChild(s);
  }
  function loadAll(names, cb) { var n = names.length; names.forEach(function (x) { load(x, function () { if (--n === 0) cb(); }); }); }
  function whileSeen(el, on, off, margin) {
    new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) on(); else if (off) off(); }); }, { rootMargin: margin || "0px" }).observe(el);
  }

  // the stars drift at two thirds of the page's speed, on a critically damped spring, only while the hero is seen
  function parallax() {
    if (calm) return;
    var pos = 0, vel = 0, raf = 0, seen = true;
    function step() {
      var target = Math.min(window.scrollY, hero.offsetHeight) * 0.33;
      vel = (vel + (target - pos) * 0.12) * 0.62; pos += vel;
      var cv = hero.querySelector(".sx-sky-cv"); if (cv) cv.style.transform = "translate3d(0," + pos.toFixed(2) + "px,0)";
      raf = Math.abs(target - pos) > 0.1 || Math.abs(vel) > 0.1 ? requestAnimationFrame(step) : 0;
    }
    window.addEventListener("scroll", function () { if (seen && !raf) raf = requestAnimationFrame(step); }, { passive: true });
    whileSeen(hero, function () { seen = true; }, function () { seen = false; });
  }

  function skyOn(el, opts) {
    var live = null;
    // off screen the loop stops and its last still frame stays; coming back, the old canvas makes way for the live one
    whileSeen(el, function () { if (!live && window.SXSky) { var c = el.querySelector(".sx-sky-cv"); if (c) c.remove(); live = window.SXSky.mount(el, opts); } },
      function () { if (live) { live.stop(); live = null; } });
  }

  function start() {
    load("sky", function () {
      var sky = window.SXSky; if (!sky) return;
      if (slot && sky.seal) slot.innerHTML = sky.seal();
      skyOn(hero, { density: 1.15, galaxy: false });
      parallax();
      var closing = document.querySelector("section.closing");
      if (closing) skyOn(closing, { density: 0.7, galaxy: false, seed: 20261125 });
      // the seal and the gold call, lit with real optics; the CSS look stays underneath as the fallback
      loadAll(["touch", "materials"], function () {});
    });
    // one material per card, each only when its card is near
    document.querySelectorAll("[data-sx-obj]").forEach(function (obj) {
      var done = false;
      whileSeen(obj, function () {
        if (done) return; done = true;
        var kind = obj.getAttribute("data-sx-obj"), have = +obj.getAttribute("data-have") || 0, want = +obj.getAttribute("data-want") || 0;
        var label = obj.getAttribute("data-label") || "";
        if (kind === "gold") loadAll(["touch", "world", "gold"], function () { if (window.SXWorld) obj.innerHTML = SXWorld.goldBars(have, want, label); });
        else if (kind === "water") loadAll(["touch", "materials", "world", "water"], function () {
          if (window.SXWorld) obj.innerHTML = SXWorld.vessel(have / want, have >= want ? "good" : "watch", obj.getAttribute("data-aim") || "", label);
        });
        else if (kind === "sea") loadAll(["sea"], function () {
          var s = obj.querySelector("[data-sx-sea]"); if (!s || !window.SXSea) return;
          whileSeen(s, function () { window.SXSea.mount(s); });
        });
      }, null, "200px");
    });
  }
  var later = window.requestIdleCallback || function (f) { return setTimeout(f, 200); };
  if (document.readyState === "complete") later(start);
  else window.addEventListener("load", function () { later(start); });
})();
