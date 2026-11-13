// test90: an easy start (owner, 2026-11-13: "too many jargons", "exhausted to fill in the fields"). Plain English on screen,
// the research kept underneath (every translation still keyed on the original words), four questions answered by taps,
// the make-it-mine card first under the greeting, and nothing called "low" that the app does not know.
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const boot = (lang) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "http://localhost/",
  beforeParse(w) { Object.defineProperty(w.navigator, "languages", { get: () => [lang] }); w.matchMedia = (q) => ({ matches: /max-width/.test(q), media: q, addListener() {}, removeListener() {} });
    w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } }).window;
const w = boot("en-IN"), g = boot("gu-IN");
setTimeout(() => {
  try {
    const d = w.document; w.goTab("today");
    setTimeout(() => { try {
      const vis = []; const tw = d.createTreeWalker(d.body, 4); let n; while ((n = tw.nextNode())) { if (!/^(SCRIPT|STYLE)$/.test(n.parentElement.tagName)) vis.push(n.textContent); }
      const t = vis.join(" ");
      ok(/Three small things today/.test(t) && !/the floor is enough/.test(t), "the daily three reads in plain English");
      ok(/Your next step/.test(t) && !/Rule 1 says|L0 Identity|open action ·/i.test(t), "the next step has no method jargon");
      const sec = d.querySelector(".section.active"), greet = sec.querySelector(".gm-greet"), strip = sec.querySelector(".gm-setup");
      ok(greet && strip && (greet.compareDocumentPosition(strip) & 4), "make-it-mine is on Today, after the daily three (value first, then the ask; test41)");
      ok(/all taps/.test(strip.textContent) && /Make it mine/.test(strip.textContent), "the card promises taps, not typing");
      ok(w.gmPlain && w.gmPlain["Prime Directive Waterfall"] && Object.keys(w.gmPlain).length >= 20, "the plain-English layer covers the method names");
      ok(/Do the smallest version/.test(JSON.stringify(Object.keys(w.gmPlain))), "the plain layer is keyed on the original words (the research text is unchanged underneath)");
      // Gujarati keeps working: its catalog is keyed on the original English, not on the plain layer.
      ok(g.gmLang() === "gu" && g.document.getElementById("gmNav").textContent.includes("આજે"), "Gujarati is unaffected by plain English");
      // Four taps finish set-up.
      w.gmQuickSetup();
      let taps = 0;
      for (let i = 0; i < 4; i++) { const b = d.querySelectorAll(".gm-qtap"); if (b.length >= 5) { taps++; b[2].click(); } }
      ok(taps === 4, "every question can be answered with one tap: " + taps);
      ok(JSON.parse(w.localStorage.getItem("gm_quick_done")) === true, "four taps complete the set-up");
      w.renderAll();
      const buf = [...d.querySelectorAll("#gmVitals > div")].find(x => /Buffer|Runway/.test(x.textContent));
      ok(buf && !/low/.test(buf.getAttribute("aria-label") || "") && /—/.test(buf.textContent), "an unknown buffer is a calm dash, never 'low'");
    } catch (e) { fail++; console.log("FAIL threw " + e.message); }
    console.log("test90 easy start: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
    }, 300);
  } catch (e) { fail++; console.log("FAIL threw " + e.message); console.log("test90: " + pass + " passed, " + fail + " failed"); process.exit(1); }
}, 1800);
