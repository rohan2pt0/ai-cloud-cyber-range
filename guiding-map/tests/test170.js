// test170: Coming up in your world, mended on a phone (owner 2026-11-24): a stored name shows tidy (never changed), exactly one row is in view,
// a slip reads "Still open" (amber, no count of days late), and one tap marks the paper done with the same function as the Property tab. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(); const iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const NAME = "406_VeryLongFakeNameCHS_Testville", NAME2 = "101_SunriseCHS_Testville";
const prof = { name: "Fake", dob: "1989-05-05", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 500000, ret: 60, tsav: 20, example: false, earners: 1 };
const props = [{ n: NAME, use: "letout", rent: 20000, val: 80, start: iso(-259), months: 11 }, { n: NAME2, use: "letout", rent: 15000, val: 60, start: iso(-200), months: 11, police: iso(-190) }];
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_props", JSON.stringify(props)); w.localStorage.setItem("gm_simple", "false");
    w.localStorage.setItem("gm_mine_done", "true"); w.localStorage.setItem("gm_quick_done", "true"); w.matchMedia = mm; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  ok("the tidy helper", w.gmTidyName(NAME2) === "101 Sunrise CHS, Testville" && w.gmTidyName("A  B") === "A B" && w.gmTidyName(undefined) === "", w.gmTidyName(NAME2));
  w.goTab("today"); w.renderAll();
  let c = d.querySelector(".gm-cu"); ok("the card shows", !!c);
  const inView = () => [...d.querySelectorAll(".gm-cu > div[role=list] > .gm-cu-row")];
  ok("exactly one row in view, the rest under Later", inView().length === 1 && /Later \(\d+\)/.test(c.textContent) && !!c.querySelector("details .gm-cu-row"));
  ok("the name is tidy, with no underscore", !/_/.test(c.textContent) && /Very Long Fake Name CHS, Testville/.test(c.textContent), c.textContent.slice(0, 160));
  ok("the title can never leave the card", /overflow-wrap:anywhere/.test(c.querySelector(".gm-cu-t").getAttribute("style")));
  const r = inView()[0], when = r.querySelector(".gm-cu-when");
  ok("an overdue row says Still open, kindly", /Still open/.test(when.textContent) && /since /.test(when.textContent) && !/days? late/i.test(c.textContent), when.textContent);
  ok("in the amber tone, not red", when.classList.contains("gm-cu-watch") && !when.classList.contains("gm-cu-low") && !/c0392b/i.test(r.innerHTML));
  ok("the old hand-off sentence is gone", !/Mark it done on the Property tab/.test(c.textContent));
  const b = r.querySelector("button.gm-cu-done"); ok("a one-tap quiet button", !!b && /Submitted/.test(b.textContent), r.innerHTML.slice(0, 200));
  ok("papers offer Already done", !!r.querySelector(".gm-cu-already"));
  ok("the stored name is untouched", JSON.parse(w.localStorage.getItem("gm_props"))[0].n === NAME);
  const homeBefore = w.gmComingUp().filter(x => x.kind === "home").length, first = w.gmComingUp()[0], pi = first.pi, id = first.id;
  b.click();
  const stored = JSON.parse(w.localStorage.getItem("gm_props"));
  ok("the tap stores the same change as the Property tab", id === "police" && stored[pi].police === iso(0), JSON.stringify(stored[pi]));
  ok("the item leaves the list", w.gmComingUp().filter(x => x.kind === "home").length === homeBefore - 1 && !w.gmComingUp().some(x => x.pi === pi && x.id === id));
  ok("one Undo is held", !!w.localStorage.getItem("gm_undo"));
  w.gmUndo(); ok("Undo brings it back", w.gmComingUp().some(x => x.pi === pi && x.id === id));
  console.log("test170 coming up, mended: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
