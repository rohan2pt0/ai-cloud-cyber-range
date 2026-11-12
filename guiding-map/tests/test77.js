// test77: luxury slice 1, typography and motion (owner, 2026-11-12).
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.confirm = () => false; w.alert = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const w = dom.window, doc = w.document;
setTimeout(() => {
  try {
    const css = Array.from(doc.querySelectorAll("style")).map((s) => s.textContent).join("\n");
    ok(/#sections \.cat-t\{font-family:'Instrument Serif'/.test(css), "section titles use the editorial serif");
    ok(/prefers-reduced-motion: reduce\)\{#sections\.gm-first/.test(css), "no entrance motion for a person who asks for less motion");
    ok(/tabular-nums lining-nums/.test(css), "numbers line up");
    ok(/\.gm-d3 \.t\{text-transform:none!important/.test(css), "the daily-three heading is calm, not capitals");
    w.goTab("risk");
    const box = doc.getElementById("sections"), first = box.getAttribute("data-first");
    ok(!!first, "a newly opened screen is marked as a first render");
    const vit = Array.from(doc.querySelectorAll("#gmVitals div")).filter((d) => /uppercase/.test(d.getAttribute("style") || ""));
    ok(vit.length === 0, "vitals labels are not forced into capitals");
    setTimeout(() => {
      w.renderAll();
      ok(box.getAttribute("data-first") === first, "a redraw of the same screen is not a first render (nothing moves while working)");
      w.goTab("money");
      ok(box.getAttribute("data-first") !== first, "switching screens is a first render again");
      console.log("test77 luxury typography and motion: " + pass + " passed, " + fail + " failed");
      process.exit(fail ? 1 : 0);
    }, 20);
  } catch (e) { fail++; console.log("FAIL threw " + e.message); console.log("test77: " + pass + " passed, " + fail + " failed"); process.exit(1); }
}, 1500);
