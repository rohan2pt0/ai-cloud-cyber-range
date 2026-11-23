// test160: people who matter, the season and festivals, and what-if (owner 2026-11-23). Fake data only; no network.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false, mine: { epf: 500000 } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage, soon = new Date(Date.now() + 5 * 864e5);
  // people who matter: asked once, then they come up by themselves
  ok("a person is added with a name, a day and a month", w.gmPeopleAdd("Asha Fake", soon.getMonth() + 1, soon.getDate()) && JSON.parse(ls.getItem("gm_people")).length === 1);
  ok("their birthday comes up, with no age said", w.gmComingUp().some(x => x.t === "Asha's birthday" && x.days === 5));
  ok("a bad month, a bad day or no name stores nothing", !w.gmPeopleAdd("X", 13, 1) && !w.gmPeopleAdd("X", 2, 30) && !w.gmPeopleAdd("  ", 1, 1) && w.gmPeople().length === 1);
  ok("a name cannot inject HTML", w.gmPeopleAdd("<img src=x onerror=alert(1)>", 1, 1) && !/<img/.test(w.gmComingUpHTML()));
  w.gmPeopleDel(1); w.gmPeopleDel(0); ok("removing works", w.gmPeople().length === 0);
  for (let i = 0; i < 45; i++) w.gmPeopleAdd("P" + i, 1, 1); ok("at most 40", w.gmPeople().length === 40); ls.removeItem("gm_people");
  // the season and a festival near
  ok("23 Nov, Local: post-monsoon and Guru Nanak's Birthday tomorrow", w.gmSeasonLine(new Date(2026, 10, 23)) === "Post-monsoon · Guru Nanak's Birthday tomorrow", w.gmSeasonLine(new Date(2026, 10, 23)));
  ok("15 Jul, Local: monsoon and no festival", w.gmSeasonLine(new Date(2027, 6, 15)) === "Monsoon");
  ls.setItem("gm_region", JSON.stringify("global"));
  ok("Global: temperate seasons, no Indian festival", w.gmSeasonLine(new Date(2026, 10, 23)) === "Autumn"); ls.removeItem("gm_region");
  w.goTab("today"); w.renderAll();
  ok("the greeting carries the line", !!d.querySelector(".gm-season"));
  // what if: one tap, nothing saved
  const before = JSON.stringify(Object.assign({}, ls));
  const r = w.gmWhatIf("spend10k"), q = w.gmWhatIf("raise10");
  ok("spending less raises the buffer, the saving rate and net worth", r && r.after.months > r.before.months && r.after.save > r.before.save && r.after.nw12 - r.before.nw12 === 120000, JSON.stringify(r));
  ok("a raise moves saving and net worth, not the buffer", q && q.after.save > q.before.save && q.after.months === q.before.months);
  const wi = d.querySelector(".gm-wi"); ok("Today shows What if, folded", !!wi && !wi.open);
  wi.querySelector(".gm-wi-chip").click();
  ok("one tap shows before and after", /→/.test(d.getElementById("gmWiOut").textContent) && /▲/.test(d.getElementById("gmWiOut").textContent));
  ok("nothing is saved", JSON.stringify(Object.assign({}, ls)) === before);
  console.log("test160 people, seasons, what-if: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); } process.exit(0);
}, 400);
