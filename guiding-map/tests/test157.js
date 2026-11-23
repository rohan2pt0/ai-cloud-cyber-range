// test157: each goal as a path up a mountain (owner 2026-11-23): the climber sits at the goal's grade along the trail, each key
// result is a camp (lit at 0.7, the OKR success bar), the summit flag flies at 1.0; nothing to enter. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), now = Date.now();
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false };
const st = { checked: {}, vals: {}, valsAt: {}, archived: [], pts: 0, daily: {}, wheel: null, commits: [], pdMatch: false, wheelBase: null, strengths: ["Security"],
  okrs: [{ o: "Make my money unshakeable", at: now, krs: [{ t: "Emergency fund from 2 to 6 months", b: 2, c: 4.5, g: 6, v: 0.6, at: now }, { t: "Close the card", v: 1, at: now }] }] };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("sovS", JSON.stringify(st)); w.localStorage.setItem("gm_simple", "false");
    w.localStorage.setItem("gm_mine_done", "true"); w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("okr"); w.renderAll();
  const m = d.querySelector(".okr-card .gm-mtn");
  ok("each goal card shows its mountain", !!m, (d.querySelector("#sections") || d.body).textContent.slice(0, 160));
  ok("the climber is placed at the grade and the camps are counted", m && /Goal climb: 80 percent of the way up, 1 of 2 camps reached/.test(m.getAttribute("aria-label")), m && m.getAttribute("aria-label"));
  ok("the summit flag turns gold only at 1.0", /data-gold="1"/.test(w.gmMountain(1, [])) && !/data-gold="1"/.test(w.gmMountain(0.5, [])));
  ok("nothing to enter on the mountain", m && !m.querySelector("input, button"));
  console.log("test157 mountain: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
