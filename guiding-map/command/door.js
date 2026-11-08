/* The Command Center door (doc 131): a page on the product site, so it needs no machine of yours. It keeps your list of machines on
   this device, asks each one "are you up?", and opens the best one. Text is always set as text, never as markup. */
(function () {
  "use strict";
  var L = window.DoorLogic, KEY = "securax-door-v1", SEEN = "securax-door-seen-v1", EVERY_MS = 15000, TIMEOUT_MS = 4000;
  var nodes = read(KEY, []), seen = read(SEEN, {}), state = {}, checkedAt = null, pending = null;
  nodes = L.sanitizeList(nodes);

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function read(k, d) { try { return JSON.parse(localStorage.getItem(k)) || d; } catch (e) { return d; } }
  function write(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private window: the list lasts for this visit */ } }
  function save() { write(KEY, nodes); }
  function when(iso) { var d = new Date(iso); return isNaN(d) ? "" : d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); }

  // The truth about a machine comes from the machine itself: it answers one path, readable from any site, with a fixed sentence. A dead
  // tunnel still serves an error page, so "something answered" is not "it is up"; only that exact answer is.
  function probe(n) {
    var t0 = performance.now(), ctl = new AbortController(), timer = setTimeout(function () { ctl.abort(); }, TIMEOUT_MS);
    return fetch(n.url + "_door.json?t=" + Date.now(), { cache: "no-store", credentials: "omit", mode: "cors", referrerPolicy: "no-referrer", signal: ctl.signal })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return j && j.ok === true && j.service === "securax-command-center" ? { up: true, ms: Math.round(performance.now() - t0) } : { up: false, ms: 0 }; })
      .catch(function () { return { up: false, ms: 0 }; })
      .then(function (s) {
        clearTimeout(timer);
        state[n.url] = s;
        if (s.up) seen[n.url] = new Date().toISOString();
        return s;
      });
  }
  function checkAll() {
    if (!nodes.length) { render(); return Promise.resolve(); }
    pending = Promise.all(nodes.map(probe)).then(function () { checkedAt = new Date(); write(SEEN, seen); render(); pending = null; });
    return pending;
  }

  function statusCard() {
    var box = $("status"); box.textContent = "";
    if (!nodes.length) {
      box.appendChild(el("h2", null, "Add your first machine"));
      box.appendChild(el("p", null, "Open the Command Center on your laptop or server, copy the address you used, and add it below. This page then watches it and opens whichever machine is up."));
      var go = el("button", "btn", "Add a machine"); go.type = "button";
      go.addEventListener("click", function () { $("machines").open = true; $("f-url").focus(); });
      box.appendChild(go);
      return;
    }
    if (navigator.onLine === false) {
      box.appendChild(el("div", "big", "This device is offline"));
      box.appendChild(el("p", null, "Your machines cannot be reached from here right now. The Life OS and Vantage below still open from this device's own copy."));
      return;
    }
    if (!Object.keys(state).length) { box.appendChild(el("p", null, "Checking your machines…")); return; }
    var pick = L.pickBest(nodes, state), upCount = nodes.filter(function (n) { return state[n.url] && state[n.url].up; }).length;
    if (pick.node) {
      var h = el("div", "big"); h.appendChild(el("span", "dot up")); h.appendChild(el("span", null, pick.node.name + " is up"));
      box.appendChild(h);
      box.appendChild(el("p", null, upCount + " of " + nodes.length + " machine" + (nodes.length === 1 ? "" : "s") + " answering"
        + (pick.tier === "standby" ? ". This is your standby: none of your primary machines is answering." : ", and this one answered fastest (" + state[pick.node.url].ms + " ms).")));
      var open = el("a", "btn", "Open Command Center"); open.href = pick.node.url + "hub.html"; open.rel = "noopener";
      box.appendChild(open);
    } else {
      var d = el("div", "big"); d.appendChild(el("span", "dot down")); d.appendChild(el("span", null, "No machine is answering"));
      box.appendChild(d);
      box.appendChild(el("p", null, "Nothing is lost. Try these in order:"));
      var ol = el("ol");
      ["Is this device on your private network (Tailscale)? A machine that is only reachable there looks down from outside it.",
       "A machine behind a sign-in page (Cloudflare Access) looks down here, because this check sends no cookies. List its private-network address instead (./securax phones prints it).",
       "On your laptop: ./securax up --safe. On the server: ./securax why says what stopped.",
       "The Life OS and Vantage below work with every machine off."].forEach(function (t) { ol.appendChild(el("li", null, t)); });
      box.appendChild(ol);
      var again = el("button", "btn", "Check again"); again.type = "button"; again.addEventListener("click", checkAll);
      box.appendChild(again);
    }
    if (checkedAt) box.appendChild(el("p", "mut", "Checked " + checkedAt.toLocaleTimeString([], { timeStyle: "short" })));
  }

  function listCard() {
    var ul = $("list"); ul.textContent = "";
    $("count").textContent = nodes.length ? "(" + nodes.length + ")" : "";
    nodes.forEach(function (n, i) {
      var s = state[n.url], li = el("li", "node");
      li.appendChild(el("span", "dot " + (s ? (s.up ? "up" : "down") : "checking")));
      li.appendChild(el("strong", null, n.name));
      li.appendChild(el("span", "state", s ? (s.up ? "up, " + s.ms + " ms" : "not answering" + (seen[n.url] ? " (last seen " + when(seen[n.url]) + ")" : "")) : "checking"));
      li.appendChild(el("span", "url", n.url));
      var ctl = el("div", "ctl"), sel = el("select"); sel.setAttribute("aria-label", "Role of " + n.name);
      [["primary", "Primary"], ["standby", "Standby"]].forEach(function (o) { var op = el("option", null, o[1]); op.value = o[0]; if (n.role === o[0]) op.selected = true; sel.appendChild(op); });
      sel.addEventListener("change", function () { nodes[i].role = sel.value === "standby" ? "standby" : "primary"; save(); render(); });
      var rm = el("button", "btn quiet", "Remove"); rm.type = "button"; rm.setAttribute("aria-label", "Remove " + n.name);
      rm.addEventListener("click", function () { nodes.splice(i, 1); save(); render(); });
      ctl.appendChild(sel); ctl.appendChild(rm); li.appendChild(ctl); ul.appendChild(li);
    });
  }

  function render() { statusCard(); listCard(); }

  $("add").addEventListener("submit", function (e) {
    e.preventDefault();
    var msg = $("msg"), v = L.validateNode({ name: $("f-name").value, url: $("f-url").value, role: $("f-role").value });
    if (!v) { msg.hidden = false; msg.textContent = "Use the https address where you open the Command Center on that machine. Plain http works only for this device."; return; }
    if (nodes.some(function (n) { return n.url === v.url; })) { msg.hidden = false; msg.textContent = "That machine is already in the list."; return; }
    if (nodes.length >= L.MAX_NODES) { msg.hidden = false; msg.textContent = "That is the most machines this page can hold (" + L.MAX_NODES + ")."; return; }
    msg.hidden = true; nodes.push(v); save(); $("add").reset(); render(); checkAll();
  });

  $("share").addEventListener("click", function () {
    if (!nodes.length) return;
    var link = location.origin + location.pathname + "#" + L.encodeSetup(nodes), box = $("share-box");
    box.value = link; box.hidden = false; box.focus(); box.select();
    try { navigator.clipboard.writeText(link); } catch (e) { /* the box is selected: copy it by hand */ }
  });

  // A setup link never changes anything by itself: it shows what it wants to add and waits for a yes.
  var incoming = L.parseSetup(location.hash);
  function clearHash() { try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* ignore */ } }
  if (incoming) {
    var ul = $("import-list");
    incoming.forEach(function (n) { var li = el("li"); li.appendChild(el("strong", null, n.name + " ")); li.appendChild(el("code", null, n.url)); li.appendChild(el("span", "mut", " (" + n.role + ")")); ul.appendChild(li); });
    $("import").hidden = false;
    $("import-yes").addEventListener("click", function () { nodes = L.sanitizeList(nodes.concat(incoming)); save(); $("import").hidden = true; clearHash(); render(); checkAll(); });
    $("import-no").addEventListener("click", function () { $("import").hidden = true; clearHash(); });
  }

  render();
  checkAll();
  setInterval(function () { if (!document.hidden && !pending) checkAll(); }, EVERY_MS);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) checkAll(); });
  window.addEventListener("online", checkAll);
  window.addEventListener("offline", render);

  // The page itself keeps working with the site host down: this device keeps its own copy (the same pattern as the Life OS).
  if ("serviceWorker" in navigator && (location.protocol === "https:" || /^(localhost|127\.0\.0\.1)$/.test(location.hostname))) {
    fetch("build.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; })
      .then(function (b) { return navigator.serviceWorker.register("sw.js?b=" + encodeURIComponent((b && b.commit) || "dev")); }).catch(function () { /* optional */ });
  }
})();
