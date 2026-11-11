// v44: the backup is encrypted (owner, 2026-11-11: an export left the whole life readable in Downloads). AES-256-GCM under a
// backup phrase made once on the device (PBKDF2 310k); the phrase is shown once, never in the file, never synced; this device
// restores by itself, another device with the phrase; a wrong phrase opens nothing; old plain files still restore; the
// "who touched my data" log reads on a phone and names no terminal command. Threat model lifeos-backup.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom'), { webcrypto } = require('crypto');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), SECRET = "FAKE-SECRET-HERON";
function boot(seed, files) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      Object.defineProperty(w, "crypto", { value: webcrypto });
      Object.entries(seed).forEach(([k, v]) => w.localStorage.setItem(k, typeof v === "string" ? v : JSON.stringify(v)));
      w.confirm = () => true; w.alert = (m) => { w.__alert = m; }; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
      w.URL.createObjectURL = (b) => { files.push(b); return "blob:x"; }; w.HTMLAnchorElement.prototype.click = function () { files.names = (files.names || []).concat(this.download); };
      w.location.reload = () => {};
    } });
}
const read = (w, b) => new Promise((r) => { const fr = new w.FileReader(); fr.onload = () => r(fr.result); fr.readAsText(b); });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
function restoreFrom(w, text) {   // drive gmImportNow with a fake file picker
  const orig = w.document.createElement.bind(w.document);
  w.document.createElement = (t) => { const el = orig(t); if (t === "input") { el.click = () => { Object.defineProperty(el, "files", { value: [new w.Blob([text])] }); el.onchange(); }; } return el; };
  w.gmImportNow(); w.document.createElement = orig;
}
(async () => {
  const fa = []; const A = boot({ gm_goals: JSON.stringify([{ t: SECRET }]) }, fa); await wait(1200);
  const w = A.window;
  w.gmExportNow(); await wait(1500);
  const text = await read(w, fa[0]), env = JSON.parse(text), phrase = JSON.parse(w.localStorage.getItem("gm_sync_od_bkphrase"));
  ok("the backup file is encrypted: no data readable in it", env.kind === "securax-life-os-backup" && env.ct && !text.includes(SECRET) && !text.includes("gm_goals"));
  ok("the file name says encrypted", /life-os-backup-\d{4}-\d{2}-\d{2}-encrypted\.json/.test(fa.names[0]), fa.names[0]);
  ok("the phrase is 100 bits in five groups and is not in the file", /^[A-Z2-9]{4}(-[A-Z2-9]{4}){4}$/.test(phrase) && !text.includes(phrase.replace(/-/g, "")) && !text.includes(phrase));
  ok("the first backup shows the phrase once, with Copy", /Your backup phrase/.test((w.document.getElementById("gmOverlay") || {}).textContent || "") && /Copy/.test(w.document.getElementById("gmOverlay").textContent));
  w.gmClose(); w.gmExportNow(); await wait(1500);
  ok("a later backup needs no typing and shows no dialog", fa.length === 2 && !w.document.getElementById("gmOverlay"));
  ok("the log says an encrypted backup was saved", w.gmTouchRows()[0].w === "Saved an encrypted backup");
  const opened = await w.gmBackupOpen(env, phrase.toLowerCase());
  ok("the phrase opens it (case and dashes do not matter)", JSON.parse(opened.gm_goals)[0].t === SECRET && !opened.gm_sync_od_bkphrase);
  let bad = false; try { await w.gmBackupOpen(env, "AAAA-AAAA-AAAA-AAAA-AAAA"); } catch (x) { bad = true; }
  ok("a wrong phrase opens nothing", bad);
  ok("the phrase is never sent by sync (device-only key)", /gm_sync_od_bkphrase/.test(fs.readFileSync(path.join(__dirname, '..', 'ops.js'), 'utf8')) && w.eval("typeof gmPush") === "function");
  // another device: asks for the phrase, restores, keeps the phrase for its own backups
  const fb = []; const B = boot({}, fb); await wait(1200);
  B.window.gmPrompt = (t, ph, cb) => cb(phrase);
  restoreFrom(B.window, text); await wait(1800);
  ok("a new device restores with the phrase", JSON.parse(B.window.localStorage.getItem("gm_goals") || "[]")[0]?.t === SECRET, B.window.__alert);
  ok("…and keeps the phrase for its own backups", JSON.parse(B.window.localStorage.getItem("gm_sync_od_bkphrase") || "null") === phrase);
  // an old plain file still restores
  const fc = []; const C = boot({}, fc); await wait(1200);
  restoreFrom(C.window, JSON.stringify({ gm_goals: JSON.stringify([{ t: "FAKE-OLD-PLAIN" }]) })); await wait(500);
  ok("an old readable backup still restores", JSON.parse(C.window.localStorage.getItem("gm_goals") || "[]")[0]?.t === "FAKE-OLD-PLAIN");
  // a readable copy only when asked for by name, and logged plainly
  w.gmConfirm = (m, cb) => cb(true); w.gmExportPlain(); await wait(300);
  ok("a readable copy is a separate, named choice and is logged as not encrypted", fa.names.at(-1).indexOf("encrypted") < 0 && /not encrypted/.test(w.gmTouchRows()[0].w));
  // the screen: no terminal command, readable rows, the plain export flagged with what to do
  w.goTab("ops");
  const sec = w.document.getElementById("sections").textContent;
  ok("Who touched my data names no terminal command", !/securax audit/.test(sec) && /tamper-proof log/.test(sec));
  ok("a readable export tells the person to delete it", /Delete it from Downloads/.test(sec));
  ok("Settings offers the encrypted backup and the phrase", /Save encrypted backup/.test(sec) && /Backup phrase/.test(sec));
  console.log("test44 encrypted backup: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
})().catch(x => { console.log("test44 crashed: " + (x && x.stack || x)); process.exit(1); });
