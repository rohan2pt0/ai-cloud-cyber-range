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
  function row(it) {
    var st = K.cadenceDue(it), open = K._cad === it.id, ck = K.get("cadChk", {})[it.id] || [];
    var tag = st.late > 0 ? '<span class="tag late">' + st.late + " day(s) late</span>" : st.late === 0 ? '<span class="tag due">due today</span>' : '<span class="muted">next ' + K.esc(st.due) + "</span>";
    var h = '<li class="row"><div class="grow"><b>' + K.esc(it.name) + '</b> <span class="muted">every ' + K.esc(it.every) + "</span> " + tag + (it.why ? '<div class="muted">' + K.esc(it.why) + "</div>" : "") + "</div>"
      + '<button data-a="cadOpen" data-x="' + K.esc(it.id) + '" aria-expanded="' + open + '">' + (open ? "Close" : "Open") + "</button></li>";
    if (open) {
      h += '<li class="form"><ul class="list">' + (it.checklist || []).map(function (s, i) {
        var on = ck.indexOf(i) >= 0;
        return '<li class="row tick' + (on ? " done" : "") + '"><button class="check" data-a="cadChk" data-x="' + K.esc(it.id + "|" + i) + '" aria-pressed="' + on + '" aria-label="Step ' + (i + 1) + '">' + (on ? "✓" : "") + '</button><div class="grow">' + K.esc(s) + "</div></li>";
      }).join("") + "</ul>" + (it.cmd ? '<p class="muted">On the estate: <code>' + K.esc(it.cmd) + "</code></p>" : "")
        + '<button class="primary" data-a="cadDone" data-x="' + K.esc(it.id) + '">Mark done for this ' + K.esc(it.every) + "</button></li>";
    }
    return h;
  }
  K.module({
    id: "cadence", label: function () { return K.term("cadence", "Rhythm"); },
    render: function () {
      var c = K.cfg("cadence") || {}, L = items().slice();
      L.sort(function (a, b) { return K.cadenceDue(b).late - K.cadenceDue(a).late; });
      return "<h2>" + K.esc(K.term("cadence", "Rhythm")) + "</h2>" + (c.intro ? '<p class="muted">' + K.esc(c.intro) + "</p>" : "")
        + K.card("", "<ul class='list'>" + L.map(row).join("") + "</ul>");
    },
    next: function () {
      var out = [];
      items().forEach(function (it) { var st = K.cadenceDue(it); if (st.late >= 0) out.push({ score: 70 + Math.min(st.late, 20) + (it.weight || 0), text: it.name + (st.late > 0 ? " (" + st.late + " day(s) late)" : " is due today"), why: it.why || "", go: "cadence" }); });
      return out;
    },
    week: function (from) {
      var n = 0, lg = log(); Object.keys(lg).forEach(function (k) { (lg[k] || []).forEach(function (d) { if (d >= from) n++; }); });
      return n ? [{ n: n, what: "review(s) done on time or caught up" }] : [];
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
        K.set("cadence", lg, { what: "review done" }); K.set("cadChk", m, { noUndo: true }); K._cad = null; K.render(); K.toast("Done. The next one is dated by itself.");
      }
    }
  });
})();
