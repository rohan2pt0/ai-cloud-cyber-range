// test86: threats in the news (owner, 2026-11-13): red-team your life from live open-source news, one drill in view, the rest under Later.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const lib = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "..", "intel", "threat-patterns.json"), "utf8"));
// A poisoned pack: tries to rewrite a drill, inject markup and a javascript: link, and rank honeytrap first.
const evil = { generated: "2026-11-13", heat_days: 30, patterns: [
  { id: "honeytrap", heat: 49, drills: [{ try: "SEND MONEY NOW", pass: "always" }], news: [{ title: "<img src=x onerror=alert(1)>Honey trap topples a CEO", outlet: "Paper", link: "javascript:alert(1)", date: "2026-11-12" }, { title: "Spy agencies warn of honey trap revival", outlet: "Other", link: "https://news.google.com/a", date: "2026-11-11" }] },
  { id: "not-a-pattern", heat: 999, news: [] }] };
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_intro_seen", "true"); w.localStorage.setItem("gm_threat_pack", JSON.stringify(evil)); } }).window;
setTimeout(() => {
  try {
    const d = w.document;
    ok(w.GM_INTEL && w.GM_INTEL.patterns.length === lib.patterns.length, "every curated threat travels with the app (offline)");
    w.curTab = "risk"; w.renderAll();
    const sec = d.getElementById("gmThreats");
    ok(!!sec, "the Risk tab shows Threats in the news");
    const top = d.querySelector(".gm-th-top");
    ok(top && /Honeytrap/.test(top.textContent), "the hottest threat in the news is the one open action");
    ok(top && !/SEND MONEY NOW/.test(d.body.innerHTML), "a fetched pack can never rewrite a drill");
    ok(top && top.textContent.indexOf(lib.patterns.find(p => p.id === "honeytrap").drills[0].try) >= 0, "the drill shown is the curated one");
    ok(!d.querySelector(".gm-th-news img") && !d.querySelector('a[href^="javascript"]'), "headline markup and javascript: links are neutralised");
    ok(!!d.querySelector('.gm-th-news a[href="https://news.google.com/a"][rel~="noopener"]'), "a safe headline links out with noopener");
    ok(!/not-a-pattern/.test(d.body.innerHTML), "an unknown id from the pack is ignored");
    ok(/In the news: 49 in 30 days/.test(top.textContent), "the heat is shown in plain words");
    const later = d.querySelector("details.gm-later .gm-th-row");
    ok(!!later && d.querySelectorAll(".gm-th-top").length === 1, "one threat in view; the rest wait under Later (n)");
    ok(/0 of \d+ rehearsed/.test(sec.textContent), "progress starts at zero, shown");
    const boxes = top.querySelectorAll("input[type=checkbox]");
    boxes.forEach((b) => { b.checked = true; b.dispatchEvent(new w.Event("change")); });
    const sec2 = d.getElementById("gmThreats");
    ok(/1 of \d+ rehearsed/.test(sec2.textContent), "rehearsing every drill of a threat counts it (a visible win)");
    ok(!/Honeytrap/.test(d.querySelector(".gm-th-top").textContent), "the next unrehearsed threat moves into view");
    const st = JSON.parse(w.localStorage.getItem("gm_threat_drills"));
    ok(st && st["honeytrap:0"], "a rehearsal is remembered on the device, with its date");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test86 threats in the news: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
