// test174: Find anything (queue find-anything, slice 1; owner 2026-11-25). One search box finds goals, homes, people,
// policies and what is coming up, from data already on the device. Pure: no network, no AI, no storage write; a query
// under two characters answers nothing; matching ignores case and accents; at most 8 per kind; a PIN, password or
// account number is never read, so it can never be shown; damaged storage gives an empty answer, never a crash.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: iso(-Math.round(38.5 * 365.25)), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 50000, sav: 300000,
  kids: [], loans: [], ret: 60, tsav: 20, example: false, earners: 1 };
const okrs = { okrs: [{ o: "Emergency fund", at: Date.now(), krs: [{ t: "Save 6 months of costs", v: 3, at: Date.now() }] }] };
const home = (n) => ({ n: n, use: "letout", val: 75, rent: 18000, loan: 0, rate: 0, emi: 0, out: 0, vac: "1", owner: "me", tenant: "Tenant A", rentDay: 5, start: "2025-06-01", months: 11, pin: "4433", acct: "1234567890" });
const props = [home("101 Sunrise Heights")].concat([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(i => home("Sunrise Flat " + i)));
const mh = { policies: [{ type: "term", who: "me", sa: 10000000, prem: 14000, start: iso(-365), term: 25 }, { type: "health", who: "family", sa: 500000, prem: 18000, start: "2017-06-01" }], funds: [], macro: {}, alloc: {}, bench: {} };
let fetches = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("sovS", JSON.stringify(okrs));
    w.localStorage.setItem("gm_props", JSON.stringify(props)); w.localStorage.setItem("gm_people", JSON.stringify([{ n: "Asha", m: 3, d: 14 }]));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true"); w.localStorage.setItem("gm_quick_done", "true");
    w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => { fetches++; return Promise.reject(new Error("offline")); }; } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const flat = (r) => r.reduce((a, g) => a.concat((g.items || []).map(x => [g.kind, x.t, x.sub])), []);
  const texts = (r) => flat(r).map(x => x.join(" ")).join(" | ");

  // 1. the answer is grouped by kind, and each hit has a title and a one-line context
  const R = w.gmFind("sunrise");
  ok("the answer is a list of groups", Array.isArray(R) && R.every(g => g && typeof g.kind === "string" && Array.isArray(g.items)), JSON.stringify(R).slice(0, 200));
  ok("each hit has a title and a one-line context", R.every(g => g.items.every(x => x && typeof x.t === "string" && x.t && typeof x.sub === "string" && x.sub)));
  ok("a hit knows where to open", R.every(g => g.items.every(x => typeof x.go === "string" && x.go)));
  const homes = R.find(g => g.kind === "Homes");
  ok("the home is found by its name", !!homes && homes.items.some(x => /101 Sunrise Heights/.test(x.t)), texts(R));
  ok("only the home and its own coming-up rows match 'sunrise'", R.every(g => g.kind === "Homes" || g.kind === "Coming up"), R.map(g => g.kind).join());

  // 2. every kind answers
  ok("a person is found by name", flat(w.gmFind("asha")).some(x => x[0] === "People" && /Asha/.test(x[1])), texts(w.gmFind("asha")));
  ok("a goal is found, its key result as the context", flat(w.gmFind("emergency")).some(x => x[0] === "Goals" && /Emergency fund/.test(x[1]) && /Save 6 months/.test(x[2])), texts(w.gmFind("emergency")));
  ok("a key result is found under its goal", flat(w.gmFind("months of costs")).some(x => x[0] === "Goals" && /Emergency fund/.test(x[1])), texts(w.gmFind("months of costs")));
  ok("a policy is found by what it is called", flat(w.gmFind("term")).some(x => x[0] === "Policies" && /Term/.test(x[1])), texts(w.gmFind("term")));
  ok("a policy's context says who and how much", flat(w.gmFind("term")).filter(x => x[0] === "Policies").every(x => /You|Family/.test(x[2])), texts(w.gmFind("term")));
  ok("what is coming up is found", flat(w.gmFind("check-in")).some(x => x[0] === "Coming up" && /Month-end money check-in/.test(x[1])), texts(w.gmFind("check-in")));

  // 3. matching ignores case and accents; short queries answer nothing
  ok("UPPER CASE matches", !!w.gmFind("SUNRISE").find(g => g.kind === "Homes"));
  ok("an accented query matches", !!w.gmFind("SUNRÍSE").find(g => g.kind === "Homes"));
  ok("one character answers nothing", w.gmFind("a").length === 0 && w.gmFind("1").length === 0, texts(w.gmFind("a")));
  ok("an empty query answers nothing", w.gmFind("").length === 0 && w.gmFind("   ").length === 0);
  ok("no match answers nothing", w.gmFind("zzzzqq").length === 0);

  // 4. at most 8 per kind
  const many = w.gmFind("sunrise");
  ok("at most 8 per kind", many.every(g => g.items.length <= 8), many.map(g => g.items.length).join());

  // 5. a PIN, password or account number is never shown
  ok("a PIN is never found", w.gmFind("4433").length === 0, texts(w.gmFind("4433")));
  ok("an account number is never found", w.gmFind("1234567890").length === 0, texts(w.gmFind("1234567890")));
  ok("no hit carries a long digit run", !/\d{6,}/.test(texts(many)), texts(many));

  // 6. no network call and no storage write
  const snap = () => { const o = {}; for (let i = 0; i < w.localStorage.length; i++) { const k = w.localStorage.key(i); o[k] = w.localStorage.getItem(k); } return JSON.stringify(o); };
  const f0 = fetches, s0 = snap();
  w.gmFind("sunrise"); w.gmFind("asha"); w.gmFind("e"); w.gmFindOpen(); w.gmClose();
  ok("no network call", fetches === f0, String(fetches - f0));
  ok("no storage write", snap() === s0);

  // 7. damaged storage never throws
  let threw = "";
  try {
    w.localStorage.setItem("sovS", "5"); w.localStorage.setItem("gm_props", '"str"'); w.localStorage.setItem("gm_people", "[null,null]");
    w.localStorage.setItem("gm_mhealth", "}{"); w.localStorage.setItem("sovP", "}{");
    const r = w.gmFind("su");
    ok("damaged storage: an empty, finite answer", Array.isArray(r) && r.every(g => !/NaN|Infinity|undefined/.test(texts([g]))), texts(r));
  } catch (er) { threw = String(er); }
  ok("damaged storage: no crash", !threw, threw);
  // the app's own readers settle a damaged key at boot; put the good fixture back for what follows
  w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("sovS", JSON.stringify(okrs));
  w.localStorage.setItem("gm_props", JSON.stringify(props)); w.localStorage.setItem("gm_people", JSON.stringify([{ n: "Asha", m: 3, d: 14 }]));
  w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));

  // 8. the dialog: one tap opens the place; Enter opens the first result; Escape closes
  w.gmFindOpen();
  const ov = d.getElementById("gmOverlay");
  ok("the Find dialog opens with an input", !!ov && !!ov.querySelector("input"));
  const inp = ov.querySelector("input");
  inp.value = "sunrise"; inp.dispatchEvent(new w.Event("input", { bubbles: true }));
  const rows = [...ov.querySelectorAll("[data-g][data-i]")];
  ok("typing shows the results as rows", rows.length >= 1 && /101 Sunrise Heights/.test(ov.textContent), ov.textContent.slice(0, 120));
  inp.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  ok("Enter opens the first result and closes the dialog", !d.getElementById("gmOverlay") && w.curTab === "prop", String(w.curTab));
  w.gmFindOpen();
  const inp2 = d.querySelector("#gmOverlay input");
  inp2.value = "sunrise"; inp2.dispatchEvent(new w.Event("input", { bubbles: true }));
  const first = d.querySelector("#gmOverlay [data-g][data-i]");
  first.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  ok("one tap on a result opens its place", !d.getElementById("gmOverlay") && w.curTab === "prop", String(w.curTab));
  w.gmFindOpen();
  const inp3 = d.querySelector("#gmOverlay input");
  inp3.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok("Escape closes the dialog", !d.getElementById("gmOverlay"));
  // one line in the header, beside All Apps, quiet and finger-sized
  const btn = d.querySelector("#dash header .hdr-btn[onclick='gmFindOpen()']");
  ok("a quiet Find button sits in the header", !!btn && /Find/.test(btn.textContent) && btn.previousElementSibling && /All Apps/.test(btn.previousElementSibling.textContent), btn ? btn.textContent : "missing");
  ok("the Find button is not gold (quiet)", !/var\(--gold\)/.test(btn.getAttribute("style") || ""));

  // 9. pure: same answer, no hidden state
  ok("the same query gives the same answer twice", texts(w.gmFind("sunrise")) === texts(many));

  console.log("test174 find anything: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
