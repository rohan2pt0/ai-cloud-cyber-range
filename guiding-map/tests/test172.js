// test172: every flagged issue shows its fixes (principle every-issue-has-a-path, owner 2026-11-25). The Property tab's red
// numbers and warning cards each carry "How to fix it": the best fix open with its number and one button, the rest under
// More ways, worked out by code from the person's own numbers (standard amortisation), never by an AI. Fake data only: the
// figures follow a pattern (DSCR about 0.52, debt about 17.9 years of rent, break-even 192%, about ₹14,200 over the ₹2L cap).
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(); const iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: "1988-03-10", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 200000,
  kids: [], ret: 60, tsav: 20, example: false, earners: 1, loans: [] };
const flat = { n: "Test flat A", use: "letout", val: "90", rent: "26000", loan: "55.82", rate: "7.75", emi: "50000", out: "0", vac: "0",
  owner: "me", start: iso(-200), months: "11" };
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
let fetches = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_props", JSON.stringify([flat])); w.localStorage.setItem("gm_facts", JSON.stringify({ state: "MH" }));
    w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
    w.fetch = () => { fetches++; return Promise.reject(new Error("offline")); }; } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  // the person's own numbers, as the tab works them out
  const r = w.gmPropCalc(flat);
  ok("fixture: DSCR about 0.52", Math.abs(r.dscr - 0.52) < 0.005, r.dscr);
  ok("fixture: debt about 17.9 years of rent", Math.abs(r.debtToRent - 17.9) < 0.05, r.debtToRent);
  ok("fixture: break-even about 192%", Math.round(r.beOcc) === 192, r.beOcc);
  ok("fixture: about ₹14,200 over the ₹2L set-off cap", Math.abs(r.carryForward - 14200) < 50, r.carryForward);

  w.goTab("prop"); w.renderAll();
  const sec = d.getElementById("sections") || d.body;
  const blocks = [...sec.querySelectorAll(".gm-fix")], ids = blocks.map(b => b.getAttribute("data-issue"));
  ["dscr-low", "beocc-high", "debt-heavy", "setoff-cap", "papers-open"].forEach(id => ok("flagged issue " + id + " has a fix block", ids.includes(id), ids.join()));
  ok("every flagged warning card carries a fix block", [...sec.querySelectorAll(".gm-issue")].filter(c => /var\(--(red|amber)\)/.test(c.getAttribute("style"))).every(c => c.querySelector(".gm-fix")));
  blocks.forEach(b => {
    const id = b.getAttribute("data-issue");
    ok(id + ": exactly one fix is open", b.querySelectorAll(".gm-fix-best").length === 1);
    ok(id + ": the others fold under More ways (n)", !!b.querySelector("details.gm-fix-more") && /More ways \(\d+\)/.test(b.querySelector("details.gm-fix-more > summary").textContent) && !b.querySelector("details.gm-fix-more").open);
    ok(id + ": the working is one tap away (or the same step already led a block above)", !!b.querySelector(".gm-fix-best details.gm-fix-how") || /The same step as above/.test(b.querySelector(".gm-fix-best").textContent));
  });
  ok("the same lead fix is spelled out once, then named briefly", (sec.textContent.match(/The same step as above/g) || []).length >= 1 && sec.querySelectorAll('.gm-fix-best[data-rem="rate-reset"] details.gm-fix-how').length === 1);
  ok("a guard says what not to do: no prepay while the buffer is under 6 months", /What not to do: Do not prepay yet: it would leave 2\.5 months of buffer/.test(d.querySelector('.gm-fix[data-issue="debt-heavy"]').textContent), d.querySelector('.gm-fix[data-issue="debt-heavy"]').textContent.slice(-300));
  ok("a fix that does not move the issue's number never leads it", d.querySelector('.gm-fix[data-issue="debt-heavy"] .gm-fix-best').getAttribute("data-rem") === "rent-renewal");
  ok("the hard compliance fix leads the papers block", (d.querySelector('.gm-fix[data-issue="papers-open"] .gm-fix-best') || {}).getAttribute && d.querySelector('.gm-fix[data-issue="papers-open"] .gm-fix-best').getAttribute("data-rem") === "police");
  // plain-first (2026-11-25): a weak number sits inside its problem's one card, under "How we worked this out", beside that card's best fix
  ok("a red number never stands alone: each red measure sits in a card that carries its best fix", [...sec.querySelectorAll(".gm-num.gm-v-r")].every(n => { const card = n.closest(".gm-issue"); return card && card.querySelector(".gm-fix .gm-fix-best") && n.closest("details.gm-pf-how"); }));
  ok("the best fix for the EMI gap is one call to the lender", d.querySelector('.gm-fix[data-issue="dscr-low"] .gm-fix-best').getAttribute("data-rem") === "rate-reset");

  // the EMI saving per 0.25% from the standard amortisation formula, on the person's own loan
  const c = w.gmRemedyCtx(0), L = 5582000, E = 50000, i0 = 7.75 / 1200;
  const n = -Math.log(1 - i0 * L / E) / Math.log(1 + i0), emi = (rate, m) => { const i = rate / 1200, f = Math.pow(1 + i, m); return L * i * f / (f - 1); };
  const want = emi(7.75, n) - emi(7.5, n), rr = w.gmRemedies("dscr-low", c).fixes.find(x => x.id === "rate-reset");
  ok("EMI saving per 0.25% matches the amortisation formula within ₹1", rr && Math.abs(rr.impact.rupeesPerMonth - want) < 1, rr && rr.impact.rupeesPerMonth + " vs " + want);
  ok("the formula gives back the EMI the person entered", Math.abs(emi(7.75, n) - E) < 0.01 && Math.abs(w.gmRemEmi(L, 7.75, n) - E) < 0.01);
  ok("break-even months = fee ÷ saving, with the ₹10,000 default", rr && rr.impact.breakEvenMonths === Math.ceil(10000 / want) && c.feeAssumed);
  ok("the saving is shown, never a hard-coded figure", d.querySelector('.gm-fix[data-issue="dscr-low"]').textContent.includes("+" + new w.Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Math.round(want)) + " a month"));
  ok("the default is said and can be changed", /Assumes a fee of ₹10,000/.test(d.querySelector('.gm-fix[data-issue="dscr-low"]').textContent));

  // rent at renewal: the new DSCR is the new rent over the EMI
  const rn = w.gmRemedies("dscr-low", c).fixes.find(x => x.id === "rent-renewal");
  ok("escalation DSCR = new rent ÷ EMI", rn && Math.abs(rn.impact.newDscr - 26000 * 1.05 / 50000) < 1e-9 && rn.impact.metricBefore === "0.52×" && rn.impact.metricAfter === "0.55×", rn && JSON.stringify([rn.impact.newDscr, rn.impact.metricBefore, rn.impact.metricAfter]));
  ok("rent rise: rupees a month = 5% of the rent", rn && Math.abs(rn.impact.rupeesPerMonth - 1300) < 1e-9);
  ok("the 11-month practice in Maharashtra is a tagged note, said as practice", /data-where="IN-MH"[^>]*>In Maharashtra, leave-and-licence agreements usually run 11 months/.test(d.querySelector('.gm-fix[data-issue="dscr-low"]').innerHTML) && /not a right to a rise/.test(d.querySelector('.gm-fix[data-issue="dscr-low"]').textContent));

  // prepayment: a hard guard keeps 6 months of buffer
  const base = Object.assign({}, c, { prepay: 50000, prepayAssumed: false, rateType: "floating", rateTypeAssumed: false });
  const low = w.gmRemedies("debt-heavy", Object.assign({}, base, { buffer: 3, liquid: 150000, bufferGap: 50000 }));
  ok("prepay is hidden when the buffer would fall under 6 months", !low.fixes.some(x => x.id === "prepay") && low.guards.some(g => /Do not prepay yet/.test(g) && /2\.0 months/.test(g)), JSON.stringify(low.guards));
  const high = w.gmRemedies("debt-heavy", Object.assign({}, base, { buffer: 20, liquid: 1000000, bufferGap: 50000 }));
  const pp = high.fixes.find(x => x.id === "prepay");
  const n1 = -Math.log(1 - i0 * (L - 50000) / E) / Math.log(1 + i0);
  ok("prepay with a healthy buffer: months cut and interest saved by amortisation", pp && Math.abs(pp.impact.monthsCut - (n - n1)) < 1e-6 && Math.abs(pp.impact.interestSaved - (E * (n - n1) - 50000)) < 1e-3, pp && JSON.stringify(pp.impact));
  ok("prepay: the new debt-to-rent years", pp && Math.abs(pp.impact.newDebtToRent - (L - 50000) / 312000) < 1e-9 && pp.impact.metricAfter === ((L - 50000) / 312000).toFixed(1) + " yrs");
  ok("prepay on a fixed rate says to check the lender's fee", (w.gmRemedies("debt-heavy", Object.assign({}, base, { buffer: 20, liquid: 1000000, bufferGap: 50000, rateType: "fixed" })).fixes.find(x => x.id === "prepay") || {}).preNote === "A fixed rate: check your lender's prepayment fee first.");
  ok("a fixed rate never leads the block", w.gmRemedies("debt-heavy", Object.assign({}, base, { buffer: 20, liquid: 1000000, bufferGap: 50000, rateType: "fixed" })).fixes[0].pre === true);

  // tax: old regime only; the new regime hides the set-off fix and says why
  const oldR = w.gmRemedies("setoff-cap", c);
  ok("old regime: the ₹2L set-off fix, valued at the derived 30% slab plus cess", oldR.fixes.some(x => x.id === "setoff-claim" && Math.abs(x.impact.rupeesPerMonth * 12 - 200000 * 0.3 * 1.04) < 1e-6), JSON.stringify(oldR.fixes.map(x => x.id)));
  ok("old regime: the rest is carried forward", oldR.fixes.some(x => x.id === "setoff-carry" && /Carry ₹14,20\d forward/.test(x.title)));
  const noSlab = w.gmRemedies("setoff-cap", Object.assign({}, c, { slab: null })).fixes.find(x => x.id === "setoff-claim");
  ok("slab unknown: a range at 20% and 30% plus cess", noSlab && /₹41,600 to ₹62,400 a year/.test(noSlab.impact.headline), noSlab && noSlab.impact.headline);
  const newR = w.gmRemedies("setoff-cap", Object.assign({}, c, { regime: "new", regimeAssumed: false }));
  ok("new regime: no set-off fix", !newR.fixes.some(x => x.id === "setoff-claim" || x.id === "setoff-carry"));
  ok("new regime: the old-regime note shows", newR.notes.some(x => /applies under the old regime only/.test(x)));
  ok("new regime: a regime check is offered instead", newR.fixes.some(x => x.id === "regime-check"));
  w.gmRemRegime("new"); w.renderAll();
  const sb = d.querySelector('.gm-fix[data-issue="setoff-cap"]');
  ok("new regime on the screen: the note, and no set-off claim", sb && /applies under the old regime only/.test(sb.textContent) && !sb.querySelector('[data-rem="setoff-claim"]'));
  w.gmRemRegime("old");

  // the owner who can claim is the one who also borrows
  ok("owner and borrower the same: no warning", w.gmRemedies("setoff-cap", c).warns.length === 0);
  const mis = w.gmRemedies("setoff-cap", Object.assign({}, c, { owner: "partner", borrower: "me" }));
  ok("owner not the borrower: a warning", mis.warns.length === 1 && /Only an owner who is also a borrower can claim the interest/.test(mis.warns[0]), JSON.stringify(mis.warns));
  w.gmPropSet(0, "owner", "partner"); w.renderAll();
  ok("owner not the borrower: the warning is on the screen", !!d.querySelector('.gm-fix[data-issue="setoff-cap"] .gm-fix-warn'));
  w.gmPropSet(0, "owner", "me"); w.renderAll();

  // hold or sell only when it is truly heavy, and as a question
  ok("hold-or-sell: only under DSCR 0.6 and break-even 150%, and never first", (() => { const f = w.gmRemedies("dscr-low", c).fixes; const h = f.findIndex(x => x.id === "hold-sell"); return h > 0 && f[h].question && !w.gmRemedies("dscr-low", Object.assign({}, c, { dscr: 0.8 })).fixes.some(x => x.id === "hold-sell"); })());
  ok("room by room is folded, never the open fix", w.gmRemedies("yield-thin", c).fixes[0].id !== "rooms");
  ok("Global hides fixes true in one country only", !w.gmRemedies("setoff-cap", Object.assign({}, c, { local: false })).fixes.length && w.gmRemedies("dscr-low", Object.assign({}, c, { local: false })).fixes.every(x => !x.where));

  // pure, and no AI: the same ctx gives the same answer, the ctx is untouched, and nothing reaches out
  const fz = Object.freeze(Object.assign({}, c)), before = JSON.stringify(fz);
  const f0 = fetches, issues = Object.keys(w.GM_REMEDIES);
  let same = true; issues.forEach(id => { if (JSON.stringify(w.gmRemedies(id, fz)) !== JSON.stringify(w.gmRemedies(id, fz))) same = false; });
  ok("the remedies are pure: same ctx, same fixes; ctx unchanged", same && JSON.stringify(fz) === before);
  let ask = 0; const realAsk = w.gmAsk; w.gmAsk = () => { ask++; };
  issues.forEach(id => w.gmRemedies(id, fz)); w.renderAll();
  ok("the AI is never called and nothing goes to the network", ask === 0 && fetches === f0);
  w.gmAsk = realAsk;
  const src = issues.map(id => w.GM_REMEDIES[id].map(R => [R.impact, R.preconditions, R.guard || "", R.doIt || ""].join("\n")).join("\n")).join("\n");
  ok("no fix reads storage, the network or the assistant", !/fetch\(|gmAsk|localStorage|XMLHttpRequest|\bG\(/.test(src));

  // no NaN, Infinity or negative months, also on awkward inputs
  const odd = [Object.assign({}, c, { emi: 30000 }), Object.assign({}, c, { rent: 0, dscr: 0 }), Object.assign({}, c, { loan: 0, emi: 0 }), Object.assign({}, c, { rate: 0 }), Object.assign({}, c, { prepay: 1e9, buffer: 50, liquid: 2e9, bufferGap: 1 })];
  let bad = [];
  [c].concat(odd).forEach((cx, k) => issues.forEach(id => { const R = w.gmRemedies(id, cx); const s = JSON.stringify(R);
    if (/NaN|Infinity|null,"metricBefore"|-\d[\d,.]* months?/.test(s)) bad.push(k + ":" + id);
    R.fixes.forEach(x => { const im = x.impact; ["monthsCut", "breakEvenMonths", "interestSaved"].forEach(k2 => { if (im[k2] !== undefined && !(im[k2] >= 0 && isFinite(im[k2]))) bad.push(k + ":" + id + ":" + x.id + ":" + k2); }); }); }));
  ok("no NaN, Infinity or negative months, even on odd inputs", !bad.length, bad.join(" "));
  const txt = [...d.querySelectorAll(".gm-fix")].map(b => b.textContent).join(" ");
  ok("the screen shows no NaN, Infinity or negative months", !/NaN|Infinity|−\d+ months?|-\d+ months?/.test(txt));
  ok("the EMI below the interest: no prepay fix, no endless months", !w.gmRemedies("debt-heavy", Object.assign({}, base, { emi: 30000, buffer: 20, liquid: 1e7, bufferGap: 1000 })).fixes.some(x => x.id === "prepay"));

  // asked once, with a default: the inputs live in the property's own numbers, and the link opens them
  w.gmRemAsk(0, "fee");
  const nums = d.querySelector('details.gm-prop-nums[data-pi="0"]');
  ok("'tap to change' opens the numbers at the fee", nums && nums.open && !!nums.querySelector('input[data-rk="fee"]'));
  w.gmPropSet(0, "fee", "5000"); w.renderAll();
  const rr2 = w.gmRemedies("dscr-low", w.gmRemedyCtx(0)).fixes.find(x => x.id === "rate-reset");
  ok("a fee the person gives replaces the default", rr2 && !w.gmRemedyCtx(0).feeAssumed && rr2.impact.breakEvenMonths === Math.ceil(5000 / want));

  console.log("test172 every issue has a path: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
}, 400);
