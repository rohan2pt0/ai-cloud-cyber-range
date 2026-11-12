// v64: Breaks planner, slice 1. Finds the dates when both partners are off work,
// with the fewest leave days: HOLIDAY_LISTS, gmDaysOff, gmBreaks and the Breaks tab.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [], loans: [], ret: 50, tsav: 20, dream: "", goal: "", example: false };
// Fake today: 2027-01-04, so the planner scans 2027 with a fixed answer.
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
    // 1. gmDaysOff: gazetted holiday + every Saturday and Sunday.
    const me = { off: "satsun", list: "in-central", rh: [], own: [] };
    const off = w.gmDaysOff(me, "2027-01-01", "2027-01-31");
    ok("gmDaysOff includes Republic Day 2027-01-26", !!off["2027-01-26"], JSON.stringify(Object.keys(off)));
    const satSun = ["2027-01-02", "2027-01-03", "2027-01-09", "2027-01-10", "2027-01-16", "2027-01-17", "2027-01-23", "2027-01-24", "2027-01-30", "2027-01-31"];
    ok("gmDaysOff includes every Saturday and Sunday", satSun.every(x => !!off[x]), satSun.filter(x => !off[x]).join(","));
    const off24 = w.gmDaysOff({ off: "sun24", list: "in-central", rh: [], own: [] }, "2027-01-01", "2027-01-31");
    ok("sun24 keeps the 2nd and 4th Saturday, drops the others", !!off24["2027-01-09"] && !!off24["2027-01-23"] && !off24["2027-01-02"] && !off24["2027-01-16"]);
    const ownOff = w.gmDaysOff({ off: "satsun", list: "own", rh: [], own: [{ d: "2027-03-04", n: "Office founding day" }] }, "2027-03-01", "2027-03-10");
    ok("gmDaysOff includes a pasted own-list date", !!ownOff["2027-03-04"]);

    // 2. gmBreaks, both on satsun + in-central, from 2027-01-04.
    const wins = w.gmBreaks("2027-01-04", 365);
    ok("gmBreaks returns at most 6 windows", wins.length >= 1 && wins.length <= 6, String(wins.length));
    ok("every window is 3 days or longer", wins.every(x => x.days >= 3 && x.start <= x.end), JSON.stringify(wins.map(x => x.days)));
    ok("gmBreaks windows do not overlap", wins.every(x => wins.every(y => y === x || x.end < y.start || y.end < x.start)));
    const republic = wins.some(x => x.start <= "2027-01-26" && x.end >= "2027-01-26" && x.days >= 4 && x.leaveMe.length <= 1 && x.leavePartner.length <= 1);
    const holi = wins.some(x => x.start <= "2027-03-23" && x.end >= "2027-03-26");
    ok("gmBreaks finds the Republic Day bridge (4 days for 1 leave day) or the Holi-Good Friday window", republic || holi,
      JSON.stringify(wins.map(x => x.start + ".." + x.end + " d" + x.days)));
    if (republic) {
      const rw = wins.find(x => x.start <= "2027-01-26" && x.end >= "2027-01-26");
      ok("the Republic Day bridge takes Monday 25 Jan as leave", rw.leaveMe.indexOf("2027-01-25") >= 0 && rw.leavePartner.indexOf("2027-01-25") >= 0, JSON.stringify(rw.leaveMe));
      ok("the Republic Day bridge names its holiday", rw.holidays.some(h => /Republic/.test(h)), JSON.stringify(rw.holidays));
    }
    if (holi) {
      const hw = wins.find(x => x.start <= "2027-03-23" && x.end >= "2027-03-26");
      ok("the Holi window names Holi and Good Friday", hw.holidays.some(h => /Holi/.test(h)) && hw.holidays.some(h => /Good Friday/.test(h)), JSON.stringify(hw.holidays));
    }

    // 3. Partner on "sun": the Republic Day window needs more partner leave than mine.
    w.localStorage.setItem("gm_work", JSON.stringify({ two: true, me: { off: "satsun", list: "in-central", rh: [], own: [] }, partner: { off: "sun", list: "in-central", rh: [], own: [] } }));
    const wins2 = w.gmBreaks("2027-01-04", 365);
    const rw2 = wins2.filter(x => x.start <= "2027-01-26" && x.end >= "2027-01-26");
    ok("with partner on Sunday-only, a window still covers Republic Day", rw2.length > 0, JSON.stringify(wins2.map(x => x.start + ".." + x.end)));
    ok("that window needs more partner leave than mine", rw2.every(x => x.leavePartner.length > x.leaveMe.length),
      JSON.stringify(rw2.map(x => x.leaveMe + " vs " + x.leavePartner)));
    w.localStorage.removeItem("gm_work");

    // 4. Pasted own-list lines are parsed; bad lines are ignored and counted.
    const parsed = w.gmParseOwn("2027-01-26 <script>alert(1)</script>\nnot a date\n2027-03-10 Id-ul-Fitr\n");
    ok("gmParseOwn reads the good lines", parsed.list.length === 2 && parsed.list[0].d === "2027-01-26" && parsed.list[1].n === "Id-ul-Fitr", JSON.stringify(parsed));
    ok("gmParseOwn counts the bad lines", parsed.bad === 1, String(parsed.bad));

    // 5. The Breaks tab.
    w.goTab("breaks");
    const s = sec().querySelector(".section.active");
    ok("Breaks: the tab opens", !!s && /Breaks|days off together/.test(s.textContent), s && s.textContent.slice(0, 120));
    ok("Breaks: exactly one hero tile", s.querySelectorAll(".gm-hero").length === 1);
    ok("Breaks: the hero opens the tab, before its first card", s.firstElementChild === s.querySelector(".gm-hero"), s.firstElementChild && s.firstElementChild.className);
    ok("Breaks: no NaN or undefined on the page", !/NaN|undefined/.test(s.textContent), s.textContent.slice(0, 200));
    const how = s.querySelector("details.gm-how");
    ok("Breaks: the explanation is folded, closed", !!how && !how.open && /How this works/.test(how.querySelector("summary").textContent));
    const later = s.querySelector("details.gm-later");
    ok("Breaks: the other windows sit folded under Later (n)", !!later && !later.open && /Later \(\d+\)/.test(later.querySelector("summary").textContent), later && later.querySelector("summary").textContent);
    ok("Breaks: the example settings note asks to be corrected once", /Example settings: correct them once/.test(s.textContent));
    ok("Breaks: the work-calendars fold exists", !!s.querySelector("details.gm-work") && /Your work calendars/.test(s.querySelector("details.gm-work").textContent));
    ok("Breaks: the partner block shows when the profile has a partner", !!d.getElementById("gmw_off_partner"));

    // The script-tag line is shown escaped.
    w.localStorage.setItem("gm_work", JSON.stringify({ two: true, me: { off: "satsun", list: "own", rh: [], own: [{ d: "2027-01-26", n: "<script>alert(1)</script>" }] }, partner: { off: "satsun", list: "in-central", rh: [], own: [] } }));
    w.goTab("breaks");
    const s2 = sec().querySelector(".section.active");
    ok("Breaks: a script tag in a pasted name is shown escaped", /&lt;script&gt;/.test(s2.innerHTML) && s2.textContent.indexOf("<script>alert(1)</script>") >= 0);
    w.localStorage.removeItem("gm_work");

    // 6. The partner block hides without a partner and comes back with "Plan for two".
    w.P.pdob = "";
    w.goTab("breaks");
    ok("Breaks: no partner block without a partner", !d.getElementById("gmw_off_partner"));
    const two = d.getElementById("gmw_two");
    ok("Breaks: the Plan-for-two tick exists without a partner", !!two);
    two.checked = true;
    w.gmWorkSave();
    ok("Breaks: ticking Plan for two adds the partner block and saves", !!d.getElementById("gmw_off_partner") && !!w.gmG("gm_work", null));
    w.P.pdob = "1992-01-10";
  } catch (err) { ok("test ran without throwing", false, String(err && err.stack || err)); }
  console.log("test64 breaks planner: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
