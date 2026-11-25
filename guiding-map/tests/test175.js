// test175: plain words first on the Property tab (principle plain-first, owner 2026-11-25). One card per problem, with a
// headline in everyday words built from the person's own numbers, a calm state word, the best fix with its rupees, and the
// ratio, its technical name, formula, aim and source one tap away under "How we worked this out". Fake data only, shaped
// like the owner's screenshot: rent ₹26,000 against an EMI of ₹50,000, a loan of about ₹55.8 lakh.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const t = new Date(); const iso = (days) => { const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const prof = { name: "Fake Person", dob: "1988-03-10", country: "India", cur: "INR", gross: 180000, net: 120000, exp: 80000, sav: 200000, kids: [], ret: 60, tsav: 20, example: false, earners: 1, loans: [] };
const mk = (o) => Object.assign({ n: "Test flat A", use: "letout", val: "90", rent: "26000", loan: "55.82", rate: "7.75", emi: "50000", out: "0", vac: "0", owner: "me", start: iso(-200), months: "11" }, o || {});
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
const boot = (flat, cb) => {
  const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof)); w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
      w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_props", JSON.stringify([flat])); w.localStorage.setItem("gm_facts", JSON.stringify({ state: "MH" }));
      w.matchMedia = mm; w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
  setTimeout(() => { dom.window.goTab("prop"); dom.window.renderAll(); cb(dom.window, dom.window.document); }, 400);
};
const TERMS = /\bDSCR\b|\bKPIs?\b|\bKRIs?\b|\bX?IRR\b|\bCAGR\b|\bamorti[sz]ation\b|\boccupancy\b|\bLTV\b|\bdebt-to\b|\bratios?\b|×|\bbasis points?\b|\bbps\b|\balpha\b|\bbeta\b|\bSharpe\b|\bdrawdowns?\b|\bcorpus\b/i;
// the text a person sees by default: not inside a closed <details>, and not inside "How we worked this out"
function visible(root) {
  const out = [];
  (function walk(n) {
    if (n.nodeType === 3) { out.push(n.textContent); return; }
    if (n.nodeType !== 1 || n.tagName === "SCRIPT" || n.tagName === "STYLE") return;
    if (n.tagName === "DETAILS") { const s = n.querySelector(":scope > summary"); if (s && /How we worked this out/i.test(s.textContent)) return; if (!n.open) { if (s) out.push(s.textContent); return; } }
    n.childNodes.forEach(walk); out.push(" ");
  })(root);
  return out.join("");
}
const rs = (w, n) => new w.Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

boot(mk(), (w, d) => {
  const sec = d.getElementById("sections");
  const r = w.gmPropCalc(mk());
  ok("fixture: rent covers about half the EMI, debt about 18 years of rent, break-even above 100%", Math.abs(r.dscr - 0.52) < 0.005 && Math.round(r.debtToRent) === 18 && r.beOcc > 100, [r.dscr, r.debtToRent, r.beOcc].join());

  // one card per problem, not three
  const cards = [...sec.querySelectorAll(".gm-pf")], ids = cards.map(c => c.getAttribute("data-issue"));
  ["dscr-low", "beocc-high", "debt-heavy"].forEach(id => ok("one card for " + id + " (not a row, a fix line and a warning)", ids.filter(x => x === id).length === 1, ids.join()));
  ok("no old warning card or red 'Best fix' line is left", !/Rent does not cover the EMI|Break-even occupancy above 100%|Debt is heavy against rent/.test(visible(sec)) && !sec.querySelector(".gm-fix-kpi"));
  ok("a card's fix block is inside the card", cards.every(c => c.querySelectorAll(".gm-fix").length <= 1) && cards.filter(c => c.getAttribute("data-issue") === "dscr-low").every(c => !!c.querySelector(".gm-fix")));

  // the headlines, from the numbers
  const head = (id) => (sec.querySelector('.gm-pf[data-issue="' + id + '"] .gm-pf-head') || { textContent: "" }).textContent;
  ok("rent pays about half the EMI, and you add ₹24,000 a month", head("dscr-low") === "Rent pays about half your EMI. You add " + rs(w, 24000) + " a month.", head("dscr-low"));
  ok("the loan would take about 18 years of rent to clear", head("debt-heavy") === "At today's rent, the loan would take about 18 years of rent to clear.", head("debt-heavy"));
  ok("even rented all year, this flat costs you money", head("beocc-high") === "Even rented all year, this flat costs you money.", head("beocc-high"));

  // the summary on top
  const sum = (sec.querySelector(".gm-pf-sum") || { textContent: "" }).textContent;
  ok("one plain line on top: the monthly cost and the best next step", sum.startsWith("This flat costs you " + rs(w, 24000) + " a month. Best next step: ask your lender for a 0.25% lower rate (saves about ") && /a month\)\.$/.test(sum), sum);
  const want = w.gmRemedies("dscr-low", w.gmRemedyCtx(0)).fixes.find(x => x.id === "rate-reset").impact.rupeesPerMonth;
  ok("the saving in the line is the engine's own number", sum.includes(rs(w, want)), sum + " / " + want);

  // the state word is calm, never WEAK in red capitals; amber unless it is a real emergency
  const state = (id) => (sec.querySelector('.gm-pf[data-issue="' + id + '"] .gm-pf-state') || { textContent: "" }).textContent.trim();
  ok("a calm state word", state("dscr-low") === "Needs attention" && !/\bWeak\b/i.test(visible(sec)), state("dscr-low"));
  ok("amber, not red, when the top-up is under half of take-home", /var\(--amber\)/.test(cards[0].getAttribute("style")) && !/var\(--red\)/.test(cards[0].getAttribute("style")));
  ok("one open action: one problem in view, the others under Later (n)", cards.filter(c => !c.closest("details.gm-later")).length === 1 && /Later \(\d+\)/.test(sec.querySelector("details.gm-later > summary").textContent));

  // the default view has no jargon at all, and the fold still holds the depth
  const vis = visible(sec);
  ok("the default view of the Property tab contains no jargon term", !TERMS.test(vis), (vis.match(new RegExp(TERMS.source, "gi")) || []).join(" | "));
  const fold = sec.querySelector('.gm-pf[data-issue="dscr-low"] details.gm-pf-how'), ft = fold ? fold.textContent : "";
  ok("the fold is closed by default and named 'How we worked this out'", fold && !fold.open && /How we worked this out/.test(fold.querySelector("summary").textContent));
  ok("the fold keeps DSCR, the formula, the aim and the source", /DSCR/.test(ft) && /rent × \(12 − vacant months\) ÷ \(EMI × 12\)/.test(ft) && /Lenders like 1\.2× or more/.test(ft) && /Source:/.test(ft) && /0\.52×/.test(ft), ft.slice(0, 300));
  const bo = sec.querySelector('.gm-pf[data-issue="beocc-high"] details.gm-pf-how'), dh = sec.querySelector('.gm-pf[data-issue="debt-heavy"] details.gm-pf-how');
  ok("the other two folds keep their technical name and number", bo && /Break-even occupancy/.test(bo.textContent) && /192%/.test(bo.textContent) && dh && /Debt to rent/.test(dh.textContent) && /17\.9 yrs/.test(dh.textContent));
  ok("nothing is lost: every old measure is still on the page, in a fold or under Later", ["Rent-to-EMI cover", "Debt-to-rental-income", "Break-even occupancy", "Monthly cash flow", "Net rental yield", "Loan-to-value"].every(n => [...sec.querySelectorAll(".gm-metric")].some(m => m.textContent.includes(n))));
  ok("the ratio's move in a fix is in the fix's own fold, not the line", !/Rent-to-EMI 0\.52/.test(vis) && /Rent-to-EMI: 0\.52× → /.test(sec.textContent));


  // the engine's numbers are unchanged
  const c = w.gmRemedyCtx(0), L = 5582000, E = 50000, i0 = 7.75 / 1200, n = -Math.log(1 - i0 * L / E) / Math.log(1 + i0), emi = (rate) => { const i = rate / 1200, f = Math.pow(1 + i, n); return L * i * f / (f - 1); };
  ok("REMEDIES: the saving per 0.25% is still the amortisation formula", Math.abs(want - (emi(7.75) - emi(7.5))) < 1, want);
  ok("REMEDIES: the plain flag changes words only, never numbers", JSON.stringify(w.gmRemedies("dscr-low", c).fixes.map(x => x.impact.rupeesPerMonth)) === JSON.stringify(w.gmRemedies("dscr-low", Object.assign({}, c, { plain: true })).fixes.map(x => x.impact.rupeesPerMonth)));
  ok("no NaN, Infinity or undefined on the tab", !/NaN|Infinity|undefined/.test(sec.textContent));
  next();
});

function next() {
  // words follow the numbers: a third, most; tight, not over 100%; a lighter debt; a flat that pays for itself
  boot(mk({ rent: "17000", emi: "50000", loan: "30" }), (w, d) => {
    const sec = d.getElementById("sections"), h = (id) => (sec.querySelector('.gm-pf[data-issue="' + id + '"] .gm-pf-head') || { textContent: "" }).textContent;
    ok("a third: rent 17,000 against an EMI of 50,000", /^Rent pays about a third of your EMI\. You add ₹33,000 a month\.$/.test(h("dscr-low")), h("dscr-low"));
    ok("no NaN on a second flat", !/NaN|Infinity|undefined/.test(sec.textContent));
    boot(mk({ rent: "45000", emi: "50000", loan: "30", out: "0" }), (w2, d2) => {
      const s2 = d2.getElementById("sections"), h2 = (id) => (s2.querySelector('.gm-pf[data-issue="' + id + '"] .gm-pf-head') || { textContent: "" }).textContent;
      ok("most: rent 45,000 against an EMI of 50,000", /^Rent pays most of your EMI\. You add ₹5,000 a month\.$/.test(h2("dscr-low")), h2("dscr-low"));
      boot(mk({ rent: "80000", emi: "20000", loan: "20", rate: "8", out: "0" }), (w3, d3) => {
        const s3 = d3.getElementById("sections"), sum3 = (s3.querySelector(".gm-pf-sum") || { textContent: "" }).textContent;
        ok("a flat that pays for itself says so, in rupees", /^This flat pays for itself: about ₹60,000 a month is left after the loan and costs\.$/.test(sum3), sum3);
        ok("no problem card, and no jargon, when all is well", !s3.querySelector('.gm-pf[data-issue="dscr-low"]') && !TERMS.test(visible(s3)), visible(s3).match(new RegExp(TERMS.source, "gi")));
        console.log("test175 plain-first property: " + P + " passed, " + F + " failed"); e.forEach(x => console.log("  " + x)); process.exit(F ? 1 : 0);
      });
    });
  });
}
