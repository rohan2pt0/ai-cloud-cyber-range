// v67: Life OS deadlines. Every date the person sets lands in one registry, the Deadlines tab shows the vital few with a
// calm countdown, and one tap puts all of it in the calendar on the dated-items contract (stable UID, SEQUENCE, CANCELLED).
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const iso = d => d.toISOString().slice(0, 10), plus = n => { const d = new Date(); d.setDate(d.getDate() + n); return iso(d); };
const career = { cfg: { noticeStart: plus(1), noticeMonths: 3 }, done: {} };
const inbox = [
  { id: "fakeRenew1", t: "Renew health insurance (fake-policy) before 01 Jan 2099", next: "Compare and renew it", kind: "issue", area: "Insurance", due: plus(20), from: "lifedocs" },
  { id: "fakePlain", t: "Fake call the plumber", kind: "action", due: plus(2), from: "capture" },
  { id: "fakeLate", t: "Fake overdue task", kind: "action", due: plus(-2), from: "capture" }
];
const sov = {
  commits: [{ id: "cFake1", goal: "Fake signed goal", stake: "100", ref: "FakeRef", dl: plus(5), status: "live" }],
  okrs: [{ o: "Fake objective", at: Date.now(), krs: [{ t: "Fake KR from 1 to 2 by date", b: 1, g: 2, c: 1, v: 0, due: plus(8), dueMs: Date.parse(plus(8) + "T00:00:00") }] }]
};
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovS", JSON.stringify(sov)); w.localStorage.setItem("gm_career", JSON.stringify(career));
    w.localStorage.setItem("gm_inbox", JSON.stringify(inbox));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.URL.createObjectURL = () => "blob:x"; } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  const items = w.datedItems();

  const commit = items.filter(x => x.uid === "commit-cFake1")[0];
  ok("a signed commitment with a deadline is in datedItems() under deadlines", !!commit && commit.group === "deadlines" && /Fake signed goal/.test(commit.name));
  ok("career items keep their uid", !!items.filter(x => x.uid === "car-offer-paper" && x.group === "career").length);
  ok("renewals items keep their uid", !!items.filter(x => x.uid === "ib-fakeRenew1" && x.group === "renewals").length);
  ok("a plain Inbox item with a due date appears once", items.filter(x => x.uid === "ib-fakePlain").length === 1 && items.filter(x => x.uid === "ib-fakePlain")[0].group === "deadlines");
  ok("a quarterly goal with a due date is in the deadlines group", items.filter(x => x.group === "deadlines" && /^okr-/.test(x.uid)).length === 1);
  ok("no uid is duplicated across groups", (() => { const seen = {}; return items.every(x => !seen[x.uid] && (seen[x.uid] = 1)); })());

  w.goTab("deadlines");
  let s = sec().querySelector(".section.active");
  ok("the Deadlines tab renders", !!s);
  ok("it opens with a hero", !!s.querySelector(".gm-hero"));
  ok("the hero shows the nearest open deadline", /Fake overdue task/.test(s.textContent) && /days/.test(s.textContent), s.textContent.slice(0, 180));
  ok("an overdue item shows the calm late line", /Late\. Pick a new date or let it go\./.test(s.textContent));
  ok("the overdue row uses amber, never red", !/var\(--red\)|#f87171|#991b1b/i.test(s.innerHTML));
  ok("one primary calendar button is offered", /Put all of these in my calendar/.test(s.textContent));
  ok("the import line explains the same calendar", /Import into the same calendar each time; changes update the same events\./.test(s.textContent));

  const ics = w.gmCalendarDatedICS();
  ok("the calendar file contains the commitment's UID", /UID:securax-gm-commit-cFake1@local/.test(ics));

  w.goTab("commit");
  s = sec().querySelector(".section.active");
  const dl = d.getElementById("c_dl");
  ok("the Commit deadline input has a non-empty default", !!dl && /^\d{4}-\d{2}-\d{2}$/.test(dl.value));
  ok("the deadline label is plain words", /Deadline \(tap to change\)/.test(s.textContent));
  ok("the 78% statistic is gone", !/78%/.test(s.textContent));

  d.getElementById("c_goal").value = "Fake new goal";
  d.getElementById("c_dl").value = plus(12);
  w.addCommit();
  const saved = JSON.parse(w.localStorage.getItem("sovS")).commits.filter(x => x.goal === "Fake new goal")[0];
  ok("a new commitment gets a stable id", !!saved && /^c\d+$/.test(saved.id));
  ok("the new commitment lands in datedItems()", !!saved && w.datedItems().some(x => x.uid === "commit-" + saved.id && x.group === "deadlines"));

  console.log("test67 deadlines: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
