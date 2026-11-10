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
    if (x.kind === "action") h += '<div class="muted">' + K.esc(K.t("inbox.next_prefix", "Next: ")) + K.esc(x.next || "") + (x.due ? K.esc(K.t("inbox.by", " · by {d}", { d: x.due })) : "") + (x.due && x.due < K.ymd() ? ' <span class="tag late">' + K.esc(K.t("inbox.late", "late")) + '</span>' : "") + "</div>";
    if (x.kind === "note") h += '<div class="muted">' + K.esc(K.t("inbox.note_kept", "Note, kept {d}", { d: x.at })) + "</div>";
    h += "</div>";
    if (!x.kind) h += '<button data-a="ibDecide" data-x="' + id + '">' + K.esc(K.t("inbox.decide", "Decide")) + '</button>';
    else if (x.kind === "action" && !x.done) h += '<button data-a="ibDone" data-x="' + id + '">' + K.esc(K.t("inbox.done", "Done")) + '</button>';
    h += '<button class="ghost" data-a="ibDel" data-x="' + id + '" aria-label="' + K.esc(K.t("inbox.delete", "Delete")) + '">✕</button></li>';
    if (K._decide === x.id) {
      h += '<li class="form"><label for="ibNext">' + K.esc(K.t("inbox.next_step_label", "Next physical step")) + '</label><input id="ibNext" placeholder="' + K.esc(K.t("inbox.next_step_ph", "e.g. call the vendor about the renewal")) + '">'
        + '<label for="ibDue">' + K.esc(K.t("inbox.by_label", "By")) + '</label><input id="ibDue" type="date" value="' + K.addDays(K.ymd(), 2) + '">'
        + '<div class="btns"><button class="primary" data-a="ibAction" data-x="' + id + '">' + K.esc(K.t("inbox.is_action", "It is an action")) + '</button>'
        + '<button data-a="ibNote" data-x="' + id + '">' + K.esc(K.t("inbox.keep_note", "Keep as a note")) + '</button></div></li>';
    }
    return h;
  }
  K.module({
    id: "inbox", label: function () { return K.term("inbox", "Inbox"); },
    captureCard: function () {
      var u = undecided().length, d = dueActions().length;
      return K.card(K.esc(K.t("inbox.capture", "Capture")), '<div class="inline"><input id="ibText" aria-label="' + K.esc(K.t("inbox.capture_aria", "Capture a thought, ask or task")) + '" placeholder="' + K.esc(K.t("inbox.capture_ph", "One line is enough")) + '"><button data-a="ibAdd">' + K.esc(K.t("inbox.add", "Add")) + '</button></div>'
        + ((u || d) ? '<p class="muted">' + (d ? K.esc(K.t("inbox.due_n", "{n} action(s) due", { n: d })) + " · " : "") + (u ? K.esc(K.t("inbox.to_decide_n", "{n} to decide", { n: u })) + " · " : "") + '<a href="#" data-a="go" data-x="inbox">' + K.esc(K.t("inbox.open", "open {n}", { n: K.term("inbox", "Inbox") })) + "</a></p>" : ""));
    },
    render: function () {
      var a = items(), open = a.filter(function (x) { return !(x.kind === "action" && x.done); });
      open.sort(function (x, y) { return (x.kind ? 1 : 0) - (y.kind ? 1 : 0) || String(x.due || "9").localeCompare(String(y.due || "9")); });
      var done = a.filter(function (x) { return x.done; }).length;
      return "<h2>" + K.esc(K.term("inbox", "Inbox")) + "</h2>" + this.captureCard()
        + K.card("", open.length ? "<ul class='list'>" + open.map(row).join("") + "</ul>" : "<p>" + K.esc(K.t("inbox.empty", "Empty. Everything is decided.")) + "</p>")
        + (done ? '<p class="muted">' + K.esc(K.t("inbox.done_so_far", "{n} done so far.", { n: done })) + "</p>" : "");
    },
    next: function () {
      var d = dueActions(); if (d.length) return { score: 80, text: d[0].next || d[0].text, why: K.t("inbox.due_why", "An action from your inbox is due") + (d.length > 1 ? K.t("inbox.and_more", " (and {n} more)", { n: d.length - 1 }) : "") + ".", go: "inbox" };
      var u = undecided(); if (u.length >= 3) return { score: 50, text: K.t("inbox.decide_n", "Decide {n} inbox items", { n: u.length }), why: K.t("inbox.decide_why", "Undecided items turn into worry. Two minutes each."), go: "inbox" };
      return null;
    },
    week: function (from) {
      var n = items().filter(function (x) { return x.done && x.doneAt >= from; }).length;
      return n ? [{ n: n, what: K.t("inbox.week", "inbox action(s) done") }] : [];
    },
    acts: {
      ibAdd: function () {
        var t = K.val("ibText"); if (!t) return;
        var a = items(); a.unshift({ id: K.uid(), text: t.slice(0, 500), at: K.ymd() }); save(a, "capture"); K.render(); K.toast(K.t("inbox.toast_captured", "Captured."));
      },
      ibDecide: function (id) { K._decide = K._decide === id ? null : id; K.render(); },
      ibAction: function (id) {
        var a = items(), i = find(a, id); if (i < 0) return;
        var nx = K.val("ibNext"); if (!nx) { K.toast(K.t("inbox.toast_next", "Write the next step: what you will physically do.")); return; }
        a[i].kind = "action"; a[i].next = nx.slice(0, 300); a[i].due = K.val("ibDue") || K.addDays(K.ymd(), 2); K._decide = null; save(a, "decide"); K.render();
      },
      ibNote: function (id) { var a = items(), i = find(a, id); if (i < 0) return; a[i].kind = "note"; K._decide = null; save(a, "note"); K.render(); },
      ibDone: function (id) { var a = items(), i = find(a, id); if (i < 0) return; a[i].done = true; a[i].doneAt = K.ymd(); save(a, "done"); K.render(); K.toast(K.t("inbox.toast_done", "Done. One less thing.")); },
      ibDel: function (id) { var a = items(), i = find(a, id); if (i < 0) return; a.splice(i, 1); save(a, "delete"); K.render(); K.toast(K.t("inbox.toast_deleted", "Deleted.")); }
    }
  });
})();
