// v61: Life OS visual standard, slice 5. The Stack and Guides open with one calm hero tile,
// the explanation is folded under "How this works", and the Stack shows one "Next" status.
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
    ok(label + ": the hero opens the tab, before its first card", !!hero && s.firstElementChild === hero, s.firstElementChild && s.firstElementChild.className);
    const how = s.querySelector("details.gm-how");
    ok(label + ": the explanation is folded, closed, under How this works", !!how && !how.open && /How this works/.test(how.querySelector("summary").textContent));
    ok(label + ": the hero has no NaN or undefined", !!hero && !/NaN|undefined/.test(hero.textContent), hero && hero.textContent);
    return s;
  };

  const stack = checkTab("stack", "Stack");
  const nextStatus = [...stack.querySelectorAll(".gm-status")].filter(x => x.textContent.trim() === "Next");
  ok("Stack: exactly one Next status", nextStatus.length === 1, stack.querySelectorAll(".gm-status").length + " statuses");
  ok("Stack: the hero shows the share of the whole stack", /%/.test((stack.querySelector(".gm-hero-u") || {}).textContent || ""));

  const guide = checkTab("guide", "Guides");
  const search = guide.querySelector('input[aria-label="Search guides"]');
  ok("Guides: the search box is labelled Search guides", !!search);
  ok("Guides: the hero counts the how-tos", /how-tos/.test((guide.querySelector(".gm-hero-u") || {}).textContent || ""));

  console.log("test61 calm stack and guides: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
