/* SecuRAX shared sea (reuse-first; natures-design, signature-perfect; owner 2026-11-24: "breathe with the ocean").
   One engine behind the box-breathing pacer: a live sea whose long swell rises with the in-breath, holds, falls with the
   out-breath and holds, so the person breathes with the water. SXWorld lists it ("sea": calm and the breath).
   - Physics: a sum of 40 Gerstner (trochoidal) waves. Amplitudes come from the Pierson-Moskowitz spectrum for a gentle
     breeze (U19.5 = 4.5 m/s: Hs = 0.21 U^2/g = 0.43 m, peak period 3.3 s), each a_i = sqrt(2 S(w_i) dw_i) on a log grid
     from 0.65 to 16 times the peak frequency, directions spread about the wind. Deep-water dispersion w^2 = g k, so long
     waves travel faster. Crest sharpness (choppiness) 1.3: whitecaps on well under 1% of the surface, as a gentle breeze makes. One extra swell, period 16 s (lambda = 400 m, c = 25 m/s, 1.6 m crest to trough, a low swell),
     carries the breath: its phase is eased through the 4-4-4-4 box, so at the viewer it rises, holds, falls and holds,
     and on average it still travels at its true speed.
   - Camera: eye 1.7 m above mean sea level, 50 degree vertical field, pitched 6.4 degrees down, so the horizon sits
     at 38% of the card and the near water is about 3 m away.
   - Optics: water n = 1.333, Schlick Fresnel with F0 = 0.020 (dark and transmissive looking down, mirror-bright at grazing
     angles); the sky is reflected (from SXSky.state() when the live sky offers it, else a calm dusk in light and a
     moonlit blue hour in dark); a Beckmann sun or moon glitter path whose roughness is the Cox-Munk slope variance the waves
     do not resolve (it grows with distance as waves fade under a pixel); subsurface glow through the backs of high waves; foam only where the Jacobian of the Gerstner map falls
     under 0.45, soft and fading; aerial perspective toward the horizon; ACES tone map, then sRGB.
   - Cost: ONE WebGL context (released on stop), 30 frames a second, only while the pacer is open, on screen and the
     page visible. Reduced motion: a still sea, only the words and a small level line move. jsdom: no canvas, no timer,
     the SVG pacer stays. An automated browser: one still frame. No WebGL: a 2D canvas sea; no canvas: the SVG.
   - Sound (off by default, one tap): WebAudio filtered noise, louder and brighter as the swell rises. No files, no network.
   Use: SXSea.mount(element) -> { stop(), mode }. The element holds .sx-sea-word, .sx-sea-n, .sx-sea-level, .sx-sea-snd. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXSea) return;
  var G = 9.81, TAU = Math.PI * 2, N = 40, WIND = 4.5, LAMBDA = 1.3, BREATH = 16, SWELL_A = 0.8, EYE = 1.7;
  var WORDS = ["Breathe in", "Hold", "Breathe out", "Hold"];

  /* ---- physics (pure: the tests drive it directly) ---- */
  function rng(seed) { var s = seed >>> 0 || 1; return function () { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
  function omegaOf(T) { return TAU / T; }
  function kOf(w) { return w * w / G; }                       // deep water: w^2 = g k
  function phaseSpeed(T) { var w = omegaOf(T); return w / kOf(w); }   // = g T / 2 pi
  // Pierson-Moskowitz: S(w) = alpha g^2 w^-5 exp(-beta (w0/w)^4), w0 = g / U19.5
  function pm(w, U) { var w0 = G / U; return 0.0081 * G * G * Math.pow(w, -5) * Math.exp(-0.74 * Math.pow(w0 / w, 4)); }
  function hsPM(U) { return 0.21 * U * U / G; }
  function peak(U) { return (G / U) * Math.pow(4 * 0.74 / 5, 0.25); }
  function spectrum(U, n, seed) {
    U = U || WIND; n = n || N;
    var r = rng(seed || 20261124), wp = peak(U), lo = Math.log(0.65 * wp), hi = Math.log(16 * wp), out = [], i, base = Math.PI + 0.26;
    for (i = 0; i < n; i++) {
      var l = lo + (hi - lo) * (i + 0.5) / n, w = Math.exp(l), dw = Math.exp(lo + (hi - lo) * (i + 1) / n) - Math.exp(lo + (hi - lo) * i / n);
      var spread = 0.35 + 0.35 * i / n, g = (r() + r() + r() - 1.5) * 2 * spread, th = base + g;
      var k = kOf(w);
      out.push({ w: w, k: k, a: Math.sqrt(2 * pm(w, U) * dw), dx: Math.cos(th), dz: Math.sin(th), p0: r() * TAU });
    }
    return out;
  }
  function hsOf(W) { var m0 = 0, i; for (i = 0; i < W.length; i++) m0 += W[i].a * W[i].a / 2; return 4 * Math.sqrt(m0); }
  function ease(u) { u = Math.max(0, Math.min(1, u)); return 0.5 - 0.5 * Math.cos(Math.PI * u); }
  // The breath at time t (s): which phase, the word, the count (4..1), the level b (0 low .. 1 high).
  function breath(t) {
    var c = ((t % BREATH) + BREATH) % BREATH, ph = Math.floor(c / 4), u = (c - ph * 4) / 4;
    var b = ph === 0 ? ease(u) : ph === 1 ? 1 : ph === 2 ? 1 - ease(u) : 0;
    return { phase: ph, word: WORDS[ph], count: 4 - Math.floor(c - ph * 4), b: b };
  }
  // The swell's phase: eased through the box, 2 pi a breath, so its mean speed is the true g T / 2 pi.
  function swellPhase(t) {
    var n = Math.floor(t / BREATH), c = t - n * BREATH, ph = Math.floor(c / 4), u = (c - ph * 4) / 4;
    var f = ph === 0 ? ease(u) : ph === 1 ? 1 : ph === 2 ? 1 + ease(u) : 2;
    return (n * 2 + f) * Math.PI;
  }
  var SWELL_K = kOf(omegaOf(BREATH));
  // Swell height at a point (x, z metres; the viewer at 0, 0; the swell comes toward the viewer from +z).
  function swellAt(x, z, t) { return -SWELL_A * Math.cos(-SWELL_K * z - swellPhase(t)); }
  // The Jacobian of the Gerstner map at (x, z): under 1 the surface bunches; near 0 a crest is about to break (foam).
  function jacobian(W, x, z, t) {
    var jxx = 0, jzz = 0, jxz = 0, i;
    for (i = 0; i < W.length; i++) {
      var w = W[i], s = Math.sin(w.k * (w.dx * x + w.dz * z) - w.w * t - w.p0), q = LAMBDA * w.k * w.a * s;
      jxx += q * w.dx * w.dx; jzz += q * w.dz * w.dz; jxz += q * w.dx * w.dz;
    }
    return (1 - jxx) * (1 - jzz) - jxz * jxz;
  }
  // Cox-Munk (1954) mean square slope of the real sea, 0.003 + 0.00512 U; what the 40 waves do not resolve becomes the
  // Beckmann roughness of the glitter (m^2 = the unresolved slope variance).
  function coxMunk(U) { return 0.003 + 0.00512 * U; }
  function slopeVar(W) { var v = 0, i; for (i = 0; i < W.length; i++) v += W[i].k * W[i].a * W[i].k * W[i].a / 2; return v; }
  function unresolved(W, U) { return Math.max(0.001, coxMunk(U) - slopeVar(W)); }
  function heightAt(W, x, z, t) { var h = 0, i; for (i = 0; i < W.length; i++) { var w = W[i]; h += w.a * Math.sin(w.k * (w.dx * x + w.dz * z) - w.w * t - w.p0); } return h + swellAt(x, z, t); }

  /* ---- the look ---- */
  // Linear-light presets. Light theme: dusk, the sun 3 degrees up. Dark: the blue hour, the moon 10 degrees up.
  var LOOK = {
    dusk: { zen: [0.010, 0.022, 0.085], hor: [1.0, 0.36, 0.11], glow: [1.0, 0.36, 0.08], sun: [1.0, 0.42, 0.12], elev: 3, az: 18,
      disk: 5, rad: 0.0047, spec: 0.14, amb: 0.9, deep: [0.0035, 0.016, 0.028], sss: [0.02, 0.12, 0.10], foam: [0.55, 0.45, 0.42], exp: 0.9, fog: 6000 },
    night: { zen: [0.0020, 0.0040, 0.014], hor: [0.026, 0.036, 0.070], glow: [0.012, 0.014, 0.020], sun: [0.85, 0.90, 1.0], elev: 10, az: 24,
      disk: 10, rad: 0.0045, spec: 0.012, amb: 0.14, deep: [0.0012, 0.004, 0.009], sss: [0.004, 0.018, 0.020], foam: [0.07, 0.08, 0.10], exp: 1.8, fog: 6000 }
  };
  function lookNow() {
    var dark = document.documentElement.getAttribute("data-theme") !== "light", L = dark ? LOOK.night : LOOK.dusk;
    try {   // the live sky may lend its colours and its sun or moon (duck-typed: SXSky.state() -> {zen, hor, elev, az})
      var s = window.SXSky && typeof window.SXSky.state === "function" && window.SXSky.state();
      if (s) { var o = {}, k; for (k in L) o[k] = L[k]; for (k in s) if (s[k] != null) o[k] = s[k]; L = o; }
    } catch (e) {}
    return L;
  }

  var VS = "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
  var FS = [
    "precision highp float;",
    "uniform vec2 uRes;uniform vec4 uW[" + N + "];uniform float uM2,uLam,uEye,uPx,uSK,uSA,uSP,uExp,uFogL,uDisk,uDiskE,uSpec,uAmb,uRad;",
    "uniform vec3 uL,uZen,uHor,uGlow,uSun,uDeep,uSss,uFoam;uniform mat3 uCam;",
    "vec3 sky(vec3 d,float disk){float e=max(d.y,0.);vec3 c=uZen+(uHor-uZen)*exp(-e*9.);float mu=max(dot(d,uL),0.);",
    " c+=uGlow*(pow(mu,20.)*.35+pow(mu,300.)*2.2)*(1.-.6*e);c+=disk*uSun*uDiskE*smoothstep(cos(uRad*1.25),cos(uRad*.8),mu);return c;}",
    "float swell(vec2 p){return -uSA*cos(-uSK*p.y-uSP);}",
    "void sumW(vec2 p,vec2 fp,out float h,out vec2 d){h=0.;d=vec2(0.);",
    " for(int i=0;i<" + N + ";i++){vec4 w=uW[i];float k=length(w.xy);float f=1.-smoothstep(1.,3.,length(w.xy*fp));if(f<=0.)continue;",
    "  float th=dot(w.xy,p)-w.w;float a=w.z*f;h+=a*sin(th);d+=uLam*a*(w.xy/k)*cos(th);}}",
    "void detail(vec2 p,vec2 fp,out vec3 n,out float J,out float hr,out float rough){float sx=0.,sz=0.,sy=0.,jxx=0.,jzz=0.,jxz=0.;hr=0.;rough=0.;",
    " for(int i=0;i<" + N + ";i++){vec4 w=uW[i];float k=length(w.xy);float f=1.-smoothstep(1.,3.,length(w.xy*fp));float ka=k*w.z;rough+=ka*ka*.5*(1.-f);if(f<=0.)continue;",
    "  vec2 D=w.xy/k;float th=dot(w.xy,p)-w.w;float s=sin(th),c=cos(th);ka*=f;sx+=D.x*ka*c;sz+=D.y*ka*c;float q=uLam*ka*s;sy+=q;",
    "  jxx+=q*D.x*D.x;jzz+=q*D.y*D.y;jxz+=q*D.x*D.y;hr+=w.z*f*s;}",
    " float sk=uSK*uSA*sin(-uSK*p.y-uSP);n=normalize(vec3(-sx,1.-sy,-sz+sk));J=(1.-jxx)*(1.-jzz)-jxz*jxz;}",
    "vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}",
    "vec3 srgb(vec3 c){return mix(c*12.92,1.055*pow(c,vec3(1./2.4))-.055,step(.0031308,c));}",
    "void main(){vec2 q=(gl_FragCoord.xy-.5*uRes)/uRes.y;vec3 rd=normalize(uCam*vec3(q*2.*tan(radians(25.)),1.));",
    " vec3 ro=vec3(0.,uEye,0.);vec3 col=sky(rd,1.);",
    " if(rd.y<0.){float t=(ro.y-swell(vec2(0.)))/(-rd.y);vec3 P=ro+rd*t;vec2 x0=P.xz;float h;vec2 d;vec2 fp;",
    "  for(int it=0;it<3;it++){fp=t*uPx*vec2(1.,1./max(-rd.y,.02));sumW(x0,fp,h,d);x0=P.xz-d;h+=swell(P.xz);t=clamp((ro.y-h)/(-rd.y),.1,6000.);P=ro+rd*t;}",
    "  fp=t*uPx*vec2(1.,1./max(-rd.y,.02));vec3 n;float J,hr,ro2;detail(x0,fp,n,J,hr,ro2);",
    "  vec3 V=-rd;float cv=max(dot(n,V),0.);float F=.02+.98*pow(1.-cv,5.);",
    "  vec3 r=reflect(rd,n);r.y=abs(r.y);vec3 refl=sky(r,0.);",
    "  vec2 vf=normalize(rd.xz),lf=normalize(uL.xz);float back=pow(max(dot(vf,lf),0.),3.);",
    "  float thick=clamp(hr/.22+.15,0.,1.);vec3 body=uDeep*uAmb+uSss*thick*back*(.25+5.*(1.-n.y));",
    "  vec3 c=(1.-F)*body+F*refl;",
    "  vec3 H=normalize(uL+V);float nh=max(dot(n,H),1e-3);float m2=uM2+ro2;float n2=nh*nh;",
    "  float Dm=exp(-(1.-n2)/(n2*m2))/(3.14159*m2*n2*n2);float Fh=.02+.98*pow(1.-max(dot(H,V),0.),5.);",
    "  c+=uSun*uSpec*Fh*Dm/(4.*max(cv,.12))*smoothstep(-.02,.02,uL.y);",
    "  float fog=1.-exp(-t/uFogL);float fo=(1.-smoothstep(.08,.45,J))*(1.-fog)*(.55+.45*clamp(hr/.2,0.,1.));c=mix(c,uFoam*(.6+.4*uAmb),fo*.8);",
    "  vec3 hz=sky(normalize(vec3(rd.x,.002,rd.z)),0.);c=mix(c,hz*.92,fog);",
    "  col=mix(c,col,smoothstep(-uPx*1.5,0.,rd.y));}",
    " gl_FragColor=vec4(srgb(aces(col*uExp)),1.);}"
  ].join("\n");

  function calm() { try { return !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches); } catch (e) { return false; } }
  function isJsdom() { return /jsdom/i.test(navigator.userAgent || ""); }

  var cur = null, stats = { mode: "none", frames: 0, frameMs: 0, fps: 30 };

  function mount(el, opts) {
    opts = opts || {};
    if (cur && cur.el === el && cur.alive) return cur.handle;
    if (cur) cur.handle.stop();
    var doc = el.ownerDocument, W = spectrum(opts.wind || WIND), M2 = unresolved(W, opts.wind || WIND), word = el.querySelector(".sx-sea-word"), num = el.querySelector(".sx-sea-n"),
      lvl = el.querySelector(".sx-sea-level"), snd = el.querySelector(".sx-sea-snd");
    var st = { el: el, alive: true, raf: 0, iv: 0, io: null, vis: true, onScreen: true, gl: null, cx: null, cv: null, U: {}, last: 0, t0: 0, probe: 0, probeSum: 0, audio: null, lastWord: "" };
    var handle = { stop: stop, mode: "svg", time: function () { return now(); } };
    st.handle = handle; cur = st;
    var still = !!navigator.webdriver || isJsdom(), quiet = calm();
    function now() { return typeof api.clock === "function" ? api.clock() : (performance.now() - st.t0) / 1000; }

    function sayWords(t) {
      var b = breath(t);
      if (word && b.word !== st.lastWord) { word.textContent = b.word; st.lastWord = b.word; }
      if (num && num.textContent !== String(b.count)) num.textContent = b.count;
      if (lvl) lvl.style.transform = "translateY(" + (-b.b * 38).toFixed(1) + "px)";
      if (st.audio) st.audio.set(b.b);
      return b;
    }
    if (isJsdom()) { sayWords(0); stats.mode = "svg"; return handle; }   // no canvas in a test DOM: the SVG pacer stays, no timer

    var cv = doc.createElement("canvas"); cv.className = "sx-sea-cv"; cv.setAttribute("aria-hidden", "true");
    el.insertBefore(cv, el.firstChild); st.cv = cv;
    initGL();
    if (!st.gl) { st.cx = cv.getContext && cv.getContext("2d"); handle.mode = st.cx ? "2d" : "svg"; } else handle.mode = "webgl";
    if (handle.mode === "svg") { cv.parentNode.removeChild(cv); st.cv = null; }
    else el.classList.add("sx-sea-on");
    stats.mode = handle.mode;

    function size() {
      var r = el.getBoundingClientRect(), d = Math.min(st.gl ? 1.5 : 1, window.devicePixelRatio || 1);
      var w = Math.max(2, Math.round(r.width * d)), h = Math.max(2, Math.round(r.height * d));
      if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
      return [w, h];
    }
    function initGL() {
      try {
        var gl = cv.getContext("webgl", { alpha: false, antialias: false, preserveDrawingBuffer: !!navigator.webdriver, powerPreference: "low-power" });
        if (!gl) return;
        var hp = gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
        if (!hp || hp.precision < 16 || gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS) < N + 24) return;
        var sh = function (t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
        var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
        if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr));
        gl.useProgram(pr);
        var bf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
        var a = gl.getAttribLocation(pr, "a"); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
        "uRes uM2 uW uLam uEye uPx uSK uSA uSP uExp uFogL uDisk uDiskE uSpec uAmb uRad uL uZen uHor uGlow uSun uDeep uSss uFoam uCam".split(" ").forEach(function (n) { st.U[n] = gl.getUniformLocation(pr, n); });
        cv.addEventListener("webglcontextlost", function (e) { e.preventDefault(); st.gl = null; st.cx = cv.getContext("2d"); });
        st.gl = gl;
      } catch (e) { st.gl = null; if (window.console && console.warn) console.warn("SXSea: the sea falls back to 2D", e && e.message); }
    }
    var PITCH = 6.4 * Math.PI / 180, cp = Math.cos(PITCH), sp = Math.sin(PITCH);
    var CAM = new Float32Array([1, 0, 0, 0, cp, -sp, 0, sp, cp]);   // columns: right, up, forward (looking at +z, tipped down)
    function dirOf(L) { var e = L.elev * Math.PI / 180, z = L.az * Math.PI / 180; return [Math.cos(e) * Math.sin(z), Math.sin(e), Math.cos(e) * Math.cos(z)]; }
    function drawGL(t) {
      var gl = st.gl, U = st.U, s = size(), L = lookNow(), buf = new Float32Array(N * 4), i;
      gl.viewport(0, 0, s[0], s[1]);
      for (i = 0; i < N; i++) { var w = W[i]; buf[i * 4] = w.k * w.dx; buf[i * 4 + 1] = w.k * w.dz; buf[i * 4 + 2] = w.a; buf[i * 4 + 3] = (w.w * t + w.p0) % TAU; }
      gl.uniform4fv(U.uW, buf); gl.uniform2f(U.uRes, s[0], s[1]);
      gl.uniform1f(U.uM2, M2); gl.uniform1f(U.uLam, LAMBDA); gl.uniform1f(U.uEye, EYE); gl.uniform1f(U.uPx, 2 * Math.tan(25 * Math.PI / 180) / s[1]);
      gl.uniform1f(U.uSK, SWELL_K); gl.uniform1f(U.uSA, SWELL_A); gl.uniform1f(U.uSP, swellPhase(t) % (TAU * 64));
      gl.uniform1f(U.uExp, L.exp); gl.uniform1f(U.uFogL, L.fog); gl.uniform1f(U.uDiskE, L.disk); gl.uniform1f(U.uSpec, L.spec); gl.uniform1f(U.uAmb, L.amb); gl.uniform1f(U.uRad, L.rad);
      gl.uniform3fv(U.uL, dirOf(L)); gl.uniform3fv(U.uZen, L.zen); gl.uniform3fv(U.uHor, L.hor); gl.uniform3fv(U.uGlow, L.glow); gl.uniform3fv(U.uSun, L.sun);
      gl.uniform3fv(U.uDeep, L.deep); gl.uniform3fv(U.uSss, L.sss); gl.uniform3fv(U.uFoam, L.foam); gl.uniformMatrix3fv(U.uCam, false, CAM);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    // The 2D fallback: the same sky colours, a sea gradient, a glitter path, the near water lifted by the same swell.
    function hex(c, e) { return "rgb(" + c.map(function (v) { v = v * e; v = v / (1 + v); return Math.round(255 * Math.pow(v, 1 / 2.2)); }).join(",") + ")"; }
    function draw2D(t) {
      var s = size(), x = st.cx, w = s[0], h = s[1], L = lookNow(), hy = h * 0.38, lift = swellAt(0, 0, t) / SWELL_A, i;
      var g = x.createLinearGradient(0, 0, 0, hy); g.addColorStop(0, hex(L.zen, L.exp * 2)); g.addColorStop(1, hex(L.hor, L.exp)); x.fillStyle = g; x.fillRect(0, 0, w, hy + 1);
      g = x.createLinearGradient(0, hy, 0, h); g.addColorStop(0, hex(L.hor, L.exp * 0.8)); g.addColorStop(0.25, hex(L.zen, L.exp * 1.2)); g.addColorStop(1, hex(L.deep, L.exp * 12)); x.fillStyle = g; x.fillRect(0, hy, w, h - hy);
      var sx = w * (0.5 + 0.5 * Math.tan(L.az * Math.PI / 180) / (1.5 * Math.tan(25 * Math.PI / 180)));
      x.fillStyle = hex(L.sun, L.exp * 1.5);
      for (i = 0; i < 70; i++) {
        var f = i / 70, y = hy + 2 + f * f * (h - hy) * (1 + 0.08 * lift), half = 2 + f * w * 0.07, j = Math.sin(i * 12.9898 + t * (1.3 + (i % 5) * 0.4));
        x.globalAlpha = Math.max(0, 0.5 * (1 - f) * (0.5 + 0.5 * j)); x.fillRect(sx - half * (0.6 + 0.4 * j), y, half * 2 * (0.4 + 0.6 * Math.abs(j)), 1 + f * 2);
      }
      x.globalAlpha = 1;
    }
    function frame(t) {
      var p0 = performance.now();
      if (st.gl) { drawGL(t); if (st.probe < 20) { var px = new Uint8Array(4); st.gl.readPixels(0, 0, 1, 1, st.gl.RGBA, st.gl.UNSIGNED_BYTE, px); } }
      else if (st.cx) draw2D(t);
      if (st.probe < 20) { st.probe++; st.probeSum += performance.now() - p0; stats.frameMs = +(st.probeSum / st.probe).toFixed(2); }
      stats.frames++;
      sayWords(t);
    }
    function running() { return st.alive && st.vis && st.onScreen; }
    function loop(ts) {
      st.raf = 0;
      if (!el.isConnected) { stop(); return; }
      if (!running()) return;
      st.raf = requestAnimationFrame(loop);
      if (ts - st.last < 1000 / 30 - 2) return;          // 30 frames a second
      st.last = ts; frame(now());
    }
    function kick() {
      if (still || !running()) return;
      if (quiet) { if (!st.iv) st.iv = setInterval(function () { if (!el.isConnected) return stop(); if (running()) sayWords(now()); }, 250); return; }
      if (!st.raf) st.raf = requestAnimationFrame(loop);
    }
    function onVis() { st.vis = doc.visibilityState !== "hidden"; kick(); }
    function stop() {
      if (!st.alive) return; st.alive = false;
      if (st.raf) cancelAnimationFrame(st.raf); st.raf = 0; if (st.iv) clearInterval(st.iv); st.iv = 0;
      if (st.io) st.io.disconnect(); doc.removeEventListener("visibilitychange", onVis);
      if (st.audio) st.audio.off(); st.audio = null;
      if (snd) { snd.setAttribute("aria-pressed", "false"); snd.onclick = null; }
      if (st.gl) { var lc = st.gl.getExtension("WEBGL_lose_context"); if (lc) lc.loseContext(); st.gl = null; }
      if (cur === st) cur = null;
    }
    st.t0 = performance.now();
    if (handle.mode !== "svg") frame(still || quiet ? 2 : 0);   // a still frame: the swell half-way up
    sayWords(still ? 0 : now());
    if (snd && handle.mode !== "svg") {
      snd.hidden = false;
      snd.onclick = function () {
        if (st.audio) { st.audio.off(); st.audio = null; snd.setAttribute("aria-pressed", "false"); return; }
        st.audio = sound(); if (st.audio) { snd.setAttribute("aria-pressed", "true"); st.audio.set(breath(now()).b); }
      };
    }
    if (!still) {
      doc.addEventListener("visibilitychange", onVis);
      if (window.IntersectionObserver) { st.io = new IntersectionObserver(function (es) { st.onScreen = es[es.length - 1].isIntersecting; kick(); }); st.io.observe(el); }
      kick();
    }
    return handle;
  }

  // The sea's sound: brown-ish noise through a low-pass that opens, and a gain that swells, with the breath. One tap off.
  function sound() {
    try {
      var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
      var ac = new AC(), len = ac.sampleRate * 4, buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0), v = 0, i;
      for (i = 0; i < len; i++) { v = (v + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = v * 3.5; }
      var src = ac.createBufferSource(); src.buffer = buf; src.loop = true;
      var lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 300; lp.Q.value = 0.4;
      var gn = ac.createGain(); gn.gain.value = 0;
      src.connect(lp); lp.connect(gn); gn.connect(ac.destination); src.start();
      return {
        set: function (b) { var t = ac.currentTime; lp.frequency.setTargetAtTime(260 + 900 * b, t, 0.4); gn.gain.setTargetAtTime(0.05 + 0.16 * b, t, 0.4); },
        off: function () { try { gn.gain.setTargetAtTime(0, ac.currentTime, 0.2); setTimeout(function () { try { src.stop(); ac.close(); } catch (e) {} }, 600); } catch (e) {} }
      };
    } catch (e) { return null; }
  }

  var api = window.SXSea = { clock: null, coxMunk: coxMunk, slopeVar: slopeVar, mount: mount, stats: stats, G: G, BREATH: BREATH, WIND: WIND, EYE: EYE, SWELL_A: SWELL_A, SWELL_K: SWELL_K, LAMBDA: LAMBDA,
    pm: pm, hsPM: hsPM, peak: peak, spectrum: spectrum, hsOf: hsOf, phaseSpeed: phaseSpeed, kOf: kOf, breath: breath,
    swellPhase: swellPhase, swellAt: swellAt, heightAt: heightAt, jacobian: jacobian, current: function () { return cur && cur.handle; } };
})();
