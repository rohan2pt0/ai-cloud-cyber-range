// v116: what we must earn (owner, 2026-11-15: from my figures, how much must we earn to sustain ourselves with inflation,
// and which expenses to cut). Worked by hand: spending 70,000 + EMI 30,000 at a 20% saving = 1,25,000 a month take-home;
// at 6% inflation, 10 years on = 1,25,000 x 1.06^10 = 2,23,856, shown as 2,24,000. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1988-02-02", gross: 200000, net: 150000, psal: 0, exp: 70000, tsav: 20, sav: 900000, nw: 3000000,
  kids: [], loans: [{ name: "Fake loan", emi: 30000, remaining: 2000000, rate: 8.5, tenure: 120 }], example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, card = () => d.querySelector(".gm-needs");
  w.goTab("money");
  let r = w.gmNeedsCalc();
  ok("needed take-home now = (spending + EMIs) / (1 - saving) = 1,25,000", r && r.now === 125000, JSON.stringify(r));
  ok("10 years at 6% = 2,24,000", r && r.y10 === 224000, r && r.y10);
  ok("the card shows on Money, on track (emerald) with 1,50,000 coming in", !!card() && !!card().querySelector(".sx-state-good") && /on track/.test(card().textContent), card() && card().textContent);
  w.eval("P.net=120000;store('sovP',P);"); w.goTab("money");
  ok("with 1,20,000 coming in it is close: short by Rs 5,000 (amber)", /short by Rs 5,000/.test(card().textContent) && !!card().querySelector(".sx-state-watch"), card().textContent);
  const day = new Date(Date.now() - 3 * 864e5).toISOString().slice(0, 10);
  const sp = [["Food delivery", 8000], ["Bills", 3000], ["Travel", 4000], ["Amazon", 2000], ["Insurance", 1500], ["Groceries", 6000]].map(x => ({ d: day, a: x[1], c: x[0], m: "fake" }));
  w.localStorage.setItem("gm_spend", JSON.stringify(sp)); w.goTab("money");
  ok("fixed and variable from the bank messages: Fixed Rs 4,500 · Variable Rs 20,000", /Fixed Rs 4,500/.test(card().textContent) && /Variable Rs 20,000/.test(card().textContent), card().textContent);
  ok("the largest variable cost carries one concrete cut", /Food delivery \(Rs 8,000\): Cook twice a week more/.test(card().textContent));
  w.gmNeedsInfl("40");
  ok("an impossible inflation figure is kept to 15%", JSON.parse(w.localStorage.getItem("gm_needs")).infl === 15);
  w.eval("P.example=true;");  w.goTab("money");
  ok("with example figures it asks for the person's own spending instead of guessing", /Add your monthly spending in your profile/.test(card().textContent));
  console.log("test116 what we must earn: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
