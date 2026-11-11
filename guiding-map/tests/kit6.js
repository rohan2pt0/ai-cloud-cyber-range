// kit6: the app lock (queue app-lock, threat model kit-lock). The device's biometric (WebAuthn, PRF) unlocks; with PRF every
// value is encrypted at rest and readable only after unlock; a wrong face or phrase opens nothing; the recovery phrase opens
// it; the app locks after being away and veils itself when hidden; without PRF it is an honest screen lock; turning it off
// puts everything back. The authenticator is a stub: same device secret -> same PRF output, as a real one does.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom'), nodeCrypto = require('crypto');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'vantage', 'index.html'), 'utf8');
const PFX = "osk:vantage:", SECRET = "FAKE-SECRET-RISK-ZEBRA";

function boot(store, device, prf = true) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/vantage/",
    beforeParse(w) {
      w.scrollTo = () => {}; w.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
      Object.defineProperty(w, "crypto", { value: nodeCrypto.webcrypto, configurable: true });
      w.PublicKeyCredential = function () {};
      const out = (salt) => nodeCrypto.createHmac("sha256", device).update(Buffer.from(salt)).digest();
      const ext = (salt) => () => (prf ? { prf: { enabled: true, results: { first: new Uint8Array(out(salt)).buffer } } } : { prf: { enabled: false } });
      Object.defineProperty(w.navigator, "credentials", { configurable: true, value: {
        create: (o) => Promise.resolve({ rawId: new Uint8Array([1, 2, 3, 4]).buffer, getClientExtensionResults: ext(o.publicKey.extensions.prf.eval.first) }),
        get: (o) => Promise.resolve({ rawId: new Uint8Array([1, 2, 3, 4]).buffer,
          getClientExtensionResults: o.publicKey.extensions ? ext(o.publicKey.extensions.prf.eval.first) : () => ({}) }) } });
      Object.entries(store).forEach(([k, v]) => w.localStorage.setItem(k, v));
    } });
}
const dump = (w) => { const o = {}; for (let i = 0; i < w.localStorage.length; i++) { const k = w.localStorage.key(i); o[k] = w.localStorage.getItem(k); } return o; };
const main = (w) => w.document.getElementById("oskMain").textContent;
const seed = { [PFX + "profile"]: JSON.stringify({ name: "Fake", at: "2026-01-01" }), [PFX + "reg.risks"]: JSON.stringify([{ id: "r1", risk: SECRET, status: "Open" }]),
               [PFX + "~lang"]: JSON.stringify("en") };

(async () => {
  // 1. turn on: data encrypted at rest, readable while unlocked, plain device keys stay plain
  const A = boot(seed, "device-A"); await new Promise(r => setTimeout(r, 600));
  const K = A.window.OSK;
  ok("the browser can use the device lock", K.lockInfo().prf === true && K.lockInfo().on === false);
  const r = await K.lockEnable();
  ok("turning on gives encryption and a recovery phrase", r.mode === "encrypted" && /^[A-Z2-7]{4}(-[A-Z2-7]{4}){4}$/.test(r.phrase), JSON.stringify(r));
  const disk = dump(A.window);
  ok("no stored value holds the secret in plain text", !Object.values(disk).some(v => v.includes(SECRET)));
  ok("the person's values are encrypted on disk", disk[PFX + "reg.risks"].startsWith("enc1:") && disk[PFX + "profile"].startsWith("enc1:"));
  ok("device keys that say nothing about the person stay readable", disk[PFX + "~lang"] === JSON.stringify("en") && !disk[PFX + "~lock"].includes(SECRET));
  ok("while unlocked the app reads its data", K.get("reg.risks", [])[0].risk === SECRET);
  K.set("note", { t: "FAKE-NEW-ENTRY-OTTER" }); await new Promise(r => setTimeout(r, 200));
  ok("a new value is written encrypted", dump(A.window)[PFX + "note"].startsWith("enc1:") && !JSON.stringify(dump(A.window)).includes("OTTER"));

  // 2. a fresh start: locked, nothing of the person on screen
  const saved = dump(A.window);
  const B = boot(saved, "device-A"); await new Promise(r => setTimeout(r, 600));
  ok("a fresh start is locked", B.window.OSK.locked === true && /Unlock/.test(main(B.window)));
  ok("locked: nothing of the person on screen or readable", !main(B.window).includes(SECRET) && B.window.OSK.get("reg.risks", null) === null
     && B.window.document.getElementById("oskNav").innerHTML === "" && B.window.document.getElementById("oskWho").textContent === "");
  // locked: no sync, so nothing plain is written and no copy of nulls is ever sent to the estate
  let fetched = 0; B.window.fetch = () => { fetched++; return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ payload: {}, meta: {} }) }); };
  B.window.localStorage.setItem("gm_sync_cfg", JSON.stringify({ url: "https://fake.example.invalid", key: "fake-fake-fake" }));
  const pushed = await B.window.OSK.push(), pulled = await B.window.OSK.pull(), merged = B.window.OSK.merge({ [PFX + "reg.risks"]: "[]" }, { [PFX + "reg.risks"]: Date.now() + 9e9 });
  ok("locked: no push, no pull, no merge", fetched === 0 && pushed === false && pulled === 0 && merged === 0 && dump(B.window)[PFX + "reg.risks"].startsWith("enc1:"));
  B.window.localStorage.removeItem("gm_sync_cfg");
  await B.window.OSK.unlock();
  ok("the same device's biometric unlocks it", B.window.OSK.locked === false && B.window.OSK.get("reg.risks", [])[0].risk === SECRET);

  // 3. another face (another device secret) opens nothing
  const C = boot(saved, "device-OTHER"); await new Promise(r => setTimeout(r, 600));
  let refused = false; try { await C.window.OSK.unlock(); } catch (x) { refused = true; }
  ok("another face or device opens nothing", refused && C.window.OSK.locked === true && C.window.OSK.get("reg.risks", null) === null);

  // 4. the recovery phrase opens it; a wrong phrase does not
  let bad = false; try { await C.window.OSK.unlockPhrase("AAAA-AAAA-AAAA-AAAA-AAAA"); } catch (x) { bad = /does not match/.test(x.message); }
  ok("a wrong recovery phrase is refused plainly", bad && C.window.OSK.locked === true);
  await C.window.OSK.unlockPhrase(r.phrase.toLowerCase());
  ok("the recovery phrase opens it (case and dashes do not matter)", C.window.OSK.locked === false && C.window.OSK.get("reg.risks", [])[0].risk === SECRET);

  // 5. away too long: locks; hidden: veiled
  const W = B.window; let now = Date.now(); W.Date.now = () => now;
  Object.defineProperty(W.document, "hidden", { configurable: true, get: () => true }); W.document.dispatchEvent(new W.Event("visibilitychange"));
  ok("hidden: the screen is veiled", W.document.body.classList.contains("osk-veil"));
  now += 301 * 1000; Object.defineProperty(W.document, "hidden", { configurable: true, get: () => false }); W.document.dispatchEvent(new W.Event("visibilitychange"));
  ok("back after more than 5 minutes: locked, veil lifted", W.OSK.locked === true && !W.document.body.classList.contains("osk-veil") && /Unlock/.test(main(W)));

  // 6. turning off puts every value back in plain storage
  await C.window.OSK.lockDisable();
  const off = dump(C.window);
  ok("turning off decrypts everything and removes the lock", !off[PFX + "~lock"] && JSON.parse(off[PFX + "reg.risks"])[0].risk === SECRET && !Object.values(off).some(v => v.startsWith("enc1:")));

  // 7. a browser without PRF: an honest screen lock, data stays plain, and the screen says so
  const G = boot(seed, "device-G", false); await new Promise(r => setTimeout(r, 600));
  const g = await G.window.OSK.lockEnable();
  ok("without PRF: screen lock only, no phrase, data unchanged", g.mode === "gate" && g.phrase === null && dump(G.window)[PFX + "reg.risks"].includes(SECRET));
  G.window.OSK.go("settings");
  ok("…and Settings says the data itself is not encrypted", /not encrypted/.test(main(G.window)));
  const G2 = boot(dump(G.window), "device-G", false); await new Promise(r => setTimeout(r, 600));
  ok("…a fresh start still asks for the biometric", G2.window.OSK.locked === true && /Unlock/.test(main(G2.window)));

  // 8. the invitation: one quiet card on Today, never at first run, gone for good in one tap
  const N = boot(seed, "device-N"); await new Promise(r => setTimeout(r, 600));
  N.window.OSK.go("today");
  ok("Today invites once there is something to protect, with no second primary button", /No new password/.test(main(N.window))
     && N.window.document.querySelectorAll("#oskMain button.primary").length <= 1);
  N.window.document.querySelector('[data-a="lockLater"]').dispatchEvent(new N.window.MouseEvent("click", { bubbles: true }));
  ok("'Not now' hides the invitation for good", !/No new password/.test(main(N.window)));

  console.log("kit6 app lock: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
})().catch(x => { console.log("kit6 crashed: " + (x && x.stack || x)); process.exit(1); });
