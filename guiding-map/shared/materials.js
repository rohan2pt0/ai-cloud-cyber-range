/* SecuRAX shared materials (reuse-first, owner 2026-11-14: "no picture pretending to be gold"). A small physically based
   renderer: real materials are not drawn, they are LIT. One studio (a night room, a large soft box, a strip light, a
   horizon line and two small spots) lights every surface on the screen, so every reflection agrees with every other one,
   and the whole studio turns with the phone (shared/touch.js), so reflections move as they would in the hand.

   Optics, from measured data (sources in docs and the PR):
   - metals: Fresnel reflectance F0 from measured complex refractive indices (n, k), linear RGB:
     gold (0.944, 0.776, 0.373), platinum (0.679, 0.642, 0.588), silver (0.962, 0.949, 0.922); Schlick's Fresnel;
     roughness widens and dims the reflected lights (a prefiltered glossy reflection);
   - diamond: a round brilliant in Tolkowsky's proportions (table 53%, crown 34.5°, pavilion 40.75°), 73 facets, ray traced
     with refraction, total internal reflection and Fresnel at every facet, and dispersion (n = 2.410 red, 2.426 green,
     2.444 blue), which is where its fire comes from;
   - enamel: a translucent blue glass layer (Beer-Lambert absorption) with a clear-coat reflection, over engine-turned
     (guilloché) silver, as on the finest watch dials;
   - velvet: the microfacet sheen of Estevez and Kulla (SIGGRAPH 2017) over a crushed pile.
   Output is tone mapped (ACES) and encoded for the screen.

   Use: elements opt in by selector (the AUTO map below) or with data-sx-mat="gold|platinum|seal|velvet". The rendered
   material sits behind the element's own content; the CSS look underneath stays as the fallback (no WebGL, high-precision
   shaders missing, a lost context). SXMat.glass(el) adds refracting glass edges where the browser can (Chromium).
   One WebGL context for the whole page; a surface renders only when it is on screen and the light moved. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXMat) return;
  var doc = document, items = [], gl = null, glc = null, U = {}, ok = null, pending = 0, lastDraw = 0;
  var LX = 0, LY = 0, MAXPX = 1024, MAXITEMS = 24;
  var AUTO = { ".sx-seal": "seal", ".gm-lock-go": "gold", "#oskMain button.primary": "gold", ".sx-gold": "gold",
    "nav#oskNav": "velvet", "#oskMore .sheet": "velvet", "[data-sx-mat]": null };
  var MAT = { gold: [0, 0], platinum: [0, 1], seal: [1, 0], velvet: [2, 0] };

  var VS = "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
  var FS = [
    "precision highp float;",
    "uniform vec2 uRes;uniform float uDpr;uniform int uShape;uniform int uMat;uniform vec2 uHalf;uniform float uRad;uniform float uSeal;",
    "uniform mat3 uRot;uniform mat3 uGem;uniform vec4 uP[73];",
    "#define PI 3.14159265",
    "const vec3 F0G=vec3(.944,.776,.373);const vec3 F0P=vec3(.679,.642,.588);const vec3 F0S=vec3(.962,.949,.922);",
    "float hash(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}",
    "float vnoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}",
    "float fbm(vec2 p){float s=0.,a=.5;for(int i=0;i<4;i++){s+=a*vnoise(p);p*=2.03;a*=.5;}return s;}",
    "float box(vec3 d,vec3 ax,vec2 hs,float sf){float k=dot(d,ax);if(k<=0.)return 0.;vec3 p=d/k;vec3 r=normalize(cross(vec3(0,1,0),ax));vec3 u=cross(ax,r);",
    " vec2 q=abs(vec2(dot(p,r),dot(p,u)));vec2 e=smoothstep(hs+sf,hs-sf,q);return e.x*e.y;}",
    "float spot(vec3 d,vec3 ax,float rd,float sf){return smoothstep(rd+sf,rd-sf*.5,acos(clamp(dot(d,ax),-1.,1.)));}",
    // The studio. Behind the viewer (z>0) a light tent: bright above the horizon, a crisp horizon line, a dark warm floor.
    "vec3 env(vec3 d,float ro){d=uRot*d;float s=.012+ro*.5;float e=1./(1.+ro*5.);",
    " vec3 c=mix(vec3(.006,.009,.018),vec3(.035,.045,.07),smoothstep(-.3,.9,d.y));",
    " c+=vec3(.024,.018,.011)*smoothstep(0.,-.5,d.y);",
    " float fr=smoothstep(-.15,.35,d.z)*smoothstep(1.05,.35,abs(d.x));",
    " c+=vec3(1.,.90,.74)*.95*e*fr*smoothstep(.0-s,.03+s,d.y)*mix(.22,1.,smoothstep(.0,.42,d.y))*mix(1.,.6,smoothstep(.55,.95,d.y));",
    " c+=vec3(1.,.96,.88)*2.2*e*fr*smoothstep(.018+s,.0,abs(d.y+.005));",
    " c+=vec3(1.,.95,.88)*6.*e*box(d,normalize(vec3(-.42,.62,.66)),vec2(.40,.24),s);",
    " c+=vec3(.82,.88,1.)*3.*e*box(d,normalize(vec3(.74,.16,.65)),vec2(.07,.55),s);",
    " c+=vec3(1.,.98,.95)*38.*e*spot(d,normalize(vec3(.26,.78,.57)),.03,s*.6);",
    " c+=vec3(.95,.97,1.)*24.*e*spot(d,normalize(vec3(-.66,.28,.70)),.022,s*.6);",
    " return c;}",
    "vec3 metal(vec3 N,vec3 F0,float ro){float c=clamp(N.z,0.,1.);vec3 F=F0+(1.-F0)*pow(1.-c,5.);return F*env(reflect(vec3(0,0,-1),N),ro);}",
    "float sdBox(vec2 p,vec2 b,float r){vec2 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,q.y),0.)-r;}",
    "vec3 tm(vec3 x){x=clamp(x*(2.51*x+.03)/(x*(2.43*x+.59)+.14),0.,1.);return pow(x,vec3(1./2.2));}",
    // A bevelled, very slightly cushioned plate (a polished bar or key). Normals from the shape's distance field.
    "vec4 plate(vec2 px){vec2 p=px-uRes*.5;vec2 b=uHalf;float rd=uRad;float d=sdBox(p,b,rd);float al=clamp(.5-d,0.,1.);if(al<=0.)return vec4(0.);",
    " float bev=min(b.y*.34,8.*uDpr);vec2 g=vec2(sdBox(p+vec2(1,0),b,rd)-sdBox(p-vec2(1,0),b,rd),sdBox(p+vec2(0,1),b,rd)-sdBox(p-vec2(0,1),b,rd));g=normalize(g+1e-6);",
    " float t=clamp(1.+d/bev,0.,1.);float an=pow(t,1.5)*1.32;vec2 cu=(p/b*vec2(.05,.22)+vec2(0.,.11))*(1.-t);",
    " vec3 N=normalize(vec3(g*sin(an)+cu,cos(an)));N.xy+=(vec2(vnoise(px*.8),vnoise(px*.8+17.))-.5)*.006;N=normalize(N);",
    " vec3 c=uMat==1?metal(N,F0P,.13):metal(N,F0G,.10);return vec4(c,1.)*al;}",
    // The seal: guilloché enamel dome, a gold padlock casting its shadow, a platinum line, a gold bezel with circular
    // graining, and a diamond in a platinum collet at twelve o'clock.
    "float shk(vec2 p,out vec2 g){vec2 c=vec2(0.,.07);float R=.16;if(p.y>=c.y){vec2 d=p-c;float l=length(d);g=d/max(l,1e-4)*sign(l-R);return abs(l-R);}",
    " vec2 L=vec2(sign(p.x)*R,clamp(p.y,-.08,c.y));vec2 d=p-L;float l=length(d);g=d/max(l,1e-4);return l;}",
    "float body(vec2 p){return sdBox(p-vec2(0.,-.16),vec2(.26,.18),.06);}",
    "float hole(vec2 p){return min(length(p-vec2(0.,-.12))-.036,sdBox(p-vec2(0.,-.19),vec2(.014,.06),.01));}",
    "float padSd(vec2 p){vec2 g;return min(shk(p,g)-.04,body(p));}",
    "float enterT(vec3 o,vec3 d,out vec3 nI){float tn=-1e9,tf=1e9;nI=vec3(0,0,1);for(int i=0;i<73;i++){vec4 P=uP[i];float dn=dot(P.xyz,d);float nu=P.w-dot(P.xyz,o);",
    " if(abs(dn)<1e-6){if(nu<0.)return -1.;}else{float t=nu/dn;if(dn<0.){if(t>tn){tn=t;nI=P.xyz;}}else tf=min(tf,t);}}return tn<=tf&&tf>0.?tn:-1.;}",
    "float exitT(vec3 o,vec3 d,out vec3 nO){float tm=1e9;nO=vec3(0,0,1);for(int i=0;i<73;i++){vec4 P=uP[i];float dn=dot(P.xyz,d);if(dn>1e-6){float t=(P.w-dot(P.xyz,o))/dn;if(t<tm){tm=t;nO=P.xyz;}}}return tm;}",
    "float fres(float ci,float n1,float n2){float r=(n1-n2)/(n1+n2);r*=r;return r+(1.-r)*pow(1.-ci,5.);}",
    "float chan(vec3 p,vec3 d,vec3 n,float ior,int ch){vec3 dir=refract(d,n,1./ior);float th=1.-fres(clamp(dot(-d,n),0.,1.),1.,ior);float acc=0.;",
    " for(int b=0;b<5;b++){vec3 m;float t=exitT(p+dir*1e-4,dir,m);p+=dir*t;vec3 nm=-m;vec3 od=refract(dir,nm,ior);",
    "  if(dot(od,od)<1e-4){dir=reflect(dir,nm);continue;}float Fi=fres(clamp(dot(-dir,nm),0.,1.),ior,1.);vec3 e=env(uGem*od,.004);",
    "  acc+=th*(1.-Fi)*(ch==0?e.r:(ch==1?e.g:e.b));th*=Fi;dir=reflect(dir,nm);}return acc;}",
    "vec4 gem(vec2 q){vec3 o=uGem*vec3(q,3.),d=uGem*vec3(0,0,-1.);vec3 n;float t=enterT(o,d,n);if(t<0.)return vec4(0.);vec3 p=o+d*t;",
    " float F=fres(clamp(dot(-d,n),0.,1.),1.,2.426);vec3 c=F*env(uGem*reflect(d,n),.004);",
    " c+=vec3(chan(p,d,n,2.410,0),chan(p,d,n,2.426,1),chan(p,d,n,2.444,2));return vec4(c,1.);}",
    "vec4 ring(float r,vec2 P,float r0,float r1,vec3 F0,float ro,float aa){if(r<r0-aa||r>r1+aa)return vec4(0.);float m=(r0+r1)*.5,h=(r1-r0)*.5;float u=clamp((r-m)/h,-1.,1.);",
    " vec2 dr=P/max(r,1e-4);vec3 N=normalize(vec3(dr*u,sqrt(max(1.-u*u,.02))));N.xy+=dr*sin(r*uSeal*3.1)*.012;",
    " float al=smoothstep(r0-aa,r0,r)*smoothstep(r1+aa,r1,r);return vec4(metal(normalize(N),F0,ro),1.)*al;}",
    "vec4 over(vec4 a,vec4 b){return b+a*(1.-b.a);}",
    "vec4 seal(vec2 px){vec2 P=(px-uRes*.5)/uSeal;float r=length(P);float aa=1.6/uSeal;vec4 o=vec4(0.);",
    " if(r<.905){vec3 N=normalize(vec3(P*.95,1.));float a=atan(P.y,P.x);vec3 T=vec3(-sin(a),cos(a),0.);",
    "  float rid=sin(a*96.)*.55+sin(a*192.+r*14.)*.15;vec3 Nb=normalize(vec3(P*.06,1.)+T*rid*.30);vec3 un=metal(Nb,F0S,.30);",
    "  float cv=max(N.z,.2);vec3 Tr=exp(-vec3(4.4,3.0,1.05)*(.62+.18*r)/cv);float Fc=.04+.96*pow(1.-cv,5.);",
    "  vec3 c=Fc*env(reflect(vec3(0,0,-1),N),.02)+(1.-Fc)*Tr*un;c*=mix(.30,1.,smoothstep(-.015,.08,padSd(P-vec2(.03,-.045))));",
    "  o=vec4(c,1.)*smoothstep(.905,.905-aa,r);}",
    " vec2 g;float sd=shk(P,g);if(sd<.04+aa){float q=clamp(sd/.04,0.,1.);vec3 N=normalize(vec3(g*q,sqrt(max(1.-q*q,.03))));o=over(o,vec4(metal(N,F0G,.09),1.)*smoothstep(.04+aa,.04,sd));}",
    " float bd=body(P);if(bd<aa){float bv=.045;float t=clamp(1.+bd/bv,0.,1.);vec2 gb=normalize(vec2(body(P+vec2(.001,0))-body(P-vec2(.001,0)),body(P+vec2(0,.001))-body(P-vec2(0,.001)))+1e-6);",
    "  float an=pow(t,1.4)*1.3;vec3 N=normalize(vec3(gb*sin(an)+(P-vec2(0.,-.16))*vec2(.12,.18)*(1.-t),cos(an)));vec3 c=metal(N,F0G,.09);",
    "  float hd=hole(P);c=mix(c,vec3(.004,.006,.01)+metal(normalize(vec3(-normalize(P-vec2(0,-.12))*.8,.6)),F0G,.2)*.08,smoothstep(aa,-aa,hd));",
    "  o=over(o,vec4(c,1.)*smoothstep(aa,0.,bd));}",
    " if(r>.905&&r<.922)o=over(o,vec4(vec3(.004,.005,.008),1.)*smoothstep(.905,.905+aa,r)*smoothstep(.922+aa,.922,r));",
    " o=over(o,ring(r,P,.885,.905,F0P,.12,aa));o=over(o,ring(r,P,.92,1.,F0G,.14,aa));",
    " vec2 gc=vec2(0.,.962);vec2 q=(P-gc)/.135;float rq=length(q);",
    " if(rq<1.36){o=over(o,vec4(0.,0.,0.,.55)*smoothstep(1.36,1.05,length(q-vec2(.12,-.18))));",
    "  o=over(o,ring(rq,q,1.,1.32,F0P,.10,aa/.135));if(rq<1.02){vec4 gm=gem(q*1.02);o=over(o,vec4(gm.rgb,1.)*smoothstep(1.02,.99,rq));}}",
    " return o;}",
    // Velvet: a crushed pile under the same two lights, the Estevez-Kulla sheen lobe; brightest where the pile lies over.
    "vec4 velvet(vec2 px){vec2 p=px/uDpr;float cr=fbm(p*.011);float an=cr*9.42;vec2 gd=vec2(cos(an),sin(an));",
    " float pl=fbm(p*.33)*.6+vnoise(p*1.6)*.4;vec3 N=normalize(vec3(gd*(.30+.55*cr)+(pl-.5)*.22,1.));",
    " vec3 V=vec3(0,0,1),c=vec3(.008,.013,.030)*(.5+.5*N.z);float r=.38;",
    " for(int i=0;i<2;i++){vec3 L=normalize((i==0?vec3(-.42,.62,.66):vec3(.74,.16,.65))*uRot);vec3 H=normalize(L+V);float sh=sqrt(max(0.,1.-pow(dot(N,H),2.)));",
    "  float D=(2.+1./r)*pow(sh,1./r)/(2.*PI);c+=(i==0?vec3(.42,.47,.70):vec3(.30,.36,.62))*D*.22*max(dot(N,L),0.);}",
    " return vec4(c,1.);}",
    "void main(){vec2 px=gl_FragCoord.xy;vec4 o=uShape==0?plate(px):(uShape==1?seal(px):velvet(px));",
    " gl_FragColor=vec4(tm(o.rgb/max(o.a,1e-4))*o.a,o.a);}"
  ].join("\n");

  // The 73 facet planes of a round brilliant (radius 1, table up), in Tolkowsky's proportions.
  function brilliant() {
    var P = [], r = Math.PI / 180, zg = 0.015, zt = zg + 0.324;
    function add(b, f, up, R, z) { var s = Math.sin(b * r), c = Math.cos(b * r), n = [s * Math.cos(f * r), s * Math.sin(f * r), up ? c : -c]; P.push([n[0], n[1], n[2], n[0] * R * Math.cos(f * r) + n[1] * R * Math.sin(f * r) + n[2] * z]); }
    P.push([0, 0, 1, zt]);
    for (var k = 0; k < 8; k++) { add(34.5, k * 45, true, 1, zg); add(21.7, 22.5 + k * 45, true, 0.53, zt); add(40.75, k * 45, false, 1, -zg); }
    for (k = 0; k < 16; k++) { add(42, 11.25 + k * 22.5, true, 1, zg); add(42, 11.25 + k * 22.5, false, 1, -zg); add(90, k * 22.5, true, 1, 0); }
    return [].concat.apply([], P);
  }
  function rot(ax, ay) { var cx = Math.cos(ax), sx = Math.sin(ax), cy = Math.cos(ay), sy = Math.sin(ay);
    return new Float32Array([cy, sx * sy, -cx * sy, 0, cx, sx, sy, -sx * cy, cx * cy]); }

  function init() {
    if (ok !== null) return ok;
    ok = false;
    try {
      if (doc.documentElement.hasAttribute("data-sx-mat-off")) return ok;
      glc = doc.createElement("canvas"); glc.width = glc.height = 256;
      gl = glc.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: false, preserveDrawingBuffer: false });
      if (!gl) return ok;
      var hp = gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
      if (!hp || hp.precision < 16 || gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS) < 96) return ok;
      function sh(t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; }
      var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr));
      gl.useProgram(pr);
      var bf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      var a = gl.getAttribLocation(pr, "a"); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
      ["uRes", "uDpr", "uShape", "uMat", "uHalf", "uRad", "uSeal", "uRot", "uGem", "uP"].forEach(function (n) { U[n] = gl.getUniformLocation(pr, n); });
      gl.uniform4fv(U.uP, new Float32Array(brilliant()));
      glc.addEventListener("webglcontextlost", function (e) { e.preventDefault(); ok = false; });
      ok = true;
    } catch (e) { ok = false; if (window.console && console.warn) console.warn("SXMat: materials fall back to CSS", e && e.message); }
    return ok;
  }

  function attach(el, kind) {
    if (el._sxMat || items.length >= MAXITEMS || !MAT[kind]) return;
    var cs = getComputedStyle(el); if (cs.display === "none") return;
    var cv = doc.createElement("canvas"); cv.className = "sx-mat-cv sx-mat-" + kind; cv.setAttribute("aria-hidden", "true");
    var inset = kind === "seal" ? 16 : 0;
    cv.style.cssText = "position:absolute;left:" + (-inset) + "px;top:" + (-inset) + "px;width:calc(100% + " + 2 * inset + "px);height:calc(100% + " + 2 * inset + "px);pointer-events:none;z-index:-1;" + (inset ? "" : "border-radius:inherit");
    if (cs.position === "static") el.style.position = "relative";
    el.style.isolation = "isolate";
    el.insertBefore(cv, el.firstChild);
    var it = { el: el, cv: cv, cx: cv.getContext("2d"), kind: kind, inset: inset, vis: true };
    el._sxMat = it; items.push(it);
    if (io) io.observe(el);
    if (draw(it)) el.classList.add("sx-mat-on", "sx-mat-" + kind + "-on");
  }
  function draw(it) {
    if (!ok || !it.vis) return false;
    var r = it.el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false;
    if (it.kind === "velvet" && doc.documentElement.getAttribute("data-theme") === "light" && it.el.matches("#oskMore .sheet")) { it.cx.clearRect(0, 0, it.cv.width, it.cv.height); it.el.classList.remove("sx-mat-on"); return false; }
    var d = Math.min(2, window.devicePixelRatio || 1) * (it.kind === "velvet" ? 0.75 : 1);
    var W = Math.round((r.width + 2 * it.inset) * d), H = Math.round((r.height + 2 * it.inset) * d);
    var f = Math.min(1, MAXPX / Math.max(W, H)); if (f < 1) { d *= f; W = Math.round(W * f); H = Math.round(H * f); }
    if (it.cv.width !== W || it.cv.height !== H) { it.cv.width = W; it.cv.height = H; }
    if (glc.width < W || glc.height < H) { glc.width = Math.max(glc.width, W); glc.height = Math.max(glc.height, H); }
    var m = MAT[it.kind], rad = parseFloat(getComputedStyle(it.el).borderTopLeftRadius) || 0;
    gl.viewport(0, 0, W, H);
    gl.uniform2f(U.uRes, W, H); gl.uniform1f(U.uDpr, d); gl.uniform1i(U.uShape, m[0]); gl.uniform1i(U.uMat, m[1]);
    gl.uniform2f(U.uHalf, r.width * d / 2, r.height * d / 2); gl.uniform1f(U.uRad, Math.min(rad, r.height / 2) * d);
    gl.uniform1f(U.uSeal, (r.width / 2) * d);
    gl.uniformMatrix3fv(U.uRot, false, rot(LY * 0.42, LX * 0.42));
    gl.uniformMatrix3fv(U.uGem, false, rot(0.16 + LY * 0.22, -0.08 + LX * 0.22));
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    it.cx.clearRect(0, 0, W, H);
    it.cx.drawImage(glc, 0, glc.height - H, W, H, 0, 0, W, H);
    it.el.classList.add("sx-mat-on", "sx-mat-" + it.kind + "-on");
    return true;
  }
  function drawAll() {
    pending = 0; lastDraw = performance.now();
    items = items.filter(function (it) { if (it.el.isConnected) return true; if (io) io.unobserve(it.el); return false; });
    items.forEach(draw);
  }
  function soon() { if (!ok || pending) return; var w = Math.max(0, 33 - (performance.now() - lastDraw)); pending = setTimeout(function () { requestAnimationFrame(drawAll); }, w); }
  var io = window.IntersectionObserver ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { var it = e.target._sxMat; if (it) { it.vis = e.isIntersecting; if (it.vis) draw(it); } });
  }) : null;
  function scan(root) {
    if (!init()) return;
    Object.keys(AUTO).forEach(function (sel) {
      (root || doc).querySelectorAll(sel).forEach(function (el) { attach(el, AUTO[sel] || el.getAttribute("data-sx-mat")); });
    });
  }

  // Glass that refracts: the backdrop bends at the bevelled rim (a displacement map from the element's own shape), with a
  // touch of dispersion, as thick glass does. Chromium only; elsewhere the frosted blur in lux.css stays.
  var glassN = 0;
  function glass(el) {
    if (el._sxGlass || !(window.CSS && CSS.supports && CSS.supports("backdrop-filter", "url(#a)")) || !/Chrome\//.test(navigator.userAgent || "")) return;
    var r = el.getBoundingClientRect(); if (r.width < 10) return;
    var W = Math.round(r.width), H = Math.round(r.height), rad = parseFloat(getComputedStyle(el).borderTopLeftRadius) || 24, bev = 22;
    var c = doc.createElement("canvas"); c.width = W; c.height = H; var x = c.getContext("2d"), im = x.createImageData(W, H), D = im.data;
    function sd(px, py) { var qx = Math.abs(px - W / 2) - W / 2 + rad, qy = Math.abs(py - H / 2) - H / 2 + rad; return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - rad; }
    for (var y = 0; y < H; y++) for (var i = 0; i < W; i++) {
      var dd = sd(i + .5, y + .5), t = Math.max(0, 1 + dd / bev), gx = sd(i + 1.5, y + .5) - sd(i - .5, y + .5), gy = sd(i + .5, y + 1.5) - sd(i + .5, y - .5), gl2 = Math.hypot(gx, gy) || 1;
      var mag = t * t * (3 - 2 * t), k = (y * W + i) * 4;
      D[k] = 128 - 127 * mag * gx / gl2; D[k + 1] = 128 - 127 * mag * gy / gl2; D[k + 2] = 128; D[k + 3] = 255;
    }
    x.putImageData(im, 0, 0);
    var id = "sxGlass" + (++glassN), url = c.toDataURL();
    var svg = doc.createElementNS(["http", "//www.w3.org/2000/svg"].join(":"), "svg")   // the SVG namespace name, not a network address;
    svg.setAttribute("width", "0"); svg.setAttribute("height", "0"); svg.setAttribute("aria-hidden", "true"); svg.style.position = "absolute";
    svg.innerHTML = '<filter id="' + id + '" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">'
      + '<feImage href="' + url + '" x="0" y="0" width="' + W + '" height="' + H + '" preserveAspectRatio="none" result="m"/>'
      + '<feDisplacementMap in="SourceGraphic" in2="m" scale="34" xChannelSelector="R" yChannelSelector="G" result="dg"/>'
      + '<feDisplacementMap in="SourceGraphic" in2="m" scale="40" xChannelSelector="R" yChannelSelector="G" result="dr"/>'
      + '<feDisplacementMap in="SourceGraphic" in2="m" scale="28" xChannelSelector="R" yChannelSelector="G" result="db"/>'
      + '<feColorMatrix in="dr" type="matrix" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="cr"/>'
      + '<feColorMatrix in="dg" type="matrix" values="0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0" result="cg"/>'
      + '<feColorMatrix in="db" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0" result="cb"/>'
      + '<feBlend in="cr" in2="cg" mode="screen" result="rg"/><feBlend in="rg" in2="cb" mode="screen"/></filter>';
    doc.body.appendChild(svg);
    el.style.backdropFilter = el.style.webkitBackdropFilter = "url(#" + id + ") blur(14px) saturate(150%)";
    el._sxGlass = svg; el.classList.add("sx-glass-on");
  }

  window.SXMat = {
    light: function (x, y) { LX = x; LY = y; soon(); },
    scan: scan, glass: glass, refresh: function () { soon(); },
    ready: function () { return init(); }
  };
  function boot() {
    scan(doc);
    var mo = window.MutationObserver ? new MutationObserver(function () { if (!boot.q) boot.q = requestAnimationFrame(function () { boot.q = 0; scan(doc); doc.querySelectorAll(".sx-lock-card, body.osk-locked #oskMain .card.hero").forEach(glass); }); }) : null;
    if (mo) mo.observe(doc.body, { childList: true, subtree: true });
    doc.querySelectorAll(".sx-lock-card, body.osk-locked #oskMain .card.hero").forEach(glass);
    window.addEventListener("resize", function () { soon(); });
    doc.addEventListener("visibilitychange", function () { if (!doc.hidden) soon(); });
    new MutationObserver(function () { soon(); }).observe(doc.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }
  if (/jsdom/i.test(navigator.userAgent || "")) return;   // a test DOM: the CSS look stays, nothing to light
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", boot); else setTimeout(boot, 0);
})();
