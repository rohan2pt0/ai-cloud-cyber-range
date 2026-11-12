// v65: Breaks planner, slice 1b. Work calendars change on a date: a person holds
// periods, a gap between jobs is off, a pasted list replaces the built-in year, and
// the yearly "paste next year's list" reminder is in the calendar registry.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [], loans: [], ret: 50, tsav: 20, dream: "", goal: "", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) {
    const RealDate = w.Date;
    w.Date = class extends RealDate {
      constructor(...a) { super(...(a.length ? a : [2027, 0, 4])); }
      static now() { return new RealDate(2027, 0, 4).getTime(); }
    };
    w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
  } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  try {
    // 1. Two periods: old job to 2026-12-30 on sun24, new job from 2027-01-01 on satsun.
    const twoJobs = { periods: [
      { from: "", to: "2026-12-30", off: "sun24", list: "in-central", extra: [], rh: [], own: [] },
      { from: "2027-01-01", to: "", off: "satsun", list: "in-central", extra: [], rh: [], own: [] }
    ] };
    const off = w.gmDaysOff(twoJobs, "2026-12-01", "2027-01-31");
    ok("period 1: 2nd Saturday 2026-12-12 is off", !!off["2026-12-12"], JSON.stringify(Object.keys(off)));
    ok("period 1: 3rd Saturday 2026-12-19 is not off", !off["2026-12-19"], off["2026-12-19"]);
    ok("the day between jobs, 2026-12-31, is off", !!off["2026-12-31"], off["2026-12-31"]);
    ok("period 2: 2nd Saturday 2027-01-09 is off", !!off["2027-01-09"], off["2027-01-09"]);
    ok("period 2: Saturday 2027-01-16 is off", !!off["2027-01-16"], off["2027-01-16"]);
    ok("period 2: Sunday 2027-01-17 is off", !!off["2027-01-17"], off["2027-01-17"]);

    // 2. An old single-object work calendar is read as one period, never loses a setting.
    const oldMe = { off: "satsun", list: "in-central", rh: [], own: [] };
    w.localStorage.setItem("gm_work", JSON.stringify({ two: false, me: oldMe, partner: oldMe }));
    const oldOff = w.gmDaysOff(w.gmG("gm_work", null).me, "2027-01-01", "2027-01-31");
    ok("an old single-object calendar still gives its weekly offs", !!oldOff["2027-01-02"] && !!oldOff["2027-01-03"], JSON.stringify(Object.keys(oldOff)));
    ok("an old single-object calendar still gives its holidays", !!oldOff["2027-01-26"], oldOff["2027-01-26"]);
    ok("an old single-object calendar still plans breaks", w.gmBreaks("2027-01-04", 365).length >= 1);

    // 3. A pasted list for a year replaces the built-in dates for that year, in that period only.
    const ownPerson = { periods: [
      { from: "", to: "2027-06-30", off: "satsun", list: "in-central", extra: [], rh: [], own: [{ d: "2027-03-04", n: "Office founding day" }] },
      { from: "2027-07-01", to: "", off: "satsun", list: "in-central", extra: [], rh: [], own: [] }
    ] };
    const ownOff = w.gmDaysOff(ownPerson, "2027-01-01", "2027-12-31");
    ok("a pasted 2027 list replaces the built-in 2027 dates", !ownOff["2027-01-26"], ownOff["2027-01-26"]);
    ok("the pasted date itself is a day off", !!ownOff["2027-03-04"], ownOff["2027-03-04"]);
    ok("the next period still uses the built-in list", !!ownOff["2027-10-02"], ownOff["2027-10-02"]);

    // 4. The optional Maharashtra add-on joins a period through "extra".
    const mhPerson = { periods: [{ from: "", to: "", off: "satsun", list: "in-central", extra: ["in-mh-extra"], rh: [], own: [] }] };
    const mhOff = w.gmDaysOff(mhPerson, "2027-05-01", "2027-05-01");
    ok("the Maharashtra add-on adds Maharashtra Day", !!mhOff["2027-05-01"], JSON.stringify(mhOff));

    // 5. The fold shows a line per period, the bank pattern label, and the add-a-period button.
    w.localStorage.setItem("gm_work", JSON.stringify({ two: false, me: twoJobs, partner: { periods: [{ from: "", to: "", off: "satsun", list: "in-central", extra: [], rh: [], own: [{ d: "2027-03-04", n: "Office founding day" }] }] } }));
    w.goTab("breaks");
    const s = sec().querySelector(".section.active");
    ok("the fold shows a line for each period", /From Sat, 1 Jan 2027|From .*2027/.test(s.textContent) && (s.textContent.match(/Edit/g) || []).length >= 2, s.textContent.slice(0, 300));
    ok("sun24 is named as the bank pattern", /Bank pattern: Sunday plus 2nd and 4th Saturday/.test(s.textContent), s.textContent.slice(0, 400));
    ok("the add-a-period button is there", /My job changes on a date/.test(s.textContent));
    ok("a pasted year says it is using the office's list", /Using your office's list for 2027/.test(s.textContent));
    const addBtn = [].slice.call(s.querySelectorAll("button")).find(b => /My job changes on a date/.test(b.textContent));
    const before = JSON.parse(w.localStorage.getItem("gm_work")).me.periods.length;
    addBtn.click();
    const after = JSON.parse(w.localStorage.getItem("gm_work")).me.periods.length;
    ok("one tap adds a dated period", after === before + 1 && !!d.getElementById("gmw_from_me_2"), String(before) + " -> " + String(after));
    w.localStorage.removeItem("gm_work");

    // 6. The yearly reminder is a permanent calendar item.
    const reg = w.gmCalendarRegistry();
    const hl = reg.filter(x => x.id === "holiday-list")[0];
    ok("the registry holds holiday-list in the rhythm", !!hl && hl.group === "rhythm" && hl.v === 1, JSON.stringify(hl));
    const ics = w.gmCalendarICS("rhythm");
    ok("the reminder is the 2nd Saturday of December at 10:15", ics.includes("SUMMARY:Paste next year's holiday list") && ics.includes("RRULE:FREQ=YEARLY;BYMONTH=12;BYDAY=2SA") && ics.includes("DTSTART:20261212T100000") && ics.includes("DTEND:20261212T101500"), ics.slice(0, 200));
  } catch (err) { ok("test ran without throwing", false, String(err && err.stack || err)); }
  console.log("test65 work-calendar periods: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
