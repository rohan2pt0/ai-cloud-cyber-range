/* Scorecard: the few numbers that show whether things are getting better (KPIs) or riskier (KRIs).
   Each has a start, a target and a direction; one tap logs today's value and the trend shows itself.
   A number not updated within its cadence is raised on Today: a stale scorecard is worse than none. */
(function () {
  var K = window.OSK;
  function metrics() { return (K.cfg("scorecard") || {}).metrics || []; }
  function hist() { return K.get("score", {}); }
  function last(id) { var h = hist()[id] || []; return h[h.length - 1] || null; }
  // Progress counts from YOUR first logged value (your real start), not the edition's example start.
  function base(m) { var h = hist()[m.id]; return h && h.length ? h[0].v : m.base; }
  K.metricPct = function (m, v) {
    if (v == null) return 0;
    var b = base(m), r = m.goal - b;
    if (!r) return v === m.goal ? 100 : 0;
    return Math.max(0, Math.min(100, Math.round((v - b) / r * 100)));
  };
  function rag(p) { return p >= 70 ? "on" : p >= 40 ? "medium" : "high"; }
  function spark(id) {
    var h = (hist()[id] || []).slice(-12); if (h.length < 2) return "";
    var vs = h.map(function (e) { return e.v; }), lo = Math.min.apply(null, vs), hi = Math.max.apply(null, vs), span = hi - lo || 1;
    var pts = h.map(function (e, i) { return (i * 100 / (h.length - 1)).toFixed(1) + "," + (28 - (e.v - lo) / span * 24).toFixed(1); }).join(" ");
    return '<svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden="true"><polyline points="' + pts + '"/></svg>';
  }
  K.module({
    id: "scorecard", label: function () { return K.term("scorecard", "Scorecard"); },
    render: function () {
      var c = K.cfg("scorecard") || {}, h = "<h2>" + K.esc(K.term("scorecard", "Scorecard")) + "</h2>" + (c.intro ? '<p class="muted">' + K.esc(c.intro) + "</p>" : "");
      var groups = {}; metrics().forEach(function (m) { (groups[m.kind || "KPI"] = groups[m.kind || "KPI"] || []).push(m); });
      Object.keys(groups).forEach(function (g) {
        h += K.card(K.esc(g === "KRI" ? "Risk indicators (KRI)" : g === "KPI" ? "Performance indicators (KPI)" : g), "<ul class='list'>" + groups[g].map(function (m) {
          var l = last(m.id), p = l ? K.metricPct(m, l.v) : 0, stale = !l || K.days(l.d) > (m.every || 31);
          return '<li class="row"><div class="grow"><b>' + K.esc(m.name) + "</b>" + (l ? ' <span class="tag ' + rag(p) + '">' + K.esc(l.v) + (m.unit ? " " + K.esc(m.unit) : "") + "</span>" : "")
            + (stale ? ' <span class="tag due">' + (l ? "update" : "no value yet") + "</span>" : "")
            + '<div class="muted">from ' + base(m) + " to " + m.goal + (m.unit ? " " + K.esc(m.unit) : "") + (l ? " · " + p + "% of the way · " + K.esc(l.d) : "") + "</div>" + (m.why ? '<div class="muted">' + K.esc(m.why) + "</div>" : "") + spark(m.id) + "</div>"
            + '<label class="sr" for="sc_' + K.esc(m.id) + '">' + K.esc(m.name) + ' today</label><input class="num" id="sc_' + K.esc(m.id) + '" type="number" step="any" placeholder="today" data-c="scSet" data-x="' + K.esc(m.id) + '"></li>';
        }).join("") + "</ul>");
      });
      return h;
    },
    next: function () {
      var stale = metrics().filter(function (m) { var l = last(m.id); return !l || K.days(l.d) > (m.every || 31); });
      if (!stale.length) return null;
      return { score: hist() && Object.keys(hist()).length ? 32 : 18, text: "Update " + stale.length + " " + K.term("scorecard", "scorecard") + " number(s), starting with " + stale[0].name, why: "A number you have not looked at is a risk you have not looked at.", go: "scorecard" };
    },
    week: function (from) {
      var n = 0, better = 0, H = hist();
      metrics().forEach(function (m) { var h = H[m.id] || []; h.forEach(function (e, i) { if (e.d >= from) { n++; if (i && K.metricPct(m, e.v) > K.metricPct(m, h[i - 1].v)) better++; } }); });
      var out = []; if (n) out.push({ n: n, what: "number(s) logged" }); if (better) out.push({ n: better, what: "number(s) moved the right way" }); return out;
    },
    onTarget: function () { var M = metrics(), n = 0, on = 0; M.forEach(function (m) { var l = last(m.id); if (l) { n++; if (K.metricPct(m, l.v) >= 70) on++; } }); return n ? on / n : null; },
    acts: {
      scSet: function (id, el) {
        var v = parseFloat(el.value); if (isNaN(v)) return;
        var H = hist(), h = H[id] || (H[id] = []), d = K.ymd();
        if (h.length && h[h.length - 1].d === d) h[h.length - 1].v = v; else h.push({ d: d, v: v });
        H[id] = h.slice(-60); K.set("score", H, { what: "number" }); K.render(); K.toast("Logged.");
      }
    }
  });
})();
