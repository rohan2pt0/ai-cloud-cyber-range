/* Today: the one screen opened every morning. The single next step (picked from every module), today's rituals,
   a capture box and the week's visible wins. Nothing here asks for typing that another screen could work out. */
(function () {
  var K = window.OSK;
  function greet() {
    var h = new Date().getHours(), p = K.get("profile", {});
    return K.t(h < 12 ? "today.morning" : h < 17 ? "today.afternoon" : "today.evening", h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening") + (p.name ? ", " + p.name : "");
  }
  // Every module may offer its pressing items; the highest score (risk) wins. Ties keep the module order of the edition.
  // One open action (principle one-open-action): the winner is the only primary; the rest wait, folded, under "Later (n)".
  K.nextSteps = function () {
    var all = [], order = 0;
    Object.keys(K.mods).forEach(function (id) {
      var m = K.mods[id]; if (!m.next || !K.cfg(id)) return;
      var c; try { c = m.next(); } catch (e) { c = null; }
      (Array.isArray(c) ? c : c ? [c] : []).forEach(function (x) { if (x && x.text) all.push({ x: x, o: order++ }); });
    });
    return all.sort(function (a, b) { return (b.x.score || 0) - (a.x.score || 0) || a.o - b.o; }).map(function (a) { return a.x; });
  };
  K.nextStep = function () { return K.nextSteps()[0] || null; };
  function oneStep(quiet) {
    var all = K.nextSteps(), n = all[0], later = all.slice(1);
    if (!n) return K.card(K.esc(K.t("today.next", "Your next step")), "<p class='big'>" + K.esc(K.t("today.clear", "All clear. Nothing is late and nothing waits on you.")) + "</p><p class='muted'>" + K.esc(K.t("today.think_ahead", "A good day to think ahead: open {p}.", { p: K.term("playbooks", "Playbooks") })) + "</p>", "hero");
    return K.card(K.esc(K.t("today.next", "Your next step")), "<p class='big'>" + K.esc(n.text) + "</p>" + (n.why ? "<p class='muted'>" + K.esc(n.why) + "</p>" : "")
      + (n.go ? '<button class="' + (quiet ? "" : "primary") + '" data-a="go" data-x="' + K.esc(n.go) + '">' + K.esc(K.t("today.do", "Do it now")) + '</button>' : "")
      + (later.length ? '<details class="later"><summary>' + K.esc(K.t("today.later", "Later ({n})", { n: later.length })) + '</summary><ul class="list">'
        + later.slice(0, 12).map(function (x) { return "<li>" + (x.go ? '<a href="#" data-a="go" data-x="' + K.esc(x.go) + '">' + K.esc(x.text) + "</a>" : K.esc(x.text)) + "</li>"; }).join("")
        + "</ul><p class='muted'>" + K.esc(K.t("today.later_note", "Chosen by risk. Finish the first; the next moves up by itself.")) + "</p></details>" : ""), "hero");
  }
  function setup() {
    var p = K.get("profile", null);
    if (p && p.name) return "";
    var ed = K.ed;
    return K.card(K.esc(K.t("today.setup_title", "Start in one minute")),
      "<p>" + K.esc(ed.welcome || K.t("today.setup_welcome", "Tell the app who it is for. Everything stays on this device unless you pair it with your estate.")) + "</p>"
      + '<label for="pfName">' + K.esc(K.t("today.first_name", "Your first name")) + '</label><input id="pfName" autocomplete="given-name">'
      + '<label for="pfOrg">' + K.esc(K.t("today.org_optional", "Organisation (optional)")) + '</label><input id="pfOrg" autocomplete="organization">'
      + '<button class="primary" data-a="profileSave">' + K.esc(K.t("today.start", "Start")) + '</button>');
  }
  // What changed in the kit or this app, shown once: dismissing it hides everything up to that day.
  function newsCard() {
    var seen = K.get("~newsSeen", ""), fresh = (K.ed.whatsnew || []).filter(function (n) { return n.date > seen && K.days(n.date) <= 30; });
    if (!fresh.length) return "";
    return K.card(K.esc(K.t("today.new_in", "New in {name}", { name: K.ed.name })), "<ul class='list'>" + fresh.map(function (n) { return "<li>" + K.esc(n.text) + ' <span class="muted">' + K.esc(n.date) + "</span></li>"; }).join("")
      + '</ul><button class="ghost" data-a="newsSeen" data-x="' + K.esc(fresh[fresh.length - 1].date) + '">' + K.esc(K.t("today.got_it", "Got it")) + '</button>');
  }
  K.module({
    id: "today", icon: "", label: function () { return K.t("today.title", K.term("today", "Today")); },
    render: function () {
      var h = '<p class="greet">' + K.esc(greet()) + "</p>";
      if (K.ed.north_star) h += '<p class="north">' + K.esc(K.ed.north_star) + "</p>";
      var su = setup();
      h += su + newsCard() + oneStep(!!su);   // during first-run setup, Start is the one primary
      // one quiet invitation to lock, once there is something to protect: never at first run, dismissed for good in one tap
      if (!su && !K.lockInfo().on && K.lockInfo().prf && !K.get("~lockOfferSeen", false))
        h += K.card(K.esc(K.t("lock.title_off", "Lock")), "<p>" + K.esc(K.t("lock.offer", "Keep this private: unlock with this device's Face ID, fingerprint or Windows Hello. No new password.")) + "</p>"
          + '<div class="btns"><button data-a="lockOn">' + K.esc(K.t("lock.turn_on", "Turn on")) + '</button><button class="ghost" data-a="lockLater">' + K.esc(K.t("lock.not_now", "Not now")) + "</button></div>");
      if (K.mods.rituals && K.cfg("rituals")) h += K.mods.rituals.todayCard();
      if (K.mods.inbox && K.cfg("inbox")) h += K.mods.inbox.captureCard();
      if (K.mods.feeds && K.cfg("feeds")) h += K.mods.feeds.todayCard();
      if (K.mods.progress && K.cfg("progress")) h += K.mods.progress.weekCard();
      return h;
    },
    acts: {
      lockOn: function () { K.set("~lockOfferSeen", true); K.lockStart(); },
      lockLater: function () { K.set("~lockOfferSeen", true); K.render(); },
      newsSeen: function (d) { var all = (K.ed.whatsnew || []).map(function (n) { return n.date; }).sort(); K.set("~newsSeen", all[all.length - 1] || d); K.render(); },
      profileSave: function () {
        var n = K.val("pfName"); if (!n) { K.toast(K.t("today.toast_name", "Type a first name, or anything you like to be called.")); return; }
        K.set("profile", { name: n, org: K.val("pfOrg"), at: K.ymd() }, { what: "profile" }); K.render();
      }
    }
  });
})();
