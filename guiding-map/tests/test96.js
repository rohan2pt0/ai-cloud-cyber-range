// test96: messages that arrive by themselves from the estate's SMS inbox are read once and cleared (doc 137; estate-sms-inbox).
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const now = Date.now();
const BOX = [
  { from: "VM-HDFCBK", t: "Rs 3,249 spent on HDFC Bank Swiggy Credit Card XX0202 at AMAZON on 03-11-2026", at: now - 3000 },
  { from: "AX-ICICIB", t: "ICICI Bank Credit Card XX0101 statement generated on 28-10-2026. Total amt due Rs 18,240", at: now - 2000 },
  { from: "VM-EPFOHO", t: "Dear member, your EPF balance as on 01-11-2026 is Rs. 2,34,567. UAN XXXXXXXX1234", at: now - 1000 }];
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://localhost/",
  beforeParse(w) { w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_intro_seen", "true"); w.localStorage.setItem("gm_sms_inbox", JSON.stringify(BOX)); } });
const w = dom.window;
setTimeout(() => {
  try {
    const sp = JSON.parse(w.localStorage.getItem("gm_spend") || "[]"), cards = JSON.parse(w.localStorage.getItem("gm_cards") || "[]"), a = JSON.parse(w.localStorage.getItem("gm_assets") || "{}");
    ok(sp.length === 1 && sp[0].a === 3249 && sp[0].c === "Amazon", "the forwarded spend was read with nothing typed: " + JSON.stringify(sp));
    ok(cards.some((c) => /ICICI/.test(c.name) && c.stmt === 28) && cards.some((c) => /HDFC Swiggy/.test(c.name)), "the cards appeared by themselves: " + JSON.stringify(cards));
    ok(a.epf && a.epf.v === 234567 && a.epf.at > 0, "the EPF balance was saved, dated");
    ok(JSON.parse(w.localStorage.getItem("gm_sms_inbox")).length === 0, "the inbox is cleared, so the texts leave the estate on the next sync");
    ok(+w.localStorage.getItem("gm_sms_done") === now - 1000, "the newest message read is remembered");
    w.localStorage.setItem("gm_sms_inbox", JSON.stringify(BOX.slice(0, 1)));
    ok(w.gmInboxDrain() === 0 && JSON.parse(w.localStorage.getItem("gm_spend")).length === 1, "a message already read is never counted twice");
  } catch (e) { fail++; console.log("FAIL threw " + e.stack); }
  console.log("test96 messages that arrive by themselves: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1800);
