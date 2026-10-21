/* Goals: quarterly objectives with measurable key results (the OKR method, as in the Life OS).
   A key result runs from a start number to a target by a date; progress is where the current number sits between them.
   A goal nobody touched for `idle_days` is raised on Today: recommit, rescope or drop it. Never let it rot silently. */
(function () {
  var K = window.OSK;
  function cfg() { return K.cfg("goals") || {}; }
  function all() { return K.get("goals", []); }
  function save(a, w) { K.set("goals", a, { what: w }); }
  function idx(a, id) { for (var i = 0; i < a.length; i++) if (a[i].id === id) return i; return -1; }
  K.krFrac = function (k) { if (k.g === k.b) return k.c >= k.g ? 1 : 0; return Math.max(0, Math.min(1, (k.c - k.b) / (k.g - k.b))); };
  K.goalGrade = function (o) { return o.krs && o.krs.length ? o.krs.reduce(function (s, k) { return s + K.krFrac(k); }, 0) / o.krs.length : 0; };
  function touched(o) { return (o.krs || []).reduce(function (m, k) { return k.at > m ? k.at : m; }, o.at || K.ymd()); }
  function live() { return all().filter(function (o) { return !o.closed; }); }
  function krRow(o, k, j) {
    var pct = Math.round(K.krFrac(k) * 100), id = K.esc(o.id + "|" + j);
    return '<li class="row"><div class="grow">' + K.esc(k.t) + '<div class="muted">from ' + k.b + " to " + k.g + (k.u ? " " + K.esc(k.u) : "") + (k.by ? " by " + K.esc(k.by) : "") + "</div>" + K.bar(pct) + "</div>"
      + '<label class="sr" for="kr' + id + '">Now</label><input class="num" id="kr' + id + '" type="number" step="any" value="' + k.c + '" data-c="krSet" data-x="' + id + '" aria-label="Current value"></li>';
  }
  function goalCard(o) {
    var g = Math.round(K.goalGrade(o) * 100), idle = K.days(touched(o)), lim = cfg().idle_days || 42, id = K.esc(o.id);
    var h = "<p class='muted'>" + K.esc(o.q) + " · " + g + "% · " + (o.area ? K.esc(o.area) + " · " : "") + (idle >= lim ? '<span class="tag late">idle ' + idle + " days</span>" : "touched " + (idle ? idle + " days ago" : "today")) + "</p>";
    h += "<ul class='list'>" + (o.krs || []).map(function (k, j) { return krRow(o, k, j); }).join("") + "</ul>";
    if (K._krFor === o.id) {
      h += '<div class="form"><label for="krT">Key result</label><input id="krT" placeholder="e.g. critical findings past SLA">'
        + '<div class="cols"><span><label for="krB">From</label><input id="krB" type="number" step="any"></span><span><label for="krG">To</label><input id="krG" type="number" step="any"></span>'
        + '<span><label for="krU">Unit</label><input id="krU" placeholder="%, count, days"></span></div>'
        + '<label for="krBy">By</label><input id="krBy" type="date" value="' + qEnd() + '"><button class="primary" data-a="krAdd" data-x="' + id + '">Add key result</button></div>';
    } else h += '<div class="btns"><button data-a="krOpen" data-x="' + id + '">Add a key result</button>'
      + (idle >= lim ? '<button data-a="goalRecommit" data-x="' + id + '">Recommit</button>' : "")
      + '<button class="ghost" data-a="goalClose" data-x="' + id + '">Close this goal</button></div>';
    return K.card(K.esc(o.o), h);
  }
  function qEnd() { var d = new Date(), m = Math.floor(d.getMonth() / 3) * 3 + 3; return K.ymd(new Date(d.getFullYear(), m, 0)); }
  K.module({
    id: "goals", label: function () { return K.term("goals", "Goals"); },
    render: function () {
      var c = cfg(), L = live(), h = "<h2>" + K.esc(K.term("goals", "Goals")) + "</h2>";
      if (c.intro) h += '<p class="muted">' + K.esc(c.intro) + "</p>";
      h += L.map(goalCard).join("");
      if (L.length >= (c.max || 3)) h += '<p class="muted">' + (c.max || 3) + " live goals is the limit: focus beats a long list. Close one to add another.</p>";
      else {
        var areas = (K.cfg("wheel") || {}).dims || [];
        h += K.card("New goal", '<label for="goalO">Objective (what changes, in plain words)</label><input id="goalO" placeholder="' + K.esc(c.placeholder || "e.g. Close the riskiest gaps first") + '">'
          + (areas.length ? '<label for="goalA">Area</label><select id="goalA"><option value="">(any)</option>' + areas.map(function (d) { return "<option>" + K.esc(d.label) + "</option>"; }).join("") + "</select>" : "")
          + '<button class="primary" data-a="goalAdd">Add goal</button>'
          + ((c.starter || []).length ? '<p class="muted">Or start from a proven one:</p><div class="chips">' + c.starter.map(function (s, i) { return '<button data-a="goalStarter" data-x="' + i + '">' + K.esc(s.o) + "</button>"; }).join("") + "</div>" : ""));
      }
      var closed = all().filter(function (o) { return o.closed; });
      if (closed.length) h += K.card("Closed", "<ul class='list'>" + closed.slice(-8).map(function (o) { return "<li>" + K.esc(o.o) + ' <span class="muted">' + Math.round(K.goalGrade(o) * 100) + "% · " + K.esc(o.closed) + "</span></li>"; }).join("") + "</ul>");
      return h;
    },
    next: function () {
      var lim = cfg().idle_days || 42, out = [];
      live().forEach(function (o) {
        var idle = K.days(touched(o));
        if (idle >= lim) out.push({ score: 40, text: "Recommit, rescope or close: " + o.o, why: "No key result moved for " + idle + " days.", go: "goals" });
        else if (!(o.krs || []).length) out.push({ score: 35, text: "Give “" + o.o + "” a number to move", why: "A goal without a key result cannot show progress.", go: "goals" });
      });
      if (!live().length) out.push({ score: 20, text: "Set this quarter's goals (" + (cfg().max || 3) + " at most)", why: "What gets measured moves.", go: "goals" });
      return out;
    },
    week: function (from) {
      var n = 0; all().forEach(function (o) { (o.krs || []).forEach(function (k) { if (k.at >= from && k.c !== k.b) n++; }); });
      return n ? [{ n: n, what: "key result(s) moved" }] : [];
    },
    acts: {
      goalAdd: function () {
        var o = K.val("goalO"); if (!o) { K.toast("Write the objective first."); return; }
        var a = all(); a.push({ id: K.uid(), o: o.slice(0, 200), area: K.val("goalA"), q: K.quarter(), at: K.ymd(), krs: [] }); save(a, "new goal"); K._krFor = a[a.length - 1].id; K.render();
      },
      goalStarter: function (i) {
        var s = (cfg().starter || [])[+i]; if (!s) return;
        var a = all(); a.push({ id: K.uid(), o: s.o, area: s.area || "", q: K.quarter(), at: K.ymd(), krs: (s.krs || []).map(function (k) { return { t: k.t, b: +k.b, g: +k.g, c: +k.b, u: k.u || "", by: qEnd(), at: K.ymd() }; }) });
        save(a, "starter goal"); K.render(); K.toast("Added. Set each key result's real starting number.");
      },
      krOpen: function (id) { K._krFor = id; K.render(); },
      krAdd: function (id) {
        var a = all(), i = idx(a, id); if (i < 0) return;
        var t = K.val("krT"), b = parseFloat(K.val("krB")), g = parseFloat(K.val("krG"));
        if (!t || isNaN(b) || isNaN(g) || b === g) { K.toast("A key result needs words, a start number and a different target."); return; }
        a[i].krs.push({ t: t.slice(0, 200), b: b, g: g, c: b, u: K.val("krU").slice(0, 20), by: K.val("krBy"), at: K.ymd() }); K._krFor = null; save(a, "key result"); K.render();
      },
      krSet: function (x, el) {
        var p = String(x).split("|"), a = all(), i = idx(a, p[0]); if (i < 0) return;
        var k = a[i].krs[+p[1]], v = parseFloat(el.value); if (!k || isNaN(v)) return;
        k.c = v; k.at = K.ymd(); save(a, "progress"); K.render(); K.toast(K.krFrac(k) >= 1 ? "Target reached. Well done." : "Progress saved.");
      },
      goalRecommit: function (id) { var a = all(), i = idx(a, id); if (i < 0) return; a[i].at = K.ymd(); a[i].recommits = (a[i].recommits || 0) + 1; save(a, "recommit"); K.render(); K.toast("Recommitted. Move one key result this week."); },
      goalClose: function (id) { var a = all(), i = idx(a, id); if (i < 0) return; a[i].closed = K.ymd(); save(a, "close goal"); K.render(); K.toast("Closed. What did it teach you? Log it as a lesson."); }
    }
  });
})();
