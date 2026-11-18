// v133: friction is noticed by itself on the device (queue friction-meter, slice 4 of 5). Three signals are counted,
// quietly and locally: a system sheet closed with no tick or input (an abandon), three taps on one spot within a second
// (a rage), and switching between the same two tabs four times within ten seconds (a bounce). Nothing is sent.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const seen = () => { try { return JSON.parse(w.localStorage.getItem("gm_friction_seen") || "{}") || {}; } catch (x) { return {}; } };

  ok("gmFrictionSeen is a function", typeof w.gmFrictionSeen === "function", typeof w.gmFrictionSeen);
  ok("gmFrictionTop is a function", typeof w.gmFrictionTop === "function", typeof w.gmFrictionTop);
  if (F) {
    console.log("test133 friction meter: " + P + " passed, " + F + " failed");
    e.forEach(x => console.log("  " + x));
    process.exit(1);
  }

  const fi = w.KPIs.findIndex(k => k && k.id === "friends");
  ok("the friends system exists to open", fi > -1, "index " + fi);

  if (fi > -1) w.openK(fi);
  w.closeM();
  ok("closing a system sheet with no change records one abandon", seen()["sys:friends"] === 1, JSON.stringify(seen()));

  if (fi > -1) w.openK(fi);
  const tick = d.querySelector("#m_sys input[type=checkbox]");
  if (tick) tick.click();
  w.closeM();
  ok("closing after a tick does not record an abandon", seen()["sys:friends"] === 1, JSON.stringify(seen()));

  const btn = d.createElement("button");
  btn.setAttribute("data-feat", "feat:demo");
  d.body.appendChild(btn);
  btn.click(); btn.click(); btn.click();
  ok("three taps on one spot within a second record one rage", seen()["feat:demo"] === 1, JSON.stringify(seen()));

  w.goTab("money"); w.goTab("risk"); w.goTab("money"); w.goTab("risk");
  ok("four switches between money and risk within ten seconds record one bounce", seen()["tab:money-risk"] === 1, JSON.stringify(seen()));

  w.localStorage.setItem("gm_friction_seen", JSON.stringify({ "sys:a": 5, "sys:b": 3, "sys:c": 9, "sys:d": 1 }));
  const top = w.gmFrictionTop(3);
  ok("gmFrictionTop(3) returns the three highest counts", Array.isArray(top) && top.length === 3
    && top[0].id === "sys:c" && top[1].id === "sys:a" && top[2].id === "sys:b", JSON.stringify(top));

  w.localStorage.setItem("gm_friction_seen", "{not json");
  let crashed = false;
  try { w.gmFriction("sys:x"); } catch (x) { crashed = true; }
  ok("a damaged gm_friction_seen is replaced, never crashes", !crashed && seen()["sys:x"] === 1, crashed ? "threw" : "not recorded");

  w.localStorage.setItem("gm_friction_seen", JSON.stringify(["wrong shape"]));
  crashed = false;
  try { w.gmFriction("sys:y"); } catch (x) { crashed = true; }
  ok("a gm_friction_seen of the wrong shape is replaced, never crashes", !crashed && seen()["sys:y"] === 1, crashed ? "threw" : "not recorded");

  const big = {};
  for (let i = 0; i < 205; i++) big["f" + i] = 1;
  w.localStorage.setItem("gm_friction_seen", JSON.stringify(big));
  w.gmFriction("sys:z");
  const capped = seen();
  ok("the map keeps at most 200 keys, dropping the oldest", Object.keys(capped).length <= 200 && !capped["f0"] && !!capped["sys:z"],
    Object.keys(capped).length + " keys");

  console.log("test133 friction meter: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
