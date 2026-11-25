// test154: per property, only the worst problem stays in view (one plain card); the rest fold under "Later" (owner 2026-11-21, plain-first 2026-11-25).
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", pname: "Sam", pdob: "1994-02-01", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000,
  nw: 0, kids: [], ret: 60, tsav: 20, example: false, earners: 2, rent1: 30000, rent2: 0,
  loans: [], mine: { epf: 200000, nps: 1000000, term: 15000000 }, partner: { net: 50000, epf: 500000, term: 10000000 },
  work: { kind: "contract", from: "2027-01-01" }, pwork: { kind: "permanent", from: "2027-01-01" } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_props", JSON.stringify([{ n: "Fake flat", use: "letout", val: "80", rent: "15000", loan: "60", emi: "50000", out: "30000", vac: "1" }]));
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("prop"); w.renderAll();
  const box = d.querySelector("#sections") || d.body;
  const all = [...box.querySelectorAll(".gm-metric")];
  const rankOf = m => { const n = m.querySelector(".gm-num"); const c = n ? n.className : ""; return /gm-v-r/.test(c) ? 0 : /gm-v-a/.test(c) ? 1 : /gm-v-g/.test(c) ? 2 : 3; };
  const shown = all.filter(m => !m.closest("details.gm-later"));
  // plain-first (2026-11-25): the first problem is in view as ONE plain card; its measures sit in its fold, the rest under Later
  const inView = [...box.querySelectorAll(".gm-pf")].filter(c => !c.closest("details.gm-later"));
  ok("exactly one problem stays in view, and no bare measure row", inView.length === 1 && shown.every(m => m.closest("details")), inView.length + " cards, " + shown.length + " bare rows")
  ;
  ok("the worst problem comes first", inView[0] && inView[0].getAttribute("data-issue") === "dscr-low", inView[0] && inView[0].getAttribute("data-issue"));
  const det = box.querySelector("details.gm-later");
  const folded = all.filter(m => m.closest("details.gm-later"));
  ok("the rest fold under a Later summary", det && det.querySelector("summary") && det.querySelector("summary").textContent.trim().indexOf("Later (") === 0, det ? det.querySelector("summary").textContent : "none");
  const kids = det ? [...det.querySelectorAll(":scope > div > .gm-pf, :scope > div > .gm-metric")].length : -1;
  ok("the summary counts the folded cards and rows", det && det.querySelector("summary").textContent.trim() === "Later (" + kids + ")", det ? det.querySelector("summary").textContent + " vs " + kids : "none");
  console.log("PASS " + P + " FAIL " + F); e.forEach(x => console.log("  FAIL: " + x)); process.exit(F ? 1 : 0);
}, 400);
