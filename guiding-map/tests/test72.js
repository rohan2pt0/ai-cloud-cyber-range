// v72: every progress-bar fill draws one refreshing teal gradient (.gm-fill), not a per-bar inline
// colour. The Growth tab's pillar-leverage bars and the daily-routine bar share it, and no progress
// fill keeps an inline navy background.
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
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("growth");
  const lev = [...sec().querySelectorAll(".afp-bar > div")];
  ok("Growth has pillar-leverage fills", lev.length > 0, lev.length);
  ok("Every pillar-leverage fill uses gm-fill", lev.every(x => x.classList.contains("gm-fill")), lev.map(x => x.className).join("|"));
  const rb = d.getElementById("routine-fill");
  ok("The daily-routine bar exists", !!rb);
  ok("The daily-routine bar uses gm-fill", !!rb && rb.classList.contains("gm-fill"), rb && rb.className);
  ok("The daily-routine bar is 8px tall", !!rb && (rb.getAttribute("style") || "").indexOf("height:8px") >= 0, rb && rb.getAttribute("style"));
  const navyFill = [...sec().querySelectorAll("[style]")].filter(x => {
    const s = x.getAttribute("style") || "";
    return s.indexOf("width:") >= 0 && s.indexOf("background:var(--navy)") >= 0;
  });
  ok("No progress fill keeps an inline navy background", navyFill.length === 0, navyFill.map(x => x.getAttribute("style")).join("|"));
  console.log("test72 one teal gradient for progress fills: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
