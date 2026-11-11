// v46: friction by consequence (owner, 2026-11-11). On Ops the safe, frequent choice (Save encrypted backup) is the one primary,
// Restore beside it; the rare exports fold under "More backup options"; erase lives only in a closed Danger zone at the very
// bottom, behind a typed ERASE, and it really erases every value of this app while leaving other apps on the origin alone.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom'), { webcrypto } = require('crypto');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { Object.defineProperty(w, "crypto", { value: webcrypto });
    w.localStorage.setItem("gm_inbox", JSON.stringify([{ id: "fakeA", t: "Fake item" }])); w.localStorage.setItem("gm_life", "{}");
    w.localStorage.setItem("osk:vantage:profile", JSON.stringify({ name: "Fake" }));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.location.reload = () => { w.__reloaded = true; }; } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("ops");
  const row = sec().querySelector(".gm-bk-row");
  ok("the backup row has exactly Save encrypted backup and Restore from file", row && [...row.querySelectorAll("button")].map(b => b.textContent).join("|") === "Save encrypted backup|Restore from file", row && row.textContent);
  const more = sec().querySelector("details.gm-more-backup");
  ok("the four rare options are folded under a closed More backup options", more && !more.open && ["Backup phrase", "Readable copy", "Export for Excel (CSV)", "Spouse emergency page"].every(t => more.textContent.includes(t)));
  ok("readable exports say so", /Readable by anyone who gets the file/.test(more.textContent));
  const erases = [...sec().querySelectorAll("button")].filter(b => /Erase/.test(b.textContent));
  const danger = sec().querySelector("details.gm-danger");
  ok("erase appears only inside the closed Danger zone", erases.length === 1 && danger && !danger.open && danger.contains(erases[0]));
  const folds = [...sec().querySelectorAll("details")], gl = folds.findIndex(x => /Glossary/.test(x.querySelector("summary").textContent));
  ok("the Danger zone comes after the Glossary, at the bottom", folds.indexOf(danger) > gl && gl >= 0);
  ok("erase is never styled as a primary", !erases[0].classList.contains("btn-p") && !/gold/.test(erases[0].getAttribute("style")));
  ok("the Danger zone offers a backup first", /Save an encrypted backup first/.test(danger.textContent));
  ok("no Erase in the footer or on Today", (w.goTab("today"), ![...d.querySelectorAll("footer button, #sections button")].some(b => /Erase|Reset all/.test(b.textContent))));
  // the typed confirmation
  w.resetAll();
  const inp = d.getElementById("gmEraseIn"), go = d.getElementById("gmEraseGo");
  ok("every erase path asks for the typed word", inp && go && go.disabled);
  inp.value = "erase"; inp.dispatchEvent(new w.Event("input"));
  ok("lower-case 'erase' keeps it disabled", go.disabled);
  inp.value = "ERASE"; inp.dispatchEvent(new w.Event("input"));
  ok("ERASE enables it", !go.disabled);
  go.click();
  const keys = Object.keys(w.localStorage);
  ok("it erases every value of this app", !keys.some(k => /^(gm_|sov)/.test(k)), keys.join(","));
  ok("…and leaves other apps on this origin alone", w.localStorage.getItem("osk:vantage:profile") !== null);
  console.log("test46 friction by consequence: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
