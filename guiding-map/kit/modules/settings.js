/* Settings: who it is for, the principles behind it, backup (export and import), sync with your own estate, theme, Undo.
   Backup is a plain JSON file: it always works, with or without the estate. */
(function () {
  var K = window.OSK;
  function syncBlock() {
    var c = K.syncCfg(), own = K.get("~sync", null), f = K.get("~syncFails", 0), last = K.get("~synced", null), note = K.get("~syncNote", null);
    var h = c ? "<p>" + K.esc(K.t("settings.synced", "Synced with your estate")) + (last ? K.esc(K.t("settings.synced_last", ", last at {d}", { d: last })) : "") + (own ? "" : K.esc(K.t("settings.pairing_note", " (using the Life OS pairing on this address)"))) + ".</p>" + (f > 2 ? '<p class="tag late">' + K.esc(K.t("settings.sync_fails", "The last {n} tries failed. Your data is safe here; it will catch up.", { n: f })) + "</p>" : "")
      : "<p>" + K.esc(K.t("settings.not_synced", "Not synced: your data lives on this device only. Export a backup now and then, or pair with your estate below.")) + "</p>";
    if (note) h += '<p class="muted">' + K.esc(note) + "</p>";
    h += '<details><summary>' + K.esc(K.t("settings.pair_self", "Pair this app by itself")) + '</summary><label for="syU">' + K.esc(K.t("settings.sync_address", "Sync address (in a phone app from a store, your estate's full address ending in /sync)")) + '</label><input id="syU" placeholder="/sync" value="' + K.esc((own && own.url) || "") + '">'
      + '<label for="syN">' + K.esc(K.t("settings.username", "Your user name on the estate")) + '</label><input id="syN" value="' + K.esc((own && own.user) || "") + '">'
      + '<label for="syK">' + K.esc(K.t("settings.device_key", "Device key")) + '</label><input id="syK" type="password" autocomplete="off">'
      + '<div class="btns"><button data-a="syncSave">' + K.esc(K.t("settings.pair", "Pair")) + '</button>' + (own ? '<button class="ghost" data-a="syncForget">' + K.esc(K.t("settings.forget", "Forget this pairing")) + '</button>' : "") + "</div></details>";
    return h + (c ? '<button data-a="syncNow">' + K.esc(K.t("settings.sync_now", "Sync now")) + '</button>' : "");
  }
  K.module({
    id: "settings", label: function () { return K.term("settings", "Settings"); },
    render: function () {
      var p = K.get("profile", {}), ed = K.ed, h = "<h2>" + K.esc(K.term("settings", "Settings")) + "</h2>";
      h += K.card(K.esc(K.t("settings.about", "About {n}", { n: ed.name })), "<p>" + K.esc(ed.tagline || "") + "</p>" + (ed.audience ? '<p class="muted">' + K.esc(K.t("settings.for", "For: ")) + K.esc(ed.audience) + "</p>" : "")
        + ((ed.principles || []).length ? "<ul class='list'>" + ed.principles.map(function (x) { return "<li><b>" + K.esc(x.name) + "</b>" + (x.core ? ' <span class="tag">' + K.esc(K.t("settings.core", "core")) + '</span>' : "") + ": " + K.esc(x.text) + "</li>"; }).join("") + "</ul>"
          + '<p class="muted">' + K.esc(K.t("settings.principles_note", "Core principles come from the estate's one shared list, so every app carries them and gets their improvements.")) + '</p>' : ""));
      if ((ed.whatsnew || []).length) h += K.card(K.esc(K.t("settings.whats_new", "What's new")), "<ul class='list'>" + ed.whatsnew.slice().reverse().map(function (n) { return "<li>" + K.esc(n.text) + ' <span class="muted">' + K.esc(n.date) + "</span></li>"; }).join("") + "</ul>");
      var L = K.langs();
      h += K.card(K.esc(K.t("settings.language", "Language")), "<p class='muted'>" + K.esc(K.t("settings.language_note", "Your choice is remembered on this device. Anything not translated yet shows in English.")) + "</p><div class='btns'>"
        + Object.keys(L).map(function (k) { var on = k === K.lang;
          return '<button data-a="setLang" data-x="' + K.esc(k) + '" aria-pressed="' + on + '" lang="' + K.esc(k) + '"' + (on ? ' class="primary"' : "") + ">" + K.esc(L[k].name || k)
            + (L[k].status === "beta" ? " · " + K.esc(K.t("lang.beta", "beta")) : "") + "</button>"; }).join("") + "</div>");
      h += K.card(K.esc(K.t("settings.you", "You")), '<label for="pfName">' + K.esc(K.t("settings.first_name", "First name")) + '</label><input id="pfName" value="' + K.esc(p.name || "") + '"><label for="pfOrg">' + K.esc(K.t("settings.org", "Organisation")) + '</label><input id="pfOrg" value="' + K.esc(p.org || "") + '"><button data-a="profileSave">' + K.esc(K.t("settings.save", "Save")) + '</button>');
      h += K.card(K.esc(K.t("settings.backup", "Backup")), '<p>' + K.esc(K.t("settings.backup_note", "Your data stays on this device. A backup is one file you can keep anywhere.")) + '</p><div class="btns"><button class="primary" data-a="exportNow">' + K.esc(K.t("settings.export", "Export a backup")) + '</button>'
        + '<label class="file">' + K.esc(K.t("settings.import", "Import a backup")) + '<input type="file" id="impFile" accept="application/json" data-c="importFile"></label></div>'
        + (K.get("lastExport", null) ? '<p class="muted">' + K.esc(K.t("settings.last_export", "Last export {d}", { d: K.get("lastExport") })) + "</p>" : ""));
      h += K.card(K.esc(K.t("settings.sync", "Sync")), syncBlock());
      h += K.card(K.esc(K.t("settings.look_undo", "Look and undo")), '<div class="btns"><button data-a="theme">' + K.esc(K.t("settings.theme", "Light or dark")) + '</button><button data-a="undo">' + K.esc(K.t("settings.undo", "Undo the last change")) + '</button></div>');
      return h;
    },
    next: function () {
      if (K.syncCfg()) return null;
      var le = K.get("lastExport", null), st = K.get("started", K.ymd());
      if ((le && K.days(le) > 30) || (!le && K.days(st) > 7 && K.keys().length > 5)) return { score: 28, text: K.t("settings.next_backup", "Export a backup (one tap)"), why: le ? K.t("settings.next_backup_why_recent", "Last backup {d}.", { d: le }) : K.t("settings.next_backup_why_none", "Nothing is synced and there is no backup yet."), go: "settings" };
      return null;
    },
    acts: {
      setLang: function (l) { K.setLang(l); },
      exportNow: function () {
        K.set("lastExport", K.ymd(), { noUndo: true });
        var blob = new Blob([JSON.stringify(K.dump(), null, 1)], { type: "application/json" });
        var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = (K.ed.id || "app") + "-backup-" + K.ymd() + ".json";
        document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
        K.toast(K.t("settings.toast_exported", "Backup saved to your downloads."));
      },
      importFile: function (_x, el) {
        var f = el.files && el.files[0]; if (!f) return;
        var r = new FileReader();
        r.onload = function () { try { K.load(JSON.parse(r.result)); K.render(); K.toast(K.t("settings.toast_restored", "Backup restored.")); } catch (e) { K.toast(K.t("settings.toast_not_restored", "Not restored: {e}", { e: e.message })); } };
        r.readAsText(f);
      },
      syncSave: function () {
        var u = K.val("syU"), n = K.val("syN"), k = K.val("syK");
        if (!u || !n || !k) { K.toast(K.t("settings.toast_need_all", "All three are needed: address, user name and key.")); return; }
        K.set("~sync", { url: u, user: n, key: k }); K.pull().then(function () { K.render(); }); K.toast(K.t("settings.toast_paired", "Paired. Syncing now."));
      },
      syncForget: function () { K.set("~sync", null); K.render(); },
      syncNow: function () { K.pull().then(function () { K.render(); K.toast(K.get("~syncFails", 0) ? K.t("settings.toast_unreachable", "Could not reach the estate. Your data is safe here.") : K.t("settings.toast_synced", "Synced.")); }); }
    }
  });
})();
