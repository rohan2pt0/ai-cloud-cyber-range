/* Today: the one screen opened every morning. The single next step (picked from every module), today's rituals,
   a capture box and the week's visible wins. Nothing here asks for typing that another screen could work out. */
(function () {
  var K = window.OSK;
  function greet() {
    var h = new Date().getHours(), p = K.get("profile", {});
    return (h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening") + (p.name ? ", " + p.name : "");
  }
  // Every module may offer its most pressing item; the highest score wins. Ties keep the module order of the edition.
  K.nextStep = function () {
    var best = null;
    Object.keys(K.mods).forEach(function (id) {
      var m = K.mods[id]; if (!m.next || !K.cfg(id)) return;
      var c; try { c = m.next(); } catch (e) { c = null; }
      (Array.isArray(c) ? c : c ? [c] : []).forEach(function (x) { if (x && (!best || x.score > best.score)) best = x; });
    });
    return best;
  };
  function oneStep() {
    var n = K.nextStep();
    if (!n) return K.card("Your next step", "<p class='big'>All clear. Nothing is late and nothing waits on you.</p><p class='muted'>A good day to think ahead: open " + K.esc(K.term("playbooks", "Playbooks")) + ".</p>", "hero");
    return K.card("Your next step", "<p class='big'>" + K.esc(n.text) + "</p>" + (n.why ? "<p class='muted'>" + K.esc(n.why) + "</p>" : "")
      + (n.go ? '<button class="primary" data-a="go" data-x="' + K.esc(n.go) + '">Do it now</button>' : ""), "hero");
  }
  function setup() {
    var p = K.get("profile", null);
    if (p && p.name) return "";
    var ed = K.ed;
    return K.card("Start in one minute",
      "<p>" + K.esc(ed.welcome || "Tell the app who it is for. Everything stays on this device unless you pair it with your estate.") + "</p>"
      + '<label for="pfName">Your first name</label><input id="pfName" autocomplete="given-name">'
      + '<label for="pfOrg">Organisation (optional)</label><input id="pfOrg" autocomplete="organization">'
      + '<button class="primary" data-a="profileSave">Start</button>');
  }
  // What changed in the kit or this app, shown once: dismissing it hides everything up to that day.
  function newsCard() {
    var seen = K.get("~newsSeen", ""), fresh = (K.ed.whatsnew || []).filter(function (n) { return n.date > seen && K.days(n.date) <= 30; });
    if (!fresh.length) return "";
    return K.card("New in " + K.esc(K.ed.name), "<ul class='list'>" + fresh.map(function (n) { return "<li>" + K.esc(n.text) + ' <span class="muted">' + K.esc(n.date) + "</span></li>"; }).join("")
      + '</ul><button class="ghost" data-a="newsSeen" data-x="' + K.esc(fresh[fresh.length - 1].date) + '">Got it</button>');
  }
  K.module({
    id: "today", icon: "", label: function () { return K.term("today", "Today"); },
    render: function () {
      var h = '<p class="greet">' + K.esc(greet()) + "</p>";
      if (K.ed.north_star) h += '<p class="north">' + K.esc(K.ed.north_star) + "</p>";
      h += setup() + newsCard() + oneStep();
      if (K.mods.rituals && K.cfg("rituals")) h += K.mods.rituals.todayCard();
      if (K.mods.inbox && K.cfg("inbox")) h += K.mods.inbox.captureCard();
      if (K.mods.feeds && K.cfg("feeds")) h += K.mods.feeds.todayCard();
      if (K.mods.progress && K.cfg("progress")) h += K.mods.progress.weekCard();
      return h;
    },
    acts: {
      newsSeen: function (d) { var all = (K.ed.whatsnew || []).map(function (n) { return n.date; }).sort(); K.set("~newsSeen", all[all.length - 1] || d); K.render(); },
      profileSave: function () {
        var n = K.val("pfName"); if (!n) { K.toast("Type a first name, or anything you like to be called."); return; }
        K.set("profile", { name: n, org: K.val("pfOrg"), at: K.ymd() }, { what: "profile" }); K.render();
      }
    }
  });
})();
