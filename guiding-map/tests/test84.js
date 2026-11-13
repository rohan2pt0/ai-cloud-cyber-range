// test84: the guarded switch (owner, 2026-11-13, after fighter-jet switch guards): erase sits under a cover that lifts first.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } }).window;
setTimeout(() => {
  try {
    w.goTab("ops");
    const d = w.document, guard = d.querySelector(".gm-guard"), sw = guard && guard.querySelector(".gm-erase"), cover = guard && guard.querySelector(".gm-guard-cover");
    ok(!!guard && !!cover && !!sw, "erase sits inside a guard with a cover");
    ok(sw && sw.hidden === true, "the erase switch is hidden until the cover is lifted");
    ok(cover && cover.getAttribute("aria-expanded") === "false", "the cover says it is closed");
    cover.click();
    setTimeout(() => {
      ok(guard.classList.contains("up") && cover.getAttribute("aria-expanded") === "true", "lifting the cover opens it");
      ok(sw.hidden === false, "then the switch shows");
      ok(/gmEraseAsk/.test(sw.getAttribute("onclick")), "the switch still leads to the typed confirmation");
      console.log("test84 guarded switch: " + pass + " passed, " + fail + " failed");
      process.exit(fail ? 1 : 0);
    }, 350);
  } catch (e) { fail++; console.log("FAIL threw " + e.message); console.log("test84: " + pass + " passed, " + fail + " failed"); process.exit(1); }
}, 1500);
