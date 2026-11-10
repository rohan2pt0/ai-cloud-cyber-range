// kit3: the calendar contract in the OS kit (principle `in-the-calendar`). Vantage's rhythm becomes one repeating event per
// review, from the edition's own cadence list: permanent UIDs (an id is never removed, only retired), fixed start dates, a
// version as SEQUENCE, and the same version always gives the same events.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0; const ok = (c, n) => { c ? P++ : (F++, console.log("FAIL", n)); };
// Ids already handed out to people's calendars. Add new ones; NEVER delete one (retire it in the edition instead).
const HANDED_OUT = ["w-risk", "w-wins", "f-team", "m-exco", "m-tools", "m-vuln", "m-access", "q-board", "q-okr", "q-drill", "q-tprm",
  "q-budget", "h-restore", "y-policy", "y-strategy", "y-bcp", "y-audit", "y-insure", "y-train"];
const html = fs.readFileSync(path.join(__dirname, '..', 'vantage', 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/vantage/",
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; w.URL.revokeObjectURL = () => {};
    w.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) }); } });
setTimeout(() => {
  const w = dom.window, K = w.OSK;
  const ids = (K.cfg("cadence").items || []).map(i => i.id);
  ok(HANDED_OUT.every(id => ids.includes(id)), "every review id ever handed out is still in the edition: " + HANDED_OUT.filter(id => !ids.includes(id)));
  ok(new Set(ids).size === ids.length, "review ids are unique");
  const strip = s => s.replace(/DTSTAMP:[0-9T]+/g, "DTSTAMP:x");
  const a = K.cadenceICS(), b = K.cadenceICS();
  ok(strip(a) === strip(b), "the same version always gives the same events");
  const uids = a.match(/UID:[^\r\n]+/g) || [];
  ok(uids.length === ids.length && new Set(uids).size === uids.length, "one stable UID per review");
  ok(uids.every(u => /^UID:securax-vantage-[a-z0-9-]+@local$/.test(u)), "UIDs are securax-vantage-<id>@local");
  ok((a.match(/SEQUENCE:\d+/g) || []).length === ids.length, "each event carries its version");
  ok((a.match(/DTSTART:2026\d{4}T/g) || []).length === ids.length, "start dates are fixed in 2026, not moved to today");
  ok(a.includes("RRULE:FREQ=WEEKLY;BYDAY=MO") && a.includes("RRULE:FREQ=WEEKLY;BYDAY=FR"), "the Monday review and the Friday wins land on their days");
  ok(/RRULE:FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=\d+/.test(a) && /RRULE:FREQ=YEARLY;BYMONTH=\d+;BYMONTHDAY=\d+/.test(a), "quarterly and yearly reviews repeat as such");
  ok(a.split("\r\n").every(l => Buffer.byteLength(l) <= 75), "lines are folded to 75 octets");
  ok(K.icsText("a;b,c") === "a\;b\\,c", "semicolons and commas in text are escaped");
  ok(a.includes("X-WR-CALNAME:Vantage rhythm"), "the calendar is named for the app");
  K.go("cadence");
  ok(!!w.document.querySelector('[data-a="cadCal"]'), "the Rhythm screen has Add the rhythm to my calendar");
  console.log("kit3 calendar contract: " + P + " passed, " + F + " failed");
  process.exit(F ? 1 : 0);
}, 1500);
