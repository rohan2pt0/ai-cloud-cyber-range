// v108: impossible numbers can never be saved (owner, 2026-11-15: "a person's age can't be 200, salary can't be minus...
// humans make the mistake, not the machine"). The one door every profile write passes fixes the value and says why.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const pad = n => (n < 10 ? "0" : "") + n;
const ymd = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
const now = new Date();
const dob40 = ymd(new Date(now.getFullYear() - 40, now.getMonth(), now.getDate()));
const tomorrow = ymd(new Date(now.getTime() + 864e5));
const base = { name: "Fake", dob: dob40, country: "India", city: "", cur: "INR", gross: 100000, net: 80000, exp: 60000,
  sav: 100000, nw: 1000000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1988-01-01", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2015-03-01" }], loans: [{ type: "Fake Loan", remaining: 100000, rate: 8.5, emi: 5000, tenure: 120 }],
  ret: 60, tsav: 20, dream: "Fake dream", goal: "Fake goal", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(base));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, G = k => JSON.parse(w.localStorage.getItem(k) || "null");
  const put = (patch) => { const p = Object.assign({}, base, patch); w.gmGuardNotes = [];
    w.eval("P = " + JSON.stringify(p) + "; store('sovP', P);"); return G("sovP"); };
  const notes = () => w.gmGuardNotes || [];

  let a = put({ dob: "1826-01-01" });
  ok("an impossible birth date is cleared", a.dob === "", a.dob);
  ok("…and the note names the age", notes().some(n => /age of \d+/.test(n)), notes().join(" | "));

  a = put({ gross: 50000, net: 90000 });
  ok("take-home can never exceed gross", a.net === 50000, a.net);
  ok("…and says so plainly", notes().some(n => /Take-home was more than gross/.test(n)), notes().join(" | "));

  a = put({ exp: -2000 });
  ok("a negative spending figure becomes 0", a.exp === 0, a.exp);

  a = put({ ret: 20 });
  ok("retirement cannot be before the next birthday", a.ret === 41, a.ret);

  a = put({ loans: [{ type: "Fake Loan", remaining: -5, rate: 85, emi: 100, tenure: 900 }] });
  ok("a loan rate is capped at 60 with a note", a.loans[0].rate === 60 && notes().some(n => /Interest rate 85% looks like a typo/.test(n)), JSON.stringify(a.loans[0]));
  ok("loan remaining is never negative and tenure never over 480 months", a.loans[0].remaining === 0 && a.loans[0].tenure === 480 && a.loans[0].emi === 100, JSON.stringify(a.loans[0]));

  a = put({ kids: [{ name: "FakeKid", dob: tomorrow }] });
  ok("a child born in the future is cleared", a.kids[0].dob === "", a.kids[0].dob);

  a = put({ nw: -300000 });
  ok("net worth may be negative", a.nw === -300000, a.nw);

  a = put({});
  ok("a normal profile passes unchanged", a.dob === base.dob && a.gross === base.gross && a.net === base.net && a.ret === base.ret && a.loans[0].rate === 8.5, JSON.stringify(a.loans[0]));
  ok("…with no notes", notes().length === 0, notes().join(" | "));

  console.log("test108 profile guards: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
