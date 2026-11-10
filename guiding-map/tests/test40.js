// v40: calendar-everywhere, dated items. The career plan's dates and the papers' renewals go into the person's calendar on
// the same contract as the repeating steps (test38): a UID from the item's permanent id, the item's own date, SEQUENCE raised
// when the date or wording changes, and CANCELLED when it is done or gone, so a newer file never doubles an event.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const iso = d => d.toISOString().slice(0, 10), plus = n => { const d = new Date(); d.setDate(d.getDate() + n); return iso(d); };
const career = { cfg: { noticeStart: plus(-10), noticeMonths: 3 }, done: {} };
const inbox = [
  { id: "fakeRenew1", t: "Renew health insurance (fake-policy), before 01 Jan 2099", next: "Compare and renew it", kind: "issue", area: "Insurance", due: plus(20), from: "lifedocs" },
  { id: "fakePrem1", t: "Pay the life insurance premium (fake-term) before 05 Jan 2099", kind: "issue", area: "Insurance", due: plus(30), from: "lifedocs" },
  { id: "fakePlain", t: "Fake call the plumber", kind: "action", due: plus(2), from: "capture" }
];
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("gm_career", JSON.stringify(career)); w.localStorage.setItem("gm_inbox", JSON.stringify(inbox));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.URL.createObjectURL = () => "blob:x"; } });
const ev = (ics, uid) => { const m = ics.split("BEGIN:VEVENT").find(b => b.includes("UID:securax-gm-" + uid + "@local")); return m || ""; };
const seq = (b) => +((b.match(/SEQUENCE:(\d+)/) || [])[1] || 0);
const strip = s => s.replace(/DTSTAMP:[0-9T]+/g, "DTSTAMP:x");
setTimeout(() => {
  const w = dom.window, d = w.document, G = k => JSON.parse(w.localStorage.getItem(k) || "null");
  let car = w.gmCalendarDatedICS("career"), ren = w.gmCalendarDatedICS("renewals");
  ok("career: every dated plan step is an all-day event with a permanent UID", /UID:securax-gm-car-offer-paper@local/.test(car) && /DTSTART;VALUE=DATE:\d{8}/.test(ev(car, "car-offer-paper")) && (car.match(/BEGIN:VEVENT/g) || []).length === 14, (car.match(/BEGIN:VEVENT/g) || []).length);
  ok("career: the date is the plan's own date (notice start + 14 days)", ev(car, "car-offer-paper").includes("DTSTART;VALUE=DATE:" + plus(4).replace(/-/g, "")));
  ok("renewals: renewal and premium items are in, a plain action is not", /securax-gm-ib-fakeRenew1@local/.test(ren) && /securax-gm-ib-fakePrem1@local/.test(ren) && !/fakePlain/.test(ren));
  ok("the same data always gives the same file (only the stamp differs)", strip(car) === strip(w.gmCalendarDatedICS("career")));
  ok("first export: SEQUENCE 1, CONFIRMED, a reminder on the day", seq(ev(ren, "ib-fakeRenew1")) === 1 && /STATUS:CONFIRMED/.test(ev(ren, "ib-fakeRenew1")) && /TRIGGER:PT9H/.test(ev(ren, "ib-fakeRenew1")));
  ok("escaping: a comma in a title goes out as \\,", ev(ren, "ib-fakeRenew1").includes("(fake-policy)\\, before"));

  // export, then change the notice date: the moved steps update in place (SEQUENCE 2), nothing doubles
  w.gmCalendarDated("career"); w.gmCalendarDated("renewals");
  const led = G("gm_cal_seq");
  ok("exporting records each UID in the ledger", led && led["securax-gm-car-offer-paper"] && led["securax-gm-car-offer-paper"].v === 1 && led["securax-gm-ib-fakeRenew1"]);
  const c2 = G("gm_career"); c2.cfg.noticeStart = plus(-5); w.localStorage.setItem("gm_career", JSON.stringify(c2));
  car = w.gmCalendarDatedICS("career");
  ok("a moved date raises SEQUENCE and keeps the UID", seq(ev(car, "car-offer-paper")) === 2 && (car.match(/UID:securax-gm-car-offer-paper@local/g) || []).length === 1);
  ok("a renewal that did not change keeps SEQUENCE 1", seq(ev(w.gmCalendarDatedICS("renewals"), "ib-fakeRenew1")) === 1);

  // done, and gone: both are cancelled, never left behind
  w.gmInboxDone("fakeRenew1");
  const a = G("gm_inbox").filter(x => x.id !== "fakePrem1"); w.localStorage.setItem("gm_inbox", JSON.stringify(a));
  ren = w.gmCalendarDatedICS("renewals");
  ok("a renewal marked done is sent as CANCELLED with a higher SEQUENCE", /STATUS:CANCELLED/.test(ev(ren, "ib-fakeRenew1")) && seq(ev(ren, "ib-fakeRenew1")) === 2);
  ok("a renewal gone from the list is sent once more as CANCELLED", /STATUS:CANCELLED/.test(ev(ren, "ib-fakePrem1")) && seq(ev(ren, "ib-fakePrem1")) === 2 && !/VALARM/.test(ev(ren, "ib-fakePrem1")));
  w.gmCalendarDated("renewals");
  ok("…and after that export it is not sent again", !/fakePrem1/.test(w.gmCalendarDatedICS("renewals")));
  ok("the ledger is bounded (at most 500 entries)", Object.keys(G("gm_cal_seq")).length <= 500 && /at most 500/.test(fs.readFileSync(path.join(__dirname, '..', 'ops.js'), 'utf8')));

  // the buttons are where the dates are
  w.goTab("career");
  ok("Career has 'Add the plan to my calendar'", /Add the plan to my calendar/.test(d.getElementById("sections").textContent));
  const ib = G("gm_inbox"); ib.push({ id: "fakeRenew2", t: "Renew vehicle insurance (fake-car) before 09 Jan 2099", kind: "issue", due: plus(40), from: "lifedocs" }); w.localStorage.setItem("gm_inbox", JSON.stringify(ib));
  w.goTab("inbox");
  ok("Inbox has 'Add 1 renewal to my calendar'", /Add 1 renewal to my calendar/.test(d.getElementById("sections").textContent), d.getElementById("sections").textContent.slice(0, 200));

  console.log("test40 calendar dates: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
