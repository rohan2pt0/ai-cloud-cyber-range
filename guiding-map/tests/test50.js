// v50: the Life OS speaks Hindi and Marathi (owner, 2026-11-11). A switch on Ops, the device language as the first default,
// exact-match swaps after each render (never a key, never blank: anything untranslated stays English), attributes too,
// the page's lang follows, and switching back restores English. Catalogs live in guiding-map/i18n and are inlined offline.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const boot = (lang) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { Object.defineProperty(w.navigator, "languages", { get: () => [lang] }); Object.defineProperty(w.navigator, "language", { get: () => lang });
    w.localStorage.setItem("sovP", JSON.stringify({ name: "Fake", dob: "1990-05-15", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000, nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, dream: "UAE", example: false }));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
const hi = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'i18n', 'lifeos.hi.json'), 'utf8')), mr = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'i18n', 'lifeos.mr.json'), 'utf8'));
const E = boot("en-GB"), H = boot("hi-IN");
setTimeout(() => {
  const nav = (w) => (w.document.getElementById("gmNav") || w.document.body).textContent;
  ok("English device: English, lang=en", E.window.gmLang() === "en" && E.window.document.documentElement.lang === "en" && /Today/.test(nav(E.window)));
  ok("Hindi device: Hindi by itself, lang=hi", H.window.gmLang() === "hi" && H.window.document.documentElement.lang === "hi" && nav(H.window).includes(hi.strings.Today), nav(H.window).slice(0, 80));
  const w = E.window; w.goTab("ops");
  const sw = w.document.querySelector('.gm-lang button[lang="mr"]');
  ok("Ops has a language switch with each name in its own script", sw && /मराठी/.test(sw.textContent) && w.document.querySelector('.gm-lang button[lang="hi"]'));
  sw.click();
  setTimeout(() => {
    ok("one tap switches to Marathi, sets lang and is remembered", w.gmLang() === "mr" && w.document.documentElement.lang === "mr" && JSON.parse(w.localStorage.getItem("gm_lang")) === "mr");
    ok("the screen shows Marathi words", w.document.body.textContent.includes(mr.strings["Save encrypted backup"]), "");
    ok("the beta note shows", /Beta/.test(w.document.querySelector(".gm-lang").textContent) || /बीटा/.test(w.document.querySelector(".gm-lang").textContent));
    ok("untranslated text stays English, never a key", /System health|Back up now|Who touched my data/.test(w.document.body.textContent));
    w.goTab("today");
    setTimeout(() => {
      ok("a new render is translated too", nav(w).includes(mr.strings.Today));
      w.gmSetLang("en");
      ok("switching back restores English", nav(w).includes("Today") && !nav(w).includes(mr.strings.Today) && w.document.documentElement.lang === "en");
      ok("catalogs name their locale and status", [hi, mr].every(c => c._meta && /-IN$/.test(c._meta.locale) && c._meta.status));
      ok("Hindi and Marathi cover the same strings", Object.keys(hi.strings).sort().join("|") === Object.keys(mr.strings).sort().join("|"));
      ok("the catalogs are inlined for offline use", /window\.GM_I18N = \{"hi":/.test(html));
      console.log("test50 Life OS languages: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
    }, 200);
  }, 200);
}, 1500);
