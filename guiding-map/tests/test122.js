// v122: Calls journal on Today (queue calls-journal, slice 2). A call whose date has come shows as one calm line above
// the daily three, with Yes and No, so the person judges it where they already look. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const due = [{ id: "callA", text: "I expect the fund to cross 10 lakh", conf: 70, date: "2020-01-01", outcome: null, ts: 1 }];
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_calls", JSON.stringify(due));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const saved = () => { try { return JSON.parse(w.localStorage.getItem("gm_calls") || "[]") || []; } catch (x) { return []; } };
  w.goTab("today");
  let line = d.querySelector(".gm-call-today"), d3 = d.querySelector("#sections .gm-d3");
  const above = !!line && !!d3 && !!(line.compareDocumentPosition(d3) & w.Node.DOCUMENT_POSITION_FOLLOWING);
  ok("Today shows the due call as one calm line above the daily three", !!line && above && d.querySelectorAll(".gm-call-today").length === 1,
    line ? "not above the daily three" : "no .gm-call-today line");
  ok("the line carries the call in its own words", !!line && /fund to cross 10 lakh/.test(line.textContent),
    line ? line.textContent.slice(0, 140) : "no line");
  const yes = line && line.querySelector("[data-call-yes]"), no = line && line.querySelector("[data-call-no]");
  ok("the line offers Yes and No", !!(yes && no), "missing a tap");
  if (yes) yes.click();
  ok("tapping Yes records the outcome", saved().length === 1 && saved()[0].outcome === "yes", JSON.stringify(saved()));
  w.goTab("today");
  ok("the judged call's line is gone on the next render", !d.querySelector(".gm-call-today"));

  w.localStorage.setItem("gm_calls", JSON.stringify([{ id: "callB", text: "I expect the fund to cross 20 lakh", conf: 80, date: "2999-01-01", outcome: null, ts: 1 }]));
  w.goTab("today");
  ok("a call whose date has not come shows no line on Today", !d.querySelector(".gm-call-today"));

  console.log("test122 calls journal on Today: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
