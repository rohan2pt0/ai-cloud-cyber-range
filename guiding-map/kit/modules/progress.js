/* Progress: the north star made visible. What got better this week (from every module's own count), the streak of
   weeks with a win, and a resilience index that only rises with real practice: rhythm kept, numbers on target,
   lessons turned into changes, and the riskiest items owned and dated. Every part says where it comes from. */
(function () {
  var K = window.OSK;
  function weekStart() { var d = new Date(), wd = (d.getDay() + 6) % 7; return K.addDays(K.ymd(), -wd); }   // Monday
  K.weekWins = function (from) {
    var out = [];
    Object.keys(K.mods).forEach(function (id) { var m = K.mods[id]; if (m.week && K.cfg(id)) { try { out = out.concat(m.week(from) || []); } catch (e) {} } });
    return out;
  };
  // 0-100, from parts the person can see and change; a part with no data yet is left out, never counted as zero or full.
  K.resilience = function () {
    var parts = [], c = K.cfg("progress") || {};
    if (K.mods.cadence && K.cfg("cadence")) { var t = K.mods.cadence.onTime(); if (t != null) parts.push({ n: "Rhythm kept (90 days)", v: t }); }
    if (K.mods.scorecard && K.cfg("scorecard")) { var s = K.mods.scorecard.onTarget(); if (s != null) parts.push({ n: "Numbers on target", v: s }); }
    if (c.lessons && K.mods.registers) {
      var ok = c.lessons_done || ["Changed"], L = K.get("reg." + c.lessons, []), done = L.filter(function (x) { return ok.indexOf(x.status) >= 0; }).length;
      if (L.length) parts.push({ n: "Lessons turned into a change", v: done / L.length });
    }
    if (c.risks && K.mods.registers) {
      var R = (K.get("reg." + c.risks, []) || []).filter(function (x) { return (c.risks_closed || ["Closed"]).indexOf(x.status) < 0; });
      var rc = (K.cfg("registers") || []).filter(function (r) { return r.id === c.risks; })[0] || {};
      var hi = R.filter(function (x) { return K.regScore(rc, x) >= (c.risk_high || 12); });
      if (hi.length) parts.push({ n: "Top risks owned and dated", v: hi.filter(function (x) { return x.owner && x.due; }).length / hi.length });
    }
    var score = parts.length ? Math.round(parts.reduce(function (a, p) { return a + p.v; }, 0) / parts.length * 100) : null;
    return { score: score, parts: parts };
  };
  function sum(a) { return a.reduce(function (x, w) { return x + w.n; }, 0); }
  // the counters look forward from a date, so one week's wins are "since its Monday" less "since the next Monday"
  function inWeek(w) { return sum(K.weekWins(w)) - sum(K.weekWins(K.addDays(w, 7))); }
  function streak() {
    var n = 0, w = weekStart();
    if (inWeek(w) <= 0) w = K.addDays(w, -7);   // this week may not have its first win yet
    for (var i = 0; i < 52 && inWeek(w) > 0; i++) { n++; w = K.addDays(w, -7); }
    return n;
  }
  K.module({
    id: "progress", label: function () { return K.term("progress", "Progress"); },
    weekCard: function () {
      var W = K.weekWins(weekStart()), R = K.resilience();
      var h = W.length ? "<ul class='wins'>" + W.map(function (w) { return "<li><b>" + w.n + "</b> " + K.esc(w.what) + "</li>"; }).join("") + "</ul>" : "<p>No wins logged this week yet. One ritual or one decision is enough to start.</p>";
      if (R.score != null) h += '<p class="muted">' + K.esc(K.term("resilience", "Resilience index")) + ": <b>" + R.score + "</b>/100 · " + '<a href="#" data-a="go" data-x="progress">why</a></p>';
      return K.card("This week", h);
    },
    render: function () {
      var R = K.resilience(), s = streak(), h = "<h2>" + K.esc(K.term("progress", "Progress")) + "</h2>";
      if (K.ed.north_star) h += '<p class="north">' + K.esc(K.ed.north_star) + "</p>";
      h += this.weekCard();
      h += K.card("Weeks in a row with a win", '<p class="big">' + s + "</p>");
      h += K.card(K.esc(K.term("resilience", "Resilience index")), R.score == null ? "<p>It appears once there is something to measure: a review done, a number logged, a lesson recorded.</p>"
        : '<p class="big">' + R.score + "/100</p><ul class='list'>" + R.parts.map(function (p) { return "<li>" + K.esc(p.n) + ": " + Math.round(p.v * 100) + "%" + K.bar(p.v * 100) + "</li>"; }).join("") + "</ul><p class='muted'>Only practice moves it. It falls when the rhythm slips, so it cannot be gamed by typing.</p>");
      h += K.card("Last week", "<p>" + inWeek(K.addDays(weekStart(), -7)) + " thing(s) done last week.</p>");
      return h;
    }
  });
})();
