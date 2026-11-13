// test83: the Atelier (owner, 2026-11-12, after bespoke coachbuilding): choose the material the estate is finished in.
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
    ok(d.documentElement.getAttribute("data-mat") === "classic", "the default is the classic navy");
    w.goTab("ops");
    const opts = Array.from(d.querySelectorAll(".gm-atelier .gm-at"));
    ok(opts.length === 5, "five materials to choose from");
    ok(d.querySelector(".gm-atelier [role=radiogroup]") && opts.every((o) => o.getAttribute("role") === "radio"), "a proper radio group for screen readers");
    opts.find((o) => /Cognac/.test(o.textContent)).click();
    ok(d.documentElement.getAttribute("data-mat") === "cognac", "choosing cognac re-skins the estate");
    ok(JSON.parse(w.localStorage.getItem("gm_mat")) === "cognac", "the choice is remembered on this device");
    ok(d.querySelector(".gm-atelier .gm-at.on").getAttribute("aria-checked") === "true", "the chosen material is marked");
    const css = Array.from(d.querySelectorAll("style")).map((s) => s.textContent).join("\n");
    ["cognac", "marble", "sapphire", "carbon"].forEach((m) => ok(new RegExp("html\\[data-mat=" + m + "\\] \\.gm-hero").test(css), m + " finishes the hero cards"));
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test83 the Atelier: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
