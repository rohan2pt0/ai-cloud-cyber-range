// test173: Money health (every-issue-has-a-path, slice 2; owner 2026-11-25). One bird's-eye card on the Money tab finds where
// money leaks or protection is thin, and each finding carries its fixes from the one REMEDIES engine. Pure code, no AI, no
// network; everything stays on the device. Fake data only: a Postal Life Insurance endowment with poor cover for its premium,
// two health floaters for the same family, a regular-plan fund, a costly personal loan and a 70/30 mix against a lower target.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(), iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: iso(-Math.round(38.5 * 365.25)), country: "India", cur: "INR", gross: 180000, net: 120000, exp: 50000, sav: 300000, pname: "Fake Partner",
  kids: [{ name: "Kid A", dob: "2018-01-01" }], ret: 60, tsav: 20, example: false, earners: 1, mine: { mf: 1400000, epf: 600000 },
  loans: [{ type: "Personal loan", remaining: 200000, emi: 10000, rate: 14, tenure: 20 }] };
const mh = { policies: [
  { type: "pli", who: "me", sa: 500000, prem: 24000, start: iso(-Math.round(7.5 * 365.25)), term: 20, ppt: 20, sv: 110000, pu: 180000 },
  { type: "health", who: "family", sa: 500000, prem: 18000, start: "2017-06-01" },
  { type: "health", who: "family", sa: 500000, prem: 21000, start: "2023-06-01" }],
  funds: [{ name: "Example Flexi Cap Fund", value: 800000, plan: "regular" }, { name: "Example Index Fund", value: 600000, plan: "direct" }],
  macro: { repo: 5.5, cpi: 3, at: iso(-20) }, alloc: {}, bench: {} };
let fetches = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_mhealth", JSON.stringify(mh));
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x";
    w.fetch = () => { fetches++; return Promise.reject(new Error("offline")); }; } });
const near = (a, b, tol) => Math.abs(a - b) <= (tol === undefined ? 1e-6 : tol);
setTimeout(() => {
  const w = dom.window, d = w.document, c = w.gmMhCtx();
  if (process.env.MH_PROBE) { console.log(JSON.stringify(c, (k, v) => k === "policies" || k === "funds" ? undefined : v)); w.gmMhScan(c).forEach(f => console.log(f.issue, f.tier, Math.round(f.freedYear), Math.round(f.coverGain), "|", f.title, "|", f.line)); }

  // the person's own numbers, read once
  ok("fixture: age 38, two dependants, 22 years to retirement", c.age === 38 && c.deps === 2 && c.horizon === 22, [c.age, c.deps, c.horizon].join());
  ok("fixture: term need = 120 months of gross pay + loans (gmTermNeed)", c.need === 180000 * 120 + 200000 && c.need === w.gmTermNeed(180000, true), c.need);
  ok("fixture: life cover is the PLI's ₹5 lakh, so the gap is need − 5 lakh", c.lifeHave === 500000 && c.lifeGap === c.need - 500000);

  // 1. the anomaly math
  const L = w.gmMhScan(c), ids = L.map(f => f.issue);
  ["life-cover-gap", "health-below-floor", "endow-low-return", "health-overlap", "debt-costly", "fund-regular", "alloc-drift"].forEach(id => ok("flags " + id, ids.includes(id), ids.join()));
  ok("no idle cash flagged: savings sit inside the buffer", !ids.includes("cash-idle"));
  const en = w.gmMhEndow(c.policies[0], c);
  ok("cover per ₹1,000 of premium = SA ÷ premium × 1,000", near(en.cpk, 500000 / 24000 * 1000), en.cpk);
  ok("term benchmark at 38: ₹7 lakh per ₹1,000 (editable)", c.cpk === 700000);
  ok("real return = (1 + 5%) ÷ (1 + 6%) − 1", near(en.real, (1.05 / 1.06 - 1) * 100), en.real);
  const n = 20 - 7.5, m = 20 - 8, wait = 8 - 7.5;
  let pr = (rate) => { let s = 0; for (let k = 0; k < m; k++) s += 24000 * Math.pow(1 + rate, n - (wait + k)); return s; };
  ok("years left and premiums left", near(en.years, n, 0.01) && en.premsLeft === m, [en.years, en.premsLeft].join());
  ok("continue = SV grown at 5% + each premium grown at 5%", near(en.cont, 110000 * Math.pow(1.05, en.years) + pr(0.05), 300), [en.cont, 110000 * Math.pow(1.05, n) + pr(0.05)].join());
  ok("paid-up = the paid-up value + each premium grown at 7%", near(en.paidUp, 180000 + pr(0.07), 300));
  ok("surrender = SV grown at 7% + each premium grown at 7%", near(en.surrender, 110000 * Math.pow(1.07, en.years) + pr(0.07), 300));
  const noVals = w.gmMhEndow(Object.assign({}, c.policies[0], { sv: "", pu: "" }), c);
  ok("values never invented: no surrender or paid-up value means null", noVals.surrender === null && noVals.paidUp === null && noVals.cont === null);
  const ov = L.find(f => f.issue === "health-overlap");
  ok("duplicate health: the newer policy folds into a super top-up (₹21,000 − ₹5L × ₹1,500 per ₹10L)", ov && ov.ctx.newer.i === 2 && near(ov.freedYear, 21000 - 750), ov && ov.freedYear);
  const hf = L.find(f => f.issue === "health-below-floor");
  ok("health floor for 3 people in a metro = max(₹10L, 3 × ₹5L) = ₹15L; a ₹5L super top-up", c.floor === 1500000 && c.hHave === 1000000 && c.stuAmt === 500000 && hf.coverGain === 500000);
  ok("costly debt: ₹2L at 14% against 7% costs ₹14,000 a year more", near(L.find(f => f.issue === "debt-costly").freedYear, 14000));
  ok("regular plan drag = ₹8L × 0.75% = ₹6,000 a year", near(L.find(f => f.issue === "fund-regular").freedYear, 6000));
  ok("risk-ranked: protection gaps first, life before health", ids[0] === "life-cover-gap" && ids[1] === "health-below-floor");
  ok("then the money leaks, the largest first", L.slice(2).filter(f => f.freedYear > 0).every((f, i, a) => i === 0 || a[i - 1].freedYear >= f.freedYear));

  // 2. the surrender guard: no paid-up or surrender before term cover is in force
  const ef = L.find(f => f.issue === "endow-low-return"), cx = Object.assign({}, c, ef.ctx);
  const R0 = w.gmRemedies("endow-low-return", cx);
  ok("without term in force: surrender and paid-up are hidden", !R0.fixes.some(x => x.id === "endow-surrender" || x.id === "endow-paidup"), R0.fixes.map(x => x.id).join());
  ok("and the reason is shown", R0.guards.length === 2 && R0.guards.every(g => /Do not make it paid-up or surrender it yet/.test(g) && /medical/.test(g)));
  ok("term cover first leads, as a hard step", R0.fixes[0].id === "term-first" && R0.fixes[0].hard);
  const R1 = w.gmRemedies("endow-low-return", Object.assign({}, cx, { termIn: c.need }));
  ok("with enough term in force: paid-up and surrender open, compared with continuing", ["endow-paidup", "endow-surrender", "endow-continue"].every(id => R1.fixes.some(x => x.id === id)) && !R1.fixes.some(x => x.id === "term-first"));
  const sur = R1.fixes.find(x => x.id === "endow-surrender");
  ok("the surrender fix shows the premium freed and the gap to continuing", sur && /₹24,000 a year freed · ₹[\d,]+ (more|less) than continuing/.test(sur.impact.headline), sur && sur.impact.headline);
  ok("a term policy merely applied for does not lift the guard", w.gmMhCtx && (() => { const s = JSON.parse(w.localStorage.getItem("gm_mhealth")); s.policies.push({ type: "term", sa: 30000000, prem: 20000, st: "applied" });
    w.localStorage.setItem("gm_mhealth", JSON.stringify(s)); const c2 = w.gmMhCtx(); const r = c2.termIn === 0; s.policies.pop(); w.localStorage.setItem("gm_mhealth", JSON.stringify(s)); return r; })());
  ok("the tax point is cited by topic, tagged for India", R1.notes.some(x => /data-where="IN"/.test(x) && /first two years/.test(x) && /check your policy terms/.test(x)));
  const R2 = w.gmRemedies("endow-low-return", Object.assign({}, cx, { termIn: c.need, p: Object.assign({}, cx.p, { sv: "", pu: "" }), e: noVals }));
  ok("no values given: the options ask once, with where to find them", R2.fixes.filter(x => x.id === "endow-surrender" || x.id === "endow-paidup").every(x => x.pre === "unknown" && /Where to find this/.test(x.preNote)));

  // 3. the allocation engine: target, tilt, the 5/25 band and the cadence
  const tg = w.gmMhTarget({ age: 38, horizon: 22, deps: 2, work: "salaried", tilt: 0 });
  ok("strategic target = 100 − 38 − 2 × 2.5 = 57% equity, method shown", tg.strategic === 57 && /100 − age 38 = 62/.test(tg.how), tg.how);
  ok("glide path falls with age", tg.glide.every((g, i, a) => i === 0 || g.equity <= a[i - 1].equity) && tg.glide.length === 4);
  ok("short horizon caps equity at 30%", w.gmMhTarget({ age: 30, horizon: 3, deps: 0 }).strategic === 30);
  ok("contract income lowers it by 10", w.gmMhTarget({ age: 30, horizon: 30, deps: 0, work: "contract" }).strategic === 60);
  const mc = w.gmMhMacro({ repo: 5.5, cpi: 3 });
  ok("macro: real rate 2.5% → tilt −4 points, a longer debt duration", mc.real === 2.5 && mc.tilt === -4 && /medium to long/.test(mc.duration));
  ok("the tilt never passes ±5 points", w.gmMhMacro({ repo: 2, cpi: 12 }).tilt === 5 && w.gmMhMacro({ repo: 12, cpi: 1 }).tilt === -5);
  ok("no macro typed: the published figures fill in", (() => { const p0 = w.gmMhMacro({}); return p0.set && p0.repo > 0 && p0.cpi > 0 && p0.repoOwn === false && p0.cpiOwn === false; })());
  ok("an invalid stored figure stays marked as yours, not silently replaced", (() => { const z = w.gmMhMacro({ repo: 0, cpi: 0 }); return z.set === false && z.repoOwn === true && z.cpiOwn === true; })());
  const al = w.gmMhAlloc(c);
  ok("the fixture mix is 70/30 against a 53% target", near(al.actual, 70) && al.t.target === 53 && al.breach, JSON.stringify([al.actual, al.t.target]));
  ok("inside the band: 5 points either way is no breach", !w.gmMhDrift(58, 53).breach && !w.gmMhDrift(48, 53).breach && w.gmMhDrift(58.1, 53).breach);
  ok("relative band: 25% of a small target", w.gmMhDrift(13, 10).breach && !w.gmMhDrift(12, 10).breach);
  const cad0 = w.gmMhCadence({ reviews: [], acts: [] }, iso(0));
  ok("no review this quarter: due", cad0.due && cad0.canAct);
  const cad1 = w.gmMhCadence({ reviews: [iso(0)], acts: [] }, iso(0));
  ok("reviewed this quarter: not due, so no nag", !cad1.due);
  const cad2 = w.gmMhCadence({ reviews: [], acts: [iso(-300), iso(-100)] }, iso(0));
  ok("two actions in 12 months: no third", !cad2.canAct && cad2.nextAct === iso(65), cad2.nextAct);
  ok("an action over a year ago no longer counts", w.gmMhCadence({ reviews: [], acts: [iso(-400), iso(-100)] }, iso(0)).canAct);
  const inBand = Object.assign({}, c, { eq: 1100000, debt: 900000 });
  ok("no nag inside the band: the drift finding is absent", !w.gmMhScan(inBand).some(f => f.issue === "alloc-drift"));
  ok("no nag once reviewed this quarter", !w.gmMhScan(Object.assign({}, c, { alloc: { reviews: [iso(0)], acts: [] } })).some(f => f.issue === "alloc-drift"));
  ok("no nag after two actions this year", !w.gmMhScan(Object.assign({}, c, { alloc: { reviews: [], acts: [iso(-200), iso(-30)] } })).some(f => f.issue === "alloc-drift"));
  const Ra = w.gmRemedies("alloc-drift", Object.assign({}, c, { al: al }));
  ok("rebalance with new money first", Ra.fixes[0].id === "alloc-newmoney" && /with no sale/.test(Ra.fixes[0].impact.headline));
  ok("the move = drift × total", near(al.move, 0.17 * 2000000, 1));

  // 4. the waterfall order
  const wf = w.gmMhWaterfall(1e9, { bufTarget: 6, bufGap: 1000, termGapPrem: 2000, healthGapPrem: 3000, costlyDebt: 4000 });
  ok("freed money flows: buffer, term, health, debt, then goals", wf.map(x => x.k).join() === "buffer,term,health,debt,goals" && wf[4].amt === 1e9 - 10000);
  const wf2 = w.gmMhWaterfall(2500, { bufGap: 1000, termGapPrem: 2000, healthGapPrem: 3000, costlyDebt: 4000 });
  ok("a small amount fills the first steps only", wf2.map(x => x.k + x.amt).join() === "buffer1000,term1500");
  ok("nothing negative from the waterfall", w.gmMhWaterfall(-5, { bufGap: -1 }).length === 0);

  // 5. Global hides what is true in one country only
  const G1 = w.gmMhScan(Object.assign({}, c, { local: false })).map(f => f.issue);
  ok("Global: no health-floor (city tiers), regular-plan or PLI finding", !G1.includes("health-below-floor") && !G1.includes("fund-regular") && !G1.includes("endow-low-return") && G1.includes("life-cover-gap"), G1.join());
  ok("Global: no India-tagged fix or note", ["endow-low-return", "alloc-drift", "fund-regular", "health-below-floor"].every(id => { const R = w.gmRemedies(id, Object.assign({}, cx, { local: false, termIn: c.need, al: al, regV: 1, stuAmt: 1 }));
    return R.fixes.every(x => !x.where) && R.notes.every(nt => !/data-where="IN/.test(nt)); }));

  // 6. the card: one open finding with one button, the rest under Later (n)
  w.goTab("money"); w.renderAll();
  const card = d.querySelector(".gm-mh");
  ok("the Money tab shows the Money health card", !!card);
  const items = card ? [...card.querySelectorAll(".gm-mh-item")] : [];
  ok("one finding open, the rest under Later (n), folded", items.length === L.length && card.querySelector(".gm-mh-item .gm-fix-best") && /Later \(\d+\)/.test(card.querySelector("details.gm-mh-later > summary").textContent) && !card.querySelector("details.gm-mh-later").open);
  ok("the open finding has one button", items[0] && items[0].querySelectorAll(".gm-fix-best button").length === 1);
  ok("each finding shows rupees a year freed or cover gained", items.every(it => /a year freed|cover \+|to move back/.test(it.querySelector(".gm-mh-n") ? it.querySelector(".gm-mh-n").textContent : "")), items.map(it => it.getAttribute("data-issue")).join());
  ok("an Add to calendar for the quarterly review, from the one registry", !!card.querySelector("[onclick=\"gmCalendar('mhealth')\"]") && w.gmCalendarICS("mhealth").includes("UID:securax-gm-money-health@local") && w.gmCalendarICS("mhealth").includes("RRULE:FREQ=YEARLY;BYMONTH=1,4,7,10;BYDAY=3SA"));
  ok("education, not advice; your decision", /Education, not advice: your decision/.test(card.textContent) && /SEBI-registered/.test(card.textContent));
  ok("the screen shows no NaN, Infinity or a negative rupee", !/NaN|Infinity|-₹|−₹/.test(card.textContent));
  // asked once: a policy row added by one tap carries example numbers to correct
  const before = JSON.parse(w.localStorage.getItem("gm_mhealth")).policies.length;
  w.gmMhAdd("term"); const s1 = JSON.parse(w.localStorage.getItem("gm_mhealth"));
  ok("one tap adds an example row to correct; a new term policy starts as applied, not in force", s1.policies.length === before + 1 && s1.policies[before].ex === 1 && s1.policies[before].st === "applied");
  w.gmMhSetP(before, "st", ""); w.gmMhSetP(before, "sa", "30000000");
  ok("marking the new term in force lifts the guard on the card", (() => { const c3 = w.gmMhCtx(); const f = w.gmMhScan(c3).find(x => x.issue === "endow-low-return"); return f && w.gmRemedies("endow-low-return", Object.assign({}, c3, f.ctx)).fixes.some(x => x.id === "endow-surrender"); })());
  w.gmMhDel("policies", before);
  // reviewed: the drift item leaves the list
  w.gmMhReview(0); ok("a review this quarter removes the drift nag", !w.gmMhScan(w.gmMhCtx()).some(f => f.issue === "alloc-drift"));

  // 7. no NaN, Infinity or negative values, even on damaged or odd inputs
  w.localStorage.setItem("gm_mhealth", JSON.stringify({ policies: [{ type: "endow", sa: "abc", prem: -5, start: "nope", term: "x" }, { type: "bogus" }, null, { type: "health", sa: 1e15, prem: "" }], funds: "x", macro: [], alloc: { reviews: "x" }, bench: { irr: "lots" } }));
  let threw = ""; try { w.renderAll(); } catch (er) { threw = String(er); }
  const c4 = w.gmMhCtx(), L4 = w.gmMhScan(c4), s4 = JSON.stringify([L4.map(f => [f.freedYear, f.coverGain, f.title, f.line]), w.gmMhAlloc(c4)]);
  ok("damaged storage: no crash", !threw, threw);
  ok("damaged storage: no NaN or Infinity in the findings", !/NaN|Infinity/.test(s4), s4.slice(0, 300));
  ok("freed rupees and cover are never negative", L.concat(L4).every(f => f.freedYear >= 0 && f.coverGain >= 0 && isFinite(f.freedYear) && isFinite(f.coverGain)));
  const odd = [w.gmMhEndow({ prem: 0, sa: 0, term: 0 }, { irr: 0, alt: 0, infl: 0 }), w.gmMhEndow({ prem: 1e6, sa: 1, term: 99, ppt: 99, start: "2001-01-01", sv: 0, pu: 0 }, { irr: 30, alt: 30, infl: 0 })];
  ok("odd policies: finite values", !/NaN|Infinity/.test(JSON.stringify(odd)) && odd.every(o => o.years >= 0 && o.premsLeft >= 0));
  ok("odd targets: inside 0 to 100", [w.gmMhTarget({ age: 99, horizon: 0, deps: 50, work: "contract", tilt: -99 }), w.gmMhTarget({ age: 18, horizon: 80, deps: 0, work: "permanent", tilt: 99 })].every(x => x.target >= 0 && x.target <= 100));
  ok("no target without an age", w.gmMhTarget({ age: 0 }) === null);

  // 8. pure, and no AI
  const fz = Object.freeze(Object.assign({}, c)), b4 = JSON.stringify(fz);
  ok("the scan is pure: same input, same answer, input untouched", JSON.stringify(w.gmMhScan(fz)) === JSON.stringify(w.gmMhScan(fz)) && JSON.stringify(fz) === b4);
  let ask = 0; const realAsk = w.gmAsk; w.gmAsk = () => { ask++; }; const f0 = fetches;
  w.gmMhScan(c); w.renderAll(); w.goTab("money");
  ok("the AI is never called and nothing goes to the network", ask === 0 && fetches === f0);
  w.gmAsk = realAsk;
  const src = fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8"), a = src.indexOf("── Money health (every-issue-has-a-path"), b = src.indexOf("// The Money tab shows it, after the numbers");
  ok("the money-health code calls no network, assistant or gateway", a > 0 && b > a && !/fetch\(|gmAsk|XMLHttpRequest|gateway|sendBeacon|WebSocket/.test(src.slice(a, b)));

  console.log("test173 money health: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
