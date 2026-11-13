// test88: founders and business owners (owner, 2026-11-13): one fact asked once changes the right places, 80/20.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
function boot(facts) {
  return new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
    beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
      w.localStorage.setItem("gm_intro_seen", "true"); if (facts) w.localStorage.setItem("gm_facts", JSON.stringify(facts)); } }).window;
}
const founder = boot({ business: true }), salaried = boot({ salaried: true }), both = boot({ business: true, salaried: true }), fresh = boot(null), said_no = boot({ business: false });
setTimeout(() => {
  try {
    const S = founder.GM_SYSTEMS;
    ok(S.facts.some(f => f.id === "business"), "the business fact is asked once, with the others");
    const fs3 = S.systems.filter(s => (s.when || []).indexOf("business") >= 0).map(s => s.id);
    ok(["founder-cash", "founder-tax", "founder-focus"].every(id => fs3.indexOf(id) >= 0), "three founder systems: cash, tax, the CEO week");
    const tax = S.systems.find(s => s.id === "founder-tax");
    ok(tax.where === "IN" && /15 June/.test(JSON.stringify(tax)) && /15 March/.test(JSON.stringify(tax)) && S.sources.incometax && S.sources.incometax.checked, "India tax dates are local-only and sourced");
    // Money ladder: a founder without a salary pays themself first and keeps 12 months.
    const fp = founder.primeSteps(founder.engine()), sp = salaried.primeSteps(salaried.engine()), bp = both.primeSteps(both.engine());
    ok(/Pay yourself first/.test(fp[2].t) && /EPF/.test(sp[2].t) && /EPF/.test(bp[2].t), "step 2 fits how the person earns");
    ok(/12 months/.test(fp[4].t) && /6 months/.test(sp[4].t) && /6 months/.test(bp[4].t), "irregular income gets a 12-month buffer; a salary keeps 6");
    ok(founder.engine().emGoal === 12 && salaried.engine().emGoal === 6, "the emergency-fund goal follows the fact everywhere");
    // Risk Shield: the business card only for business owners.
    founder.curTab = "risk"; founder.renderAll(); salaried.curTab = "risk"; salaried.renderAll();
    const bc = [...founder.document.querySelectorAll(".kc.riskc .kl")].some(x => /Business continuity/.test(x.textContent));
    const sc = [...salaried.document.querySelectorAll(".kc.riskc .kl")].some(x => /Business continuity/.test(x.textContent));
    ok(bc && !sc, "Business continuity shows for founders only");
    const card = founder.RISKS.find(r => r.id === "r_business");
    ok(card && card.steps.length === 6 && /two-person rule/.test(card.steps.join(" ")), "the card carries the vital few, with the two-person payment rule");
    ok(founder.riskFirst() === "r_health", "Start here still begins with health");
    // Nothing appears until the person says so: a fresh install and an explicit No both see no founder content at all.
    [["nothing answered", fresh], ["answered No", said_no]].forEach(([label, w]) => {
      const p = w.primeSteps(w.engine());
      ok(/EPF/.test(p[2].t) && /6 months/.test(p[4].t) && w.engine().emGoal === 6, label + ": the money ladder is unchanged");
      w.curTab = "risk"; w.renderAll();
      ok(![...w.document.querySelectorAll(".kc.riskc .kl")].some(x => /Business/.test(x.textContent)) && !w.RISKS.some(r => r.id === "r_business"), label + ": no Business continuity card");
      w.goTab("systems");
      const ids = [...w.document.querySelectorAll('details[id^="gmsys-"]')].map(x => x.id);
      ok(!ids.some(i => /founder/.test(i)), label + ": no founder systems: " + ids.join(","));
    });
    founder.goTab("systems");
    const fids = [...founder.document.querySelectorAll('details[id^="gmsys-"]')].map(x => x.id);
    ok(["founder-cash", "founder-tax", "founder-focus"].every(id => fids.indexOf("gmsys-" + id) >= 0), "after Yes, the three founder systems appear: " + fids.join(","));
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test88 founders: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1800);
