// v56: "Where the money goes" starts from the profile when the plan is empty, uses a validated categorical palette,
// and shows the meters as a healthy band with the value as a dot and a status word, never a filled red track.
// Fake data only: net 200000, spending 90000, one loan EMI 20000, gm_life left empty.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 0, parents: false,
  kids: [], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("life");
  const rows = () => [...sec().querySelectorAll(".flowrow")].map(r => ({
    name: (r.querySelector(".flowname") || {}).textContent || "", amt: (r.querySelector(".flowamt") || {}).textContent || "",
    pc: (r.querySelector(".flowpc") || {}).textContent || "", from: /from your profile/.test(r.textContent)
  }));
  const text = () => sec().textContent;
  ok("fixed costs come from the profile (spending + loan EMI = 110000)", rows().some(r => /Fixed costs/.test(r.name) && /1,10,000/.test(r.amt)), JSON.stringify(rows()));
  ok("saving comes from the profile (net - spending - EMI = 90000)", rows().some(r => /Saving/.test(r.name) && /90,000/.test(r.amt)), JSON.stringify(rows()));
  ok("those two numbers are marked 'from your profile'", rows().filter(r => r.from && /Fixed costs|Saving/.test(r.name)).length === 2, JSON.stringify(rows()));
  const g = rows().find(r => /Guilt-free/.test(r.name));
  ok("guilt-free is shown and is not 100%", !!g && !/100%/.test(g.pc), g && JSON.stringify(g));
  ok("the status words are present, with words not colour alone", /Healthy|In range/.test(text()) && /Low/.test(text()), text().slice(0, 400));
  const flow = sec().querySelector(".flowbar");
  ok("no purple in the flow", !!flow && !/#6d28d9|purple|#7c3aed|#8b5cf6|#a855f7/i.test(flow.outerHTML), flow && flow.outerHTML);
  // no income at all: an empty state, not a 100% guilt-free bar
  w.localStorage.setItem("gm_life", JSON.stringify({ inc: "24" }));
  w.eval("P.net = 0");
  w.goTab("life");
  ok("with no income the empty state names the one next step", /Add your take-home to see where it goes/.test(text()), text().slice(0, 300));
  ok("…and no bar is drawn", !sec().querySelector(".flowbar"));
  console.log("test56 money flow: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
