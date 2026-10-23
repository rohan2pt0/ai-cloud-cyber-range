// Scan a document: the Inbox has a camera button; a photo is read on THIS device (tesseract.js, stubbed here) and the
// text drops into the capture box for you to check and Add. A failed read never breaks capture by hand.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/index.html", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
setTimeout(() => {
  const w = d.window, doc = w.document;
  w.gmNavGo("inbox");
  const btn = doc.getElementById("ibScan");
  ok(btn && /Scan a document/.test(btn.textContent), "the Inbox shows a 'Scan a document' button");
  ok(typeof w.gmScan === "function" && typeof w.gmScanFile === "function" && typeof w.gmScanFill === "function",
     "the scan helpers are defined");

  // gmScanFill drops read text into the capture box, kept apart from anything already typed.
  doc.getElementById("ibText").value = "";
  w.gmScanFill("  Policy no 98765  \nRenew by March  ");
  ok(doc.getElementById("ibText").value === "Policy no 98765 Renew by March", "read text is collapsed to one line into the capture box");
  w.gmScanFill("Second line");
  ok(doc.getElementById("ibText").value.indexOf("Second line") > 0 && /Renew by March/.test(doc.getElementById("ibText").value),
     "a second scan appends, it does not overwrite");
  const before = doc.getElementById("ibText").value;
  w.gmScanFill("   ");
  ok(doc.getElementById("ibText").value === before, "an empty read changes nothing");

  // gmScanFile runs the (stubbed) on-device engine and fills the box.
  doc.getElementById("ibText").value = "";
  w.Tesseract = { recognize: function () { return Promise.resolve({ data: { text: "Aadhaar enrolment slip" } }); } };
  w.gmScanFile({ files: [{ name: "doc.jpg" }], value: "x" });
  setTimeout(() => {
    ok(doc.getElementById("ibText").value === "Aadhaar enrolment slip", "a scanned photo's text lands in the capture box");

    // A failed read must not throw and must leave capture by hand working.
    doc.getElementById("ibText").value = "typed by hand";
    delete w.Tesseract;
    // No ocr/tesseract.min.js loads in jsdom, so loadTesseract rejects; this must be caught.
    let threw = false;
    try { w.gmScanFile({ files: [{ name: "bad.jpg" }], value: "y" }); } catch (e) { threw = true; }
    ok(!threw, "a scan whose engine will not load does not throw");
    setTimeout(() => {
      ok(doc.getElementById("ibText").value === "typed by hand", "a failed scan leaves what you typed untouched");
      console.log("test34 scan a document: " + pass + " passed, " + fail + " failed");
      process.exit(fail ? 1 : 0);
    }, 300);
  }, 100);
}, 900);
