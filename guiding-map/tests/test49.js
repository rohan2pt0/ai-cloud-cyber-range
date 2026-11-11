// v49: accessible names (owner, 2026-11-11). The Wheel sliders and the fields a person meets in Ask, Commit,
// the Life Map and Career carry a plain-name aria-label, and no Career control nests another control inside it.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const ops = fs.readFileSync(path.join(__dirname, '..', 'ops.js'), 'utf8');
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  // Wheel: every slider says which area it scores
  w.goTab("wheel");
  const ranges = [...sec().querySelectorAll('input[type="range"]')];
  ok("Wheel renders its sliders", ranges.length === 8, String(ranges.length));
  ok("Wheel: every slider has a non-empty aria-label", ranges.length > 0 && ranges.every(i => (i.getAttribute("aria-label") || "").trim()), ranges.map(i => i.getAttribute("aria-label")).join("|"));
  ok("Wheel: a slider's label names its area and the scale", (ranges[0] && /Career, score 1 to 10/.test(ranges[0].getAttribute("aria-label") || "")), ranges[0] && ranges[0].getAttribute("aria-label"));
  // Ask: the estate address and key fields have names
  w.goTab("ask");
  const gw = d.getElementById("askGwIn"), key = d.getElementById("askKeyIn");
  ok("Ask: the estate address has an aria-label", gw && (gw.getAttribute("aria-label") || "").trim() === "Estate address", gw && gw.getAttribute("aria-label"));
  ok("Ask: the estate key has an aria-label", key && (key.getAttribute("aria-label") || "").trim() === "Estate key", key && key.getAttribute("aria-label"));
  // Commit: the deadline has a name
  w.goTab("commit");
  const dl = d.getElementById("c_dl");
  ok("Commit: the deadline has an aria-label", dl && (dl.getAttribute("aria-label") || "").trim() === "Deadline", dl && dl.getAttribute("aria-label"));
  // Life Map: the monthly take-home field has its visible label as its name
  w.goTab("life");
  const minc = [...sec().querySelectorAll("input")].filter(i => (i.getAttribute("onchange") || "").includes("gmLifeSet('minc'"));
  ok("Life Map: the monthly take-home field has an aria-label", minc.length > 0 && minc.every(i => (i.getAttribute("aria-label") || "").trim()), minc.map(i => i.getAttribute("aria-label")).join("|"));
  // Career: no control nests another control
  w.goTab("career");
  const nested = [...sec().querySelectorAll('[role="button"]')].filter(el => el.querySelector('input, button, [role="button"]'));
  ok("Career: no role=button control contains another control", nested.length === 0, nested.map(el => el.outerHTML.slice(0, 80)).join(" || "));
  // the out-of-storage alert points at the same gold backup button it names
  const alertLine = (ops.split("\n").find(l => l.includes("out of storage")) || "");
  ok("the storage alert names the gold backup button", /Save encrypted backup/.test(alertLine) && !/Export backup/.test(alertLine), alertLine.trim());
  console.log("test49 accessible labels: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
