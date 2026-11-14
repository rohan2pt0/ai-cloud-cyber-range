// v102: audit round 1, a lost phone costs nothing but the phone (owner, 2026-11-14). The backup phrase used to live only on the
// phone, so losing it made every encrypted backup unreadable. When the Life OS is paired with the person's own estate, the
// phrase is also kept there (gm_bk_escrow, which only the estate sync carries; the estate already holds the synced data), a
// newly paired device adopts it and opens old backups, and it never goes into a backup file or the OneDrive copy. "I have
// saved it" is believed only when the last four characters are typed. Threat model lifeos-backup.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom'), { webcrypto } = require('crypto');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), SECRET = "FAKE-SECRET-WREN";
const PAIR = { url: "https://estate.example.org/sync", key: "fake-device-token", user: "fake" };
function boot(seed, files, sent) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      Object.defineProperty(w, "crypto", { value: webcrypto });
      Object.entries(seed).forEach(([k, v]) => w.localStorage.setItem(k, typeof v === "string" ? v : JSON.stringify(v)));
      w.confirm = () => true; w.alert = (m) => { w.__alert = m; }; w.scrollTo = () => {};
      w.fetch = (u, o) => { if (sent && o && o.body) sent.push(String(o.body)); return Promise.reject(new Error("offline")); };
      w.URL.createObjectURL = (b) => { files.push(b); return "blob:x"; }; w.HTMLAnchorElement.prototype.click = function () {};
      w.location.reload = () => {};
    } });
}
const read = (w, b) => new Promise((r) => { const fr = new w.FileReader(); fr.onload = () => r(fr.result); fr.readAsText(b); });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  // Not paired: the phrase stays on the device only, as before
  const f0 = []; const A0 = boot({ gm_goals: JSON.stringify([{ t: SECRET }]) }, f0); await wait(1200);
  A0.window.gmExportNow(); await wait(1500);
  ok("not paired: nothing is escrowed", A0.window.localStorage.getItem("gm_bk_escrow") === null);
  // Paired with the estate: the phrase is escrowed, never in the file
  const fa = [], sent = []; const A = boot({ gm_goals: JSON.stringify([{ t: SECRET }]), gm_sync_cfg: PAIR }, fa, sent); await wait(1200);
  const w = A.window;
  w.gmExportNow(); await wait(1500);
  const phrase = JSON.parse(w.localStorage.getItem("gm_sync_od_bkphrase")), esc = JSON.parse(w.localStorage.getItem("gm_bk_escrow") || "null");
  ok("paired: the phrase is escrowed for the estate", esc === phrase && /^[A-Z2-9]{4}(-[A-Z2-9]{4}){4}$/.test(String(phrase)), esc);
  const text = await read(w, fa[0]);
  ok("the encrypted file does not carry the phrase", !text.includes(phrase) && !text.includes(phrase.replace(/-/g, "")) && !text.includes("gm_bk_escrow"));
  const opened = await w.gmBackupOpen(JSON.parse(text), phrase);
  ok("…nor does the data inside it", !("gm_bk_escrow" in opened) && !("gm_sync_od_bkphrase" in opened) && JSON.parse(opened.gm_goals)[0].t === SECRET);
  w.gmConfirm = (m, cb) => cb(true); w.gmExportPlain(); await wait(300);
  const plain = await read(w, fa.at(-1));
  ok("a readable export never carries the phrase", !plain.includes(phrase) && !plain.includes("gm_bk_escrow"));
  w.gmPush(); await wait(300);
  ok("the estate sync carries the escrowed phrase", sent.some((b) => b.includes("gm_bk_escrow")), sent.length + " sends");
  // "I have saved it" is checked
  ok("the first backup asks for the last four characters", /type its last four characters/.test((w.document.getElementById("gmOverlay") || {}).textContent || ""));
  w.document.getElementById("gmBkLast").value = "ZZZZ"; w.gmBkConfirm();
  ok("a wrong ending is not accepted", !w.localStorage.getItem("gm_bk_confirmed") && !!w.document.getElementById("gmOverlay"));
  w.document.getElementById("gmBkLast").value = phrase.slice(-4).toLowerCase(); w.gmBkConfirm();
  ok("the right ending (any case) is accepted and closes the dialog", !!w.localStorage.getItem("gm_bk_confirmed") && !w.document.getElementById("gmOverlay"));
  // A new phone paired with the same estate: the escrow arrives by sync, and the old backup opens with no typing
  const fb = []; const B = boot({ gm_sync_cfg: PAIR, gm_bk_escrow: JSON.stringify(phrase) }, fb);   // stored as sync stores it (JSON) await wait(1200);
  B.window.gmPrompt = () => { B.window.__asked = true; };
  const orig = B.window.document.createElement.bind(B.window.document);
  B.window.document.createElement = (t) => { const el = orig(t); if (t === "input") { el.click = () => { Object.defineProperty(el, "files", { value: [new B.window.Blob([text])] }); el.onchange(); }; } return el; };
  B.window.gmImportNow(); B.window.document.createElement = orig; await wait(1800);
  ok("a new paired phone opens the old backup without asking for the phrase", JSON.parse(B.window.localStorage.getItem("gm_goals") || "[]")[0]?.t === SECRET && !B.window.__asked, B.window.__alert);
  ok("…and adopts the phrase for its own backups", JSON.parse(B.window.localStorage.getItem("gm_sync_od_bkphrase") || "null") === phrase);
  console.log("test102 a lost phone loses nothing: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
})();
