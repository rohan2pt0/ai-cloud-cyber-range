// test152: one money model (owner 2026-11-20: "the numbers don't tally"). Income, spend, saving rate, buffer, net worth and
// term cover are worked out once (gmMoney) and every screen shows the same figures. Fake round numbers only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const prof = { name: "Fake", dob: "1989-05-15", pname: "Sam", pdob: "1994-02-01", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000,
  nw: 0, kids: [], ret: 60, tsav: 20, example: false, earners: 2, rent1: 30000, rent2: 0,
  loans: [{ type: "Home Loan", remaining: 5000000, rate: 7.5, emi: 40000, tenure: 300 }, { type: "Personal Loan", remaining: 80000, rate: 10, emi: 80000, tenure: 1 }],
  mine: { epf: 200000, nps: 1000000, term: 15000000 }, partner: { net: 50000, epf: 500000, term: 10000000 },
  work: { kind: "contract", from: "2027-01-01" }, pwork: { kind: "permanent", from: "2027-01-01" } };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage;
  w.gmFixedAdd(0); const rb = JSON.parse(ls.getItem("gm_fixed"))[0]; w.gmFixedSet(rb.id, "amt", "30000");   // a "Rent" bill
  const r = w.gmRealSpend();
  ok("a loan with 1 month left is not a lasting bill", r.ending === 80000 && r.fixed === 70000, JSON.stringify(r));
  ok("spend = fixed 70,000 + variable 50,000 (spending 80,000 + lasting EMI 40,000 less the bills)", r.total === 120000 && r.variable === 50000, JSON.stringify(r));
  const M = w.gmMoney();
  ok("income = both pays + rent less one empty month a year", M.salary === 170000 && M.rentPlan === 27500 && M.income === 197500, JSON.stringify(M));
  ok("saving rate = (income - spend) / income", M.save === 39, M.save);
  ok("buffer: savings over spend less the pay that stays and the rent", Math.abs(M.buffer.months - 500000 / 42500) < 1e-9 && M.buffer.target === 12 && M.buffer.state === "watch", M.buffer.months);
  ok("net worth = investments + savings - loans other than the home loan", M.invest === 1700000 && M.netWorth === 2120000, M.netWorth);
  ok("term need = 10 years of pay before tax + loans for the first earner", w.gmTermNeed(180000, true) === 21600000 + 5080000 && w.gmTermNeed(50000, false) === 6000000);
  ok("the age ladder is Fidelity's, smooth: 1x at 30, 2.4x at 37, 4.5x at 45, 10x at 67", w.gmRetMult(30) === 1 && w.gmRetMult(37) === 2.4 && w.gmRetMult(45) === 4.5 && w.gmRetMult(67) === 10, [w.gmRetMult(30), w.gmRetMult(37)].join());
  ok("a home loan with no flat value is left out with the flat, and asked for", M.loans.needVal === true && M.loans.homeCounted === 0);
  w.renderAll();
  const tiles = d.getElementById("gmVitals") ? d.getElementById("gmVitals").textContent : w.gmVitalsHTML();
  ok("the Saving tile shows the same 39%", /39%\s*Saving/.test(tiles.replace(/<[^>]+>/g, " ")), tiles.slice(0, 200));
  ok("the buffer tile shows the same 11.8 months", /11\.8m/.test(tiles), tiles.slice(0, 200));
  const n = w.gmNeedsCalc();
  ok("What we must earn uses the same spend and income", n.now === 150000 && n.cur === 197500, JSON.stringify(n));
  w.goTab("money"); w.renderAll();
  const card = w.gmSpendCard();
  ok("the ending loan is said plainly", /loan ending within 3 months \(₹80,000 a month\)/i.test(card));
  ok("a Rent bill beside rent coming in asks once", /class="gm-rentq"/.test(card));
  w.gmRentQ("in", rb.id);
  ok("rent that comes in is not also a bill", w.gmRealSpend().fixed === 40000 && !/gm-rentq/.test(w.gmSpendCard()) && ls.getItem("gm_rent_q") === '"in"', w.gmRealSpend().fixed);
  w.goTab("life"); w.renderAll();
  const life = (d.querySelector("#sections") || d.body).textContent;
  ok("the Life map shows income with rent and the same net worth", /₹27,60,000 a year, both pays before tax/.test(life) && /₹21,20,000 \(investments/.test(life), life.slice(life.indexOf("Household annual"), life.indexOf("Household annual") + 160));
  ok("the Life map term line uses the same rule", /term cover\??\s*should be ₹2,66,80,000/.test(life), life.slice(life.indexOf("term cover"), life.indexOf("term cover") + 200));
  // the family lives on rent and the home loan bought the let-out flat: its value counts, and so does its loan
  ls.setItem("gm_props", JSON.stringify([{ n: "Fake flat", use: "letout", val: "80", rent: "30000", loan: "", vac: "1" }]));
  const M2 = w.gmMoney();
  ok("a let-out flat's value counts and its home loan is subtracted", M2.loans.letVal === 8000000 && M2.loans.homeCounted === 5000000 && M2.netWorth === 1700000 + 500000 + 3000000 - 80000, M2.netWorth);
  console.log("PASS " + P + " FAIL " + F); e.forEach(x => console.log("  FAIL: " + x)); process.exit(F ? 1 : 0);
}, 400);
