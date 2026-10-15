// Ask panel: advisor chips switch in place (typed question kept), answers render as escaped Markdown.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/" });
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
setTimeout(() => {
  const w = d.window, doc = w.document;
  const md = w.gmMdLite("**Key:**\n* **a** b\n* <img src=x onerror=alert(1)>\n\n1. one\n# H");
  ok(md.indexOf("<b>Key:</b>") >= 0, "bold renders");
  ok(md.indexOf("<ul><li>") >= 0 && md.indexOf("<ol><li>one") >= 0, "lists render");
  ok(md.indexOf("<img") < 0 && md.indexOf("&lt;img") >= 0, "model HTML is escaped");
  ok(md.indexOf("<h4>H</h4>") >= 0, "heading renders");
  // Build a chip row like the Ask panel's, then switch advisor.
  const box = doc.createElement("div");
  box.innerHTML = '<div class="chips"><button class="chip on" data-k="general"></button><button class="chip" data-k="cfo"></button></div><textarea id="askQ">half typed</textarea>';
  doc.body.appendChild(box);
  w.gmAskSet("cfo");
  ok(doc.querySelector('[data-k="cfo"]').classList.contains("on"), "chosen chip highlighted");
  ok(!doc.querySelector('[data-k="general"]').classList.contains("on"), "previous chip cleared");
  ok(doc.getElementById("askQ").value === "half typed", "typed question kept");
  console.log("test21 ask panel: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 800);
