// v131: the friendships system runs itself on Today (queue step-doers, slice 4). On a Wednesday one calm line names
// tonight's call: the friend from the 5 names called longest ago (never called counts as oldest), with the last note
// that mentions them; one tap says Called and the next render names the other. Fake data only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1985-04-10", country: "India", cur: "INR", gross: 200000, net: 150000, exp: 80000,
  sav: 500000, nw: 3000000, kids: [], loans: [], ret: 55, tsav: 20, example: false };
const stepdo = { "friends:0": ["Amit", "Neha"], "friends:2": [{ d: "2026-11-01", t: "Amit started a new job" }] };
let nowMs = new Date(2026, 10, 18, 20, 0, 0).getTime();   // Wednesday 18 Nov 2026
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    const RD = w.Date;
    function FD(...a) { return a.length ? new RD(...a) : new RD(nowMs); }
    FD.prototype = RD.prototype; FD.now = () => nowMs; FD.parse = RD.parse; FD.UTC = RD.UTC;
    w.Date = FD;
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.localStorage.setItem("gm_simple", "false"); w.localStorage.setItem("gm_mine_done", "true");
    w.localStorage.setItem("gm_stepdo", JSON.stringify(stepdo));
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const saved = () => { try { return JSON.parse(w.localStorage.getItem("gm_stepdo") || "{}") || {}; } catch (x) { return {}; } };
  w.goTab("today");
  let line = d.querySelector(".gm-friend-today"), d3 = d.querySelector("#sections .gm-d3");
  const above = !!line && !!d3 && !!(line.compareDocumentPosition(d3) & w.Node.DOCUMENT_POSITION_FOLLOWING);
  ok("Today shows one calm call line above the daily three", !!line && above && d.querySelectorAll(".gm-friend-today").length === 1,
    line ? "not above the daily three" : "no .gm-friend-today line");
  ok("the line names the friend called longest ago, with the last note that mentions them",
    !!line && /Amit/.test(line.textContent) && /started a new job/.test(line.textContent),
    line ? line.textContent.slice(0, 180) : "no line");
  const called = line && Array.prototype.slice.call(line.querySelectorAll("button")).filter((b) => /Called/.test(b.textContent))[0];
  ok("the line offers one Called tap", !!called, "missing a tap");
  if (called) called.click();
  const calls = saved()["friends:calls"];
  ok("Called records today for that friend", !!calls && calls.Amit === "2026-11-18", JSON.stringify(calls));
  w.goTab("today");
  line = d.querySelector(".gm-friend-today");
  ok("after Called, the line is a small win, never a second name the same night", !!line && /Called/.test(line.textContent) && /Amit/.test(line.textContent) && !/Neha/.test(line.textContent),
    line ? line.textContent : "no line");
  nowMs = new Date(2026, 10, 25, 20, 0, 0).getTime();   // the next Wednesday
  w.goTab("today");
  line = d.querySelector(".gm-friend-today");
  ok("next Wednesday names the other friend", !!line && /Neha/.test(line.textContent) && !/Amit/.test(line.textContent),
    line ? line.textContent : "no line");
  nowMs = new Date(2026, 10, 18, 20, 0, 0).getTime();

  nowMs = new Date(2026, 10, 19, 20, 0, 0).getTime();   // Thursday
  w.goTab("today");
  ok("on any other day there is no line", !d.querySelector(".gm-friend-today"));

  nowMs = new Date(2026, 10, 18, 20, 0, 0).getTime();
  w.localStorage.setItem("gm_stepdo", JSON.stringify({ "friends:0": ["", ""], "friends:2": [] }));
  w.goTab("today");
  ok("with no names there is no line", !d.querySelector(".gm-friend-today"));

  console.log("test131 friendships on Today: " + P + " passed, " + F + " failed");
  if (F) { e.forEach((x) => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
