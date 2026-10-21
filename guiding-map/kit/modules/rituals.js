/* Rituals: the few daily habits that carry everything else. Each has an IF-THEN anchor and a two-minute floor,
   and the Never-Miss-Twice rule: missing once is life; missing twice is the start of a new habit, so Today raises it. */
(function () {
  var K = window.OSK;
  function list() { return (K.cfg("rituals") || {}).items || []; }
  function log() { return K.get("rituals", {}); }
  function on(day, id) { return (log()[day] || []).indexOf(id) >= 0; }
  K.streak = function (id) {
    var n = 0, d = K.ymd(); if (!on(d, id)) d = K.addDays(d, -1);
    while (on(d, id) && n < 3650) { n++; d = K.addDays(d, -1); }
    return n;
  };
  function missedTwice(id) {
    var t = K.ymd(), y = K.addDays(t, -1), wk = 0;
    for (var i = 2; i <= 8; i++) if (on(K.addDays(t, -i), id)) wk++;
    return !on(t, id) && !on(y, id) && wk > 0;   // only for a ritual that was alive last week
  }
  function tickRow(r) {
    var done = on(K.ymd(), r.id), s = K.streak(r.id);
    return '<li class="row tick' + (done ? " done" : "") + '"><button class="check" data-a="ritTick" data-x="' + K.esc(r.id) + '" aria-pressed="' + done + '" aria-label="' + K.esc(r.name) + '">' + (done ? "✓" : "") + "</button>"
      + '<div class="grow"><b>' + K.esc(r.name) + "</b>" + (s > 1 ? ' <span class="tag">' + s + " days</span>" : "") + (missedTwice(r.id) ? ' <span class="tag late">missed twice</span>' : "")
      + '<div class="muted">' + K.esc(done ? r.anchor || "" : r.min || r.anchor || "") + "</div></div></li>";
  }
  K.module({
    id: "rituals", label: function () { return K.term("rituals", "Rituals"); },
    todayCard: function () {
      var L = list(); if (!L.length) return "";
      var n = L.filter(function (r) { return on(K.ymd(), r.id); }).length;
      return K.card(K.esc(K.term("rituals", "Rituals")) + ' <span class="muted">' + n + "/" + L.length + "</span>", "<ul class='list'>" + L.map(tickRow).join("") + "</ul>");
    },
    render: function () {
      var L = list(), c = K.cfg("rituals") || {}, h = "<h2>" + K.esc(K.term("rituals", "Rituals")) + "</h2>";
      if (c.intro) h += '<p class="muted">' + K.esc(c.intro) + "</p>";
      h += this.todayCard();
      h += K.card("How each one is anchored", "<ul class='list'>" + L.map(function (r) { return "<li><b>" + K.esc(r.name) + "</b><div>" + K.esc(r.anchor || "") + '</div><div class="muted">Floor: ' + K.esc(r.min || "") + "</div>" + (r.why ? '<div class="muted">Why: ' + K.esc(r.why) + "</div>" : "") + "</li>"; }).join("") + "</ul>");
      var days = [], lg = log(); for (var i = 27; i >= 0; i--) days.push(K.addDays(K.ymd(), -i));
      h += K.card("The last four weeks", '<div class="dots" role="img" aria-label="Rituals done each day, last 28 days">' + days.map(function (d) { var n = (lg[d] || []).length, f = L.length ? n / L.length : 0; return '<i class="d' + (f >= 0.99 ? 3 : f >= 0.5 ? 2 : n ? 1 : 0) + '" title="' + d + ": " + n + '"></i>'; }).join("") + "</div>");
      return h;
    },
    next: function () {
      var m = list().filter(function (r) { return missedTwice(r.id); });
      if (m.length) return { score: 60, text: "Do the two-minute floor of “" + m[0].name + "”: " + (m[0].min || m[0].anchor || ""), why: "Missed twice. Never miss three times.", go: "today" };
      var todo = list().filter(function (r) { return !on(K.ymd(), r.id); });
      if (todo.length && new Date().getHours() >= 17) return { score: 25, text: todo[0].name + ": " + (todo[0].min || ""), why: "Still open today. The floor is enough.", go: "today" };
      return null;
    },
    week: function (from) {
      var lg = log(), n = 0; Object.keys(lg).forEach(function (d) { if (d >= from) n += lg[d].length; });
      return n ? [{ n: n, what: "ritual(s) kept" }] : [];
    },
    acts: {
      ritTick: function (id) {
        var lg = log(), d = K.ymd(), a = lg[d] || (lg[d] = []), p = a.indexOf(id);
        if (p >= 0) a.splice(p, 1); else a.push(id);
        // bounded: a year of days is plenty for streaks and the four-week view
        Object.keys(lg).forEach(function (k) { if (K.days(k) > 400) delete lg[k]; });
        K.set("rituals", lg, { what: "ritual" }); K.render();
      }
    }
  });
})();
