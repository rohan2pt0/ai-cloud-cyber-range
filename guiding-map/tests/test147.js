// v147: two earners (owner 2026-11-19): each person holds their own pay, balances and cover; the household is derived.
// Fake data only; numbers are round and obviously not real.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const base = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const boot = prof => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    if (prof) w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const legacy = Object.assign({}, base, { psal: 50000, pname: "Sam" });   // old data: only psal
const two = Object.assign({}, base, { psal: 100000, pname: "Sam", earners: 2,
  mine: { epf: 1000000, nps: 200000, ppf: 300000, mf: 500000, fd: 100000, term: 30000000, health: 1000000 },
  partner: { gross: 150000, net: 100000, epf: 400000, nps: 0, ppf: 0, mf: 200000, fd: 50000, term: 4000000, health: 500000 } });
const dL = boot(legacy), d2 = boot(two), d1 = boot(Object.assign({}, base, { earners: 1 })), dE = boot(null);
setTimeout(() => {
  const L = dL.window, W = d2.window, O = d1.window, X = dE.window;
  // 1. old data with only psal still loads, and the household income is the sum
  ok("legacy: earners reads as 2 from psal", L.gmEarners(L.P) === 2, L.gmEarners(L.P));
  ok("legacy: household income is net + psal", L.gmHouseholdIncome(L.P) === 250000, L.gmHouseholdIncome(L.P));
  ok("legacy: partner net comes from psal", L.gmPartner(L.P).net === 50000);
  L.goTab("money");
  ok("legacy: Money screen renders the Two of you table", !!L.document.querySelector(".gm-two table"));
  ok("one earner: household income is net only", O.gmHouseholdIncome(O.P) === 200000);
  O.goTab("money");
  ok("one earner: no table", !O.document.querySelector(".gm-two"));
  // 3. the table: three columns with correct sums (before the save test changes the profile)
  W.goTab("money");
  const T = W.document.querySelector(".gm-two table");
  ok("table exists", !!T);
  // red, amber, green with a word (owner 2026-11-19: "visual cues whether it's progress or needs my attention")
  const rag = T ? [...T.querySelectorAll(".gm-rag")].map(x => x.dataset.state + ":" + x.textContent.trim()) : [];
  ok("term cover: 12.5 years is strong, 3.3 years needs care", rag.includes("good:12.5 yrs") && rag.includes("low:3.3 yrs"), rag.join(" "));
  ok("retirement pot below half the band for the age needs care", rag.includes("low:0.6 yrs"), rag.join(" "));
  ok("household health cover of 15 lakh is strong", rag.some(x => /^good:₹15/.test(x)), rag.join(" "));
  ok("every chip carries its word, never colour alone", T && [...T.querySelectorAll(".gm-rag")].every(x => /strong|building|needs care/.test(x.getAttribute("aria-label") || "")));
  ok("a key explains the three colours", !!W.document.querySelector(".gm-rag-key"));
  const heads = T ? [...T.querySelectorAll("thead th")].map(x => x.textContent.trim()) : [];
  ok("columns: label, You, Sam, Household", heads.join("|") === "|You|Sam|Household", heads.join("|"));
  const cells = l => { const r = T && [...T.querySelectorAll("tbody tr")].find(r => r.cells[0].textContent.replace(/\?/g, "").trim() === l); return r ? [...r.cells].slice(1).map(c => c.textContent.trim()) : []; };
  ok("net row sums", cells("Net per month").join(",") === "₹2.0L,₹1.0L,₹3.0L", cells("Net per month").join(","));
  ok("EPF row sums", cells("EPF").join(",") === "₹10.0L,₹4.0L,₹14.0L", cells("EPF").join(",")+"/"+cells("EPF").length);
  ok("NPS: empty cell reads as a dash", cells("NPS")[1] === "—" && cells("NPS")[2] === "₹2.0L", cells("NPS").join(","));
  const ty = cells("Term cover, years of that person’s income");
  ok("term years row", ty.slice(0, 2).map(x => x.replace(/aim.*$/, "")).join(",") === "12.5 yrs,3.3 yrs", ty.join(","));
  // each value shows its own target, worked out for that person (owner 2026-11-19)
  const tg = T ? [...T.querySelectorAll(".gm-tgt")].map(x => x.textContent) : [];
  ok("term cover target is 10 years of that person's own income", tg.includes("aim 10+ yrs · ₹2.40Cr") && tg.includes("aim 10+ yrs · ₹1.20Cr"), tg.join(" | "));
  ok("retirement target follows the age band (36: 2 years of income)", tg.some(t => /^aim 2\+ yrs at 3\d · ₹48\.0L$/.test(t)), tg.join(" | "));
  ok("health target is sized to the household, never under 10 lakh", tg.some(t => /^aim ₹10\.0L\+ for 2$/.test(t)), tg.join(" | "));
  ok("nine money rows plus three derived rows (term years, retirement years, health for the home)", !!T && T.querySelectorAll("tbody tr").length === 12, T && T.querySelectorAll("tbody tr").length);
  const ins = W.document.querySelector(".gm-two").textContent;
  ok("insight names Sam's thin term cover", /Sam has term cover worth 3\.3 years/.test(ins), ins.slice(-220));
  const t2 = Object.assign({}, two, { partner: Object.assign({}, two.partner, { term: 0 }) });
  ok("insight: missing cover is named", /Sam has no term cover/.test(W.gmTwoInsight(t2)));
  const t3 = Object.assign({}, two, { mine: Object.assign({}, two.mine, { term: 1000000 }) });
  ok("insight: the lowest of the two wins", /^You have term cover worth 0\.4 years/.test(W.gmTwoInsight(t3)), W.gmTwoInsight(t3));
  const t4 = Object.assign({}, two, { partner: Object.assign({}, two.partner, { term: 20000000, epf: 0, mf: 0, fd: 0 }) });
  ok("insight: no retirement pot when cover is fine", /^Sam has no EPF, NPS or PPF/.test(W.gmTwoInsight(t4)), W.gmTwoInsight(t4));
  ok("insight: empty state reads well", /^Add each person/.test(W.gmTwoInsight(Object.assign({}, base, { earners: 2, psal: 1000 }))));
  ok("household investments: sum when filled, nw otherwise", W.gmHouseholdInvest(two) === 2100000 + 650000 && W.gmHouseholdInvest(legacy) === 2500000, W.gmHouseholdInvest(two));
  // example profile shows the two-column view, marked as an example
  X.goTab("money");
  const t = X.document.querySelector(".gm-two");
  ok("example: Two of you shown with a fake partner, marked example", !!t && /example numbers/.test(t.previousSibling ? t.previousSibling.textContent : ""), t && t.previousSibling && t.previousSibling.textContent);
  // 5. no wife or husband in visible text
  const vis = [W, L, X].map(w => { const b = w.document.body.cloneNode(true); b.querySelectorAll("script,style").forEach(n => n.remove()); return b.textContent; }).join(" ");
  ok("no wife or husband in visible text", !/\b(wife|husband)\b/i.test(vis), (vis.match(/.{30}\b(wife|husband)\b.{30}/i)||[""])[0]);
  // 2. the switch shows and hides the partner block
  W.editProfile();
  const pm = W.document.getElementById("w_pmoney"), pb = W.document.getElementById("w_pbal"), sel = W.document.getElementById("w_earners");
  ok("both: select loads as 2, partner blocks shown", sel.value === "2" && pm.style.display !== "none" && pb.style.display !== "none");
  ok("both: partner fields filled back", W.document.getElementById("w_psal").value === "100000" && W.document.getElementById("w_p_epf").value === "400000");
  sel.value = "1"; sel.dispatchEvent(new W.Event("change"));
  ok("just me: partner blocks hidden", pm.style.display === "none" && pb.style.display === "none");
  sel.value = "2"; sel.dispatchEvent(new W.Event("change"));
  ok("both again: partner blocks shown", pm.style.display !== "none" && pb.style.display !== "none");
  ok("fold says it was never stamped", /not added yet/.test(W.document.getElementById("w_bal_s").textContent));
  // saving keeps psal in step, stamps balAt, derives nw
  W.document.getElementById("w_psal").value = "110000"; W.document.getElementById("w_m_epf").value = "1100000";
  W.buildDash();
  const sp = JSON.parse(W.localStorage.getItem("sovP"));
  ok("save: psal follows partner net", sp.psal === 110000 && sp.partner.net === 110000, sp.psal);
  ok("save: earners 2 and mine saved", sp.earners === 2 && sp.mine.epf === 1100000);
  ok("save: balAt stamped", sp.balAt > 0);
  const typed = +W.document.getElementById("w_nw").value;
  ok("save: a net worth the person typed is never overwritten by the balances", typed > 0 && sp.nw === typed, sp.nw + " vs " + typed);
  W.document.getElementById("w_nw").value = ""; W.buildDash();
  const sp2 = JSON.parse(W.localStorage.getItem("sovP"));
  ok("save: a blank net worth is filled from both persons' balances", sp2.nw === 1100000 + 200000 + 300000 + 500000 + 100000 + 400000 + 200000 + 50000, sp2.nw);
  W.editProfile();
  W.editProfile();
  ok("fold label now says updated today", /updated today/.test(W.document.getElementById("w_bal_s").textContent));
  W.document.getElementById("w_earners").value = "1"; W.buildDash();
  const s1 = JSON.parse(W.localStorage.getItem("sovP"));
  ok("save as just me: psal is 0 and household is net only", s1.psal === 0 && s1.earners === 1 && W.gmHouseholdIncome(s1) === 200000);
  done();
}, 800);
function done() { console.log("PASS " + P + " FAIL " + F); e.forEach(x => console.log("  FAIL " + x)); process.exit(F ? 1 : 0); }
