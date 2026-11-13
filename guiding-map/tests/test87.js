// test87: calm luxury (owner, 2026-11-13 screenshots): one visual language, calm empty states, no duplicate objectives,
// a quiet delete away from the safe button, and the healthy band drawn on the spending bar.
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
let pass = 0, fail = 0;
function ok(c, m) { if (c) pass++; else { fail++; console.log("FAIL " + m); } }
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const w = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } }).window;
setTimeout(() => {
  try {
    const d = w.document;
    w.curTab = "risk"; w.renderAll();
    const cards = [...d.querySelectorAll(".kc.riskc")];
    ok(cards.length > 0, "the risk cards render");
    const status = cards.map(c => c.querySelector(".gm-status").textContent.trim());
    ok(!status.includes("Exposed"), "nothing started never shouts Exposed: " + status.join(","));
    ok(d.querySelectorAll(".kc.riskc.gm-start-here").length === 1 && d.querySelectorAll(".gm-start").length === 1, "exactly one risk says Start here");
    ok(/Health/.test(d.querySelector(".gm-start-here .kl").textContent), "the ladder starts with health");
    ok(cards.every(c => c.querySelector(".kv .gm-glyph i")), "every risk icon sits in a gold medallion");
    ok(!/⭐/.test(cards.map(c => c.innerHTML).join("")), "the vital-few mark is a gold star glyph, not an emoji button");
    const titles = [...d.querySelectorAll(".cat-t")];
    ok(titles.length && titles.every(t => !/^\s*\p{Extended_Pictographic}/u.test(t.textContent) || t.firstElementChild && t.firstElementChild.className === "gm-glyph"), "every section title's emoji is a medallion");
    w.renderAll(); w.renderAll();
    ok([...d.querySelectorAll(".cat-t")].every(t => t.querySelectorAll(".gm-glyph").length <= 1), "re-rendering never stacks medallions");
    // OKRs: duplicates merge once; adopting the same suggestion twice adds nothing.
    const kr = { t: "1 pathway researched", v: 0, at: 1 };
    w.S.okrs = [{ o: "Acquire geographic optionality", at: 1, krs: [Object.assign({}, kr)] }, { o: "Acquire geographic optionality", at: 2, krs: [Object.assign({}, kr)] }];
    ok(w.gmOkrDedupe() === 1 && w.S.okrs.length === 1, "an exact, untouched duplicate objective is merged");
    w.S.okrs.push({ o: "Acquire geographic optionality", at: 3, krs: [{ t: "1 pathway researched", v: 0.5, at: 3 }] });
    ok(w.gmOkrDedupe() === 0 && w.S.okrs.length === 2, "a copy with progress is never removed");
    w.S.okrs = [{ o: "Acquire geographic optionality", at: 1, krs: [Object.assign({}, kr)] }];
    w.__sugCache = { picks: [{ t: "Acquire geographic optionality", kr: "1 pathway researched" }] };
    w.adoptOKR(0); w.adoptOKR(0);
    ok(w.S.okrs.length === 1, "adopting the same suggestion again does not add a copy");
    w.curTab = "okr"; w.renderAll();
    const card = d.querySelector(".okr-card .gm-okr-acts");
    const del = card && card.querySelector(".gm-quiet"), add = card && card.querySelector(".gm-btn-ghost");
    ok(del && add && /Delete/.test(del.textContent) && del.getAttribute("aria-label"), "delete is a quiet, labelled text button");
    ok(del && !/redBg|--red/.test(del.getAttribute("style") || ""), "delete is not a coloured button beside the safe one");
    ok(d.querySelector(".okr-grade").getAttribute("style").indexOf("--muted") >= 0, "a zero score is muted, not red");
    ok(d.querySelectorAll(".kr .chips .chip").length >= 5, "the stage chooser is one segmented control");
    // Money: the band is visible on the bar; no off-palette blue.
    w.curTab = "money"; w.renderAll();
    ok(d.querySelectorAll(".csp-zone").length >= 2, "each spending bar shows its healthy band");
    ok(!/#1d4ed8/i.test(d.querySelector(".section.active").innerHTML), "no off-palette blue");
    ok(!!d.getElementById("gmCalmLux"), "the calm-luxury styles are in place");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test87 calm luxury: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
