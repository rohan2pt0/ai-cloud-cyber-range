/* Feeds: read-only numbers the estate already knows, shown where the person looks every day.
   Each feed is a same-address JSON file the estate writes (for example ./securax govern writes portal/govern-state.json).
   No feed file, no card: the app never depends on it, and never calls another site. */
(function () {
  var K = window.OSK;
  var cache = {};
  function feeds() { return (K.cfg("feeds") || {}).items || []; }
  function fetchAll() {
    if (!window.fetch || location.protocol.indexOf("http") !== 0) return;
    feeds().forEach(function (f) {
      if (!/^(\.\.\/|\/)?[a-z0-9_\-\/]+\.json$/i.test(f.url)) return;   // same address only
      fetch(f.url, { cache: "no-cache", credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { if (j) { cache[f.id] = j; K.set("~feed." + f.id, j); K.render(); } })
        .catch(function () {});
    });
  }
  // A view per feed kind; a kind the kit does not know is skipped.
  var VIEWS = {
    govern: function (j, f) {
      var tiers = j.coverage || {}, recs = (j.top || []).slice(0, f.top || 3);
      var h = '<p><b>Maturity ' + K.esc(j.maturity) + "/5</b> · " + Object.keys(tiers).map(function (t) { return K.esc(t) + " " + K.esc(tiers[t]) + "%"; }).join(" · ") + "</p>";
      if (j.budget) h += '<p class="muted">To close the gaps: ' + K.esc(j.budget) + "</p>";
      if (recs.length) h += "<ol class='list'>" + recs.map(function (r) { return "<li><b>" + K.esc(r.what) + '</b><div class="muted">' + K.esc([r.who, r.when, r.how_much].filter(Boolean).join(" · ")) + "</div></li>"; }).join("") + "</ol>";
      h += '<p class="muted">From <code>./securax govern</code>' + (j.at ? ", " + K.esc(j.at) : "") + ".</p>";
      return h;
    }
  };
  function view(f) {
    var j = cache[f.id] || K.get("~feed." + f.id, null), v = VIEWS[f.kind];
    if (!j || !v) return "";
    try { return K.card(K.esc(f.title || f.id), v(j, f)); } catch (e) { return ""; }
  }
  K.module({
    id: "feeds", label: function () { return K.term("feeds", "From the estate"); },
    todayCard: function () { return feeds().filter(function (f) { return f.today; }).map(view).join(""); },
    render: function () {
      var h = feeds().map(view).join("");
      return "<h2>" + K.esc(K.term("feeds", "From the estate")) + "</h2>" + (h || "<p>Nothing from the estate yet. On the estate machine run <code>./securax govern</code> once; this screen then fills itself.</p>");
    }
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fetchAll); else setTimeout(fetchAll, 0);
})();
