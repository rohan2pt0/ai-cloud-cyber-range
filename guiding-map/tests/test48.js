// v48: plain words on the main tabs (calm, write plainly). A person sees "measure", "quarterly goal",
// "main goal" and "spending plan", never the abbreviations; headings are sentence case, not shouting;
// and no research citation (an author, a year, a forum) is left in the visible text.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, text = () => d.getElementById("sections").textContent.replace(/\s+/g, " ");
  const tabs = ["map", "all", "score", "plan", "money", "career", "book", "commit"];
  tabs.forEach(t => {
    w.goTab(t);
    const txt = text();
    ["KPI", "OKR", "KGI", "CSP"].forEach(a => ok(t + ": no \\b" + a + "\\b", !new RegExp("\\b" + a + "\\b").test(txt), txt.slice(0, 240)));
    const shout = txt.match(/\b[A-Z]{6,}\b/g) || [];
    ok(t + ": no run of 6+ capital letters", shout.length === 0, [...new Set(shout)].join(", "));
    ok(t + ": no year citation", !/\((?:19|20)\d{2}\)/.test(txt), (txt.match(/\((?:19|20)\d{2}\)/g) || []).join(", "));
  });
  console.log("test48 plain words: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
