// test89: Gujarati, held to a quality gate (owner, 2026-11-13: business communities speak Gujarati; many read little;
// "the translations are not accurate"). Real keys only, Gujarati script, numbers and symbols kept, one word per idea
// (the glossary), the device language as the default, and Listen only when the phone has a voice for that language.
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const I = (f) => JSON.parse(fs.readFileSync(path.join(__dirname, "..", "i18n", f), "utf8"));
const gu = I("lifeos.gu.json"), src = new Set(I("lifeos.source.json").strings.concat(["Today", "Inbox", "Goals", "Ask", "More", "Language", "Save encrypted backup", "Restore from file", "Later", "Danger zone"])), gl = I("glossary.gu.json");
const S = gu.strings, keys = Object.keys(S);
ok(gu._meta.locale === "gu-IN" && gu._meta.status === "beta" && /native Gujarati/.test(gu._meta.note), "the catalog names its locale, beta status and the native review still to come");
ok(keys.length >= 150, "the vital few are translated: " + keys.length);
ok(keys.every(k => src.has(k)), "every key is a real English string of the app: " + keys.filter(k => !src.has(k)).join(" | "));
ok(keys.every(k => /[઀-૿]/.test(S[k])), "every value is written in Gujarati script: " + keys.filter(k => !/[઀-૿]/.test(S[k])).join(" | "));
const sym = (s) => (s.match(/[0-9%₹→·▾◆☾+✨🏆😴📖•—]/gu) || []).sort().join("");
ok(keys.every(k => sym(k) === sym(S[k])), "numbers and symbols survive translation: " + keys.filter(k => sym(k) !== sym(S[k])).join(" | "));
ok(keys.every(k => gl.keep.every(t => !new RegExp("\\b" + t + "\\b").test(k) || S[k].includes(t))), "kept terms (SIP, INR, OKR, AI...) stay as written");
const terms = Object.entries(gl.terms);
const clash = keys.filter(k => terms.some(([en, g]) => new RegExp("(^|[^A-Za-z])" + en.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "([^A-Za-z]|$)").test(k) && !S[k].includes(g)));
ok(clash.length === 0, "one word per idea, as the glossary says: " + clash.join(" | "));
ok(!keys.some(k => /^(Arjun|Priya|Mumbai|India|Amazon|Decathlon)$/.test(k) || /^(INR|USD|AED|EUR|GBP|SGD)$/.test(k)), "names, places, brands and currency codes are never translated");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const boot = (lang, voices) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "http://localhost/",
  beforeParse(w) { Object.defineProperty(w.navigator, "languages", { get: () => [lang] }); Object.defineProperty(w.navigator, "language", { get: () => lang });
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true");
    if (voices) { w.speechSynthesis = { getVoices: () => voices, speaking: false, cancel() {}, speak() {}, addEventListener() {} }; w.SpeechSynthesisUtterance = function (t) { this.text = t; }; } } }).window;
const G1 = boot("gu-IN", [{ lang: "gu-IN", name: "Gujarati" }]), G2 = boot("gu-IN", [{ lang: "en-IN", name: "English" }]), G3 = boot("gu-IN", null);
setTimeout(() => {
  try {
    ok(G1.gmLang() === "gu" && G1.document.documentElement.lang === "gu", "a Gujarati phone opens in Gujarati by itself");
    ok(G1.document.getElementById("gmNav").textContent.includes(S.Today), "the navigation reads in Gujarati");
    G1.goTab("ops");
    ok(!!G1.document.querySelector('.gm-lang button[lang="gu"]') && /ગુજરાતી/.test(G1.document.querySelector('.gm-lang').textContent), "the switch offers ગુજરાતી in its own script");
    G1.curTab = "risk"; G1.renderAll(); G2.curTab = "risk"; G2.renderAll(); G3.curTab = "risk"; G3.renderAll();
    const b = G1.document.querySelector(".gm-hero > .gm-say");
    ok(b && b.getAttribute("aria-label") === "સાંભળો", "Listen shows, labelled in Gujarati, when the phone has a Gujarati voice");
    ok(!G2.document.querySelector(".gm-say") && !G3.document.querySelector(".gm-say"), "no Listen without a Gujarati voice (never Gujarati in an English accent) or with no speech at all");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  setTimeout(() => {
    ok(G1.document.querySelector(".gm-hero").textContent.includes(S["Risks covered"]), "the risk screen's top card reads in Gujarati (after the swap settles)");
    console.log("test89 Gujarati: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
  }, 300);
}, 1800);
