// v132: a resting door wakes by itself when the person's own data says it is needed (queue friction-meter, slice 3 of 5).
// A child's birthday in the next 7 days wakes Kids; tax season (January to March, India) wakes Money. A woken door says why.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const pad = n => ("0" + n).slice(-2);
const ymdD = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
let nowMs = new Date(2026, 1, 15, 12, 0, 0).getTime();   // 15 February 2026, tax season in India
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [{ name: "Test Kid", dob: "2020-02-18" }], loans: [], ret: 55, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    const RD = w.Date;
    function FD(...a) { return a.length ? new RD(...a) : new RD(nowMs); }
    FD.prototype = RD.prototype; FD.now = () => nowMs; FD.parse = RD.parse; FD.UTC = RD.UTC;
    w.Date = FD;
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_first_open", JSON.stringify("2025-08-01"));
    w.localStorage.setItem("gm_use_since", JSON.stringify("2025-08-01"));
    w.localStorage.setItem("gm_use", JSON.stringify({}));   // no use at all: every resting door would rest
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const sheet = () => d.getElementById("gmMoreSheet");
  const idsIn = sel => Array.from(sheet().querySelectorAll(sel)).map(b => b.getAttribute("data-tab"));
  const activeIds = () => idsIn(".gm-more-all > .gm-more-g > button[data-tab]");
  const resting = () => sheet().querySelector(".gm-more-all .gm-more-rest");
  const restingIds = () => resting() ? idsIn(".gm-more-all .gm-more-rest button[data-tab]") : [];
  const tile = id => sheet().querySelector('button[data-tab="' + id + '"]');
  const note = id => { const b = tile(id), n = b && b.querySelector(".gm-new"); return n ? n.textContent : ""; };

  // 15 February 2026: a birthday in 3 days, tax season, India.
  w.gmNavMore(true);
  ok("a child's birthday in the next 7 days wakes Kids out of Resting",
    activeIds().indexOf("kids") > -1 && restingIds().indexOf("kids") < 0,
    "active " + activeIds().join(",") + " resting " + restingIds().join(","));
  ok("the woken Kids door says why: Birthday soon", note("kids") === "Birthday soon", JSON.stringify(note("kids")));
  ok("tax season keeps Money open", !!tile("money") && restingIds().indexOf("money") < 0, restingIds().join(","));
  ok("the woken Money door says why: Tax season", note("money") === "Tax season", JSON.stringify(note("money")));

  // The same day with the region set to Global: a country's tax season does not wake it.
  w.localStorage.setItem("gm_region", JSON.stringify("global"));
  w.gmNavMore(true);
  ok("tax season only wakes Money in India", note("money") === "", JSON.stringify(note("money")));
  w.localStorage.setItem("gm_region", JSON.stringify("local"));

  // 17 November 2026: outside both windows, Kids rests as before and no door says it was woken.
  nowMs = new Date(2026, 10, 17, 12, 0, 0).getTime();
  w.P.kids[0].dob = "2020-11-01";   // 16 days away
  w.gmNavMore(true);
  ok("outside the birthday window Kids rests as before",
    restingIds().indexOf("kids") > -1 && activeIds().indexOf("kids") < 0,
    "active " + activeIds().join(",") + " resting " + restingIds().join(","));
  ok("outside the birthday window Kids has no wake note", note("kids") === "", JSON.stringify(note("kids")));
  ok("outside tax season Money has no wake note", note("money") === "", JSON.stringify(note("money")));

  console.log("test132 More menu wakes by need: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
