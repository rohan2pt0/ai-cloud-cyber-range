// test153: every property verdict shows its target, and no value is cut off on a phone (owner 2026-11-22).
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
  const metrics = [...box.querySelectorAll(".gm-metric")];
  ok("the property shows its metric rows", metrics.length >= 8, metrics.length);
  const verdictRows = metrics.filter(m => m.querySelector(".gm-vw"));
  ok("every verdict row shows a target starting 'aim'", verdictRows.length >= 8 && verdictRows.every(m => { const t = m.querySelector(".gm-tgt"); return t && /^aim /.test(t.textContent.trim()); }), verdictRows.length + " verdict rows");
  ok("no metric value column keeps white-space:nowrap", metrics.every(m => { const c = m.lastElementChild; return c && !/nowrap/.test(c.getAttribute("style") || ""); }), metrics.map(m => m.lastElementChild && m.lastElementChild.getAttribute("style")).join(" | "));
  console.log("PASS " + P + " FAIL " + F); e.forEach(x => console.log("  FAIL: " + x)); process.exit(F ? 1 : 0);
}, 400);
