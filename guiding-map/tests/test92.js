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
      // Tidy, permanent fixes: round checks, no crushed rows, engraved tags, plain guide titles (owner screenshots, 2026-11-13).
      const lux = none.document.getElementById("gmCalmLux").textContent;
      ok(/\.gm-tap\.gm-chk\{[^}]*width:44px/.test(lux) && /\.gm-tap\.gm-chk\.on::after/.test(lux), "tick boxes are a small round check inside a 44 px tap area");
      ok(/\[style\*='display:flex'\] > button\.btn[^{]*\{width:auto/.test(lux), "a button in a row sizes to its content, so text beside it is never crushed");
      ok(/\.stk-k\{background:transparent!important/.test(lux), "metric labels are engraved tags, not gold slabs");
      none.goTab("guide");
      const gt = vis(none.document, none.document.querySelector(".section.active"));
      ok(/max-width:440px/.test(lux) && !/\.ws-tap\.on\{[^}]*radial-gradient/.test(lux) && /min-width:900px\)\{html body #sections\{max-width:820px/.test(lux), "on a laptop: keys stay key-sized, jade has a stone's gloss (no painted blob), one centred column");
      ok(!/OPSEC:/.test(gt) && /Pick a password manager/.test(gt) && none.document.querySelector(".guide-card .gm-gt small"), "guides read plainly, with the tag on its own small line");
      // offer scores use the same keycaps as the Wheel; must-have status is a small round mark
      none.localStorage.setItem("gm_career", JSON.stringify({ offers: [{ name: "Fake option", mode: "salary", ctc: 0, gates: {}, scores: {} }], cfg: {}, cur: {}, house: {}, done: {}, gaps: {} }));
      none.goTab("career");
      const keys = none.document.querySelectorAll(".gm-scale .ws-tap.gm-key");
      ok(keys.length >= 5 && none.document.querySelector(".gm-gate") && !none.document.querySelector('.section.active .gm-tap[style*="min-width:30px"]'), "offer scores are keycaps in a tray and must-haves are small round marks");
      keys[2].click();
      ok(none.document.querySelectorAll(".gm-scale .gm-key.on").length === 1, "a tapped score turns jade");
      // readable money, guides and stages (owner screenshots, 2026-11-13)
      none.goTab("life");
      const met = none.document.querySelector(".meter");
      ok(met && met.querySelector(".meter-you") && /You \d+%/.test(met.querySelector(".meter-you").textContent) && met.querySelector(".meter-band-l") && met.querySelector(".meter-scale"), "a money meter labels your value, the healthy zone and the scale");
      ok(/Healthy|Low|High/.test(met.querySelector(".meter-status").textContent), "the status word matches the band");
      none.goTab("guide");
      ok(none.document.querySelectorAll(".guide-card .gs-k").length >= 4 && !/• BITWARDEN/.test(vis(none.document, none.document.querySelector(".section.active"))), "guide steps read as a small label and its text, not a shouted line");
      ok(/--accent:#b8902f/.test(lux) && /--line:var\(--border\)/.test(lux), "the guides' drawings use defined colours (no black bar, a visible box)");
      none.goTab("book");
      ok(none.document.querySelectorAll(".pb-list li").length >= 4, "stage cards turn ' · ' runs into short lists");
      const lis = [...none.document.querySelectorAll(".pb-list li")].map(x => x.textContent.trim());
      ok(!lis.some(t => t.length < 20 && !/^\S/.test("x")) && !lis.includes("sweep-in FD"), "a short inline list inside a sentence is never split into broken bullets");
      ok(none.document.querySelectorAll(".pb-num li").length >= 4, "circled ① ② ③ ④ runs become a numbered list");
      none.goTab("today");
      ok(none.document.querySelectorAll(".gm-energy .ws-tap.gm-key").length === 5, "energy uses the same keycaps as the Wheel");
      // a mistaken answer is never lost: answered questions stay one tap away while others wait
      none.localStorage.setItem("gm_facts", JSON.stringify({ partner: true })); none.goTab("systems");
      const ans = none.document.querySelector("details.gm-answers");
      ok(ans && /Your answers \(1\)/.test(ans.textContent) && /partner/i.test(ans.textContent) && ans.querySelector('button[aria-pressed="true"]'), "an answered question stays reachable, its answer shown, while others are still open");
    } catch (e) { fail++; console.log("FAIL threw " + e.message); }
    console.log("test92 human pass: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0); }, 300);
  } catch (e) { fail++; console.log("FAIL threw " + e.message); console.log("test92: " + pass + " passed, " + fail + " failed"); process.exit(1); }
}, 1800);
