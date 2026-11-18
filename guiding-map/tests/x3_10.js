// x3_10: the title names the view (owner 2026-11-18; queue experience-v3, fix 10 of 20). The browser tab, history and
// a screen reader should hear the tab, not a fixed "The Guiding Map": after goTab('today') the title is "Today · Life OS",
// and after goTab('okr') it starts with that tab's label from TABS. A chosen language uses its translated label.
// jsdom, fake data only.
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
  w.goTab("today");
  ok("the title names Today and the app", d.title === "Today · Life OS", JSON.stringify(d.title));
  w.goTab("okr");
  const label = ((w.TABS || []).filter(t => t[0] === "okr")[0] || [])[1] || "";
  ok("the title starts with the tab's label from TABS", label && d.title.indexOf(label) === 0, JSON.stringify(d.title) + " vs " + JSON.stringify(label));
  w.gmSetLang("hi");
  w.goTab("today");
  ok("a chosen language uses the translated label", d.title === "आज · Life OS", JSON.stringify(d.title));
  console.log("x3_10 title names the view: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
