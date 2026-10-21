/* Settings: who it is for, the principles behind it, backup (export and import), sync with your own estate, theme, Undo.
   Backup is a plain JSON file: it always works, with or without the estate. */
(function () {
  var K = window.OSK;
  function syncBlock() {
    var c = K.syncCfg(), own = K.get("~sync", null), f = K.get("~syncFails", 0), last = K.get("~synced", null), note = K.get("~syncNote", null);
    var h = c ? "<p>Synced with your estate" + (last ? ", last at " + K.esc(last) : "") + (own ? "" : " (using the Life OS pairing on this address)") + ".</p>" + (f > 2 ? '<p class="tag late">The last ' + f + " tries failed. Your data is safe here; it will catch up.</p>" : "")
      : "<p>Not synced: your data lives on this device only. Export a backup now and then, or pair with your estate below.</p>";
    if (note) h += '<p class="muted">' + K.esc(note) + "</p>";
    h += '<details><summary>Pair this app by itself</summary><label for="syU">Sync address (in a phone app from a store, your estate\'s full address ending in /sync)</label><input id="syU" placeholder="/sync" value="' + K.esc((own && own.url) || "") + '">'
      + '<label for="syN">Your user name on the estate</label><input id="syN" value="' + K.esc((own && own.user) || "") + '">'
      + '<label for="syK">Device key</label><input id="syK" type="password" autocomplete="off">'
      + '<div class="btns"><button data-a="syncSave">Pair</button>' + (own ? '<button class="ghost" data-a="syncForget">Forget this pairing</button>' : "") + "</div></details>";
    return h + (c ? '<button data-a="syncNow">Sync now</button>' : "");
  }
  K.module({
    id: "settings", label: function () { return K.term("settings", "Settings"); },
    render: function () {
      var p = K.get("profile", {}), ed = K.ed, h = "<h2>" + K.esc(K.term("settings", "Settings")) + "</h2>";
      h += K.card("About " + K.esc(ed.name), "<p>" + K.esc(ed.tagline || "") + "</p>" + (ed.audience ? '<p class="muted">For: ' + K.esc(ed.audience) + "</p>" : "")
        + ((ed.principles || []).length ? "<ul class='list'>" + ed.principles.map(function (x) { return "<li><b>" + K.esc(x.name) + "</b>" + (x.core ? ' <span class="tag">core</span>' : "") + ": " + K.esc(x.text) + "</li>"; }).join("") + "</ul>"
          + '<p class="muted">Core principles come from the estate\'s one shared list, so every app carries them and gets their improvements.</p>' : ""));
      if ((ed.whatsnew || []).length) h += K.card("What's new", "<ul class='list'>" + ed.whatsnew.slice().reverse().map(function (n) { return "<li>" + K.esc(n.text) + ' <span class="muted">' + K.esc(n.date) + "</span></li>"; }).join("") + "</ul>");
      h += K.card("You", '<label for="pfName">First name</label><input id="pfName" value="' + K.esc(p.name || "") + '"><label for="pfOrg">Organisation</label><input id="pfOrg" value="' + K.esc(p.org || "") + '"><button data-a="profileSave">Save</button>');
      h += K.card("Backup", '<p>Your data stays on this device. A backup is one file you can keep anywhere.</p><div class="btns"><button class="primary" data-a="exportNow">Export a backup</button>'
        + '<label class="file">Import a backup<input type="file" id="impFile" accept="application/json" data-c="importFile"></label></div>'
        + (K.get("lastExport", null) ? '<p class="muted">Last export ' + K.esc(K.get("lastExport")) + "</p>" : ""));
      h += K.card("Sync", syncBlock());
      h += K.card("Look and undo", '<div class="btns"><button data-a="theme">Light or dark</button><button data-a="undo">Undo the last change</button></div>');
      return h;
    },
    next: function () {
      if (K.syncCfg()) return null;
      var le = K.get("lastExport", null), st = K.get("started", K.ymd());
      if ((le && K.days(le) > 30) || (!le && K.days(st) > 7 && K.keys().length > 5)) return { score: 28, text: "Export a backup (one tap)", why: le ? "Last backup " + le + "." : "Nothing is synced and there is no backup yet.", go: "settings" };
      return null;
    },
    acts: {
      exportNow: function () {
        K.set("lastExport", K.ymd(), { noUndo: true });
        var blob = new Blob([JSON.stringify(K.dump(), null, 1)], { type: "application/json" });
        var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = (K.ed.id || "app") + "-backup-" + K.ymd() + ".json";
        document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
        K.toast("Backup saved to your downloads.");
      },
      importFile: function (_x, el) {
        var f = el.files && el.files[0]; if (!f) return;
        var r = new FileReader();
        r.onload = function () { try { K.load(JSON.parse(r.result)); K.render(); K.toast("Backup restored."); } catch (e) { K.toast("Not restored: " + e.message); } };
        r.readAsText(f);
      },
      syncSave: function () {
        var u = K.val("syU"), n = K.val("syN"), k = K.val("syK");
        if (!u || !n || !k) { K.toast("All three are needed: address, user name and key."); return; }
        K.set("~sync", { url: u, user: n, key: k }); K.pull().then(function () { K.render(); }); K.toast("Paired. Syncing now.");
      },
      syncForget: function () { K.set("~sync", null); K.render(); },
      syncNow: function () { K.pull().then(function () { K.render(); K.toast(K.get("~syncFails", 0) ? "Could not reach the estate. Your data is safe here." : "Synced."); }); }
    }
  });
})();
