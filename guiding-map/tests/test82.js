// test82: your constellation (owner, 2026-11-12, after the Rolls-Royce Starlight headliner): each real achievement is a permanent star.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } }).window;
setTimeout(() => {
  try {
    const d = w.document;
    const before = d.querySelectorAll("#gmSky .gm-star").length;
    const k = (o) => { const x = new Date(); x.setDate(x.getDate() - o); return w.dKey(x); };
    w.S.daily[k(1)] = ["ex", "mf", "fm"]; w.S.daily[k(2)] = ["ex", "mf", "fm"]; w.S.daily[k(3)] = ["ex"];
    w.renderAll();
    const stars = Array.from(d.querySelectorAll("#gmSky .gm-star"));
    ok(stars.length === before + 2, "each day with all three done adds one star (a partial day does not)");
    ok(d.getElementById("gmSky").getAttribute("aria-hidden") === "true", "the sky is decoration for screen readers");
    const pos = stars.map((s) => s.style.left + s.style.top).join("|");
    w.renderAll();
    const pos2 = Array.from(d.querySelectorAll("#gmSky .gm-star")).map((s) => s.style.left + s.style.top).join("|");
    ok(pos === pos2, "every star keeps its place: the sky is yours and stable");
    const css = Array.from(d.querySelectorAll("style")).map((s) => s.textContent).join("\n");
    ok(/prefers-reduced-motion: reduce\)\{\.gm-star\{animation:none\}/.test(css), "no twinkle for reduced motion");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test82 your constellation: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
