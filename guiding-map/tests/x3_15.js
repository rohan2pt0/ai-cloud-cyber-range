// x3_15: one main landmark (owner 2026-11-18; experience-v3 fix 15 of 20). The page has a skip link and a nav but no
// main landmark, so a screen reader cannot jump to the content. Exactly one element is the main landmark, it contains
// #sections, it can take focus (tabindex="-1"), and the skip link points at it. Fake data only.
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
  const w = dom.window, d = w.document, sections = d.getElementById("sections");
  const mains = [...d.querySelectorAll('[role="main"], main')];
  ok("there is exactly one main landmark", mains.length === 1, mains.length + " found");
  const main = mains[0];
  if (main) {
    ok("it contains #sections", !!sections && main.contains(sections));
    ok("it can take focus (tabindex=-1)", main.getAttribute("tabindex") === "-1", main.getAttribute("tabindex"));
    const sk = d.querySelector("a.skip");
    ok("the skip link exists", !!sk);
    ok("the skip link points at the main landmark", !!sk && !!main.id && sk.getAttribute("href") === "#" + main.id,
      (sk && sk.getAttribute("href")) + " vs #" + main.id);
  }
  console.log("x3_15 one main landmark: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
