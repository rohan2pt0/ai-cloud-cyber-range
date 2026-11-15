// v107: the Wheel folds what is already rated (owner, 2026-11-15: the biggest card on each tab must look its
// best, and the Wheel was a 1,700 px wall of eight ten-key trays). An area with a value is one closed <details>
// whose summary shows its score as a gemstone (low 1-4, watch 5-6, good 7-10); opening it shows the same ten
// keys. An unrated area still shows its keys straight away. Fake data only; S.wheel starts empty.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("wheel");
  ok("with no wheel values every area shows its ten keys", sec().querySelectorAll(".ws-tap").length === 80 && sec().querySelectorAll("details.ws-done").length === 0,
    sec().querySelectorAll(".ws-tap").length + " keys, " + sec().querySelectorAll("details.ws-done").length + " folded");
  w.whl(0, 3); w.whl(1, 8); w.goTab("wheel");
  const done = [...sec().querySelectorAll("details.ws-done")];
  ok("two rated areas fold into closed details", done.length === 2 && done.every(x => x.open === false), done.length + " folded, open=" + done.map(x => x.open).join(","));
  const gem0 = done[0] && done[0].querySelector(".ws-gem");
  ok("Career shows 3/10 as a low gemstone", !!gem0 && gem0.classList.contains("sx-state-low") && gem0.textContent === "3/10", gem0 && gem0.className + " " + gem0.textContent);
  const gem1 = done[1] && done[1].querySelector(".ws-gem");
  ok("Finances shows 8/10 as a good gemstone", !!gem1 && gem1.classList.contains("sx-state-good") && gem1.textContent === "8/10", gem1 && gem1.className + " " + gem1.textContent);
  if (done[0]) done[0].open = true;
  const taps = done[0] ? [...done[0].querySelectorAll(".ws-tap")] : [], on = taps.find(b => b.getAttribute("data-v") === "3");
  ok("opening a rated area shows its ten keys, with its score lit", taps.length === 10 && !!on && on.classList.contains("on"), taps.length + " keys, 3 on=" + (on && on.className));
  console.log("test107 wheel folds what is rated: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
