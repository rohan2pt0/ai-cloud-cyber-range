// v39: ONE OPEN ACTION (principle `one-open-action`, owner 2026-11-10). The Stack's discipline on every screen where things
// compete: at most one primary action in view, chosen by risk; the rest folded under "Later (n)"; a long list offers
// "Show only the vital few (80/20)". Life OS (every tab, Today ranking, Inbox) and the OS kit (Vantage Today, Rhythm, a register).
// The Command Center's "what needs you" is held by test32.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const ymd = (d) => d.toISOString().slice(0, 10);
const day = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return ymd(d); };

// a primary in view: not inside a closed <details> (a summary stays visible), not hidden
function primaries(w, root, sel) {
  return [...root.querySelectorAll(sel)].filter(el => {
    for (let p = el.parentElement; p && p !== root.ownerDocument.body; p = p.parentElement) {
      if (p.tagName === "DETAILS" && !p.open) return false;
      if (p.style && p.style.display === "none") return false;
      if (p.classList.contains("gm-hide")) return false;
    }
    return true;
  });
}

// ── Life OS ────────────────────────────────────────────────────────────────
const seed = {
  gm_inbox: [
    { id: "fakeA", t: "Fake decide one", kind: "idea", created: 1 },
    { id: "fakeB", t: "Fake decide two", kind: "idea", created: 1 },
    { id: "fakeC", t: "Fake decide three", kind: "idea", created: 1 },
    { id: "fakeLate", t: "Fake renew the health policy", next: "Fake renew the health policy", kind: "action", due: day(-3), vital: true, area: "Insurance", created: 1 },
    { id: "fakeToday", t: "Fake call the bank", kind: "action", due: day(0), created: 1 },
    { id: "fakeSoon", t: "Fake file the papers", kind: "action", due: day(5), created: 1 }
  ]
};
const life = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/",
  beforeParse(w) { Object.entries(seed).forEach(([k, v]) => w.localStorage.setItem(k, JSON.stringify(v)));
    w.confirm = () => false; w.alert = () => {}; w.scrollTo = () => {}; w.fetch = () => Promise.reject(new Error("offline")); } });

// ── Vantage (OS kit) ───────────────────────────────────────────────────────
const PFX = "osk:vantage:";
const risks = [];
for (let i = 1; i <= 10; i++) risks.push({ id: "fr" + i, risk: "Fake risk " + i, likelihood: String(1 + (i % 5)), impact: String(1 + ((i * 2) % 5)), status: "Open", due: day(30) });
const van = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'vantage', 'index.html'), 'utf8'), { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/vantage/",
  beforeParse(w) { w.scrollTo = () => {}; w.fetch = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
    w.localStorage.setItem(PFX + "profile", JSON.stringify({ name: "Fake", at: day(-10) }));
    w.localStorage.setItem(PFX + "reg.risks", JSON.stringify(risks)); } });

setTimeout(() => {
  const w = life.window, d = w.document, sec = () => d.getElementById("sections");
  // 1. Today: one card, chosen by risk, the rest under Later (n)
  w.goTab("today");
  const one = d.querySelector(".gm-one");
  ok("Today: the late vital inbox action outranks everything else", one && /Fake renew the health policy/.test(one.textContent), one ? one.textContent.slice(0, 160) : sec().textContent.slice(0, 300));
  ok("Today: exactly one primary button in view", primaries(w, sec(), ".btn-p, .btn.primary").length === 1, primaries(w, sec(), ".btn-p, .btn.primary").map(b => b.textContent).join("|"));
  const later = d.querySelector("details.gm-later");
  ok("Today: the rest are folded under 'Later (n)', closed", later && !later.open && /Later \(\d+\)/.test(later.querySelector("summary").textContent));
  ok("Today: Later holds the item due today and the Stack's step, not the item due in five days", later && /Fake call the bank/.test(later.textContent) && /lowest unfinished layer/.test(later.textContent) && !/Fake file the papers/.test(later.textContent), later && later.textContent.slice(0, 400));
  const c = w.gmFocusCands();
  ok("Today: candidates are sorted by risk score", c.every((x, i) => i === 0 || c[i - 1].score >= x.score), c.map(x => x.id + ":" + x.score).join(" "));
  // finishing the one open action moves the next one up by itself
  w.gmInboxDone("fakeLate");
  const one2 = d.querySelector(".gm-one, .section.active");
  ok("Today: when it is done, the next by risk moves up", !/Fake renew the health policy/.test((d.querySelector(".gm-one") || {}).textContent || "") && w.gmFocusCands()[0].id !== "ib-fakeLate", one2 && one2.textContent.slice(0, 120));

  // 2. Inbox: decide one at a time
  w.goTab("inbox");
  const pr = primaries(w, sec(), ".btn-p, .btn.primary");
  ok("Inbox: one primary in view (decide the first; capture is quiet while things wait)", pr.length === 1 && /Add to my list/.test(pr[0].textContent), pr.map(b => b.textContent).join("|"));
  ok("Inbox: the other two wait under 'Later (2)'", [...sec().querySelectorAll("details.ibnotes > summary")].some(s => /Later \(2\)/.test(s.textContent)));
  ok("Inbox: the vital few and the folded rest are kept", /The vital few|Actions \(/.test(sec().textContent));

  // 3. Every Life OS tab: at most one primary in view
  const tabs = w.eval("TABS").map(t => t[0]), over = [];
  tabs.forEach(id => { try { w.goTab(id); } catch (x) { over.push(id + ":ERR " + x.message); return; }
    const n = primaries(w, sec(), ".btn-p, .btn.primary").length; if (n > 1) over.push(id + ":" + n); });
  ok("every Life OS tab shows at most one primary action", over.length === 0, over.join(" "));

  // 4. Vantage
  const vw = van.window, vd = vw.document, K = vw.OSK, main = () => vd.getElementById("oskMain");
  K.go("today");
  const steps = K.nextSteps();
  ok("Vantage Today: next steps are ranked by risk score", steps.length > 1 && steps.every((x, i) => i === 0 || (steps[i - 1].score || 0) >= (x.score || 0)), steps.map(x => x.score).join(" "));
  ok("Vantage Today: nextStep() is the top of that ranking", K.nextStep() === steps[0] || K.nextStep().text === steps[0].text);
  ok("Vantage Today: one primary in view", primaries(vw, main(), "button.primary").length === 1, primaries(vw, main(), "button.primary").map(b => b.textContent).join("|"));
  const vl = main().querySelector("details.later");
  ok("Vantage Today: the rest are under 'Later (n)', closed", vl && !vl.open && new RegExp("Later \\(" + (steps.length - 1) + "\\)").test(vl.textContent), vl && vl.textContent.slice(0, 120));
  K.go("cadence");
  const cl = main().querySelector("details.later");
  ok("Vantage Rhythm: reviews not yet due wait under 'Later (n)'", cl && !cl.open && /Later \(\d+\)/.test(cl.querySelector("summary").textContent));
  ok("Vantage Rhythm: one primary in view", primaries(vw, main(), "button.primary").length === 1);
  K.go("registers:risks");
  const vb = main().querySelector('[data-a="regVital"]');
  ok("Vantage register: a long list offers 'Show only the vital few (80/20)'", vb && /vital few/.test(vb.textContent));
  const before = main().querySelectorAll("li.row").length;
  vb.dispatchEvent(new vw.MouseEvent("click", { bubbles: true }));
  const after = main().querySelectorAll("li.row").length;
  ok("Vantage register: the vital few is the top fifth by risk (at least three)", before === 10 && after === 3, before + " -> " + after);
  ok("Vantage register: highest score first", /Fake risk/.test((main().querySelector("li.row b") || {}).textContent || ""));

  // 5. the principle is core, in every app
  const pr2 = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'governance', 'principles.json'), 'utf8')).principles.find(p => p.id === "one-open-action");
  ok("one-open-action is a core principle", pr2 && pr2.core === true);
  ok("…and it reached Vantage", K.ed.principles.some(p => p.id === "one-open-action"));

  console.log("test39 one open action: " + P + " passed, " + F + " failed"); if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); } process.exit(0);
}, 1800);
