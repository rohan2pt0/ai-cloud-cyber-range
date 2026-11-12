// test80: gadget-grade touches (owner, 2026-11-12): three activity rings, detents on checkboxes and folds, a tilt sheen.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_intro_seen", "true"); w.navigator.vibrate = (ms) => { w.__v = (w.__v || []).concat([ms]); return true; }; } }).window;
setTimeout(() => {
  try {
    const d = w.document, svg = d.querySelector(".gm-greet svg.gm-rings");
    ok(!!svg, "Today shows the rings");
    ok(svg && svg.querySelectorAll("circle.gm-arc").length === 3, "three rings: daily three, Stack and Shield");
    ok(svg && /done today; Stack \d+%; Shield \d+%/.test(svg.getAttribute("aria-label")), "a screen reader hears all three values");
    ok(svg && !!svg.querySelector("#gmRgGold") && !!svg.querySelector("#gmRgVel"), "gold and velvet ring materials");
    const css = Array.from(d.querySelectorAll("style")).map((s) => s.textContent).join("\n");
    ok(/@keyframes gmsweep2/.test(css) && /prefers-reduced-motion: reduce\)\{\.gm-arc\{animation:none\}/.test(css), "the gauge sweep, off for reduced motion");
    ok(/\.gm-hero::after\{[^}]*var\(--sx,0\)/.test(css), "the hero sheen follows the tilt");
    const box = d.createElement("input"); box.type = "checkbox"; d.body.appendChild(box);
    box.dispatchEvent(new w.Event("pointerdown", { bubbles: true }));
    ok((w.__v || []).indexOf(4) >= 0, "a checkbox gives a soft detent");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test80 rings, detents and tilt: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
