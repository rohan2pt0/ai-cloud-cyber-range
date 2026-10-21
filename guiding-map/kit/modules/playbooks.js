/* Playbooks: the edition's know-how as short, tickable steps ("when this happens, do this, in this order").
   Ticks are kept per playbook, so a long one (the first 90 days) can be worked through over weeks; Reset starts it again. */
(function () {
  var K = window.OSK;
  function list() { return (K.cfg("playbooks") || {}).items || []; }
  function ticks() { return K.get("pb", {}); }
  K.module({
    id: "playbooks", label: function () { return K.term("playbooks", "Playbooks"); },
    render: function () {
      var c = K.cfg("playbooks") || {}, t = ticks(), open = K._pb, h = "<h2>" + K.esc(K.term("playbooks", "Playbooks")) + "</h2>";
      if (c.intro) h += '<p class="muted">' + K.esc(c.intro) + "</p>";
      list().forEach(function (p) {
        var done = (t[p.id] || []).length, n = (p.steps || []).length, isOpen = open === p.id;
        var body = (p.when ? '<p class="muted">When: ' + K.esc(p.when) + "</p>" : "") + K.bar(n ? done / n * 100 : 0);
        if (isOpen) {
          body += "<ol class='list'>" + p.steps.map(function (s, i) {
            var on = (t[p.id] || []).indexOf(i) >= 0;
            return '<li class="row tick' + (on ? " done" : "") + '"><button class="check" data-a="pbTick" data-x="' + K.esc(p.id + "|" + i) + '" aria-pressed="' + on + '" aria-label="Step ' + (i + 1) + '">' + (on ? "✓" : "") + '</button><div class="grow">' + K.esc(s) + "</div></li>";
          }).join("") + "</ol>";
          if (p.cmd) body += '<p class="muted">On the estate: <code>' + K.esc(p.cmd) + "</code></p>";
          if (p.template) body += '<p class="muted">Template: <code>' + K.esc(p.template) + "</code></p>";
          body += '<div class="btns"><button data-a="pbOpen" data-x="">Close</button>' + (done ? '<button class="ghost" data-a="pbReset" data-x="' + K.esc(p.id) + '">Reset</button>' : "") + "</div>";
        } else body += '<button data-a="pbOpen" data-x="' + K.esc(p.id) + '">' + (done ? "Continue (" + done + "/" + n + ")" : "Open") + "</button>";
        h += K.card(K.esc(p.title), body);
      });
      return h;
    },
    // a playbook started and left half-done for two weeks deserves a nudge
    next: function () {
      var t = ticks(), at = K.get("pbAt", {}), out = [];
      list().forEach(function (p) { var d = (t[p.id] || []).length; if (d && d < p.steps.length && at[p.id] && K.days(at[p.id]) >= 14) out.push({ score: 22, text: "Continue the playbook “" + p.title + "” (" + d + "/" + p.steps.length + ")", why: "Half-done for " + K.days(at[p.id]) + " days.", go: "playbooks" }); });
      return out;
    },
    week: function (from) { var at = K.get("pbAt", {}), n = Object.keys(at).filter(function (k) { return at[k] >= from; }).length; return n ? [{ n: n, what: "playbook(s) worked on" }] : []; },
    acts: {
      pbOpen: function (id) { K._pb = id || null; K.render(); },
      pbTick: function (x) {
        var p = String(x).split("|"), t = ticks(), a = t[p[0]] || (t[p[0]] = []), i = +p[1], j = a.indexOf(i);
        if (j >= 0) a.splice(j, 1); else a.push(i);
        var at = K.get("pbAt", {}); at[p[0]] = K.ymd();
        K.set("pb", t, { what: "step" }); K.set("pbAt", at, { noUndo: true }); K.render();
      },
      pbReset: function (id) { var t = ticks(); delete t[id]; K.set("pb", t, { what: "reset playbook" }); K.render(); }
    }
  });
})();
