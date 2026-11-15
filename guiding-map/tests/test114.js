// v114: Savings levers on the Money tab (owner, 2026-11-15). Legitimate ways to cut costs and tax, run as a working
// system: one open lever, one question at a time, steps ticked and kept, and every lever placed by area then effort.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const facts = { stages: ["salaried"], home: true, state: "MH", women: true, electricity: 3000, apartment: false, hufFit: false, parents: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_facts", JSON.stringify(facts));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const money = () => { w.goTab("money"); return d.querySelector('.gm-levers'); };
  const lever = (id) => d.querySelector('[data-lever="' + id + '"]');
  const saved = () => { try { return JSON.parse(w.localStorage.getItem("gm_levers") || "{}") || {}; } catch (x) { return {}; } };
  let card = money();

  ok("window.GM_LEVERS has at least 10 levers", !!(w.GM_LEVERS && w.GM_LEVERS.levers && w.GM_LEVERS.levers.length >= 10),
    w.GM_LEVERS && w.GM_LEVERS.levers ? String(w.GM_LEVERS.levers.length) : "missing");
  ok("the Money tab shows Savings levers", !!card && /Savings levers/.test(card.textContent), card ? "no title" : "no card");
  ok("exactly one lever is open", d.querySelectorAll(".gm-lever-open").length === 1, String(d.querySelectorAll(".gm-lever-open").length));
  ["rooftop-solar", "msrtc-women", "tax-regime", "employer-nps"].forEach(id =>
    ok("the " + id + " lever is among the matched ones", !!lever(id), "not shown"));
  ["presumptive-professional", "huf"].forEach(id =>
    ok("the " + id + " lever is not matched", !lever(id), "shown anyway"));

  const openBefore = d.querySelector(".gm-lever-open");
  const stepBtn = openBefore ? openBefore.querySelector("[data-lev-step]") : null;
  const stepId = stepBtn ? stepBtn.getAttribute("data-lev-step") : "";
  if (stepBtn) stepBtn.click();
  const st = saved();
  ok("ticking a step persists in gm_levers", !!stepId && st[stepId.split("|")[0]] && st[stepId.split("|")[0]].steps[0] === true, JSON.stringify(st));

  money();
  const openNow = d.querySelector(".gm-lever-open");
  const before = openNow ? openNow.getAttribute("data-lever") : "none";
  const doneBtn = openNow ? openNow.querySelector("[data-lev-done]") : null;
  if (doneBtn) doneBtn.click();
  money();
  const after = d.querySelector(".gm-lever-open");
  ok("Done moves to the next lever", !!after && after.getAttribute("data-lever") !== before, before + " -> " + (after ? after.getAttribute("data-lever") : "none"));

  w.localStorage.setItem("gm_facts", JSON.stringify(Object.assign({}, facts, { state: "other" })));
  w.renderAll(); card = money();
  ok("with another state, no IN-MH lever is shown", !lever("msrtc-women") && !lever("msrtc-senior"), "shown anyway");

  const noState = Object.assign({}, facts); delete noState.state;
  w.localStorage.setItem("gm_facts", JSON.stringify(noState));
  w.localStorage.removeItem("gm_levers");
  w.renderAll(); card = money();
  ok("a missing state asks its one-tap question", !!d.querySelector('[data-lev-q="state"]') && /Maharashtra/.test(d.body.textContent), "no question");
  // parents who depend on the person, with no age known yet: the card asks the eldest parent's age once (it lands in the Life Map)
  w.localStorage.setItem("gm_facts", JSON.stringify(Object.assign({}, facts, { parents: true })));
  w.goTab("money");
  ok("parents who depend on you, age unknown: the card asks the eldest parent's age", !!d.querySelector('[data-lev-q="page"]'), "no age question");
  w.gmLevFact("page", "72");
  ok("the age is kept in the Life Map, and parent levers (Ayushman for 70+) now fit", (JSON.parse(w.localStorage.getItem("gm_life") || "{}").page === "72") && /Ayushman/.test(d.body.textContent), w.localStorage.getItem("gm_life"));

  // slice 2: the tax comparator, on the person's own figures (worked by hand: 30 lakh gross, new 4,75,800; old 7,25,400; fees 1,09,200)
  ok("the tax tables give the hand-worked figures", w.gmTaxNew(1200000) === 0 && w.gmTaxNew(2925000) === 475800 && w.gmTaxOld(2950000) === 725400 && w.gmTaxNew(1500000) === 109200,
    [w.gmTaxNew(1200000), w.gmTaxNew(2925000), w.gmTaxOld(2950000), w.gmTaxNew(1500000)].join(","));
  w.localStorage.setItem("gm_levers", "{}");
  w.localStorage.setItem("gm_facts", JSON.stringify(facts));
  w.eval("P.gross=250000;P.example=false;store('sovP',P);");
  w.goTab("money");
  const est = d.querySelector(".gm-lev-est");
  ok("the tax-regime lever shows both regimes on the person's own gross and which saves", !!est && /New regime: \u20b94,75,800/.test(est.textContent) && /new regime saves/i.test(est.textContent), est && est.textContent);
  w.gmLevTaxDed("350000");
  ok("deductions they can claim move the old-regime figure", /old regime: \u20b96,16,200/.test((d.querySelector(".gm-lev-est") || {}).textContent || ""), (d.querySelector(".gm-lev-est") || {}).textContent);
  console.log("test114 savings levers: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
