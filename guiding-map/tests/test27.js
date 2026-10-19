// Home-screen shortcuts and the spreadsheet export: a long-press on the app icon ticks one of the daily three without opening
// anything else (and never unticks), and Ops exports one row per day that opens in Excel.
const { JSDOM } = require("jsdom");
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "manifest.json"), "utf8"));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
ok((manifest.shortcuts || []).map((s) => s.url).join(" ") === "./index.html?do=ex ./index.html?do=mf ./index.html?do=fm ./index.html?do=note", "the manifest offers Move, Mind, Family and Note");
const d = new JSDOM(html, { runScripts: "dangerously", url: "https://hub.securax.localhost/index.html?do=mf", pretendToBeVisual: true,
  beforeParse(w) { w.scrollTo = () => {}; w.URL.createObjectURL = () => "blob:x"; } });
setTimeout(() => {
  const w = d.window;
  ok(w.todayChecks().indexOf("mf") >= 0, "the Mind shortcut ticked Mind for today");
  ok(!/do=/.test(w.location.href), "the shortcut is dropped from the address, so a reload does not repeat it");
  w.gmShortcut("mf");
  ok(w.todayChecks().indexOf("mf") >= 0, "a second tap does not untick it");
  ok(w.gmShortcut("nope") === false, "an unknown shortcut does nothing");
  const k = w.dKey(new Date()), notes = {}; notes[k] = 'Walked, said "no" to one meeting';
  w.localStorage.setItem("gm_notes", JSON.stringify(notes));
  const en = {}; en[k] = 4; w.localStorage.setItem("gm_energy", JSON.stringify(en));
  const csv = w.gmCsv(30).trim().split("\r\n");
  ok(csv[0] === "date,move,mind,family,energy,note", "the header names each column");
  ok(csv[1] === k + ',0,1,0,4,"Walked, said ""no"" to one meeting"', "today's row: ticks, energy and the note, safely quoted");
  ok(csv.length === 2, "days with nothing recorded are left out");
  console.log("test27 shortcuts and CSV: " + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}, 900);
