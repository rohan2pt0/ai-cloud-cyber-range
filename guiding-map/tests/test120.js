// v120: landlord desk, slice 2 (owner, 2026-11-15): a let-out home with no monthly rent says one calm line,
// "Add the monthly rent to track it", and its quiet action puts the cursor in the rent field. A home with rent
// does not show the line, and neither does a lived-in home. Fake data only, no real place names.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const iso = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
const now = new Date(), start = new Date(now.getFullYear(), now.getMonth() - 11, now.getDate() + 20);
const base = { use: "letout", val: "60", tenant: "Fake Tenant", rentDay: 5, start: iso(start), months: 11, maint: 2500, maintDay: 10 };
const noRent = Object.assign({}, base, { n: "Fake flat no rent", rent: "" });
const withRent = Object.assign({}, base, { n: "Fake flat with rent", rent: "18000" });
const lived = Object.assign({}, base, { n: "Fake lived in", use: "self", rent: "" });
const prof = { name: "Fake", dob: "1990-05-15", gross: 300000, net: 200000, exp: 90000, sav: 400000, nw: 2500000, kids: [], loans: [], ret: 50, example: false };
const boot = (props) => new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_props", JSON.stringify(props));
    w.localStorage.setItem("gm_facts", JSON.stringify({ state: "MH", home: true })); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const dom = boot([noRent, withRent, lived]);
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.goTab("prop");
  const cards = [...d.querySelectorAll("#sections details.road-col")];
  const card = (name) => cards.filter(c => /Fake flat|Fake lived/.test((c.querySelector("summary") || {}).textContent || "") && (c.querySelector("summary").textContent || "").includes(name))[0];
  const line = (c) => c && [...c.querySelectorAll("[data-rent-hint]")];
  const phrase = /Add the monthly rent to track it/;
  ok("a let-out home with no rent shows the line once", !!card("Fake flat no rent") && line(card("Fake flat no rent")).length === 1
    && phrase.test(card("Fake flat no rent").textContent), card("Fake flat no rent") ? card("Fake flat no rent").textContent.slice(0, 80) : "card missing");
  ok("a home with rent does not show the line", !!card("Fake flat with rent") && line(card("Fake flat with rent")).length === 0
    && !phrase.test(card("Fake flat with rent").textContent));
  ok("a lived-in home does not show the line", !!card("Fake lived in") && line(card("Fake lived in")).length === 0
    && !phrase.test(card("Fake lived in").textContent));
  const a = line(card("Fake flat no rent"))[0];
  let clicked = true; try { a.click(); } catch (x) { clicked = false; }
  const rent = d.getElementById("gmPropRent-0");
  ok("the quiet action puts the cursor in the rent field", clicked && !!rent && d.activeElement === rent,
    rent ? (d.activeElement ? d.activeElement.tagName : "none") : "rent field missing");
  console.log("test120 rent line: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1800);
