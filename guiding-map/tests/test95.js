// test95: where the money went, from many messages at once; zero typing (owner 2026-11-14; threat model lifeos-share-in).
const fs = require("fs"), path = require("path"); const { JSDOM } = require("jsdom");
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL " + m); } };
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://localhost/",
  beforeParse(w) { w.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {} }); w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); w.localStorage.setItem("gm_intro_seen", "true"); } });
const w = dom.window;
setTimeout(() => {
  try {
    const p = (t) => w.gmParseSms(t);
    const a = p("Rs 3,249 spent on HDFC Bank Swiggy Credit Card XX0202 at AMAZON on 03-11-2026");
    ok(a.bank === "HDFC" && a.product === "Swiggy" && a.l4 === "0202" && a.amount === 3249 && a.merchant === "AMAZON" && a.cat === "Amazon" && a.debit, "a card spend: bank, card, shop, category " + JSON.stringify(a));
    const b = p("Rs 640 spent on ICICI Bank Credit Card XX0101 at SWIGGY on 01-11-2026");
    ok(b.product === "" && b.cat === "Food delivery", "the shop never renames the card " + JSON.stringify(b));
    const c = p("SBI Card Flipkart XX0303 bill generated on 10-11-2026, total amount due Rs 6,400");
    ok(c.bill && !c.debit && c.date.getDate() === 10 && c.product === "Flipkart", "a bill gives the statement day, and is not a spend");
    ok(p("Rs 500 credited to your account XX0101 as refund").debit === false, "a refund is not a spend");
    ok(p("Late payment fee of Rs 750 charged on HDFC Bank Credit Card XX0202").fee, "a late fee is noticed");
    // the sample case study: cards appear by themselves, nothing is saved
    const r = w.gmSpendSample();
    ok(r.cardList.length === 4 && r.cardList.every((x) => x.stmt > 0), "four cards found with their statement days: " + r.cardList.map((x) => x.name + "@" + x.stmt).join(", "));
    ok(!w.localStorage.getItem("gm_spend") && !w.localStorage.getItem("gm_cards"), "the sample saves nothing");
    const ins = w.gmSpendInsights(r.list, r.cardList, r.fees);
    ok(ins.vital.length < ins.cats.length, "80/20: fewer categories than all make 80% of spending");
    ok(/autopay/i.test(ins.actions[0].t), "a late fee makes autopay the one change worth most");
    ok(ins.missed > 400 && ins.actions.some((x) => /Amazon Pay ICICI/.test(x.t)), "money left on the table is found: " + Math.round(ins.missed));
    ok(ins.actions.some((x) => /subscriptions/i.test(x.t)) && ins.actions.some((x) => /Food delivery/.test(x.t)), "subscriptions and food delivery are named");
    // a real read: saved, deduplicated, the card guide fills itself, nothing typed
    const text = "Rs 1,299 spent on Amazon Pay ICICI Bank Credit Card XX0101 at AMAZON on 02-11-2026\n\nICICI Bank Credit Card XX0101 statement generated on 28-10-2026. Total amt due Rs 18,240";
    const r1 = w.gmSpendRead(text), r2 = w.gmSpendRead(text);
    ok(r1.spends === 1 && r2.spends === 0, "the same message twice is counted once");
    const cards = JSON.parse(w.localStorage.getItem("gm_cards"));
    ok(cards.length === 1 && /Amazon Pay/.test(cards[0].name) && cards[0].stmt === 28, "the card guide filled itself: " + JSON.stringify(cards));
    ok(Object.keys(cards[0]).every((k) => ["id", "key", "name", "stmt"].indexOf(k) > -1) && !/\d{5,}/.test(JSON.stringify(cards)), "only a name with the last four digits and the statement day are kept");
    ok(/Where your money went/.test(w.gmSpendHTML()), "the Money view shows where the money went");
    // a shared batch goes to the spend reader by itself
    w.gmReadOpen("Rs 520 spent on ICICI Bank Credit Card XX0101 at SWIGGY on 02-11-2026\n\nRs 455 spent on ICICI Bank Credit Card XX0101 at SWIGGY on 06-11-2026");
    ok(JSON.parse(w.localStorage.getItem("gm_spend")).length === 3, "a shared batch of messages is read as spends");
  } catch (e) { fail++; console.log("FAIL threw " + e.stack); }
  console.log("test95 where the money went: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 1500);
