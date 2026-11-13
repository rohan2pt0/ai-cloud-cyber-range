// test91: one question a day (owner, 2026-11-13: never block a person until every detail is filled; fill it in gradually).
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const w = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "http://localhost/",
  beforeParse(w) { w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } }).window;
setTimeout(() => {
  try {
    const d = w.document, ask = () => d.querySelector(".gm-ask:not(.gm-ask-done)");
    w.goTab("today");
    ok(!ask(), "while the four-tap set-up waits, that is the only ask (one ask at a time)");
    ok(!!d.querySelector(".gm-daily, .gm-d3, .tile") || /Three small things|daily three/i.test(d.body.innerHTML), "Today is fully usable before any question is answered");
    w.gmQuickSetup(); for (let i = 0; i < 4; i++) d.querySelectorAll(".gm-qtap")[2].click();
    w.renderAll();
    const q1 = ask();
    ok(q1 && /Money in your bank accounts and FDs/.test(q1.textContent) && q1.querySelectorAll(".gm-qtap").length === 5, "the first daily question is the riskiest gap: cash on hand, five taps");
    ok(q1 && /Not now/.test(q1.textContent), "every question can be put off");
    const before = w.gmAskProgress().known;
    q1.querySelectorAll(".gm-qtap")[2].click();
    ok(w.gmAskProgress().known === before + 1, "one tap makes the app know one more thing");
    const buf = [...d.querySelectorAll("#gmVitals > div")].find(x => /Buffer|Runway/.test(x.textContent));
    ok(buf && /m/.test(buf.querySelector(".gm-vv").textContent) && !/—/.test(buf.querySelector(".gm-vv").textContent), "the buffer becomes a real number of months");
    ok(!ask() && /Today’s question done/.test(d.querySelector(".gm-ask-done").textContent), "after one answer: a small win, not another demand");
    w.gmAskMore(); const q2 = ask();
    ok(q2 && q2.querySelectorAll(".gm-qtap").length === 2 && /Yes/.test(q2.textContent), "One more? offers the next question, yes or no");
    q2.querySelectorAll(".gm-qtap")[1].click(); w.gmAskMore();
    ok(Object.keys(JSON.parse(w.localStorage.getItem("gm_facts") || "{}")).length >= 1, "the answer is saved as a fact the life systems use");
    w.gmAskLater();
    ok(!ask(), "Not now hides it until tomorrow");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test91 one question a day: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
}, 1800);
