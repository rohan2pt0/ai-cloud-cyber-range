/* The Command Center door: the decisions, with no page in them, so they can be tested on their own (doc 131).
   Which machines are valid, which one to open, and how a list of machines travels to another device in a link. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DoorLogic = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var MAX_NODES = 8, MAX_NAME = 40;

  // The device you are on is reachable by plain http; any other machine must be https (a page opened over https cannot talk to http).
  function thisDevice(host) { return host === "localhost" || host === "127.0.0.1" || host === "[::1]" || /\.localhost$/.test(host); }

  function cleanName(s) { return String(s == null ? "" : s).replace(/[\u0000-\u001f\u007f<>]/g, "").trim().slice(0, MAX_NAME); }

  // An address is where you open the Command Center on that machine. No sign-in details, no query, no fragment: just a place.
  function cleanUrl(s) {
    var u;
    try { u = new URL(String(s).trim()); } catch (e) { return ""; }
    if (u.username || u.password || !u.hostname) return "";
    if (!(u.protocol === "https:" || (u.protocol === "http:" && thisDevice(u.hostname)))) return "";
    return u.origin + u.pathname.replace(/\/+$/, "") + "/";
  }

  function validateNode(n) {
    if (!n || typeof n !== "object") return null;
    var url = cleanUrl(n.url);
    if (!url) return null;
    return { name: cleanName(n.name) || new URL(url).hostname, url: url, role: n.role === "standby" ? "standby" : "primary" };
  }

  function sanitizeList(list) {
    var out = [], seen = {};
    (Array.isArray(list) ? list : []).forEach(function (n) {
      var v = validateNode(n);
      if (v && !seen[v.url] && out.length < MAX_NODES) { seen[v.url] = 1; out.push(v); }
    });
    return out;
  }

  // state: { <url>: { up: true|false, ms: number } }. Primaries share the work: the fastest one that answers wins (active-active).
  // A standby is used only when no primary answers (active-passive). Equal speed: the one listed first.
  function pickBest(nodes, state) {
    function best(role) {
      var b = null;
      nodes.forEach(function (n) {
        var s = state[n.url];
        if (n.role !== role || !s || !s.up) return;
        if (!b || s.ms < state[b.url].ms) b = n;
      });
      return b;
    }
    var p = best("primary");
    if (p) return { node: p, tier: "primary" };
    var q = best("standby");
    return q ? { node: q, tier: "standby" } : { node: null, tier: null };
  }

  function b64uEncode(str) {
    var bytes = new TextEncoder().encode(str), bin = "";
    for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function b64uDecode(s) {
    s = String(s).replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    var bin = atob(s), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  }

  // The list as a link fragment, so one tap sets up another device. It carries addresses only: no keys, no passwords.
  function encodeSetup(nodes) {
    return "n=" + b64uEncode(JSON.stringify(sanitizeList(nodes).map(function (n) { return { name: n.name, url: n.url, role: n.role }; })));
  }
  // Anything that does not decode to at least one valid machine is ignored; nothing from a link is ever trusted as-is.
  function parseSetup(hash) {
    var m = /^#?n=([A-Za-z0-9_-]{1,4000})$/.exec(String(hash || ""));
    if (!m) return null;
    try { var list = sanitizeList(JSON.parse(b64uDecode(m[1]))); return list.length ? list : null; } catch (e) { return null; }
  }

  return { MAX_NODES: MAX_NODES, cleanUrl: cleanUrl, validateNode: validateNode, sanitizeList: sanitizeList,
           pickBest: pickBest, encodeSetup: encodeSetup, parseSetup: parseSetup };
});
