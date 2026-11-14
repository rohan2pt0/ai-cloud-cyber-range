// v99: alerts with one Allow tap (zero-setup, slice 1b part 2). When this device is paired to its estate (gm_sync_cfg),
// the Nudges card offers one "Allow alerts" tap that uses the estate's own push endpoint — no address to paste, no Worker
// URL in view. The old Worker URL path stays, folded under "Other ways (for engineers)", and is unchanged when there is no
// gm_sync_cfg. gmPushOn asks /push/key then posts /push/subscribe with the sync's Authorization header; gmPushOff sends a
// DELETE with the endpoint.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, kids: [], loans: [], ret: 50, tsav: 20, example: false };

function boot(withSync) {
  const calls = [];
  const sub = { endpoint: "https://fcm.googleapis.com/fcm/send/fake", toJSON() { return { endpoint: this.endpoint, keys: { p256dh: "x", auth: "y" } }; } };
  const reg = {
    pushManager: {
      subscribe: () => Promise.resolve(sub),
      getSubscription: () => Promise.resolve({ endpoint: sub.endpoint, unsubscribe: () => Promise.resolve(true) })
    }
  };
  const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), {
    runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
    beforeParse(w) {
      w.localStorage.setItem("sovP", JSON.stringify(prof));
      if (withSync) w.localStorage.setItem("gm_sync_cfg", JSON.stringify({ url: "https://estate.example.org/sync", key: "fake-device-token", user: "fake" }));
      w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
      w.Notification = { permission: "granted", requestPermission: () => Promise.resolve("granted") };
      w.PushManager = function () {};
      w.navigator.serviceWorker = { ready: Promise.resolve(reg), controller: null, addEventListener() {}, register: () => Promise.resolve({ update() {} }) };
      w.fetch = (url, opts) => {
        const u = String(url);
        calls.push({ u, o: opts || {} });
        if (u.indexOf("/push/key") >= 0) return Promise.resolve({ ok: true, json: () => Promise.resolve({ key: "BA" }) });
        if (u.indexOf("/push/subscribe") >= 0) return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) });
        return Promise.resolve({ ok: false, json: () => Promise.resolve(null) });
      };
    }
  });
  dom.__calls = calls;
  return dom;
}

const estate = boot(true), plain = boot(false);
setTimeout(async () => {
  const w = estate.window, d = w.document;
  w.goTab("ops");
  const ops = d.getElementById("sections").innerHTML;
  ok("paired: the card offers one Allow alerts tap",
    ops.indexOf("Allow alerts") >= 0 && ops.indexOf("Alerts from your estate, on this device. One tap; nothing to install.") >= 0);
  ok("paired: the other ways are folded", ops.indexOf("Other ways (for engineers)") >= 0);
  const pu = d.getElementById("pushUrl");
  ok("paired: no Worker URL input outside a closed details", pu && pu.closest("details") && !pu.closest("details").open);

  await w.gmPushOn();
  const keyCall = estate.__calls.find(c => c.u.indexOf("/push/key") >= 0);
  const subCall = estate.__calls.find(c => c.u.indexOf("/push/subscribe") >= 0);
  ok("gmPushOn asks the estate for its push key", !!keyCall && keyCall.u.indexOf("/push/key?user=fake") >= 0);
  ok("gmPushOn sends the sync Authorization header", !!keyCall && keyCall.o.headers && keyCall.o.headers.Authorization === "Bearer fake-device-token");
  ok("gmPushOn posts the subscription to the estate", !!subCall && subCall.o.method === "POST");
  ok("gmPushOn records the estate as the push source", w.gmG("gm_push_on", false) === true && w.gmG("gm_push_via", "") === "estate");

  await w.gmPushOff();
  const delCall = estate.__calls.find(c => c.o.method === "DELETE" && c.u.indexOf("/push/subscribe") >= 0);
  ok("gmPushOff sends a DELETE with the endpoint", !!delCall && delCall.u.indexOf("endpoint=") >= 0 && delCall.u.indexOf("fcm.googleapis.com") >= 0);
  ok("gmPushOff clears the push flags", w.localStorage.getItem("gm_push_on") === null && w.localStorage.getItem("gm_push_via") === null);

  const w2 = plain.window, d2 = w2.document;
  w2.goTab("ops");
  const ops2 = d2.getElementById("sections").innerHTML;
  ok("unpaired: the old card is unchanged", ops2.indexOf("Enable nudges on this device") >= 0 && ops2.indexOf("free ntfy app") >= 0);
  ok("unpaired: no estate wording", ops2.indexOf("Allow alerts") < 0 && ops2.indexOf("Other ways (for engineers)") < 0);

  console.log("test99 alerts with one Allow tap: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
