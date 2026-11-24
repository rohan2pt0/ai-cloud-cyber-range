/* The product site's home page (website-v2). A separate file, because the site's policy allows scripts from itself only
   (website/_headers: script-src 'self'), so an inline script would never run on the hosted site.
   1. Copy the install sentence.
   2. A link to something folded away (Products, Readiness) opens its fold first, so it never lands on nothing.
   3. The hero's night sky and gold seal: the shared engine (guiding-map/shared/sky.js, copied in by website/build.sh),
      loaded only after the page has loaded, drawn only while the hero is on screen. Reduced motion, a hidden tab or an
      automated browser get one still frame (sky.js decides). Without the file, the hero keeps its plain night colour. */
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
  window.addEventListener("hashchange", function () { reveal(location.hash); });
  reveal(location.hash);

  // 3. the night sky and the seal, lazily
  var hero = document.getElementById("hero"), slot = document.getElementById("seal");
  if (!hero || !("IntersectionObserver" in window)) return;
  function load(cb) {
    if (window.SXSky) { cb(); return; }
    var s = document.createElement("script");
    s.src = "shared/sky.js"; s.async = true; s.onload = cb;
    document.head.appendChild(s);
  }
  function start() {
    load(function () {
      var sky = window.SXSky; if (!sky) return;
      if (slot && sky.seal) slot.innerHTML = sky.seal();
      var live = null;
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting && !live) live = sky.mount(hero, { density: 0.8, galaxy: false });
          else if (!en.isIntersecting && live) { live.stop(); live = null; }   // off screen: no frames at all
        });
      }).observe(hero);
    });
  }
  var later = window.requestIdleCallback || function (f) { return setTimeout(f, 200); };
  if (document.readyState === "complete") later(start);
  else window.addEventListener("load", function () { later(start); });
})();
