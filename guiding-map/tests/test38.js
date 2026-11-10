// The calendar contract (principle `in-the-calendar`): every recurring step comes from one registry, and a newer calendar
// file never conflicts with an earlier one. Stable UIDs (an id is never removed, only retired), a fixed start date, a
// version in SEQUENCE, retired items end with UNTIL and CANCELLED, and the same version always produces the same events.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
// The ids already handed out. Add new ones here when you add an item; NEVER delete one (retire it in the registry instead):
// a calendar out there still holds an event with that UID.
const HANDED_OUT = ["quarter", "monthly", "weekly", "tax", "annual", "family-q1", "family-q2", "family-q3", "family-q4"];
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/index.html", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
setTimeout(() => {
  const w = d.window;
  const reg = w.gmCalendarRegistry();
  const ids = reg.map(e => e.id);
  ok(HANDED_OUT.every(id => ids.includes(id)), "every id ever handed out is still in the registry (retire, never delete): " + HANDED_OUT.filter(id => !ids.includes(id)));
  ok(new Set(ids).size === ids.length, "ids are unique");
  ok(reg.every(e => Number.isInteger(e.v) && e.v >= 1), "every item has a version");
  const strip = s => s.replace(/DTSTAMP:[0-9T]+/g, "DTSTAMP:x");
  const a = w.gmCalendarICS(), b = w.gmCalendarICS();
  ok(strip(a) === strip(b), "the same version always gives the same events (only the stamp differs)");
  const uids = (a.match(/UID:[^\r\n]+/g) || []);
  ok(uids.length === ids.length && new Set(uids).size === uids.length, "one stable UID per item");
  ok(uids.every(u => /^UID:securax-gm-[a-z0-9-]+@local$/.test(u)), "UIDs follow securax-gm-<id>@local");
  ok((a.match(/SEQUENCE:\d+/g) || []).length === ids.length, "every event carries its version as SEQUENCE");
  ok((a.match(/DTSTART:2026\d{4}T/g) || []).length === ids.length, "start dates are fixed in 2026, not moved to today on each export");
  const fam = w.gmCalendarICS("family");
  ok((fam.match(/BEGIN:VEVENT/g) || []).length === 4 && fam.includes("X-WR-CALNAME:Family health"), "the family preventive calendar is four yearly events");
  ok(fam.includes("RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=1MO") && fam.includes("RRULE:FREQ=YEARLY;BYMONTH=1;BYDAY=1MO"), "on the first Monday of each quarter");
  ok(!/Akshat|[A-Z][a-z]+ \+ /.test(fam.replace(/Family health|Life OS/g, "")), "no person's name is written into the shared file text");
  ok(w.gmCalendarICS("rhythm").split("BEGIN:VEVENT").length - 1 === 5, "the rhythm alone is the five rhythm events");
  ok(a.split("\r\n").every(l => Buffer.byteLength(l) <= 75), "lines are folded to 75 octets");
  // a retired item stops in every app: UNTIL ends the series, CANCELLED removes it where honoured
  ok(fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8").includes(String.raw`.replace(/;/g, "\\;")`), "the text escape writes a backslash before ';'");
  ok(/UNTIL=/.test(fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8")) && /STATUS:" \+ \(e\.retired \? "CANCELLED"/.test(fs.readFileSync(path.join(__dirname, "..", "ops.js"), "utf8")), "a retired item exports UNTIL and CANCELLED");
  w.goTab("cal");
  ok(!!w.document.querySelector("[onclick=\"gmCalendar('family')\"]"), "the family calendar has its own Add to calendar button");
  ok(!/NOW\./.test(w.document.getElementById("sections").textContent), "no shouted command on the family calendar");
  console.log("test38 calendar contract: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
