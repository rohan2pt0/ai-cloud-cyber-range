// test184: Ready for the big waves, slice 2 (queue horizon-waves; owner 2026-11-25). The two life waves' one step is a
// button: scams opens the Risk tab's drill, AI changes work adds one learning goal. One tap, then it is done, not read.
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
  const w = dom.window, d = w.document;
  w.S = w.S || { okrs: [] }; w.S.okrs = [];
  w.localStorage.removeItem("gm_threat_drills");
  w.goTab("money"); w.renderAll();
  const card = d.querySelector(".gm-mh");
  const btn = (id) => card && [...card.querySelectorAll("button")].find(b => (b.getAttribute("onclick") || "").indexOf("gmWaveDo('" + id + "')") >= 0);

  // 1. the two life waves' steps are buttons
  ok("the card has a button for the scam drill", !!btn("scams"), card ? card.textContent.slice(0, 120) : "missing");
  ok("the card has a button for the learning goal", !!btn("ai-work"));
  ok("both are real buttons, not a line to read", btn("scams") && btn("scams").tagName === "BUTTON" && btn("ai-work") && btn("ai-work").tagName === "BUTTON");
  ok("the scam button is the plain step", !!btn("scams") && btn("scams").textContent.trim() === "Rehearse one scam drill (Risk tab)");

  // 2. the scam button opens the Risk tab, where the drill lives
  let calls = []; const orig = w.goTab;
  w.goTab = function (id) { calls.push(id); return orig.apply(w, arguments); };
  btn("scams").click();
  ok("tapping the scam step asks for the Risk tab", calls.indexOf("risk") >= 0, calls.join());
  ok("the Risk tab then shows the drill", !!d.getElementById("gmThreats"));
  w.goTab = orig;

  // 3. the learning button adds exactly one goal, saves it, and the wave reads ready
  ok("no learning goal yet", w.gmWaves(w.gmMhCtx()).find(x => x.id === "ai-work").status === "not");
  const aiBtn = btn("ai-work");
  aiBtn.click();
  const okrs = w.S.okrs || [];
  ok("one tap adds exactly one goal", okrs.length === 1, String(okrs.length));
  ok("the goal is to learn one new skill this quarter", okrs[0] && okrs[0].o === "Learn one new skill this quarter", okrs[0] && okrs[0].o);
  ok("with one short course as its key result", okrs[0] && okrs[0].krs && okrs[0].krs.length === 1 && okrs[0].krs[0].t === "Finish one short course", JSON.stringify(okrs[0] && okrs[0].krs));
  const saved = JSON.parse(w.localStorage.getItem("sovS") || "{}");
  ok("the goal is saved on the device", saved.okrs && saved.okrs.length === 1 && saved.okrs[0].o === "Learn one new skill this quarter", JSON.stringify(saved.okrs));
  ok("the AI changes work wave now reads ready", w.gmWaves(w.gmMhCtx()).find(x => x.id === "ai-work").status === "ready");
  aiBtn.click();
  ok("a second tap adds nothing more", (w.S.okrs || []).length === 1, String((w.S.okrs || []).length));

  console.log("test184 ready for the big waves, slice 2: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
