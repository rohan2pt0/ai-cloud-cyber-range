// v129: a recurring step ("Every Wednesday 8:30pm", "Monthly on the 1st Sunday", "Daily") reads its own words and gets
// Add to calendar under it (queue step-doers, slice 3). The UID never changes, the start date is fixed at the first
// export, and SEQUENCE rises only when the rule or the words change. A step with no day or rhythm gets no button.
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
    w.URL.createObjectURL = () => "blob:x";
  } });
setTimeout(() => {
  const w = dom.window, d = w.document;
  const stepBy = (re) => Array.prototype.slice.call(d.querySelectorAll("#m_sys .step")).filter((s) => re.test(s.textContent))[0];
  const boxesOf = (step) => { const out = []; let n = step && step.nextElementSibling; while (n && !/(^|\s)step(\s|$)/.test(n.className)) { out.push(n); n = n.nextElementSibling; } return out; };
  const calOf = (step) => { const b = boxesOf(step).filter((x) => x.querySelector("[data-stepdo-cal]"))[0]; return b ? b.querySelector("[data-stepdo-cal]") : null; };
  const evOf = (ics, uid) => (ics.split("BEGIN:VEVENT").filter((x) => x.indexOf("UID:" + uid) >= 0)[0] || "");
  const seqOf = (b) => +((b.match(/SEQUENCE:(\d+)/) || [])[1] || 0);
  const dtOf = (b) => (b.match(/DTSTART:(\d{8}T\d{6})/) || [])[1] || "";

  const fi = w.KPIs.findIndex((k) => k.id === "friends");
  ok("the friends system exists", fi >= 0, "index " + fi);
  if (fi >= 0) w.openK(fi);
  const wedText = fi >= 0 ? String(w.KPIs[fi].steps[1]) : "";

  const wed = stepBy(/Every Wednesday 8:30pm/);
  ok("the Every Wednesday 8:30pm step is shown", !!wed, "no step");
  ok("it shows Add to calendar under it", !!calOf(wed) && /Add to calendar/i.test(calOf(wed).textContent), calOf(wed) ? calOf(wed).textContent : "no button");

  const uid = "securax-sys-friends-1@local";
  const first = w.gmStepICS("friends", 1, wedText), ev1 = evOf(first, uid);
  ok("its event repeats weekly on Wednesday", /RRULE:FREQ=WEEKLY;BYDAY=WE/.test(ev1), ev1 ? "no weekly rule" : "no event");
  ok("its DTSTART is at 20:30", /T203000/.test(dtOf(ev1)), dtOf(ev1) || "no DTSTART");
  ok("it keeps the permanent UID and SEQUENCE 1", /UID:securax-sys-friends-1@local/.test(ev1) && seqOf(ev1) === 1, seqOf(ev1) + " " + ev1.split("\r\n")[1]);

  w.gmStepCalendar("friends", 1, wedText); w.gmStepCalendar("friends", 1, wedText);
  const again = evOf(w.gmStepICS("friends", 1, wedText), uid);
  ok("exported again unchanged it keeps SEQUENCE 1", seqOf(again) === 1, "SEQUENCE " + seqOf(again));
  ok("…and the same DTSTART", dtOf(again) === dtOf(ev1) && !!dtOf(again), dtOf(again) + " vs " + dtOf(ev1));

  const changed = wedText + " Now 20 minutes.";
  w.gmStepCalendar("friends", 1, changed);
  const next = evOf(w.gmStepICS("friends", 1, changed), uid);
  ok("after the step's words change it becomes SEQUENCE 2", seqOf(next) === 2, "SEQUENCE " + seqOf(next));
  ok("…with the same UID and fixed DTSTART", /UID:securax-sys-friends-1@local/.test(next) && dtOf(next) === dtOf(ev1), dtOf(next) + " vs " + dtOf(ev1));

  const asym = stepBy(/Accept the asymmetry/);
  ok("a step with no day or rhythm gets no calendar button", !!asym && !calOf(asym), asym ? "has a button" : "step not found");

  const si = w.KPIs.findIndex((k) => k.id === "savings");
  if (si >= 0) w.openK(si);
  const mon = stepBy(/Monthly 15-min Money Date, 1st Sunday/);
  ok("the monthly 1st-Sunday step is shown", !!mon, "no step");
  ok("it shows Add to calendar under it", !!calOf(mon), "no button");
  if (si >= 0) {
    const mev = evOf(w.gmStepICS("savings", 5, w.KPIs[si].steps[5]), "securax-sys-savings-5@local");
    ok("its event repeats on the 1st Sunday", /RRULE:FREQ=MONTHLY;BYDAY=1SU/.test(mev), mev ? "no monthly rule" : "no event");
  }

  console.log("test129 recurring step calendar: " + P + " passed, " + F + " failed");
  if (F) { e.forEach((x) => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
