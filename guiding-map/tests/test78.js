// test78: signature moments (owner, 2026-11-12): a once-per-install intro, an unveil every open, a shimmer when the daily three are done.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
function boot(pre, reduced) {
  return new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
    beforeParse(w) { w.matchMedia = (q) => ({ matches: /reduce/.test(q) ? !!reduced : /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.navigator.vibrate = () => { w.__vib = (w.__vib || 0) + 1; return true; }; pre && pre(w); } }).window;
}
const a = boot();
setTimeout(() => {
  ok(!!a.document.getElementById("gmIntro"), "the first open shows the signature intro");
  ok(JSON.parse(a.localStorage.getItem("gm_intro_seen")) === true, "it is remembered, so it plays once per install");
  ok(/Your private estate/.test(a.document.getElementById("gmIntro").textContent), "it says 'Your private estate'");
  a.document.getElementById("gmIntro").click();
  ok(a.document.getElementById("gmIntro").classList.contains("out"), "a tap enters at once");
  const b = boot((w) => { w.localStorage.setItem("gm_intro_seen", "true"); w.__unveil = false;
    w.addEventListener("DOMContentLoaded", () => { new w.MutationObserver(() => { if (w.document.querySelector(".logo-ring.gm-unveil")) w.__unveil = true; }).observe(w.document.body, { subtree: true, attributes: true, attributeFilter: ["class"] }); }); });
  const c = boot(null, true);
  setTimeout(() => {
    ok(!b.document.getElementById("gmIntro"), "a later open has no intro");
    ok(b.__unveil === true, "a later open unveils the header ring");
    ok(!c.document.getElementById("gmIntro"), "no intro for a person who asks for reduced motion");
    const tiles = b.document.querySelectorAll(".gm-d3 .tile");
    tiles.forEach((t) => { if (!t.classList.contains("on")) t.click(); });
    setTimeout(() => {
      ok(!!b.localStorage.getItem("gm_d3_celebrated"), "completing the daily three is celebrated");
      ok((b.__vib || 0) >= 1, "with one soft haptic pulse");
      const n = b.__vib; b.renderAll();
      ok(b.__vib === n, "only once a day, not on every redraw");
      console.log("test78 signature moments: " + pass + " passed, " + fail + " failed");
      process.exit(fail ? 1 : 0);
    }, 300);
  }, 1500);
}, 1500);
