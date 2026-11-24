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
      const o = typeof webauthn === "object" ? webauthn : {}; let made = 0; w.prompt = () => (o.prompt ? o.prompt() : null);
      Object.defineProperty(w.navigator, "credentials", { value: { get: (a) => (o.get ? o.get(a) : Promise.resolve({ id: "x" })), create: () => { made++; if (o.made) o.made(made); return Promise.resolve({ rawId: new Uint8Array([1, 2, 3, made]).buffer }); } } }); } } }).window;
const plain = boot(null, false), locked = boot(REC, true), fresh = boot(null, true);
// owner 2026-11-24: off keeps the code; the passkeys of this device were reset (get fails); an off record at boot
const gone = { made: 0, code: null }; const missing = boot(Object.assign({}, REC, { off: true }), { get: () => Promise.reject(Object.assign(new Error("no"), { name: "NotAllowedError" })), made: (n) => { gone.made = n; }, prompt: () => gone.code });
const offBoot = boot(Object.assign({}, REC, { off: true }), true);
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
    const before = JSON.parse(fresh.localStorage.getItem("gm_lock"));
    ok(await fresh.gmLockDisable() === true && !fresh.gmLockOn(), "it can be turned off (a confirmation and the person's fingerprint or face) while unlocked");
    const offRec = JSON.parse(fresh.localStorage.getItem("gm_lock"));
    ok(offRec.off === true && offRec.hash === before.hash && offRec.salt === before.salt && offRec.id === before.id, "off keeps the code's hash and the credential id, marked off");
    fresh.goTab("ops");
    ok(/Turn the lock back on/.test(fresh.document.querySelector(".gm-lock-set").textContent) && /stays the same/.test(fresh.document.querySelector(".gm-lock-set").textContent), "the off card offers one tap back on, with the same code");
    ok(await fresh.gmLockEnable() === null && fresh.gmLockOn(), "back on: no new code is made");
    const backRec = JSON.parse(fresh.localStorage.getItem("gm_lock"));
    ok(backRec.hash === before.hash && backRec.id === before.id && !backRec.off, "back on reuses the same hash and the same credential");
    fresh.goTab("ops");
    const card2 = fresh.document.querySelector(".gm-lock-set");
    ok(/Back on\. Your recovery code is the same one you saved before\./.test(card2.textContent) && !card2.querySelector(".gm-lock-code"), "the card says plainly the code is the same one");
    ok(await fresh.gmUnlockCode(code) === true, "the code saved the first time still opens it");
    // a new code: folded, the safe step first, typed confirmation, and it replaces the hash
    ok(card2.querySelector(".gm-quiet.gm-lock-new") && /Make a new recovery code…/.test(card2.textContent), "a new code sits under one quiet line");
    fresh.gmLockNewAsk();
    const inp = fresh.document.getElementById("gmLockNewIn"), go = fresh.document.getElementById("gmLockNewGo");
    ok(inp && go && go.disabled && /Keep my current code/.test(fresh.document.body.textContent) && /stop working/.test(fresh.document.body.textContent), "the new-code dialog says the old code stops working, offers keeping it first, and starts disabled");
    inp.value = "new code"; inp.dispatchEvent(new fresh.Event("input"));
    ok(!go.disabled, "typing NEW CODE enables it");
    if (fresh.gmClose) fresh.gmClose();
    ok(await fresh.gmLockNewCode("yes") === null && JSON.parse(fresh.localStorage.getItem("gm_lock")).hash === before.hash, "without the typed words nothing changes");
    const code2 = await fresh.gmLockNewCode("NEW CODE");
    const newRec = JSON.parse(fresh.localStorage.getItem("gm_lock"));
    ok(code2 && code2 !== code && newRec.hash !== before.hash && newRec.id === before.id, "with the typed words a new code replaces the hash");
    fresh.goTab("ops");
    ok(fresh.document.querySelector(".gm-lock-code") && fresh.document.querySelector(".gm-lock-code").textContent === code2, "the new code is shown once to save");
    ok(await fresh.gmUnlockCode(code) === false && await fresh.gmUnlockCode(code2) === true, "the old code stops working, the new one opens it");
    fresh.gmLockSaved();
    // an off record at boot: nothing locked, the boot veil's guess settled
    ok(!offBoot.gmLockOn() && !offBoot.document.getElementById("gmLock") && !offBoot.document.documentElement.classList.contains("gm-locked"), "an off record at boot locks nothing");
    // this device's passkeys were reset: back on makes a new credential, keeps the code
    ok(await missing.gmLockEnable() === null && missing.gmLockOn() && gone.made === 1, "credential gone: back on makes a new credential");
    const mr = JSON.parse(missing.localStorage.getItem("gm_lock"));
    ok(mr.hash === REC.hash && mr.salt === REC.salt && mr.id !== REC.id, "credential gone: the recovery code's hash is kept");
    // turning off needs the person: a failed fingerprint and a wrong code keep it on; the right code turns it off
    gone.code = "WRONG-CODE-0000-0000";
    ok(await missing.gmLockDisable() === false && missing.gmLockOn(), "turning off without the fingerprint or the code is refused");
    gone.code = CODE;
    ok(await missing.gmLockDisable() === true && !missing.gmLockOn(), "the recovery code can stand in for the fingerprint to turn it off");
    // erase still removes everything
    fresh.gmEraseAsk();
    const ei = fresh.document.getElementById("gmEraseIn"); ei.value = "ERASE"; ei.dispatchEvent(new fresh.Event("input"));
    try { fresh.document.getElementById("gmEraseGo").click(); } catch (e) {}
    ok(fresh.localStorage.getItem("gm_lock") === null, "Erase removes the lock record, code hash and credential id included");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test93 privacy lock: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
}, 1800);
