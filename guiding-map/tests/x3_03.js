// x3_03: a tick is announced (experience-fixes brief 3). Today has one hidden live region; ticking a daily three tile
// tells a screen reader the habit's name and the count, and un-ticking says so. Fake data only.
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
  const w = dom.window, d = w.document, say = () => d.getElementById("gmSay");
  const css = () => (d.getElementById("sxLux") || {}).textContent || "";
  ok("the page has exactly one #gmSay", d.querySelectorAll("#gmSay").length === 1);
  const el = say();
  ok("it is a polite status region", !!el && el.getAttribute("aria-live") === "polite" && el.getAttribute("role") === "status");
  ok("it is visually hidden", !!el && el.classList.contains("gm-sr") && /\.gm-sr\{[^}]*clip:rect\(0 0 0 0\)/.test(css()));
  const name = w.HABITS[0].name;
  w.tgHabit(0);
  ok("a tick says the habit's name and 1 of 3", !!say() && say().textContent.indexOf(name) >= 0 && /1 of 3/.test(say().textContent), say() && say().textContent);
  w.renderAll();
  ok("the region survives a redraw", d.querySelectorAll("#gmSay").length === 1 && say() === el);
  w.tgHabit(0);
  ok("un-ticking says so", !!say() && say().textContent.indexOf(name) >= 0 && /not done/.test(say().textContent) && /0 of 3/.test(say().textContent), say() && say().textContent);
  console.log("x3_03 a tick is announced: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
