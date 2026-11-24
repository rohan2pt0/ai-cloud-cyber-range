// test142: seamless sync, slice 1 (owner 2026-11-18: "one more key to copy-paste, every day"). A device that syncs hands
// the pairing to the next device through the share sheet; a device that does not sync shows no key box in plain sight.
// Fake values only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
function boot(cfg, shared) {
  return new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/app/",
    beforeParse(w) {
      w.localStorage.setItem("gm_mine_done", "true");
      if (cfg) w.localStorage.setItem("gm_sync_cfg", JSON.stringify(cfg));
      // the hub answers its door probe (/_door.json), so the estate sync is offered here (move-phone: never on a page with no estate)
      w.fetch = (u) => /\/_door\.json$/.test(String(u)) ? Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true, service: "securax-command-center" }) }) : Promise.reject(new Error("offline"));
      w.scrollTo = () => {}; w.alert = () => {}; w.confirm = () => true;
      if (shared) Object.defineProperty(w.navigator, "share", { value: (o) => { shared.push(o); return Promise.resolve(); }, configurable: true });
    } });
}
const fake = { url: "https://hub.securax.localhost/sync", key: "fake-fake-fake-token", user: "me" };
const shared = [];
const a = boot(null), b = boot(fake, shared), c = boot({ url: "https://hub.securax.localhost/sync", key: "access", user: "me", access: true });
setTimeout(() => {
  const show = (dom) => { const w = dom.window; try { w.goTab("ops"); } catch (x) {} w.renderAll(); return w.document; };
  // 1. a device that does not sync: no key box in plain sight, one line that says where to tap
  let d = show(a);
  const key = d.getElementById("syKey"), hand = key && key.closest("details");
  ok("the device token box is folded under Set it up by hand", !!key && !!hand && !hand.open && /Set it up by hand/.test(hand.querySelector("summary").textContent));
  ok("the card says where to tap instead", /Add another device/.test(d.getElementById("sections").textContent));
  // 2. a device that syncs: one button hands the pairing over, and the link holds exactly this device's settings
  d = show(b);
  const btn = d.querySelector("[data-sync-share]");
  ok("a syncing device shows Add another device", !!btn && /Add another device/.test(btn.textContent));
  const link = b.window.gmSyncLink();
  const m = /^https:\/\/hub\.securax\.localhost\/app\/#sync=([A-Za-z0-9_-]+)$/.exec(link);
  ok("the link opens this same app with the pairing in the #fragment", !!m, link);
  if (m) {
    let t = m[1].replace(/-/g, "+").replace(/_/g, "/"); while (t.length % 4) t += "=";
    const o = JSON.parse(Buffer.from(t, "base64").toString("utf8"));
    ok("the link carries the url, key and row id, nothing more", o.url === fake.url && o.key === fake.key && o.user === "me" && Object.keys(o).length === 3, JSON.stringify(o));
  }
  b.window.gmSyncShare().then(() => {
    ok("Add another device uses the share sheet with that link", shared.length === 1 && shared[0].url === link, JSON.stringify(shared));
    // 3. paired by sign-in: nothing to hand over; the card says to sign in on the other device
    d = show(c);
    ok("a sign-in paired device shows no share button", !d.querySelector("[data-sync-share]"));
    ok("and says the other device pairs itself on sign-in", /sign in\. It pairs itself/.test(d.getElementById("sections").textContent));
    ok("gmSyncLink gives nothing for a sign-in pairing", c.window.gmSyncLink() === "");
    // 4. OneDrive: the link carries the data key, so the next device never asks for the passphrase
    const od = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/app/",
      beforeParse(w) { w.localStorage.setItem("gm_mine_done", "true"); w.fetch = () => Promise.reject(new Error("offline")); w.scrollTo = () => {};
        w.localStorage.setItem("gm_sync_od", JSON.stringify({ on: 1, since: "2026-11-01" }));
        w.localStorage.setItem("gm_sync_odk", JSON.stringify({ k: "ZmFrZWZha2VmYWtlZmFrZQ==", salt: "c2FsdHNhbHRzYWx0" }));
        w.localStorage.setItem("gm_ms_cfg", JSON.stringify({ id: "fake-app-id-one" })); } });
    setTimeout(() => {
      const l2 = od.window.gmSyncLink();
      ok("a OneDrive device makes a hand-over link too", /#sync=/.test(l2), l2);
      const fresh = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: l2 || "https://hub.securax.localhost/app/",
        beforeParse(w) { w.localStorage.setItem("gm_mine_done", "true"); w.fetch = () => Promise.reject(new Error("offline")); w.scrollTo = () => {};
          w.alert = () => {}; w.__asked = 0; w.confirm = () => { w.__asked++; return true; }; } });
      setTimeout(() => {
        const ls = fresh.window.localStorage, k = JSON.parse(ls.getItem("gm_sync_odk") || "null"), ms = JSON.parse(ls.getItem("gm_ms_cfg") || "null");
        ok("the new device holds the same OneDrive key, no passphrase typed", !!k && k.k === "ZmFrZWZha2VmYWtlZmFrZQ==" && k.salt === "c2FsdHNhbHRzYWx0", JSON.stringify(k));
        ok("and the same Microsoft app id", !!ms && ms.id === "fake-app-id-one", JSON.stringify(ms));
        ok("the pairing leaves the address bar", !/#sync=/.test(fresh.window.location.href), fresh.window.location.href);
        ok("the OneDrive hand-over asked once before taking the key", fresh.window.__asked === 1, String(fresh.window.__asked));
    console.log("test142 sync hand-over: " + P + " passed, " + F + " failed");
    if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
    process.exit(0);
      }, 1800);
    }, 1500);
  });
}, 1800);
