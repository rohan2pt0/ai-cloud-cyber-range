// test92: a human's-eye pass (owner, 2026-11-13): plain questions, no doubled words, a 'No' hides what cannot apply,
// a calm Inbox (capture first, the laptop jobs folded), and a global job offer weighed in rupees you can actually use.
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const boot = (facts) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "http://localhost/",
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_intro_seen", "true"); if (facts) w.localStorage.setItem("gm_facts", JSON.stringify(facts)); } }).window;
const vis = (d, root) => { const out = []; const tw = d.createTreeWalker(root || d.body, 4); let n; while ((n = tw.nextNode())) if (!/^(SCRIPT|STYLE)$/.test(n.parentElement.tagName)) out.push(n.textContent); return out.join(" ").replace(/\s+/g, " "); };
const none = boot(null), no = boot({ kids: false, vehicle: false });
setTimeout(() => {
  try {
    none.goTab("okr");
    setTimeout(() => { try {
      const t = vis(none.document, none.document.querySelector(".section.active"));
      ok(!/Quarterly Quarter/i.test(t) && /Quarterly Goals/.test(t), "the goals heading reads 'Quarterly Goals', never 'Quarterly Quarter goals'");
      // a No hides what cannot apply; unanswered still shows
      const more = (w) => { w.gmNavMore && w.gmNavMore(true); return vis(w.document, w.document.getElementById("gmMoreSheet") || w.document.body); };
      ok(/\bKids\b/.test(more(none)), "Kids shows while the question is unanswered");
      ok(!/\bKids\b/.test(more(no)), "Kids is hidden after 'No children'");
      ok(none.RISKS.some(r => r.id === "r_vehicle") && !no.RISKS.some(r => r.id === "r_vehicle"), "the vehicle checklist leaves after 'No vehicle'");
      // Inbox: capture first, nothing to read first, the laptop jobs folded
      none.goTab("inbox");
      const sec = none.document.querySelector(".section.active");
      ok(sec.querySelector("#ibText") && /One line is enough/.test(sec.querySelector("#ibText").getAttribute("placeholder")), "the Inbox opens on one box: what is on your mind");
      ok(!sec.querySelector(".info") || sec.querySelector(".ibcap").compareDocumentPosition(sec.querySelector(".info")) & 4, "no paragraph to read before the box");
      const folds = [...sec.querySelectorAll("details.ib-fold")];
      ok(folds.length === 2 && folds.every(f => !f.open), "papers and reviews are folded to one line each");
      ok(/Papers to bring in/.test(folds[0].querySelector("summary").textContent) && /Reviews, when you have time/.test(folds[1].querySelector("summary").textContent), "each fold says plainly what it holds");
      // a global offer, in rupees you can use (fake numbers)
      const pay = none.gmOfferPay({ mode: "abroad", lpay: 20000, fx: 20, ltax: 0, lrent: 8000, lliving: 2000, lallow: 500, health: true });
      ok(pay.abroad && pay.inh === (20000 - 8000 - 2000 + 500) * 20, "abroad: pay minus rent and living costs plus allowances, at your rate, in rupees");
      ok(pay.ctc === 20000 * 12 * 20 && pay.tax === 0, "zero local tax stays zero, and no Indian tax is applied abroad");
      const taxed = none.gmOfferPay({ mode: "abroad", lpay: 10000, fx: 10, ltax: 20, lrent: 0, lliving: 0, lallow: 0, health: false });
      ok(taxed.inh === 80000 && taxed.usable < taxed.inh, "local tax is taken off, and health cover you buy yourself is counted");
    } catch (e) { fail++; console.log("FAIL threw " + e.message); }
    console.log("test92 human pass: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0); }, 300);
  } catch (e) { fail++; console.log("FAIL threw " + e.message); console.log("test92: " + pass + " passed, " + fail + " failed"); process.exit(1); }
}, 1800);
