// test93: the Life OS privacy lock (queue app-lock slice 2; threat model lifeos-lock; owner 2026-11-11 and 2026-11-13).
const fs = require("fs"), path = require("path"), nodeCrypto = require("crypto"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const b64 = (b) => Buffer.from(b).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const CODE = "ABCD-EFGH-JKLM-NPQR", salt = Buffer.from("fake-salt-fake-1");
const hash = b64(nodeCrypto.pbkdf2Sync("ABCDEFGHJKLMNPQR", salt, 310000, 32, "sha256"));
const REC = { id: b64(Buffer.from("fake-credential-id")), salt: b64(salt), hash, idle: 300, at: 1 };
const boot = (lockRec, webauthn) => new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://localhost/",
  beforeParse(w) { w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_intro_seen", "true"); if (lockRec) w.localStorage.setItem("gm_lock", JSON.stringify(lockRec));
    Object.defineProperty(w, "crypto", { value: nodeCrypto.webcrypto, configurable: true });
    w.confirm = () => true;
    if (webauthn) { w.PublicKeyCredential = { isUserVerifyingPlatformAuthenticatorAvailable: () => Promise.resolve(true) };
      Object.defineProperty(w.navigator, "credentials", { value: { get: () => Promise.resolve({ id: "x" }), create: () => Promise.resolve({ rawId: new Uint8Array([1, 2, 3]).buffer }) } }); } } }).window;
const plain = boot(null, false), locked = boot(REC, true), fresh = boot(null, true);
setTimeout(async () => {
  try {
    // no device lock in this browser: an honest line, no button that cannot work
    plain.goTab("ops");
    ok(/cannot use your fingerprint or face/.test(plain.document.querySelector(".gm-lock-set").textContent), "a browser without device biometrics is told so plainly");
    ok(!plain.document.getElementById("gmLock") && !plain.document.documentElement.classList.contains("gm-locked"), "no lock record: nothing is locked");
    // a locked app shows nothing but the lock
    const d = locked.document;
    ok(d.getElementById("gmLock") && d.documentElement.classList.contains("gm-locked") && locked.gmIsLocked(), "with the lock on, the app opens locked");
    ok(/visibility:hidden/.test([...d.querySelectorAll("style")].map(s => s.textContent).join("")), "everything behind the lock is hidden");
    ok(!/Recovery code|recovery code/.test(d.getElementById("gmLock").textContent) || /Use your recovery code/.test(d.getElementById("gmLock").textContent), "the lock offers the recovery code, folded");
    ok(await locked.gmUnlockCode("WRONG-CODE-0000-0000") === false && locked.gmIsLocked(), "a wrong recovery code is refused");
    ok(await locked.gmUnlockCode(CODE.toLowerCase()) === true && !locked.gmIsLocked() && !d.getElementById("gmLock"), "the right recovery code opens it (any case, any dashes)");
    locked.gmLockNow();
    ok(locked.gmIsLocked() && d.getElementById("gmLock"), "Lock now locks at once");
    ok(await locked.gmUnlock() === true && !locked.gmIsLocked(), "the device's fingerprint or face opens it");
    Object.defineProperty(d, "hidden", { value: true, configurable: true }); d.dispatchEvent(new locked.Event("visibilitychange"));
    ok(d.documentElement.classList.contains("gm-veil"), "hidden: the screen is veiled for the app switcher");
    Object.defineProperty(d, "hidden", { value: false, configurable: true }); d.dispatchEvent(new locked.Event("visibilitychange"));
    ok(!d.documentElement.classList.contains("gm-veil") && !locked.gmIsLocked(), "back within the idle time: unveiled, still open");
    const st = JSON.parse(locked.localStorage.getItem("gm_lock"));
    ok(st.hash && !/ABCD/.test(JSON.stringify(st)), "only the code's hash is stored, never the code");
    // turning it on: one prompt, a recovery code shown once, then on
    await new Promise(r => setTimeout(r, 50));
    const code = await fresh.gmLockEnable();
    ok(/^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$/.test(code) && fresh.gmLockOn(), "turning it on gives a 16-character recovery code and the lock is on");
    fresh.goTab("ops");
    ok(fresh.document.querySelector(".gm-lock-code") && /I have saved it/.test(fresh.document.querySelector(".gm-lock-set").textContent), "the code is shown once, with 'I have saved it'");
    fresh.gmLockSaved(); fresh.goTab("ops");
    const card = fresh.document.querySelector(".gm-lock-set");
    ok(!card.querySelector(".gm-lock-code") && /Lock now/.test(card.textContent) && card.querySelector(".gm-quiet"), "after saving: Lock now, the idle choice, and a quiet Turn off");
    fresh.gmLockDisable();
    ok(!fresh.gmLockOn(), "it can be turned off (with a confirmation) while unlocked");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test93 privacy lock: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
}, 1800);
