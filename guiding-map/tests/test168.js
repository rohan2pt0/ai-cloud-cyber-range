// test168: Move to another phone (owner 2026-11-24; threat model move-phone). A copy of the Life OS with no estate behind it
// (GitHub Pages) used to ask for an invented sync address, a token and a row id. Now the old phone seals everything into one
// end-to-end-encrypted file under a one-time code, shows the code as a QR, and the new phone opens the file and scans it.
// Proves: the round trip; a wrong code, a changed byte, a malicious or stale or replayed file are refused; the merge keeps newer
// data; no estate means no hand form and no invented address; the code is never written to storage. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom'), { webcrypto } = require('crypto');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d !== undefined ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const mm = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
function boot(prof, seed, calls, shared) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://pages.example/app/",
    beforeParse(w) {
      Object.defineProperty(w, "crypto", { value: webcrypto });
      w.matchMedia = mm; w.scrollTo = () => {}; w.alert = () => {}; w.confirm = () => true;
      w.localStorage.setItem("gm_mine_done", "true"); w.localStorage.setItem("gm_quick_done", "true"); w.localStorage.setItem("gm_simple", "false");
      if (prof) w.localStorage.setItem("sovP", JSON.stringify(prof));
      Object.keys(seed || {}).forEach(k => w.localStorage.setItem(k, seed[k]));
      // a static host with no estate: every path is a 404 page (the door probe must not read it as an estate)
      w.fetch = (u) => { if (calls) calls.push(String(u)); return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error("not json")), text: () => Promise.resolve("<h1>404</h1>") }); };
      if (shared) {
        Object.defineProperty(w.navigator, "canShare", { value: () => true, configurable: true });
        Object.defineProperty(w.navigator, "share", { value: (o) => { shared.push(o); return Promise.resolve(); }, configurable: true });
      }
    } });
}
// a sealed file made outside the app, the same format, so a valid code can carry a malicious inside
const enc = new TextEncoder(), b64 = (u) => Buffer.from(u).toString("base64");
async function seal(inner, code) {
  const salt = webcrypto.getRandomValues(new Uint8Array(16)), iv = webcrypto.getRandomValues(new Uint8Array(12));
  const base = await webcrypto.subtle.importKey("raw", enc.encode(code), "PBKDF2", false, ["deriveKey"]);
  const key = await webcrypto.subtle.deriveKey({ name: "PBKDF2", salt, iterations: 310000, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, false, ["encrypt"]);
  const ct = await webcrypto.subtle.encrypt({ name: "AES-GCM", iv }, key, enc.encode(typeof inner === "string" ? inner : JSON.stringify(inner)));
  return JSON.stringify({ v: 1, alg: "AES-256-GCM, key PBKDF2-SHA256 x310000", salt: b64(salt), iv: b64(iv), ct: b64(new Uint8Array(ct)), kind: "securax-life-os-move" });
}
const allValues = (w) => { let s = ""; for (let i = 0; i < w.localStorage.length; i++) { const k = w.localStorage.key(i); s += k + "=" + w.localStorage.getItem(k) + "\n"; } return s; };
// each value's time lives in gm_meta (the per-key merge's clock); written here as the sync layer writes it
const stamp = (w, k, v, t) => { w.localStorage.setItem(k, v); const m = JSON.parse(w.localStorage.getItem("gm_meta") || "{}"); m[k] = t; w.localStorage.setItem("gm_meta", JSON.stringify(m)); };
const refused = (p) => p.then(() => "opened", (x) => String(x && x.message || x));

const callsA = [], shared = [];
const A = boot({ name: "Fake Alpha", example: false, country: "India", cur: "INR", net: 100000, exp: 60000 }, { gm_fake_only_a: "from-a", "osk:fake_kit": "kit-a" }, callsA, shared);
const B = boot(null, null, []);
setTimeout(async () => {
  try {
    const wa = A.window, da = wa.document;
    // 1. no estate here: no hand form, no address, and the move is offered instead
    wa.goTab("ops"); wa.renderAll();
    const sec = da.getElementById("sections");
    ok("the door probe asked this page's own origin and got no estate", callsA.some(u => u === "https://pages.example/_door.json") && wa.gmEstateUp() === false, callsA.join(","));
    ok("no estate: the hand form is not offered", !da.getElementById("syUrl") && !da.getElementById("syKey") && !da.querySelector(".gm-sync-hand"));
    ok("no estate: no sync address is invented or stored", !/pages\.example\/sync/.test(sec.innerHTML) && wa.localStorage.getItem("gm_sync_cfg") === null);
    ok("the move is offered in its place", !!da.querySelector("[data-move-out]") && !!da.querySelector("[data-move-in]"));
    ok("a phone with its own data makes Move the one primary", da.querySelector("[data-move-out]").classList.contains("btn-p") && !da.querySelector("[data-move-in]").classList.contains("btn-p"));

    // 2. the old phone seals: ciphertext only, a one-time code of 16 symbols (80 bits), and the code is never stored
    stamp(wa, "gm_fake_note", "alpha-older", Date.now() - 60000);       // older than what the third phone writes later
    const r = await wa.gmMoveMake();
    ok("the code is four groups of four from the 32-symbol alphabet (80 bits)", /^[A-HJ-NP-Z2-9]{16}$/.test(r.code), r.code);
    ok("the file is ciphertext: no value is readable in it", !/Fake Alpha|from-a|alpha-older/.test(r.text) && JSON.parse(r.text).kind === "securax-life-os-move");
    ok("the code is not in the file", r.text.indexOf(r.code) < 0);
    await wa.gmMoveOut();
    const dlg = da.getElementById("gmOverlay");
    const shown = dlg && (dlg.querySelector(".gm-mv-code") || {}).textContent || "";
    const code = shown.replace(/-/g, "");
    ok("the dialog shows the code as a QR and as four groups", !!(dlg && dlg.querySelector(".gm-mv-qr svg[role=img] path")) && /^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$/.test(shown), shown);
    const m = wa.SXQR.matrix("SXMOVE1:" + code);
    ok("the QR is a version 2 symbol with its three finder patterns", m.length === 25 && m[0][0] && m[0][6] && m[6][0] && !m[1][1] && m[0][24] && m[24][0] && !m[24][24 - 7]);
    const how = await wa.gmMoveShare();
    const f = shared[0] && shared[0].files && shared[0].files[0];
    ok("Share hands the sealed file to the share sheet", how === "shared" && !!f && /^life-os-move-\d{4}-\d{2}-\d{2}\.json$/.test(f.name), f && f.name);
    const fileText = f ? await new Promise(res => { const rd = new wa.FileReader(); rd.onload = () => res(rd.result); rd.readAsText(f); }) : "";
    wa.gmMoveDone();
    ok("the code is never written to this phone's storage", allValues(wa).indexOf(code) < 0 && allValues(wa).indexOf(r.code) < 0);

    // 3. the new phone: a wrong code, a changed byte and junk are refused; the right scan brings the life here
    const wb = B.window, db = wb.document;
    wb.goTab("ops"); wb.renderAll();
    ok("a fresh phone makes Bring my life here the one primary", db.querySelector("[data-move-in]").classList.contains("btn-p"));
    const wrong = (code[0] === "A" ? "B" : "A") + code.slice(1);
    ok("a wrong code opens nothing", /does not open/.test(await refused(wb.gmMoveOpen(fileText, wrong))));
    const env = JSON.parse(fileText), ct = Buffer.from(env.ct, "base64"); ct[Math.floor(ct.length / 2)] ^= 1;
    ok("one changed byte is refused (the GCM tag)", /does not open/.test(await refused(wb.gmMoveOpen(JSON.stringify(Object.assign({}, env, { ct: ct.toString("base64") })), code))));
    ok("a file that is not a move file is refused", /not a move file/.test(await refused(wb.gmMoveOpen('{"kind":"securax-life-os-backup","v":1}', code))) && /not a move file/.test(await refused(wb.gmMoveOpen("<html>", code))));
    ok("a file that is not a move file opens no dialog", wb.gmMoveAsk('{"hello":1}') === false && !db.getElementById("gmOverlay"));
    ok("the real move file opens the scan step", wb.gmMoveAsk(fileText) === true && /Bring my life here/.test(db.getElementById("gmOverlay").textContent));
    const res = await wb.gmMoveCode("SXMOVE1:" + code);                 // what the QR scan hands over (no camera in CI)
    const pb = JSON.parse(wb.localStorage.getItem("sovP") || "{}");
    ok("the round trip brings the data here", res && res.ok && pb.name === "Fake Alpha" && wb.localStorage.getItem("gm_fake_only_a") === "from-a" && wb.localStorage.getItem("gm_fake_note") === "alpha-older", JSON.stringify(res));
    ok("the example data on a fresh phone gives way to the moved life", res && res.fresh === true && pb.example === false);
    ok("a kit edition's own keys come too", wb.localStorage.getItem("osk:fake_kit") === "kit-a");
    ok("device-only keys never arrive", wb.localStorage.getItem("gm_sync_dev") !== wa.localStorage.getItem("gm_sync_dev"));
    ok("an undo snapshot was kept before the merge", /another phone/.test(wb.localStorage.getItem("gm_undo") || ""));
    ok("Who touched my data records the move", /Brought your life from another phone/.test(allValues(wb)));
    ok("the same file cannot be brought twice (replay)", /already brought/.test(await refused(wb.gmMoveOpen(fileText, code))));
    ok("the code is never written to the new phone's storage", allValues(wb).indexOf(code) < 0);

    // 4. malicious, stale and future files that DO open with their code are still refused, and nothing leaks into Object.prototype
    const C = "K7QMXRAPL9TW2HN3", id = "0a1b2c3d4e5f60718293a4b5", base = () => ({ kind: "securax-life-os-move", v: 1, id, made: Date.now(), from: "x", data: { gm_x: "1" }, meta: {} });
    ok("a wrong inner kind is refused", /not in a shape/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { kind: "evil" }), C), C))));
    ok("a newer version is refused", /not in a shape/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { v: 2 }), C), C))));
    const poison = '{"kind":"securax-life-os-move","v":1,"id":"' + id + '","made":' + Date.now() + ',"from":"x","data":{"__proto__":{"polluted":"yes"},"constructor":"x","gm_ok":"1"},"meta":{}}';
    ok("prototype-pollution keys are refused", /not Life OS data/.test(await refused(wb.gmMoveOpen(await seal(poison, C), C))) && ({}).polluted === undefined && wb.Object.prototype.polluted === undefined);
    ok("a value that is not text is refused", /not Life OS data/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { data: { gm_x: { a: 1 } } }), C), C))));
    ok("a key outside the Life OS's names is refused", /not Life OS data/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { data: { "<img src=x>": "1" } }), C), C))));
    ok("a device-only key (a sync token) is refused", /not Life OS data/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { data: { gm_sync_cfg: "{}" } }), C), C))));
    ok("a file older than two days is refused", /more than two days old/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { made: Date.now() - 3 * 864e5 }), C), C))));
    ok("a file from the future is refused", /in the future/.test(await refused(wb.gmMoveOpen(await seal(Object.assign(base(), { made: Date.now() + 864e5 }), C), C))));

    // 5. a phone with its own life: the per-key merge keeps what is newer here, says so, and still brings what is new
    const Cdom = boot({ name: "Fake Gamma", example: false, country: "India", cur: "INR" }, null, []);
    await new Promise(res => setTimeout(res, 1500));
    const wc = Cdom.window;
    stamp(wc, "gm_fake_note", "gamma-newer", Date.now());               // written after phone A's: newer
    const mv = await wc.gmMoveOpen(fileText, code);
    const r2 = wc.gmMoveApply(mv);
    ok("the merge keeps the newer value on this phone", wc.localStorage.getItem("gm_fake_note") === "gamma-newer", wc.localStorage.getItem("gm_fake_note"));
    ok("and counts it, never replacing it silently", r2.ok && r2.kept >= 1 && r2.fresh === false, JSON.stringify(r2));
    ok("what this phone did not have arrives", wc.localStorage.getItem("gm_fake_only_a") === "from-a");
    ok("the code is never written to storage on any phone", allValues(wc).indexOf(code) < 0);
  } catch (x) { ok("no exception", false, x && x.stack); }
  console.log("test168 move to another phone: " + P + " passed, " + F + " failed");
  e.forEach(x => console.log("  " + x));
  process.exit(F ? 1 : 0);
}, 1800);
