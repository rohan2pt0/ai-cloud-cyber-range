// test94: which card when, and numbers from a shared message (owner 2026-11-14; threat model lifeos-share-in).
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://localhost/",
  beforeParse(w) { w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } });
const w = dom.window;
setTimeout(() => {
  try {
    // 1. the card guide refuses anything that looks like a card number (12+ digits), and keeps only name and statement day
    ok(w.gmCardsAdd("My card 1234 5678 9012, 13") === 0 && !(JSON.parse(w.localStorage.getItem("gm_cards") || "[]").length), "a card number is refused, nothing stored");
    ok(w.gmCardsAdd("HDFC Swiggy, 13\nICICI Amazon Pay, 28\nIDFC FIRST LIC Select, 19") === 3, "three cards from three lines");
    const kept = JSON.parse(w.localStorage.getItem("gm_cards"));
    ok(kept.every((c) => Object.keys(c).sort().join() === "id,name,stmt"), "only id, name and statement day are kept");
    // 2. the big-spend card: the statement that has just passed gives the most days before paying
    const best = w.gmCardBest(new Date(2026, 10, 14, 12));
    ok(best && /Swiggy/.test(best.card.name) && best.days === 47, "on 14 Nov the card whose statement was on the 13th wins, 47 days: " + JSON.stringify(best));
    // 3. the Money view opens with the guide and the category picks
    const h = w.gmCardsHTML();
    ok(/Big spend today/.test(h) && /Amazon<\/b>: ICICI Amazon Pay/.test(h) && /LIC premiums<\/b>: IDFC FIRST LIC Select/.test(h), "category picks shown");
    ok(/autopay/i.test(h) && /Never a card number/.test(h), "the habits and the privacy line are shown");
    // 4. the message reader on realistic formats (fake numbers)
    const r = (t) => w.gmReadMessage(t);
    const epf = r("Dear member, your EPF balance as on 01-11-2026 is Rs. 2,34,567. UAN XXXXXXXX1234");
    ok(epf.kind === "epf" && epf.amount === 234567, "EPFO SMS: " + JSON.stringify(epf));
    const bank = r("A/c XX1234 credited with Rs 5,000. Avl Bal Rs 1,23,456.78 on 14-11");
    ok(bank.kind === "bank" && bank.amount === 123456.78, "bank SMS picks the balance, not the credit: " + JSON.stringify(bank));
    const due = r("Total amt due Rs 12,345 for card XX9876, due date 03-Dec");
    ok(due.kind === "due" && due.amount === 12345, "card bill SMS: " + JSON.stringify(due));
    const nps = r("PRAN XXXX5678: Total Holding Value Rs 5,67,890 as on 13-11-2026");
    ok(nps.kind === "nps" && nps.amount === 567890, "NPS: " + JSON.stringify(nps));
    ok(r("hello there").amount === null, "no amount, nothing found");
    // 5. shared text is never markup
    w.gmReadOpen("<img src=x onerror=window.__x=1> Avl Bal Rs 100");
    ok(!w.document.querySelector("#gmOverlay img") && w.__x === undefined, "shared markup never runs or renders");
    // 6. one tap saves, dated, and net worth follows the statements
    w.gmAssetSave("epf", 234567);
    const a = JSON.parse(w.localStorage.getItem("gm_assets"));
    ok(a.epf.v === 234567 && a.epf.at > 0, "saved with its date");
    ok(w.S.intData.networth === 2.35, "net worth comes from the statements: " + w.S.intData.networth);
    ok(/updated today/.test(w.gmReaderHTML()), "the reader shows when each number was updated");
    // 7. the share link is answered on the device, never sent to the host
    const sw = fs.readFileSync(path.join(__dirname, "..", "sw.js"), "utf8"), man = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "manifest.json"), "utf8"));
    ok(man.share_target && man.share_target.action === "./share-in", "the app is a share target");
    ok(sw.indexOf('endsWith("/share-in")') > -1 && sw.indexOf('endsWith("/share-in")') < sw.indexOf("fetch(new Request(req"), "the service worker answers the share link before any network fetch");
    ok(/slice\(0, 20000\)/.test(sw), "shared text is capped");
  } catch (e) { fail++; console.log("FAIL threw " + e.stack); }
  console.log("test94 cards and shared messages: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
