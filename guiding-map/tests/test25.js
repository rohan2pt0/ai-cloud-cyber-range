// Pattern interrupt: in a heavy week the app subtracts. It notices the signs (heavy-week words in your notes and questions,
// low-energy days), offers one question, one small action and one rest block, blocks new plans in recovery mode, checks the
// AI's answer in code, and tells you when you have asked the same question before.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
setTimeout(() => {
  const w = d.window, ls = w.localStorage, day = (n) => { const x = new Date(); x.setDate(x.getDate() - n); return w.dKey ? w.dKey(x) : x.toISOString().slice(0, 10); };
  w.HTMLAnchorElement.prototype.click = function () {};
  // A calm week: nothing fires.
  ok(!w.gmSatScan().fire && w.gmInterruptHTML() === "", "a calm week shows nothing");
  // A heavy week: two notes and one low-energy day.
  const notes = {}; notes[day(0)] = "Totally overwhelmed today"; notes[day(2)] = "Life is a mess, need a new system";
  ls.setItem("gm_notes", JSON.stringify(notes));
  const en = {}; en[day(1)] = 2; ls.setItem("gm_energy", JSON.stringify(en));
  const s = w.gmSatScan();
  ok(s.fire && s.score === 3 && s.low === 1, "3 signs in 7 days turn it on");
  let card = w.gmInterruptHTML();
  ok(/not the week for a new plan/.test(card) && /One question/.test(card) && /One small thing/.test(card) && /Book 3 hours of rest/.test(card), "one question, one action, one rest block");
  ok(!/framework|KPI|OKR/i.test(card), "the card itself offers no plan");
  const ics = w.gmRestIcs();
  ok(/BEGIN:VEVENT/.test(ics) && /DTSTART:\d{8}T1400/.test(ics) && /Rest \(no laptop/.test(ics), "the rest block is a real calendar event, Saturday 14:00");
  w.gmSatLater();
  ok(w.gmInterruptHTML() === "", "Not now hides it for a few days");
  // Recovery mode: new plans wait; the AI is checked in code.
  w.gmSatPause();
  ok(w.gmInterruptHTML() === "" && JSON.parse(ls.getItem("gm_recovery")).until, "pausing turns on recovery mode for 7 days");
  const before = w.S.okrs.length; w.addOKR();
  ok(w.S.okrs.length === before && !w.document.getElementById("gmPin"), "no new goal while in recovery");
  const planned = w.gmRecoveryGuard("Here is a 30-day framework with KPIs: Step 1 …");
  ok(/not giving you a plan/.test(planned) && !/KPI/.test(planned), "a planning answer is replaced, not shown");
  ok(w.gmRecoveryGuard("Rest tonight. What would help most?") === "Rest tonight. What would help most?", "a short kind answer passes");
  w.gmRecoveryOff();
  ok(w.gmRecoveryGuard("A framework with KPIs") === "A framework with KPIs", "outside recovery the guard does nothing");
  // "You have asked this before."
  w.gmAskRemember("How do I fix my whole life in one week with a system?");
  ok(w.gmAskSeen("how can I fix my whole life in one week with a new system").length === 1, "a near-repeat question is recognised");
  ok(w.gmAskSeen("What is the tax on fixed deposits?").length === 0, "a different question is not");
  console.log("test25 pattern interrupt: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 800);
