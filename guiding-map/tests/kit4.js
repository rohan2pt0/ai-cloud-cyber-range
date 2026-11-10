// kit4: languages in the OS kit (queue multilingual). The device's language is used when a catalog exists; a choice in
// Settings wins and is remembered; anything not translated falls back to the English in the code (never blank, never a
// raw key); numbers use Indian grouping; the page's lang attribute follows, for screen readers and the right fonts.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'vantage', 'index.html'), 'utf8');
const PFX = "osk:vantage:";
function boot(deviceLang, seed) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/vantage/",
    beforeParse(w) {
      w.scrollTo = () => {}; w.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
      Object.defineProperty(w.navigator, "languages", { get: () => [deviceLang] });
      Object.defineProperty(w.navigator, "language", { get: () => deviceLang });
      w.localStorage.setItem(PFX + "profile", JSON.stringify({ name: "Fake", at: "2026-01-01" }));
      Object.entries(seed || {}).forEach(([k, v]) => w.localStorage.setItem(PFX + k, JSON.stringify(v)));
    } });
}
const en = boot("en-GB"), hi = boot("hi-IN"), mrPick = boot("en-US", { "~lang": "mr" });
setTimeout(() => {
  const E = en.window, H = hi.window, M = mrPick.window, main = w => w.document.getElementById("oskMain").textContent;
  ok("English device: English, lang=en", E.OSK.lang === "en" && E.document.documentElement.lang === "en" && /Your next step/.test(main(E)));
  ok("Hindi device: Hindi by itself, lang=hi", H.OSK.lang === "hi" && H.document.documentElement.lang === "hi" && /आपका अगला कदम/.test(main(H)), main(H).slice(0, 120));
  ok("a saved choice wins over the device (Marathi)", M.OSK.lang === "mr" && /तुमचे पुढचे पाऊल/.test(main(M)));
  ok("an untranslated string falls back to English, never a key", H.OSK.t("no.such.key", "Plain English") === "Plain English" && H.OSK.t("no.such.key") === "no.such.key");
  ok("placeholders are filled", H.OSK.t("today.later", "Later ({n})", { n: 3 }) === "बाद में (3)");
  ok("numbers use Indian grouping", E.OSK.num(1234567) === "12,34,567", E.OSK.num(1234567));
  const L = E.OSK.langs();
  ok("English, Hindi and Marathi are offered, the new ones marked beta", L.en && L.hi && L.mr && L.hi.status === "beta" && L.mr.status === "beta");
  // switch from Settings, one tap
  E.OSK.go("settings");
  const b = E.document.querySelector('[data-a="setLang"][data-x="hi"]');
  ok("Settings has a language switch with each name in its own script", b && /हिंदी/.test(b.textContent) && b.getAttribute("lang") === "hi");
  b.dispatchEvent(new E.MouseEvent("click", { bubbles: true }));
  ok("one tap switches, sets lang and is remembered on this device", E.OSK.lang === "hi" && E.document.documentElement.lang === "hi"
    && JSON.parse(E.localStorage.getItem(PFX + "~lang")) === "hi" && /भाषा/.test(main(E)));
  // every catalog key exists in every catalog (a language never silently lags another's screens)
  const cats = ["hi", "mr"].map(l => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'kit', 'i18n', l + '.json'), 'utf8')));
  const keys = cats.map(c => Object.keys(c.strings).sort().join("|"));
  ok("Hindi and Marathi cover the same keys", keys[0] === keys[1]);
  ok("every catalog names its locale and status", cats.every(c => c._meta && /-IN$/.test(c._meta.locale) && c._meta.status));
  console.log("kit4 languages: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1200);
