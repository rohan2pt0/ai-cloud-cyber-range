// test143: personal packs (owner 2026-11-18). The public app carries only the slot; a pack installs from a #pack= link
// after one question, renders one open action on Career with the rest under Later (n), ticks persist, dated items go to
// the calendar group "pack", and hostile pack text is shown as text. Fake content only.
const fs = require('fs'), path = require('path'), { JSDOM } = require('jsdom');
let P = 0, F = 0, e = []; const ok = (n, c, d) => { c ? P++ : (F++, e.push(n + (d ? " :: " + d : ""))); };
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const pack = { name: "Test pack", items: [
  { id: "later-one", title: "A later window", steps: ["Read the official page", "Draft"], due: "2027-08-01", url: "https://example.org/x" },
  { id: "soon-one", title: "The soonest window", why: "Because it is first.", steps: ["Ask a referee", "Send the form"], due: "2027-02-01" },
  { id: "weekly-one", title: "Weekly flagship block", steps: ["90 minutes on the paper"], every: "weekly" },
  { id: "bad-one", title: "<img src=x onerror=alert(1)>", steps: ["<script>x</script>"], url: "javascript:alert(1)" },
  { id: "BAD ID", title: "dropped", steps: ["x"] },
  { id: "no-steps", title: "dropped too", steps: [] } ] };
const link = "https://hub.securax.localhost/app/#pack=" + Buffer.from(JSON.stringify(pack)).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
let asked = 0;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: link,
  beforeParse(w) { w.localStorage.setItem("gm_mine_done", "true"); w.fetch = () => Promise.reject(new Error("offline")); w.scrollTo = () => {};
    w.alert = () => {}; w.confirm = () => { asked++; return true; }; } });
const plain = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://hub.securax.localhost/app/",
  beforeParse(w) { w.localStorage.setItem("gm_mine_done", "true"); w.fetch = () => Promise.reject(new Error("offline")); w.scrollTo = () => {}; } });
setTimeout(() => {
  const w = dom.window, d = w.document, ls = w.localStorage;
  ok("the link installs nothing until the person says yes", !ls.getItem("gm_pack") && !!ls.getItem("gm_pack_offer"));
  ok("the link opens Career", w.eval("curTab") === "career", w.eval("curTab"));
  w.goTab("today");
  const ctab = [...d.querySelectorAll("#tabBar > *")].filter(t => /Career/.test(t.textContent))[0];
  ok("with a pack waiting, Career stays in the tab bar (not folded under More)", !!ctab && ctab.style.display !== "none", ctab && ctab.style.display);
  w.goTab("career");
  const add = d.querySelector("[data-pack-accept]");
  ok("Career asks with an Add my pack button, not a browser dialog an in-app browser can swallow", !!add && asked === 0 && /Test pack/.test(add.closest(".gm-pack-offer").textContent));
  add && add.click();
  const stored = JSON.parse(ls.getItem("gm_pack") || "null");
  ok("one tap installs the pack and clears the offer", !!stored && stored.name === "Test pack" && !ls.getItem("gm_pack_offer"), JSON.stringify(stored && stored.name));
  ok("the link leaves the address bar", !/#pack=/.test(w.location.href));
  ok("bad ids and items without steps are dropped", !!stored && stored.items.length === 4 && !stored.items.some(x => x.id === "BAD ID" || x.id === "no-steps"));
  ok("a javascript: link is not kept", !!stored && stored.items.filter(x => x.id === "bad-one")[0].url === "");
  w.goTab("career"); w.renderAll();
  const card = d.querySelector(".gm-pack");
  ok("Career shows the pack, marked yours only", !!card && /Test pack/.test(card.textContent) && /yours only/.test(card.textContent));
  const first = card && card.querySelector("[data-pack-item]");
  ok("the one open action is a recurring or the soonest dated item", !!first && ["weekly-one", "soon-one"].indexOf(first.getAttribute("data-pack-item")) >= 0, first && first.getAttribute("data-pack-item"));
  const later = card && card.querySelector("details summary");
  ok("the rest fold under Later (3)", !!later && /Later \(3\)/.test(later.textContent), later && later.textContent);
  ok("hostile text is shown as text, never as markup", !!card && !card.querySelector("img") && !card.querySelector("script") && /<img src=x/.test(card.textContent));
  ok("no link carries a javascript: address", !card.innerHTML.includes("javascript:"));
  w.gmPackTick("soon-one", 0); w.renderAll();
  const done = JSON.parse(ls.getItem("gm_pack_done") || "{}");
  ok("a tick persists on the device", Array.isArray(done["soon-one"]) && done["soon-one"][0] === true, JSON.stringify(done));
  const ics = w.gmCalendarDatedICS("pack");
  ok("dated items go to the calendar with a permanent uid", /UID:securax-gm-pack-soon-one/.test(ics) && /UID:securax-gm-pack-later-one/.test(ics) && !/weekly-one/.test(ics), ics.slice(0, 300));
  w.gmPackTick("weekly-one", 0);
  const wk = Object.keys(JSON.parse(ls.getItem("gm_pack_done") || "{}")).filter(k => k.indexOf("weekly-one:") === 0);
  ok("a weekly item's ticks belong to this week, so it starts over next week", wk.length === 1 && /^weekly-one:\d{4}-\d{2}-\d{2}$/.test(wk[0]), JSON.stringify(wk));
  // a device with no pack shows nothing extra
  plain.window.goTab("career"); plain.window.renderAll();
  ok("the public app without a pack shows no pack card", !plain.window.document.querySelector(".gm-pack"));
  let threw = ""; try { w.gmPackClean({ items: [] }); } catch (x) { threw = x.message; }
  ok("an empty pack is refused with a plain reason", /no usable items/.test(threw), threw);
  console.log("test143 personal packs: " + P + " passed, " + F + " failed");
  if (F) { e.forEach(x => console.log("  " + x)); process.exit(1); }
  process.exit(0);
}, 1800);
