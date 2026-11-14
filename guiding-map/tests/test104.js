// test104: sync keeps working while the Life OS is locked (audit round 1, finding 3; queue audit-round-1).
// A goal written on the laptop must land in storage even while this device sits behind its privacy lock, and
// must be on the Goals tab once the person unlocks. The Goals tab renders S.okrs, which lives in sovS, so the
// "newer goal" travels as sovS; gm_goals is also synced as the marker key the finding names.
const fs = require("fs"), path = require("path"), nodeCrypto = require("crypto"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const b64 = (b) => Buffer.from(b).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const CODE = "FAKE-CODE-AAAA", salt = Buffer.from("fake-salt-sync-1");
const hash = b64(nodeCrypto.pbkdf2Sync("FAKECODEAAAA", salt, 310000, 32, "sha256"));
const REC = { id: b64(Buffer.from("fake-credential-id")), salt: b64(salt), hash, idle: 300, at: 1 };
const PAIR = { url: "https://estate.example.org/sync", key: "fake-device-token", user: "fake" };
const GOAL = { okrs: [{ o: "FAKE-FROM-LAPTOP", krs: [] }] };
const payload = { sovS: JSON.stringify(GOAL), gm_goals: JSON.stringify(["FAKE-FROM-LAPTOP"]) };
const meta = { sovS: Date.now() + 100000, gm_goals: Date.now() + 100000 };
function boot() {
  const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://localhost/",
    beforeParse(w) {
      w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} });
      w.scrollTo = () => {}; w.confirm = () => true; w.alert = () => {};
      w.WebSocket = undefined;
      Object.defineProperty(w, "crypto", { value: nodeCrypto.webcrypto, configurable: true });
      w.localStorage.setItem("gm_intro_seen", "true");
      w.localStorage.setItem("gm_lock", JSON.stringify(REC));
      w.localStorage.setItem("gm_sync_cfg", JSON.stringify(PAIR));
      w.fetch = (u, o) => {
        u = String(u); o = o || {};
        if (o.method === "HEAD") return Promise.resolve({ ok: true, headers: { get: (h) => h === "date" ? new Date().toUTCString() : null } });
        if (/\/sync\/state/.test(u)) {
          if (o.method === "PUT") return Promise.resolve({ ok: true, json: () => Promise.resolve({ snapshots: 1, latest_snapshot: "s-1" }) });
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ payload, meta }) });
        }
        return Promise.reject(new Error("offline"));
      };
    } });
  return dom.window;
}
setTimeout(async () => {
  try {
    const w = boot(), d = w.document;
    await new Promise(r => setTimeout(r, 500));   // let the boot and its own sync settle
    ok(d.getElementById("gmLock") && w.gmIsLocked(), "the app opens locked");
    // A sync while locked: reset to a small known state so the pull's integrity guard lets the goal in, then pull.
    w.localStorage.clear();
    w.localStorage.setItem("gm_intro_seen", "true");
    w.localStorage.setItem("gm_lock", JSON.stringify(REC));
    w.localStorage.setItem("gm_sync_cfg", JSON.stringify(PAIR));
    w.gmSyncInit(true);
    await new Promise(r => setTimeout(r, 600));   // clock -> pull -> merge -> push
    const goals = w.localStorage.getItem("gm_goals") || "", sovS = w.localStorage.getItem("sovS") || "";
    ok(goals.indexOf("FAKE-FROM-LAPTOP") >= 0 && sovS.indexOf("FAKE-FROM-LAPTOP") >= 0, "the goal synced into storage while locked");
    ok(w.gmIsLocked() && d.getElementById("gmLock"), "#gmLock still covers the screen while syncing");
    ok(await w.gmUnlockCode("WRONG-CODE-0000-0000") === false && w.gmIsLocked(), "a wrong recovery code keeps it locked");
    ok(await w.gmUnlockCode(CODE) === true && !w.gmIsLocked() && !d.getElementById("gmLock"), "the right recovery code unlocks");
    w.goTab("okr");
    ok(d.getElementById("sections").textContent.indexOf("FAKE-FROM-LAPTOP") >= 0, "the Goals tab shows the goal that synced while locked");
  } catch (e) { fail++; console.log("FAIL threw " + e.message); }
  console.log("test104 sync while locked: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
}, 700);
