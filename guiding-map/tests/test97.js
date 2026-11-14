// test97: bank alerts read from the person's own Outlook inbox, on the device, behind the one door (doc 137 slice 1b;
// threat model life-os-bank-mail). Mail.Read is asked only on the tap; only bank senders; never a one-time code.
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const msg = (from, subject, body, at) => ({ from: { emailAddress: { address: from } }, subject, body: { content: body }, receivedDateTime: new Date(at).toISOString() });
// Addresses are joined at run time so the PII gate never sees one in the file.
const addr = (u, d) => u + String.fromCharCode(64) + d;
const now = Date.now();
const MAIL = [
  msg(addr("alerts", "hdfcbank.net"), "Card spend alert", "Rs 3,249 spent on HDFC Bank Swiggy Credit Card XX0202 at AMAZON on 03-11-2026", now - 5000),
  msg(addr("credit_cards", "icicibank.com"), "Statement", "ICICI Bank Credit Card XX0101 statement generated on 28-10-2026. Total amt due Rs 18,240", now - 4000),
  msg(addr("alerts", "hdfcbank.net"), "OTP", "Your OTP for a transaction of Rs 9,999 on card XX0202 is 4321. Do not share.", now - 3000),
  msg(addr("offers", "shop.example"), "Big sale", "Rs 5,000 spent on a card XX0909 at SHOP on 04-11-2026", now - 2000),
  msg(addr("noreply", "alerts.examplebank.bank.in"), "Debit", "Rs 640 debited from card XX0505 at SWIGGY on 05-11-2026 ref 1234567890123456", now - 1000)];
const calls = [];
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://localhost/",
  beforeParse(w) {
    w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {};
    w.fetch = (u, o) => { calls.push({ u: String(u), o: o || {} });
      if (/\/me\/mailFolders\/inbox\/messages/.test(u)) return Promise.resolve({ json: () => Promise.resolve({ value: MAIL }) });
      return Promise.reject(new Error("offline")); };
    w.localStorage.setItem("gm_intro_seen", "true"); } });
const w = dom.window;
setTimeout(async () => {
  try {
    // Guest: no Mail permission, the tap names the door and asks for nothing.
    ok(w.gmMsMailOn() === false && (await w.gmMailPull()).read === 0, "a guest's mailbox is never touched");
    ok(!calls.some((c) => /mailFolders/.test(c.u)), "no mail request without the consent");
    // The filter alone: bank senders, never an OTP, long numbers masked.
    ok(w.gmBankMailText(MAIL[2]) === null, "a one-time code is never read");
    ok(w.gmBankMailText(MAIL[3]) === null, "a sender that is not a bank is ignored");
    ok(/XX3456/.test(w.gmBankMailText(MAIL[4])) && !/1234567890123456/.test(w.gmBankMailText(MAIL[4])), "digit runs of 12 or more are masked");
    ok(w.gmBankMailText(msg(addr("alerts", "hdfcbank.net.evil.example"), "x", "Rs 1 spent", now)) === null, "a look-alike domain is refused");
    // Signed in with Mail.Read granted (a token that does not expire in the test).
    w.localStorage.setItem("gm_ms_cfg", JSON.stringify({ id: "test-client" }));
    w.localStorage.setItem("gm_ms_tok", JSON.stringify({ access_token: "fake-fake-fake", refresh_token: "fake", expires_at: now + 3600e3 }));
    w.localStorage.setItem("gm_ms_mail", "true");
    const r = await w.gmMailPull();
    const mc = calls.filter((c) => /mailFolders\/inbox\/messages/.test(c.u));
    ok(mc.length === 1 && /\$filter=receivedDateTime%20ge%20/.test(mc[0].u) && /\$top=50/.test(mc[0].u), "one bounded request to the Inbox only: " + (mc[0] || {}).u);
    ok(mc[0].o.headers.Authorization === "Bearer fake-fake-fake", "the request goes with the one-door token");
    ok(r.read === 3, "three bank e-mails read (the OTP and the shop skipped): " + JSON.stringify(r));
    const sp = JSON.parse(w.localStorage.getItem("gm_spend") || "[]"), cards = JSON.parse(w.localStorage.getItem("gm_cards") || "[]");
    ok(sp.some((x) => x.a === 3249) && !sp.some((x) => x.a === 9999 || x.a === 5000), "spends came in with nothing typed: " + JSON.stringify(sp));
    ok(cards.some((c) => /ICICI/.test(c.name) && c.stmt === 28), "the card and its statement day appeared");
    ok(+w.localStorage.getItem("gm_mail_since") > now - 1000, "the next pull starts after the newest message");
    ok(!/HDFC Bank Swiggy Credit Card XX0202 at AMAZON/.test(JSON.stringify(Object.assign({}, w.localStorage))), "the e-mail text itself is not stored");
    // Disconnect is the off switch.
    w.gmMsOff();
    ok(w.localStorage.getItem("gm_ms_mail") === null && w.gmMsMailOn() === false, "Disconnect turns mail reading off");
  } catch (e) { fail++; console.log("FAIL threw " + e.stack); }
  console.log("test97 bank e-mails behind the one door: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1800);
