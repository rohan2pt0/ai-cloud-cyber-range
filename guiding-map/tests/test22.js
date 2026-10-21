// OneDrive sync (doc 72): two devices stay in step with NO laptop in the loop; the file in OneDrive is ciphertext only;
// two devices writing at the same moment both keep their change (ETag guard + per-key merge); a wrong passphrase is refused;
// the sync key never travels in an export.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path"), { webcrypto } = require("crypto");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };

// ── a fake OneDrive app folder that behaves like Microsoft Graph on the calls the app makes ──
const drive = { file: null, etag: null, n: 0 };
const res = (status, body) => ({ status, ok: status >= 200 && status < 300, headers: { get: () => null },
  json: async () => (typeof body === "string" ? JSON.parse(body) : body), text: async () => String(body) });
function fakeFetch(url, opt = {}) {
  const u = String(url), m = (opt.method || "GET").toUpperCase(), h = opt.headers || {};
  if (u.endsWith("/approot:/sync/state.enc.json") && m === "GET")
    return Promise.resolve(drive.file ? res(200, { eTag: drive.etag, "@microsoft.graph.downloadUrl": "https://dl.test/state" }) : res(404, {}));
  if (u === "https://dl.test/state") return Promise.resolve(res(200, drive.file));
  if (u.endsWith("/approot:/sync/state.enc.json:/content") && m === "PUT") {
    if (h["If-Match"] && h["If-Match"] !== drive.etag) return Promise.resolve(res(412, {}));
    if (h["If-None-Match"] === "*" && drive.file) return Promise.resolve(res(412, {}));
    drive.file = opt.body; drive.etag = "e" + (++drive.n);
    return Promise.resolve(res(200, { eTag: drive.etag }));
  }
  return Promise.resolve(res(404, {}));     // everything else (estate sync, backups list) is simply absent
}
function device(name) {
  const d = new JSDOM(html, { runScripts: "dangerously", url: "https://" + name + ".test/", beforeParse(w) {
    Object.defineProperty(w, "crypto", { value: webcrypto });
    w.fetch = fakeFetch; w.alert = (t) => { w.__alerts.push(String(t)); }; w.confirm = () => true; w.__alerts = [];
    w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
    w.localStorage.setItem("gm_ms_cfg", JSON.stringify({ id: "test-client-id" }));
    w.localStorage.setItem("gm_ms_tok", JSON.stringify({ access_token: "t", refresh_token: "r", expires_at: Date.now() + 3600e3 }));
  } });
  return d.window;
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
async function turnOn(w, pass) {
  const el = w.document.createElement("input"); el.id = "odPass"; el.value = pass; w.document.body.appendChild(el);
  w.gmOdSyncOn(); for (let i = 0; i < 60 && !w.localStorage.getItem("gm_sync_od_last") && !w.__alerts.length; i++) await wait(100);
  await wait(300); el.remove();
}

(async () => {
  await wait(800);
  const A = device("laptop"), B = device("phone"), C = device("stranger");
  await wait(800);
  A.localStorage.setItem("gm_test_goal", JSON.stringify("SECRET-GOAL-from-laptop"));
  await turnOn(A, "correct horse battery staple");
  ok(!!drive.file, "the laptop wrote the shared state to OneDrive");
  ok(drive.file && drive.file.indexOf("SECRET-GOAL") < 0 && JSON.parse(drive.file).ct, "OneDrive holds ciphertext only (no plaintext goal in the file)");

  await turnOn(B, "correct horse battery staple");
  ok(B.localStorage.getItem("gm_test_goal") === JSON.stringify("SECRET-GOAL-from-laptop"), "the phone received the laptop's goal through OneDrive (no laptop server involved)");

  // both edit at the same moment, then both sync at once: the second writer meets a stale ETag, re-reads, merges, retries
  A.localStorage.setItem("gm_test_a", JSON.stringify("edit on laptop"));
  B.localStorage.setItem("gm_test_b", JSON.stringify("edit on phone"));
  await Promise.all([A.gmOdSync(), B.gmOdSync()]);
  // whichever wrote first had not seen the other's edit yet: one more round EACH, in either order, and both must hold both
  // (syncing only A here made the test depend on which write landed first, and it failed in CI when B won)
  await A.gmOdSync();
  await B.gmOdSync();
  ok(A.localStorage.getItem("gm_test_b") === JSON.stringify("edit on phone") && B.localStorage.getItem("gm_test_a") === JSON.stringify("edit on laptop"),
     "simultaneous edits on two devices are both kept (neither overwrites the other)");

  await turnOn(C, "a different passphrase entirely");
  ok(!C.localStorage.getItem("gm_sync_odk") && C.__alerts.some((t) => /does not open/.test(t)), "a wrong passphrase is refused and no key is stored");
  ok(!C.localStorage.getItem("gm_test_goal"), "a device with the wrong passphrase gets none of the data");

  // the sync key never leaves in an export
  let exported = null;
  A.URL.createObjectURL = (blob) => { exported = blob; return "blob:x"; };
  A.document.createElement = ((orig) => function (t) { const e = orig.call(A.document, t); if (t === "a") e.click = () => {}; return e; })(A.document.createElement);
  A.gmExportNow();
  const text = exported ? await new Promise((r) => { const fr = new A.FileReader(); fr.onload = () => r(fr.result); fr.readAsText(exported); }) : "";
  ok(text && text.indexOf("gm_test_goal") >= 0 && text.indexOf("gm_sync_odk") < 0, "an export carries the data but never the OneDrive sync key");

  console.log("test22 onedrive sync: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
})();
