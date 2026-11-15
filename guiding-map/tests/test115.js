// v115: the landlord desk (owner, 2026-11-15: rent, maintenance, property tax, agreement end, registration, police details
// for tenants are hard to keep track of across homes). Each let-out home shows "Next for this home": what is due, overdue
// first, with a ruby stone for overdue and amber within a week, a one-tap Done, and a ready message from landlord.json.
// Registration rows are for Maharashtra only. Fake data only, no real place names.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const iso = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
const now = new Date(), start = new Date(now.getFullYear(), now.getMonth() - 11, now.getDate() + 20), taxDue = new Date(now.getTime() - 20 * 864e5);
const home = { n: "Fake flat", use: "letout", val: "60", rent: "18000", tenant: "Fake Tenant", rentDay: 5, start: iso(start), months: 11,
  maint: 2500, maintDay: 10, taxDue: iso(taxDue), registered: "", police: "" };
const prof = { name: "Fake", dob: "1990-05-15", gross: 300000, net: 200000, exp: 90000, sav: 400000, nw: 2500000, kids: [], loans: [], ret: 50, example: false };
const boot = (facts) => new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_props", JSON.stringify([home]));
    w.localStorage.setItem("gm_facts", JSON.stringify(facts)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const mh = boot({ state: "MH", home: true }), other = boot({ state: "other", home: true });
setTimeout(() => {
  const w = mh.window, d = w.document;
  w.goTab("prop");
  const desk = d.querySelector(".gm-ll"), rows = () => [...d.querySelectorAll(".gm-ll .gm-ll-row")].map(r => r.getAttribute("data-ll"));
  ok("a let-out home shows Next for this home", !!desk && /Next for this home/.test(desk.textContent));
  ok("overdue comes first, oldest first (the police details, due at move-in 11 months ago), each as a ruby stone",
    rows()[0] === "police" && !!d.querySelector('.gm-ll-row[data-ll="police"] .sx-state-low') && !!d.querySelector('.gm-ll-row[data-ll="propertyTax"] .sx-state-low'), rows().join(","));
  const all = [...d.querySelectorAll(".gm-ll-row")].map(r => r.getAttribute("data-ll"));
  ok("the renewal (ending within 60 days), registration and police rows are there", ["renewal", "registration", "police"].every(x => all.includes(x)), all.join(","));
  ok("the summary line at the top names the next thing due", /1 home let/.test((d.querySelector(".gm-ll-sum") || {}).textContent || ""));
  ok("a ready message travels with the row (the renewal note)", /Renewal note to the tenant/.test(d.body.textContent));
  const before = all.length;
  w.gmLlDone(0, "tax", "");
  const tax2 = JSON.parse(w.localStorage.getItem("gm_props"))[0].taxDue;
  ok("Done on property tax diarises next year", tax2 === iso(new Date(taxDue.getFullYear() + 1, taxDue.getMonth(), taxDue.getDate())), tax2);
  const ym = iso(now).slice(0, 7);
  w.gmLlDone(0, "paid", ym);
  ok("rent received this month removes the rent row", !rows().includes("rent") && JSON.parse(w.localStorage.getItem("gm_props"))[0].paid[ym] === true, rows().join(","));
  w.gmPropSet(0, "rentDay", "40");
  ok("a rent day of 40 is kept to 28", JSON.parse(w.localStorage.getItem("gm_props"))[0].rentDay === 28);
  ok("fewer rows after two are done", [...d.querySelectorAll(".gm-ll-row")].length < before);
  const w2 = other.window, d2 = w2.document;
  w2.goTab("prop");
  const all2 = [...d2.querySelectorAll(".gm-ll-row")].map(r => r.getAttribute("data-ll"));
  ok("outside Maharashtra there is no registration row (it is a Maharashtra rule)", !all2.includes("registration") && all2.includes("police"), all2.join(","));
  console.log("test115 landlord desk: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1800);
