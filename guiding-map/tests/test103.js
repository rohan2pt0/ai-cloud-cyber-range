// v103: audit round 1, a backup saved to the phone's own Downloads is lost with the phone. A backup shared off the phone
// (the phone's share sheet) or downloaded on a wide screen counts as an off-phone copy; a phone download does not. Health
// says safe only when a copy is off the phone within 31 days, and calls a phone-only backup "Saved on this phone only".
// Threat model lifeos-backup.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom'), { webcrypto } = require('crypto');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'),
  today = (function () { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); })();
function boot(seed, opts) {
  const files = [], shared = [];
  const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      Object.defineProperty(w, "crypto", { value: webcrypto });
      Object.entries(seed).forEach(([k, v]) => w.localStorage.setItem(k, typeof v === "string" ? v : JSON.stringify(v)));
      w.confirm = () => true; w.alert = (m) => { w.__alert = m; }; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
      w.URL.createObjectURL = (b) => { files.push(b); return "blob:x"; }; w.HTMLAnchorElement.prototype.click = function () { files.names = (files.names || []).concat(this.download); };
      w.location.reload = () => {};
      w.matchMedia = (q) => ({ matches: !!(opts && opts.phone), media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      Object.defineProperty(w.navigator, "canShare", { configurable: true, value: (o) => !!(o && o.files && o.files.length) });
      Object.defineProperty(w.navigator, "share", { configurable: true, value: (o) => {
        shared.push(o);
        return (opts && opts.shareRejects) ? Promise.reject(new Error("cancelled")) : Promise.resolve();
      } });
    } });
  return { w: dom.window, files, shared };
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  // The phone's share sheet takes the encrypted file off the phone
  const A = boot({ gm_goals: JSON.stringify([{ t: "FAKE-SHARE-HERON" }]) }, {}); await wait(1200);
  A.w.gmExportNow(); await wait(1500);
  ok("share received one encrypted backup file", A.shared.length === 1 && A.shared[0].files && A.shared[0].files.length === 1
    && /-encrypted\.json$/.test(A.shared[0].files[0].name), A.shared.length + " share(s)");
  ok("a shared backup counts as an off-phone copy", JSON.parse(A.w.localStorage.getItem("gm_last_offsite") || "null") === today,
    A.w.localStorage.getItem("gm_last_offsite"));

  // A cancelled share falls back to the download; on a phone a download is not off the phone
  const B = boot({ gm_goals: JSON.stringify([{ t: "FAKE-CANCEL-WREN" }]) }, { phone: true, shareRejects: true }); await wait(1200);
  B.w.gmExportNow(); await wait(1500);
  ok("a cancelled share still downloads the backup", (B.files.names || []).some((n) => /-encrypted\.json$/.test(n)), (B.files.names || []).join(","));
  ok("a phone download is not an off-phone copy", B.w.localStorage.getItem("gm_last_offsite") === null, B.w.localStorage.getItem("gm_last_offsite"));

  // Health tells the truth about where the copy lives
  const C = boot({ gm_last_export: JSON.stringify(today) }, { phone: true }); await wait(1200); C.w.goTab("ops");
  ok("a phone-only backup is called out", /Saved on this phone only/.test(C.w.document.getElementById("sections").textContent));
  const L = boot({ gm_last_export: JSON.stringify(today) }, {}); await wait(1200); L.w.goTab("ops");
  ok("a copy saved on a laptop counts as off the phone", !/Saved on this phone only/.test(L.w.document.getElementById("sections").textContent) && /Last backup today/.test(L.w.document.getElementById("sections").textContent));
  const D = boot({ gm_last_export: JSON.stringify(today), gm_last_offsite: JSON.stringify(today) }, {}); await wait(1200); D.w.goTab("ops");
  ok("an off-phone copy clears the warning", !/Saved on this phone only/.test(D.w.document.getElementById("sections").textContent));

  console.log("test103 off-phone backup: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
})().catch(x => { console.log("test103 crashed: " + (x && x.stack || x)); process.exit(1); });
