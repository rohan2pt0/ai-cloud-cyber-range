// v101: Life OS number tiles show their health in natural materials (owner, 2026-11-14: "all KPIs must show the status
// as per its progress: danger red, medium amber, safe green, in gradient and natural materials; a 0.5m buffer must show
// red"). Every KPI tile carries .sx-state-<state>, data-state and a word, so colour is never the only signal. A 0.5-month
// buffer is low; 4 months watch; 8 good. Today with nothing ticked is never guilt, and example numbers are never a status.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
function boot(life) {
  return new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.localStorage.setItem("sovP", JSON.stringify(prof));
      w.localStorage.setItem("gm_simple", "false");
      if (life) w.localStorage.setItem("gm_life", JSON.stringify(life));
      w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
}
const doms = { low: boot({ fFixed: 100000, ef: "0.5" }), watch: boot({ fFixed: 100000, ef: "4" }), good: boot({ fFixed: 100000, ef: "8" }) };
setTimeout(() => {
  const tiles = (w) => [...w.document.querySelectorAll("#gmVitals > div")];
  const buffer = (w) => tiles(w).find(x => /Buffer|Runway/.test(x.textContent));
  const has = (x, state) => !!x && x.classList.contains("sx-state-" + state) && x.getAttribute("data-state") === state;
  const low = buffer(doms.low.window);
  ok("a 0.5-month buffer is low", has(low, "low"), low && low.className);
  ok("…and it says 'needs care' in words", !!low && /needs care/.test(low.textContent) && /needs care/.test(low.getAttribute("aria-label") || ""));
  const watch = buffer(doms.watch.window);
  ok("a 4-month buffer is watch", has(watch, "watch"), watch && watch.className);
  ok("…and it says 'building'", !!watch && /building/.test(watch.textContent));
  const good = buffer(doms.good.window);
  ok("an 8-month buffer is good", has(good, "good"), good && good.className);
  ok("…and it says 'strong'", !!good && /strong/.test(good.textContent));
  // Today with nothing ticked: never guilt before the day is over.
  const today = tiles(doms.low.window).find(x => /^Today:/.test(x.getAttribute("aria-label") || ""));
  ok("Today with nothing ticked has no state", !!today && !/sx-state/.test(today.className) && !today.getAttribute("data-state"), today && today.className);
  // Example numbers are not the person's: no status.
  const ex = doms.good.window; ex.gmTplLife();
  ok("example data raises no status", tiles(ex).every(x => !/sx-state/.test(x.className) && !x.getAttribute("data-state")),
    tiles(ex).map(x => x.className).join(" | "));
  console.log("test101 number tiles in natural materials: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
