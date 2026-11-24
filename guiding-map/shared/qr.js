/* SXQR: a small QR code encoder, built into every SecuRAX app (reuse-first). No dependency and no network: a pairing code is
   drawn on the device that made it, never sent to a QR web service. Byte mode, error correction M, versions 1 to 10 (up to
   213 bytes), the mask chosen by the standard's penalty rules (ISO/IEC 18004). Used by "Move to another phone" (threat model
   move-phone); a later pairing scan reuses it. SXQR.matrix(text) gives rows of true (dark) and false; SXQR.svg(text, label)
   gives a crisp, accessible SVG with the quiet zone. */
(function (root) {
  "use strict";
  var ECC_M = [0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26], BLOCKS_M = [0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5];
  function gmul(x, y) { var z = 0; for (var i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11d); z ^= ((y >>> i) & 1) * x; } return z & 0xff; }
  function rsDivisor(deg) {
    var r = []; for (var i = 0; i < deg - 1; i++) r.push(0); r.push(1);
    var root = 1;
    for (var k = 0; k < deg; k++) {
      for (var j = 0; j < r.length; j++) { r[j] = gmul(r[j], root); if (j + 1 < r.length) r[j] ^= r[j + 1]; }
      root = gmul(root, 2);
    }
    return r;
  }
  function rsRemainder(data, div) {
    var r = div.map(function () { return 0; });
    data.forEach(function (b) { var f = b ^ r.shift(); r.push(0); div.forEach(function (c, i) { r[i] ^= gmul(c, f); }); });
    return r;
  }
  function rawModules(v) {
    var n = (16 * v + 128) * v + 64;
    if (v >= 2) { var a = Math.floor(v / 7) + 2; n -= (25 * a - 10) * a - 55; if (v >= 7) n -= 36; }
    return n;
  }
  function dataCodewords(v) { return Math.floor(rawModules(v) / 8) - ECC_M[v] * BLOCKS_M[v]; }
  function alignPos(v) {
    if (v === 1) return [];
    var n = Math.floor(v / 7) + 2, size = v * 4 + 17, step = Math.ceil((v * 4 + 4) / (n * 2 - 2)) * 2, out = [6];
    for (var p = size - 7; out.length < n; p -= step) out.splice(1, 0, p);
    return out;
  }
  function utf8(s) { var u = unescape(encodeURIComponent(String(s))), b = []; for (var i = 0; i < u.length; i++) b.push(u.charCodeAt(i)); return b; }

  function matrix(text) {
    var bytes = utf8(text), v = 1;
    while (v <= 10 && 4 + (v < 10 ? 8 : 16) + bytes.length * 8 > dataCodewords(v) * 8) v++;
    if (v > 10) throw new Error("too long for a QR code here");
    var size = v * 4 + 17, cap = dataCodewords(v) * 8, bits = [];
    function put(val, len) { for (var i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1); }
    put(4, 4); put(bytes.length, v < 10 ? 8 : 16); bytes.forEach(function (b) { put(b, 8); });
    put(0, Math.min(4, cap - bits.length)); while (bits.length % 8) bits.push(0);
    for (var pad = 0xec; bits.length < cap; pad ^= 0xec ^ 0x11) put(pad, 8);
    var data = []; for (var i = 0; i < bits.length; i += 8) { var x = 0; for (var j = 0; j < 8; j++) x = (x << 1) | bits[i + j]; data.push(x); }
    // error correction, split into blocks and interleaved
    var nb = BLOCKS_M[v], el = ECC_M[v], raw = Math.floor(rawModules(v) / 8), nShort = nb - raw % nb, shortLen = Math.floor(raw / nb);
    var div = rsDivisor(el), blocks = [], k = 0;
    for (var b = 0; b < nb; b++) {
      var d = data.slice(k, k + shortLen - el + (b < nShort ? 0 : 1)); k += d.length;
      var e = rsRemainder(d, div); if (b < nShort) d.push(0); blocks.push(d.concat(e));
    }
    var cw = [];
    for (var c = 0; c < blocks[0].length; c++) for (var q = 0; q < nb; q++) if (c !== shortLen - el || q >= nShort) cw.push(blocks[q][c]);
    // function patterns
    var M = [], F = [];
    for (var y = 0; y < size; y++) { M.push([]); F.push([]); for (var x2 = 0; x2 < size; x2++) { M[y].push(false); F[y].push(false); } }
    function set(x, y, dark) { M[y][x] = !!dark; F[y][x] = true; }
    for (var t = 0; t < size; t++) { set(6, t, t % 2 === 0); set(t, 6, t % 2 === 0); }
    [[3, 3], [size - 4, 3], [3, size - 4]].forEach(function (p) {
      for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) {
        var dist = Math.max(Math.abs(dx), Math.abs(dy)), xx = p[0] + dx, yy = p[1] + dy;
        if (xx >= 0 && xx < size && yy >= 0 && yy < size) set(xx, yy, dist !== 2 && dist !== 4);
      }
    });
    var ap = alignPos(v), last = ap.length - 1;
    ap.forEach(function (ay, i) {
      ap.forEach(function (ax, j) {
        if ((i === 0 && j === 0) || (i === 0 && j === last) || (i === last && j === 0)) return;
        for (var dy = -2; dy <= 2; dy++) for (var dx = -2; dx <= 2; dx++) set(ax + dx, ay + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
      });
    });
    function format(mask) {
      var d = (0 << 3) | mask, r = d;                     // error correction M is 00
      for (var i = 0; i < 10; i++) r = (r << 1) ^ ((r >>> 9) * 0x537);
      var f = ((d << 10) | r) ^ 0x5412, g = function (i) { return (f >>> i) & 1; };
      for (var a = 0; a <= 5; a++) set(8, a, g(a));
      set(8, 7, g(6)); set(8, 8, g(7)); set(7, 8, g(8));
      for (var a2 = 9; a2 < 15; a2++) set(14 - a2, 8, g(a2));
      for (var a3 = 0; a3 < 8; a3++) set(size - 1 - a3, 8, g(a3));
      for (var a4 = 8; a4 < 15; a4++) set(8, size - 15 + a4, g(a4));
      set(8, size - 8, 1);
    }
    format(0);
    if (v >= 7) {
      var r7 = v; for (var i7 = 0; i7 < 12; i7++) r7 = (r7 << 1) ^ ((r7 >>> 11) * 0x1f25);
      var vb = (v << 12) | r7;
      for (var i8 = 0; i8 < 18; i8++) { var bit = (vb >>> i8) & 1, aa = size - 11 + i8 % 3, bb = Math.floor(i8 / 3); set(aa, bb, bit); set(bb, aa, bit); }
    }
    // the data, in the zigzag order
    var n = 0;
    for (var right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (var vert = 0; vert < size; vert++) for (var jj = 0; jj < 2; jj++) {
        var xx3 = right - jj, up = ((right + 1) & 2) === 0, yy3 = up ? size - 1 - vert : vert;
        if (!F[yy3][xx3] && n < cw.length * 8) { M[yy3][xx3] = ((cw[n >>> 3] >>> (7 - (n & 7))) & 1) === 1; n++; }
      }
    }
    function flip(mask) {
      for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
        var inv;
        switch (mask) {
          case 0: inv = (x + y) % 2 === 0; break;
          case 1: inv = y % 2 === 0; break;
          case 2: inv = x % 3 === 0; break;
          case 3: inv = (x + y) % 3 === 0; break;
          case 4: inv = (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; break;
          case 5: inv = (x * y) % 2 + (x * y) % 3 === 0; break;
          case 6: inv = ((x * y) % 2 + (x * y) % 3) % 2 === 0; break;
          default: inv = ((x + y) % 2 + (x * y) % 3) % 2 === 0;
        }
        if (inv && !F[y][x]) M[y][x] = !M[y][x];
      }
    }
    function penalty() {
      var p = 0, dark = 0, y, x;
      function lines(get) {
        for (var a = 0; a < size; a++) {
          var run = 1, s = "";
          for (var b = 0; b < size; b++) {
            var m = get(a, b); s += m ? "1" : "0";
            if (b > 0) { if (m === get(a, b - 1)) { run++; if (run === 5) p += 3; else if (run > 5) p++; } else run = 1; }
          }
          s = "0000" + s + "0000";                        // a finder-like run (1:1:3:1:1 beside four light modules)
          var pat = /10111010000|00001011101/g, mt; while ((mt = pat.exec(s))) { p += 40; pat.lastIndex = mt.index + 1; }
        }
      }
      lines(function (a, b) { return M[a][b]; });
      lines(function (a, b) { return M[b][a]; });
      for (y = 0; y < size - 1; y++) for (x = 0; x < size - 1; x++) { var c = M[y][x]; if (c === M[y][x + 1] && c === M[y + 1][x] && c === M[y + 1][x + 1]) p += 3; }
      for (y = 0; y < size; y++) for (x = 0; x < size; x++) if (M[y][x]) dark++;
      p += Math.floor(Math.abs(dark * 20 - size * size * 10) / (size * size)) * 10;
      return p;
    }
    var best = 0, bestP = Infinity;
    for (var mk = 0; mk < 8; mk++) { flip(mk); format(mk); var pp = penalty(); if (pp < bestP) { bestP = pp; best = mk; } flip(mk); }
    flip(best); format(best);
    return M;
  }

  // An SVG with a 4-module quiet zone, dark on a white card in either theme (a code must keep its contrast to scan).
  function svg(text, label) {
    var m = matrix(text), n = m.length, q = 4, d = "";
    for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) if (m[y][x]) d += "M" + (x + q) + " " + (y + q) + "h1v1h-1z";
    var w = n + 2 * q, lab = String(label || "QR code").replace(/[<>&"]/g, "");
    return '<svg viewBox="0 0 ' + w + " " + w + '" role="img" aria-label="' + lab + '" shape-rendering="crispEdges" style="display:block;width:100%;height:auto;background:#fff;border-radius:8px">'
      + '<rect width="' + w + '" height="' + w + '" fill="#fff"/><path fill="#000" d="' + d + '"/></svg>';
  }
  root.SXQR = { matrix: matrix, svg: svg };
})(typeof window !== "undefined" ? window : this);
