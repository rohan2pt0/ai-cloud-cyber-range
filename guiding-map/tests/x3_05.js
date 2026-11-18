// x3_05: the stars rest (experience-fixes brief 5). The twinkle on .gm-star stops while the Life OS rests —
// the tab hidden, or 20 s untouched — and wakes on the first touch. The rule pauses the stars; a small controller
// adds and removes gm-rest on <html>. jsdom, fake data only.
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
  const css = () => [...d.querySelectorAll("style")].map(s => s.textContent || "").join("\n");
  const rest = () => d.documentElement.classList.contains("gm-rest");
  const hide = (v) => { Object.defineProperty(d, "hidden", { configurable: true, get: () => v }); d.dispatchEvent(new w.Event("visibilitychange")); };
  const touch = () => d.dispatchEvent(new w.Event("pointerdown", { bubbles: true }));

  ok("the stylesheet pauses the stars under html.gm-rest",
    /html\.gm-rest\s+\.gm-star\s*\{[^}]*animation-play-state\s*:\s*paused/.test(css()));
  ok("the stars are awake at first", !rest());
  w.gmRestNow();
  ok("gmRestNow puts them to rest at once", rest());
  touch();
  ok("a touch wakes them", !rest());
  hide(true);
  ok("a hidden tab puts them to rest", rest());
  hide(false);
  touch();
  ok("back again with a touch wakes them", !rest());
  console.log("x3_05 the stars rest: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
