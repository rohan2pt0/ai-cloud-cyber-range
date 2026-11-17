// v130: the More menu learns order and rest (queue friction-meter, slice 2 of 5). Doors the person uses come first;
// a door not opened for 45 days, or never used, rests at the end by itself, and one use brings it straight back.
// Nothing is asked of the person and nothing is sent.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const pad = n => ("0" + n).slice(-2);
const ymdD = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
const today = ymdD(new Date());
function ago(n) { const t = new Date(); t.setDate(t.getDate() - n); return ymdD(t); }
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const use = {
  "tab:kids": { l: today, d: [ago(1), ago(2), ago(3), ago(4), today] },
  "tab:arch": { l: today, d: [today] },
  "tab:book": { l: ago(60), d: [ago(60)] }
};
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_first_open", JSON.stringify(ago(90))); w.localStorage.setItem("gm_use_since", JSON.stringify(ago(90))); w.localStorage.setItem("gm_use", JSON.stringify(use));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const sheet = () => d.getElementById("gmMoreSheet");
  const activeIds = () => Array.from(sheet().querySelectorAll(".gm-more-all > .gm-more-g > button[data-tab]"))
    .map(b => b.getAttribute("data-tab"));
  const resting = () => sheet().querySelector(".gm-more-all .gm-more-rest");
  const restingIds = () => resting() ? Array.from(resting().querySelectorAll("button[data-tab]")).map(b => b.getAttribute("data-tab")) : [];

  w.gmNavMore(true);
  ok("the More sheet shows Everything else", !!sheet() && !!sheet().querySelector(".gm-more-all"));
  let a = activeIds();
  ok("with five recent days kids comes before arch in Everything else", a.indexOf("kids") > -1 && a.indexOf("arch") > -1 && a.indexOf("kids") < a.indexOf("arch"), a.join(","));
  ok("a tab last used over 45 days ago sits under Resting", restingIds().indexOf("book") > -1, restingIds().join(","));
  ok("a tab never used sits under Resting", restingIds().indexOf("cal") > -1, restingIds().join(","));
  ok("Resting names its count", !!resting() && resting().querySelector("summary").textContent.indexOf("Resting (" + restingIds().length + ")") === 0, resting() ? resting().querySelector("summary").textContent : "no Resting");
  ok("risk and deadlines never rest", restingIds().indexOf("risk") < 0 && restingIds().indexOf("deadlines") < 0, restingIds().join(","));

  w.goTab("book");
  w.gmNavMore(true);
  a = activeIds();
  ok("a resting door opened comes straight back out of Resting", a.indexOf("book") > -1 && restingIds().indexOf("book") < 0, "active " + a.join(",") + " resting " + restingIds().join(","));

  w.localStorage.setItem("gm_first_open", JSON.stringify(ago(10))); w.localStorage.setItem("gm_use_since", JSON.stringify(ago(10)));
  w.gmNavMore(false); w.gmNavMore(true);
  ok("nothing rests while the app is newer than 45 days", !resting(), resting() ? restingIds().join(",") : "none");
  ok("the unused door is shown, not hidden, in that grace period", activeIds().indexOf("cal") > -1, activeIds().join(","));

  // An existing person whose usage starts being learned today: nothing rests on day one, however old the app is.
  w.localStorage.setItem("gm_first_open", JSON.stringify(ago(300))); w.localStorage.setItem("gm_use_since", JSON.stringify(ago(0)));
  w.localStorage.removeItem("gm_more_order"); w.gmNavMore(true);
  ok("learning that began today rests nothing, however old the app", !resting(), resting() ? resting().textContent.slice(0, 80) : "");
  console.log("test130 More menu rest: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
