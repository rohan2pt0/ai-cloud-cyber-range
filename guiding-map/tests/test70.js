// v70: the Ask tab puts the question first and folds the rare setup away by how often it is used. The question box
// comes before the status line and the two folds; the on-device tools live under one "More tools" fold; and the
// connection (links, address, key) is closed under "Connection (set once)", never shown as text outside it.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const prof = { name: "Fake", dob: "1990-05-15", country: "India", city: "", cur: "INR", gross: 300000, net: 200000, exp: 90000, sav: 400000,
  nw: 2500000, rent1: 0, rent2: 0, pname: "FakePartner", pdob: "1992-01-10", psal: 50000, parents: false,
  kids: [{ name: "FakeKid", dob: "2022-03-01" }], loans: [{ type: "Home Loan", remaining: 1000000, rate: 8.5, emi: 20000, tenure: 120 }],
  ret: 50, tsav: 20, dream: "UAE", goal: "Financial independence", example: false };
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { w.localStorage.setItem("sovP", JSON.stringify(prof));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });
setTimeout(() => {
  const w = dom.window, d = w.document, sec = () => d.getElementById("sections");
  w.goTab("ask");
  const q = d.getElementById("askQ"), status = d.getElementById("askStatus");
  const details = [...sec().querySelectorAll("details")];
  const summaryText = el => (el && el.querySelector("summary") ? el.querySelector("summary").textContent : "");
  const more = details.find(x => /More tools/.test(summaryText(x)));
  const conn = details.find(x => /Connection/.test(summaryText(x)));
  const before = (a, b) => !!(a && b && (a.compareDocumentPosition(b) & w.Node.DOCUMENT_POSITION_FOLLOWING));

  ok("Ask has a question box", !!q);
  ok("the question box comes before the status line", before(q, status));
  ok("the question box comes before the More tools fold", before(q, more));
  ok("the question box comes before the Connection fold", before(q, conn));

  const gw = d.getElementById("askGwIn"), key = d.getElementById("askKeyIn");
  ok("the Connection fold names itself in its summary", /Connection/.test(summaryText(conn)), summaryText(conn));
  ok("the Connection fold is closed", !!conn && conn.open === false);
  ok("the gateway address is inside the closed Connection fold", !!gw && !!conn && conn.contains(gw) && conn.open === false);
  ok("the gateway key is inside the closed Connection fold", !!key && !!conn && conn.contains(key) && conn.open === false);

  const gq = d.getElementById("guardQ"), ii = d.getElementById("intelItems");
  ok("the footprint guard is inside the More tools fold", !!gq && !!more && more.contains(gq));
  ok("the Intel box is inside the More tools fold", !!ii && !!more && more.contains(ii));

  // Text a person can see: skip the inside of every closed details.
  const visible = root => {
    let out = "";
    const walk = node => {
      for (const c of node.childNodes) {
        if (c.nodeType === 3) { out += c.nodeValue; continue; }
        if (c.nodeType !== 1) continue;
        if (c.tagName === "DETAILS" && !c.open) continue;
        walk(c);
      }
    };
    walk(root);
    return out;
  };
  const seen = visible(sec());
  ok("no localhost address is visible outside a closed fold", !/localhost/i.test(seen), (seen.match(/[^\n]*localhost[^\n]*/i) || [""])[0]);
  ok("no :8080 port is visible outside a closed fold", !/:8080/.test(seen), (seen.match(/[^\n]*:8080[^\n]*/) || [""])[0]);

  ["askQ", "askOut", "askFb", "askStatus", "guardQ", "guardOut", "intelItems", "intelVocab", "intelOut", "askGwIn", "askKeyIn"].forEach(id => {
    ok("id " + id + " still exists once", sec().querySelectorAll("#" + id).length === 1, String(sec().querySelectorAll("#" + id).length));
  });

  console.log("test70 Ask puts the question first and folds setup away: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1500);
