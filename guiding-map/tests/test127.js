// v127: a one-off step that starts with Open, Buy, Book, Set up or Sign up gets "Remind me Saturday" under it
// (queue step-doers, slice 2). One tap puts the step in the Inbox with a due date on the coming Saturday, the button
// then says so, and a second tap adds nothing. A list or note step keeps only its own doer, never a reminder.
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
  const inbox = () => { try { return JSON.parse(w.localStorage.getItem("gm_inbox") || "[]") || []; } catch (x) { return []; } };
  const stepBy = (re) => Array.prototype.slice.call(d.querySelectorAll("#m_sys .step")).filter((s) => re.test(s.textContent))[0];
  const doerOf = (step) => (step && step.nextElementSibling && /(^|\s)step-do(\s|$)/.test(step.nextElementSibling.className)) ? step.nextElementSibling : null;
  const reminderOf = (step) => { const b = doerOf(step); return b ? (b.querySelector('[data-stepdo-remind]') || Array.prototype.slice.call(b.querySelectorAll("button")).filter((x) => /Remind me Saturday/i.test(x.textContent))[0]) : null; };
  const sat = () => { const x = new Date(); let add = ((6 - x.getDay()) + 7) % 7; if (add === 0) add = 7; x.setDate(x.getDate() + add);
    return x.getFullYear() + "-" + ("0" + (x.getMonth() + 1)).slice(-2) + "-" + ("0" + x.getDate()).slice(-2); };

  const si = w.KPIs.findIndex((k) => k.id === "savings");
  ok("the savings system exists", si >= 0, "index " + si);
  if (si >= 0) w.openK(si);

  const open = stepBy(/Open a separate online savings account/);
  ok("opening it shows the Open step", !!open, "no step");
  const first = reminderOf(open);
  ok("the Open step shows Remind me Saturday under it", !!first && /Remind me Saturday/i.test(first.textContent), first ? first.textContent : (open ? "no reminder button" : "no step"));
  const due = sat(), before = inbox().length;
  if (reminderOf(open)) reminderOf(open).click();
  const after = inbox();
  ok("tapping it adds one Inbox item with the step's text", after.length === before + 1
    && !!after[0] && after[0].t === open.querySelector(".step-t").textContent.trim(), JSON.stringify(after[0] || null));
  ok("the item is an action due on the coming Saturday", !!after[0] && after[0].kind === "action" && after[0].due === due,
    after[0] ? after[0].kind + " " + after[0].due + " (want action " + due + ")" : "no item");
  const btn = reminderOf(open);
  ok("the button then reads Reminder set for that date", !!btn && /Reminder set for/.test(btn.textContent)
    && btn.textContent.indexOf(new Date(due + "T00:00:00").toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })) >= 0,
    btn ? btn.textContent : "no button");
  if (btn) btn.click();
  ok("a second tap adds nothing", inbox().length === after.length, inbox().length + " items");

  const fi = w.KPIs.findIndex((k) => k.id === "friends");
  if (fi >= 0) w.openK(fi);
  const names = stepBy(/Write the 5 names/), call = stepBy(/After each call/);
  ok("a list step gets no reminder button", !!names && !reminderOf(names), names ? "has a reminder" : "step not found");
  ok("a note step gets no reminder button", !!call && !reminderOf(call), call ? "has a reminder" : "step not found");

  console.log("test127 step reminders: " + P + " passed, " + F + " failed");
  if (F) { e.forEach((x) => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1500);
