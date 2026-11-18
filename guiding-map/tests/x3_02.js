// x3_02: Escape closes the top layer (queue experience-v3, fix 2 of 20). One keydown listener on document closes the
// dialog overlay, the "Make it yours" sheet and the More sheet through each one's own close path. With nothing open it
// does nothing and throws nothing, and it never closes the lock screen. jsdom, fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };
const boot = (store) => new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    if (store) Object.keys(store).forEach((k) => w.localStorage.setItem(k, store[k]));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
const open = boot(null);
const locked = boot({ gm_lock: JSON.stringify({ id: "fake-credential", salt: "fake-salt", hash: "fake-hash", idle: 300 }) });
const key = (w, k) => w.document.dispatchEvent(new w.KeyboardEvent("keydown", { key: k, bubbles: true }));
setTimeout(() => {
  const w = open.window, d = w.document;
  const sheet = () => d.getElementById("gmMoreSheet");
  const moreOpen = () => !!(sheet() && sheet().classList.contains("on"));

  w.gmNavMore(true);
  ok("the More sheet opens", moreOpen());
  key(w, "Escape");
  ok("Escape closes the More sheet", !moreOpen(), sheet() ? sheet().className : "no sheet");

  w.gmDlg('<div>Fake dialog</div>');
  ok("a dialog overlay opens", !!d.getElementById("gmOverlay"));
  key(w, "Escape");
  ok("Escape closes the dialog overlay", !d.getElementById("gmOverlay"));

  w.gmMineSheet();
  ok("the Make it yours sheet opens", !!d.getElementById("gmMineSheet"));
  key(w, "Escape");
  ok("Escape closes the Make it yours sheet", !d.getElementById("gmMineSheet"));

  let threw = null;
  try { key(w, "Escape"); } catch (err) { threw = err; }
  ok("with nothing open Escape does nothing and throws nothing", !threw && !d.getElementById("gmOverlay") && !d.getElementById("gmMineSheet") && !moreOpen(),
    threw ? threw.message : "clean");

  const lw = locked.window, ld = lw.document;
  ok("the lock screen is up", !!ld.getElementById("gmLock") && lw.gmIsLocked());
  lw.gmNavMore(true);
  key(lw, "Escape");
  ok("the lock screen stays", !!ld.getElementById("gmLock") && lw.gmIsLocked());
  ok("a layer under the lock is not closed", !!(ld.getElementById("gmMoreSheet") && ld.getElementById("gmMoreSheet").classList.contains("on")));

  console.log("x3_02 Escape closes the top layer: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
