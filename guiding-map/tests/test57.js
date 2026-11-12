// v57: Life OS visual standard, slice 1. Risk Shield and Pillars open with one calm hero tile, the explanation
// is folded under "How this works", and status is a sentence-case dot plus word, never a tracked-out pill.
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
  const checkTab = (id, label) => {
    w.goTab(id);
    const s = sec().querySelector(".section.active");
    const hero = s.querySelector(".gm-hero");
    ok(label + ": exactly one hero tile", s.querySelectorAll(".gm-hero").length === 1);
    ok(label + ": the hero is the first thing in the section", !!hero && s.firstElementChild === hero, s.firstElementChild && s.firstElementChild.className);
    const how = s.querySelector("details.gm-how");
    ok(label + ": the explanation is folded, closed, under How this works", !!how && !how.open && /How this works/.test(how.querySelector("summary").textContent));
    ok(label + ": no status is shouted in capitals", !/\b(EXPOSED|NOT STARTED)\b/.test(s.textContent), s.textContent.slice(0, 200));
    const words = [...s.querySelectorAll(".gm-status")].map(x => x.textContent.trim());
    ok(label + ": status words are sentence case", words.length > 0 && words.every(x => /^(On track|Building|Not started|Exposed|Covered|Partial)$/.test(x)), words.join(","));
    const dots = [...s.querySelectorAll(".gm-status .gm-dot")];
    ok(label + ": every status carries a coloured dot", dots.length === words.length && dots.every(x => /var\(--(red|amber|green|muted)\)/.test(x.getAttribute("style") || "")), dots.map(x => x.getAttribute("style")).join(","));
  };
  checkTab("risk", "Risk Shield");
  checkTab("all", "Pillars");
  console.log("test57 calm risk and pillars: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
