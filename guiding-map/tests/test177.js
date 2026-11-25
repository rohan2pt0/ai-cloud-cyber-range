// test177: due-list-feed (superapp plan, owner 2026-11-25): the Money health register's policy premiums and maturities join the one
// Coming up list, with no second reminders screen. A premium shows on the next anniversary of p.start while premiums are payable;
// a savings policy shows "Matures" in its maturity year; nothing shows once the premium-paying term ends, nor for an applied row.
// Plain words only; a damaged row never throws. Fake data only. Start dates sit on the next anniversary so the 45-day window is
// exercised on any run day (a fixed 10 March and 1 August cannot both fall inside it).
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), A = new Date(t.getFullYear(), t.getMonth(), t.getDate() + 20);
const isoD = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
const started = (years) => isoD(new Date(A.getFullYear() - years, A.getMonth(), A.getDate()));
const prof = { name: "Fake Person", dob: isoD(new Date(t.getFullYear() - 38, t.getMonth(), t.getDate())), country: "India", cur: "INR", gross: 180000, net: 120000,
  exp: 50000, sav: 300000, ret: 60, tsav: 20, example: false, earners: 1, loans: [] };
const mh = { policies: [
  { type: "endow", who: "me", sa: 1000000, prem: 24000, start: started(7), term: 20, ppt: 15 },
  { type: "health", who: "family", sa: 500000, prem: 18000, start: started(2) },
  { type: "pli", who: "me", sa: 500000, prem: 30000, start: started(20), term: 20, ppt: 20 },
  { type: "endow", who: "me", sa: 500000, prem: 20000, start: started(16), term: 20, ppt: 15 },
  { type: "term", who: "me", sa: 10000000, prem: 12000, start: started(1), term: 20, ppt: 20, st: "applied" }],
  funds: [], macro: {}, alloc: {}, bench: {} };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, L = w.gmComingUp(), pol = L.filter(x => x.kind === "policy");
  const premium = pol.filter(x => /Premium due/.test(x.t));

  // each policy on its next anniversary, while premiums are payable
  ok("two premiums due: the endowment and the health policy", premium.length === 2, JSON.stringify(pol.map(x => [x.t, x.s])));
  ok("the endowment's premium is ₹24,000 with one plain next step", premium.some(x => /24,000/.test(x.s) && /Pay from the buffer, not a card/.test(x.s)), JSON.stringify(premium));
  ok("the health policy's premium is ₹18,000, with the same next step", premium.some(x => /18,000/.test(x.s) && /Pay from the buffer, not a card/.test(x.s)), JSON.stringify(premium));
  ok("both fall on the next anniversary, inside the 45-day window", premium.length === 2 && premium.every(x => x.days === 20), JSON.stringify(premium.map(x => x.days)));

  // a savings policy in its maturity year
  const mat = pol.filter(x => /Matures/.test(x.t));
  ok("a savings policy matures, on its own date", mat.length === 1 && mat[0].days === 20, JSON.stringify(mat.map(x => [x.t, x.s, x.days])));

  // nothing after the premium-paying term ends, and nothing for an applied row
  ok("no premium after the premium-paying term ends", !premium.some(x => /20,000/.test(x.s)), JSON.stringify(premium.map(x => x.s)));
  ok("an applied term row shows nothing", !pol.some(x => /12,000/.test(x.s)), JSON.stringify(pol.map(x => x.s)));

  // plain words, no jargon, and never a broken number
  const text = pol.map(x => x.t + " " + x.s).join(" ");
  ok("plain words: no jargon on the list", !/ppt|premium-paying|premium paying|annuit|endowment|money-back|sum assured|ULIP|maturity value|policy number/i.test(text), text);
  ok("no NaN, Infinity or undefined on the list", !/NaN|Infinity|undefined/.test(text), text);
  ok("every policy item is inside the window the list already uses", pol.every(x => x.days <= 45 && isFinite(x.days)), JSON.stringify(pol.map(x => x.days)));

  // a damaged row never throws and never prints a broken number
  w.localStorage.setItem("gm_mhealth", JSON.stringify({ policies: [
    { type: "endow", prem: -5, start: "nope", term: "x", ppt: "y" }, { type: "bogus" }, null, "x",
    { type: "health", prem: "", start: "2024-13-99" }, { type: "endow", start: "2019-03-10", term: 20, ppt: 15, prem: 24000 }] }));
  let threw = "", L4 = [];
  try { L4 = w.gmComingUp(); } catch (er) { threw = String(er); }
  const pol4 = L4.filter(x => x.kind === "policy"), t4 = pol4.map(x => x.t + " " + x.s).join(" ");
  ok("damaged rows never throw", !threw, threw);
  ok("damaged rows: every day is a real number", L4.every(x => isFinite(x.days)) && pol4.every(x => x.days <= 45), JSON.stringify(L4.map(x => x.days)));
  ok("damaged rows: no NaN or Infinity", !/NaN|Infinity|undefined/.test(t4), t4);

  console.log("test177 due-list feed: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
