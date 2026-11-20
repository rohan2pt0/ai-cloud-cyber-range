// test153: every property verdict says what it is aiming at, and no value is cut off on a phone (owner 2026-11-20).
// Each verdict row shows a muted "aim ..." target under the word, and the value column wraps instead of forcing one line.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", pname: "Sam", pdob: "1994-02-01", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000,
  nw: 0, kids: [], ret: 60, tsav: 20, example: false, earners: 2, rent1: 30000, rent2: 0,
  loans: [], mine: {}, partner: {}, work: {}, pwork: {} };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_props", JSON.stringify([{ n: "Fake flat", use: "letout", val: "80", rent: "15000", loan: "60", emi: "50000", out: "30000", vac: "1" }]));
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("prop"); w.renderAll();
  const box = d.querySelector("#sections") || d.body;
  const rows = [...box.querySelectorAll(".gm-metric")].filter(r => /Strong|Watch|Weak/.test(r.textContent));
  ok("there are verdict rows to check", rows.length >= 8, rows.length);
  ok("each verdict row shows an aim target", rows.every(r => { const t = r.querySelector(".gm-tgt"); return t && /^aim /.test(t.textContent.trim()); }),
    rows.map(r => r.querySelector(".gm-tgt") ? r.querySelector(".gm-tgt").textContent : "(none)").join(" | "));
  const cols = [...box.querySelectorAll(".gm-metric > div:last-child")];
  ok("no metric value column forces one line", cols.length > 0 && cols.every(c => !/white-space:\s*nowrap/.test(c.getAttribute("style") || "")), cols.length);
  console.log("PASS " + P + " FAIL " + F); e.forEach(x => console.log("  FAIL: " + x)); process.exit(F ? 1 : 0);
}, 400);
