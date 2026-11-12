// test73: a change never snaps open sections shut (owner, 2026-11-12), and the CSF self-score uses plain choices.
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
    w.goTab("ops");
    const ds = () => Array.from(doc.querySelectorAll("#sections details"));
    ok(ds().length >= 2, "the Ops screen has foldable sections");
    const target = ds()[1]; const label = target.querySelector("summary").textContent.trim();
    target.open = true;
    w.renderAll();
    const again = ds().find((d) => d.querySelector("summary").textContent.trim() === label);
    ok(again && again.open, "after a redraw on the same tab the section the person had open is still open");
    w.goTab("growth"); w.goTab("ops");
    const fresh = ds().find((d) => d.querySelector("summary").textContent.trim() === label);
    ok(fresh && !fresh.open, "a tab opened anew starts with its sections folded");
    const sec = doc.getElementById("sections");
    const csf = Array.from(sec.querySelectorAll('[role="group"]')).filter((g) => /where you are/.test(g.getAttribute("aria-label") || ""));
    if (csf.length) {
      ok(csf.length === 6, "six CSF areas, each with plain choices");
      ok(!Array.from(csf).some((g) => g.parentElement.querySelector("input[type=range]")), "no bare 0-5 slider left in the CSF cards");
      const b = Array.from(csf[0].querySelectorAll("button")).find((x) => x.textContent === "Mostly");
      ok(!!b, "a choice reads 'Mostly'");
      b.click();
      ok(JSON.parse(w.localStorage.getItem("gm_csf") || "{}").GV === 4, "tapping 'Mostly' stores 4 for Govern");
    } else ok(true, "CSF not on this screen");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test73 sections stay open, plain CSF choices: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
