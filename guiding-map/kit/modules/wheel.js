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
    return '<svg class="radar" viewBox="-60 0 420 300" role="img" aria-label="Wheel scores">' + grid + shape + dots + labels + "</svg>";
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
      h += K.card("", radar(d) + (d.at ? '<p class="muted">Last scored ' + K.esc(d.at) + "</p>" : '<p class="muted">Not scored yet. Be honest: 10 is world class, 5 is "it works on a good day".</p>'));
      h += K.card("Score each area (1-10)", "<ul class='list'>" + dims().map(function (x) {
        var v = score(d, x.id), opts = "<option value=''>-</option>"; for (var i = 1; i <= 10; i++) opts += "<option" + (i === v ? " selected" : "") + ">" + i + "</option>";
        return '<li class="row"><div class="grow"><label for="wh_' + K.esc(x.id) + '"><b>' + K.esc(x.label) + "</b></label>" + (x.hint ? '<div class="muted">' + K.esc(x.hint) + "</div>" : "") + "</div>"
          + '<select id="wh_' + K.esc(x.id) + '" data-c="whSet" data-x="' + K.esc(x.id) + '">' + opts + "</select></li>";
      }).join("") + "</ul>");
      var lo = K.wheelLowest();
      if (lo) h += K.card("Where to put the next goal", "<p><b>" + K.esc(lo.dim.label) + "</b> is lowest at " + lo.v + "/10." + (lo.dim.lever ? " " + K.esc(lo.dim.lever) : "") + "</p>" + (K.on("goals") ? '<button data-a="go" data-x="goals">Set a goal for it</button>' : ""));
      if ((d.hist || []).length > 1) h += K.card("Over time", "<ul class='list'>" + d.hist.slice(-6).map(function (e) { var vals = Object.keys(e.s).map(function (k) { return e.s[k]; }); var avg = vals.length ? vals.reduce(function (a, b) { return a + b; }, 0) / vals.length : 0; return "<li>" + K.esc(e.q) + ": average " + avg.toFixed(1) + "</li>"; }).join("") + "</ul>");
      return h;
    },
    next: function () {
      var d = data();
      if (!d.at) return { score: 15, text: "Score your " + K.term("wheel", "wheel") + " (two minutes)", why: "It shows where the next goal belongs.", go: "wheel" };
      if (K.quarter(new Date(d.at)) !== K.quarter()) return { score: 30, text: "New quarter: re-score your " + K.term("wheel", "wheel"), why: "Last scored " + d.at + ".", go: "wheel" };
      return null;
    },
    acts: {
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
