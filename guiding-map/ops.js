/* ═══════════════════════════════════════════════════════════════════
   THE GUIDING MAP — OPS LAYER v4.0
   Adds: PWA install + offline, cadence engine, Never-Miss-Twice
   enforcement, WOOP quarterly, After-Action Review, NIST CSF 2.0
   self-score, per-key sync (no blob overwrite), auto-backup nudge.
   Nothing here rewrites your existing logic. It only adds.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  /* ── tiny store helpers ─────────────────────────────────────────── */
  function G(k, d) { try { var s = localStorage.getItem(k); return s ? JSON.parse(s) : d; } catch (e) { return d; } }
  function S_(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function ymd(d) { d = d || new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  window.gmG = G; window.gmS = S_;

  /* ── 1. PWA: service worker + install ───────────────────────────── */
  if ("serviceWorker" in navigator && location.protocol.indexOf("http") === 0) {
    // Self-healing updates: when a new service worker takes control after a
    // redeploy/pull, reload the page ONCE so the fresh app shows immediately —
    // no more stale old version lingering from the cache. We only reload when a
    // controller already existed (a genuine update), never on first install.
    var _swHadController = !!navigator.serviceWorker.controller;
    var _swReloaded = false;
    navigator.serviceWorker.addEventListener("controllerchange", function () {
      if (_swReloaded || !_swHadController) return;
      _swReloaded = true;
      window.location.reload();
    });
    navigator.serviceWorker.register("sw.js").then(function (reg) {
      if (reg) { try { reg.update(); } catch (e) {} }   // check for a newer SW now
    }).catch(function () {});
  }
  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); deferredPrompt = e; });
  window.gmInstall = function () {
    if (deferredPrompt) { deferredPrompt.prompt(); deferredPrompt = null; return; }
    alert("iPhone/iPad: tap Share \u2192 Add to Home Screen.\nAndroid Chrome: menu \u22ee \u2192 Install app.\nDesktop Chrome/Edge: install icon in the address bar.");
  };

  /* ── 2. Cadence engine ──────────────────────────────────────────── */
  // A ritual is due when its window is open and it has not been logged in that window.
  function nthSundayOfMonth(d, n) {
    var f = new Date(d.getFullYear(), d.getMonth(), 1);
    var off = (7 - f.getDay()) % 7;
    return new Date(d.getFullYear(), d.getMonth(), 1 + off + (n - 1) * 7);
  }
  function weekKey(d) {
    var t = new Date(d); t.setDate(t.getDate() - t.getDay()); return ymd(t);
  }
  function qKey(d) { return d.getFullYear() + "-Q" + (Math.floor(d.getMonth() / 3) + 1); }

  var RITUALS = [
    {
      id: "sunday", name: "Sunday Pulse", mins: 20, tag: "Weekly \u00b7 Sunday",
      window: function (d) { return d.getDay() === 0; },
      key: function (d) { return weekKey(d); },
      steps: [
        "Three questions: did this month's debt payment go out? what is the emergency fund balance right now? did the top item in your queue move at all?",
        "3-line note \u2014 what worked / what didn't / what to adjust",
        "Notes app: clear the capture inbox to zero, look at each active project, update the ongoing areas",
        "OPSEC check: this week's threats, update incident response plan if needed",
        "Habit streaks: anything missed twice \u2192 mandatory recovery day"
      ]
    },
    {
      id: "money", name: "Money Date + Monthly Numbers", mins: 60, tag: "Monthly \u00b7 1st Sunday",
      window: function (d) { var t = nthSundayOfMonth(d, 1); return ymd(d) === ymd(t) || (d.getDate() <= 10 && d.getDay() === 0); },
      key: function (d) { return d.getFullYear() + "-" + (d.getMonth() + 1); },
      steps: [
        "Update all numbers: net, expenses, savings, investments, loans (Setup/Edit Profile)",
        "Run the full checklist \u2014 all KPIs + 6 Risks (Pillars + Shield tabs)",
        "Card zero-check: verify every credit card is \u20b90",
        "Review the auto-transfer \u2014 raise it 1% if the month felt comfortable",
        "Check Conscious Spending bands (Fixed 50-60% \u00b7 Investments 10%+ \u00b7 Savings 5-10%)",
        "Pick the single highest-priority action for next month \u2014 one, not three",
        "Export JSON backup \u2192 move to _archive/backups/"
      ]
    },
    {
      id: "quarter", name: "Quarterly Review", mins: 120, tag: "Quarterly \u00b7 1st month",
      window: function (d) { return [0, 3, 6, 9].indexOf(d.getMonth()) >= 0 && d.getDate() <= 14; },
      key: function (d) { return qKey(d); },
      steps: [
        "Money: re-order your priority list, update progress toward financial independence, check the equity/debt/gold split",
        "Rentals: rent vs 3 current listings per property; local market check",
        "Career: resume refresh + 1-2 recon interviews",
        "Venture: 15-min review; notes from any site visits",
        "Health: are the 4 preventive slots booked?",
        "Relationship: couple check-in booked (fortnightly 90-min slot)",
        "Set this quarter's goal card and objectives \u2014 the Wish/Outcome/Obstacle/Plan panel further down this tab",
        "Implementation-intention audit: do all six habit anchors still fire? (Ops tab)"
      ]
    },
    {
      id: "redteam", name: "Red-Team Your Life", mins: 120, tag: "Quarterly",
      window: function (d) { return [0, 3, 6, 9].indexOf(d.getMonth()) >= 0 && d.getDate() <= 21; },
      key: function (d) { return qKey(d); },
      steps: [
        "Assume compromise: email/phone/bank breached right now \u2014 what are your first 3 actions?",
        "Social engineering drill: design a real phish targeting you. Would you fall for it?",
        "Physical audit: home, car, commute \u2014 note 3 vulnerabilities, fix within a week",
        "Digital deep-scan: haveibeenpwned, password manager health, verify 2FA on all critical accounts",
        "Mental stress test: job loss + health event + family crisis simultaneously \u2014 write the plan",
        "Continuity test: hand over the binder, ask for the monthly review to be run without you"
      ]
    },
    {
      id: "april", name: "April Tax Lock-In", mins: 90, tag: "Annual \u00b7 April week 1",
      window: function (d) { return d.getMonth() === 3 && d.getDate() <= 10; },
      key: function (d) { return "apr-" + d.getFullYear(); },
      steps: [
        "Old-vs-new regime calculation for BOTH earners",
        "PPF top-up before 5 April (full-year interest)",
        "Employer asset & liability filing from the xlsx",
        "HRA hygiene: receipts, landlord PAN, bank trail, relationship disclosure",
        "Confirm the person claiming the home-loan interest deduction (Section 24(b)) and the 80C deductions is the same person your CA said should declare the rent"
      ]
    },
    {
      id: "annual", name: "Annual Overhaul", mins: 240, tag: "Annual \u00b7 August",
      window: function (d) { return d.getMonth() === 7; },
      key: function (d) { return "aug-" + d.getFullYear(); },
      steps: [
        "Insurance re-quote: life, health, property, personal accident",
        "Will + nomination audit \u2014 update for any life changes",
        "Rent benchmark: 3 comparable listings per property",
        "Re-pull the 7/12 extract (the Maharashtra land record showing ownership and encumbrances) for every land holding",
        "Hit-By-A-Bus test: your partner drives the entire review, you only answer",
        "Home-loan rate check \u2014 only reconsider prepayment if rate > 9%"
      ]
    }
  ];

  function cadenceLog() { return G("gm_cadence", {}); }
  function ritualDue(r) {
    var d = new Date();
    if (!r.window(d)) return false;
    var log = cadenceLog();
    return log[r.id] !== r.key(d);
  }
  window.gmRitualDone = function (id) {
    gmSnap("marked a ritual done");
    var r = null; RITUALS.forEach(function (x) { if (x.id === id) r = x; });
    if (!r) return;
    var log = cadenceLog(); log[r.id] = r.key(new Date()); S_("gm_cadence", log);
    if (window.renderAll) renderAll();
  };
  function dueRituals() { if (inRecovery()) return []; return RITUALS.filter(ritualDue); }

  /* ── 3. Never-Miss-Twice enforcement ────────────────────────────── */
  function brokenHabits() {
    if (typeof HABITS === "undefined" || typeof missedTwice !== "function") return [];
    return HABITS.filter(function (h) { try { return missedTwice(h.id); } catch (e) { return false; } });
  }

  /* ── 4. The pinned card on Today ────────────────────────────────── */
  function pinnedHTML() {
    var h = "", broken = brokenHabits(), due = dueRituals();
    if (broken.length) {
      h += '<div style="background:var(--redBg);border:1.5px solid var(--red);border-radius:12px;padding:13px;margin-bottom:12px">'
        + '<div style="font-weight:800;font-size:12px;letter-spacing:.6px;text-transform:uppercase;color:var(--red)">\u26a0 Never Miss Twice \u2014 recovery is mandatory today</div>'
        + '<div style="font-size:12px;line-height:1.7;margin-top:7px;color:var(--text)">';
      broken.forEach(function (b) { h += "\u2022 <b>" + esc(b.name) + "</b> \u2014 " + esc(b.min || "do the 2-minute floor, nothing more") + "<br>"; });
      h += '</div><div style="font-size:11px;color:var(--muted);margin-top:6px">One miss is an accident. Two starts a new habit. The floor counts as a win.</div></div>';
    }
    if (due.length) {
      due.forEach(function (r) {
        h += '<div style="background:var(--amberBg);border:1.5px solid var(--amber);border-radius:12px;padding:13px;margin-bottom:12px">'
          + '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
          + '<div style="font-weight:800;font-size:12.5px;color:var(--amber)">\u23f1 ' + esc(r.name) + '</div>'
          + '<div style="font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)">' + esc(r.tag) + ' \u00b7 ' + r.mins + ' min</div></div>';
        if (r.id === "sunday") h += scqaHTML();
        h += '<div style="font-size:12px;line-height:1.75;margin-top:8px;color:var(--text)">';
        r.steps.forEach(function (s) { h += '<span style="color:var(--green)">\u25b8</span> ' + esc(s) + "<br>"; });
        h += '</div><button class="btn-sm" style="background:var(--amber);color:#fff;margin-top:9px" onclick="gmRitualDone(\'' + r.id + '\')">Mark done</button></div>';
      });
    }
    return h;
  }

  /* ── 5. WOOP (Oettingen) — quarterly goal setting ───────────────── */
  function woopHTML() {
    var q = qKey(new Date()), wAll = G("gm_woop", {}), w = wAll[q] || { w: "", o: "", ob: "", p: "" };
    function f(lbl, key, ph, val) {
      return '<label class="f-label">' + lbl + '</label><textarea rows="2" placeholder="' + ph + '" oninput="gmWoopSet(\'' + key + '\',this.value)">' + esc(val || "") + '</textarea>';
    }
    return '<div class="cat-t">\u{1F3AF} Quarterly goal card \u2014 ' + q + '</div>'
      + '<div class="info">Four boxes, once a quarter. Named WOOP by the psychologist who tested it (Gabriele Oettingen): Wish, Outcome, Obstacle, Plan. Wishing on its own actually lowers follow-through \u2014 it is naming the obstacle and pre-deciding the response that does the work.</div>'
      + (w.w ? "" : tplBtn("gmTplWoop()", "Start from a worked example"))
      + '<div class="road-col">'
      + f("Wish \u2014 one challenging but feasible outcome", "w", "e.g. Emergency fund fully funded at 6 months", w.w)
      + f("Outcome \u2014 how it feels when done", "o", "Name the single best feeling, concretely", w.o)
      + f("Obstacle \u2014 the inner one, not the excuse", "ob", "What in YOU blocks this? Not circumstances.", w.ob)
      + f("Plan \u2014 IF [obstacle] THEN [action]", "p", "IF I feel the month is tight THEN I transfer \u20b95k anyway on day 1", w.p)
      + '</div>';
  }
  window.gmWoopSet = function (k, v) {
    var q = qKey(new Date()), all = G("gm_woop", {});
    all[q] = all[q] || {}; all[q][k] = v; S_("gm_woop", all);
  };

  /* ── 6. After-Action Review (US Army 4 questions) ───────────────── */
  function aarHTML() {
    var log = G("gm_aar", []);
    var h = '<div class="cat-t">\u{1F5C2} After-Action Review \u2014 monthly (four questions the army uses to debrief)</div>'
      + '<div class="info">Four questions, unchanged since they were designed for units debriefing under fire. They work because they separate intent from outcome before assigning cause.</div>'
      + '<div class="road-col">'
      + '<label class="f-label">1. What was supposed to happen?</label><textarea rows="2" id="aar1"></textarea>'
      + '<label class="f-label">2. What actually happened?</label><textarea rows="2" id="aar2"></textarea>'
      + '<label class="f-label">3. Why the difference?</label><textarea rows="2" id="aar3"></textarea>'
      + '<label class="f-label">4. What will you do differently \u2014 one thing?</label><textarea rows="2" id="aar4"></textarea>'
      + '<button class="btn btn-p" style="margin-top:6px" onclick="gmAarSave()">Save this month\u2019s review</button></div>';
    if (log.length) {
      h += '<div class="cat-t" style="margin-top:14px">Past reviews</div>';
      log.slice(-6).reverse().forEach(function (e) {
        h += '<div class="road-col" style="margin-bottom:8px"><div class="road-h">' + esc(e.d) + '</div>'
          + '<div class="road-i"><b>Planned:</b> ' + esc(e.a) + '</div>'
          + '<div class="road-i"><b>Happened:</b> ' + esc(e.b) + '</div>'
          + '<div class="road-i"><b>Why:</b> ' + esc(e.c) + '</div>'
          + '<div class="road-i"><b>Change:</b> ' + esc(e.e) + '</div></div>';
      });
    }
    return h;
  }
  window.gmAarSave = function () {
    var log = G("gm_aar", []);
    log.push({
      d: ymd(), a: (document.getElementById("aar1") || {}).value || "",
      b: (document.getElementById("aar2") || {}).value || "",
      c: (document.getElementById("aar3") || {}).value || "",
      e: (document.getElementById("aar4") || {}).value || ""
    });
    var chg = (document.getElementById("aar4") || {}).value || "";
    if (chg.trim()) {
      var q = resQ(); var dd = new Date(); dd.setDate(dd.getDate() + 7);
      q.push({ d: ymd(), txt: chg.trim().slice(0, 200), iv: 7, due: ymd(dd) });
      if (q.length > 20) q = q.slice(-20);
      S_("gm_resurface", q);
    }
    if (log.length > 24) {
      if (!confirm("You have 24 saved reviews \u2014 two years' worth. Saving this one drops the oldest.\n\nExport a backup first if you want to keep it (Ops \u2192 System health).\n\nSave anyway?")) return;
      log = log.slice(-24);
    }
    S_("gm_aar", log); renderAll();
  };

  /* ── 7. NIST CSF 2.0 self-score for the Security pillar ─────────── */
  var CSF = [
    ["GV", "Govern", "You have written rules for yourself: what you never click, what needs a second channel, who is told what. Reviewed, not just felt."],
    ["ID", "Identify", "You can list every account, device and data store that matters, and who else can reach them."],
    ["PR", "Protect", "Password manager, unique 16+ char passwords, 2FA on email/bank/broker, device encryption, separate financial email."],
    ["DE", "Detect", "haveibeenpwned monitoring, bank + CIBIL alerts on, you would notice a compromise within days not months."],
    ["RS", "Respond", "A written incident plan for lost phone, lost laptop, drained account \u2014 numbers to call, in order, offline."],
    ["RC", "Recover", "Tested restores: your backups actually open, your family can reach your accounts, nothing depends only on you."]
  ];
  function csfHTML() {
    var sc = G("gm_csf", {});
    var vals = CSF.map(function (c) { return sc[c[0]] || 0; });
    var avg = Math.round(vals.reduce(function (a, b) { return a + b; }, 0) / CSF.length * 20);
    var h = '<div class="cat-t">\u{1F510} NIST CSF 2.0 \u2014 personal self-score <span class="pill pill-g">' + avg + '%</span></div>'
      + '<div class="info">The six functions of the 2024 framework, applied to one person instead of an enterprise. Score each 0-5 honestly. Anything below 3 is your next security action, and the sentence under each heading already says exactly what to build \u2014 nothing to look up.</div>';
    CSF.forEach(function (c) {
      var v = sc[c[0]] || 0;
      h += '<div class="road-col" style="margin-bottom:8px"><div class="road-h">' + c[0] + ' \u00b7 ' + c[1]
        + ' <span style="float:right;color:' + (v >= 3 ? "var(--green)" : "var(--red)") + '">' + v + '/5</span></div>'
        + '<div class="road-i">' + c[2] + '</div>'
        + '<input type="range" min="0" max="5" step="1" value="' + v + '" style="margin:8px 0 0" oninput="gmCsfSet(\'' + c[0] + '\',this.value)"></div>';
    });
    return h;
  }
  window.gmCsfSet = function (k, v) { var sc = G("gm_csf", {}); sc[k] = parseInt(v, 10); S_("gm_csf", sc); renderAll(); };

  /* ── 8. Sync (per-key merge, dormant until configured) ──────────── */
  // Fixes the old whole-blob upsert, which let the last device to write
  // silently overwrite edits made on the other two.
  function cfg() { return G("gm_sync_cfg", null); }
  function meta() { return G("gm_meta", {}); }
  // Server-anchored clock. Two devices with drifted clocks otherwise lose writes
  // permanently in one direction: the fast clock always wins the per-key merge
  // and the slow device's edits are silently discarded on every pull.
  var skew = 0;
  function nowSrv() { return Date.now() + skew; }
  function syncClock(url) {
    return fetch(String(url).replace(/\/+$/, "") + "/", { method: "HEAD", mode: "cors" })
      .then(function (r) {
        var d = r.headers.get("date");
        if (d) { var t = Date.parse(d); if (!isNaN(t)) skew = t - Date.now(); }
      }).catch(function () { skew = 0; });
  }
  function touch(k) { var m = meta(); m[k] = nowSrv(); S_("gm_meta", m); }
  var _set0 = localStorage.setItem.bind(localStorage);
  function _set(k, v) {
    try { _set0(k, v); } catch (e) {
      // Quota exhausted. Silent failure here would mean the user keeps
      // typing into a form that is no longer saving anything.
      alert("This device is out of storage, so that change was NOT saved.\n\nOps tab \u2192 System health \u2192 Export backup, then remove old data.");
      throw e;
    }
  }
  var pushTimer = null;
  try {
    localStorage.setItem = function (k, v) {
      _set(k, v);
      if (k.indexOf("gm_meta") !== 0 && k.indexOf("gm_sync") !== 0) { try { touch(k); } catch (e) {} }
      bustDerived();
      if (cfg()) { clearTimeout(pushTimer); pushTimer = setTimeout(gmPush, 1200); }
    };
  } catch (e) { console.log("[sync] setItem not writable; sync will push on tab change only"); }
  // \u2500\u2500 Transport: the SecuRAX estate sync endpoint (sovereign, over Tailscale).
  //    A drop-in for the old cloud REST calls \u2014 SAME per-key-merge semantics,
  //    but your data lives on YOUR gateway (Postgres), never a third-party SaaS.
  //    Contract (served by the estate gateway, see docs/securax/14):
  //      GET {base}/state?user=<id>  -> { payload:{k:v}, meta:{k:ts} }  (404 if none yet)
  //      PUT {base}/state?user=<id>  body { payload, meta }            (stores)
  //    Auth: Authorization: Bearer <device token>. No SDK, no CDN \u2014 plain fetch.
  function syncHeaders(c) { return { "Content-Type": "application/json", "Authorization": "Bearer " + c.key }; }
  function stateURL(c) { return String(c.url).replace(/\/+$/, "") + "/state?user=" + encodeURIComponent(c.user); }
  var lastPull = 0;
  window.gmSyncInit = function (force) {
    var c = cfg(); if (!c || !c.url || !c.key || !navigator.onLine) return;
    if (!force && Date.now() - lastPull < 15000) return;   // app-switching must not hammer
    lastPull = Date.now();
    gmLiveStart();
    syncClock(c.url).then(function () {
      return fetch(stateURL(c), { headers: syncHeaders(c) });
    }).then(function (r) {
      if (!r || !r.ok) return gmPush();                    // 404 / first run / unreachable -> push local
      return r.json().then(function (body) {
        var remote = (body && body.payload) || {}, rmeta = (body && body.meta) || {}, m = meta(), changed = false;
        // Integrity guard: a remote copy that is drastically smaller than local is
        // corruption or a wrong row, not a legitimate state. Refuse and flag.
        var localN = localStorage.length, remoteN = Object.keys(remote).length;
        if (localN > 10 && remoteN < localN / 2) { S_("gm_sync_anomaly", ymd() + ": remote had " + remoteN + " keys vs " + localN + " local \u2014 merge refused"); return gmPush(); }
        Object.keys(remote).forEach(function (k) {
          if (!m[k] || (rmeta[k] || 0) > m[k]) { _set(k, remote[k]); m[k] = rmeta[k] || nowSrv(); changed = true; }
        });
        if (changed) { S_("gm_meta", m); renderAll(); }
        gmPush();
      });
    }).catch(function (e) { console.log("[sync]", e.message); });
  };
  window.gmPush = function () {
    var c = cfg(); if (!c || !c.url || !c.key) return;
    var blob = {}, m = meta();
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k.indexOf("gm_sync") !== 0) blob[k] = localStorage.getItem(k);
    }
    fetch(stateURL(c), { method: "PUT", headers: syncHeaders(c),
        body: JSON.stringify({ payload: blob, meta: m, updated_at: new Date(nowSrv()).toISOString(), device: devId }) })
      .then(function (r) {
        if (!r || !r.ok) { S_("gm_sync_fails", G("gm_sync_fails", 0) + 1); return; }
        S_("gm_sync_last", ymd() + " " + new Date().toTimeString().slice(0, 5));
        S_("gm_sync_fails", 0);
        // The estate keeps a snapshot of the merged state for every day (so nobody has to remember to export a backup).
        return r.json().then(function (j) { if (j && j.snapshots) S_("gm_sync_snaps", { n: j.snapshots, latest: j.latest_snapshot }); }).catch(function () {});
      })
      .catch(function () { S_("gm_sync_fails", G("gm_sync_fails", 0) + 1); });
  };
  // Live push (WebSocket): the server only says "something changed"; we then pull through
  // the same per-key merge. If the socket cannot open or drops, the existing pull-on-open
  // and push-on-edit paths keep working unchanged -- a socket costs latency, never data.
  var ws = null, wsTimer = null, wsBackoff = 2000;
  // Which device wrote: a device ignores pings about its own writes (no echo loop).
  var devId = G("gm_sync_dev", null) || (function () { var d = Math.random().toString(36).slice(2, 10); S_("gm_sync_dev", d); return d; })();
  function wsURL(c) { return String(c.url).replace(/\/+$/, "").replace(/^http/, "ws") + "/ws"; }
  window.gmLiveStop = function () { clearTimeout(wsTimer); if (ws) { try { ws.close(); } catch (e) {} ws = null; } };
  window.gmLiveStart = function () {
    var c = cfg(); if (!c || !c.url || !c.key || typeof WebSocket === "undefined") return;
    if (ws && ws.readyState <= 1) return;
    try { ws = new WebSocket(wsURL(c)); } catch (e) { return; }
    var mine = ws, ping = null;
    mine.onopen = function () { mine.send(JSON.stringify({ token: c.key, user: c.user })); };
    mine.onmessage = function (ev) {
      var m = {}; try { m = JSON.parse(ev.data); } catch (e) {}
      if (m.type === "ready") { wsBackoff = 2000; S_("gm_sync_live", 1); ping = setInterval(function () { try { mine.send("ping"); } catch (e) {} }, 30000); }
      if (m.type === "changed" && m.origin !== devId) { lastPull = 0; gmSyncInit(true); }
    };
    mine.onclose = function () {
      clearInterval(ping); S_("gm_sync_live", 0); if (ws === mine) ws = null;
      if (cfg()) { wsTimer = setTimeout(gmLiveStart, wsBackoff); wsBackoff = Math.min(wsBackoff * 2, 60000); }
    };
    mine.onerror = function () { try { mine.close(); } catch (e) {} };
  };
  // One-link setup: `./securax sync-link` prints  <hub address>/#sync=<base64url JSON {url,key,user}>.  Opening it on a phone sets sync up in one
  // tap. The data after # never leaves the browser (it is not sent to any server); we remove it from the address bar straight away, we
  // always show WHERE the data will go before saving, and an existing setup is never replaced without a second, explicit yes.
  function b64urlJson(t) { t = String(t).replace(/-/g, "+").replace(/_/g, "/"); while (t.length % 4) t += "="; return JSON.parse(decodeURIComponent(escape(atob(t)))); }
  window.gmSyncLinkImport = function () {
    var h = String(location.hash || ""), m = /^#sync=([A-Za-z0-9_-]+)$/.exec(h);
    if (!m) return false;
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    try {
      var o = b64urlJson(m[1]);
      if (!o || typeof o.url !== "string" || !/^https?:\/\//.test(o.url) || typeof o.key !== "string" || !o.key || o.key.length > 300) throw new Error("not a sync link");
      var user = String(o.user || "me").slice(0, 256), host = new URL(o.url).host;
      if (!confirm("Turn on cross-device sync?\n\nYour data will be stored on:\n" + host + "\n\nOnly continue if this link came from your own SecuRAX estate.")) return true;
      if (cfg() && !confirm("This device is already syncing to " + new URL(cfg().url).host + ". Replace it with " + host + "?")) return true;
      S_("gm_sync_cfg", { url: o.url.replace(/\/+$/, ""), key: o.key, user: user });
      alert("Sync is on. Your data will follow you across devices.");
      setTimeout(function () { gmSyncInit(true); renderAll(); }, 50);
    } catch (e) { alert("That setup link could not be read: " + e.message); }
    return true;
  };
  function snapBase() { var c = cfg(); return String(c.url).replace(/\/+$/, "") + "/snapshots"; }
  window.gmSnapList = function () {
    var c = cfg(), box = document.getElementById("snapList"); if (!c || !box) return;
    box.innerHTML = "Loading\u2026";
    fetch(snapBase() + "?user=" + encodeURIComponent(c.user), { headers: syncHeaders(c) })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (list) {
        box.innerHTML = list.length ? list.map(function (x) {
          return '<div style="display:flex;gap:8px;align-items:center;margin:4px 0"><span style="flex:1">' + esc(x.day) + ' \u00b7 ' + x.keys + ' items</span>'
            + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmSnapRestore(\'' + esc(x.day) + '\')">Restore</button></div>';
        }).join("") : "No snapshots yet: the first one is taken at your next change.";
      }).catch(function (e) { box.textContent = "Could not read the estate's snapshots (" + e.message + "). Your data on this device is untouched."; });
  };
  window.gmSnapRestore = function (day) {
    var c = cfg(); if (!c || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return;
    fetch(snapBase() + "/" + day + "?user=" + encodeURIComponent(c.user), { headers: syncHeaders(c) })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (b) {
        var keys = Object.keys(b.payload || {});
        if (!keys.length || !confirm("Restore the estate's snapshot of " + day + " (" + keys.length + " items)? Everything on this device is replaced; you can undo this once from Ops.")) return;
        gmSnap("before restoring the " + day + " snapshot");
        keys.forEach(function (k) { if (k.indexOf("gm_sync") !== 0 && k.indexOf("gm_undo") !== 0) _set0(k, b.payload[k]); });
        location.reload();
      }).catch(function (e) { alert("Could not restore that snapshot: " + e.message); });
  };
  window.gmSyncSave = function () {
    var url = document.getElementById("syUrl").value.trim();
    var key = document.getElementById("syKey").value.trim();
    var user = document.getElementById("syUser").value.trim() || "me";
    if (!url || !key) { alert("Both the estate sync URL and your device token are needed."); return; }
    S_("gm_sync_cfg", { url: url, key: key, user: user });
    gmSyncInit(true); renderAll();
  };
  window.gmSyncOff = function () { gmSnap("turned cross-device sync off"); localStorage.removeItem("gm_sync_cfg"); gmLiveStop(); renderAll(); };

  function syncHTML() {
    var c = cfg(), last = G("gm_sync_last", null);
    var h = '<div class="cat-t">\u{1F501} Cross-device sync <span class="pill pill-g">sovereign</span></div>';
    if (c) {
      h += '<div class="info">Sync is on for <b>' + esc(c.user) + '</b>. Last push: ' + esc(last || "not yet") + '. '
        + 'Edits merge per field by timestamp, so the phone and the laptop no longer overwrite each other. '
        + 'Your data stays on your own SecuRAX gateway \u2014 no third party.</div>'
        + '<button class="btn btn-s" onclick="gmSyncOff()">Turn sync off</button>';
    } else {
      h += '<div class="info">Optional. Without it, each device keeps its own copy and you move data with Export/Import. '
        + 'With it, all devices stay live \u2014 synced through <b>your own SecuRAX estate</b> (not a cloud SaaS), reached privately over Tailscale. '
        + 'Setup is in docs/securax/14-GUIDING-MAP.md.</div>'
        + '<label class="f-label">Estate sync URL</label><input id="syUrl" value="' + (SECURE_ORIGIN ? "https://sync." + ESTATE_DOM + "/sync" : "") + '" placeholder="' + (SECURE_ORIGIN ? "https://sync." + ESTATE_DOM + "/sync" : "http://securax.your-tailnet.ts.net:8089/sync") + '">'
        + '<label class="f-label">Device token</label><input id="syKey" placeholder="your estate sync token">'
        + '<label class="f-label">Your row id (anything, same on every device)</label><input id="syUser" placeholder="me">'
        + '<button class="btn btn-p" onclick="gmSyncSave()">Turn sync on</button>';
    }
    return h;
  }


  /* ── 12. Implementation-Intention Audit ────────────────────────────
     You have IF-THEN anchors. Nothing checked whether they still fire.
     An anchor decays when the cue disappears (schedule change, new job,
     travel, a baby). Gollwitzer's finding is that the plan works only
     while the cue is still reliably present — so the cue is the thing
     that needs auditing, not your willpower. Quarterly, 10 minutes. */
  function anchorHTML() {
    if (typeof HABITS === "undefined") return "";
    var a = G("gm_anchors", {});
    var h = '<div class="cat-t">\u{1F517} Implementation-intention audit \u2014 do your anchors still fire?</div>'
      + '<div class="info">For each habit: is the cue still reliably present in your day? '
      + 'A habit that keeps failing usually has a dead cue, not a weak operator. Rewrite the anchor rather than adding discipline.</div>';
    HABITS.forEach(function (hb) {
      var st = a[hb.id] || {};
      var fires = st.fires === undefined ? 2 : st.fires;
      var col = fires >= 2 ? "var(--green)" : fires === 1 ? "var(--amber)" : "var(--red)";
      h += '<div class="road-col" style="margin-bottom:8px">'
        + '<div class="road-h">' + hb.icon + ' ' + esc(hb.name) + '</div>'
        + '<div class="road-i" style="color:var(--muted)">Current anchor: ' + esc(st.anchor || hb.anchor) + '</div>'
        + '<div style="display:flex;gap:6px;margin:8px 0">';
      [[2, "Fires reliably"], [1, "Cue is patchy"], [0, "Cue is gone"]].forEach(function (o) {
        h += '<button class="btn-sm" style="flex:1;background:' + (fires === o[0] ? col : "var(--cardAlt)")
          + ';color:' + (fires === o[0] ? "#fff" : "var(--text)") + '" onclick="gmAnchorSet(\'' + hb.id + '\',\'fires\',' + o[0] + ')">' + o[1] + '</button>';
      });
      h += '</div>';
      if (fires < 2) {
        h += '<label class="f-label">Rewrite the anchor \u2014 IF [a cue that actually happens] THEN [the behaviour]</label>'
          + '<input value="' + esc(st.anchor || hb.anchor) + '" onchange="gmAnchorSet(\'' + hb.id + '\',\'anchor\',this.value)">';
      }
      h += '</div>';
    });
    return h;
  }
  window.gmAnchorSet = function (id, k, v) {
    var a = G("gm_anchors", {}); a[id] = a[id] || {}; a[id][k] = v;
    a[id].audited = ymd(); S_("gm_anchors", a); renderAll();
  };

  /* ── 13. The 3 Standing Rules (Part 11) ────────────────────────── */
  function rulesHTML() {
    return '<div class="cat-t">\u{1F4CF} The three standing rules</div>'
      + '<div class="road-col">'
      + '<div class="road-i"><b>1.</b> One in-progress action at a time. The queue is ordered; work the top of it.</div>'
      + '<div class="road-i"><b>2.</b> Everything has a date or it does not exist.</div>'
      + '<div class="road-i"><b>3.</b> Miss a review \u2192 do the next one. Never restart the system.</div>'
      + '</div>'
      + '<div class="info" style="margin-top:8px">Rule 3 is enforced in code: a skipped ritual does not stack up or reproach you. '
      + 'It simply comes due again in its next window, clean.</div>';
  }

  /* ── 14. Completion checklist (Part 15) ────────────────────────── */
  var DONE_LIST = [
    ["setup", "Dashboard built and every KPI card opened once"],
    ["risks", "All 6 Risks reviewed in the Shield tab"],
    ["sec", "Security pillar completed \u2014 digital hygiene, OPSEC, social engineering, mental, physical"],
    ["para", "Notes app organised into four folders: Projects (has a deadline), Areas (ongoing, no end date), Resources (reference), Archive (done)"],
    ["water", "Waterfall auto-split configured with the bank"],
    ["ef", "Emergency fund split across instant-access savings, a sweep-in fixed deposit (auto-breaks without penalty), and a liquid mutual fund"],
    ["sip", "SIP auto-debit set for salary day + 2, with annual step-up"],
    ["cards", "Credit cards verified at \u20b90 this month"],
    ["ins", "Insurance order completed \u2014 super top-up, parents, personal accident"],
    ["will", "Two wills + all nominations completed"],
    ["docs", "Document queue cleared \u2014 certificates, Aadhaar, sale deeds, DigiLocker batch"],
    ["tax", "Tax regime checked; CA clubbing determination obtained"],
    ["emp", "Employer property-intimation filed for both properties"],
    ["backup", "Monthly backup exported to _archive/backups/"],
    ["binder", "Emergency binder printed; password-manager emergency access granted"],
    ["cont", "Annual continuity test passed \u2014 the review ran without you"]
  ];
  function doneHTML() {
    var d = G("gm_done", {});
    var n = DONE_LIST.filter(function (x) { return d[x[0]]; }).length;
    var h = '<div class="cat-t">\u2705 Project completion <span class="pill pill-g">' + n + '/' + DONE_LIST.length + '</span></div>'
      + '<div class="info">The build checklist, not the daily one. Most of these are done once and never again \u2014 which is exactly why they slip.</div>'
      + '<div class="road-col">';
    DONE_LIST.forEach(function (x) {
      h += '<div class="road-i" style="cursor:pointer;display:flex;gap:8px;align-items:flex-start" onclick="gmDoneTg(\'' + x[0] + '\')">'
        + '<span style="color:' + (d[x[0]] ? "var(--green)" : "var(--muted)") + ';font-weight:800">' + (d[x[0]] ? "\u2611" : "\u2610") + '</span>'
        + '<span style="' + (d[x[0]] ? "opacity:.55;text-decoration:line-through" : "") + '">' + esc(x[1]) + '</span></div>';
    });
    return h + '</div>';
  }
  window.gmDoneTg = function (k) { var d = G("gm_done", {}); d[k] = !d[k]; S_("gm_done", d); renderAll(); };


  /* ═══════════════════════════════════════════════════════════════
     v5 — THE STACK, THE LIFE MAP, FRICTION, RECOVERY MODE
     ═══════════════════════════════════════════════════════════════ */

  /* ── 15. Recovery Mode ─────────────────────────────────────────────
     The real failure mode is not a missed day. It is abandoning the
     system after a bad fortnight and never coming back. Toyota's line
     could be stopped by any worker; the point was that stopping was
     legitimate, so nobody hid a fault. Same idea. */
  function inRecovery() {
    var r = G("gm_recovery", null);
    if (!r) return false;
    if (new Date(r.until) < new Date()) { localStorage.removeItem("gm_recovery"); return false; }
    return r;
  }
  window.gmRecoveryOn = function (days) {
    gmSnap("paused the cadence for " + days + " days");
    var u = new Date(); u.setDate(u.getDate() + days);
    S_("gm_recovery", { until: u.toISOString(), started: ymd() });
    renderAll(); window.scrollTo(0, 0);
  };
  window.gmRecoveryOff = function () { gmSnap("ended recovery mode"); localStorage.removeItem("gm_recovery"); renderAll(); };

  /* ── 16. The Daily Three ───────────────────────────────────────────
     Decision fatigue is the enemy of a 35-KPI system. Three items, the
     same three every day, is what survives a bad week. Everything else
     in this app is optional on any given day. */
  var DAILY3 = [
    { id: "ex", label: "Move", floor: "Shoes on, one set. That counts." },
    { id: "mf", label: "Mind", floor: "Three cyclic sighs \u2014 breathe in through the nose, take a second short sip of air on top, then a long slow breath out. Ninety seconds." },
    { id: "fm", label: "Family", floor: "One real question, phone in the basket." }
  ];
  function daily3HTML(calm) {
    var done = (typeof todayChecks === "function") ? todayChecks() : [];
    var rec = inRecovery();
    var h = '<div style="background:linear-gradient(160deg,var(--navy),#152b47);border-radius:16px;padding:16px;margin-bottom:14px;color:#ece8dd">'
      + '<div style="font-size:10.5px;letter-spacing:1.4px;text-transform:uppercase;color:var(--gold);font-weight:800">'
      + (rec ? "Recovery mode \u00b7 these three only" : "The daily three \u00b7 non-negotiable") + '</div>'
      + '<div style="display:flex;gap:8px;margin-top:11px">';
    DAILY3.forEach(function (d) {
      var idx = -1;
      if (typeof HABITS !== "undefined") HABITS.forEach(function (hb, i) { if (hb.id === d.id) idx = i; });
      var on = done.indexOf(d.id) >= 0;
      h += '<div onclick="' + (idx >= 0 ? "tgHabit(" + idx + ")" : "") + '" style="flex:1;cursor:pointer;text-align:center;'
        + 'background:' + (on ? "var(--gold)" : "rgba(255,255,255,.07)") + ';color:' + (on ? "#0d1f35" : "#ece8dd") + ';'
        + 'border:1.5px solid ' + (on ? "var(--gold)" : "rgba(201,168,76,.35)") + ';border-radius:12px;padding:14px 6px">'
        + '<div style="font-size:22px;line-height:1">' + (on ? "\u2713" : "\u25cb") + '</div>'
        + '<div style="font-size:12.5px;font-weight:800;margin-top:5px">' + d.label + '</div>'
        + '<div style="font-size:9.5px;opacity:.75;margin-top:3px;line-height:1.35">' + esc(d.floor) + '</div></div>';
    });
    h += '</div>';
    var n = DAILY3.filter(function (d) { return done.indexOf(d.id) >= 0; }).length;
    h += '<div style="font-size:11px;color:#9fb3c8;margin-top:10px">'
      + (n === 3 ? "Done. Today is a win regardless of what else happens."
        : n === 0 ? "Do the smallest version. The floor counts as a full win \u2014 that is the whole trick."
          : n + " of 3. The floor counts.") + '</div>';
    // Calm mode: no strength bars before the first check-in (with no history they read as a scolding). The EMA itself always updates.
    if (!calm || Object.keys((typeof S !== "undefined" && S.daily) || {}).length) h += strengthHTML(); else emaUpdate();
    if (rec) {
      h += '<div style="font-size:11px;color:var(--gold);margin-top:8px">Cadence paused until ' + esc(rec.until.slice(0, 10))
        + '. Nothing is stacking up. <span style="text-decoration:underline;cursor:pointer" onclick="gmRecoveryOff()">End early</span></div>';
    }
    return h + '</div>';
  }

  /* ── 17. THE STACK — tiered, gated, one action at a time ───────────
     Modelled on how population-scale public infrastructure was actually
     sequenced: one thin mandatory layer, fully built, before the next
     one is allowed to depend on it. Identity before trust, trust before
     flow, flow before compounding. You are never choosing what to work
     on. The stack chooses. */
  var STACK = [
    {
      id: "L0", name: "Identity", why: "Nothing above this layer can be claimed, insured, inherited or proven without it. It is the cheapest layer and the one everyone skips.",
      items: [
        "Every family member has Aadhaar, and the birth certificate that backs it",
        "Marriage certificate registered",
        "Both property sale deeds in hand + encumbrance certificate pulled",
        "Passports, licences, degrees, vaccination records scanned into DigiLocker",
        "Password manager installed, every password unique and 16+ characters",
        "2FA on email, banking and broker \u2014 authenticator app, not SMS",
        "One separate email address used only for financial accounts"
      ]
    },
    {
      id: "L1", name: "Trust", why: "This layer decides whether one bad day becomes one bad decade. It is pure downside removal and it is worth more than any return you will earn above it.",
      items: [
        "Health cover: floater \u2265\u20b910L, no room-rent cap, no disease sub-limits, restoration benefit",
        "Super top-up \u20b950L\u20131Cr on top of the base cover",
        "Parents on a separate senior policy",
        "Pure term life at 10\u201312\u00d7 annual income plus outstanding debt \u2014 sum assured verified",
        "Personal accident cover \u2014 matters more than most realise if you commute on two wheels",
        "One month of expenses in instant-access savings",
        "Nominations correct on every single account, and aligned with the will",
        "Two registered wills with a guardianship clause"
      ]
    },
    {
      id: "L2", name: "Flow", why: "Automation beats discipline. Every rupee that requires a monthly decision is a rupee at risk. Once this layer is live, saving happens whether or not you are having a good month.",
      items: [
        "Auto-split standing instruction set for salary day + 1",
        "Credit cards verified at \u20b90 and never revolving",
        "Six months of expenses fully funded across the three liquidity buckets",
        "Every bill on auto-pay",
        "A single spending account \u2014 what is left in it is genuinely free to spend"
      ]
    },
    {
      id: "L3", name: "Compounding", why: "Only now. Investing before the Trust layer exists is not wealth-building; it is a bet that nothing goes wrong while you are exposed.",
      items: [
        "Index SIP running on auto-debit with an annual step-up",
        "Savings rate \u2265 20%",
        "Retirement corpus tracked against a target you have actually calculated",
        "Education corpus started for each child \u2014 assume 10% education inflation, not 6%",
        "One serious skill or certification every six months",
        "Half of every raise routed to investment before lifestyle sees it"
      ]
    },
    {
      id: "L4", name: "Optionality", why: "The layer everyone wants to start at. It only pays once the floor beneath it cannot collapse \u2014 otherwise a side venture is just concentrated risk with extra steps.",
      items: [
        "A second income stream that is live and has actually been paid",
        "Remote-capable: portfolio, writing samples, a track record that travels",
        "Network of 50 with real relationships, some outside your country",
        "Multi-currency banking arranged",
        "Second residency researched and the first step taken",
        "Venture reviewed quarterly rather than fantasised about weekly"
      ]
    }
  ];
  function stackState() { return G("gm_stack", {}); }
  window.gmStackTg = function (lid, i) {
    var st = stackState(); st[lid] = st[lid] || {}; st[lid][i] = !st[lid][i]; S_("gm_stack", st); renderAll();
  };
  function layerPct(L) {
    var st = stackState()[L.id] || {}, n = 0;
    L.items.forEach(function (_, i) { if (st[i] || autoTicked(L.id, i)) n++; });
    return Math.round(n / L.items.length * 100);
  }
  function theOneAction() {
    var i, j, L, st;
    for (i = 0; i < STACK.length; i++) {            // vital few first
      L = STACK[i]; st = stackState()[L.id] || {};
      for (j = 0; j < L.items.length; j++) if (!st[j] && !autoTicked(L.id, j) && isVital(L.id, j)) return { layer: L, idx: j, text: L.items[j], vital: true };
    }
    for (i = 0; i < STACK.length; i++) {
      L = STACK[i]; st = stackState()[L.id] || {};
      for (j = 0; j < L.items.length; j++) if (!st[j] && !autoTicked(L.id, j)) return { layer: L, idx: j, text: L.items[j] };
    }
    return null;
  }
  function oneActionHTML() {
    var a = theOneAction();
    if (!a) return '<div class="info">Every layer of the stack is complete. Maintenance mode: run the cadence, hold the line.</div>';
    return '<div style="background:var(--card);border:2px solid var(--gold);border-radius:14px;padding:15px;margin-bottom:14px">'
      + '<div style="font-size:10.5px;letter-spacing:1.3px;text-transform:uppercase;color:var(--gold);font-weight:800">Your one open action \u00b7 ' + a.layer.id + ' ' + a.layer.name + (a.vital ? ' \u00b7 \u2605 vital few' : '') + '</div>'
      + '<div style="font-size:15px;font-weight:700;line-height:1.5;margin:8px 0 4px;color:var(--text)">' + esc(a.text) + '</div>'
      + '<div style="font-size:11.5px;color:var(--muted);line-height:1.6">Rule 1 says one in-progress action at a time. This is it. Nothing below this layer is finished, so nothing above it is yours to work on yet.</div>'
      + '<button class="btn btn-p" style="margin-top:10px" onclick="gmStackTg(\'' + a.layer.id + '\',' + a.idx + ')">Mark this done</button></div>';
  }
  function stackHTML() {
    var h = '<div class="section active">';
    h += '<div class="cat-t">\u{1F3DB} The stack</div>'
      + '<div class="info">Five layers. Each one is only allowed to depend on the layers below it, and you only work on the lowest unfinished item in the whole stack. '
      + 'This is the single most important change in this version: it removes the decision about what to do next, which is where systems like this usually die.</div>';
    var vOnly = G("gm_vitalonly", false);
    h += '<div style="display:flex;gap:8px;margin-bottom:12px"><button class="btn-sm" style="flex:1;background:'
      + (vOnly ? "var(--gold);color:#0d1f35" : "var(--cardAlt);color:var(--text)")
      + '" onclick="gmVitalOnly()">' + (vOnly ? "\u2605 Showing the vital few only" : "\u2606 Show only the vital few (80/20)") + '</button></div>';
    h += oneActionHTML();
    STACK.forEach(function (L, li) {
      var pct = layerPct(L), st = stackState()[L.id] || {};
      var prevDone = li === 0 || layerPct(STACK[li - 1]) === 100;
      var col = pct === 100 ? "var(--green)" : prevDone ? "var(--gold)" : "var(--muted)";
      h += '<details class="road-col" style="margin-bottom:10px;border-left:4px solid ' + col + '">'
        + '<summary style="cursor:pointer;font-weight:800;font-size:13.5px">' + L.id + ' \u00b7 ' + esc(L.name)
        + ' <span style="float:right;color:' + col + '">' + pct + '%</span></summary>'
        + '<div class="road-i" style="margin:8px 0 10px;font-style:italic">' + esc(L.why) + '</div>';
      if (!prevDone) h += '<div class="info" style="margin-bottom:8px">Locked by design. Finish ' + STACK[li - 1].id + ' first \u2014 this layer is not safe to stand on until it is.</div>';
      L.items.forEach(function (it, i) {
        if (vOnly && !isVital(L.id, i)) return;
        var auto = autoTicked(L.id, i);
        if (auto && !st[i]) {
          h += '<div class="road-i" style="display:flex;gap:8px;align-items:flex-start;padding:5px 0" title="' + esc(auto) + '">'
            + '<span style="color:var(--green);font-weight:800">\u2611</span>'
            + '<span style="opacity:.75">' + (isVital(L.id, i) ? '<span style="color:var(--gold)">\u2605 </span>' : "") + esc(it)
            + '<br><span style="color:var(--muted);font-size:10.5px">\u2699 ' + esc(auto) + '</span></span></div>';
          return;
        }
        h += '<div class="road-i" style="cursor:pointer;display:flex;gap:8px;align-items:flex-start;padding:5px 0" onclick="gmStackTg(\'' + L.id + '\',' + i + ')">'
          + '<span style="color:' + (st[i] ? "var(--green)" : "var(--muted)") + ';font-weight:800">' + (st[i] ? "\u2611" : "\u2610") + '</span>'
          + '<span style="' + (st[i] ? "opacity:.5;text-decoration:line-through" : "") + '">' + (isVital(L.id, i) ? '<span title="vital few" style="color:var(--gold)">\u2605 </span>' : "") + esc(it) + horizonTag(it) + '</span></div>';
      });
      h += '</details>';
    });
    h += '</div>';
    return h;
  }

  /* ── 18. THE LIFE MAP — age-driven benchmarks for the whole household */
  function life() { return G("gm_life", {}); }
  window.gmLifeSet = function (k, v) {
    var l = life(); l[k] = v; S_("gm_life", l);
    gmClearExample(k);      // you typed it, so it is yours now
    bustDerived(); renderAll();
  };
  function num(v) {
    // Keep a leading minus. Stripping it turned a negative net worth positive.
    var t = String(v).trim(), neg = /^-/.test(t);
    var n = parseFloat(t.replace(/[^0-9.]/g, ""));
    if (isNaN(n)) return 0;
    return neg ? -n : n;
  }

  // A "lakh" field typed in rupees (4,00,000 instead of 4) made runway read 274219.5 months on a real phone. Treat > 10,000 as rupees.
  function lakhs(v) { var n = num(v); return n > 10000 ? n / 1e5 : n; }

  function lifeInputs() {
    var l = life();
    var F = [
      ["age", "Your age", "36"], ["sage", "Spouse age", "33"],
      ["inc", "Household annual income (\u20b9 lakh)", "23"],
      ["nw", "Net worth excl. own home (\u20b9 lakh)", "12"],
      ["k1", "First child's age in years (0 if infant, blank if none)", "1"],
      ["page", "Eldest parent's age", "68"], ["edu", "Degree you are planning for, at today's cost (\u20b9 lakh)", "25"], ["ef", "Emergency fund balance today (\u20b9 lakh)", "4"]
    ];
    var filled = num(l.age) && num(l.inc);
    var h = '<details class="road-col" ' + (filled ? "" : "open") + '><summary style="cursor:pointer;font-weight:800;font-size:13px">Your numbers'
      + (filled ? ' \u00b7 <span style="font-weight:500;color:var(--muted)">tap to edit</span>' : '') + '</summary>'
      + (filled ? "" : tplBtn("gmTplLife()", "Fill with a worked example, then correct it"));
    F.forEach(function (f) {
      h += '<label class="f-label">' + f[1] + exampleBadge(f[0]) + '</label><input inputmode="decimal" value="' + esc(l[f[0]] === undefined ? "" : l[f[0]])
        + '" placeholder="' + f[2] + '" onchange="gmLifeSet(\'' + f[0] + '\',this.value)">'
        + saneWarn(f[0], l[f[0]]);
    });
    return h + '</details>';
  }

  function band(actual, target) {
    if (!target) return ["\u2014", "var(--muted)"];
    var r = actual / target;
    if (r >= 1) return ["Ahead", "var(--green)"];
    if (r >= 0.6) return ["On track", "var(--amber)"];
    return ["Catching up", "var(--red)"];
  }

  function lifeMapHTML() {
    var l = life(), age = num(l.age), inc = num(l.inc), nw = num(l.nw), sage = num(l.sage), k1 = l.k1 === "" || l.k1 === undefined ? null : num(l.k1), page = num(l.page);
    var h = '<div class="section active"><div class="cat-t">\u{1F9ED} Life map</div>'
      + '<div class="info">Benchmarks, not verdicts. Where you are behind, the map gives you the action \u2014 not a score to feel bad about. '
      + 'Starting late is normal and is not disqualifying; the arithmetic simply gets less forgiving, so the response is a higher savings rate, not despair.</div>';
    h += exampleWarn();
    h += lifeInputs();
    if (!age || !inc) { h += '<div class="info" style="margin-top:12px">Enter at least your age and household income to generate the map.</div></div>'; return h; }

    /* Net worth multiple — the widely used age benchmark, shifted later
       for Indian earning curves where income peaks in the 40s. */
    var mult = age < 30 ? 0.5 : age < 35 ? 1 : age < 40 ? 2 : age < 45 ? 3 : age < 50 ? 4.5 : age < 55 ? 6 : age < 60 ? 8 : 10;
    var nwTarget = Math.round(mult * inc), b = band(nw, nwTarget);
    h += '<div class="cat-t" style="margin-top:16px">You \u00b7 age ' + age + '</div><div class="road-col">'
      + '<div class="road-h">Net worth <span style="float:right;color:' + b[1] + '">' + b[0] + '</span></div>'
      + '<div class="road-i">Benchmark at ' + age + ': <b>' + mult + '\u00d7</b> annual income = <b>\u20b9' + nwTarget + 'L</b> (excluding the home you live in). You have \u20b9' + nw + 'L.</div>'
      + (nw < nwTarget * 0.6
        ? '<div class="road-i" style="color:var(--red)">Behind the band. The only lever that closes this reliably is the savings rate, not returns. Raise the auto-split by 1% every month that felt comfortable, and route half of every raise before lifestyle absorbs it.</div>'
        : '<div class="road-i" style="color:var(--green)">Inside the band. Hold the savings rate and let time do the rest.</div>')
      + '<div class="road-i">Term cover should be <b>\u20b9' + Math.round(inc * 11) + 'L</b> minimum \u2014 11\u00d7 income \u2014 plus every outstanding loan on top.</div>'
      + '<div class="road-i">By 40 the four things that should exist: full six-month buffer, term + health cover in force, a registered will, and an investment that runs without you touching it.</div>'
      + '</div>';

    /* Spouse */
    if (sage) {
      h += '<div class="cat-t" style="margin-top:14px">Spouse \u00b7 age ' + sage + '</div><div class="road-col">'
        + '<div class="road-i">Independent term cover in her own name if she earns \u2014 household cover is not a substitute.</div>'
        + '<div class="road-i">Her own credit history: one card in her name, used and cleared monthly. This matters enormously and only takes months to build, never on the day it is needed.</div>'
        + '<div class="road-i">Her own emergency access: a bank account she alone controls, plus emergency access to the password manager.</div>'
        + '<div class="road-i">Her own retirement instrument \u2014 PPF or NPS \u2014 running in her name, not merged into yours.</div>'
        + '<div class="road-i">She can run the annual review without you. If not, that is the highest-value gap in this entire system.</div>'
        + '</div>';
    }

    /* Children */
    if (k1 !== null) {
      var eduYears = Math.max(1, 18 - k1);
      var eduToday = num(l.edu) || 25; // \u20b9L, a professional degree at today's prices
      var eduFuture = Math.round(eduToday * Math.pow(1.10, eduYears));
      // FV of a monthly SIP: FV = P * [((1+i)^n - 1)/i] * (1+i)
      var i12 = 0.12 / 12, n = eduYears * 12;
      var sip = Math.round((eduFuture * 100000) / (((Math.pow(1 + i12, n) - 1) / i12) * (1 + i12)));
      h += '<div class="cat-t" style="margin-top:14px">Children</div><div class="road-col">'
        + '<div class="road-i">A professional degree costing <b>\u20b925L today</b> will cost roughly <b>\u20b9' + eduFuture + 'L</b> in ' + eduYears + ' years. '
        + 'Education inflation in Indian private and professional institutions runs at 10\u201312%, not the 6% most calculators default to \u2014 planning at 6% is how a corpus ends up 40% short on the day fees are due.</div>'
        + '<div class="road-i">Starting today at 12% returns, that needs about <b>\u20b9' + sip.toLocaleString("en-IN") + ' a month</b>, stepped up 10% a year. Every year of delay raises this by roughly 10\u201315%.</div>'
        + '<div class="road-i">Keep the education corpus separate from retirement. Retirement cannot be borrowed for; education can.</div>'
        + '</div>';

      /* Second child */
      var okSpacing = k1 >= 2;
      h += '<div class="cat-t" style="margin-top:14px">A second child \u2014 the readiness test</div><div class="road-col">'
        + '<div class="road-i"><b>Biological window.</b> The WHO recommendation is at least 24 months from a live birth to the next conception; ACOG frames it as at least 18 months and under five years. '
        + 'Your first child is ' + k1 + '. <b style="color:' + (okSpacing ? "var(--green)" : "var(--amber)") + '">' + (okSpacing ? "Inside the recommended window." : "Below 24 months \u2014 the guideline says wait.") + '</b> This is a doctor\u2019s decision, not an app\u2019s; the app only holds the guideline where you can see it.</div>'
        + '<div class="road-i"><b>Financial readiness \u2014 all five, not three of five:</b></div>'
        + '<div class="road-i">\u2610 Six-month emergency fund fully funded, at the higher expense level a second child creates</div>'
        + '<div class="road-i">\u2610 Term cover re-run at the new number, and the will updated with the guardianship clause covering both children</div>'
        + '<div class="road-i">\u2610 Education SIP for the first child already running and never paused</div>'
        + '<div class="road-i">\u2610 Monthly surplus of at least <b>\u20b920\u201330k</b> above current commitments \u2014 a metro upbringing to 21 runs \u20b980L\u20131.5Cr per child at 2026 prices, which is roughly this much a month for two decades</div>'
        + '<div class="road-i">\u2610 Health floater raised, with the maternity waiting period already served</div>'
        + '<div class="road-i" style="font-style:italic;color:var(--muted)">The honest version: people have second children happily without any of this. What the checklist buys is that the second child does not compete with the first for the same rupee.</div>'
        + '</div>';
    }

    /* Parents */
    if (page) {
      h += '<div class="cat-t" style="margin-top:14px">Parents \u00b7 eldest ' + page + '</div><div class="road-col">'
        + '<div class="road-i">' + (page >= 70
          ? "Past 70, fresh health cover is expensive and heavily restricted. If they are not already covered, this is urgent and moves ahead of almost everything else in the stack."
          : "Under 70 \u2014 get the senior policy in force now, while it is still cheap and while waiting periods can be served before they are needed.") + '</div>'
        + '<div class="road-i">Their nominations and their own will: the single most common cause of families losing assets is not fraud, it is an unnamed nominee.</div>'
        + '<div class="road-i">One page, in the house, listing their conditions, medicines, doctors, blood groups and insurance numbers. Photograph it.</div>'
        + '<div class="road-i">A conversation about what they want if they cannot decide for themselves. It is a bad conversation to have once and a far worse one to have never.</div>'
        + '</div>';
    }

    h += '<div style="margin-top:18px">' + flowHTML() + '</div>';
    h += '<div class="info" style="margin-top:14px">These are population benchmarks. They are useful as a compass and useless as a judgement \u2014 someone starting at 36 with nothing, who saves 30% consistently, ends up ahead of someone who started at 25 and stopped.</div>';
    return h + '</div>';
  }

  /* ── 19. FRICTION — the decision-fatigue layer ────────────────────── */
  var FRICTION = [
    ["\u{1F455} Clothes", [
      "Pick one work uniform and buy five of it. Same shirt, same trousers, same shoes. Nobody notices, and you get ten minutes and one decision back daily.",
      "Weekend uniform: two outfits, on rotation.",
      "Everything for tomorrow laid out the night before, in one place.",
      "One in, one out. A new shirt means a shirt leaves."
    ]],
    ["\u{1F35B} Food", [
      "Same breakfast every weekday. Decide it once.",
      "Same lunch, or a two-item rotation.",
      "Seven fixed dinners, one per weekday, repeating. Sunday is the only day you choose.",
      "Sunday: one shop, one prep session, containers filled. The week's food decisions are now zero.",
      "Water bottle filled and placed where you will walk past it."
    ]],
    ["\u{1F6AA} Space", [
      "A launchpad by the door: keys, wallet, badge, bag, charger. Everything leaves from there and returns there.",
      "One-touch rule: when you pick something up, it goes where it belongs, not down somewhere else.",
      "The 90/90 rule: not used in the last 90 days and not needed in the next 90? It goes.",
      "Every object has one home. If you have to think about where something lives, it does not have a home yet.",
      "Twenty minutes every Sunday: reset the flat to its default state."
    ]],
    ["\u{1F4F1} Digital", [
      "Notifications off for everything except calls and messages from named people.",
      "Home screen holds only apps you use daily. Everything else lives in search.",
      "One inbox, one task list, one notes app. Not three of each.",
      "Phone charges outside the bedroom. This one habit fixes more than any sleep tracker.",
      "Greyscale after 10pm.",
      "Unsubscribe on sight rather than delete on sight."
    ]],
    ["\u{1F4B8} Money", [
      "Every bill on auto-pay, every transfer automated for salary day + 1.",
      "One spending account. Whatever is in it is genuinely free to spend, with no calculation required.",
      "A 24-hour rule above \u20b95,000 and a 30-day list above \u20b925,000. Most wants do not survive either.",
      "Cards out of the wallet if they revolve. Not cut up \u2014 just not carried."
    ]],
    ["\u{1F9E0} Decisions", [
      "Decide once, not daily. Any decision you make more than twice should become a rule.",
      "Two-minute rule: if it takes under two minutes, it happens now.",
      "Default answer to new commitments is no, said kindly, unless it is an obvious yes.",
      "Batch anything similar: all calls in one block, all errands in one trip.",
      "Reduce the number of times a day you consult your own preferences. That is the actual definition of a free day."
    ]]
  ];
  function frictionHTML() {
    var st = G("gm_friction", {});
    var tot = 0, done = 0;
    FRICTION.forEach(function (g, gi) { g[1].forEach(function (_, i) { tot++; if ((st[gi] || {})[i]) done++; }); });
    var h = '<div class="cat-t">\u{1F9F9} Friction removal <span class="pill pill-g">' + done + '/' + tot + '</span></div>'
      + '<div class="info">Every item here removes a decision permanently. This is the highest-leverage page in the app and the least impressive-looking: '
      + 'you cannot run a 35-KPI life system while also deciding what to wear and what to eat. Do one row a week.</div>';
    FRICTION.forEach(function (g, gi) {
      h += '<details class="road-col" style="margin-bottom:8px"><summary style="cursor:pointer;font-weight:800;font-size:12.5px">' + g[0] + '</summary><div style="margin-top:6px">';
      g[1].forEach(function (it, i) {
        var on = (st[gi] || {})[i];
        h += '<div class="road-i" style="cursor:pointer;display:flex;gap:8px;padding:4px 0" onclick="gmFrTg(' + gi + ',' + i + ')">'
          + '<span style="color:' + (on ? "var(--green)" : "var(--muted)") + ';font-weight:800">' + (on ? "\u2611" : "\u2610") + '</span>'
          + '<span style="' + (on ? "opacity:.5;text-decoration:line-through" : "") + '">' + esc(it) + '</span></div>';
      });
      h += '</div></details>';
    });
    return h;
  }
  window.gmFrTg = function (gi, i) {
    var st = G("gm_friction", {}); st[gi] = st[gi] || {}; st[gi][i] = !st[gi][i]; S_("gm_friction", st); renderAll();
  };

  /* ── 20. Commitment device + honest limits ────────────────────────── */
  function commitHTML() {
    var c = G("gm_commit", {});
    return '<div class="cat-t">\u{1F91D} Commitment device</div>'
      + '<div class="info">Systems held only by private intention fail quietly, because nobody notices. '
      + 'One named person who expects a one-line message on the first Sunday of the month is worth more than every feature in this app.</div>'
      + (c.who ? "" : tplBtn("gmTplCommit()", "Start from a worked example"))
      + '<div class="road-col">'
      + '<label class="f-label">Who gets your monthly one-liner?</label>'
      + '<input value="' + esc(c.who || "") + '" placeholder="A name \u2014 not \u201csomeone\u201d" onchange="gmCommitSet(\'who\',this.value)">'
      + '<label class="f-label">What happens if you miss two months running?</label>'
      + '<input value="' + esc(c.stake || "") + '" placeholder="A real, small, specific consequence you would rather avoid" onchange="gmCommitSet(\'stake\',this.value)">'
      + '<div class="road-i" style="margin-top:8px;font-style:italic;color:var(--muted)">Make the stake small and certain rather than large and theatrical. Large stakes get renegotiated; small ones get paid.</div>'
      + '</div>'
      + '<div class="cat-t" style="margin-top:16px">\u{1F3F3} When it goes wrong</div>'
      + '<div class="info">It will. Illness, a crisis at work, a bad month. The system does not fail then \u2014 it fails in the week after, when you decide it is broken and stop opening it. '
      + 'Recovery mode exists for exactly that week: it pauses every ritual, keeps only the daily three, and lets nothing accumulate against you.</div>'
      + recoveryHTML();
  }
  window.gmCommitSet = function (k, v) { var c = G("gm_commit", {}); c[k] = v; S_("gm_commit", c); renderAll(); };


  /* ═══════════════════════════════════════════════════════════════
     v6 — PROPERTY ECONOMICS · MONEY FLOW · THE KIT · UI FIXES
     ═══════════════════════════════════════════════════════════════ */

  /* ── 21. PROPERTY ECONOMICS ────────────────────────────────────────
     Seven numbers per property. Everything below is derived — no
     spreadsheet, no annual guesswork about whether a flat is actually
     earning its keep. */
  function props() { return G("gm_props", []); }
  window.gmPropAdd = function () {
    var p = props(); p.push({ n: "Property " + (p.length + 1), use: "letout", val: "", rent: "", loan: "", rate: "", emi: "", out: "", vac: "1" });
    S_("gm_props", p); renderAll();
  };
  window.gmPropDel = function (i) {
    var p = props();
    gmSnap("removed the property \u201c" + ((p[i] && p[i].n) || "untitled") + "\u201d");
    p.splice(i, 1); S_("gm_props", p); renderAll();
  };
  window.gmPropSet = function (i, k, v) { var p = props(); p[i][k] = v; S_("gm_props", p); renderAll(); };

  function propCalc(p) {
    var val = num(p.val) * 100000,           // \u20b9 lakh -> \u20b9
      rent = num(p.rent),                    // \u20b9/month
      loan = num(p.loan) * 100000,
      rate = num(p.rate) / 100,
      emi = num(p.emi),
      out = num(p.out),                      // \u20b9/yr: society + property tax + repairs
      vacM = Math.min(12, Math.max(0, num(p.vac)));  // clamp: 13 made annual rent negative
    var grossAnnual = rent * 12;
    var effAnnual = rent * (12 - vacM);
    var netAnnual = effAnnual - out;
    var interest = loan * rate;              // approx first-year interest
    var r = {
      grossYield: val ? grossAnnual / val * 100 : 0,
      netYield: val ? netAnnual / val * 100 : 0,
      priceToRent: grossAnnual ? val / grossAnnual : 0,
      ltv: val ? loan / val * 100 : 0,
      dscr: emi ? effAnnual / (emi * 12) : 0,
      debtToRent: grossAnnual ? loan / grossAnnual : 0,
      beOcc: rent ? (emi * 12 + out) / (rent * 12) * 100 : 0,
      cashflow: rent - emi - out / 12,
      interest: interest,
      equity: val - loan
    };
    // Tax: let-out. NAV = rent less municipal tax; 30% standard deduction; interest fully deductible.
    var muni = out * 0.25; // rough split of the outgo that is municipal tax
    var nav = effAnnual - muni;
    r.hpIncome = nav - (nav * 0.30) - interest;
    r.loss = r.hpIncome < 0 ? -r.hpIncome : 0;
    r.setOffUsable = Math.min(r.loss, 200000);
    r.carryForward = Math.max(0, r.loss - 200000);
    r.taxShield = r.setOffUsable * 0.30;     // at a 30% slab, old regime
    r.effRate = loan ? (interest - r.taxShield) / loan * 100 : 0;
    return r;
  }

  function verdict(r, p) {
    var out = [];
    if (r.netYield && r.netYield < 2.5) out.push(["Yield is thin", "var(--red)",
      "Net yield under 2.5% means the flat is a leveraged bet on price appreciation, not an income asset. That is a legitimate position \u2014 but hold it deliberately, not by accident."]);
    else if (r.netYield >= 3.5) out.push(["Yield is healthy for India", "var(--green)",
      "Indian residential net yields cluster around 2\u20133%. Above 3.5% is genuinely good."]);
    if (r.dscr && r.dscr < 1) out.push(["Rent does not cover the EMI", "var(--amber)",
      "Every month you are topping up from salary. That is fine while the shortfall is small and the interest is tax-shielded \u2014 dangerous the moment income stops."]);
    if (r.beOcc > 100) out.push(["Break-even occupancy above 100%", "var(--red)",
      "Even fully let, the property does not pay for itself. Raise the rent to market, cut the outgo, or plan an exit."]);
    else if (r.beOcc > 85) out.push(["Break-even occupancy is tight", "var(--amber)",
      "Two vacant months turn the year negative. Keep a dedicated buffer of two EMIs for this flat alone."]);
    if (r.debtToRent > 12) out.push(["Debt is heavy against rent", "var(--amber)",
      Math.round(r.debtToRent) + " years of gross rent would be needed to clear the loan. Above 12 is leverage doing the work, not the asset."]);
    if (r.carryForward > 0) out.push(["Loss above the \u20b92L set-off cap", "var(--amber)",
      "\u20b9" + Math.round(r.carryForward).toLocaleString("en-IN") + " cannot be set off against salary this year. It carries forward eight years and only ever offsets future house-property income."]);
    if (!out.length) out.push(["Nothing structurally wrong", "var(--green)", "The numbers hold up. Re-benchmark the rent annually and leave it alone."]);
    return out;
  }

  function fmtL(x) { return "\u20b9" + (Math.round(x / 1000) / 100).toFixed(2) + "L"; }
  function propHTML() {
    var P = props();
    var h = '<div class="section active"><div class="cat-t">\u{1F3E0} Property economics</div>'
      + '<div class="info">Seven numbers per flat. Everything else is calculated. '
      + 'The question a let-out property has to answer is not \u201chas the price gone up\u201d \u2014 it is whether the rent, after every cost and after tax, beats what the same money would do sitting in an index fund.</div>';
    if (!P.length) h += '<div class="info">Nothing added yet. Start from the worked example and overwrite the numbers \u2014 correcting something wrong is far quicker than filling something blank.</div>'
      + tplBtn("gmTplProp()", "Start from a worked example");
    P.forEach(function (p, i) {
      var r = propCalc(p), v = verdict(r, p);
      h += '<label class="f-label">How is this property used?</label><div style="display:flex;gap:6px;margin-bottom:8px">'
        + [["letout", "Let out to a tenant"], ["self", "We live in it"]].map(function (o) {
          var on = (p.use || "letout") === o[0];
          return '<button class="btn-sm" style="flex:1;background:' + (on ? "var(--gold);color:#0d1f35" : "var(--cardAlt);color:var(--text)")
            + '" onclick="gmPropSet(' + i + ',\'use\',\'' + o[0] + '\')">' + o[1] + '</button>';
        }).join("") + '</div>';
      var F = [["n", "Name", "Rental flat A"], ["val", "Current market value (\u20b9 lakh)", "75"],
      ["rent", "Monthly rent received (\u20b9)", "18000"], ["loan", "Outstanding loan (\u20b9 lakh)", "32"],
      ["rate", "Interest rate (%)", "7.25"], ["emi", "Monthly EMI (\u20b9)", "26000"],
      ["out", "Annual outgo \u2014 society + property tax + repairs (\u20b9)", "48000"],
      ["vac", "Vacant months per year (realistic, not hoped-for)", "1"]];
      h += '<details class="road-col" style="margin-bottom:12px" ' + (i === 0 ? "open" : "") + '>'
        + '<summary style="cursor:pointer;font-weight:800;font-size:13.5px">' + esc(p.n || "Property")
        + '<span style="float:right;color:' + (r.cashflow >= 0 ? "var(--green)" : "var(--amber)") + '">'
        + (r.cashflow >= 0 ? "+" : "") + Math.round(r.cashflow).toLocaleString("en-IN") + "/mo</span></summary>";
      h += '<div style="margin-top:8px">';
      F.forEach(function (f) {
        h += '<label class="f-label">' + f[1] + '</label><input ' + (f[0] === "n" ? "" : 'inputmode="decimal"')
          + ' value="' + esc(p[f[0]] || "") + '" placeholder="' + f[2] + '" onchange="gmPropSet(' + i + ',\'' + f[0] + '\',this.value)">';
      });
      if (num(p.val) && num(p.rent)) {
        var rows = [
          ["Gross rental yield", r.grossYield.toFixed(2) + "%", "Annual rent \u00f7 market value. India typically 2\u20133%."],
          ["Net rental yield", r.netYield.toFixed(2) + "%", "After outgo and realistic vacancy. This is the number that matters."],
          ["Price-to-rent", r.priceToRent.toFixed(0) + " yrs", "Years of gross rent to equal the price. Above 30 favours renting over owning."],
          ["Rent-to-EMI cover", r.dscr.toFixed(2) + "\u00d7", "Also called DSCR. Above 1.0 the tenant covers the EMI; below 1.0 you top it up from salary every month."],
          ["Debt-to-rental-income", r.debtToRent.toFixed(1) + " yrs", "Outstanding loan \u00f7 annual rent."],
          ["Loan-to-value", r.ltv.toFixed(0) + "%", "Leverage remaining on the asset."],
          ["Break-even occupancy", r.beOcc.toFixed(0) + "%", "Share of the year that must be let just to stand still."],
          ["Monthly cash flow", "\u20b9" + Math.round(r.cashflow).toLocaleString("en-IN"), "Rent less EMI less monthly share of outgo."],
          ["Equity in the asset", fmtL(r.equity), "Value less outstanding loan."],
          ["Taxable house-property income", "\u20b9" + Math.round(r.hpIncome).toLocaleString("en-IN"), "Rent less municipal tax, less 30% standard deduction, less full interest."],
          ["Usable set-off this year", "\u20b9" + Math.round(r.setOffUsable).toLocaleString("en-IN"), "Capped at \u20b92L against salary under the old regime; nil under the new."],
          ["Effective interest after tax shield", r.effRate.toFixed(2) + "%", "What the loan actually costs you once the deduction is counted."]
        ];
        h += '<div style="margin-top:12px">';
        rows.forEach(function (x) {
          h += '<div style="display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid var(--border)">'
            + '<div style="flex:1"><div style="font-size:12.5px;font-weight:700;color:var(--text)">' + x[0] + '</div>'
            + '<div style="font-size:10.5px;color:var(--muted);line-height:1.4">' + x[2] + '</div></div>'
            + '<div style="font-size:14px;font-weight:800;color:var(--text);white-space:nowrap">' + x[1] + '</div></div>';
        });
        h += '</div><div style="margin-top:10px">';
        v.forEach(function (x) {
          h += '<div style="border-left:3px solid ' + x[1] + ';padding:6px 0 6px 9px;margin-bottom:7px">'
            + '<div style="font-size:12.5px;font-weight:800;color:' + x[1] + '">' + x[0] + '</div>'
            + '<div style="font-size:11.5px;color:var(--text);line-height:1.6">' + x[2] + '</div></div>';
        });
        h += '</div>';
      }
      h += '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text);margin-top:8px" onclick="gmPropDel(' + i + ')">Remove this property</button>';
      h += '</div></details>';
    });
    h += '<button class="btn btn-p" onclick="gmPropAdd()">Add a property</button>';
    h += '<div class="cat-t" style="margin-top:18px">\u{1F4CC} The correction worth knowing</div>'
      + '<div class="info">Your playbook records the let-out interest deduction as \u201cuncapped, therefore effective rate ~5%\u201d. Half of that is right. '
      + 'The <b>deduction</b> is uncapped for a let-out property \u2014 but the resulting <b>loss you can set off against salary</b> is capped at \u20b92 lakh a year under section 71(3A), '
      + 'with the excess carried forward eight years and usable only against future house-property income. Under the new regime that inter-head set-off is nil. '
      + 'So the effective-rate maths above holds only while your annual loss stays under \u20b92L and you remain in the old regime. '
      + 'The calculator now shows you the moment you cross that line. Worth putting to your CA alongside the clubbing question.</div>';
    h += '<div class="cat-t" style="margin-top:14px">Annual rent discipline</div><div class="road-col">'
      + '<div class="road-i">Benchmark against three live listings for a comparable flat, every August. Rent that never rises is a slow, silent pay cut.</div>'
      + '<div class="road-i">A written 11-month agreement, registered, with a clear escalation clause. Verbal comfort is not a contract.</div>'
      + '<div class="road-i">Deposit held at two to three months, returned by bank transfer with a signed handover note.</div>'
      + '<div class="road-i">Two EMIs held in a dedicated buffer for this flat. Vacancy is the risk that actually shows up.</div>'
      + '<div class="road-i">Landlord PAN, rent receipts and the bank trail kept clean \u2014 this is the paperwork that decides an assessment.</div>'
      + '</div>';
    return h + '</div>';
  }

  /* ── 22. MONEY FLOW — a Sankey you can read in three seconds ────── */
  function flowHTML() {
    var l = life(), inc = num(l.minc);
    if (!inc) {
      return '<div class="cat-t">\u{1F4B8} Where the money goes</div>'
        + '<div class="info">Add your monthly take-home and the four standing outflows to draw the flow. Five numbers, once.</div>'
        + '<div class="road-col">'
        + '<label class="f-label">Monthly take-home (\u20b9)</label><input inputmode="decimal" value="" onchange="gmLifeSet(\'minc\',this.value)">'
        + '</div>';
    }
    var parts = [
      ["Fixed costs", num(l.fFixed), "#6b7280"],
      ["Family loans", num(l.fLoan), "#b45309"],
      ["Emergency fund", num(l.fEF), "#0f766e"],
      ["Investing", num(l.fSip), "#2e9969"]
    ];
    var used = parts.reduce(function (a, b) { return a + b[1]; }, 0);
    var free = Math.max(0, inc - used);
    parts.push(["Guilt-free", free, "#6d28d9"]);

    var W = 320, H = 200, x0 = 4, x1 = 108, x2 = 196;
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto;overflow:visible">';
    svg += '<rect x="' + x0 + '" y="10" width="16" height="' + (H - 20) + '" rx="3" fill="#c9a84c"/>';
    var y = 10;
    parts.forEach(function (p) {
      var hgt = inc ? (p[1] / inc) * (H - 20) : 0;
      if (hgt < 0.5) return;
      var yc = y + hgt / 2, ty = y + hgt / 2;
      svg += '<path d="M' + (x0 + 16) + ',' + yc + ' C' + ((x0 + x1) / 2) + ',' + yc + ' ' + ((x0 + x1) / 2) + ',' + ty + ' ' + x1 + ',' + ty + '" '
        + 'stroke="' + p[2] + '" stroke-width="' + Math.max(2, hgt) + '" fill="none" opacity=".55" stroke-linecap="butt"/>';
      svg += '<rect x="' + x1 + '" y="' + (ty - hgt / 2) + '" width="10" height="' + Math.max(2, hgt) + '" rx="2" fill="' + p[2] + '"/>';
      svg += '<text x="' + x2 + '" y="' + (ty + 3) + '" font-size="9.5" font-weight="700" fill="currentColor">' + esc(p[0])
        + ' \u00b7 ' + (inc ? Math.round(p[1] / inc * 100) : 0) + '%</text>';
      y += hgt;
    });
    svg += '</svg>';

    var savRate = inc ? Math.round((num(l.fEF) + num(l.fSip)) / inc * 100) : 0;
    var fixPct = inc ? Math.round(num(l.fFixed) / inc * 100) : 0;
    var freePct = inc ? Math.round(free / inc * 100) : 0;
    var F = [["fFixed", "Fixed costs \u2014 rent, EMIs, bills, groceries (\u20b9)"], ["fLoan", "Family loan repayment (\u20b9)"],
    ["fEF", "To emergency fund (\u20b9)"], ["fSip", "To SIP / investments (\u20b9)"], ["minc", "Monthly take-home (\u20b9)"]];
    var h = '<div class="cat-t">\u{1F4B8} Where the money goes</div>'
      + '<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px;color:var(--text)">' + svg + '</div>';
    h += '<div class="road-col" style="margin-top:10px">'
      + '<div class="road-i">Fixed costs <b>' + fixPct + '%</b> \u2014 healthy band 50\u201360%. ' + (fixPct > 60 ? "Above the band; this is the number that quietly caps everything else." : "Inside the band.") + '</div>'
      + '<div class="road-i">Saving and investing <b>' + savRate + '%</b> \u2014 target 15\u201320% minimum, and this is the single number that determines when you stop needing a salary.</div>'
      + '<div class="road-i">Guilt-free <b>' + freePct + '%</b> \u2014 healthy band 20\u201335%. Under 10% is how budgets get abandoned; a plan with no pleasure in it does not survive a year.</div>'
      + '</div>';
    h += '<details class="road-col" style="margin-top:8px"><summary style="cursor:pointer;font-weight:700;font-size:12px">Edit the numbers</summary><div style="margin-top:6px">';
    F.forEach(function (f) {
      h += '<label class="f-label">' + f[1] + exampleBadge(f[0]) + '</label><input inputmode="decimal" value="' + esc(l[f[0]] || "")
        + '" onchange="gmLifeSet(\'' + f[0] + '\',this.value)">' + saneWarn(f[0], l[f[0]]);
    });
    return h + '</div></details>';
  }

  /* ── 23. THE KIT — decided once, so it is never researched again ─── */
  var KIT = [
    ["\u{1F3CB} Strength, at home", [
      ["Adjustable dumbbells, 2\u00d724kg", "\u20b910\u201317k", "One pair replaces a rack. 24kg per hand carries two to three years of progression; 16kg caps out inside a year, which is the most common expensive mistake.", "Decathlon for try-before-buy, Amazon for the dial-type models"],
      ["Flat-incline bench, foldable", "\u20b93\u20136k", "Turns dumbbells into a full upper-body gym. Folds under a bed.", "Decathlon, Amazon"],
      ["Doorway pull-up bar", "\u20b91.5\u20133k", "The single best upper-body movement, for the price of a dinner.", "Amazon"],
      ["Resistance band set", "\u20b9500\u20132k", "Warm-ups, travel, rehab. Packs into a laptop bag \u2014 removes the travel excuse entirely.", "Decathlon"],
      ["Yoga mat, 6mm+", "\u20b91\u20132.5k", "Floor work and protecting the tiles.", "Decathlon"]
    ], "Total \u20b920\u201330k, once. Against \u20b91\u20133k a month for a gym you must travel to, it pays back inside a year \u2014 and the real return is that the commute excuse stops existing."],
    ["\u{1F634} Sleep", [
      ["Blackout curtains", "\u20b92\u20135k", "The highest-return sleep purchase there is, and nobody buys it.", "Local tailor with blackout fabric beats retail"],
      ["A cheap alarm clock", "\u20b9300\u20131k", "The entire point: the phone charges in another room. This one purchase fixes more than any tracker.", "Any shop"],
      ["White-noise fan or app", "\u20b90\u20132k", "Masks corridor and street noise.", "You may already own the fan"]
    ], "Under \u20b98k fixes sleep more reliably than \u20b930k of wearables."],
    ["\u{1F510} Digital security", [
      ["Password manager subscription", "\u20b90\u2013900/yr", "Bitwarden's free tier is genuinely sufficient. Paid adds emergency access, which is what lets your spouse in if something happens to you.", "bitwarden.com"],
      ["Two hardware security keys", "\u20b92\u20135k each", "Phishing-resistant in a way no OTP is. Buy two \u2014 one is a single point of failure. Register both, keep the spare elsewhere.", "Yubico direct, or Amazon for the FIDO2 models"],
      ["Authenticator app", "\u20b90", "Aegis on Android, with encrypted backups switched on. Never SMS for 2FA.", "Play Store"],
      ["Encrypted external drive, 1TB", "\u20b95\u20138k", "Local backup of documents and photos. Cloud is not a backup if one compromised login reaches it.", "Amazon"]
    ], "Roughly \u20b915k covers the whole layer. This is your professional domain \u2014 the gap is usually not knowledge, it is that nobody buys the second key."],
    ["\u{1F6E1} Home and physical", [
      ["Deadbolt on the main door", "\u20b92\u20135k fitted", "Builder-fitted locks are the cheapest part of the flat. This is the highest-return security spend in the house.", "Local locksmith"],
      ["Two indoor cameras", "\u20b93\u20136k", "Entry and living area. Choose local SD-card storage over subscription-only cloud.", "Amazon"],
      ["Fire extinguisher, ABC 2kg + smoke alarm", "\u20b92\u20134k", "Kitchen and near the bedrooms. Check the gauge each August with the insurance review.", "Amazon, local safety dealer"],
      ["Fireproof document pouch", "\u20b91.5\u20133k", "For the originals that are not in the locker.", "Amazon"],
      ["Home first-aid kit", "\u20b91\u20132k", "Stocked, in a known place, checked annually.", "Pharmacy"]
    ], "Under \u20b920k. Judged by expected loss avoided rather than by how it feels, this outperforms most insurance riders."],
    ["\u{1F373} Kitchen and daily friction", [
      ["3\u20134 lunch containers, 800ml glass", "\u20b91.5\u20132k", "Your own office lunch only \u2014 not a household system. Box an extra portion of whatever is already being cooked, rather than batch-cooking separately. 800ml is a full adult portion; the 370ml sets are snack-sized.", "myborosil.com or Amazon"],
      ["A large water bottle", "\u20b9500\u20131.5k", "Placed on the route you already walk. Behaviour follows placement, not intention.", "Anywhere"],
      ["Five identical work shirts", "\u20b93\u20138k", "The uniform. Ten minutes and one decision returned every morning, permanently.", "Whichever brand already fits you"]
    ], "Under \u20b912k buys back roughly an hour a week and a great deal of low-grade daily choosing."],
    ["\u{1F4C4} Documents", [
      ["Bank locker", "\u20b91.5\u20135k/yr", "Wills, sale deeds, originals. Non-negotiable once the wills exist.", "Your own bank"],
      ["Document scanner app", "\u20b90", "Phone plus DigiLocker covers everything. Scan once, in one session, done forever.", "DigiLocker"],
      ["A printed emergency binder", "\u20b9500", "Accounts, policies, contacts, instructions. Printed, because a crisis is exactly when nobody can log in.", "Any print shop"]
    ], "Under \u20b96k, and the item most likely to matter to someone other than you."]
  ];
  function kitHTML() {
    var st = G("gm_kit", {});
    var tot = 0, done = 0;
    KIT.forEach(function (g, gi) { g[1].forEach(function (_, i) { tot++; if ((st[gi] || {})[i]) done++; }); });
    var h = '<div class="cat-t">\u{1F6D2} The kit <span class="pill pill-g">' + done + '/' + tot + '</span></div>'
      + '<div class="info">Decided once so it never has to be researched again. Specifications rather than brands, because the specification is what actually matters and the brands change every year. '
      + 'Price bands are indicative for 2026 \u2014 check before buying, but do not re-open the decision about <i>what</i> to buy.</div>';
    KIT.forEach(function (g, gi) {
      h += '<details class="road-col" style="margin-bottom:8px"><summary style="cursor:pointer;font-weight:800;font-size:12.5px">' + g[0] + '</summary><div style="margin-top:8px">';
      g[1].forEach(function (it, i) {
        var on = (st[gi] || {})[i];
        h += '<div style="padding:7px 0;border-bottom:1px solid var(--border);cursor:pointer" onclick="gmKitTg(' + gi + ',' + i + ')">'
          + '<div style="display:flex;gap:8px;align-items:baseline">'
          + '<span style="color:' + (on ? "var(--green)" : "var(--muted)") + ';font-weight:800">' + (on ? "\u2611" : "\u2610") + '</span>'
          + '<span style="font-size:12.5px;font-weight:700;color:var(--text);' + (on ? "opacity:.5;text-decoration:line-through" : "") + '">' + esc(it[0]) + '</span>'
          + '<span style="margin-left:auto;font-size:11.5px;font-weight:800;color:var(--gold);white-space:nowrap">' + esc(it[1]) + '</span></div>'
          + '<div style="font-size:11px;color:var(--muted);line-height:1.55;margin-left:20px">' + esc(it[2]) + '</div>'
          + '<div style="font-size:10.5px;color:var(--muted);margin-left:20px;margin-top:2px"><b>Where:</b> ' + esc(it[3]) + '</div></div>';
      });
      h += '<div class="info" style="margin-top:8px">' + esc(g[2]) + '</div></div></details>';
    });
    return h;
  }
  window.gmKitTg = function (gi, i) { var st = G("gm_kit", {}); st[gi] = st[gi] || {}; st[gi][i] = !st[gi][i]; S_("gm_kit", st); renderAll(); };


  /* ═══════════════════════════════════════════════════════════════
     v7 — VITALS STRIP · TEMPLATES · THE VITAL FEW
     ═══════════════════════════════════════════════════════════════ */

  /* ── 24. VITALS — five numbers, on every screen, every day ────────
     Nothing gets managed that is not visible. These are deliberately
     five and not fifteen: a number you see daily changes behaviour,
     a number you have to navigate to does not. */
  function vitals() {
    var l = life(), done = (typeof todayChecks === "function") ? todayChecks() : [];
    var d3 = DAILY3.filter(function (d) { return done.indexOf(d.id) >= 0; }).length;

    var tot = 0, hit = 0;
    STACK.forEach(function (L) { L.items.forEach(function (_, i) { tot++; if ((stackState()[L.id] || {})[i]) hit++; }); });
    var stackPct = tot ? Math.round(hit / tot * 100) : 0;

    var fixed = num(l.fFixed), ef = lakhs(l.ef) * 100000;
    var runway = fixed ? ef / fixed : 0;

    var inc = num(l.minc), save = inc ? Math.round((num(l.fEF) + num(l.fSip)) / inc * 100) : 0;
    // No savings split given yet: what take-home minus spending leaves is the saving rate (both come from the quick setup).
    if (!save && !num(l.fEF) && !num(l.fSip) && window.P && !P.example && num(P.net) > 0 && num(P.exp) > 0)
      save = Math.round((num(P.net) - num(P.exp)) / num(P.net) * 100);

    var age = num(l.age), ainc = lakhs(l.inc), nw = lakhs(l.nw);
    var mult = age < 30 ? 0.5 : age < 35 ? 1 : age < 40 ? 2 : age < 45 ? 3 : age < 50 ? 4.5 : age < 55 ? 6 : age < 60 ? 8 : 10;
    var nwPct = (ainc && age) ? Math.round(nw / (mult * ainc) * 100) : 0;

    return [
      { l: "Today", v: d3 + "/3", c: d3 === 3 ? "var(--green)" : d3 ? "var(--amber)" : "var(--red)", t: "today" },
      { l: "Stack", v: stackPct + "%", c: stackPct >= 80 ? "var(--green)" : stackPct >= 40 ? "var(--amber)" : "var(--red)", t: "stack" },
      { l: "Runway", v: runway ? (runway > 120 ? "120m+" : runway.toFixed(1) + "m") : "\u2014", c: runway >= 6 ? "var(--green)" : runway >= 3 ? "var(--amber)" : "var(--red)", t: "life" },
      { l: "Saving", v: save ? save + "%" : "\u2014", c: save >= 20 ? "var(--green)" : save >= 15 ? "var(--amber)" : "var(--red)", t: "life" },
      { l: "Net worth", v: nwPct ? nwPct + "%" : "\u2014", c: nwPct >= 100 ? "var(--green)" : nwPct >= 60 ? "var(--amber)" : "var(--red)", t: "life" }
    ];
  }
  function vitalsHTML() {
    var h = '<div id="gmVitals">';
    vitals().forEach(function (v) {
      h += '<div role="button" tabindex="0" aria-label="' + esc(v.l) + ': ' + esc(v.v) + '. Open the tab that changes this."'
        + ' onclick="goTab(\'' + v.t + '\')" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();goTab(\'' + v.t + '\');}">'
        + '<div style="font-size:15px;font-weight:800;color:' + v.c + ';line-height:1.15">' + v.v + '</div>'
        + '<div style="font-size:8.5px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted);font-weight:700;margin-top:2px">' + v.l + '</div></div>';
    });
    return h + '</div>';
  }

  /* ── 25. TEMPLATES — a filled page beats a blank one ──────────────
     The reason wiki templates work is not the formatting. It is that
     editing something wrong is effortless and starting from nothing
     is not. Every template below is deliberately plausible-but-yours-
     to-correct, and clearly labelled as an example. */
  window.gmTplProp = function () {
    var p = props();
    p.push({ n: "Example \u2014 rename me", use: "letout", val: "75", rent: "18000", loan: "32", rate: "7.25", emi: "26000", out: "48000", vac: "1" });
    S_("gm_props", p); renderAll();
  };
  window.gmTplLife = function () {
    var l = life();
    ["age", "sage", "inc", "nw", "k1", "page", "edu", "minc", "fFixed", "fLoan", "fEF", "fSip", "ef"].forEach(function (k, i) {
      if (l[k] === undefined || l[k] === "") l[k] = ["36", "33", "23", "12", "1", "68", "25", "195000", "110000", "25000", "20000", "15000", "4"][i];
    });
    S_("gm_life", l);
    gmMarkExample(["age", "sage", "inc", "nw", "k1", "page", "edu", "minc", "fFixed", "fLoan", "fEF", "fSip", "ef"]);
    bustDerived(); renderAll();
  };
  window.gmTplWoop = function () {
    var q = qKey(new Date()), all = G("gm_woop", {});
    if (all[q] && all[q].w) gmSnap("overwrote this quarter\u2019s goal card with the example");
    all[q] = {
      w: "Emergency fund reaches six full months by the end of this quarter",
      o: "Opening the banking app during a bad week and feeling nothing at all",
      ob: "When a month feels tight I quietly skip the transfer and tell myself I will catch up",
      p: "IF the month feels tight THEN the transfer still goes out on day one and I cut the guilt-free budget instead"
    };
    S_("gm_woop", all); renderAll();
  };
  window.gmTplCommit = function () {
    if ((G("gm_commit", {}) || {}).who) gmSnap("overwrote the commitment device with the example");
    S_("gm_commit", { who: "Name the person here", stake: "\u20b91,000 to a cause I dislike, paid the same day" }); renderAll();
  };
  function tplBtn(fn, label) {
    return '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text);border:1px dashed var(--gold);margin-bottom:8px" onclick="' + fn + '">\u2728 ' + label + '</button>';
  }

  /* ── 26. THE VITAL FEW — 80/20 across the whole system ────────────
     Eleven items out of roughly a hundred. If you did only these and
     abandoned every other page in this app, you would capture most of
     the protection it exists to give you. */
  var VITAL = {
    L0: [4, 5], L1: [0, 3, 6], L2: [0, 1, 2], L3: [0, 1], L4: []
  };
  function isVital(lid, i) { return (VITAL[lid] || []).indexOf(i) >= 0; }
  window.gmVitalOnly = function () { S_("gm_vitalonly", !G("gm_vitalonly", false)); renderAll(); };


  /* ═══════════════════════════════════════════════════════════════
     v8 — THE DERIVATION LAYER
     Enter a number once. Everything downstream computes itself.

     Design rule: derived values are SHOWN with their provenance and
     offered for one-click adoption. They are never silently written
     over something you typed. A system that quietly changes your
     numbers is a system you stop trusting, and an untrusted dashboard
     is an abandoned one.
     ═══════════════════════════════════════════════════════════════ */

  /* ── 27. Derivations from data already entered ─────────────────── */
  var _dCache = null, _dStamp = 0;
  function bustDerived() { _dCache = null; }
  function derived() {
    // Memoised for one paint. Rendering the Stack used to call this once per
    // item plus once per layer \u2014 about sixty full recomputations, each
    // looping every property. Visible jank on a phone.
    if (_dCache && Date.now() - _dStamp < 400) return _dCache;
    var l = life(), P = props(), d = {};

    // --- from the Property tab ---
    var eq = 0, selfEq = 0, debt = 0, rent = 0, emi = 0, outgo = 0, anyProp = false;
    P.forEach(function (p) {
      if (!num(p.val)) return;
      anyProp = true;
      var r = propCalc(p);
      debt += num(p.loan) * 100000;        // ₹ — all debt counts, wherever you live
      emi += num(p.emi);                   // ₹/mo
      outgo += num(p.out) / 12;            // ₹/mo
      if (p.use === "self") { selfEq += r.equity; return; }  // the roof over your head is not net worth
      eq += r.equity;                      // ₹
      rent += num(p.rent) * (12 - num(p.vac)) / 12;  // ₹/mo, vacancy-adjusted
    });
    if (anyProp) {
      d.propEquity = { v: eq / 100000, u: "L", label: "Let-out property equity", src: "Property tab: market value less loan, let-out properties only"
        + (selfEq > 0 ? ". \u20b9" + Math.round(selfEq / 100000) + "L of self-occupied equity is deliberately excluded \u2014 the Life Map benchmark is net worth outside the home you live in" : "") };
      d.propDebt = { v: debt / 100000, u: "L", label: "Outstanding property debt", src: "Property tab: sum of outstanding loans" };
      d.propRent = { v: Math.round(rent), u: "₹/mo", label: "Rental income (vacancy-adjusted)", src: "Property tab: rent × (12 − vacant months) ÷ 12" };
      d.propFixed = { v: Math.round(emi + outgo), u: "₹/mo", label: "Property fixed costs", src: "Property tab: EMIs + monthly share of society/tax/repairs" };
    }

    // --- term cover: the Stack says income multiple PLUS outstanding debt ---
    var inc = num(l.inc);
    if (inc) {
      d.termNeed = {
        v: Math.round(inc * 11 + debt / 100000), u: "L",
        label: "Term cover you actually need",
        src: "11× household income" + (debt ? " + ₹" + Math.round(debt / 100000) + "L property debt" : "") + " — the Stack requires debt on top of the multiple"
      };
    }

    // --- runway and savings rate, the two that gate Stack items ---
    var fixed = num(l.fFixed), ef = num(l.ef) * 100000, minc = num(l.minc);
    if (fixed && ef) d.runway = { v: (ef / fixed).toFixed(1), u: "months", label: "Emergency runway", src: "Emergency fund ÷ monthly fixed costs" };
    if (minc) d.savRate = { v: Math.round((num(l.fEF) + num(l.fSip)) / minc * 100), u: "%", label: "Savings rate", src: "(to emergency fund + to SIP) ÷ take-home" };

    // --- education corpus gap: required SIP vs what is actually going out ---
    var k1 = (l.k1 === "" || l.k1 === undefined) ? null : num(l.k1);
    if (k1 !== null) {
      var yrs = Math.max(1, 18 - k1), fut = (num(l.edu) || 25) * Math.pow(1.10, yrs);
      var i12 = 0.12 / 12, n = yrs * 12;
      var need = Math.round((fut * 100000) / (((Math.pow(1 + i12, n) - 1) / i12) * (1 + i12)));
      d.eduSip = { v: need, u: "₹/mo", label: "Education SIP required", src: "₹" + Math.round(fut) + "L in " + yrs + " yrs at 12%, education inflation 10%" };
      var actual = num(l.fSip);
      if (actual) d.eduGap = { v: Math.max(0, need - actual), u: "₹/mo", label: "Education funding gap", src: "Required education SIP less your current total SIP — and your total SIP also has to cover retirement" };
    }
    _dCache = d; _dStamp = Date.now();
    return d;
  }

  /* ── 28. Auto-ticked Stack items ───────────────────────────────────
     Only where the evidence is unambiguous and already in the app.
     Anything softer stays a manual tick — a checkbox that ticks itself
     on weak evidence is worse than no checkbox. */
  function stackEvidence() {
    var d = derived(), l = life(), out = {};
    if (d.runway && parseFloat(d.runway.v) >= 6)
      out["L2|2"] = "Runway is " + d.runway.v + " months — at or past six.";
    if (d.savRate && d.savRate.v >= 20)
      out["L3|1"] = "Savings rate computes to " + d.savRate.v + "%.";
    var csf = G("gm_csf", {});
    if ((csf.PR || 0) >= 4) {
      out["L0|4"] = "NIST CSF Protect scored " + csf.PR + "/5.";
      out["L0|5"] = "NIST CSF Protect scored " + csf.PR + "/5.";
    }
    return out;
  }
  var _eCache = null, _eStamp = 0;
  function stackEvidenceCached() {
    if (_eCache && Date.now() - _eStamp < 400) return _eCache;
    _eCache = stackEvidence(); _eStamp = Date.now(); return _eCache;
  }
  function autoTicked(lid, i) { return stackEvidenceCached()[lid + "|" + i]; }

  /* ── 29. The Derived panel ─────────────────────────────────────── */
  window.gmAdopt = function (field, val) {
    var l = life();
    gmSnap("replaced a Life Map value with a derived one"); l[field] = String(val); S_("gm_life", l); renderAll();
  };
  function derivedHTML() {
    var d = derived(), l = life(), rows = [], h = "";
    function row(key, field, cmp) {
      var x = d[key]; if (!x) return;
      var cur = field ? num(l[field]) : null;
      var mismatch = field && cur && Math.abs(cur - parseFloat(x.v)) / parseFloat(x.v) > 0.05;
      rows.push('<div style="padding:9px 0;border-bottom:1px solid var(--border)">'
        + '<div style="display:flex;justify-content:space-between;gap:10px;align-items:baseline">'
        + '<div style="font-size:12.5px;font-weight:700;color:var(--text)">' + esc(x.label) + '</div>'
        + '<div style="font-size:14px;font-weight:800;color:var(--gold);white-space:nowrap">'
        + (x.u === "₹/mo" ? "₹" + Number(x.v).toLocaleString("en-IN") + "/mo" : x.u === "L" ? "₹" + x.v + "L" : x.v + " " + x.u)
        + '</div></div>'
        + '<div style="font-size:10.5px;color:var(--muted);line-height:1.5;margin-top:2px">' + esc(x.src) + '</div>'
        + (field && !cur ? '<button class="btn-sm" style="background:var(--gold);color:#0d1f35;margin-top:6px" onclick="gmAdopt(\'' + field + '\',' + x.v + ')">Use this value</button>' : "")
        + (mismatch ? '<div style="font-size:10.5px;color:var(--amber);margin-top:5px">You have ' + cur + ' entered manually. '
          + '<span style="text-decoration:underline;cursor:pointer" onclick="gmAdopt(\'' + field + '\',' + x.v + ')">Replace with ' + x.v + '</span> — or leave it, if your figure includes things this calculation cannot see.</div>' : "")
        + '</div>');
    }
    row("propEquity", "nw");
    row("propDebt", null);
    row("propRent", null);
    row("propFixed", "fFixed");
    row("termNeed", null);
    row("runway", null);
    row("savRate", null);
    row("eduSip", null);
    row("eduGap", null);

    if (!rows.length) return '<div class="cat-t">🔗 Derived</div>'
      + '<div class="info">Nothing to derive yet. Fill the Life Map and add a property, and this panel starts computing the downstream numbers so you never enter the same thing twice.</div>';

    h = '<div class="cat-t">🔗 Derived — computed, not typed</div>'
      + '<div class="info">Every figure here comes from something you already entered elsewhere. Nothing is written over your own numbers without you tapping to accept it.</div>'
      + '<div class="road-col">' + rows.join("") + trajHTML() + '</div>'
      + '<div class="info" style="margin-top:8px;font-size:10.5px">Assumptions, honestly: 12% SIP return is the long-run index headline \u2014 stress-test at 9\u201310% before betting a deadline on it. 10% education inflation is the higher-education figure, not CPI. The 11\u00d7 term-cover rule is a quick floor; a needs-based calculation (expenses \u00d7 years to independence + loans + education corpus \u2212 assets) is the better number. Age benchmarks are US-derived and directional only. ' + TAX2026.note + '</div>';

    var ev = stackEvidence(), keys = Object.keys(ev);
    if (keys.length) {
      h += '<div class="cat-t" style="margin-top:14px">✓ Stack items ticked by evidence</div><div class="road-col">';
      keys.forEach(function (k) {
        var lid = k.split("|")[0], i = parseInt(k.split("|")[1], 10), L = null;
        STACK.forEach(function (x) { if (x.id === lid) L = x; });
        if (L) h += '<div class="road-i"><span style="color:var(--green);font-weight:800">☑</span> '
          + esc(L.items[i]) + '<br><span style="color:var(--muted);font-size:10.5px">' + esc(ev[k]) + '</span></div>';
      });
      h += '</div>';
    }
    return h;
  }

  /* ═══════════════════════════════════════════════════════════════
     v8 — MICROSOFT GRAPH (Calendar · To Do · OneDrive backup)
     OAuth2 Authorization Code + PKCE, entirely client-side.
     No client secret, no backend, no third-party auth library —
     deliberately, since we just removed a CDN dependency for
     supply-chain reasons and adding MSAL back would undo that.
     ═══════════════════════════════════════════════════════════════ */

  var GRAPH = "https://graph.microsoft.com/v1.0";
  var MSAUTH = "https://login.microsoftonline.com/common/oauth2/v2.0";
  var SCOPES = "openid profile offline_access Calendars.Read Tasks.ReadWrite Files.ReadWrite.AppFolder";

  function msCfg() { return G("gm_ms_cfg", null); }
  function msTok() { return G("gm_ms_tok", null); }

  function b64url(buf) {
    return btoa(String.fromCharCode.apply(null, new Uint8Array(buf)))
      .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function pkce() {
    var a = new Uint8Array(64); crypto.getRandomValues(a);
    var verifier = b64url(a.buffer);
    return crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))
      .then(function (h) { return { verifier: verifier, challenge: b64url(h) }; });
  }

  window.gmMsConnect = function () {
    var id = (document.getElementById("msId") || {}).value;
    if (id) S_("gm_ms_cfg", { id: id.trim() });
    var c = msCfg();
    if (!c || !c.id) { alert("Paste your Azure application (client) ID first."); return; }
    pkce().then(function (p) {
      sessionStorage.setItem("gm_pkce", p.verifier);
      var u = MSAUTH + "/authorize?client_id=" + encodeURIComponent(c.id)
        + "&response_type=code&redirect_uri=" + encodeURIComponent(location.origin + location.pathname)
        + "&response_mode=query&scope=" + encodeURIComponent(SCOPES)
        + "&code_challenge=" + p.challenge + "&code_challenge_method=S256";
      location.href = u;
    });
  };

  function msExchange(code) {
    var c = msCfg(), v = sessionStorage.getItem("gm_pkce");
    if (!c || !v) return Promise.reject(new Error("no pkce verifier"));
    var body = "client_id=" + encodeURIComponent(c.id) + "&grant_type=authorization_code"
      + "&code=" + encodeURIComponent(code) + "&redirect_uri=" + encodeURIComponent(location.origin + location.pathname)
      + "&code_verifier=" + encodeURIComponent(v) + "&scope=" + encodeURIComponent(SCOPES);
    return fetch(MSAUTH + "/token", {
      method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body
    }).then(function (r) { return r.json(); }).then(function (t) {
      if (t.error) throw new Error(t.error_description || t.error);
      t.expires_at = nowSrv() + (t.expires_in - 120) * 1000;
      S_("gm_ms_tok", t); sessionStorage.removeItem("gm_pkce");
      history.replaceState({}, "", location.pathname);
      return t;
    });
  }
  function msToken() {
    var t = msTok(), c = msCfg();
    if (!t || !c) return Promise.reject(new Error("not connected"));
    if (t.expires_at > nowSrv()) return Promise.resolve(t.access_token);
    var body = "client_id=" + encodeURIComponent(c.id) + "&grant_type=refresh_token"
      + "&refresh_token=" + encodeURIComponent(t.refresh_token) + "&scope=" + encodeURIComponent(SCOPES);
    return fetch(MSAUTH + "/token", {
      method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body
    }).then(function (r) { return r.json(); }).then(function (n) {
      if (n.error) { localStorage.removeItem("gm_ms_tok"); throw new Error("re-auth needed"); }
      n.expires_at = nowSrv() + (n.expires_in - 120) * 1000;
      if (!n.refresh_token) n.refresh_token = t.refresh_token;
      S_("gm_ms_tok", n); return n.access_token;
    });
  }
  function gq(path) {
    return msToken().then(function (a) {
      return fetch(GRAPH + path, { headers: { Authorization: "Bearer " + a } });
    }).then(function (r) { return r.json(); });
  }

  /* --- pull calendar + tasks into a cache the Today tab can render --- */
  window.gmMsPull = function () {
    if (!msTok()) return Promise.resolve();
    var s = new Date(); s.setHours(0, 0, 0, 0);
    var e = new Date(s); e.setDate(e.getDate() + 1);
    var cal = "/me/calendarview?startDateTime=" + s.toISOString() + "&endDateTime=" + e.toISOString()
      + "&$select=subject,start,end,isAllDay&$orderby=start/dateTime&$top=20";
    return Promise.all([
      gq(cal).catch(function () { return null; }),
      gq("/me/todo/lists").then(function (L) {
        if (!L.value || !L.value.length) return null;
        return gq("/me/todo/lists/" + L.value[0].id + "/tasks?$filter=status ne 'completed'&$top=10");
      }).catch(function () { return null; })
    ]).then(function (r) {
      S_("gm_ms_cache", {
        at: nowSrv(),
        events: (r[0] && r[0].value) ? r[0].value.map(function (x) {
          return { s: x.subject, t: x.isAllDay ? "all day" : (x.start.dateTime || "").slice(11, 16) };
        }) : [],
        tasks: (r[1] && r[1].value) ? r[1].value.map(function (x) { return x.title; }) : []
      });
      renderAll();
    });
  };

  /* --- push a dated JSON backup into the app's private OneDrive folder --- */
  window.gmMsBackup = function () {
    var blob = {};
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k.indexOf("gm_ms_tok") !== 0 && k.indexOf("gm_sync_cfg") !== 0) blob[k] = localStorage.getItem(k);
    }
    var name = "guiding-map-" + ymd() + ".json";
    return msToken().then(function (a) {
      return fetch(GRAPH + "/me/drive/special/approot:/" + name + ":/content", {
        method: "PUT",
        headers: { Authorization: "Bearer " + a, "Content-Type": "application/json" },
        body: JSON.stringify(blob, null, 2)
      });
    }).then(function (r) {
      if (!r.ok) throw new Error("upload failed " + r.status);
      S_("gm_ms_backup", ymd());
      // Rotation: keep the last 14 dated backups; monthlies (monthly-*.json) are kept forever.
      return msToken().then(function (a) {
        var mk = "monthly-" + ymd().slice(0, 7) + ".json";
        var extra = (new Date().getDate() <= 7)
          ? fetch(GRAPH + "/me/drive/special/approot:/" + mk + ":/content", {
              method: "PUT", headers: { Authorization: "Bearer " + a, "Content-Type": "application/json" },
              body: JSON.stringify(blob, null, 2) }).catch(function () {})
          : Promise.resolve();
        return extra.then(function () {
          return fetch(GRAPH + "/me/drive/special/approot/children?$select=name,id&$top=200",
            { headers: { Authorization: "Bearer " + a } }).then(function (x) { return x.json(); });
        }).then(function (ls) {
          var daily = ((ls && ls.value) || []).filter(function (f) { return /^guiding-map-\d{4}-\d{2}-\d{2}\.json$/.test(f.name); })
            .sort(function (x, y) { return x.name < y.name ? 1 : -1; });
          return Promise.all(daily.slice(14).map(function (f) {
            return fetch(GRAPH + "/me/drive/items/" + f.id, { method: "DELETE", headers: { Authorization: "Bearer " + a } }).catch(function () {});
          }));
        });
      }).catch(function () {});
    }).then(function () {
      alert("Backed up to OneDrive as " + name);
      renderAll();
    }).catch(function (e) { alert("Backup failed: " + e.message); });
  };

  window.gmMsOff = function () {
    gmSnap("disconnected Microsoft 365");
    localStorage.removeItem("gm_ms_tok"); localStorage.removeItem("gm_ms_cache"); renderAll();
  };

  /* --- the strip that appears on Today --- */
  function msTodayHTML() {
    var c = G("gm_ms_cache", null);
    if (!c || (!c.events.length && !c.tasks.length)) return "";
    var h = '<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:13px;margin-bottom:12px">';
    if (c.events.length) {
      h += '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800">Today\u2019s calendar</div>';
      c.events.forEach(function (e) {
        h += '<div style="font-size:12.5px;color:var(--text);margin-top:5px"><b style="color:var(--gold)">' + esc(e.t) + '</b> &nbsp;' + esc(e.s) + '</div>';
      });
    }
    if (c.tasks.length) {
      h += '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800;margin-top:' + (c.events.length ? "11px" : "0") + '">Open tasks</div>';
      c.tasks.forEach(function (t) {
        h += '<div style="font-size:12.5px;color:var(--text);margin-top:4px"><span style="color:var(--green)">\u25b8</span> ' + esc(t) + '</div>';
      });
    }
    return h + '</div>';
  }

  function msHTML() {
    var t = msTok(), c = msCfg(), last = G("gm_ms_backup", null);
    var h = '<div class="cat-t">\u{1F517} Microsoft 365</div>';
    if (t) {
      h += '<div class="info">Connected. Today\u2019s calendar and your open To Do items appear at the top of Today. '
        + 'Backups go to a private app folder in OneDrive that only this app can see \u2014 not your general Documents.'
        + (last ? ' Last backup: ' + esc(last) + '.' : ' No backup taken yet.') + '</div>'
        + '<div style="display:flex;gap:8px;flex-wrap:wrap">'
        + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35" onclick="gmMsPull()">Refresh now</button>'
        + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35" onclick="gmMsBackup()">Back up to OneDrive</button>'
        + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmMsOff()">Disconnect</button></div>';
    } else {
      h += '<div class="info">Optional. Pulls today\u2019s calendar and your open To Do tasks onto the Today tab, and writes dated JSON backups to OneDrive automatically \u2014 so the export ritual stops depending on you remembering it.<br><br>'
        + 'Setup: Azure Portal \u2192 App registrations \u2192 New registration \u2192 Accounts in any organizational directory and personal Microsoft accounts \u2192 Redirect URI type <b>Single-page application</b>, value <code>' + esc(location.origin + location.pathname) + '</code>. Copy the Application (client) ID below. No client secret is needed or wanted.</div>'
        + '<label class="f-label">Application (client) ID</label><input id="msId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" value="' + esc((c && c.id) || "") + '">'
        + '<button class="btn btn-p" onclick="gmMsConnect()">Connect Microsoft 365</button>';
    }
    return h;
  }


  /* ── 30. Push nudges (client half) ─────────────────────────────── */
  function pushCfg() { return G("gm_push_cfg", null); }
  function u8(b64) {
    var p = "=".repeat((4 - b64.length % 4) % 4);
    var s = (b64 + p).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(s), a = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) a[i] = raw.charCodeAt(i);
    return a;
  }
  window.gmPushOn = function () {
    var w = (document.getElementById("pushUrl") || {}).value;
    if (w) S_("gm_push_cfg", { url: w.trim().replace(/\/+$/, "") });
    var c = pushCfg();
    if (!c) { alert("Paste your Worker URL first."); return; }
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      alert("This browser cannot receive push. On iPhone/iPad the app must be installed to the Home Screen from Safari first."); return;
    }
    Notification.requestPermission().then(function (perm) {
      if (perm !== "granted") { alert("Notifications were not allowed. Nothing else to do \u2014 the app still nudges you when you open it."); return; }
      return fetch(c.url + "/vapid").then(function (r) { return r.json(); }).then(function (v) {
        return navigator.serviceWorker.ready.then(function (reg) {
          return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: u8(v.key) });
        });
      }).then(function (sub) {
        return fetch(c.url + "/subscribe", {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(sub)
        }).then(function () { S_("gm_push_on", true); renderAll(); });
      });
    }).catch(function (e) { alert("Could not enable nudges: " + e.message); });
  };
  window.gmPushOff = function () {
    var c = pushCfg();
    navigator.serviceWorker.ready.then(function (reg) { return reg.pushManager.getSubscription(); })
      .then(function (s) {
        if (!s) return;
        var ep = s.endpoint;
        return s.unsubscribe().then(function () {
          if (c) return fetch(c.url + "/unsubscribe", {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ endpoint: ep })
          });
        });
      }).then(function () { localStorage.removeItem("gm_push_on"); renderAll(); });
  };
  function pushHTML() {
    var on = G("gm_push_on", false), c = pushCfg();
    var h = '<div class="cat-t">\u{1F514} Nudges</div>';
    if (on) {
      h += '<div class="info">This device is registered. Two nudges a day, 7am and 7pm IST. '
        + 'Register each device separately \u2014 the subscription belongs to the install, not to you.</div>'
        + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmPushOff()">Turn nudges off here</button>';
    } else {
      h += '<div class="info">A static site cannot wake your phone on a schedule \u2014 that needs a server to sign and send. '
        + 'The companion Worker (push-worker.js) is the smallest one that will do it: one cron trigger, one KV namespace, free tier. '
        + 'Deploy it, then paste its URL here. On iPhone/iPad, the app must already be installed from Safari.</div>'
        + '<label class="f-label">Worker URL</label><input id="pushUrl" placeholder="https://gm-push.yourname.workers.dev" value="' + esc((c && c.url) || "") + '">'
        + '<button class="btn btn-p" onclick="gmPushOn()">Enable nudges on this device</button>';
    }
    return h;
  }


  /* ── 31. Plain-English glossary ────────────────────────────────────
     Anything in this app that is an acronym, a legal citation, or a
     term of art gets defined here. If you ever have to leave the app
     to look something up, that is a defect in the app, not in you. */
  var GLOSS = [
    ["Cyclic sigh", "Two inhales through the nose \u2014 a normal one, then a second short sip on top \u2014 followed by one long slow exhale through the mouth. Three of these takes about ninety seconds."],
    ["Buffer", "Your emergency fund balance. Used interchangeably in the older notes; it means the same thing."],
    ["Tier-1 action", "The single highest-priority thing in your queue right now. Not a category \u2014 one specific action."],
    ["7/12 extract", "Satbara. The Maharashtra land record showing who owns a plot and what claims sit on it. Pulled from the talathi or the online portal."],
    ["Section 24(b)", "The Income-tax section allowing deduction of home-loan interest. Uncapped for a let-out property \u2014 but the resulting loss you can set against salary is capped at \u20b92L a year under section 71(3A)."],
    ["Section 80C", "The \u20b91.5L annual deduction bucket \u2014 PPF, ELSS, life premium, principal repayment, tuition fees."],
    ["Clubbing", "When income from an asset you funded but registered in your spouse's name is taxed as yours anyway. Decides who declares the rent."],
    ["OC", "Occupancy Certificate. Issued by the municipal body confirming a building is legally fit to live in. Banks and buyers both ask for it."],
    ["EC", "Encumbrance Certificate. Shows every registered transaction on a property \u2014 mortgages, sales, disputes \u2014 over a stated period."],
    ["Sweep-in FD", "A fixed deposit linked to your savings account that auto-breaks in parts when you withdraw, so you keep FD interest without losing access."],
    ["DSCR", "Debt Service Coverage Ratio. Rent divided by EMI. Above 1.0 the tenant pays the bank; below, you top it up."],
    ["Break-even occupancy", "The share of the year a property must be rented just to cover its own EMI and costs. Above 85% is fragile \u2014 two vacant months sink the year."],
    ["LDCE", "Limited Departmental Competitive Examination \u2014 the internal promotion exam route in government and PSU service."],
    ["SCSS", "Senior Citizens Savings Scheme. Government-backed, for age 60+, quarterly interest, five-year term."],
    ["PARA", "The four folders for a notes app: Projects (has a deadline), Areas (ongoing), Resources (reference), Archive (finished)."],
    ["WOOP", "Wish, Outcome, Obstacle, Plan. A four-box quarterly goal method \u2014 the obstacle and the pre-decided response are what make it work."],
    ["OKR", "Objectives and Key Results. One objective, two or three measurable results, graded 0.0\u20131.0 at quarter end."],
    ["AAR", "After-Action Review. Four questions: what was supposed to happen, what happened, why the gap, what changes."],
    ["NIST CSF 2.0", "A cybersecurity framework with six functions \u2014 Govern, Identify, Protect, Detect, Respond, Recover. Used here scored against yourself rather than an organisation."],
    ["Antifragility", "Taleb's term for systems that gain from disorder rather than merely surviving it. Scored here as Redundancy 40%, Optionality 35%, Recovery 25%."],
    ["Never Miss Twice", "One missed day is an accident. Two in a row starts a new habit. So the day after a miss, the two-minute version is compulsory."],
    ["Vital few", "The starred Stack items \u2014 roughly ten of a hundred that carry most of the protection. The 80/20 filter shows only these."]
  ];
  function glossHTML() {
    var h = '<div class="cat-t">\u{1F4D6} Glossary</div>'
      + '<div class="info">Every term this app uses that is not plain English. If something here is still unclear, that is worth fixing \u2014 leaving the app to search is exactly the friction it exists to remove.</div>'
      + '<div class="road-col">';
    GLOSS.forEach(function (g) {
      h += '<div style="padding:7px 0;border-bottom:1px solid var(--border)">'
        + '<div style="font-size:12.5px;font-weight:800;color:var(--text)">' + esc(g[0]) + '</div>'
        + '<div style="font-size:11.5px;color:var(--muted);line-height:1.6;margin-top:2px">' + esc(g[1]) + '</div></div>';
    });
    return h + '</div>';
  }


  /* ── 32. System health ─────────────────────────────────────────────
     One panel that answers: is my data safe, and is anything quietly
     broken? Every failure mode in this app is silent by design \u2014 sync
     retries, pushes debounce, clocks drift. Silent failure is fine
     until you need the data and it is not there. */
  function storageBytes() {
    var n = 0;
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      n += k.length + (localStorage.getItem(k) || "").length;
    }
    return n * 2; // UTF-16
  }
  window.gmExportNow = function () {
    var blob = {};
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k.indexOf("gm_ms_tok") !== 0) blob[k] = localStorage.getItem(k);
    }
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(blob, null, 2)], { type: "application/json" }));
    a.download = "guiding-map-" + ymd() + ".json";
    a.click();
    S_("gm_last_export", ymd()); renderAll();
  };
  window.gmImportNow = function () {
    var inp = document.createElement("input");
    inp.type = "file"; inp.accept = "application/json";
    inp.onchange = function () {
      var f = inp.files[0]; if (!f) return;
      var r = new FileReader();
      r.onload = function () {
        try {
          var o = JSON.parse(r.result), n = 0;
          if (!confirm("Restore " + Object.keys(o).length + " keys from this backup? Anything newer on this device will be overwritten.")) return;
          Object.keys(o).forEach(function (k) { localStorage.setItem(k, o[k]); n++; });
          alert("Restored " + n + " keys."); location.reload();
        } catch (e) { alert("That file could not be read: " + e.message); }
      };
      r.readAsText(f);
    };
    inp.click();
  };

  function healthHTML() {
    var rows = [], c = cfg(), last = G("gm_sync_last", null), exp = G("gm_last_export", null);
    var bytes = storageBytes(), kb = Math.round(bytes / 1024);

    function row(ok, label, detail, action) {
      rows.push('<div style="display:flex;gap:9px;padding:8px 0;border-bottom:1px solid var(--border)">'
        + '<span style="color:' + (ok === true ? "var(--green)" : ok === false ? "var(--red)" : "var(--amber)")
        + ';font-weight:800;font-size:15px;line-height:1.3" title="' + (ok === true ? "healthy" : ok === false ? "needs attention" : "heads-up") + '">\u25cf</span>'
        + '<div style="flex:1"><div style="font-size:12.5px;font-weight:700;color:var(--text)">' + label + '</div>'
        + '<div style="font-size:11px;color:var(--muted);line-height:1.55">' + detail + '</div>'
        + (action || "") + '</div></div>');
    }

    // Sync
    if (!c) row(null, "Cross-device sync is off",
      "This device keeps its own copy. Use Export below before switching devices, or turn sync on.");
    else if (!last) row(false, "Sync configured but nothing has been pushed yet",
      "Change any value to trigger the first push. If this stays empty, check the estate gateway is up and reachable (Tailscale) and the browser console for a 4xx from the sync endpoint.");
    else {
      var fails = G("gm_sync_fails", 0);
      var lastD = new Date(String(last).slice(0, 10));
      var idle = isNaN(lastD) ? 0 : Math.floor((Date.now() - lastD.getTime()) / 86400000);
      if (fails >= 3) row(false, "Sync pushes are failing (" + fails + " in a row)",
        "The estate sync endpoint is unreachable or rejecting pushes. Check the SecuRAX gateway is running, "
        + "that this device is on the same Tailscale network, and that the device token is correct. Your data on this device is safe and untouched \u2014 sync resumes on its own once the endpoint is back.");
      else if (idle >= 5) row(false, "No sync push for " + idle + " days",
        "No successful push in a while. Open the app on each device while the estate gateway is up to re-sync. "
        + "Opening the app on any synced device counts as activity, so the clock resets when the next push lands.");
      else row(true, "Sync is pushing", "Last successful push: " + esc(last) + ". Data stays on your own SecuRAX gateway \u2014 no third party, nothing to keep alive.");
    }

    // Clock \u2014 the silent data-loss one
    if (c) {
      var sk = Math.abs(skew);
      if (sk > 120000) row(false, "This device's clock is " + Math.round(sk / 60000) + " minutes off",
        "Timestamps are corrected against the server, so your data is safe \u2014 but fix the device clock, because everything else on it (certificates, 2FA codes) depends on it too.");
      else row(true, "Clock is aligned with the server", "Drift " + Math.round(sk / 1000) + "s. Per-key merges use server-anchored time, so no device silently loses writes.");
    }

    // Storage
    if (kb > 4000) row(false, "Storage is nearly full (" + kb + " KB)",
      "Browsers cap this around 5 MB. Export a backup, then trim the oldest After-Action Reviews.");
    else row(true, "Storage " + kb + " KB used", "Comfortable. Browsers allow roughly 5,000 KB.");

    // Backups \u2014 the one that matters when everything else fails
    var snaps = G("gm_sync_snaps", null);
    if (c && snaps && snaps.n) row(true, "Backed up automatically \u2014 " + snaps.n + " daily snapshot" + (snaps.n === 1 ? "" : "s") + " on your estate",
      "Latest: " + esc(String(snaps.latest)) + ". Nothing for you to do. A downloaded file is still the safest extra copy (it survives a lost estate).",
      '<div style="margin-top:6px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmSnapList()">See / restore a day</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmExportNow()">Also export a file</button></div><div id="snapList" class="muted" style="margin-top:6px"></div>');
    else if (!exp) row(false, "No local backup has ever been taken",
      "Sync is convenience; a dated file is your actual insurance. It survives a deleted sync backend, a cleared browser, and a lost device.",
      '<button class="btn-sm" style="background:var(--gold);color:#0d1f35;margin-top:6px" onclick="gmExportNow()">Export one now</button>');
    else {
      var days = Math.round((Date.now() - new Date(exp).getTime()) / 86400000);
      row(days > 45 ? false : days > 31 ? null : true, "Last backup " + (days === 0 ? "today" : days + " days ago"),
        days > 31 ? "Older than a month. Take a fresh one." : "Within the monthly rhythm.",
        '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text);margin-top:6px" onclick="gmExportNow()">Export now</button>');
    }

    // Offline shell
    row(navigator.serviceWorker && navigator.serviceWorker.controller ? true : null,
      navigator.serviceWorker && navigator.serviceWorker.controller ? "Offline mode is active" : "Offline mode not active on this device",
      navigator.serviceWorker && navigator.serviceWorker.controller
        ? "The app opens without a connection."
        : "Open the installed icon rather than a browser tab. If you are in a browser tab, the service worker may not control this page.");

    // Notifications
    var perm = (typeof Notification !== "undefined") ? Notification.permission : "unsupported";
    if (G("gm_push_on", false)) row(perm === "granted", "Nudges registered on this device",
      perm === "granted" ? "Two a day, 7am and 7pm IST." : "Permission was revoked in browser settings \u2014 re-enable it there, then turn nudges on again.");

    var an = G("gm_sync_anomaly", null);
    if (an) row(false, "A suspicious sync merge was refused",
      esc(an) + ". Local data won. If this repeats, check the estate sync record before trusting sync again.");
    var u = undoFresh();
    if (u) row(null, "Your last change can still be undone (for 30 minutes)",
      "\u201c" + esc(u.label) + "\u201d. Undo is a single slot \u2014 it holds only the most recent action, and taking another replaces it.",
      '<button class="btn-sm" style="background:var(--amber);color:#fff;margin-top:6px" onclick="gmUndo()">Undo that</button>');

    return '<div class="cat-t">\u{1FA7A} System health</div>'
      + '<div class="info">Everything in this app fails quietly by design \u2014 sync retries, pushes debounce, clocks drift. That is fine until the day you need the data. This panel is where quiet failure becomes visible.</div>'
      + '<div class="road-col">' + rows.join("") + '</div>'
      + '<div style="display:flex;gap:8px;margin-top:9px;flex-wrap:wrap">'
      + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35" onclick="gmExportNow()">Export backup</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmImportNow()">Restore from file</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmEmergencyExport()">Spouse emergency page</button></div>';
  }


  /* ── 33. Undo ──────────────────────────────────────────────────────
     Eleven actions in this app were irreversible with no confirmation:
     pausing the cadence, deleting a property, disconnecting sync,
     adopting a derived value over your own, overwriting the quarterly
     goal card with the example. Tapping one to see what it did was a
     one-way door.

     A stack of confirm() dialogs would have been the lazy fix \u2014 people
     learn to dismiss those without reading, so they protect nothing.
     One snapshot slot plus a visible Undo is honest: the action still
     happens instantly, and it is always reversible for as long as you
     have not taken another one. */
  function snapKeys() {
    var o = {};
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k.indexOf("gm_undo") === 0) continue;      // never snapshot the snapshot
      o[k] = localStorage.getItem(k);
    }
    return o;
  }
  window.gmSnap = function (label) {
    try { _set0("gm_undo", JSON.stringify({ at: Date.now(), label: label, data: snapKeys() })); }
    catch (e) { /* quota: an undo slot is a luxury, never block the action */ }
  };
  window.gmUndo = function () {
    var u = G("gm_undo", null); if (!u) return;
    if (Date.now() - u.at > 30 * 60 * 1000) { localStorage.removeItem("gm_undo"); renderAll(); return; }   // never roll back days of entries
    var redo = snapKeys();
    Object.keys(localStorage).slice().forEach(function () {});
    // wipe then restore, so keys created by the undone action disappear too
    var kill = [];
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (k.indexOf("gm_undo") !== 0) kill.push(k);
    }
    kill.forEach(function (k) { localStorage.removeItem(k); });
    Object.keys(u.data).forEach(function (k) { _set0(k, u.data[k]); });
    _set0("gm_undo", JSON.stringify({ at: Date.now(), label: "redo \u2014 " + u.label, data: redo }));
    bustDerived();
    renderAll();
  };
  function undoBar() {
    var u = undoFresh(); if (!u) return "";
    var mins = Math.round((Date.now() - u.at) / 60000);
    return '<div style="background:var(--amberBg);border:1px solid var(--amber);border-radius:10px;padding:10px 12px;margin-bottom:10px;display:flex;gap:10px;align-items:center">'
      + '<div style="flex:1;font-size:11.5px;color:var(--text);line-height:1.5">You just <b>' + esc(u.label) + '</b>'
      + (mins < 1 ? " (now)" : " (" + mins + " min ago)") + '. Undo puts everything back as it was before that.</div>'
      + '<button class="btn-sm" style="background:var(--amber);color:#1a1200;font-weight:800;white-space:nowrap" onclick="gmUndo()">Undo</button>'
      + '<button class="btn-sm" aria-label="dismiss" style="background:transparent;color:var(--muted);font-size:16px;padding:4px 8px" onclick="gmUndoDismiss()">\u00d7</button></div>';
  }


  /* ── 34. Protect in-progress typing ────────────────────────────────
     I introduced this bug myself when I added the pull-on-resume: a
     sync pull calls renderAll(), which rebuilds innerHTML and destroys
     whatever the user is halfway through typing. Switch apps mid-entry,
     come back, keep typing, and the field silently reverts. */
  function isTyping() {
    var a = document.activeElement;
    if (!a) return false;
    var t = (a.tagName || "").toLowerCase();
    return t === "input" || t === "textarea" || t === "select";
  }

  /* ── 35. Sanity checks on the numbers ──────────────────────────────
     Every money field is labelled in \u20b9 lakh or \u20b9 per month, and both
     get typed in the other unit constantly. Nothing caught it, so an
     absurd figure just propagated silently into every derived number. */
  var SANE = {
    age:   [16, 100,  "years"],
    sage:  [16, 100,  "years"],
    page:  [30, 110,  "years"],
    k1:    [0,  30,   "years"],
    inc:   [0.5, 500, "\u20b9 lakh a year"],
    nw:    [-500, 5000, "\u20b9 lakh"],
    ef:    [0,  500,  "\u20b9 lakh"],
    edu:   [1,  500,  "\u20b9 lakh"],
    minc:  [1000, 5000000, "\u20b9 per month"],
    fFixed:[0,  5000000, "\u20b9 per month"],
    fLoan: [0,  5000000, "\u20b9 per month"],
    fEF:   [0,  5000000, "\u20b9 per month"],
    fSip:  [0,  5000000, "\u20b9 per month"]
  };
  function saneWarn(field, val) {
    var r = SANE[field]; if (!r) return "";
    var v = num(val); if (!v) return "";
    if (v < r[0] || v > r[1]) {
      var guess = "";
      if (r[2].indexOf("lakh") >= 0 && v > 10000) guess = " Did you type rupees? \u20b9" + v.toLocaleString("en-IN") + " is \u20b9" + (v / 100000).toFixed(2) + " lakh.";
      if (r[2].indexOf("per month") >= 0 && v < 1000 && v > 0) guess = " Did you type lakh? \u20b9" + v + " lakh is \u20b9" + (v * 100000).toLocaleString("en-IN") + " per month.";
      return '<div style="font-size:11px;color:var(--amber);line-height:1.5;margin:-6px 0 8px">'
        + "That reads as " + v.toLocaleString("en-IN") + " " + r[2] + ", which is outside the usual range." + guess + '</div>';
    }
    return "";
  }

  /* ── 36. Mark example data as example ──────────────────────────────
     Tapping "start from a worked example" filled real-looking numbers
     with nothing to distinguish them from your own. People then read
     their vitals off someone else's figures. */
  function isExample(field) {
    var e = G("gm_example_fields", {});
    return !!e[field];
  }
  window.gmMarkExample = function (fields) {
    var e = G("gm_example_fields", {});
    fields.forEach(function (f) { e[f] = 1; });
    S_("gm_example_fields", e);
  };
  window.gmClearExample = function (field) {
    var e = G("gm_example_fields", {});
    if (e[field]) { delete e[field]; S_("gm_example_fields", e); }
  };
  function exampleBadge(field) {
    return isExample(field)
      ? '<span style="background:var(--amberBg);color:var(--amber);border:1px solid var(--amber);border-radius:5px;padding:0 5px;font-size:9.5px;font-weight:800;letter-spacing:.4px;margin-left:6px;vertical-align:middle">EXAMPLE</span>'
      : "";
  }
  function exampleCount() {
    return Object.keys(G("gm_example_fields", {})).length;
  }
  function exampleWarn() {
    var n = exampleCount();
    if (!n) return "";
    return '<div style="background:var(--amberBg);border:1px solid var(--amber);border-radius:10px;padding:10px 12px;margin-bottom:10px;font-size:11.5px;color:var(--text);line-height:1.55">'
      + '<b>' + n + ' field' + (n > 1 ? "s" : "") + ' still hold example numbers.</b> Your vitals and every derived figure are being calculated from them. '
      + 'Overwrite each one marked EXAMPLE with your own, and the badge clears itself.</div>';
  }


  /* ═══════════════════════════════════════════════════════════════
     v11 — EVIDENCE LAYER (research-spec build)
     Everything below is derived from data already entered. Nothing
     asks for a new input, ever. Sources: Lally 2010 / Loop Habit
     Tracker (EMA), Google SRE (error budgets), Gollwitzer d=0.65
     (anchors), Readwise 7-14-28 (resurfacing), JITAI (nudge
     suppression, worker-side), Budget 2026 constants.
     ═══════════════════════════════════════════════════════════════ */

  /* ── 37. Habit strength (EMA) + monthly miss budget ─────────────
     A streak dies of one bad day; an exponentially-weighted score
     barely notices it — which is what the habit-formation evidence
     actually says ("missing one opportunity did not materially
     affect the habit formation process", Lally 2010). \u03b1=0.1 \u2248
     20-day memory. Budgeted misses (2/habit/month) replace streak
     perfectionism with SRE-style honesty: failure is allowed,
     within limits. */
  function emaState() { return G("gm_ema", { last: null, s: {}, miss: {}, ym: "" }); }
  function emaUpdate() {
    if (typeof HABITS === "undefined" || typeof S === "undefined" || !S.daily) return emaState();
    var st = emaState(), today = ymd(), A = 0.1;
    if (st.last === today) return st;
    var ymNow = today.slice(0, 7);
    if (st.ym !== ymNow) { st.ym = ymNow; st.miss = {}; }        // fresh budget monthly
    // Walk each elapsed day since last update using the REAL history in S.daily.
    var d = st.last ? new Date(st.last) : null;
    if (!d) {                                                    // first run: seed from up to 60 days of REAL history
      d = new Date(); d.setDate(d.getDate() - 60);
      // ...but never before your first check-in: days before you used the app are not misses (they spent the month's
      // miss budget on day one and told a new user "budget used, floor is mandatory").
      var first = Object.keys(S.daily).filter(function (k) { return (S.daily[k] || []).length; }).sort()[0];
      if (!first) { st.last = today; S_("gm_ema", st); return st; }
      var f = new Date(first + "T00:00:00"); f.setDate(f.getDate() - 1);
      if (f > d) d = f;
    }
    var stop = new Date(today);
    while (true) {
      d.setDate(d.getDate() + 1);
      if (d >= stop) break;                                      // today itself is still in progress
      var k = (typeof dKey === "function") ? dKey(d) : null;
      var done = (k && S.daily[k]) ? S.daily[k] : [];
      HABITS.forEach(function (h) {
        var hit = done.indexOf(h.id) >= 0 ? 1 : 0;
        st.s[h.id] = (st.s[h.id] === undefined ? hit : st.s[h.id] + A * (hit - st.s[h.id]));
        var dm = String(d.getFullYear()) + "-" + ("0" + (d.getMonth() + 1)).slice(-2);
        if (!hit && dm === st.ym) st.miss[h.id] = (st.miss[h.id] || 0) + 1;
      });
    }
    st.last = today; S_("gm_ema", st);
    return st;
  }
  var MISS_BUDGET = 2; // per habit per month
  function strengthHTML() {
    var st = emaUpdate();
    if (!st.s || !Object.keys(st.s).length) return "";
    var h = '<div style="display:flex;gap:8px;margin-top:9px">';
    DAILY3.forEach(function (d3) {
      var v = Math.round((st.s[d3.id] || 0) * 100);
      var left = Math.max(0, MISS_BUDGET - (st.miss[d3.id] || 0));
      var col = v >= 70 ? "var(--green)" : v >= 40 ? "var(--gold)" : "var(--amber)";
      h += '<div style="flex:1;text-align:center">'
        + '<div style="height:4px;border-radius:2px;background:rgba(255,255,255,.12);overflow:hidden">'
        + '<div style="height:100%;width:' + v + '%;background:' + col + '"></div></div>'
        + '<div style="font-size:9px;color:#9fb3c8;margin-top:3px">strength ' + v + '% \u00b7 '
        + (left ? left + " guilt-free miss" + (left > 1 ? "es" : "") + " left" : "budget used \u2014 floor is mandatory") + '</div></div>';
    });
    return h + '</div>'
      + '<div style="font-size:9.5px;color:#7f93a8;margin-top:6px">Strength is a 20-day weighted average \u2014 one miss barely moves it, which is what the habit research actually shows. Two misses a month are budgeted on purpose; perfection is not the system.</div>';
  }

  /* ── 38. Drift alarms — speak only on a threshold cross ─────────── */
  function driftSnap() {
    var t = G("gm_trail", {}), ymNow = ymd().slice(0, 7), l = life();
    if (!t[ymNow]) {
      var inc = num(l.minc);
      t[ymNow] = { sav: inc ? Math.round((num(l.fEF) + num(l.fSip)) / inc * 100) : 0, fixed: num(l.fFixed) };
      var keys = Object.keys(t).sort(); while (keys.length > 13) { delete t[keys.shift()]; }
      S_("gm_trail", t);
    }
    return t;
  }
  function driftHTML() {
    var t = driftSnap(), keys = Object.keys(t).sort(), l = life();
    if (keys.length < 2) return "";
    var prev = t[keys[keys.length - 2]], inc = num(l.minc);
    if (!prev || !inc) return "";
    var savNow = Math.round((num(l.fEF) + num(l.fSip)) / inc * 100);
    var msgs = [];
    if (prev.sav && savNow < prev.sav - 5)
      msgs.push("Savings rate has slipped from " + prev.sav + "% to " + savNow + "% since last month."
        + treeHTML("sav", "Diagnose it \u2014 exactly one branch is the cause"));
    if (prev.fixed && num(l.fFixed) > prev.fixed * 1.1)
      msgs.push("Fixed costs are up " + Math.round((num(l.fFixed) / prev.fixed - 1) * 100) + "% on last month."
        + treeHTML("fixed", "Diagnose it \u2014 exactly one branch is the cause"));
    if (!msgs.length) return "";
    return '<div style="background:var(--amberBg);border:1.5px solid var(--amber);border-radius:12px;padding:12px;margin-bottom:12px">'
      + '<div style="font-weight:800;font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--amber)">\u2696 Drift detected</div>'
      + msgs.map(function (m) { return '<div style="font-size:12px;line-height:1.65;margin-top:6px;color:var(--text)">' + m + '</div>'; }).join("")
      + '</div>';
  }

  /* ── 39. Spaced resurfacing of AAR lessons (7\u201314\u201328 ladder) ────── */
  function resQ() { return G("gm_resurface", []); }
  window.gmResAns = function (i, keep) {
    var q = resQ(); if (!q[i]) return;
    if (keep) { q[i].iv = Math.min(112, (q[i].iv || 7) * 2); }
    else { q[i].iv = 7; }
    var d = new Date(); d.setDate(d.getDate() + q[i].iv); q[i].due = ymd(d);
    S_("gm_resurface", q); renderAll();
  };
  function resHTML() {
    var q = resQ(), today = ymd();
    for (var i = 0; i < q.length; i++) {
      if (q[i].due <= today && q[i].txt) {
        return '<div style="background:var(--card);border:1px solid var(--border);border-left:3px solid var(--gold);border-radius:12px;padding:12px;margin-bottom:12px">'
          + '<div style="font-size:10px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);font-weight:800">\u21ba Lesson from ' + esc(q[i].d) + ' \u2014 still true?</div>'
          + '<div style="font-size:12.5px;line-height:1.6;margin:7px 0;color:var(--text)">\u201c' + esc(q[i].txt) + '\u201d</div>'
          + '<div style="display:flex;gap:8px"><button class="btn-sm" style="flex:1;background:var(--gold);color:#0d1f35" onclick="gmResAns(' + i + ',true)">Still holds</button>'
          + '<button class="btn-sm" style="flex:1;background:var(--cardAlt);color:var(--text)" onclick="gmResAns(' + i + ',false)">Needs revisiting</button></div></div>';
      }
    }
    return "";
  }

  /* ── 40. Sunday Pulse auto-draft — confirm-and-annotate, not recall ── */
  function autoDraft() {
    var st = emaUpdate(), l = life(), lines = [];
    if (typeof HABITS !== "undefined" && typeof S !== "undefined" && S.daily) {
      var hits = 0, slots = 0, d = new Date();
      for (var i = 1; i <= 7; i++) {
        d.setDate(d.getDate() - 1);
        var k = (typeof dKey === "function") ? dKey(d) : null;
        if (k && S.daily[k]) hits += S.daily[k].length;
        slots += HABITS.length;
      }
      lines.push("Habits this week: " + hits + "/" + slots + " check-ins.");
    }
    var inc = num(l.minc);
    if (inc) lines.push("Savings rate on current numbers: " + Math.round((num(l.fEF) + num(l.fSip)) / inc * 100) + "%.");
    var exp = G("gm_last_export", null);
    if (exp) lines.push("Last backup: " + exp + ".");
    var fails = G("gm_sync_fails", 0);
    if (fails) lines.push("\u26a0 " + fails + " sync pushes failing \u2014 check System health.");
    return lines;
  }

  /* ── 41. Trajectory: emergency-fund completion as an honest range ── */
  function trajHTML() {
    var l = life(), fixed = num(l.fFixed), ef = num(l.ef) * 100000, mo = num(l.fEF);
    if (!fixed || !mo) return "";
    var target = fixed * 6, gap = target - ef;
    if (gap <= 0) return "";
    var fast = Math.ceil(gap / (mo * 1.2)), slow = Math.ceil(gap / (mo * 0.8));
    function add(m) { var d = new Date(); d.setMonth(d.getMonth() + m); return d.toLocaleString("en-IN", { month: "short", year: "numeric" }); }
    return '<div class="road-i">At \u20b9' + mo.toLocaleString("en-IN") + '/month, the six-month fund completes around <b>'
      + add(fast) + "\u2013" + add(slow) + '</b>. A range, not a date \u2014 single-date projections are pseudo-precision.</div>';
  }

  /* ── 42. Spouse emergency export — a signpost, never a secret ────── */
  window.gmEmergencyExport = function () {
    var l = life(), P = props();
    var rows = [];
    rows.push("<h2>If you are reading this, start here</h2>");
    rows.push("<p>This page holds no passwords. It tells you what exists and where the real documents and access live.</p>");
    rows.push("<h3>Money</h3><ul>");
    if (num(l.nw)) rows.push("<li>Net worth outside the home: about \u20b9" + l.nw + " lakh</li>");
    if (num(l.ef)) rows.push("<li>Emergency fund: about \u20b9" + l.ef + " lakh \u2014 bank + sweep-in FD + liquid fund</li>");
    rows.push("<li>Password manager emergency access is the key to everything digital \u2014 it was set up for you; check your own email for the invitation</li>");
    rows.push("</ul><h3>Property</h3><ul>");
    P.forEach(function (p) { if (p.n) rows.push("<li>" + p.n + (p.use === "self" ? " (home)" : " (let out)") + (num(p.loan) ? " \u2014 loan outstanding \u2248\u20b9" + p.loan + "L" : "") + "</li>"); });
    var rp = G("gm_rapid", {}), rl = [];
    RAPID_D.forEach(function (x) { var v = rp[x[0]] || {}; if (v.d) rl.push("<li><b>" + x[1] + ":</b> " + v.d + " decides" + (v.r ? ", after asking " + v.r : "") + "</li>"); });
    if (rl.length) rows.push("</ul><h3>Who decides what</h3><ul>" + rl.join(""));
    rows.push("</ul><h3>Where the documents are</h3><ul>"
      + "<li>Wills, deeds, originals: bank locker</li>"
      + "<li>Scans: DigiLocker + OneDrive</li>"
      + "<li>Policy numbers and contacts: the printed emergency binder at home</li></ul>"
      + "<p><i>Generated " + ymd() + " from The Guiding Map. Regenerate after any big change.</i></p>");
    var html = "<html><head><meta charset='utf-8'><title>Emergency \u2014 start here</title><style>body{font-family:Georgia,serif;max-width:640px;margin:40px auto;padding:0 20px;line-height:1.7;color:#1a2333}</style></head><body>" + rows.join("") + "</body></html>";
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([html], { type: "text/html" }));
    a.download = "EMERGENCY-start-here-" + ymd() + ".html";
    a.click();
  };

  /* ── 43. Budget-2026 constants stamp (numbers, not section labels) ── */
  var TAX2026 = { note: "Tax figures current as of Budget 2026: new-regime income to \u20b912L effectively tax-free (87A rebate \u20b960k, standard deduction \u20b975k \u2192 \u20b912.75L salaried break-even); PPF 7.1%, SSY 8.2%; TDS on rent threshold \u20b96L/yr (194-I) / \u20b950k per month for individual tenants. Re-verify each April \u2014 the lock-in ritual already schedules it." };


  /* ═══════════════════════════════════════════════════════════════
     v12 — THE CONSULTANT'S LAYER
     Five frameworks from the MBB/Big-Four toolkit, and only five.
     Selection rule (itself 80/20): a framework earns a place only if
     it changes a decision you already make, on a surface that already
     exists, without asking for a new daily input. Twenty others were
     considered and rejected as scaffolding you would never re-open.
     ═══════════════════════════════════════════════════════════════ */

  /* ── 44. SCQA — the review writes answer-first ────────────────────
     Minto's Pyramid Principle: lead with the answer, support with
     three MECE arguments. Applied here, the Sunday Pulse stops being
     "what happened this week" (chronological, forgettable) and
     becomes Situation \u2192 Complication \u2192 Question \u2192 Answer, which is
     the structure that forces a decision out of a review. */
  function scqa() {
    var l = life(), st = emaUpdate(), out = { s: [], c: [], q: "", a: "" };
    var inc = num(l.minc), sav = inc ? Math.round((num(l.fEF) + num(l.fSip)) / inc * 100) : 0;

    // SITUATION — the stable facts, agreed and uncontested
    var weak = [];
    DAILY3.forEach(function (d) { if ((st.s[d.id] || 0) < 0.5) weak.push(d.label); });
    if (sav) out.s.push("Savings rate " + sav + "%, runway " + (num(l.fFixed) ? (num(l.ef) * 100000 / num(l.fFixed)).toFixed(1) : "\u2014") + " months.");
    var tot = 0, hit = 0;
    STACK.forEach(function (L) { L.items.forEach(function (_, i) { tot++; if ((stackState()[L.id] || {})[i] || autoTicked(L.id, i)) hit++; }); });
    out.s.push("Stack " + Math.round(hit / tot * 100) + "% complete; the open action sits in " + (theOneAction() ? theOneAction().layer.name : "maintenance") + ".");

    // COMPLICATION — only what has changed for the worse
    if (weak.length) out.c.push(weak.join(" and ") + " below half strength.");
    var fails = G("gm_sync_fails", 0);
    if (fails >= 3) out.c.push("Sync has failed " + fails + " times \u2014 the data layer is not safe right now.");
    var exp = G("gm_last_export", null);
    if (exp && (Date.now() - new Date(exp).getTime()) / 86400000 > 31) out.c.push("No backup in over a month.");
    var t = G("gm_trail", {}), keys = Object.keys(t).sort();
    if (keys.length >= 2 && t[keys[keys.length - 2]].sav && sav < t[keys[keys.length - 2]].sav - 5)
      out.c.push("Savings rate down " + (t[keys[keys.length - 2]].sav - sav) + " points on last month.");

    // QUESTION + ANSWER — the whole point of the review
    out.q = out.c.length
      ? "What single change closes the largest of these before next Sunday?"
      : "Nothing is broken. What is the one thing worth advancing this week?";
    out.a = theOneAction() ? theOneAction().text : "Hold the line; run the cadence.";
    return out;
  }
  function scqaHTML() {
    var x = scqa();
    function blk(lbl, body, tone) {
      return '<div style="margin-top:7px"><span style="font-size:9px;letter-spacing:.7px;text-transform:uppercase;font-weight:800;color:'
        + (tone || "var(--muted)") + '">' + lbl + '</span>'
        + '<div style="font-size:11.5px;line-height:1.6;color:var(--text)">' + body + '</div></div>';
    }
    return '<div style="background:rgba(201,168,76,.12);border-radius:8px;padding:9px 11px;margin-top:8px">'
      + '<div style="font-size:9.5px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);font-weight:800">Auto-draft \u00b7 answer-first (Minto)</div>'
      + blk("Situation", x.s.map(esc).join(" "))
      + (x.c.length ? blk("Complication", x.c.map(esc).join(" "), "var(--amber)") : "")
      + blk("Question", esc(x.q))
      + blk("Answer", "<b>" + esc(x.a) + "</b>", "var(--gold)")
      + '<div style="font-size:9.5px;color:var(--muted);margin-top:6px">Confirm or overwrite the Answer \u2014 that line is the week\u2019s decision, not a summary of it.</div></div>';
  }

  /* ── 45. Issue tree — a drift alarm that decomposes itself ─────────
     An alarm that only says "this got worse" makes you invent the
     diagnosis at the worst moment. A MECE tree hands you the branches
     so the thinking is already structured: no overlap, nothing missed. */
  var TREES = {
    sav: ["Income fell (salary, rent, or a missed reimbursement)",
          "Fixed costs rose \u2014 check the cost-creep branch below",
          "A transfer did not execute (standing instruction failed or was skipped)",
          "A one-off drawdown was taken from the buffer",
          "Guilt-free spending expanded to fill the gap"],
    fixed: ["A new recurring commitment started (EMI, subscription, fee)",
            "An existing one was repriced (insurance renewal, rent, society dues)",
            "A variable cost was reclassified as fixed",
            "A one-off was mistakenly entered as monthly \u2014 check the number first"]
  };
  function treeHTML(k, title) {
    var b = TREES[k]; if (!b) return "";
    return '<details style="margin-top:7px"><summary style="cursor:pointer;font-size:11px;font-weight:800;color:var(--amber)">'
      + esc(title) + '</summary><div style="font-size:11px;line-height:1.7;margin-top:5px;color:var(--text)">'
      + b.map(function (x) { return "\u2014 " + esc(x); }).join("<br>")
      + '<div style="color:var(--muted);margin-top:5px">Mutually exclusive, collectively exhaustive \u2014 exactly one of these is the cause. Eliminate downward, do not guess.</div></div></details>';
  }

  /* ── 46. RAPID — decision rights, so continuity survives you ───────
     Bain's answer to "who has the D?". Filled once, it is the single
     most useful page in a crisis: it tells your household who decides
     what when you are not there to be asked. */
  var RAPID_D = [
    ["money", "Money above \u20b950,000"],
    ["med", "Medical decisions for a parent"],
    ["kid", "Schooling and childcare"],
    ["prop", "Anything to do with the properties"],
    ["job", "A career move or relocation"]
  ];
  window.gmRapidSet = function (k, f, v) {
    var r = G("gm_rapid", {}); r[k] = r[k] || {}; r[k][f] = v; S_("gm_rapid", r); renderAll();
  };
  function rapidHTML() {
    var r = G("gm_rapid", {}), done = RAPID_D.filter(function (x) { return (r[x[0]] || {}).d; }).length;
    var h = '<div class="cat-t">\u2696 Decision rights <span class="pill pill-g">' + done + '/' + RAPID_D.length + '</span></div>'
      + '<div class="info">Bain\u2019s RAPID, shrunk to a household. <b>D</b> is the one person who decides; <b>R</b> recommends; <b>I</b> is consulted for input. '
      + 'Two people holding the D is how families stall at the worst possible moment. Fill it once \u2014 it goes into the emergency page automatically.</div>';
    RAPID_D.forEach(function (x) {
      var v = r[x[0]] || {};
      h += '<div class="road-col" style="margin-bottom:7px"><div class="road-h">' + esc(x[1]) + '</div>'
        + '<label class="f-label">Decides (one name only)</label><input value="' + esc(v.d || "") + '" placeholder="who has the final call" onchange="gmRapidSet(\'' + x[0] + '\',\'d\',this.value)">'
        + '<label class="f-label">Recommends / consulted</label><input value="' + esc(v.r || "") + '" placeholder="who is asked first" onchange="gmRapidSet(\'' + x[0] + '\',\'r\',this.value)">'
        + '</div>';
    });
    return h;
  }

  /* ── 47. Three Horizons on the Optionality layer ───────────────────
     Baghai/Coley/White. Optionality items are not one queue \u2014 they run
     in parallel on different clocks, and H1 gravity is what starves
     H2 and H3 in every organisation and every life. */
  var HORIZON = {
    "A second income stream that is live and has actually been paid": ["H2", "Scale \u2014 proven demand, needs volume"],
    "Remote-capable: portfolio, writing samples, a track record that travels": ["H1", "Defend \u2014 compounds your current earning power"],
    "Network of 50 with real relationships, some outside your country": ["H1", "Defend \u2014 pays off continuously, never urgent"],
    "Multi-currency banking arranged": ["H2", "Scale \u2014 mechanical once started"],
    "Second residency researched and the first step taken": ["H3", "Validate \u2014 a cheap option on an uncertain future"],
    "Venture reviewed quarterly rather than fantasised about weekly": ["H3", "Validate \u2014 fifteen minutes, quarterly, no more"]
  };
  function horizonTag(item) {
    var x = HORIZON[item]; if (!x) return "";
    var c = x[0] === "H1" ? "var(--green)" : x[0] === "H2" ? "var(--gold)" : "var(--amber)";
    return ' <span title="' + esc(x[1]) + '" style="font-size:9px;font-weight:800;color:' + c + ';border:1px solid ' + c + ';border-radius:4px;padding:0 4px">' + x[0] + '</span>';
  }

  /* ── 48. Which tool for which question ─────────────────────────────
     Not a library. Six entries, each tied to a decision you actually
     face, so the framework arrives at the moment of use rather than
     being read once and forgotten. */
  var TOOLKIT = [
    ["\u201cWhy did this number move?\u201d", "Issue tree + MECE", "Break the question into branches that do not overlap and leave nothing out, then eliminate downward. The drift alarms in this app already do this for savings rate and cost creep."],
    ["\u201cI need someone senior to act on this.\u201d", "Pyramid Principle (Minto)", "Lead with the recommendation, then three supporting arguments, then evidence. Never build up chronologically \u2014 decision-makers stop reading."],
    ["\u201cWhere do I put my limited time or money?\u201d", "80/20, then Three Horizons", "Pareto first to find the vital few; Horizons second so today\u2019s work does not starve the two-year and five-year bets."],
    ["\u201cWho actually decides this?\u201d", "RAPID (Bain)", "One D per decision. Filled in above \u2014 the most valuable page in this app on the day you cannot be reached."],
    ["\u201cIs this venture worth entering?\u201d", "Five Forces + Ansoff", "Forces tells you if the industry can be profitable at all; Ansoff tells you which of the four growth moves you are actually making, and its risk."],
    ["\u201cWhy did the change not stick?\u201d", "Influence Model + BCG 10-20-70", "Role-modelling, conviction, formal reinforcement, skills \u2014 all four or none. And expect 70% of the effort to be people and process, not tooling."]
  ];
  function toolkitHTML() {
    var h = '<div class="cat-t">\u{1F9F0} Which tool for which question</div>'
      + '<div class="info">Six, deliberately. Frameworks are scaffolding for thinking, never a substitute for judgement or current data \u2014 used mechanically they produce confident, wrong answers.</div><div class="road-col">';
    TOOLKIT.forEach(function (t) {
      h += '<div style="padding:7px 0;border-bottom:1px solid var(--border)">'
        + '<div style="font-size:12px;font-weight:800;color:var(--text)">' + esc(t[0]) + '</div>'
        + '<div style="font-size:11px;color:var(--gold);font-weight:700;margin-top:1px">' + esc(t[1]) + '</div>'
        + '<div style="font-size:11px;color:var(--muted);line-height:1.55;margin-top:2px">' + esc(t[2]) + '</div></div>';
    });
    return h + '</div>';
  }

  /* ── 48b. GUIDES — self-contained "how do I actually DO this?" layer ───────
     The friction killer: every instruction in the map carries its own how-to,
     with a simple visual where it helps, so you never leave the app to search,
     watch a video, or draw it yourself. Plain steps, equipment substitutes for
     what you actually own, and a self-check. (Systems you can act on, not look up.) */
  var BOX_SVG =
    '<svg viewBox="0 0 220 180" width="100%" style="max-width:300px;display:block;margin:6px auto">'
    + '<rect x="60" y="20" width="100" height="100" rx="8" fill="none" stroke="var(--accent)" stroke-width="3"/>'
    + '<text x="110" y="14" text-anchor="middle" font-size="11" fill="var(--muted)">Inhale 4s →</text>'
    + '<text x="168" y="74" font-size="11" fill="var(--muted)">↓ Hold 4s</text>'
    + '<text x="110" y="138" text-anchor="middle" font-size="11" fill="var(--muted)">← Exhale 4s</text>'
    + '<text x="12" y="74" font-size="11" fill="var(--muted)">Hold 4s ↑</text>'
    + '<circle r="7" fill="var(--accent)"><animateMotion dur="16s" repeatCount="indefinite" '
    + 'path="M60,20 L160,20 L160,120 L60,120 Z" keyPoints="0;0.25;0.5;0.75;1" keyTimes="0;0.25;0.5;0.75;1" calcMode="linear"/></circle>'
    + '</svg><div class="info" style="text-align:center">One lap = one full breath (16s). Follow the dot: in, hold, out, hold. Do 5–10 minutes.</div>';
  var Z2_SVG =
    '<svg viewBox="0 0 320 60" width="100%" style="max-width:320px;display:block;margin:6px auto">'
    + '<rect x="10" y="24" width="300" height="12" rx="6" fill="var(--line)"/>'
    + '<rect x="10" y="24" width="120" height="12" rx="6" fill="var(--ok)" opacity=".35"/>'
    + '<rect x="130" y="24" width="90" height="12" rx="6" fill="var(--accent)"/>'
    + '<rect x="220" y="24" width="90" height="12" rx="6" fill="var(--q1)" opacity=".5"/>'
    + '<text x="70" y="18" text-anchor="middle" font-size="10" fill="var(--muted)">too easy (can sing)</text>'
    + '<text x="175" y="18" text-anchor="middle" font-size="10" fill="var(--accent)">Zone 2 (can talk, can’t sing)</text>'
    + '<text x="265" y="18" text-anchor="middle" font-size="10" fill="var(--muted)">too hard (gasping)</text>'
    + '<text x="175" y="52" text-anchor="middle" font-size="10" fill="var(--muted)">↑ aim for the middle band</text></svg>';

  var GUIDES = [
    { id: "daily3", icon: "☀", title: "The Daily Three: Move, Mind, Family", tag: "daily · 2-min floor",
      what: "The three non-negotiables. Each has a 2-minute floor — the smallest version that still counts as a win, so you never miss twice.",
      steps: ["MOVE — get your body working: a brisk 10-min walk, the strength workout, stairs, or stretching. Floor: 2 minutes of any movement.",
        "MIND — train attention/calm: box breathing, 10 slow breaths, or 5 min journaling. Floor: 1 minute of slow breathing.",
        "FAMILY — one real connection: a proper conversation, a call to parents, phone away at a meal. Floor: one undistracted 2-min talk."],
      check: "Did I do the floor on each? Yes = streak holds. Perfection is not required; showing up is." },
    { id: "strength", icon: "💪", title: "Mon/Wed/Fri — 30-min strength (band, no handles needed)", tag: "strength · 3×/week",
      what: "Five exercises, ~5 min each, 45–60s rest between sets. You have a Decathlon loop band — no handle attachment is needed; the substitutions below use the loop directly.",
      steps: ["1) PUSH-UPS — 3 sets × max reps. Hands shoulder-width, body straight, lower chest toward floor, push up. On knees is fine to start.",
        "2) BAND ROWS — 3×12. No handles? Loop the band around a sturdy pole or the hinge side of a closed door at waist height (or stand on the middle of the band and hold the two loop ends). Hinge at hips, pull toward your waist, squeeze shoulder blades.",
        "3) SQUATS — 3×15. Feet shoulder-width, chest up, push hips back, knees track over toes, go as low as comfortable.",
        "4) BAND PRESS — 3×12. Stand on the band (or anchor it behind you at chest height), hold the loop at chest, press forward until arms straight, control back. Core tight, don’t arch.",
        "5) PLANK — 3×45s. Forearms on floor, body in a straight line, squeeze core/glutes, breathe normally."],
      subs: ["Loop band digs into hands: wrap the ends around a rolled towel or your wrists.",
        "No anchor point: standing on the band works for rows and presses.",
        "Too hard: fewer reps with good form beats more reps with bad form."],
      check: "Flow: Push-ups → Rows → Squats → Press → Plank. ~30 min total. Recovery day between sessions." },
    { id: "breathing", icon: "🧘", title: "Box breathing + the 3-month calm ladder", tag: "mind · build up",
      what: "Start with box breathing (weeks 1–2), then climb the ladder. The animation below is all you need — no video.",
      viz: BOX_SVG,
      steps: ["WEEKS 1–2 — Box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s. Follow the dot above. 5–10 min.",
        "WEEKS 3–4 — Breath counting: inhale, mentally say “1”; exhale, “2”; up to 10, then restart. Mind wanders? Gently return to 1. 10 min.",
        "MONTH 2 — Body scan / Yoga Nidra: lie down, move attention slowly from toes to head, notice sensations without judgement. 10–20 min.",
        "MONTH 3 — Open awareness: sit, let sounds/thoughts/sensations come and go without controlling them. Just observe. 10–15 min."],
      check: "One rung at a time. If a level feels hard, stay on the one below another week." },
    { id: "zone2", icon: "🚶", title: "Tue/Sat — Zone 2 cardio (the talk test)", tag: "cardio · 2×/week",
      what: "Steady aerobic effort you can sustain — the simple base Peter Attia emphasises for long-term metabolic and heart health. No heart-rate monitor needed; use the talk test.",
      viz: Z2_SVG,
      steps: ["THE RULE: you can speak a full sentence, but wouldn’t want to give a speech. Can sing = too easy. Gasping = too hard.",
        "WEEK 1 (don’t start at 45 min): 30 min each on Tue + Sat. 0–5 min easy walk → 5–25 min build to talk-test pace → 25–30 min cool down.",
        "EASIEST VERSION — fast walking: flat route, walk 5 min, then gradually raise pace to the talk-test intensity. No running required.",
        "IF YOU CYCLE: pick resistance/speed that produces the right breathing; keep it steady (no sprints/hard hills/stop-start).",
        "BUILD: once 30 min feels comfortable after a couple of sessions, move toward 35–45 min."],
      check: "Weekly shape: Mon strength · Tue Zone 2 · Wed strength · Thu mindfulness · Fri strength · Sat Zone 2 · Sun recovery. (AHA suggests building toward ~150 min/week of moderate activity over time — start with your 2×30 and grow.)" },
    { id: "pwmgr", icon: "🔐", title: "OPSEC: pick a password manager (unblocks “all passwords”)", tag: "security · do once",
      what: "The community-proven picks (verify current audit status before trusting any tool). Choose one, then import/add passwords over a week — don’t try to do all at once.",
      steps: ["BITWARDEN — best all-round: open-source, independently audited, genuinely unlimited free tier, syncs across all devices. Default choice for most.",
        "KEEPASSXC — most sovereign: the vault is a local file on your device, nothing in anyone’s cloud. You handle sync (put the file on your own estate / Tailscale). Fits SecuRAX’s sovereignty best if you’re comfortable managing a file.",
        "VAULTWARDEN — self-hosted Bitwarden-compatible server you can run inside your own SecuRAX estate: Bitwarden’s apps, your data on your hardware. The best of both once Phase 3 sync/Tailscale is up.",
        "PROTON PASS — if email aliases matter most (hide-my-email): privacy-focused, free tier includes aliases."],
      subs: ["Whichever you pick: set a long, unique master password you can remember (a passphrase of 4–5 random words), turn on 2FA/passkey, and write ONLY where the master password hint lives in your Continuity Vault — never the password itself."],
      check: "Decision rule (your Global-Intelligence method): most-recommended + open-source + audited wins → Bitwarden, or KeePassXC/Vaultwarden if you want it fully on your own hardware." },
    { id: "recoveryemail", icon: "📧", title: "OPSEC: a dedicated recovery email (the step before the vault)", tag: "security · do once",
      what: "A brand-new email used ONLY to recover your important accounts — never shared, never used to sign up for anything, never posted. It isolates your most valuable accounts from your everyday inbox (which leaks everywhere).",
      steps: ["Create a fresh account at a reputable provider (e.g. a new Gmail, or ProtonMail for extra privacy). Pick a name that isn’t obviously ‘you’.",
        "Give it a long unique password (store it in your new password manager) and turn on 2FA — ideally a passkey or an authenticator app, not SMS.",
        "Use this address as the recovery/backup email on your bank, primary email, password manager, and cloud accounts. Nothing else.",
        "Never use it to sign up for newsletters, shopping, or apps. Its only job is account recovery.",
        "Record that it exists (not its password) in your Continuity Vault so family can act in an emergency."],
      check: "If someone compromises your everyday email, your recovery paths still stand because they point at an address the attacker has never seen." },
  ];

  function guideCard(g) {
    var h = '<details class="guide-card road-col" style="margin-bottom:10px"><summary style="cursor:pointer;font-weight:800;font-size:13px">'
      + g.icon + ' ' + esc(g.title) + ' <span style="font-weight:500;color:var(--muted)">· ' + esc(g.tag) + '</span></summary>'
      + '<div style="font-size:12.5px;line-height:1.75;margin-top:8px">'
      + '<div class="info" style="margin-bottom:8px">' + esc(g.what) + '</div>'
      + (g.viz || "");
    g.steps.forEach(function (s) { h += '• ' + esc(s) + '<br>'; });
    if (g.subs) { h += '<div style="margin-top:8px;font-weight:700">If your gear/setup differs</div>'; g.subs.forEach(function (s) { h += '↳ ' + esc(s) + '<br>'; }); }
    if (g.check) { h += '<div style="margin-top:8px;color:var(--ok)">✓ ' + esc(g.check) + '</div>'; }
    return h + '</div></details>';
  }

  function guidesHTML() {
    var h = '<div class="section active">';
    h += '<div class="cat-t">📘 Guides — how to actually do it</div>';
    h += '<div class="info">Every instruction in the map, explained in plain steps with a visual where it helps — so you act now instead of researching. No internet needed.</div>';
    h += '<input placeholder="Search guides… (e.g. breathing, band, password)" oninput="gmGuideFilter(this.value)" '
      + 'style="width:100%;margin:10px 0;padding:9px 11px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink)">';
    GUIDES.forEach(function (g) { h += guideCard(g); });
    h += '<div class="info" style="margin-top:10px">Missing a how-to you keep searching for? That’s a gap worth filling — note it in the Sunday Pulse and it becomes the next guide.</div>';
    return h + '</div>';
  }
  window.gmGuideFilter = function (v) {
    v = (v || "").toLowerCase();
    var cards = document.querySelectorAll("#sections .guide-card");
    for (var i = 0; i < cards.length; i++) {
      cards[i].style.display = cards[i].textContent.toLowerCase().indexOf(v) >= 0 ? "" : "none";
    }
  };

  /* ── 48c. INLINE HELP ENGINE — explain every specialised term where it appears ───
     The friction killer, done right: instead of a separate tab you must go to, every
     ambiguous term on EVERY screen becomes a tap-for-plain-explanation chip (first use
     only, so no clutter). Define the vocabulary once here; it self-explains everywhere.
     The six big ones link to full step-by-step how-tos. Add a term = help it app-wide. */
  var GLOSSARY = [
    // fitness / health
    { id: "zone2", k: ["zone 2", "zone-2"], t: "Zone 2 cardio", d: "A steady aerobic effort you can sustain — you can talk in full sentences but couldn’t sing. Builds your long-term heart/metabolic base.", g: "zone2" },
    { id: "box", k: ["box breathing"], t: "Box breathing", d: "Breathe in 4s, hold 4s, out 4s, hold 4s — like tracing a square. Calms the nervous system fast.", g: "breathing" },
    { id: "yoganidra", k: ["yoga nidra", "body scan"], t: "Body scan / Yoga Nidra", d: "Lie down and move your attention slowly from toes to head, noticing each part without judging. Deep relaxation.", g: "breathing" },
    { id: "plank", k: ["plank", "band rows", "band press", "push-ups"], t: "The strength moves", d: "Bodyweight + resistance-band exercises. You have a loop band — no handle attachment needed.", g: "strength" },
    // finance
    { id: "fire", k: ["fire number", "⁠fire⁠", "financial independence"], t: "FIRE / Financial Independence", d: "Having enough invested to live off it — about 25× your annual expenses — so work becomes optional." },
    { id: "swr", k: ["safe withdrawal", "swr", "3.5% swr"], t: "Safe Withdrawal Rate (SWR)", d: "The share of your corpus you can spend each year without running out — commonly ~3.5–4%." },
    { id: "ef", k: ["emergency fund"], t: "Emergency fund", d: "6 months of essential expenses kept in easy-access cash, so a shock doesn’t force you to sell investments." },
    { id: "term", k: ["term cover", "term insurance", "term ≥"], t: "Term insurance", d: "Pure life cover (no investment) — aim for 10–15× income. Pays your dependents if you die; cheap when young." },
    { id: "avalanche", k: ["avalanche"], t: "Avalanche method", d: "Pay off debts highest-interest-first (while paying minimums on the rest). Mathematically the cheapest way out of debt." },
    { id: "sip", k: ["sip", "sips"], t: "SIP", d: "Systematic Investment Plan — auto-invest a fixed amount every month, so investing happens without willpower." },
    { id: "corpus", k: ["corpus"], t: "Corpus", d: "Your total invested pot — the money working for you across funds, stocks, etc." },
    { id: "savrate", k: ["savings rate"], t: "Savings rate", d: "The % of your income you invest each month. The single biggest lever on how fast you reach independence." },
    { id: "selfocc", k: ["self-occupied", "let-out", "let out"], t: "Self-occupied vs let-out", d: "Self-occupied = the home you live in (its equity isn’t spendable). Let-out = rented out (produces income)." },
    { id: "supertop", k: ["super top-up", "top-up"], t: "Super top-up (health)", d: "Cheap extra health cover that kicks in above a base amount — a low-cost way to raise your hospital cover a lot." },
    // strategy / productivity
    { id: "okr", k: ["okr", "okrs"], t: "OKR", d: "Objective + Key Results: one clear goal plus 2–4 measurable outcomes that prove you hit it. Keep to ≤3 objectives." },
    { id: "kr", k: ["key result", "key results"], t: "Key Result", d: "A specific, measurable outcome under an objective (a number you can check), not a task." },
    { id: "metrics", k: ["kgi", "kpi", "kai", "kri", "balanced scorecard", "⁠bsc⁠"], t: "KGI / KPI / KAI / KRI / BSC", d: "A metric ladder: KGI = goal outcome, KPI = performance, KAI = the leading activity you control, KRI = risk signal, BSC = keeping four perspectives in balance." },
    { id: "woop", k: ["woop"], t: "WOOP", d: "Wish → Outcome → Obstacle → Plan. A goal method with real evidence behind it: picture the win AND the obstacle, then an if-then plan." },
    { id: "aar", k: ["after-action review", "after action review"], t: "After-Action Review (AAR)", d: "Four questions after something ends — what was meant to happen, what did, why the gap, what to change — so you actually learn from it." },
    { id: "eisen", k: ["eisenhower"], t: "Eisenhower matrix", d: "Sort tasks by urgent × important: do the important, schedule the non-urgent, delegate the merely-urgent, drop the rest." },
    { id: "deepwork", k: ["deep work"], t: "Deep Work", d: "A long, distraction-free block on one cognitively demanding task — where your most valuable output comes from." },
    { id: "pareto", k: ["80/20", "pareto", "vital few"], t: "80/20 (Pareto)", d: "About 80% of results come from 20% of the effort. Find and do that vital 20% first." },
    { id: "horizons", k: ["three horizons"], t: "Three Horizons", d: "Balance effort across today’s core (H1), the 2-year bets (H2) and the 5-year options (H3), so the future isn’t starved by the present." },
    { id: "rapid", k: ["rapid"], t: "RAPID (decision rights)", d: "Names who Recommends, Agrees, Performs, gives Input, and — the key one — Decides. One D per decision, so choices don’t stall." },
    { id: "scqa", k: ["scqa"], t: "SCQA", d: "Situation → Complication → Question → Answer: a way to open any update with the point, not a long wind-up." },
    { id: "mece", k: ["mece"], t: "MECE", d: "Mutually Exclusive, Collectively Exhaustive — break a problem into buckets that don’t overlap and leave nothing out." },
    { id: "pyramid", k: ["pyramid principle"], t: "Pyramid Principle", d: "State the answer first, then the few reasons that support it. Easy to follow, hard to waffle." },
    // security / OPSEC
    { id: "pwmgr", k: ["password manager"], t: "Password manager", d: "An app that generates and stores a strong, unique password for every account, so you remember just one. Tap for which to pick.", g: "pwmgr" },
    { id: "recmail", k: ["recovery email", "dedicated email"], t: "Dedicated recovery email", d: "A brand-new email used ONLY to recover important accounts — never shared or used to sign up for anything. Tap for setup.", g: "recoveryemail" },
    { id: "twofa", k: ["2fa", "mfa", "two-factor"], t: "2FA / MFA", d: "A second proof of identity beyond your password (a code or passkey), so a stolen password alone can’t get in." },
    { id: "passkey", k: ["passkey", "passkeys"], t: "Passkey", d: "A passwordless login tied to your device/biometrics. Phishing-resistant and easier than a password — prefer it where offered." },
    { id: "phish", k: ["phishing", "phish", "port-out", "sim pin"], t: "Phishing & SIM attacks", d: "Phishing = fake messages that trick you into giving up logins. A SIM port-out lock stops someone hijacking your phone number to beat SMS 2FA." },
    { id: "fde", k: ["full-disk encryption", "disk encryption"], t: "Full-disk encryption", d: "Scrambles everything on your device so a thief who steals it can’t read your data. On by default on most modern phones; turn it on for laptops (BitLocker/FileVault)." },
    { id: "breachmon", k: ["breach monitoring"], t: "Breach monitoring", d: "A service that alerts you if your email or passwords show up in a known data leak, so you can change them fast." },
    { id: "nist", k: ["nist csf", "csf 2.0"], t: "NIST CSF 2.0", d: "A global security scorecard with six functions — Govern, Identify, Protect, Detect, Respond, Recover — you rate 0–5 to see your gaps." },
    { id: "zerotrust", k: ["zero trust", "zero-trust"], t: "Zero trust", d: "Trust nothing by default; verify every access every time, even inside your own network. Limits the damage of any one breach." },
    { id: "blast", k: ["blast radius"], t: "Blast radius", d: "How much can break if one thing is compromised. Good design keeps it small, so a single failure can’t sink everything." },
    // habits
    { id: "floor", k: ["2-minute floor", "two-minute floor"], t: "2-minute floor", d: "The smallest version of a habit that still counts as a win (e.g. 2 minutes of movement), so you never break the chain on a bad day." },
    { id: "nmt", k: ["never miss twice", "missed twice"], t: "Never Miss Twice", d: "Missing once is human; the rule is never skip two days running. One miss is a blip, two is the start of a new (bad) habit." },
    { id: "anchor", k: ["implementation intention", "if-then", "anchor"], t: "Implementation intention", d: "A plan shaped “IF situation X, THEN I do Y” (e.g. after morning chai, I meditate). Pre-deciding the trigger makes the habit automatic." },
  ];

  function escRx(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, function (c) { return "\\" + c; }); }
  function ensureGloss() {
    if (GLOSSARY._terms) return;
    var all = [];
    GLOSSARY.forEach(function (e, i) { e.k.forEach(function (t) { all.push({ t: t.replace(/⁠/g, ""), i: i }); }); });
    all.sort(function (a, b) { return b.t.length - a.t.length; });   // longest first = greedy, correct
    GLOSSARY._terms = all;
  }
  function gmSkip(n) {
    var p = n.parentNode, SKIP = " A BUTTON INPUT TEXTAREA SELECT OPTION SUMMARY SCRIPT STYLE LABEL ";
    while (p && p !== document.body) {
      var tag = (p.tagName || "").toUpperCase();
      if (SKIP.indexOf(" " + tag + " ") >= 0) return true;
      var cn = "" + (p.className || "");
      if (cn.indexOf("gm-term") >= 0 || cn.indexOf("gm-pop") >= 0 || cn.indexOf("gm-q") >= 0) return true;
      p = p.parentNode;
    }
    return false;
  }
  function gmAnnotate(root) {
    if (!root || typeof document.createTreeWalker !== "function") return;
    ensureGloss();
    var used = {};
    GLOSSARY._terms.forEach(function (term) {
      if (used[term.i]) return;
      var rx = new RegExp("\\b(" + escRx(term.t) + ")\\b", "i");
      var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false), node;
      while ((node = w.nextNode())) {
        if (used[term.i]) break;
        if (!node.nodeValue || node.nodeValue.length < term.t.length) continue;
        if (gmSkip(node)) continue;
        var m = rx.exec(node.nodeValue);
        if (!m) continue;
        var mid = node.splitText(m.index);          // mid starts at the term
        mid.splitText(m[0].length);                 // mid is now exactly the term
        var span = document.createElement("span");
        span.className = "gm-term"; span.setAttribute("tabindex", "0"); span.setAttribute("role", "button");
        span.setAttribute("title", "What is this? Tap for a plain explanation");
        span.setAttribute("onclick", "event.stopPropagation();gmHelp(" + term.i + ",this)");
        span.textContent = mid.nodeValue;
        var q = document.createElement("sup"); q.className = "gm-q"; q.textContent = "?";
        span.appendChild(q);
        mid.parentNode.replaceChild(span, mid);
        used[term.i] = 1;
        break;                                       // one chip per term per screen
      }
    });
  }
  window.gmHelp = function (i, el) {
    var openPop = document.querySelector(".gm-pop");
    var toggling = el.nextSibling && el.nextSibling.className === "gm-pop";
    if (openPop) openPop.parentNode.removeChild(openPop);
    if (toggling) return;
    var e = GLOSSARY[i]; if (!e) return;
    var pop = document.createElement("div"); pop.className = "gm-pop";
    var h = "<b>" + esc(e.t) + "</b><br>" + esc(e.d);
    if (e.g) h += '<br><button class="btn btn-s" style="margin-top:6px" onclick="gmFullGuide(\'' + e.g + "',this)\">Show full how-to →</button>";
    pop.innerHTML = h;
    el.parentNode.insertBefore(pop, el.nextSibling);
  };
  window.gmFullGuide = function (gid, btn) {
    var g = null; GUIDES.forEach(function (x) { if (x.id === gid) g = x; });
    if (!g) return;
    var box = document.createElement("div"); box.innerHTML = guideCard(g);
    var det = box.querySelector("details"); if (det) det.open = true;
    btn.parentNode.appendChild(box); btn.style.display = "none";
  };
  // theme-safe styling (uses currentColor so it works in light + dark)
  (function () {
    try {
      var s = document.createElement("style");
      s.textContent = ".gm-term{border-bottom:1px dotted;cursor:help}"
        + ".gm-q{font-size:.7em;vertical-align:super;font-weight:700;opacity:.75;margin-left:1px}"
        + ".gm-pop{border:1px solid;border-radius:10px;padding:10px 12px;margin:8px 0;font-size:12.5px;line-height:1.6;opacity:.96}";
      (document.head || document.documentElement).appendChild(s);
    } catch (e) {}
  })();

  /* ── 48d. ASK — your estate AI + the advisor army, inside the cockpit ─────────
     Brings SecuRAX's superpowers into the one app you use: ask your LOCAL model
     (guarded, anti-hallucination), summon any of the 13 stealth advisors for a
     first-draft opinion, check your footprint before sharing (Guard, on-device),
     decide the community-proven way (Intel), and launch the estate. Everything
     routes to YOUR gateway (default localhost:8080) — nothing leaves your machine
     unless you point it elsewhere. Keep the contract/roster in sync with
     assistant/enhance.py and agents/personas.py (those are the source of truth). */
  var ASK_CONTRACT =
    "You are a precise, trustworthy advisor for a user in India (BFSI context by default). "
    + "Answer the question first in one line, then the key reasons. Use ONLY facts you are "
    + "confident about or that the user provided; if unsure, say 'I'm not certain' and state what "
    + "you'd need — never guess. Never invent numbers, names, dates, citations, prices or links; "
    + "if a live figure is needed, say it must be verified from a primary source. Be concise and "
    + "plain. If the question is ambiguous, ask ONE clarifying question. Flag when a decision needs "
    + "a professional (medical/legal/financial/tax).";
  var ADVISORS = [
    { k: "legal", n: "Legal", role: "legal advisor (India)", prof: "a licensed advocate" },
    { k: "finance", n: "Finance", role: "personal-finance advisor", prof: "a SEBI-registered adviser" },
    { k: "cfo", n: "CFO", role: "chief financial officer", prof: "a qualified CA" },
    { k: "cto", n: "CTO", role: "chief technology officer", prof: "a senior architect" },
    { k: "ciso", n: "CISO", role: "chief information security officer", prof: "a security lead/auditor" },
    { k: "tax", n: "Tax", role: "tax advisor (India)", prof: "a practising CA" },
    { k: "dietician", n: "Dietician", role: "dietician", prof: "a registered dietician/doctor" },
    { k: "coach", n: "Coach", role: "fitness coach", prof: "a certified trainer/physio" },
    { k: "chef", n: "Chef", role: "chef", prof: "your own taste-test" },
    { k: "event", n: "Events", role: "event planner", prof: "your vendors in writing" },
    { k: "intel", n: "Intel", role: "open-source intelligence analyst (ethical/defensive only)", prof: "legal counsel if sensitive" },
    { k: "career", n: "Career", role: "career coach", prof: "a mentor in your field" },
    { k: "doctor", n: "Health", role: "general physician (health literacy only, never a diagnosis)", prof: "a licensed doctor — urgently if symptoms are serious" },
    { k: "mind", n: "Mind", role: "mental-health first-aid guide (support, not therapy)", prof: "a licensed therapist; a crisis line if you are in danger" },
    { k: "relationship", n: "Relations", role: "relationship counsellor", prof: "a couples/family therapist" },
    { k: "parenting", n: "Parenting", role: "parenting coach", prof: "a paediatrician for health" },
    { k: "insurance", n: "Insurance", role: "insurance advisor", prof: "a licensed IRDAI agent/broker" },
    { k: "realestate", n: "Property", role: "real-estate advisor", prof: "a RERA agent + a property lawyer" },
    { k: "estate", n: "Estate", role: "estate-planning advisor", prof: "a lawyer for the will/deeds" },
    { k: "negotiation", n: "Negotiate", role: "negotiation coach", prof: "your own pre-set red lines" },
    { k: "productivity", n: "Productivity", role: "productivity coach", prof: "your own review" },
    { k: "eldercare", n: "Elder-care", role: "elder-care advisor", prof: "a geriatric doctor + a lawyer" },
    { k: "learning", n: "Learning", role: "learning coach", prof: "your own practice" },
    { k: "travel", n: "Travel", role: "travel planner", prof: "official visa/embassy sources" },
    { k: "home", n: "Home", role: "home-maintenance advisor", prof: "a licensed electrician/plumber for hazards" }
  ];
  var askAgent = "general", lastAskQ = "", lastAskA = "";
  function askSystem(key) {
    if (key === "general") return ASK_CONTRACT;
    var a = null; ADVISORS.forEach(function (x) { if (x.k === key) a = x; });
    if (!a) return ASK_CONTRACT;
    return ASK_CONTRACT + " For THIS request you are acting as a " + a.role
      + ". Give a practical FIRST-draft opinion (not final) and tell me to confirm anything binding with " + a.prof + ".";
  }
  // Served over HTTPS by the estate's TLS edge? Services are reached BY NAME under the same domain (hub.<domain> -> chat.<domain>, api.<domain>):
  // no port numbers anywhere, so a moved service or a new IP only changes DNS. Otherwise the plain localhost ports.
  var SECURE_ORIGIN = typeof location !== "undefined" && location.protocol === "https:";
  var ESTATE_DOM = (typeof location !== "undefined" && location.hostname.indexOf("hub.") === 0) ? location.hostname.slice(4) : "securax.localhost";
  function estateUrl(name, plain, path) { return SECURE_ORIGIN ? "https://" + name + "." + ESTATE_DOM + (path || "") : "http://localhost:" + plain + (path || ""); }
  function askGw() { return G("gm_ask_gw", estateUrl("api", 8080)); }
  // Only needed when the estate turned authentication on (./securax gateway-auth enable): a gateway key, kept on THIS device only.
  function askHdrs() { var k = G("gm_ask_key", ""); var h = { "Content-Type": "application/json" }; if (k) h.Authorization = "Bearer " + k; return h; }
  var ASK_RED = /aadhaar|\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]\b|customer|account\s*no|internal ip/i;

  function askHTML() {
    var h = '<div class="section active">';
    h += '<div class="cat-t">🤖 Ask — your local AI + advisor army</div>';
    h += '<div class="info">Ask plainly — answered by <b>your own model</b> through the guardrail gateway, kept honest (no made-up numbers). Pick an advisor for a first-draft expert opinion, then confirm anything big with a real professional.</div>';
    h += '<div id="askStatus" class="info" style="margin-top:8px;display:flex;align-items:center;gap:7px"><span style="color:var(--muted)">●</span> Checking if your local AI is ready…</div>';
    h += '<div class="chips" style="margin:8px 0"><button class="chip' + (askAgent === "general" ? " on" : "") + '" onclick="gmAskSet(\'general\')">General</button>';
    ADVISORS.forEach(function (a) { h += '<button class="chip' + (askAgent === a.k ? " on" : "") + '" onclick="gmAskSet(\'' + a.k + '\')">' + esc(a.n) + '</button>'; });
    h += '</div>';
    h += '<textarea id="askQ" placeholder="e.g. Right-size my emergency fund and term cover" style="width:100%;min-height:70px;padding:9px 11px;border:1px solid var(--line,#999);border-radius:10px;background:transparent;color:inherit"></textarea>';
    h += '<div class="row" style="margin-top:8px;display:flex;gap:8px;align-items:center"><button class="btn btn-p" onclick="gmAsk()">Ask</button><span class="info" style="margin:0;padding:4px 8px">🔒 stays on your machine</span></div>';
    h += '<div id="askOut" class="info" style="display:none;white-space:pre-wrap;margin-top:10px"></div>';
    h += '<div id="askFb" class="row" style="display:none;gap:8px;align-items:center;margin-top:8px"><span class="info" style="margin:0;padding:0">Useful?</span><button class="chip" onclick="gmAskFb(\'up\')">👍</button><button class="chip" onclick="gmAskFb(\'down\')">👎</button><span class="info" style="margin:0;padding:0" id="askFbMsg"></span></div>';

    h += '<details class="road-col" style="margin-top:14px"><summary style="cursor:pointer;font-weight:800;font-size:12.5px">🛡 Check before you share (on-device footprint scan)</summary><div style="margin-top:8px">'
      + '<div class="info">Paste a bio/profile/message about yourself — scanned on this device for over-shared identifiers. Nothing is sent.</div>'
      + '<textarea id="guardQ" placeholder="Paste text about yourself…" style="width:100%;min-height:60px;padding:9px 11px;border:1px solid var(--line,#999);border-radius:10px;background:transparent;color:inherit"></textarea>'
      + '<button class="btn btn-s" onclick="gmGuardScan()" style="margin-top:8px">Scan locally</button><div id="guardOut" style="margin-top:8px"></div></div></details>';

    h += '<details class="road-col" style="margin-top:10px"><summary style="cursor:pointer;font-weight:800;font-size:12.5px">◈ Decide the community-proven way (Intel)</summary><div style="margin-top:8px">'
      + '<div class="info">Paste the top items you collected (Reddit Top/All-time, best-sellers, top videos) — one per line, best first. Get what the crowd agrees on. On-device.</div>'
      + '<textarea id="intelItems" placeholder="e.g.\nPassed CCSP! Pete Zerger videos + LEARNZAPP\nCCSP: Pete Zerger + LEARNZAPP, Sybex for depth" style="width:100%;min-height:60px;padding:9px 11px;border:1px solid var(--line,#999);border-radius:10px;background:transparent;color:inherit"></textarea>'
      + '<input id="intelVocab" placeholder="Names you saw repeating (comma-separated) — optional" style="width:100%;margin-top:6px;padding:9px 11px;border:1px solid var(--line,#999);border-radius:10px;background:transparent;color:inherit">'
      + '<button class="btn btn-s" onclick="gmIntelGo()" style="margin-top:8px">Find the consensus</button><div id="intelOut" style="margin-top:8px"></div></div></details>';

    h += '<details class="road-col" style="margin-top:10px"><summary style="cursor:pointer;font-weight:800;font-size:12.5px">⤢ Launch the estate</summary><div style="margin-top:8px" class="info">'
      + 'With <code>./securax up</code> running: '
      + '<a href="' + estateUrl("chat", 3000) + '" target="_blank" rel="noopener">Unified chat</a> · '
      + '<a href="' + estateUrl("docs", 3001) + '" target="_blank" rel="noopener">Private docs (RAG)</a> · '
      + '<a href="' + estateUrl("flows", 5678) + '" target="_blank" rel="noopener">Automations</a> · '
      + '<a href="' + estateUrl("api", 8080, "/healthz") + '" target="_blank" rel="noopener">Gateway health</a></div></details>';

    h += '<div class="info" style="margin-top:12px">Gateway URL (change only if your estate is on another machine/Tailscale): '
      + '<input id="askGwIn" value="' + esc(askGw()) + '" style="width:100%;margin-top:4px;padding:7px 9px;border:1px solid var(--line,#999);border-radius:8px;background:transparent;color:inherit">'
      + '<button class="btn btn-s" onclick="gmAskGwSave()" style="margin-top:6px">Save</button>'
      + '<div style="margin-top:8px">Gateway key <span style="color:var(--muted)">(only if sign-in is switched on for your estate; stays on this device)</span>: '
      + '<input id="askKeyIn" type="password" autocomplete="off" value="' + esc(G("gm_ask_key", "")) + '" style="width:100%;margin-top:4px;padding:7px 9px;border:1px solid var(--line,#999);border-radius:8px;background:transparent;color:inherit">'
      + '<button class="btn btn-s" onclick="gmAskKeySave()" style="margin-top:6px">Save key</button></div></div>';
    return h + '</div>';
  }
  window.gmAskSet = function (k) { askAgent = k; renderAll(); };
  window.gmAskKeySave = function () { S_("gm_ask_key", (document.getElementById("askKeyIn").value || "").trim()); renderAll(); };
  window.gmAskGwSave = function () { var v = (document.getElementById("askGwIn").value || "").trim(); if (v) S_("gm_ask_gw", v); renderAll(); };
  // Plain-language readiness: the user double-clicks START-HERE and the page tells them,
  // in their own words, whether the AI is on, still warming up, or not running — so an
  // early-opened page is never a silent, confusing dead end. Colours match the status dots.
  function askStatusHTML(colour, msg) {
    return '<span style="color:var(--' + colour + ');font-size:15px">●</span> ' + msg;
  }
  window.gmAskPing = function () {
    var el = document.getElementById("askStatus"); if (!el) return;
    var ctl = null, done = false;
    try { ctl = new AbortController(); setTimeout(function () { if (!done && ctl) ctl.abort(); }, 4000); } catch (e) {}
    fetch(askGw().replace(/\/$/, "") + "/healthz", ctl ? { signal: ctl.signal } : {})
      .then(function (r) {
        done = true;
        el.innerHTML = r && r.ok
          ? askStatusHTML("green", "Local AI is <b>ready</b> — ask anything below. Nothing leaves your machine.")
          : askStatusHTML("amber", "Gateway is up, but the model may still be loading (first run downloads ~1 GB, about 2–5 min). Try your question in a minute.");
      })
      .catch(function () {
        done = true;
        el.innerHTML = askStatusHTML("muted", "AI is off right now — double-click <b>START-HERE</b> (or run <code>./securax up</code>) to turn it on. Everything else on this page works offline.");
      });
  };
  window.gmAsk = function () {
    var q = (document.getElementById("askQ").value || "").trim(); if (!q) return;
    var out = document.getElementById("askOut"); out.style.display = "block"; out.textContent = "Thinking… (your local model)";
    document.getElementById("askFb").style.display = "none";
    var msgs = [{ role: "system", content: askSystem(askAgent) }, { role: "user", content: q }];
    fetch(askGw().replace(/\/$/, "") + "/v1/chat/completions", { method: "POST", headers: askHdrs(), body: JSON.stringify({ model: "bank-assistant", messages: msgs }) })
      .then(function (r) {
        if (r.ok) return r.json();
        return r.text().then(function (t) {
          var typ = "", why = ""; try { var er = JSON.parse(t).error || {}; typ = er.type || ""; why = er.reason || ""; } catch (e) {}
          if (typ === "guardrail_violation" && why === "detector_unavailable")
            out.textContent = "A security detector is offline, so the estate is blocking requests (fail-closed). Your message was NOT judged unsafe. Run  ./securax doctor  \u2014 or  ./securax guard off  to use the built-in rails only. Nothing was sent.";
          else if (typ === "guardrail_violation")
            out.textContent = "Blocked by the guardrail \u2014 your message matched an attack pattern or exposed sensitive data. Rephrase and try again.";
          else if (r.status === 401 || r.status === 403)
            out.textContent = "The gateway needs a key (sign-in is switched on for this estate). Paste the gateway key into the box at the bottom of this page, or ask whoever runs SecuRAX. Nothing was sent.";
          else if (r.status === 502 || r.status === 503)
            out.textContent = "No AI model is ready yet. Add a free Gemini key (run  ./securax setup ) for instant answers, or wait for the local model to finish downloading. Nothing was sent.";
          else
            out.textContent = "The AI could not answer (HTTP " + r.status + "). Run  ./securax doctor  to check the estate. Nothing was sent.";
          return null;
        });
      })
      .then(function (j) { if (!j) return; lastAskQ = q; lastAskA = (j.choices && j.choices[0].message.content) || JSON.stringify(j); out.textContent = lastAskA; document.getElementById("askFb").style.display = "flex"; })
      .catch(function () { out.textContent = "AI is off right now — double-click START-HERE (or run  ./securax up ) to turn it on, then try again. (Nothing was sent.) If your estate is on another machine, set the gateway URL below."; });
  };
  window.gmAskFb = function (r) {
    var fb = G("gm_ask_fb", []); fb.push({ ts: ymd(), rating: r, q: lastAskQ.slice(0, 200), agent: askAgent }); S_("gm_ask_fb", fb);
    var up = 0; fb.forEach(function (x) { if (x.rating === "up") up++; });
    document.getElementById("askFbMsg").textContent = (r === "up" ? "Thanks — noted. " : "Logged to improve. ") + "(" + up + "/" + fb.length + " helpful)";
  };
  var GPII = [["PAN", /\b[A-Z]{5}\d{4}[A-Z]\b/g], ["Aadhaar-like", /\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b/g], ["Mobile", /(?:\+91[ -]?)?[6-9]\d{9}/g], ["Email", /\b[\w.+-]+@[\w-]+\.[\w.-]+\b/g], ["Card", /\b(?:\d[ -]?){13,19}\b/g]];
  window.gmGuardScan = function () {
    var t = document.getElementById("guardQ").value || "", hits = [];
    GPII.forEach(function (p) { var m = t.match(p[1]); if (m) hits.push(p[0] + " ×" + m.length); });
    var inj = /ignore (all |previous )?instructions|system prompt|you are now/i.test(t);
    document.getElementById("guardOut").innerHTML = (hits.length || inj)
      ? '<div class="info" style="border:1px solid"><b>⚠ Exposed:</b> ' + (esc(hits.join(", ")) || "—") + (inj ? "<br>⚠ Hidden instruction detected in the text." : "") + "<br>Remove these before posting anywhere public.</div>"
      : '<div class="info"><b>✓ Clean.</b> No high-risk identifiers found in this sample.</div>';
  };
  function sigW(score, rank, age, mode) { var pop = Math.log10(Math.max(score, 0) + 10), rw = 1 / (1 + 0.15 * Math.max(rank - 1, 0)); if (mode === "edge") { var f = Math.exp(-Math.max(age, 0) / 180); return pop * rw * (0.3 + 0.7 * f); } return pop * rw * (1 + Math.min(Math.max(age, 0) / 365, 5) * 0.1); }
  window.gmIntelGo = function () {
    var lines = (document.getElementById("intelItems").value || "").split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
    var vocab = (document.getElementById("intelVocab").value || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean);
    var out = document.getElementById("intelOut");
    if (!lines.length) { out.innerHTML = '<div class="info">Paste at least a few top items first.</div>'; return; }
    var tally = {};
    lines.forEach(function (text, i) {
      var w = sigW(Math.max(1, lines.length - i), i + 1, 0, "replicate");
      var names = vocab.length ? vocab : (text.match(/\b[A-Z][a-zA-Z0-9+.&]+(?:\s+[A-Z][a-zA-Z0-9+.&]+){0,2}\b/g) || []);
      names.forEach(function (name) {
        if (vocab.length) { var pat = new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g, function (c) { return "\\" + c; }).replace(/\s+/g, "\\s+"), "i"); if (!pat.test(text)) return; }
        var r = tally[name] || (tally[name] = { name: name, w: 0, m: 0 }); r.w += w; r.m++;
      });
    });
    var ranked = []; for (var k in tally) if (tally.hasOwnProperty(k)) ranked.push(tally[k]);
    ranked.sort(function (a, b) { return b.w - a.w; });
    var tot = ranked.reduce(function (a, r) { return a + r.w; }, 0) || 1;
    var html = '<div class="info"><b>What the crowd agrees on</b>' + (lines.length < 6 ? ' <span>(thin — add more top items)</span>' : '');
    ranked.slice(0, 6).forEach(function (r) { html += '<br>• ' + esc(r.name) + ' <span style="opacity:.7">×' + r.m + ' · ' + Math.round(r.w / tot * 100) + '%</span>'; });
    if (!ranked.length) html += '<br>No clear names — add the names you saw repeating above.';
    html += '<br><span style="opacity:.7">Based only on what you pasted — not invented.</span></div>';
    out.innerHTML = html;
  };

  /* ── 9. The Ops tab ─────────────────────────────────────────────── */
  function opsHTML() {
    var due = dueRituals(), broken = brokenHabits().length;
    var h = '<div class="section active">';
    h += '<div class="cat-t">\u2699 Ops</div>';
    h += '<div class="info">' + (due.length ? due.length + " ritual(s) due now (they also show on Today). " : "Nothing due today. ")
      + (broken ? broken + " habit(s) need a recovery rep." : "") + '</div>';
    h += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px"><button class="btn-sm" style="background:var(--gold);color:#0d1f35;font-weight:800" onclick="gmQuarter()">Quarterly check-in</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmCalendar()">Add the rhythm to my calendar</button></div>';
    var cad = "";
    RITUALS.forEach(function (r) {
      var log = cadenceLog(), done = log[r.id] === r.key(new Date());
      cad += '<details class="road-col" style="margin-bottom:8px"><summary style="cursor:pointer;font-weight:800;font-size:12.5px">'
        + esc(r.name) + ' <span style="font-weight:500;color:var(--muted)">\u00b7 ' + esc(r.tag) + ' \u00b7 ' + r.mins + ' min'
        + (done ? ' \u00b7 \u2713 done this cycle' : '') + '</span></summary><div style="font-size:12px;line-height:1.8;margin-top:8px">';
      r.steps.forEach(function (s) { cad += '<span style="color:var(--green)">\u25b8</span> ' + esc(s) + "<br>"; });
      if (r.id === "aar") cad += aarHTML();
      cad += '</div></details>';
    });
    h += foldHTML("\u{1F4C5} The rhythm", RITUALS.length + " rituals, each shows on Today only when due", cad, false);
    h += '<div style="margin-top:16px">' + healthHTML() + '</div>';
    h += foldHTML("\u{1F3F3} When it goes wrong", inRecovery() ? "recovery mode is ON" : "pause rituals for a bad week", recoveryHTML(), !!inRecovery());
    h += foldHTML("\u{1F517} Connections", "sync, Microsoft 365, phone reminders \u00b7 all optional",
      '<div class="info">None of these is needed to use the app. Sync copies your data to your own estate; Microsoft 365 shows today\u2019s calendar on Today; reminders nudge your phone when something is due.</div>'
      + syncHTML() + '<div style="margin-top:12px">' + msHTML() + '</div><div style="margin-top:12px">' + pushHTML() + '</div>', false);
    h += foldHTML("\u{1F9F0} Advanced tools", "optional; nothing here is needed day to day",
      rulesHTML() + '<div style="margin-top:14px">' + woopHTML() + '</div><div style="margin-top:14px">' + anchorHTML() + '</div><div style="margin-top:14px">' + csfHTML() + '</div>'
      + '<div style="margin-top:14px">' + derivedHTML() + '</div><div style="margin-top:14px">' + rapidHTML() + '</div><div style="margin-top:14px">' + toolkitHTML() + '</div>'
      + '<div style="margin-top:14px">' + kitHTML() + '</div><div style="margin-top:14px">' + frictionHTML() + '</div><div style="margin-top:14px">' + commitHTML() + '</div>'
      + '<div style="margin-top:14px">' + doneHTML() + '</div>', false);
    h += foldHTML("\u{1F4D6} Glossary", "every term in this app", glossHTML(), false);
    h += '<div class="cat-t" style="margin-top:16px">\u{1F4F1} This device</div>'
      + '<div class="info">Installed as an app, this opens offline in one tap and keeps its own copy of your data.</div>'
      + '<button class="btn btn-p" onclick="gmInstall()">Add to home screen</button>';
    h += '</div>';
    return h;
  }

  /* ═══════════════════════════════════════════════════════════════
     v15 — CALM MODE: one screen, one minute, the system does the analysis
     Measured on a phone (412 px): the first tappable action sat ~700 px down,
     under three banners, ten numbers and a stage card; the same three habits
     were asked twice; quarterly checklists showed in full every day; nine
     insight cards stacked at the bottom; setup was a 20-field form and the
     Life Map asked for the same income/net-worth again. Calm mode keeps every
     feature (one tap: "Show everything") but the default day is:
       check in (taps) -> the one open action -> what is due -> one insight.
     Nothing here asks for a new number; it reads what is already stored, and
     what the estate already knows (portal/estate-feed.json).
     ═══════════════════════════════════════════════════════════════ */
  var CALM_TABS = ["today", "ask", "life", "money", "ops"];
  function calmOn() { return G("gm_calm", true) !== false; }
  window.gmCalm = function (on) { S_("gm_calm", !!on); window.scrollTo(0, 0); renderAll(); };
  var _calmMore = false;
  window.gmCalmMore = function () { _calmMore = !_calmMore; renderAll(); };
  var _calmAllInsights = false;
  window.gmCalmInsights = function () { _calmAllInsights = !_calmAllInsights; renderAll(); };

  function calmCSS() {
    if (document.getElementById("gmCalmCss")) return;
    var st = document.createElement("style"); st.id = "gmCalmCss";
    st.textContent = "body.gm-calm #gmLost,body.gm-calm .gam,body.gm-calm #stageBar,body.gm-calm #hstats,body.gm-calm #gmExBan{display:none!important}"
      + "body.gm-calm .iw.gm-hide{display:none!important}"
      + ".gm-tap{display:inline-flex;align-items:center;justify-content:center;min-width:40px;min-height:40px;border-radius:12px;border:1.5px solid var(--border);background:var(--cardAlt);color:var(--text);font-weight:800;cursor:pointer;font-size:13px}"
      + ".gm-tap.on{background:var(--gold);border-color:var(--gold);color:#0d1f35}";
    document.head.appendChild(st);
  }

  /* -- day keys + the week, computed (no input) -- */
  function dayK(off) { var d = new Date(); d.setDate(d.getDate() - off); return (typeof dKey === "function") ? dKey(d) : ymd(d); }
  function weekStats(startOff) {
    var hits = 0, slots = 0, per = {}, en = [], energy = G("gm_energy", {});
    if (typeof HABITS === "undefined" || typeof S === "undefined") return { rate: 0, per: per, energy: null, days: 0 };
    HABITS.forEach(function (h) { per[h.id] = 0; });
    var first = Object.keys(S.daily || {}).filter(function (x) { return (S.daily[x] || []).length; }).sort()[0], days = 0;
    for (var i = startOff; i < startOff + 7; i++) {
      var k = dayK(i), got = (S.daily && S.daily[k]) || [];
      if (!first || k < first) continue;                                      // days before you started are not misses
      days++;
      hits += got.length; slots += HABITS.length;
      got.forEach(function (id) { if (per[id] !== undefined) per[id]++; });
      if (energy[k]) en.push(energy[k]);
    }
    return { rate: slots ? Math.round(hits / slots * 100) : 0, per: per, days: days,
             energy: en.length ? Math.round(en.reduce(function (a, b) { return a + b; }, 0) / en.length * 10) / 10 : null };
  }
  function weekSummary() {
    var a = weekStats(0), b = weekStats(7), lines = [];
    var d = a.rate - b.rate;
    if (!a.days) return { lines: ["No check-ins yet. Tap the Daily Three above; this card then writes your week for you."], a: a, b: b };
    lines.push("Check-ins " + (a.days < 7 ? "over your first " + a.days + " day" + (a.days > 1 ? "s" : "") : "this week") + ": " + a.rate + "%"
      + (b.days ? " (" + (d >= 0 ? "+" : "") + d + " vs last week)" : ""));
    if (typeof HABITS !== "undefined" && HABITS.length) {
      var best = null, worst = null;
      HABITS.forEach(function (h) {
        if (!best || a.per[h.id] > a.per[best.id]) best = h;
        if (!worst || a.per[h.id] < a.per[worst.id]) worst = h;
      });
      if (best && a.per[best.id] > 0) lines.push("Strongest: " + best.name + " (" + a.per[best.id] + "/" + a.days + ")");
      if (a.days >= 3 && worst && best && worst.id !== best.id) lines.push("Slipping: " + worst.name + " (" + a.per[worst.id] + "/" + a.days + ") — make its floor smaller, not your ambition");
    }
    if (a.energy !== null) lines.push("Average energy: " + a.energy + "/5" + (b.energy !== null ? " (last week " + b.energy + ")" : ""));
    return { lines: lines, a: a, b: b };
  }

  /* -- 1. setup: four questions, one at a time, written once into BOTH models -- */
  var QUICK = [
    { k: "age", q: "Your age", unit: "years", ph: "36" },
    { k: "net", q: "Monthly take-home pay", unit: "₹ a month", ph: "120000" },
    { k: "exp", q: "Monthly spending, roughly", unit: "₹ a month", ph: "80000" },
    { k: "nw", q: "Savings + investments today (excluding your home)", unit: "₹ total", ph: "1500000" }
  ];
  function quickApply(ans) {
    var l = life();
    if (ans.age) { l.age = String(ans.age); gmClearExample("age"); }
    if (ans.net) { l.minc = String(ans.net); gmClearExample("minc"); if (window.P) { P.net = ans.net; if (P.example || !P.gross) P.gross = ans.net; } }
    if (ans.exp && window.P) { P.exp = ans.exp; }
    if (ans.nw) { l.nw = String(Math.round(ans.nw / 1e4) / 10); gmClearExample("nw"); if (window.P) P.nw = ans.nw; }
    if (ans.net && (isExample("inc") || !num(l.inc))) { l.inc = String(Math.round(ans.net * 12 / 1e4) / 10); gmClearExample("inc"); }   // from take-home; editable
    // An invented spouse, child, parent or loan would keep steering YOUR insights. Example-only values go; real ones stay.
    ["sage", "k1", "page", "edu", "fFixed", "fLoan", "fEF", "fSip", "ef"].forEach(function (k) { if (isExample(k)) { delete l[k]; gmClearExample(k); } });
    S_("gm_life", l);
    if (window.P) { if (P.example) P.loans = []; P.example = false; try { store("sovP", P); } catch (e) {} }
    S_("gm_quick_done", true);
    gmSnap("answered the quick setup");
    bustDerived(); renderAll();
  }
  window.gmQuickSetup = function () {
    var ans = {}, i = 0;
    function step() {
      if (i >= QUICK.length) { gmClose(); quickApply(ans); return; }
      var q = QUICK[i];
      gmDlg('<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800">Question ' + (i + 1) + ' of ' + QUICK.length + '</div>'
        + '<div style="font-weight:800;font-size:16px;margin:6px 0 10px">' + q.q + '</div>'
        + '<input id="gmQin" inputmode="decimal" placeholder="' + q.ph + '" style="font-size:18px">'
        + '<div style="font-size:11px;color:var(--muted);margin:6px 0 12px">' + q.unit + ' · a rough number is fine; you can refine it later</div>'
        + '<div style="display:flex;gap:8px"><button class="btn-sm" id="gmQok" style="flex:1;background:var(--gold);color:#0d1f35;font-weight:800;padding:10px">Next</button>'
        + '<button class="btn-sm" id="gmQskip" style="background:var(--cardAlt);color:var(--muted);padding:10px 14px">Skip</button></div>');
      var inp = document.getElementById("gmQin");
      function next(skip) { var v = skip ? 0 : num(inp.value); if (v > 0) ans[q.k] = v; i++; step(); }
      document.getElementById("gmQok").addEventListener("click", function () { next(false); });
      document.getElementById("gmQskip").addEventListener("click", function () { next(true); });
      inp.addEventListener("keydown", function (e) { if (e.key === "Enter") next(false); });
    }
    step();
  };
  window.gmQuickLater = function () { var d = new Date(); d.setDate(d.getDate() + 7); S_("gm_quick_snooze", ymd(d)); renderAll(); };
  function setupStripHTML() {
    var example = (window.P && P.example) || exampleCount() > 0;
    if (!example || G("gm_quick_done", false) || G("gm_quick_snooze", "") > ymd()) return "";
    return '<div style="background:var(--amberBg);border:1px solid var(--amber);border-radius:12px;padding:11px 12px;margin-bottom:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">'
      + '<div style="flex:1;min-width:180px;font-size:12px;color:var(--text);line-height:1.5"><b>These are example numbers.</b> Four quick questions make them yours (about a minute). Everything else is optional.</div>'
      + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35;font-weight:800" onclick="gmQuickSetup()">Start</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--muted)" onclick="gmQuickLater()">Later</button></div>';
  }

  /* -- 2. check-in: taps only (habits + an optional energy tap; a note only if you want one) -- */
  window.gmEnergy = function (n) {
    var e = G("gm_energy", {}), k = dayK(0);
    e[k] = e[k] === n ? 0 : n; if (!e[k]) delete e[k];
    var keys = Object.keys(e).sort(); while (keys.length > 400) { delete e[keys.shift()]; }
    S_("gm_energy", e); renderAll();
  };
  window.gmNote = function () {
    var notes = G("gm_notes", {}), k = dayK(0);
    gmPrompt("One line about today (optional)", notes[k] || "what helped, what got in the way", function (v) {
      if (v === null) return;
      notes[k] = v.slice(0, 280); S_("gm_notes", notes); renderAll();
    });
  };
  function checkinHTML() {
    var h = daily3HTML(true);
    if (typeof HABITS === "undefined") return h;
    var done = (typeof todayChecks === "function") ? todayChecks() : [];
    var d3 = DAILY3.map(function (d) { return d.id; });
    var rest = [];
    HABITS.forEach(function (hb, i) { if (d3.indexOf(hb.id) < 0) rest.push([hb, i]); });
    var en = G("gm_energy", {})[dayK(0)] || 0, note = G("gm_notes", {})[dayK(0)];
    h += '<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px;margin:-4px 0 14px">';
    if (rest.length) {
      h += '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800;margin-bottom:7px">Also today (tap)</div><div style="display:flex;gap:8px;flex-wrap:wrap">';
      rest.forEach(function (r) {
        var on = done.indexOf(r[0].id) >= 0;
        h += '<button class="gm-tap' + (on ? " on" : "") + '" style="padding:0 12px" onclick="tgHabit(' + r[1] + ')">' + (on ? "✓ " : "") + esc(r[0].icon + " " + r[0].name) + '</button>';
      });
      h += '</div>';
    }
    h += '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800;margin:11px 0 7px">Energy today (optional)</div><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">';
    for (var n = 1; n <= 5; n++) h += '<button class="gm-tap' + (en === n ? " on" : "") + '" aria-label="energy ' + n + ' of 5" onclick="gmEnergy(' + n + ')">' + n + '</button>';
    h += '<span style="font-size:11.5px;color:var(--muted);margin-left:4px;cursor:pointer;text-decoration:underline" onclick="gmNote()">' + (note ? "edit note" : "+ note") + '</span></div>'
      + (note ? '<div style="font-size:11.5px;color:var(--muted);margin-top:7px;font-style:italic">“' + esc(note) + '”</div>' : '')
      + '</div>';
    return h;
  }

  /* -- 3. due now: one line each, only when actually due -- */
  var _calmOpen = null;
  window.gmCalmOpen = function (id) { _calmOpen = _calmOpen === id ? null : id; renderAll(); };
  function dueNowHTML() {
    var due = dueRituals(), broken = brokenHabits(), qd = quarterDue();
    if (!due.length && !broken.length && !qd) return "";
    var h = '<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px;margin-bottom:14px">'
      + '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800;margin-bottom:6px">Due now</div>';
    if (qd) h += '<div style="display:flex;align-items:center;gap:8px;margin:7px 0"><div style="flex:1;font-size:12.5px;color:var(--text)">\u23f1 <b>Quarterly check-in</b> <span style="color:var(--muted)">\u00b7 5 min, all taps</span></div>'
      + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35" onclick="gmQuarter()">Start</button></div>';
    broken.forEach(function (b) {
      h += '<div style="font-size:12.5px;color:var(--red);margin:6px 0">⚠ <b>' + esc(b.name) + '</b> missed twice — today the 2-minute floor is the whole job</div>';
    });
    due.forEach(function (r) {
      var open = _calmOpen === r.id;
      h += '<div style="display:flex;align-items:center;gap:8px;margin:7px 0"><div style="flex:1;font-size:12.5px;color:var(--text)">⏱ <b>' + esc(r.name) + '</b> <span style="color:var(--muted)">· ' + r.mins + ' min</span></div>'
        + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmCalmOpen(\'' + r.id + '\')">' + (open ? "Hide" : "Open") + '</button>'
        + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35" onclick="gmRitualDone(\'' + r.id + '\')">Done</button></div>';
      if (open) {
        h += '<div style="font-size:12px;line-height:1.7;margin:0 0 8px 4px;color:var(--text)">' + (r.id === "sunday" ? scqaHTML() : "");
        r.steps.forEach(function (s) { h += '<span style="color:var(--green)">▸</span> ' + esc(s) + "<br>"; });
        if (r.id === "aar") h += aarHTML();
        h += '</div>';
      }
    });
    return h + '</div>';
  }

  /* -- 4. one insight, written for you; the estate AI can turn it into a review -- */
  function weekKey() { var d = new Date(); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return ymd(d); }
  window.gmWeekReview = function () {
    var ws = weekSummary(), notes = G("gm_notes", {}), said = [];
    for (var i = 0; i < 7; i++) { var t = notes[dayK(i)]; if (t && !ASK_RED.test(t)) said.push(t); }
    var top = document.querySelector("#insights .kl, #insights b");
    var prompt = "Here is my week from my life-OS app. Write a short review: 1) what worked, 2) what slipped and the likely cause, "
      + "3) ONE small change for next week (smallest version that still counts). Plain English, at most 90 words, no lecturing.\n\n"
      + ws.lines.join("\n") + (said.length ? "\nMy one-line notes: " + said.join(" | ") : "")
      + "\nCurrent one open action: " + ((theOneAction() || {}).text || "none");
    var out = G("gm_week_review", {});
    out[weekKey()] = { at: Date.now(), text: "Asking your estate AI…" }; S_("gm_week_review", out); renderAll();
    fetch(askGw().replace(/\/$/, "") + "/v1/chat/completions", { method: "POST", headers: askHdrs(),
      body: JSON.stringify({ model: "bank-assistant", messages: [{ role: "user", content: prompt }] }) })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { var t = (((j.choices || [])[0] || {}).message || {}).content || ""; out[weekKey()] = { at: Date.now(), text: t.trim() || "(empty answer)" }; })
      .catch(function (e) { out[weekKey()] = { at: Date.now(), err: true, text: "Your estate AI is not reachable from this device (" + e.message + "). The summary above is computed here, on the device." }; })
      .then(function () { S_("gm_week_review", out); renderAll(); });
  };
  function insightHTML() {
    var ws = weekSummary(), rv = G("gm_week_review", {})[weekKey()];
    var h = '<div style="background:var(--card);border:1px solid var(--border);border-left:3px solid var(--gold);border-radius:14px;padding:13px;margin-bottom:14px">'
      + '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--gold);font-weight:800;margin-bottom:6px">This week, worked out for you</div>';
    ws.lines.forEach(function (t) { h += '<div style="font-size:12.5px;color:var(--text);line-height:1.6">• ' + esc(t) + '</div>'; });
    if (rv) h += '<div style="font-size:12.5px;color:' + (rv.err ? "var(--muted)" : "var(--text)") + ';line-height:1.65;margin-top:9px;white-space:pre-wrap">' + esc(rv.text) + '</div>';
    h += '<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">'
      + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35" onclick="gmWeekReview()">' + (rv && !rv.err ? "Review again" : "Review my week with my estate AI") + '</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmCalmInsights()">' + (_calmAllInsights ? "Hide other insights" : "Other insights") + '</button></div>'
      + '<div style="font-size:10.5px;color:var(--muted);margin-top:7px">The review is written by YOUR estate gateway (rails on); notes containing ID numbers are never sent.</div>';
    return h + '</div>';
  }

  /* -- 5. from your estate: what SecuRAX already knows, no typing (./securax lifefeed writes it) -- */
  var _feed = null, _feedTried = false;
  function feedLoad() {
    if (_feedTried) return; _feedTried = true;
    if (!/^https?:/.test(location.protocol) || typeof fetch !== "function") { _feed = G("gm_estate_feed", null); return; }
    fetch("/portal/estate-feed.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) { if (j && Array.isArray(j.items)) { _feed = j; S_("gm_estate_feed", j); renderAll(); } })
      .catch(function () { _feed = G("gm_estate_feed", null); });
  }
  function estateHTML() {
    feedLoad();
    var f = _feed;
    if (!f || !f.items || !f.items.length) return "";
    var h = '<div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px;margin-bottom:14px">'
      + '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800;margin-bottom:5px">From your estate · ' + esc(String(f.generated || "").slice(0, 16).replace("T", " ")) + '</div>';
    f.items.slice(0, 4).forEach(function (it) {
      var col = it.level === "act" ? "var(--amber)" : it.level === "ok" ? "var(--green)" : "var(--text)";
      h += '<div style="font-size:12.5px;line-height:1.6;margin:5px 0;color:' + col + '">' + esc(it.icon || "•") + ' ' + esc(it.text)
        + (it.cmd ? ' <span style="color:var(--muted);font-family:monospace;font-size:11px">' + esc(it.cmd) + '</span>' : '') + '</div>';
    });
    return h + '</div>';
  }

  function calmTodayHTML() {
    return '<div class="section active">' + setupStripHTML() + undoBar() + checkinHTML() + oneActionHTML() + dueNowHTML()
      + (inRecovery() ? "" : driftHTML() + resHTML()) + msTodayHTML() + insightHTML() + estateHTML()
      + '<div style="text-align:center;margin:6px 0 4px"><span style="font-size:11.5px;color:var(--muted);cursor:pointer;text-decoration:underline" onclick="gmCalm(false)">Show everything (all tabs, all cards)</span></div></div>';
  }
  function calmTabs() {
    var bar = document.getElementById("tabBar");
    if (!bar || typeof TABS === "undefined") return;
    var kids = bar.children;
    for (var i = 0; i < kids.length && i < TABS.length; i++) {
      var keep = _calmMore || CALM_TABS.indexOf(TABS[i][0]) >= 0 || TABS[i][0] === curTab;
      kids[i].style.display = keep ? "" : "none";
    }
    var m = document.createElement("div");
    m.className = "tab"; m.tabIndex = 0; m.textContent = _calmMore ? "Less ▴" : "More ▾";
    m.onclick = function () { gmCalmMore(); };
    bar.appendChild(m);
  }
  function calmFrame() {
    calmCSS();
    var on = calmOn();
    document.body.classList.toggle("gm-calm", on);
    var iw = document.querySelector(".iw"); if (iw) iw.classList.toggle("gm-hide", on && !_calmAllInsights);
    if (on) calmTabs();
    else if (!document.getElementById("gmCalmBack") && document.getElementById("dash")) {
      var b = document.createElement("div"); b.id = "gmCalmBack";
      b.style.cssText = "text-align:center;margin:8px 0;font-size:11.5px";
      b.innerHTML = '<span style="color:var(--muted);cursor:pointer;text-decoration:underline" onclick="gmCalm(true)">Back to Calm mode (one screen)</span>';
      var sec = document.getElementById("sections"); if (sec) sec.parentNode.insertBefore(b, sec);
    }
    if (on) { var bk = document.getElementById("gmCalmBack"); if (bk) bk.remove(); }
  }

  /* ═══════════════════════════════════════════════════════════════
     v16 — FREEZE-READY: the quarterly system you will actually run
     From the user's own screenshots: OKR sliders and the 8-slider wheel
     were "too complicated to do manually"; the After-Action Review never
     happened because nothing ever said "now"; Undo kept a 10-day-old
     snapshot (tapping it would have wiped ten days); Ops was a wall of
     tools; the "integrations" promised auto-fill but were paste boxes.
     ═══════════════════════════════════════════════════════════════ */

  /* -- 1. Quarterly check-in: grade last quarter (one tap per result) -> wheel (8 taps) -> pick up to 3 goals (taps) -- */
  var QSUG = {
    career: { o: "Make my next career move visible", krs: ["One certification exam booked or passed (./securax certs next)", "Three conversations with people already in the role I want"] },
    money: { o: "Make my money unshakeable", krs: ["Emergency fund up by one month of expenses", "Salary-day auto-transfer ran in all three months"] },
    health: { o: "Feel fit and rested again", krs: ["Move habit on 60 of 90 days", "Annual health check-up done and results read"] },
    family: { o: "Be present at home", krs: ["Family-presence habit on 60 of 90 days", "One planned family outing every month (3)"] },
    love: { o: "Invest in us", krs: ["Fortnightly couple check-in held 6 times", "One full day together, phones away"] },
    growth: { o: "Learn one hard thing properly", krs: ["Read 3 books to the end", "Finish one course or module end to end"] },
    fun: { o: "Make room for joy", krs: ["One hobby session every week (12)", "One weekend fully offline"] },
    env: { o: "Fix my surroundings", krs: ["Declutter one room completely", "Close the 3 home repairs I keep postponing"] }
  };
  var GRADES = [[0, "Not started"], [0.25, "A little"], [0.5, "Half"], [0.75, "Most of it"], [1, "Done"]];
  function qKeyNow() { var d = new Date(); return d.getFullYear() + "-Q" + (Math.floor(d.getMonth() / 3) + 1); }
  function quarterDone() { return !!G("gm_quarter_done", {})[qKeyNow()]; }
  function quarterDue() { return !quarterDone() && (new Date().getMonth() % 3 === 0 || !(S.okrs || []).length || !S.wheel); }
  function wheelSuggestions() {
    var dims = (typeof WHEEL_DIMS !== "undefined") ? WHEEL_DIMS : [];
    var ranked = dims.map(function (w, i) { return { k: w[0], label: w[1], v: wheelVal(i) }; }).sort(function (a, b) { return a.v - b.v; });
    var out = [];
    ranked.slice(0, 3).forEach(function (r) { if (QSUG[r.k]) out.push({ k: r.k, why: r.label + " is " + r.v + "/10", o: QSUG[r.k].o, krs: QSUG[r.k].krs }); });
    if (!out.some(function (x) { return x.k === "money"; })) {
      var l = life(), fixed = num(l.fFixed), ef = lakhs(l.ef) * 1e5;
      if (fixed && ef / fixed < 6) out.push({ k: "money", why: "emergency fund is " + (ef / fixed).toFixed(1) + " months", o: QSUG.money.o, krs: QSUG.money.krs });
    }
    (S.okrs || []).forEach(function (o) {
      if (okrAvg(o) < 0.7 && !out.some(function (x) { return x.o === o.o; })) out.push({ k: "keep", why: "unfinished last quarter", o: o.o, krs: o.krs.map(function (k) { return k.t; }) });
    });
    return out.slice(0, 5);
  }
  function okrAvg(o) { return o.krs.length ? o.krs.reduce(function (s, k) { return s + (+k.v || 0); }, 0) / o.krs.length : 0; }
  function qDlg(step, total, title, body, extra) {
    gmDlg('<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800">Quarterly check-in \u00b7 step ' + step + ' of ' + total + '</div>'
      + '<div style="font-weight:800;font-size:15.5px;margin:6px 0 10px;line-height:1.45">' + title + '</div>' + body
      + '<div style="display:flex;gap:8px;margin-top:12px">' + (extra || "") + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--muted);padding:9px 12px" onclick="gmClose()">Stop (progress is saved)</button></div>');
  }
  window.gmQuarter = function (opts) {
    opts = opts || {};
    var krs = [];
    (S.okrs || []).forEach(function (o, oi) { o.krs.forEach(function (k, ki) { krs.push([oi, ki]); }); });
    var dims = (typeof WHEEL_DIMS !== "undefined") ? WHEEL_DIMS : [];
    var total = opts.gradeOnly ? 1 : 3, gi = 0, wi = 0, picks = [];
    function grade() {
      if (gi >= krs.length) { if (opts.gradeOnly) { gmClose(); gmSnap("updated goal progress"); renderAll(); gmToast("Progress saved."); return; } return wheel(); }
      var o = S.okrs[krs[gi][0]], k = o.krs[krs[gi][1]];
      var b = '<div style="font-size:12px;color:var(--muted);margin-bottom:8px">Goal: ' + esc(o.o) + '</div><div style="display:flex;flex-direction:column;gap:7px">';
      GRADES.forEach(function (g) { b += '<button class="gm-tap' + (+k.v === g[0] ? " on" : "") + '" style="justify-content:flex-start;padding:0 14px" data-v="' + g[0] + '">' + g[1] + '</button>'; });
      qDlg(1, total, esc(k.t) + ' <span style="font-weight:500;color:var(--muted)">(' + (gi + 1) + '/' + krs.length + ')</span>', b + '</div>');
      [].forEach.call(document.querySelectorAll("#gmOverlay [data-v]"), function (el) {
        el.addEventListener("click", function () { k.v = +el.getAttribute("data-v"); store("sovS", S); gi++; grade(); });
      });
    }
    function wheel() {
      if (wi >= dims.length) return choose();
      var cur = (S.wheel && S.wheel[dims[wi][0]]) || 0;
      var b = '<div style="font-size:12px;color:var(--muted);margin-bottom:8px">How satisfied are you right now? 1 = very unhappy, 10 = could not be better.' + (cur ? " Last time: " + cur + "." : "") + '</div><div style="display:grid;grid-template-columns:repeat(5,1fr);gap:7px">';
      for (var v = 1; v <= 10; v++) b += '<button class="gm-tap' + (cur === v ? " on" : "") + '" data-v="' + v + '">' + v + '</button>';
      qDlg(2, total, dims[wi][1] + ' <span style="font-weight:500;color:var(--muted)">(' + (wi + 1) + '/' + dims.length + ')</span>', b + '</div>');
      [].forEach.call(document.querySelectorAll("#gmOverlay [data-v]"), function (el) {
        el.addEventListener("click", function () { whl(wi, +el.getAttribute("data-v")); wi++; wheel(); });
      });
    }
    function choose() {
      var sug = wheelSuggestions();
      var b = '<div style="font-size:12px;color:var(--muted);margin-bottom:8px">Picked from your lowest scores. Tap up to 3; each comes with two measurable results.</div><div style="display:flex;flex-direction:column;gap:8px">';
      sug.forEach(function (x, i) {
        b += '<button class="gm-tap" style="justify-content:flex-start;text-align:left;padding:9px 12px;line-height:1.4;flex-direction:column;align-items:flex-start" data-i="' + i + '"><span>' + esc(x.o) + '</span>'
          + '<span style="font-weight:500;font-size:11px;opacity:.8">' + esc(x.why) + ' \u00b7 ' + esc(x.krs.join(" \u00b7 ")) + '</span></button>';
      });
      qDlg(3, total, "Your goals for this quarter", b + '</div>', '<button class="btn-sm" id="gmQfin" style="flex:1;background:var(--gold);color:#0d1f35;font-weight:800;padding:10px">Save my quarter</button>');
      [].forEach.call(document.querySelectorAll("#gmOverlay [data-i]"), function (el) {
        el.addEventListener("click", function () {
          var i = +el.getAttribute("data-i"), at = picks.indexOf(i);
          if (at >= 0) picks.splice(at, 1); else if (picks.length < 3) picks.push(i); else { gmToast("Three is the limit: fewer, deeper."); return; }
          el.classList.toggle("on", picks.indexOf(i) >= 0);
        });
      });
      document.getElementById("gmQfin").addEventListener("click", function () {
        gmSnap("finished the quarterly check-in");
        var hist = G("gm_okr_hist", []);
        if ((S.okrs || []).length) hist.push({ q: G("gm_okr_q", "") || "before " + qKeyNow(), okrs: JSON.parse(JSON.stringify(S.okrs)), avg: Math.round(S.okrs.reduce(function (s, o) { return s + okrAvg(o); }, 0) / S.okrs.length * 100) / 100 });
        while (hist.length > 12) hist.shift();
        S_("gm_okr_hist", hist);
        if (picks.length) { S.okrs = picks.map(function (i) { var x = sug[i]; return { o: x.o, krs: x.krs.map(function (t) { return { t: t, v: 0 }; }) }; }); }
        store("sovS", S); S_("gm_okr_q", qKeyNow());
        var done = G("gm_quarter_done", {}); done[qKeyNow()] = ymd(); S_("gm_quarter_done", done);
        gmClose(); renderAll();
        gmDlg('<div style="font-weight:800;font-size:15px;margin-bottom:8px">Quarter saved</div><div style="font-size:12.5px;line-height:1.6;color:var(--text)">'
          + (picks.length ? picks.length + " goal(s) set. Update progress once a month with one tap per result (Today \u2192 Due now, or the OKRs tab)." : "Wheel saved; your goals stay as they were.")
          + '<br><br>Make it a system: put the whole rhythm in your calendar once (quarterly, monthly, weekly).</div>'
          + '<div style="display:flex;gap:8px;margin-top:12px"><button class="btn-sm" style="flex:1;background:var(--gold);color:#0d1f35;font-weight:800;padding:10px" onclick="gmCalendar();gmClose()">Add to my calendar</button>'
          + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--muted);padding:10px" onclick="gmClose()">Close</button></div>');
      });
    }
    if (krs.length && !G("gm_quarter_done", {})[qKeyNow()]) grade(); else if (opts.gradeOnly) { if (krs.length) grade(); else gmToast("No goals yet: start the quarterly check-in."); } else wheel();
  };
  function quarterCardHTML(tab) {
    var due = quarterDue(), n = (S.okrs || []).length;
    return '<div style="background:var(--card);border:2px solid var(--gold);border-radius:14px;padding:13px;margin:12px 13px 0">'
      + '<div style="font-weight:800;font-size:13.5px;color:var(--text)">' + (due ? "\u23f1 Quarterly check-in is due" : "\u2713 Quarterly check-in done for " + qKeyNow()) + '</div>'
      + '<div style="font-size:12px;color:var(--muted);line-height:1.55;margin:5px 0 9px">About 5 minutes, all taps: grade last quarter, rate the 8 areas of life, pick up to 3 goals from your lowest scores.</div>'
      + '<div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn-sm" style="background:var(--gold);color:#0d1f35;font-weight:800" onclick="gmQuarter()">' + (due ? "Start" : "Redo") + '</button>'
      + (n && tab === "okr" ? '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmQuarter({gradeOnly:true})">Update progress (taps)</button>' : '')
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmCalendar()">Add rhythm to calendar</button></div></div>';
  }

  /* -- 2. The rhythm in your calendar: one .ics, recurring, with what to do written in each event -- */
  function nextOn(month0s, nth, dow, hh) {           // first future date that is the nth <dow> of one of month0s (null = every month)
    var d = new Date(); d.setHours(0, 0, 0, 0);
    for (var add = 0; add < 400; add++) {
      var t = new Date(d); t.setDate(d.getDate() + add);
      if (t.getDay() !== dow) continue;
      if (month0s && month0s.indexOf(t.getMonth()) < 0) continue;
      if (nth && Math.ceil(t.getDate() / 7) !== nth) continue;
      if (add === 0 && new Date().getHours() >= hh) continue;
      return t;
    }
    return d;
  }
  function icsDate(d, hh, mm) { function z(n) { return (n < 10 ? "0" : "") + n; } return d.getFullYear() + z(d.getMonth() + 1) + z(d.getDate()) + "T" + z(hh) + z(mm) + "00"; }
  function icsText(t) { return String(t).replace(/\\/g, "\\\\").replace(/;/g, "\;").replace(/,/g, "\\,").replace(/\n/g, "\\n"); }
  function icsFold(line) { var out = [], s = line; while (s.length > 74) { out.push(s.slice(0, 74)); s = " " + s.slice(74); } out.push(s); return out.join("\r\n"); }
  function rhythmEvents() {
    var url = location.origin && /^https?:/.test(location.protocol) ? location.origin + "/" : "";
    return [
      { id: "quarter", name: "Quarterly check-in (Guiding Map)", rule: "FREQ=YEARLY;BYMONTH=1,4,7,10;BYDAY=1SA", start: nextOn([0, 3, 6, 9], 1, 6, 10), hh: 10, mins: 60,
        desc: "Open the Guiding Map > Today > Due now > Quarterly check-in: grade last quarter, rate 8 areas (taps), pick up to 3 goals. Then the Quarterly Review and Red-Team checklists (Due now > Open)." },
      { id: "monthly", name: "Monthly review: money + After-Action Review", rule: "FREQ=MONTHLY;BYDAY=1SU", start: nextOn(null, 1, 0, 10), hh: 10, mins: 45,
        desc: "Money Date numbers, then the four questions: what did I plan, what happened, why, what will I change. Update goal progress (one tap per result)." },
      { id: "weekly", name: "Sunday Pulse (20 min)", rule: "FREQ=WEEKLY;BYDAY=SU", start: nextOn(null, 0, 0, 19), hh: 19, mins: 20,
        desc: "Open Today: read 'This week, worked out for you' and tap 'Review my week with my estate AI'. Pick the one change for next week." },
      { id: "tax", name: "April tax lock-in", rule: "FREQ=YEARLY;BYMONTH=4;BYDAY=1SA", start: nextOn([3], 1, 6, 11), hh: 11, mins: 90,
        desc: "Choose the tax regime for the year, plan the year's tax-saving investments, collect Form 16 / AIS. (Guiding Map > Ops > cadence.)" },
      { id: "annual", name: "Annual overhaul", rule: "FREQ=YEARLY;BYMONTH=8;BYDAY=1SA", start: nextOn([7], 1, 6, 10), hh: 10, mins: 240,
        desc: "Insurance re-quote, will and nominations, property checks, the hit-by-a-bus test with your partner. (Guiding Map > Ops > cadence.)" }
    ].map(function (e) { e.url = url; return e; });
  }
  window.gmCalendarICS = function () {
    var now = new Date(), stamp = icsDate(now, now.getHours(), now.getMinutes());
    var L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//SecuRAX//Guiding Map rhythm//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:Life OS rhythm"];
    rhythmEvents().forEach(function (e) {
      var end = new Date(e.start); end.setHours(e.hh, e.mins, 0, 0);
      L.push("BEGIN:VEVENT", "UID:securax-gm-" + e.id + "@local", "DTSTAMP:" + stamp,
        "DTSTART:" + icsDate(e.start, e.hh, 0), "DTEND:" + icsDate(end, end.getHours(), end.getMinutes()), "RRULE:" + e.rule,
        icsFold("SUMMARY:" + icsText(e.name)), icsFold("DESCRIPTION:" + icsText(e.desc + (e.url ? "\nOpen: " + e.url : ""))),
        "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + icsText(e.name), "TRIGGER:-PT30M", "END:VALARM", "END:VEVENT");
    });
    L.push("END:VCALENDAR");
    return L.join("\r\n") + "\r\n";
  };
  window.gmCalendar = function () {
    var ics = gmCalendarICS();
    try {
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
      a.download = "life-os-rhythm.ics"; document.body.appendChild(a); a.click(); a.remove();
    } catch (e) {}
    S_("gm_cal_exported", ymd());
    gmToast("Calendar file saved. Open it to add 5 repeating events (quarterly, monthly, weekly, April, August). Already added them by hand? Skip this.");
  };

  /* -- 3. The After-Action Review now has a moment: the last week of every month, in Due now and in the calendar -- */
  if (typeof RITUALS !== "undefined" && !RITUALS.some(function (r) { return r.id === "aar"; })) {
    RITUALS.push({ id: "aar", name: "Monthly After-Action Review", mins: 15, tag: "Monthly \u00b7 last week",
      window: function (d) { return d.getDate() >= 24; },
      key: function (d) { return "aar-" + d.getFullYear() + "-" + (d.getMonth() + 1); },
      steps: ["What did I plan this month?", "What actually happened?", "Why the difference? (one cause, not a list)", "What will I do differently next month? (one change)"] });
  }

  /* -- 4. Undo you can trust: it only offers the last 30 minutes, says what it does, and can be dismissed -- */
  var UNDO_MS = 30 * 60 * 1000;
  window.gmUndoDismiss = function () { localStorage.removeItem("gm_undo"); renderAll(); };
  function undoFresh() { var u = G("gm_undo", null); return u && Date.now() - u.at < UNDO_MS ? u : null; }

  /* -- 5. Recovery mode: asks before pausing; when on, says until when and ends with one tap -- */
  window.gmRecoveryAsk = function (days) {
    gmConfirm("Pause every ritual for " + days + " days? Only the daily three stay; nothing piles up against you. You can end it early at any time.", function (y) { if (y) gmRecoveryOn(days); });
  };
  function recoveryHTML() {
    var r = inRecovery();
    if (r) return '<div class="info" style="border:1.5px solid var(--amber)">Recovery mode is <b>on</b> until ' + esc(r.until.slice(0, 10)) + '. <button class="btn-sm" style="background:var(--gold);color:#0d1f35;margin-left:6px" onclick="gmRecoveryOff()">End it now</button></div>';
    return '<div class="info">A bad week (illness, a crisis at work)? Pause the rituals instead of abandoning the app. Only the daily three stay.</div>'
      + '<div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmRecoveryAsk(7)">Pause 7 days\u2026</button>'
      + '<button class="btn-sm" style="background:var(--cardAlt);color:var(--text)" onclick="gmRecoveryAsk(14)">Pause 14 days\u2026</button></div>';
  }

  /* -- 6. Kids: add a child right here (name + date of birth); the plan appears at once -- */
  window.gmKidAdd = function () {
    var n = (document.getElementById("gmKidN") || {}).value, d = (document.getElementById("gmKidD") || {}).value;
    if (!n || !d) { gmToast("Name and date of birth, please."); return; }
    gmSnap("added a child"); P.kids = P.kids || []; P.kids.push({ name: n.trim().slice(0, 40), dob: d }); store("sovP", P); renderAll();
  };
  function kidAddHTML(first) {
    return '<div class="road-col" style="margin-bottom:12px"><div style="font-weight:800;font-size:13px;margin-bottom:6px">' + (first ? "Add your child" : "Add another child") + '</div>'
      + '<div class="f-row"><div><label class="f-label">First name</label><input id="gmKidN" type="text"></div><div><label class="f-label">Date of birth</label><input id="gmKidD" type="date"></div></div>'
      + '<button class="btn-sm" style="background:var(--gold);color:#0d1f35;font-weight:800;margin-top:8px" onclick="gmKidAdd()">Add</button>'
      + '<div style="font-size:11px;color:var(--muted);margin-top:6px">The stage plan, health-calendar items and the education-fund schedule appear automatically. Stays on this device.</div></div>';
  }

  /* -- 6b. Each child gets THIS quarter's three actions (tick them) and the monthly SIP that funds their education -- */
  var KID_ACTIONS = [
    [2, ["Vaccinations up to date on the IAP schedule (check the card)", "15 minutes a day of talking, reading or singing together", "Growth and development check with the paediatrician"]],
    [5, ["Read together at least 5 nights a week", "One outdoor physical activity every day", "Dental check (every 6 months)"]],
    [12, ["One sport and one skill both running (confirm the classes)", "Pocket money in three jars: spend, save, give", "Eye and dental check"]],
    [17, ["One career-exposure day (shadow someone, visit a workplace)", "Show them the family budget once and answer every question", "Annual health check, including how they are really doing"]],
    [99, ["Plan how the education fund will be drawn down", "Teach them to run this dashboard for themselves", "Agree how you will support them for the next two years"]]
  ];
  window.gmKidTick = function (key) { var d = G("gm_kid_done", {}); if (d[key]) delete d[key]; else d[key] = ymd(); S_("gm_kid_done", d); renderAll(); };
  function kidFund(ka) {
    if (ka >= 18) return "";
    var cost = num(life().edu) ? lakhs(life().edu) : 25, yrs = 18 - ka, need = cost * Math.pow(1.10, yrs);
    var n = yrs * 12, r = 0.12 / 12, sip = need * 1e5 / ((Math.pow(1 + r, n) - 1) / r);
    return '<div style="font-size:12px;color:var(--text);margin-top:8px;line-height:1.55">\u{1F393} Education fund: about <b>' + money(Math.round(sip / 100) * 100) + ' a month</b> from now reaches about ' + money(need * 1e5) + ' at 18.</div>'
      + '<div style="font-size:10.5px;color:var(--muted)">Assumes today’s cost of ' + money(cost * 1e5) + ' (edit "Degree you are planning for" in Life Map), 10% a year education inflation and 12% a year from equity funds. A plan, not a promise.</div>';
  }
  window.kidStage = function (k) {
    var ka = age(k.dob), list = null;
    KID_ACTIONS.forEach(function (x) { if (!list && ka <= x[0]) list = x[1]; });
    var stages = [[2, "0-2: The 1000-day window"], [5, "3-5: Play-based learning"], [12, "6-12: Skills and character"], [17, "13-17: Direction years"], [99, "18+: Launch"]];
    var st = ""; stages.forEach(function (x) { if (!st && ka <= x[0]) st = x[1]; });
    var done = G("gm_kid_done", {}), q = qKeyNow(), h = '<div class="kid-stage"><div class="ks-t">' + esc(k.name) + ' — age ' + ka + '</div><div class="ks-s">' + st + '</div>'
      + '<div style="font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);font-weight:800;margin:9px 0 5px">This quarter (' + q + ')</div>';
    list.forEach(function (t, i) {
      var key = k.name + "|" + q + "|" + i, on = !!done[key];
      h += '<div role="button" tabindex="0" onclick="gmKidTick(decodeURIComponent(\'' + encodeURIComponent(key).replace(/'/g, "%27") + '\'))" style="display:flex;gap:9px;align-items:flex-start;cursor:pointer;margin:6px 0;font-size:12.5px;color:var(--text);line-height:1.5">'
        + '<span class="gm-tap' + (on ? " on" : "") + '" style="min-width:26px;min-height:26px;border-radius:8px;font-size:12px">' + (on ? "✓" : "") + '</span><span' + (on ? ' style="text-decoration:line-through;opacity:.7"' : '') + '>' + esc(t) + '</span></div>';
    });
    return h + kidFund(ka) + '</div>';
  };

  /* -- 7. Ops in three parts: what is due (and the calendar), your connections, then advanced tools folded away -- */
  function foldHTML(title, sub, inner, open) {
    return '<details class="road-col" style="margin-top:12px"' + (open ? " open" : "") + '><summary style="cursor:pointer;font-weight:800;font-size:13px">' + title
      + (sub ? ' <span style="font-weight:500;color:var(--muted);font-size:11.5px">\u00b7 ' + sub + '</span>' : '') + '</summary><div style="margin-top:10px">' + inner + '</div></details>';
  }

  /* ── 10. Wire into the existing render loop ─────────────────────── */
  if (typeof TABS !== "undefined") {
    var keep = TABS.filter(function (t) { return ["today", "map"].indexOf(t[0]) < 0; });
    var today = TABS.filter(function (t) { return t[0] === "today"; });
    var map = TABS.filter(function (t) { return t[0] === "map"; });
    TABS.length = 0;
    today.concat([["ask", "\ud83e\udd16 Ask"], ["guide", "\ud83d\udcd8 Guides"], ["stack", "\u{1F3DB} Stack"], ["life", "\u{1F9ED} Life Map"],
      ["prop", "\u{1F3E0} Property"], ["ops", "\u2699 Ops"]]).concat(map).concat(keep)
      .forEach(function (t) { TABS.push(t); });
  }
  var _renderAll = window.renderAll;
  var _pendingRender = false;
  window.renderAll = function () {
    // Never rebuild the DOM out from under someone who is mid-entry.
    if (isTyping() && !_pendingRender) {
      _pendingRender = true;
      document.activeElement.addEventListener("blur", function () {
        _pendingRender = false; renderAll();
      }, { once: true });
      return;
    }
    _pendingRender = false;
    try { _renderAll.apply(this, arguments); } catch (e) { console.log(e); }
    var box = document.getElementById("sections");
    if (!box) return;
    var old = document.getElementById("gmVitals");
    if (old) old.parentNode.removeChild(old);
    document.body.insertAdjacentHTML("beforeend", vitalsHTML());
    if (curTab === "ask") { box.innerHTML = askHTML(); try { gmAskPing(); } catch (e) {} }
    else if (curTab === "guide") { box.innerHTML = guidesHTML(); }
    else if (curTab === "ops") { box.innerHTML = opsHTML(); }
    else if (curTab === "stack") { box.innerHTML = stackHTML(); }
    else if (curTab === "life") { box.innerHTML = lifeMapHTML(); }
    else if (curTab === "prop") { box.innerHTML = propHTML(); }
    else if (curTab === "today" && calmOn()) { box.innerHTML = calmTodayHTML(); }
    else if (curTab === "okr" || curTab === "wheel") { box.insertAdjacentHTML("afterbegin", quarterCardHTML(curTab)); }
    else if (curTab === "kids" && window.P) {
      var sec = box.querySelector(".section");
      if (sec) { var inf = sec.querySelector(".info"); if (!P.kids.length && inf) inf.outerHTML = kidAddHTML(true); else if (P.kids.length) sec.insertAdjacentHTML("beforeend", kidAddHTML(false)); }
    }
    else if (curTab === "today") {
      box.insertAdjacentHTML("afterbegin", exampleWarn() + undoBar() + daily3HTML() + msTodayHTML()
        + (inRecovery() ? "" : driftHTML() + resHTML()) + oneActionHTML() + (inRecovery() ? "" : pinnedHTML()));
    }
    try { calmFrame(); } catch (e) { console.log(e); }
    // Inline help: self-explain every specialised term on whatever screen just rendered.
    try { gmAnnotate(box); } catch (e) { }
  };

  /* ── 11. Boot ───────────────────────────────────────────────────── */
  // An installed PWA is resumed far more often than it is loaded. Pulling only
  // on "load" is why one device sat on stale state for days.
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") gmSyncInit();
  });
  window.addEventListener("online", function () { gmSyncInit(); });

  // A service worker cannot complete an interactive Access OTP login.
  if (navigator.serviceWorker) {
    navigator.serviceWorker.addEventListener("message", function (e) {
      if (e.data && e.data.type === "AUTH_EXPIRED") location.reload();
    });
  }

  window.addEventListener("load", function () {
    try { curTab = "today"; } catch (e) {}
    var qc = new URLSearchParams(location.search).get("code");
    if (qc && msCfg()) { msExchange(qc).then(gmMsPull).catch(function (e) { console.log("[ms]", e.message); }); }
    else if (msTok()) {
      var mc = G("gm_ms_cache", null);
      if (!mc || nowSrv() - mc.at > 1800000) gmMsPull();
    }
    // Auto-fill Life Map on first visit (no age + no income = never filled)
    var l = life();
    if (!l.age && !l.inc) {
      gmTplLife();
    }
    // Auto-fill example properties on first visit so the Property tab is explorable
    try { var pr = G("gm_props", null); if ((!pr || !pr.length) && window.P && window.P.example) { if (window.gmTplProp) gmTplProp(); } } catch (e) {}
    gmSyncLinkImport();
    gmSyncInit();
    if (window.renderAll) renderAll();
    // Monthly backup nudge, once per month, non-blocking
    var last = G("gm_backup_seen", "");
    var mk = new Date().getFullYear() + "-" + (new Date().getMonth() + 1);
    if (new Date().getDate() <= 7 && last !== mk && !inRecovery()) {
      S_("gm_backup_seen", mk);
      setTimeout(function () {
        if (confirm("Monthly ritual: export a dated JSON backup now?")) {
          if (window.gmExportBackup) gmExportBackup();
        }
      }, 1500);
    }
  });
})();
