// test156: Us (owner 2026-11-23): closeness as wellbeing, plainly and privately: off until turned on, three taps a week,
// a kind suggestion after two quieter weeks, health basics folded, and never anything explicit. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", pname: "Sam Example", pdob: "1994-02-01", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000,
  kids: [], ret: 60, tsav: 20, example: false, earners: 2, partner: { net: 50000 } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage;
  w.goTab("life"); w.renderAll();
  let c = d.querySelector(".gm-us");
  ok("off by default: one line and a Turn on button, no questions", !!c && /Turn on/.test(c.textContent) && !c.querySelector("[role=group]"), c && c.textContent);
  w.gmUsOn(true); c = d.querySelector(".gm-us");
  ok("on: three one-tap scales", c && c.querySelectorAll("[role=group]").length === 3);
  w.gmUsSet("close", 4);
  const u = JSON.parse(ls.getItem("gm_us"));
  ok("a tap is stored under this week", u.on === true && Object.values(u.weeks)[0].close === 4);
  ok("no dip line after one good week", !/Two quieter weeks/.test(d.querySelector(".gm-us").textContent));
  u.weeks = { "2026-01-05": { close: 2 }, "2026-01-12": { close: 1 } }; ls.setItem("gm_us", JSON.stringify(u)); w.renderAll();
  ok("two quieter weeks: one kind suggestion", /Two quieter weeks/.test(d.querySelector(".gm-us").textContent));
  ok("health basics are folded, plain and non-explicit", !!d.querySelector(".gm-us details") && /talk about with a doctor/.test(d.querySelector(".gm-us details").textContent));
  w.gmUsOn(false);
  ok("turning off hides it and keeps the check-ins", /Turn on/.test(d.querySelector(".gm-us").textContent) && JSON.parse(ls.getItem("gm_us")).weeks["2026-01-12"].close === 1);
  console.log("test156 us: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
