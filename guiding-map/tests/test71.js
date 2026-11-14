// test71: the More sheet shows the vital few first, ordered by risk, and folds everything else (owner 2026-11-12: focus).
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = () => ({ matches: true, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }); w.scrollTo = () => {}; } });
const w = dom.window, doc = w.document;
setTimeout(() => {
  try {
    // Start simple (owner, 2026-11-14): three doors (Money, Protection, Life balance) then Show everything; the full
    // ordering below is checked with everything shown.
    w.gmNavMore(true);
    const simple = doc.getElementById("gmMoreSheet");
    const doors = [...simple.querySelectorAll(".sh button[role=menuitem]")].map((b) => (b.getAttribute("onclick") || "").replace(/.*'(\w+)'.*/, "$1"));
    ok(doors.slice(0, 3).join() === "money,breaks,wheel" && /Show everything/.test(simple.textContent), "simple: the three doors, then Show everything: " + doors.join());
    // Calm and real (owner, 2026-11-14): one more door each week used; after two weeks the Shield and Deadlines join.
    w.localStorage.setItem("gm_first_seen", JSON.stringify(Date.now() - 15 * 24 * 60 * 60 * 1000));
    w.gmSimple(true); w.gmNavMore(true);
    const grown = doc.getElementById("gmMoreSheet");
    const grownDoors = [...grown.querySelectorAll(".sh button[role=menuitem]")].map((b) => (b.getAttribute("onclick") || "").replace(/.*'(\w+)'.*/, "$1"));
    ok(grownDoors.slice(0, 5).join() === "money,breaks,wheel,risk,deadlines" && /Show everything/.test(grown.textContent), "simple, after two weeks: the next doors appear: " + grownDoors.join());
    w.localStorage.removeItem("gm_first_seen");
    w.gmSimple(false); w.gmNavMore(true);
    const sheet = doc.getElementById("gmMoreSheet");
    const idOf = (b) => ((b.getAttribute("onclick") || "").match(/gmNavGo\('([a-z]+)'\)/) || [])[1];
    const first = Array.from(sheet.querySelectorAll(".sh > button")).map(idOf);
    const want = ["risk", "deadlines", "systems", "money", "breaks", "wheel"].filter((id) => w.TABS.some((t) => t[0] === id));
    ok(JSON.stringify(first) === JSON.stringify(want), "the vital few come first, in risk order: " + first.join(","));
    ok(first[0] === "risk", "the Shield is the first tile");
    const fold = sheet.querySelector("details.gm-more-all");
    ok(fold && !fold.open, "everything else is folded and closed by default");
    ok(fold && /Everything else \(\d+\)/.test(fold.querySelector("summary").textContent), "the fold says how many");
    const main = ["today", "inbox", "okr", "ask"];
    const all = Array.from(sheet.querySelectorAll("button")).map(idOf).filter(Boolean);
    w.TABS.filter((t) => main.indexOf(t[0]) < 0).forEach((t) => ok(all.filter((x) => x === t[0]).length === 1, t[0] + " appears exactly once"));
    ok(Array.from(fold.querySelectorAll("button")).some((b) => /All apps/.test(b.textContent)), "All apps stays, inside the fold");
    w.gmMoreAll(true);
    ok(JSON.parse(w.localStorage.getItem("gm_more_all")) === true, "opening the fold is remembered");
    w.localStorage.removeItem("gm_more_all");
    w.gmNavGo("career"); w.gmNavMore(true);
    const f2 = doc.querySelector("#gmMoreSheet details.gm-more-all");
    ok(f2 && f2.open, "when the current tab is inside the fold, the fold opens");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test71 more sheet, vital few first: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
