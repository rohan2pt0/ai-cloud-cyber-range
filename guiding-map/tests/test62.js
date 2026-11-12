// v62: the Growth routine is a loop the person runs: one open block with a two-minute floor,
// the rest folded under Later (n), ticks kept in gm_routine, and a small win when all seven are done.
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
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections").querySelector(".section.active");
  const doneButtons = (s) => [...s.querySelectorAll("button")].filter((b) => b.textContent.trim() === "Done");
  const progress = (s) => (s.querySelector("#routine-progress") || {}).textContent || "";

  w.goTab("growth");
  let s = sec();
  ok("routine: exactly one Done primary button", doneButtons(s).length === 1, String(doneButtons(s).length));
  ok("routine: the progress line starts at 0 of 7, 0 of 100", /^0 of 7 done today, 0 of 100 minutes$/.test(progress(s).trim()), progress(s));

  const btn = doneButtons(s)[0];
  const id = (btn.getAttribute("onclick") || "").match(/gmRoutineTick\('([^']+)'\)/);
  ok("routine: the Done button ticks one named block", !!id, btn.getAttribute("onclick"));
  btn.click();

  s = sec();
  const day = w.dKey(new Date());
  let stored = {};
  try { stored = JSON.parse(w.localStorage.getItem("gm_routine") || "{}"); } catch (err) { stored = {}; }
  const today = Array.isArray(stored[day]) ? stored[day] : [];
  ok("routine: clicking Done stores today's block id in gm_routine", !!id && today.indexOf(id[1]) >= 0, JSON.stringify(stored));
  ok("routine: the progress line goes from 0 to 1", /^1 of 7 done today, \d+ of 100 minutes$/.test(progress(s).trim()), progress(s));

  if (today.indexOf("move") < 0) {
    let row = s.querySelector('[data-routine="move"]');
    if (!row) row = [...s.querySelectorAll("button")].find((b) => /gmRoutineTick\('move'\)/.test(b.getAttribute("onclick") || ""));
    ok("routine: move has a one-tap tick", !!row);
    if (row) row.click();
    s = sec();
  }
  const checks = w.todayChecks();
  ok("routine: ticking move also marks habit ex done today", checks.indexOf("ex") >= 0, checks.join(","));

  const all = ["money", "move", "read", "reset", "outreach", "connect", "give"];
  const next = JSON.parse(w.localStorage.getItem("gm_routine") || "{}");
  next[day] = all.slice();
  w.localStorage.setItem("gm_routine", JSON.stringify(next));
  w.goTab("growth");
  s = sec();
  ok("routine: all seven stored shows the win line", /All done today\. That is a vote for the person you are becoming\./.test(s.textContent));
  ok("routine: all seven done leaves no Done button", doneButtons(s).length === 0, String(doneButtons(s).length));
  ok("routine: all seven done shows 7 of 7, 100 of 100 minutes", /7 of 7 done today, 100 of 100 minutes/.test(progress(s)), progress(s));
  ok("routine: no NaN in the routine", !/NaN/.test(s.textContent));
  ok("routine: no undefined in the routine", !/undefined/.test(s.textContent));

  console.log("test62 routine loop: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
