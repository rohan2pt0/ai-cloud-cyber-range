/* Registers: one module, any number of lists, each described by the edition (risks, decisions, exceptions,
   stakeholders, team, lessons...). A register can score items (likelihood x impact), date them (due, expiry) and
   ask for a regular touch (last contact + every N days). Whatever is late or scores high rises to Today. */
(function () {
  var K = window.OSK;
  function regs() { return K.cfg("registers") || []; }
  function reg(id) { var r = regs(); for (var i = 0; i < r.length; i++) if (r[i].id === id) return r[i]; return null; }
  function rows(r) { return K.get("reg." + r.id, []); }
  function save(r, a, w) { K.set("reg." + r.id, a, { what: w }); }
  function idx(a, id) { for (var i = 0; i < a.length; i++) if (a[i].id === id) return i; return -1; }
  function isOpen(r, x) { return !(r.status && (r.status.closed || []).indexOf(x[r.status.field]) >= 0); }
  K.regScore = function (r, x) { return r.score ? r.score.reduce(function (p, f) { return p * (parseFloat(x[f]) || 0); }, 1) : 0; };
  function band(r, s) { var b = r.bands || [[15, "high"], [8, "medium"], [0, "low"]]; for (var i = 0; i < b.length; i++) if (s >= b[i][0]) return b[i][1]; return "low"; }
  // the date this item next needs you, and why
  function when(r, x) {
    if (!isOpen(r, x)) return null;
    if (r.touch && x[r.touch.last]) { var ev = parseInt(x[r.touch.every], 10) || r.touch.default || 30; return { d: K.addDays(x[r.touch.last], ev), why: K.t("registers.touch_base", "time to touch base") }; }
    if (r.touch && !x[r.touch.last]) return { d: K.ymd(), why: K.t("registers.no_contact", "no contact logged yet") };
    if (r.expiry && x[r.expiry.field]) return { d: K.addDays(x[r.expiry.field], -(r.expiry.warn || 30)), why: K.t("registers.expires", "expires {d}", { d: x[r.expiry.field] }) };
    if (r.due && x[r.due]) return { d: x[r.due], why: K.t("registers.due", "due {d}", { d: x[r.due] }) };
    return null;
  }
  function input(f, v) {
    var id = "rf_" + f.id, val = v == null ? (f.default == null ? "" : f.default) : v, h = '<label for="' + id + '">' + K.esc(f.label) + (f.required ? " *" : "") + "</label>";
    if (f.type === "select") return h + '<select id="' + id + '">' + (f.required ? "" : "<option value=''>-</option>") + (f.options || []).map(function (o) { return "<option" + (String(o) === String(val) ? " selected" : "") + ">" + K.esc(o) + "</option>"; }).join("") + "</select>";
    if (f.type === "scale") { var o = ""; for (var i = 1; i <= (f.max || 5); i++) o += "<option" + (String(i) === String(val) ? " selected" : "") + ">" + i + "</option>"; return h + '<select id="' + id + '">' + o + "</select>" + (f.hint ? '<div class="muted">' + K.esc(f.hint) + "</div>" : ""); }
    if (f.type === "long") return h + '<textarea id="' + id + '" rows="3">' + K.esc(val) + "</textarea>";
    if (f.type === "date" && val === "today") val = K.ymd();
    return h + '<input id="' + id + '" type="' + (f.type === "date" ? "date" : f.type === "number" ? "number" : "text") + '" value="' + K.esc(val) + '"' + (f.placeholder ? ' placeholder="' + K.esc(f.placeholder) + '"' : "") + ">";
  }
  function form(r, x) {
    return '<div class="form">' + r.fields.map(function (f) { return input(f, x ? x[f.id] : null); }).join("")
      + '<div class="btns"><button class="primary" data-a="regSave" data-x="' + K.esc(r.id + "|" + (x ? x.id : "")) + '">' + K.esc(K.t("registers.save", "Save")) + '</button><button data-a="regCancel">' + K.esc(K.t("registers.cancel", "Cancel")) + '</button></div></div>';
  }
  function line(r, x) {
    var s = K.regScore(r, x), w = when(r, x), late = w && w.d <= K.ymd(), id = K.esc(r.id + "|" + x.id);
    var sub = (r.list || []).map(function (f) { return x[f] ? K.esc(x[f]) : ""; }).filter(Boolean).join(" · ");
    var h = '<li class="row"><div class="grow"><b>' + K.esc(x[r.title] || K.t("registers.untitled", "(untitled)")) + "</b>"
      + (r.score ? ' <span class="tag ' + band(r, s) + '">' + s + "</span>" : "") + (!isOpen(r, x) ? ' <span class="tag">' + K.esc(K.t("registers.closed", "closed")) + "</span>" : "")
      + (w ? ' <span class="' + (late ? "tag late" : "muted") + '">' + K.esc(w.why) + "</span>" : "")
      + (sub ? '<div class="muted">' + sub + "</div>" : "") + "</div>";
    if (r.touch && isOpen(r, x)) h += '<button data-a="regTouch" data-x="' + id + '">' + K.esc(K.t("registers.touched_today", "Touched today")) + '</button>';
    h += '<button data-a="regEdit" data-x="' + id + '">' + K.esc(K.t("registers.edit", "Edit")) + '</button></li>';
    if (K._regEdit === r.id + "|" + x.id) h += '<li class="form">' + form(r, x) + '<button class="ghost" data-a="regDel" data-x="' + id + '">' + K.esc(K.t("registers.delete_this", "Delete this {n}", { n: r.item || K.t("registers.item", "item") })) + "</button></li>";
    return h;
  }
  K.module({
    id: "registers",
    label: function (sub) { var r = reg(sub); return r ? r.label : K.term("registers", "Registers"); },
    render: function (sub) {
      var r = reg(sub) || regs()[0]; if (!r) return "<p>" + K.esc(K.t("registers.empty", "No registers in this edition.")) + "</p>";
      var a = rows(r).slice(), showAll = K._regAll === r.id;
      a.sort(function (x, y) {
        return (isOpen(r, y) ? 1 : 0) - (isOpen(r, x) ? 1 : 0) || K.regScore(r, y) - K.regScore(r, x)
          || String((when(r, x) || {}).d || "9").localeCompare(String((when(r, y) || {}).d || "9"));
      });
      var open = a.filter(function (x) { return isOpen(r, x); }), shown = showAll ? a : open;
      // one-open-action: a long list gets "Show only the vital few (80/20)": the top fifth by risk (at least three)
      var long = !showAll && open.length > 7, vital = long && K.get("regVital", {})[r.id];
      if (vital) shown = open.slice(0, Math.max(3, Math.ceil(open.length / 5)));
      var h = "<h2>" + K.esc(r.label) + "</h2>" + (r.intro ? '<p class="muted">' + K.esc(r.intro) + "</p>" : "");
      h += K.card("", (shown.length ? "<ul class='list'>" + shown.map(function (x) { return line(r, x); }).join("") + "</ul>" : "<p>" + K.esc(K.t("registers.nothing_open", "Nothing open.")) + "</p>")
        + (long ? '<button class="ghost" data-a="regVital" data-x="' + K.esc(r.id) + '" aria-pressed="' + !!vital + '">' + K.esc(vital ? K.t("registers.show_all", "Show all {n} open", { n: open.length }) : K.t("registers.vital_few", "Show only the vital few (80/20)")) + "</button>" : "")
        + (a.length > open.length ? '<button class="ghost" data-a="regAll" data-x="' + K.esc(r.id) + '">' + K.esc(showAll ? K.t("registers.hide_closed", "Hide closed") : K.t("registers.show_closed", "Show closed ({n})", { n: a.length - open.length })) + "</button>" : ""));
      h += K._regNew === r.id ? K.card(K.esc(K.t("registers.new_item", "New {n}", { n: r.item || K.t("registers.item", "item") })), form(r, null)) : '<button class="primary" data-a="regNew" data-x="' + K.esc(r.id) + '">' + K.esc(K.t("registers.add_item", "Add a {n}", { n: r.item || K.t("registers.item", "item") })) + "</button>";
      if (r.guide) h += K.card(K.esc(K.t("registers.guide", "How to use it well")), "<ul class='list'>" + r.guide.map(function (g) { return "<li>" + K.esc(g) + "</li>"; }).join("") + "</ul>");
      return h;
    },
    next: function () {
      var out = [];
      regs().forEach(function (r) {
        rows(r).forEach(function (x) {
          var w = when(r, x), s = K.regScore(r, x);
          if (w && w.d <= K.ymd()) out.push({ score: 45 + Math.min(30, s) + (r.weight || 0), text: (r.next_verb || K.t("registers.review", "Review")) + ": " + (x[r.title] || r.item), why: (r.item || K.t("registers.item", "item")) + ", " + w.why + ".", go: "registers:" + r.id });
          else if (r.score && isOpen(r, x) && band(r, s) === "high" && !x[r.due]) out.push({ score: 55 + s, text: K.t("registers.treatment_date", "Give the {i} “{t}” a treatment date", { i: r.item || K.t("registers.item", "item"), t: x[r.title] || "" }), why: K.t("registers.scored_high", "Scored {n}: high, and nothing is dated.", { n: s }), go: "registers:" + r.id });
        });
      });
      return out;
    },
    week: function (from) {
      var out = [];
      regs().forEach(function (r) {
        var a = rows(r), added = a.filter(function (x) { return x.at >= from; }).length, closed = a.filter(function (x) { return x.closedAt >= from; }).length;
        if (added) out.push({ n: added, what: K.t("registers.recorded", "{n}(s) recorded", { n: r.item || K.t("registers.item", "item") }) });
        if (closed) out.push({ n: closed, what: K.t("registers.closed_count", "{n}(s) closed", { n: r.item || K.t("registers.item", "item") }) });
      });
      return out;
    },
    count: function (rid, open) { var r = reg(rid); if (!r) return 0; return rows(r).filter(function (x) { return !open || isOpen(r, x); }).length; },
    acts: {
      regNew: function (rid) { K._regNew = rid; K._regEdit = null; K.render(); },
      regCancel: function () { K._regNew = K._regEdit = null; K.render(); },
      regAll: function (rid) { K._regAll = K._regAll === rid ? null : rid; K.render(); },
      regVital: function (rid) { var v = K.get("regVital", {}); v[rid] = !v[rid]; K.set("regVital", v); K.render(); },
      regEdit: function (x) { K._regEdit = K._regEdit === x ? null : x; K._regNew = null; K.render(); },
      regSave: function (x) {
        var p = String(x).split("|"), r = reg(p[0]); if (!r) return;
        var a = rows(r), i = p[1] ? idx(a, p[1]) : -1, o = i >= 0 ? a[i] : { id: K.uid(), at: K.ymd() }, wasOpen = i >= 0 ? isOpen(r, o) : true;
        for (var j = 0; j < r.fields.length; j++) {
          var f = r.fields[j], v = K.val("rf_" + f.id).slice(0, f.type === "long" ? 2000 : 300);
          if (f.required && !v) { K.toast(K.t("registers.needed", "{n} is needed.", { n: f.label })); return; }
          o[f.id] = f.type === "number" || f.type === "scale" ? (v === "" ? "" : +v) : v;
        }
        if (wasOpen && !isOpen(r, o)) o.closedAt = K.ymd();
        if (i < 0) a.push(o);
        K._regNew = K._regEdit = null; save(r, a, i < 0 ? "new " + (r.item || "item") : "edit"); K.render(); K.toast(K.t("registers.toast_saved", "Saved."));
      },
      regTouch: function (x) {
        var p = String(x).split("|"), r = reg(p[0]); if (!r || !r.touch) return;
        var a = rows(r), i = idx(a, p[1]); if (i < 0) return;
        a[i][r.touch.last] = K.ymd(); save(r, a, "touch"); K.render(); K.toast(K.t("registers.toast_logged", "Logged. Next one is dated."));
      },
      regDel: function (x) {
        var p = String(x).split("|"), r = reg(p[0]); if (!r) return;
        var a = rows(r), i = idx(a, p[1]); if (i < 0) return;
        a.splice(i, 1); K._regEdit = null; save(r, a, "delete"); K.render(); K.toast(K.t("registers.toast_deleted", "Deleted."));
      }
    }
  });
})();
