// test183: Ready for the big waves, slice 1b (queue horizon-waves; owner 2026-11-25). Two life waves join the four money
// ones: scams and false news, and AI changes work. Each is ready, partly or not yet, with one plain line why and one step
// in plain words, never an issue id. Pure: no network, no AI, no storage write.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: iso(-Math.round(38.5 * 365.25)), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 50000, sav: 300000, pname: "Fake Partner",
  kids: [{ name: "Kid A", dob: "2018-01-01" }], ret: 60, tsav: 20, example: false, earners: 1, mine: { mf: 1400000, epf: 600000 },
  loans: [{ type: "Personal loan", remaining: 200000, emi: 10000, rate: 14, tenure: 20 }] };
const mh = { policies: [
  { type: "health", who: "family", sa: 500000, prem: 18000, start: iso(-355) }],
  funds: [{ name: "Example Index Fund", value: 600000, plan: "direct" }],
  macro: { repo: 5.5, cpi: 3, at: iso(-20) }, alloc: {}, bench: {} };
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, c = w.gmMhCtx();
  w.S = w.S || { okrs: [] }; w.S.okrs = [];

  // 1. six waves: the money four first, then the two life waves
  const W = w.gmWaves(c), ids = W.map(x => x.id).join();
  ok("gmWaves gives six waves, the money four then the two life waves", W.length === 6 && ids === "slowdown,prices-rates,trade-shocks,health-weather,scams,ai-work", ids);
  ok("the two life waves have a name, a status and a plain line why", ["scams", "ai-work"].every(id => {
    const x = W.find(y => y.id === id);
    return x && typeof x.name === "string" && x.name && ["ready", "partly", "not"].indexOf(x.status) > -1 && typeof x.why === "string" && x.why.length > 10;
  }));

  // 2. scams is ready when a drill was recorded in the last 90 days
  const scams = () => w.gmWaves(c).find(x => x.id === "scams");
  w.localStorage.removeItem("gm_threat_drills");
  ok("scams: no drill on record is not ready yet", scams().status === "not", scams().status);
  w.localStorage.setItem("gm_threat_drills", JSON.stringify({ "fake:0": iso(-10) }));
  ok("scams: a drill in the last 90 days is ready", scams().status === "ready", scams().status);
  w.localStorage.setItem("gm_threat_drills", JSON.stringify({ "fake:0": iso(-200) }));
  ok("scams: a drill older than 90 days is not ready yet", scams().status === "not", scams().status);
  w.localStorage.setItem("gm_threat_drills", "}{");
  ok("scams: damaged storage reads not ready, never throws", scams().status === "not", scams().status);

  // 3. ai-work is ready when an active goal or key result names learning
  const ai = () => w.gmWaves(c).find(x => x.id === "ai-work");
  const withOkr = (o, krs) => { w.S.okrs = [{ o: o, krs: (krs || []).map(t => ({ t: t, v: 0 })) }]; };
  withOkr("Run a calmer quarter", ["Walk daily"]);
  ok("ai-work: no learning word in a goal is not ready yet", ai().status === "not", ai().status);
  withOkr("Learn Spanish", []);
  ok("ai-work: an objective that says learn is ready", ai().status === "ready", ai().status);
  withOkr("Build a new skill", []);
  ok("ai-work: an objective that says skill is ready", ai().status === "ready", ai().status);
  withOkr("A steady quarter", ["Finish a course"]);
  ok("ai-work: a key result that says course is ready", ai().status === "ready", ai().status);
  withOkr("A steady quarter", ["Earn a certification"]);
  ok("ai-work: a key result that says certif is ready", ai().status === "ready", ai().status);
  w.S.okrs = [];
  ok("ai-work: an empty goal list is not ready yet", ai().status === "not", ai().status);

  // 4. each step is plain words, not an issue id from REMEDIES
  const keys = Object.keys(w.GM_REMEDIES);
  ["scams", "ai-work"].forEach(id => {
    const x = w.gmWaves(c).find(y => y.id === id);
    ok(id + ": the step is a plain line, not a REMEDIES id", typeof x.step === "string" && x.step.length > 5 && keys.indexOf(x.step) < 0, x.step);
  });
  ok("scams: the step names the rehearsal", w.gmWaves(c).find(x => x.id === "scams").step === "Rehearse one scam drill (Risk tab)");
  ok("ai-work: the step names the learning goal", w.gmWaves(c).find(x => x.id === "ai-work").step === "Add one learning goal this quarter");

  // 5. the card under Money health shows both waves and both steps in plain words
  w.S.okrs = [{ o: "Run a calmer quarter", krs: [] }];
  w.localStorage.removeItem("gm_threat_drills");
  w.goTab("money"); w.renderAll();
  const card = d.querySelector(".gm-mh");
  ok("the Money health card shows the two life waves", !!card && card.textContent.includes("Scams and false news") && card.textContent.includes("AI changes work"), card ? card.textContent.slice(0, 80) : "missing");
  ok("the card shows the scam step as one plain line", !!card && card.textContent.includes("Rehearse one scam drill (Risk tab)"));
  ok("the card shows the learning step as one plain line", !!card && card.textContent.includes("Add one learning goal this quarter"));
  ok("the card shows no issue id as a step", !!card && !new RegExp(keys.filter(k => k.length > 6).join("|")).test(card.textContent));

  // 6. a wave that is ready shows no step (nothing to do)
  w.S.okrs = [{ o: "Learn Spanish", krs: [] }];
  w.goTab("money"); w.renderAll();
  const card2 = d.querySelector(".gm-mh");
  ok("a ready wave shows no step", !!card2 && card2.textContent.includes("AI changes work") && !card2.textContent.includes("Add one learning goal this quarter"));

  console.log("test183 ready for the big waves, slice 1b: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
