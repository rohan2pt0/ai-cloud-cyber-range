// v20: restore asks for a typed word (owner 2026-11-18; experience-v3, fix 20 of 20). Restoring the estate's snapshot
// used a browser confirm(). It now opens an in-page dialog that says how many items on this device will be replaced,
// offers "Save a copy first" as its primary, and only proceeds when RESTORE is typed. window.confirm is never called.
// Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_life", "OLD");
    w.localStorage.setItem("gm_sync_cfg", JSON.stringify({ url: "https://hub.securax.localhost/sync", key: "fake-key", user: "me" }));
    w.__confirm = 0;
    w.confirm = () => { w.__confirm++; return false; };
    w.alert = () => {};
    w.scrollTo = () => {};
    w.location.reload = () => { w.__reloaded = true; };
    w.fetch = (u) => {
      if (String(u).indexOf("/snapshots/") >= 0) return Promise.resolve({ ok: true, json: () => Promise.resolve({ payload: { gm_life: "NEW", sovS: "[]" } }) });
      return Promise.reject(new Error("offline"));
    };
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  w.gmSnapRestore("2026-11-17");
  setTimeout(() => {
    const ov = d.getElementById("gmOverlay");
    ok("the snapshot restore never calls window.confirm", w.__confirm === 0, w.__confirm + " calls");
    ok("it opens an in-page dialog instead", !!ov);
    ok("the dialog says how many items will be replaced", !!ov && /2 items/.test(ov.textContent), ov && ov.textContent);
    const safe = d.getElementById("gmTypeSafe");
    ok("Save a copy first is offered as the primary", !!safe && safe.textContent === "Save a copy first"
      && (safe.classList.contains("btn-p") || /var\(--gold\)/.test(safe.getAttribute("style") || "")), safe && safe.textContent);
    const inp = d.getElementById("gmTypeIn"), go = d.getElementById("gmTypeGo");
    ok("the continue button starts disabled", !!inp && !!go && go.disabled);
    if (inp && go) {
      inp.value = "restore"; inp.dispatchEvent(new w.Event("input"));
      ok("lower-case 'restore' keeps it disabled", go.disabled);
      inp.value = "RESTORE"; inp.dispatchEvent(new w.Event("input"));
      ok("RESTORE enables it", !go.disabled);
      go.click();
    }
    setTimeout(() => {   // the restore runs when the typed-word promise resolves, one tick after the click
    ok("it replaces the data on this device", /NEW/.test(w.localStorage.getItem("gm_life") || ""), w.localStorage.getItem("gm_life"));
    ok("and the dialog is gone", !d.getElementById("gmOverlay"));
    console.log("test20 restore asks for a typed word: " + P + " passed, " + F + " failed");
    if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
    process.exit(0);
    }, 50);
  }, 250);
}, 1500);
