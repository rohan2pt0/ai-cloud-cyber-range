// v55: the hero cards look premium (a layered glow over deep navy), and headings are sentence case, not tracked-out capitals.
// Fake data only; the stylesheet is checked as text so the look cannot drift back.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const rule = (sel) => { const m = html.match(new RegExp("\\" + sel + "\\{([^}]*)\\}")); return m ? m[1] : ""; };
const ns = rule(".ns-card");
ok("the antifragility card has a soft radial glow", /radial-gradient/.test(ns), ns);
ok("the glow sits over deep navy to midnight teal", /#0b1a2e/.test(ns) && /#0f2f3a/.test(ns), ns);
ok("the card keeps a 1px inner highlight", /inset[^;]*rgba\(255,255,255,\.06\)/.test(ns), ns);
ok("the card keeps the gold border", /2px solid var\(--gold\)/.test(ns), ns);
const ey = rule(".ns-ey");
ok(".ns-ey is sentence case, not tracked-out capitals", !/text-transform\s*:\s*uppercase/.test(ey) && /font-size:12px/.test(ey) && /letter-spacing:\s*(0|\.2px)/.test(ey), ey);
const ct = rule(".cat-t");
ok(".cat-t is sentence case and readable", !/text-transform\s*:\s*uppercase/.test(ct) && /font-size:13px/.test(ct) && /letter-spacing:\s*(0|\.2px)/.test(ct), ct);
const nb = rule(".ns-band");
ok(".ns-band is not tracked out", !/text-transform\s*:\s*uppercase/.test(nb) && /letter-spacing:\s*(0|\.2px)/.test(nb), nb);
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("map");
  const card = d.querySelector("#sections .ns-card");
  ok("the Map tab shows the antifragility card", !!card);
  ok("the card carries its band class", !!card && /(^|\s)ns-(fragile|robust|antifragile)(\s|$)/.test(card.className), card && card.className);
  console.log("test55 premium hero cards: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
