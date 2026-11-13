/* Rhythm: the reviews that keep a programme honest (weekly, monthly, quarterly, yearly), each with its checklist.
   The app does the remembering: anything due or late rises to Today. Marking one done stamps it; the next one dates itself. */
(function () {
  var K = window.OSK;
  var EVERY = { week: 7, fortnight: 14, month: 30, quarter: 91, half: 182, year: 365 };
  function items() { return (K.cfg("cadence") || {}).items || []; }
  function log() { return K.get("cadence", {}); }
  K.cadenceDue = function (it) {
    var done = (log()[it.id] || []), last = done[done.length - 1];
    var start = K.get("started", K.ymd()), gap = EVERY[it.every] || +it.every || 30;
    var due = last ? K.addDays(last, gap) : K.addDays(start, Math.min(gap, it.first || 7) - 1);
    return { last: last || null, due: due, late: K.days(due) };   // late > 0: days past due
  };
  // The rhythm in the calendar (principle `in-the-calendar`): one repeating event per review, made from this edition's own
  // cadence list, so the ids there are the permanent UIDs. An edition item may set "cal" (rule + start, hh, mins), "v" and
  // "retired"; otherwise the rule follows "every" and "first". Never delete an item: retire it.
  function calOf(it) {
    var c = it.cal || {}, f = +it.first || 1, D = K.icsDays;
    var dayOfMonth = Math.min(28, ((f - 1) % 28) + 1);
    var hh = c.hh || (it.every === "week" ? 9 : 10), rule, match;
    if (c.rule && c.start) {                                           // a custom rule names its own fixed first date (YYYY-MM-DD)
      rule = c.rule; var st = String(c.start); match = function (x) { return K.ymd(x) >= st; };
    }
    else if (it.every === "week" || it.every === "fortnight") {
      var dow = it.every === "week" ? (f % 7) : ((f % 5) + 1);          // week: first = weekday (1 = Monday); fortnight: a weekday
      rule = "FREQ=WEEKLY;" + (it.every === "fortnight" ? "INTERVAL=2;" : "") + "BYDAY=" + D[dow];
      match = function (t) { return t.getDay() === dow; };
    } else if (it.every === "year") {
      var mon = Math.min(11, Math.floor((f - 1) / 30));                  // year: "first" days in becomes a month and a day
      rule = "FREQ=YEARLY;BYMONTH=" + (mon + 1) + ";BYMONTHDAY=" + dayOfMonth;
      match = function (t) { return t.getMonth() === mon && t.getDate() === dayOfMonth; };
    } else {
      var n = { month: 1, quarter: 3, half: 6 }[it.every] || 1;
      rule = "FREQ=MONTHLY;" + (n > 1 ? "INTERVAL=" + n + ";" : "") + "BYMONTHDAY=" + dayOfMonth;
      match = function (t) { return t.getDate() === dayOfMonth; };
    }
    var desc = (it.why ? it.why + "\n" : "") + (it.checklist || []).map(function (s) { return "- " + s; }).join("\n");
    return { id: it.id, v: it.v || 1, retired: it.retired || "", name: it.name, desc: desc, rule: rule, start: K.calFirst(match), hh: hh, mins: c.mins || (it.every === "week" ? 30 : 60) };
  }
  K.cadenceICS = function () { return K.ics((K.edition().name || "OS kit") + " rhythm", items().map(calOf)); };
  function row(it) {
    var st = K.cadenceDue(it), open = K._cad === it.id, ck = K.get("cadChk", {})[it.id] || [];
    var tag = st.late > 0 ? '<span class="tag late">' + K.esc(K.t("cadence.days_late", "{n} day(s) late", { n: st.late })) + "</span>" : st.late === 0 ? '<span class="tag due">' + K.esc(K.t("cadence.due_today", "due today")) + '</span>' : '<span class="muted">' + K.esc(K.t("cadence.next", "next {d}", { d: st.due })) + "</span>";
    var h = '<li class="row"><div class="grow"><b>' + K.esc(it.name) + '</b> <span class="muted">' + K.esc(K.t("cadence.every", "every {n}", { n: it.every })) + "</span> " + tag + (it.why ? '<div class="muted">' + K.esc(it.why) + "</div>" : "") + "</div>"
      + '<button data-a="cadOpen" data-x="' + K.esc(it.id) + '" aria-expanded="' + open + '">' + K.esc(K.t(open ? "cadence.close" : "cadence.open", open ? "Close" : "Open")) + "</button></li>";
    if (open) {
      h += '<li class="form"><ul class="list">' + (it.checklist || []).map(function (s, i) {
        var on = ck.indexOf(i) >= 0;
        return '<li class="row tick' + (on ? " done" : "") + '"><button class="check sx-check" data-a="cadChk" data-x="' + K.esc(it.id + "|" + i) + '" aria-pressed="' + on + '" aria-label="' + K.esc(K.t("cadence.step_n", "Step {n}", { n: i + 1 })) + '">' + (on ? "✓" : "") + '</button><div class="grow">' + K.esc(s) + "</div></li>";
      }).join("") + "</ul>" + (it.cmd ? '<p class="muted">' + K.esc(K.t("cadence.on_estate", "On the estate: ")) + '<code>' + K.esc(it.cmd) + "</code></p>" : "")
        + '<button class="primary" data-a="cadDone" data-x="' + K.esc(it.id) + '">' + K.esc(K.t("cadence.mark_done", "Mark done for this {n}", { n: it.every })) + "</button></li>";
    }
    return h;
  }
  K.module({
    id: "cadence", label: function () { return K.term("cadence", "Rhythm"); },
    render: function () {
      var c = K.cfg("cadence") || {}, L = items().slice();
      L.sort(function (a, b) { return K.cadenceDue(b).late - K.cadenceDue(a).late; });
      var now = L.filter(function (it) { return K.cadenceDue(it).late >= 0; }), later = L.filter(function (it) { return K.cadenceDue(it).late < 0; });
      return "<h2>" + K.esc(K.term("cadence", "Rhythm")) + "</h2>" + (c.intro ? '<p class="muted">' + K.esc(c.intro) + "</p>" : "")
        + '<p><button class="' + (K._cad ? "" : "primary") + '" data-a="cadCal" data-haptic="success">' + K.esc(K.t("cadence.add_calendar", "Add the rhythm to my calendar")) + '</button></p>'
        // one-open-action: what is due or late is shown, most late first; the rest waits under "Later (n)"
        + K.card("", (now.length ? "<ul class='list'>" + now.map(row).join("") + "</ul>" : "<p>" + K.esc(K.t("cadence.nothing_due", "Nothing is due. Every review is on time.")) + "</p>")
          + (later.length ? '<details class="later"' + (later.some(function (it) { return it.id === K._cad; }) ? " open" : "") + '><summary>' + K.esc(K.t("cadence.later", "Later ({n})", { n: later.length })) + '</summary><ul class="list">' + later.map(row).join("") + "</ul></details>" : ""));
    },
    next: function () {
      var out = [];
      items().forEach(function (it) { var st = K.cadenceDue(it); if (st.late >= 0) out.push({ score: 70 + Math.min(st.late, 20) + (it.weight || 0), text: st.late > 0 ? K.t("cadence.next_late", "{n} ({d} day(s) late)", { n: it.name, d: st.late }) : K.t("cadence.next_due_today", "{n} is due today", { n: it.name }), why: it.why || "", go: "cadence" }); });
      return out;
    },
    week: function (from) {
      var n = 0, lg = log(); Object.keys(lg).forEach(function (k) { (lg[k] || []).forEach(function (d) { if (d >= from) n++; }); });
      return n ? [{ n: n, what: K.t("cadence.week", "review(s) done on time or caught up") }] : [];
    },
    // the share of reviews done within a week of their due date, over the last 90 days (feeds the resilience index)
    onTime: function () {
      var lg = log(), hit = 0, all = 0, from = K.addDays(K.ymd(), -90);
      items().forEach(function (it) {
        var st = K.cadenceDue(it), d = lg[it.id] || [];
        d.forEach(function (x) { if (x >= from) { all++; hit++; } });
        if (st.late > 7) all++;
      });
      return all ? hit / all : null;
    },
    acts: {
      cadCal: function () {
        K.download((K.edition().id || "kit") + "-rhythm.ics", K.cadenceICS(), "text/calendar");
        K.set("calExported", K.ymd(), { noUndo: true });
        K.toast(K.t("cadence.toast_saved", "Calendar file saved: {n} repeating reviews. Add them to the same calendar each time; a newer file updates them, it never doubles them.", { n: items().length }));
      },
      cadOpen: function (id) { K._cad = K._cad === id ? null : id; K.render(); },
      cadChk: function (x) {
        var p = String(x).split("|"), m = K.get("cadChk", {}), a = m[p[0]] || (m[p[0]] = []), i = +p[1], j = a.indexOf(i);
        if (j >= 0) a.splice(j, 1); else a.push(i);
        K.set("cadChk", m, { what: "step" }); K.render();
      },
      cadDone: function (id) {
        var lg = log(), a = lg[id] || (lg[id] = []); if (a[a.length - 1] !== K.ymd()) a.push(K.ymd());
        lg[id] = a.slice(-60);
        var m = K.get("cadChk", {}); delete m[id];
        K.set("cadence", lg, { what: "review done" }); K.set("cadChk", m, { noUndo: true }); K._cad = null; K.render(); K.toast(K.t("cadence.toast_done", "Done. The next one is dated by itself."));
      }
    }
  });
})();
