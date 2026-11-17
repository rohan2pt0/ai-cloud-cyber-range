// v128: how use is learned on the device (queue friction-meter, slice 1 of 5). Which feature was used on which day is
// counted locally and silently, so rarely used things can rest later with no task for the person. Nothing is sent.
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
  const today = (() => { const n = new Date(); return n.getFullYear() + "-" + ("0" + (n.getMonth() + 1)).slice(-2) + "-" + ("0" + n.getDate()).slice(-2); })();
  const usage = () => { try { return JSON.parse(w.localStorage.getItem("gm_use") || "{}") || {}; } catch (x) { return {}; } };

  ok("gmUsage is a function", typeof w.gmUsage === "function", typeof w.gmUsage);
  ok("gmUse is a function", typeof w.gmUse === "function", typeof w.gmUse);
  if (F) {
    console.log("test128 use meter: " + P + " passed, " + F + " failed");
    e.forEach(x => console.log("  " + x));
    process.exit(1);
  }

  w.goTab("money"); w.goTab("money");
  let u = usage();
  ok("opening the Money tab records tab:money, last used today", !!(u["tab:money"] && u["tab:money"].l === today), JSON.stringify(u["tab:money"]));
  ok("today appears once in its days", !!u["tab:money"] && Array.isArray(u["tab:money"].d)
    && u["tab:money"].d.filter(x => x === today).length === 1, JSON.stringify(u["tab:money"] && u["tab:money"].d));

  const fi = (w.KPIs || []).findIndex(k => k && k.id === "friends");
  ok("the friends system exists to open", fi > -1, "index " + fi);
  if (fi > -1) w.openK(fi);
  u = usage();
  ok("opening the friends system records sys:friends", !!u["sys:friends"], JSON.stringify(u["sys:friends"]));

  const btn = d.createElement("button");
  btn.setAttribute("data-feat", "feat:demo");
  d.body.appendChild(btn);
  btn.click();
  u = usage();
  ok("a click on a data-feat element records that value", !!u["feat:demo"], JSON.stringify(u["feat:demo"]));

  const m = w.gmUsage();
  ok("gmUsage returns the recorded map", !!m && m["tab:money"] && m["sys:friends"] && m["feat:demo"], JSON.stringify(m && Object.keys(m)));

  w.gmUse("bad id!");
  ok("an id with anything but letters, digits, colon and dash is ignored", !w.gmUsage()["bad id!"], "recorded anyway");

  const days = [], pad = n => ("0" + n).slice(-2);
  for (let i = 1; i <= 30; i++) days.push("2000-01-" + pad(i));
  w.localStorage.setItem("gm_use", JSON.stringify({ "days:test": { l: days[days.length - 1], d: days } }));
  w.gmUse("days:test");
  const dd = w.gmUsage()["days:test"].d;
  ok("the days list keeps at most 30, dropping the least recent", dd.length === 30 && dd.indexOf(days[0]) < 0 && dd.indexOf(today) > -1,
    JSON.stringify(dd));

  const big = {};
  for (let i = 0; i < 305; i++) big["f" + i] = { l: "2000-01-01", d: ["2000-01-01"] };
  w.localStorage.setItem("gm_use", JSON.stringify(big));
  w.gmUse("f304");
  const capped = w.gmUsage();
  ok("the map keeps at most 300 ids, dropping the least recent", Object.keys(capped).length <= 300 && !capped["f0"] && !!capped["f304"],
    Object.keys(capped).length + " ids");

  w.localStorage.setItem("gm_use", "{not json");
  let crashed = false;
  try { w.gmUse("tab:money"); } catch (x) { crashed = true; }
  ok("a damaged gm_use is replaced, never crashes", !crashed && !!w.gmUsage()["tab:money"], crashed ? "threw" : "not recorded");
  w.localStorage.setItem("gm_use", JSON.stringify(["wrong shape"]));
  crashed = false;
  try { w.gmUse("tab:plan"); } catch (x) { crashed = true; }
  ok("a gm_use of the wrong shape is replaced, never crashes", !crashed && !!w.gmUsage()["tab:plan"], crashed ? "threw" : "not recorded");

  console.log("test128 use meter: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
