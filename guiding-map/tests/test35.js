// The lens: understand what you captured on THIS device. It classes the text (policy, bill, appointment, id),
// pulls out the amount and the due date, flags scams in plain words, LEARNS from your taps, and lets future
// senses plug in through gmLensRegister. All of this runs on text, so it is fully testable without a camera.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/index.html", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
setTimeout(() => {
  const w = d.window, doc = w.document;

  // 1. Classification (semantic type → an Inbox kind and an area).
  ok(w.gmLensClassify("Max term plan premium due, nominee not set").type === "policy", "an insurance policy is recognised");
  ok(w.gmLensClassify("Electricity bill, amount due this month").type === "bill", "a bill is recognised");
  ok(w.gmLensClassify("Doctor appointment booked for next week").type === "appointment", "an appointment is recognised");
  ok(w.gmLensClassify("This is my Aadhaar card, identity proof").kind === "note", "an ID is kept as a note");

  // 2. Entities pulled out of the text.
  ok(w.gmLensAmount("premium is ₹14,999 this year") === 14999, "an amount in rupees is read");
  ok(w.gmLensAmount("no money here") === null, "no amount is null, not a guess");
  ok(w.gmLensDate("due on 12 Nov 2026") === "2026-11-12", "a '12 Nov 2026' date is read");
  ok(w.gmLensDate("pay by 15/11/2026 please") === "2026-11-15", "a '15/11/2026' date is read (day first, India)");

  // 3. The fraud scanner, with plain-words reasons.
  const scam = w.gmRiskScan("Dear customer your account will be blocked today, update KYC immediately, click http://bit.ly/x and share OTP to avoid suspension");
  ok(scam.level === "danger", "a classic scam SMS is flagged danger");
  ok(scam.reasons.some((r) => /OTP/.test(r)) && scam.reasons.some((r) => /hurry/.test(r)), "it says WHY in plain words (OTP, urgency)");
  ok(w.gmRiskScan("Electricity bill ₹1240 due 15 Nov 2026, pay at the board portal").level === "safe", "a genuine bill is safe");
  ok(w.gmRiskScan("Payee testuser@fakeupi requests ₹499, approve to pay").level !== "safe", "a UPI collect-request sent TO you is not called safe");

  // 4. The whole read: a scam becomes an 'issue', a bill keeps its date.
  const r1 = w.gmLensRead("your account is blocked, share OTP now, http://bit.ly/x, urgent");
  ok(r1.kind === "issue" && r1.risk.level === "danger", "a scam read becomes an issue to deal with, flagged danger");
  const r2 = w.gmLensRead("Max term plan premium ₹14,999 due on 12 Nov 2026");
  ok(r2.type === "policy" && r2.fields.amount === 14999 && r2.suggest.due === "2026-11-12", "a policy read carries its amount and due date");
  ok(w.gmLensRead("") === null, "empty text reads as nothing");

  // 5. It LEARNS, on this device: three taps teach it a scam it did not know.
  w.localStorage.removeItem("gm_lens_model");
  ok(w.gmRiskScan("join the crypto doubling scheme for guaranteed returns").level === "safe", "an unknown pitch is safe at first");
  ["crypto doubling scheme guaranteed returns", "crypto doubling guaranteed returns", "doubling scheme returns crypto guaranteed"].forEach((t) => w.gmLensLearnRisk(t, true));
  ok(w.gmRiskScan("want in on the crypto doubling scheme returns?").level !== "safe", "after you flag it three times, the lens catches the same scam");
  ok(w.gmRiskScan("Electricity bill ₹1240 due 15 Nov 2026").level === "safe", "learning one scam does not make everything look risky");

  // 6. The rails: a future sense plugs in with the same shape (gmLensRegister) and handles its own text.
  const before = w.gmLensRegister({ id: "lab", name: "Lab", test: (t) => /quantum/i.test(t) ? 0.9 : 0, read: () => ({ type: "note", kind: "note", area: "Lab" }) });
  ok(before >= 1, "a lens can register");
  ok(w.gmLensRead("quantum experiment notes for the week").area === "Lab", "a registered lens handles its own text, no engine change (plug-and-play)");
  ok(w.gmLensRead("Electricity bill due 15 Nov 2026").area !== "Lab", "a lens that does not match stays out of the way");

  // 7. In the Inbox: a scan shows what it understood and a red banner for a scam.
  w.gmNavGo("inbox");
  w.gmShowRead("your account is blocked, share OTP now, http://bit.ly/x, urgent");
  const box = doc.getElementById("ibRead");
  ok(/scam/i.test(box.textContent) && box.querySelector(".ibread-risk.danger"), "a scam scan shows a red danger banner with reasons");
  ok(doc.getElementById("ibKind").value === "issue", "a risky item is pre-set as an issue");
  w.gmReadScam();
  ok(/Flagged as a scam/.test(box.textContent), "'Yes, it is a scam' teaches the device and warns plainly");

  // 8. A scanned bill arrives already dated — no typing, less friction (the SixthSense point).
  doc.getElementById("ibText").value = "Electricity bill ₹1240 due 15 Nov 2026";
  w.gmShowRead(doc.getElementById("ibText").value);
  ok(/bill/.test(box.textContent) && /15 Nov|2026-11-15/.test(box.textContent), "a bill scan shows its kind and due date");
  w.gmInboxCapture();
  const top = JSON.parse(w.localStorage.getItem("gm_inbox"))[0];
  ok(top.due === "2026-11-15" && top.from === "lens", "the captured bill arrives with its date filled in, straight from the lens");

  console.log("test35 the lens: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 900);
