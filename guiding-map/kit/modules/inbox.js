/* Inbox: capture in one line, decide later. Each item becomes an action (a next step and a date), a note, or nothing.
   Same rule as the Life OS inbox: nothing stays undecided for long, and an action always has a date. */
(function () {
  var K = window.OSK;
  function items() { return K.get("inbox", []); }
  function save(a, what) { K.set("inbox", a, { what: what }); }
  function find(a, id) { for (var i = 0; i < a.length; i++) if (a[i].id === id) return i; return -1; }
  function undecided() { return items().filter(function (x) { return !x.kind; }); }
  function dueActions() { var t = K.ymd(); return items().filter(function (x) { return x.kind === "action" && !x.done && x.due && x.due <= t; }); }
  function row(x) {
    var id = K.esc(x.id), h = '<li class="row"><div class="grow"><b>' + K.esc(x.text) + "</b>";
    if (x.kind === "action") h += '<div class="muted">Next: ' + K.esc(x.next || "") + (x.due ? " · by " + K.esc(x.due) : "") + (x.due && x.due < K.ymd() ? ' <span class="tag late">late</span>' : "") + "</div>";
    if (x.kind === "note") h += '<div class="muted">Note, kept ' + K.esc(x.at) + "</div>";
    h += "</div>";
    if (!x.kind) h += '<button data-a="ibDecide" data-x="' + id + '">Decide</button>';
    else if (x.kind === "action" && !x.done) h += '<button data-a="ibDone" data-x="' + id + '">Done</button>';
    h += '<button class="ghost" data-a="ibDel" data-x="' + id + '" aria-label="Delete">✕</button></li>';
    if (K._decide === x.id) {
      h += '<li class="form"><label for="ibNext">Next physical step</label><input id="ibNext" placeholder="e.g. call the vendor about the renewal">'
        + '<label for="ibDue">By</label><input id="ibDue" type="date" value="' + K.addDays(K.ymd(), 2) + '">'
        + '<div class="btns"><button class="primary" data-a="ibAction" data-x="' + id + '">It is an action</button>'
        + '<button data-a="ibNote" data-x="' + id + '">Keep as a note</button></div></li>';
    }
    return h;
  }
  K.module({
    id: "inbox", label: function () { return K.term("inbox", "Inbox"); },
    captureCard: function () {
      var u = undecided().length, d = dueActions().length;
      return K.card("Capture", '<div class="inline"><input id="ibText" aria-label="Capture a thought, ask or task" placeholder="One line is enough"><button data-a="ibAdd">Add</button></div>'
        + ((u || d) ? '<p class="muted">' + (d ? d + " action(s) due · " : "") + (u ? u + " to decide · " : "") + '<a href="#" data-a="go" data-x="inbox">open ' + K.esc(K.term("inbox", "Inbox")) + "</a></p>" : ""));
    },
    render: function () {
      var a = items(), open = a.filter(function (x) { return !(x.kind === "action" && x.done); });
      open.sort(function (x, y) { return (x.kind ? 1 : 0) - (y.kind ? 1 : 0) || String(x.due || "9").localeCompare(String(y.due || "9")); });
      var done = a.filter(function (x) { return x.done; }).length;
      return "<h2>" + K.esc(K.term("inbox", "Inbox")) + "</h2>" + this.captureCard()
        + K.card("", open.length ? "<ul class='list'>" + open.map(row).join("") + "</ul>" : "<p>Empty. Everything is decided.</p>")
        + (done ? '<p class="muted">' + done + " done so far.</p>" : "");
    },
    next: function () {
      var d = dueActions(); if (d.length) return { score: 80, text: d[0].next || d[0].text, why: "An action from your inbox is due" + (d.length > 1 ? " (and " + (d.length - 1) + " more)" : "") + ".", go: "inbox" };
      var u = undecided(); if (u.length >= 3) return { score: 50, text: "Decide " + u.length + " inbox items", why: "Undecided items turn into worry. Two minutes each.", go: "inbox" };
      return null;
    },
    week: function (from) {
      var n = items().filter(function (x) { return x.done && x.doneAt >= from; }).length;
      return n ? [{ n: n, what: "inbox action(s) done" }] : [];
    },
    acts: {
      ibAdd: function () {
        var t = K.val("ibText"); if (!t) return;
        var a = items(); a.unshift({ id: K.uid(), text: t.slice(0, 500), at: K.ymd() }); save(a, "capture"); K.render(); K.toast("Captured.");
      },
      ibDecide: function (id) { K._decide = K._decide === id ? null : id; K.render(); },
      ibAction: function (id) {
        var a = items(), i = find(a, id); if (i < 0) return;
        var nx = K.val("ibNext"); if (!nx) { K.toast("Write the next step: what you will physically do."); return; }
        a[i].kind = "action"; a[i].next = nx.slice(0, 300); a[i].due = K.val("ibDue") || K.addDays(K.ymd(), 2); K._decide = null; save(a, "decide"); K.render();
      },
      ibNote: function (id) { var a = items(), i = find(a, id); if (i < 0) return; a[i].kind = "note"; K._decide = null; save(a, "note"); K.render(); },
      ibDone: function (id) { var a = items(), i = find(a, id); if (i < 0) return; a[i].done = true; a[i].doneAt = K.ymd(); save(a, "done"); K.render(); K.toast("Done. One less thing."); },
      ibDel: function (id) { var a = items(), i = find(a, id); if (i < 0) return; a.splice(i, 1); save(a, "delete"); K.render(); K.toast("Deleted."); }
    }
  });
})();
