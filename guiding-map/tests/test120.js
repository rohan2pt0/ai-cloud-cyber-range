// v120: nothing leaves its own origin until the person connects something (release gate guest-sends-nothing, doc release-readiness).
// The promise "your data stays on this device" is held here, not in a sentence: the app is booted twice, as a guest with empty
// storage and with a profile but nothing connected, every screen in TABS is opened, and every way a page can talk to another
// site is recorded: fetch, XMLHttpRequest, WebSocket, EventSource, sendBeacon, and anything the page would load by itself
// (a script, a style sheet, an image, a frame, a media file). A link the person may tap is not a request and is allowed.
// "Its own" means the page's origin and the person's own estate: the sibling names of hub.<their domain> and this machine itself
// (the Ask screen looks for the gateway there). The third boot is the hosted copy on someone else's static host.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const HOME = "https://hub.securax.localhost/", HOSTED = "https://apps.example.org/app/";
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

function boot(seed, home) {
  home = home || HOME;
  const calls = [];
  const rec = (how, u) => { try { calls.push({ how, url: new URL(String(u && u.url || u), home).href }); } catch (x) { calls.push({ how, url: String(u) }); } };
  const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: home,
    beforeParse(w) {
      if (seed) w.localStorage.setItem("sovP", JSON.stringify(seed));
      w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {};
      w.fetch = (u) => { rec("fetch", u); return Promise.reject(new Error("offline")); };
      w.XMLHttpRequest = function () { this.open = (m, u) => rec("XMLHttpRequest", u); this.send = () => {}; this.setRequestHeader = () => {}; this.abort = () => {}; };
      w.WebSocket = function (u) { rec("WebSocket", u); this.close = () => {}; this.send = () => {}; this.addEventListener = () => {}; };
      w.EventSource = function (u) { rec("EventSource", u); this.close = () => {}; this.addEventListener = () => {}; };
      try { Object.defineProperty(w.navigator, "sendBeacon", { value: (u) => { rec("sendBeacon", u); return true; }, configurable: true }); } catch (x) { /* no navigator */ }
    } });
  return { dom, calls, home };
}
const foreign = (u, home) => {
  try {
    const x = new URL(u, home), h = new URL(home);
    if (!/^(https?|wss?):$/.test(x.protocol) || x.origin === h.origin) return false;
    if (/^(localhost|127\.0\.0\.1|\[::1\])$/.test(x.hostname) || /\.localhost$/.test(x.hostname)) return false;      // this machine itself
    return !(h.hostname.indexOf("hub.") === 0 && x.hostname.endsWith("." + h.hostname.slice(4)));                  // the estate's sibling names
  } catch (x) { return false; }
};
const loads = (d, home) => [...d.querySelectorAll("script[src],link[rel~=stylesheet][href],link[rel~=preload][href],img[src],iframe[src],video[src],audio[src],source[src],embed[src],object[data]")]
  .map(n => n.getAttribute("src") || n.getAttribute("href") || n.getAttribute("data")).filter(u => foreign(u, home));

const guest = boot(null), person = boot(prof), hosted = boot(prof, HOSTED);
setTimeout(() => {
  for (const [who, run] of [["a guest", guest], ["a person with a profile and nothing connected", person], ["the hosted copy, nothing connected", hosted]]) {
    const w = run.dom.window, d = w.document, seen = [], auto = loads(d, run.home);
    let tabs = []; try { tabs = w.eval("TABS").map(t => t[0]); } catch (x) { /* a guest may still be in set-up */ }
    for (const t of tabs) { try { w.goTab(t); seen.push(t); auto.push(...loads(d, run.home)); } catch (x) { /* a screen's own bug is another test's subject */ } }
    const out = run.calls.filter(c => foreign(c.url, run.home));
    ok(who + ": no request leaves its own origin, on boot or on any screen", out.length === 0, out.slice(0, 4).map(c => c.how + " " + c.url).join(" | "));
    ok(who + ": no screen loads a script, style, image, frame or media file from another site", auto.length === 0, [...new Set(auto)].slice(0, 4).join(" | "));
    if (who !== "a guest") ok(who + ": every screen in TABS was opened (" + seen.length + ")", tabs.length >= 20 && seen.length === tabs.length, seen.length + " of " + tabs.length);
  }
  // the recorder itself works: a call to another site would have been seen (a test that cannot fail proves nothing)
  const probe = boot(null); probe.dom.window.fetch("https://elsewhere.invalid/x").catch(() => {});
  ok("the recorder sees a call to another site", probe.calls.filter(c => foreign(c.url, HOME)).length === 1);
  ok("the estate's own names and this machine are not another site, and a look-alike name is",
    !foreign("https://api.securax.localhost/healthz", HOME) && !foreign("http://localhost:8080/healthz", HOSTED) && foreign("https://api.securax.localhost.example.org/x", HOME));
  console.log("test120 nothing leaves its own origin: " + P + " passed, " + F + " failed"); if (F) e.forEach(x => console.log("  " + x));
  process.exit(F ? 1 : 0);
}, 1800);
