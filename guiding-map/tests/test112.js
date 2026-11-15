// v112: impossible numbers can never be saved on Property or Career (owner, 2026-11-15: "a salary can't be minus...
// make it almost impossible to make a mistake"). One guard, gmFieldGuard, clamps and explains every figure before it
// is stored, so a minus rent, a salary typed in rupees or a 20-month vacancy never reaches the screen.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const g = (rule, v) => w.gmFieldGuard(rule, v);
  let r = g({ min: 0, max: 10 }, "-5");
  ok("a minus amount is clamped to its floor, with a note", r.v === 0 && !!r.note, JSON.stringify(r));
  r = g({ min: 0, max: 10 }, "abc");
  ok("text that is not a number is cleared, with a note", r.v === "" && !!r.note, JSON.stringify(r));
  r = g({ min: 0, max: 10000000 }, "\u20b918,000");
  ok("18,000 typed the Indian way (with commas and the rupee sign) is a number, not a mistake", r.v === 18000 && !r.note, JSON.stringify(r));
  r = g({ min: 0, max: 10000000 }, "Rs. 1,20,000");
  ok("Rs. 1,20,000 reads as 120000", r.v === 120000 && !r.note, JSON.stringify(r));
  r = g({ min: 0, max: 10 }, "");
  ok("an empty field stays empty and quiet", r.v === "" && !r.note, JSON.stringify(r));
  r = g({ lakh: true, min: 0, max: 100000 }, "7500000");
  ok("a value typed in rupees becomes lakh, with a note that says so", r.v === 75 && /lakh/i.test(r.note), JSON.stringify(r));
  r = g({ month: true }, "1826-05");
  ok("a birth month before 1900 is cleared", r.v === "", JSON.stringify(r));
  r = g({ date: true }, "2026-02-30");
  ok("30 February is cleared: it is not a real date", r.v === "", JSON.stringify(r));

  w.gmPropAdd();
  w.gmPropSet(0, "rent", "-18000");
  ok("Property stores a minus rent as 0", w.gmG("gm_props", [])[0].rent === 0, JSON.stringify(w.gmG("gm_props", [])[0]));
  w.gmPropSet(0, "val", "7500000");
  ok("Property stores a rupee value as 75 lakh", w.gmG("gm_props", [])[0].val === 75, JSON.stringify(w.gmG("gm_props", [])[0]));
  w.gmPropSet(0, "vac", "20");
  ok("Property stores a 20-month vacancy as 12", w.gmG("gm_props", [])[0].vac === 12, JSON.stringify(w.gmG("gm_props", [])[0]));

  w.gmCarSet("cfg.infl", "900");
  ok("Career stores 900% inflation as 20%", w.gmG("gm_career", {}).cfg.infl === 20, JSON.stringify(w.gmG("gm_career", {}).cfg));
  w.gmCarSet("cur.gross", "-1");
  ok("Career stores a minus salary as 0", w.gmG("gm_career", {}).cur.gross === 0, JSON.stringify(w.gmG("gm_career", {}).cur));

  console.log("test112 impossible numbers are clamped on Property and Career: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
