// test85: a living sky (owner, 2026-11-13, "it doesn't look like a sky unless it has some motion"): stars breathe, a comet crosses now and then.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
ok(/@keyframes gmtw\{[^}]*scale/.test(html), "stars swell as they twinkle, not only fade");
ok(/@keyframes gmcomet/.test(html) && /\.gm-comet\{/.test(html), "a shooting star has its own streak and flight");
ok(/prefers-reduced-motion: reduce\)\{\.gm-comet\{display:none\}/.test(html), "no comet for people who ask for less motion");
ok(/header>\*:not\(#gmSky\):not\(#gmTrail\)/.test(html), "the comet layer sits behind the title and buttons");
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } }).window;
setTimeout(() => {
  try {
    ok(!w._gmComets, "no repeating comet timer in a headless page (it would keep the page alive)");
    w.renderAll(); w.renderAll();
    ok(/if \(!window\._gmComets && !navigator\.webdriver/.test(html), "the scheduler is armed once, and only in a real browser");
    ok(w.document.querySelectorAll(".gm-comet").length <= 1, "at most one comet in the sky at a time");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test85 living sky: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
