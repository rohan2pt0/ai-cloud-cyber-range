/* Wheel: score each area 1-10 once a quarter (the Wheel of Life method, renamed by the edition).
   The lowest area is the honest place to put the next goal; the history shows whether the wheel is getting rounder. */
(function () {
  var K = window.OSK;
  function dims() { return (K.cfg("wheel") || {}).dims || []; }
  function data() { return K.get("wheel", { s: {}, at: null, hist: [] }); }
  function score(d, id) { var v = d.s[id]; return typeof v === "number" ? v : 0; }
  function radar(d) {
    var D = dims(), n = D.length; if (n < 3) return "";
    var cx = 150, cy = 150, R = 110, pts = [], grid = "", labels = "", dots = "", scored = 0;
    for (var ring = 2; ring <= 10; ring += 2) {
      var g = []; for (var i = 0; i < n; i++) { var a = -Math.PI / 2 + i * 2 * Math.PI / n; g.push((cx + R * ring / 10 * Math.cos(a)).toFixed(1) + "," + (cy + R * ring / 10 * Math.sin(a)).toFixed(1)); }
      grid += '<polygon points="' + g.join(" ") + '" class="ring"/>';
    }
    D.forEach(function (x, i) {
      var a = -Math.PI / 2 + i * 2 * Math.PI / n, v = score(d, x.id);
      var lx = cx + (R + 22) * Math.cos(a), ly = cy + (R + 22) * Math.sin(a);
      labels += '<text x="' + lx.toFixed(0) + '" y="' + ly.toFixed(0) + '" text-anchor="' + (Math.abs(Math.cos(a)) < 0.3 ? "middle" : Math.cos(a) > 0 ? "start" : "end") + '">' + K.esc(x.short || x.label) + "</text>";
      var px = (cx + R * v / 10 * Math.cos(a)).toFixed(1), py = (cy + R * v / 10 * Math.sin(a)).toFixed(1);
      if (v > 0) { scored++; pts.push(px + "," + py); dots += '<circle cx="' + px + '" cy="' + py + '" r="3.2" class="dot"/>'; }
      else pts.push(null);
    });
    // Honest rendering: the filled polygon is drawn ONLY when every area is scored — a closed shape implies a complete picture.
    // Until then the rings stay empty and each scored area shows a dot at its value, so "not scored yet" never reads as "a 0 life".
    var shape = scored === n ? '<polygon points="' + pts.join(" ") + '" class="shape"/>' : "";
    return '<svg class="radar" viewBox="-60 0 420 300" role="img" aria-label="' + K.esc(K.t("wheel.scores_aria", "Wheel scores")) + '">' + grid + shape + dots + labels + "</svg>";
  }
  K.wheelLowest = function () {
    var d = data(), D = dims().filter(function (x) { return score(d, x.id) > 0; });
    D.sort(function (a, b) { return score(d, a.id) - score(d, b.id); });
    return D[0] ? { dim: D[0], v: score(d, D[0].id) } : null;
  };
  K.module({
    id: "wheel", label: function () { return K.term("wheel", "Wheel"); },
    render: function () {
      var d = data(), c = K.cfg("wheel") || {}, h = "<h2>" + K.esc(K.term("wheel", "Wheel")) + "</h2>";
      if (c.intro) h += '<p class="muted">' + K.esc(c.intro) + "</p>";
      h += K.card("", radar(d) + (d.at ? '<p class="muted">' + K.esc(K.t("wheel.last_scored", "Last scored {d}", { d: d.at })) + "</p>" : '<p class="muted">' + K.esc(K.t("wheel.not_scored", "Not scored yet. Be honest: 10 is world class, 5 is \"it works on a good day\".")) + "</p>"));
      h += K.card(K.esc(K.t("wheel.score_each", "Score each area (1-10)")), "<ul class='list'>" + dims().map(function (x) {
        var v = score(d, x.id), opts = "<option value=''>-</option>"; for (var i = 1; i <= 10; i++) opts += "<option" + (i === v ? " selected" : "") + ">" + i + "</option>";
        return '<li class="row"><div class="grow"><b>' + K.esc(x.label) + "</b>" + (x.hint ? '<div class="muted">' + K.esc(x.hint) + "</div>" : "") + "</div>"
          + '<div class="sx-keys" role="group" aria-label="' + K.esc(x.label) + '">' + [1,2,3,4,5,6,7,8,9,10].map(function (n) {
            return '<button type="button" class="sx-key' + (n === v ? " on" : "") + '" aria-pressed="' + (n === v) + '" data-a="whKey" data-x="' + K.esc(x.id + "|" + n) + '">' + n + "</button>"; }).join("") + "</div></li>";
      }).join("") + "</ul>");
      var lo = K.wheelLowest();
      if (lo) h += K.card(K.esc(K.t("wheel.next_goal", "Where to put the next goal")), "<p><b>" + K.esc(lo.dim.label) + "</b>" + K.esc(K.t("wheel.lowest_suffix", " is lowest at {v}/10.", { v: lo.v })) + (lo.dim.lever ? " " + K.esc(lo.dim.lever) : "") + "</p>" + (K.on("goals") ? '<button data-a="go" data-x="goals">' + K.esc(K.t("wheel.set_goal", "Set a goal for it")) + '</button>' : ""));
      if ((d.hist || []).length > 1) h += K.card(K.esc(K.t("wheel.over_time", "Over time")), "<ul class='list'>" + d.hist.slice(-6).map(function (e) { var vals = Object.keys(e.s).map(function (k) { return e.s[k]; }); var avg = vals.length ? vals.reduce(function (a, b) { return a + b; }, 0) / vals.length : 0; return "<li>" + K.esc(K.t("wheel.average", "{q}: average {v}", { q: e.q, v: avg.toFixed(1) })) + "</li>"; }).join("") + "</ul>");
      return h;
    },
    next: function () {
      var d = data();
      if (!d.at) return { score: 15, text: K.t("wheel.next_score", "Score your {w} (two minutes)", { w: K.term("wheel", "wheel") }), why: K.t("wheel.next_score_why", "It shows where the next goal belongs."), go: "wheel" };
      if (K.quarter(new Date(d.at)) !== K.quarter()) return { score: 30, text: K.t("wheel.next_requarter", "New quarter: re-score your {w}", { w: K.term("wheel", "wheel") }), why: K.t("wheel.next_last", "Last scored {d}.", { d: d.at }), go: "wheel" };
      return null;
    },
    acts: {
      // A tap on a key sets the score (tapping the chosen key again clears it): no dropdown to open (shared keycaps).
      whKey: function (x) { var p = String(x).split("|"), d = data(); K.acts.whSet(p[0], { value: d.s[p[0]] === +p[1] ? "" : p[1] }); },
      whSet: function (id, el) {
        var d = data(), v = parseInt(el.value, 10); if (isNaN(v)) delete d.s[id]; else d.s[id] = Math.max(1, Math.min(10, v));
        d.at = K.ymd(); d.hist = d.hist || [];
        var q = K.quarter(), last = d.hist[d.hist.length - 1];
        if (last && last.q === q) last.s = JSON.parse(JSON.stringify(d.s)); else d.hist.push({ q: q, s: JSON.parse(JSON.stringify(d.s)) });
        d.hist = d.hist.slice(-16);
        K.set("wheel", d, { what: "wheel" }); K.render();
      }
    }
  });
})();
