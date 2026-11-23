// test161: last month, in review (owner 2026-11-23). Fake data only; no network.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, kids: [], ret: 60, tsav: 20, example: false, mine: { epf: 500000 } };
let nowMs = new Date(2026, 10, 3, 10, 0, 0).getTime();   // 3 Nov 2026
const daily = {}; for (let d = 1; d <= 20; d++) daily["2026-10-" + (d < 10 ? "0" : "") + d] = ["ex"];
const okrs = [{ o: "Fake goal", at: new Date(2026, 8, 1).getTime(), krs: [{ t: "Step", v: 0.5, at: new Date(2026, 9, 12).getTime() }] }];
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    const RD = w.Date; function FD(...a) { return a.length ? new RD(...a) : new RD(nowMs); }
    FD.prototype = RD.prototype; FD.now = () => nowMs; FD.parse = RD.parse; FD.UTC = RD.UTC; w.Date = FD;
    w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true");
    w.localStorage.setItem("gm_spendcheck", JSON.stringify({ "2026-09": { me: 100000 }, "2026-10": { me: 110000, vs: 40000 } }));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage;
  const ib = () => JSON.parse(ls.getItem("gm_inbox") || "[]");
  ok("gmMonthAAR exists", typeof w.gmMonthAAR === "function");
  w.eval("S.daily=" + JSON.stringify(daily) + ";S.okrs=" + JSON.stringify(okrs) + ";");
  const a = w.gmMonthAAR();
  ok("daily three counted from last month", a.went.concat(a.slipped).some(x => /kept on 20 of 31 days/.test(x)), JSON.stringify(a));
  ok("saving rate comes from the check-in", a.went.concat(a.slipped).some(x => /saved \d+% of your income/.test(x)), JSON.stringify(a));
  ok("a goal that moved is named", a.went.some(x => /1 of 1 goal moved/.test(x)), JSON.stringify(a));
  ok("exactly three choices", Array.isArray(a.choices) && a.choices.length === 3);
  w.goTab("today"); w.renderAll();
  const c = d.querySelector(".gm-aar");
  ok("Today shows the card on day 3", !!c && /Last month, in review/.test(c.textContent));
  const n0 = ib().length;
  d.querySelector(".gm-aar-pick").click();
  const all = ib();
  ok("one pick adds one inbox item with a due date", all.length === n0 + 1 && /^\d{4}-\d{2}-\d{2}$/.test(all[0].due), JSON.stringify(all[0]));
  ok("the card folds and is stored by month", !d.querySelector(".gm-aar") && JSON.parse(ls.getItem("gm_aar_seen"))["2026-11"] === "picked");
  ls.removeItem("gm_aar_seen"); w.renderAll(); ok("the card is back before a choice", !!d.querySelector(".gm-aar"));
  d.querySelector(".gm-aar .gm-aar-ok").click();
  ok("Got it folds it with no new inbox item", !d.querySelector(".gm-aar") && ib().length === n0 + 1);
  ls.removeItem("gm_aar_seen"); nowMs = new Date(2026, 10, 9, 10, 0, 0).getTime(); w.renderAll();
  ok("not shown after day 7", !d.querySelector(".gm-aar"));
  console.log("test161 last month in review: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  FAIL " + x)); process.exit(1); } process.exit(0);
}, 400);
