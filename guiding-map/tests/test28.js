// The Inbox makes notes into a system: capture one line, decide it (an action with a next step and a date, a note, or delete),
// run a review whose findings become dated actions, and the tab bar uses plain words, not emoji.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/index.html", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
setTimeout(() => {
  const w = d.window, doc = w.document;
  const inbox = () => JSON.parse(w.localStorage.getItem("gm_inbox") || "[]");
  ok(w.TABS.some((t) => t[0] === "inbox" && t[1] === "Inbox"), "an Inbox tab exists");
  ok(w.TABS.every((t) => /^[A-Za-z0-9]/.test(t[1])), "every tab label starts with a word, not an emoji");
  w.gmNavGo("inbox");
  ok(doc.getElementById("ibText"), "the Inbox opens with a capture line");
  ok(doc.getElementById("ibText").closest(".section").classList.contains("active"), "its section is .active (the app hides any other section)");
  doc.getElementById("ibText").value = "Renew the car insurance";
  w.gmInboxCapture();
  const it = inbox()[0];
  ok(it && it.t === "Renew the car insurance" && !it.due, "a captured line waits to be decided");
  ok(w.gmInboxStats().decide === 1, "the Today nudge counts it as 'to decide'");
  doc.getElementById("ibNext_" + it.id).value = "Call the agent for two quotes";
  doc.getElementById("ibDue_" + it.id).value = "2026-01-05";
  w.gmInboxDecide(it.id, "action");
  const a = inbox()[0];
  ok(a.next === "Call the agent for two quotes" && a.due === "2026-01-05", "deciding it gives a next physical step and a date");
  ok(w.gmInboxStats().due === 1 && /late/.test(doc.getElementById("sections").textContent), "a past date shows as late");
  w.gmInboxDone(a.id);
  ok(inbox()[0].done, "done is recorded");
  const n = w.gmInboxAdd("Idea: a family offsite in March", "idea");
  w.gmInboxDecide(n.id, "note");
  ok(inbox().find((x) => x.id === n.id).kind === "note", "an idea can be kept as a note, with no date");
  const x = w.gmInboxAdd("junk", "note");
  w.gmInboxDecide(x.id, "delete");
  ok(!inbox().find((y) => y.id === x.id), "delete removes it");
  w.gmReviewOpen("redteam");
  ok(doc.getElementById("rv_redteam_0"), "a review shows its steps one by one");
  doc.getElementById("rv_redteam_2").value = "Garage side door lock is broken";
  doc.getElementById("rv_redteam_3").value = "2FA missing on the old email";
  const made = w.gmReviewFindings("redteam");
  const issues = inbox().filter((y) => y.from === "review:redteam");
  ok(made === 2 && issues.length === 2 && issues.every((y) => y.kind === "issue" && y.due), "each finding of the review became a dated action; empty steps made none");
  ok(issues[0].area === "Red-Team Your Life", "each action names the review it came from");
  console.log("test28 inbox and reviews: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 900);
