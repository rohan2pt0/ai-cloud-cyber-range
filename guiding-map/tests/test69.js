// v69: the Health Cal hero names the next check-up in full from the family calendar ("Family health Q4: closure"), form
// labels read in sentence case, and the Guides search box looks like a field: a visible border, rounded, card coloured.
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
  // 1. the Health Cal hero shows the next check-up's full family-calendar name.
  w.goTab("cal");
  const hero = sec().querySelector(".gm-hero");
  const heroText = hero ? hero.textContent : "";
  ok("Health Cal hero names the next check-up in full", /Family health Q[1-4]:\s*(blood work|dental and vision|children and parents|closure)/i.test(heroText), heroText);
  ok("Health Cal hero carries the quarter", /Q[1-4]/.test(heroText), heroText);
  // 2. form labels are sentence case: no uppercase transform, no letter-spacing.
  const label = d.querySelector(".f-label");
  ok("a form label exists to style", !!label);
  const ls = label ? w.getComputedStyle(label) : {};
  ok(".f-label no longer forces uppercase", ls.textTransform === "none", ls.textTransform);
  // 3. the Guides search box has a visible 1px border, radius, card background and touch height.
  w.goTab("guide");
  const search = sec().querySelector('input[aria-label="Search guides"]');
  ok("the Guides screen has its search box", !!search);
  const ss = search ? w.getComputedStyle(search) : {};
  ok("the Guides search box has a visible border", !!search && (search.style.border || ss.borderTopWidth === "1px"), search && (search.style.border || ss.borderTopWidth));
  ok("the Guides search box border uses the border colour", !!search && /var\(--border\)/.test(search.style.border || ss.border || ""), search && (search.style.border || ss.border));
  ok("the Guides search box is rounded and card coloured", !!search && /10px/.test(search.style.borderRadius || ss.borderRadius) && /var\(--card\)/.test(search.style.background || ss.background || ""), search && (search.style.borderRadius + " / " + search.style.background));
  ok("the Guides search box is comfortable to tap", !!search && /44px/.test(search.style.minHeight || ss.minHeight), search && (search.style.minHeight || ss.minHeight));
  console.log("test69 Life OS polish: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
