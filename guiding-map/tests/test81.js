// test81: golden repairs (owner, 2026-11-12, after kintsugi): a missed day you came back from is mended in gold, never shown as failure.
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
    ok(!d.querySelector(".gm-kin"), "a new person sees no strip of empty circles");
    const k = (o) => { const x = new Date(); x.setDate(x.getDate() - o); return w.dKey(x); };
    w.S.daily[k(4)] = ["ex"]; w.S.daily[k(2)] = ["mf"]; w.S.daily[k(1)] = ["fm"];
    w.renderAll();
    const strip = d.querySelector(".gm-kin");
    ok(!!strip, "with history, the seven-day strip shows");
    ok(strip && strip.querySelectorAll(".kd").length === 7, "seven days");
    ok(strip && strip.querySelectorAll(".k-kept").length === 3, "kept days are gold coins");
    ok(strip && strip.querySelectorAll(".k-rep").length === 1, "the missed day you came back from is repaired in gold");
    ok(/repaired in gold because you came back/.test(d.querySelector(".gm-kin-note").textContent), "the note is kind, never a reproach");
    ok(!/fail|missed streak|broke/i.test(strip.textContent + d.querySelector(".gm-kin-note").textContent), "no failure words");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test81 golden repairs: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
