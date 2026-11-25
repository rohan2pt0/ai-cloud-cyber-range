/* SecuRAX shared water (reuse-first; natures-design, signature-perfect; owner 2026-11-23: "water in a glass must look and move
   like real water in real glass"). One engine behind SXWorld.vessel (the emergency fund: months of cover in the tank).

   It is not drawn, it is lit and traced, as the gold is (shared/materials.js): one WebGL context for every vessel on the
   page, a ray traced through real optics, lit by the SAME studio as the gold (SXMat.STUDIO), so reflections agree.

   Real scale: the glass is 90 mm across (outer radius 45 mm, a 3 mm soda-lime wall, a 9 mm base), 138 mm tall; the canvas
   shows it at about 1 CSS pixel per millimetre, seen from a camera 215 mm above the table and 700 mm away.

   Optics (measured values):
   - water: n = 1.333, F0 = ((n-1)/(n+1))^2 = 0.020, Schlick's Fresnel, total internal reflection past 48.6 degrees;
     absorption by Beer-Lambert with pure water's coefficients (Pope and Fry 1997; Smith and Baker 1981): 0.45 /m at
     680 nm, 0.06 /m at 550 nm, 0.01 /m at 450 nm. A real glass of water is almost perfectly clear (a 9 cm path absorbs
     4% of red), so, as art direction, the path is read as if the glass were 4 m across (x48): clear aqua that deepens
     where the path is long. The state (good, watch, low) only tints the light through the water, at most 15%.
   - glass: soda-lime, n = 1.52, F0 = 0.043, the faint green of its iron (about 0.03 /cm red, 0.012 /cm green,
     0.028 /cm blue), refraction through both walls and the thick base; the lip and the base edge are rounded.
   - the surface: the exact linear solution of the damped wave equation in the glass, as modes. Each mode is a damped
     oscillator with the real dispersion of gravity-capillary waves, w^2 = (g k + sigma k^3 / rho) tanh(k h), g = 9.81,
     sigma = 0.0728 N/m, the wavenumbers of a round glass (the slosh mode k = 1.8412 / R, the first zero of J1'). It is
     solved in closed form per mode, so it is stable at any frame rate, and the volume is exact (the modes have no mean).
     Damping is the wall boundary layer (rate grows with the square root of frequency) plus viscosity (2 nu k^2).
     The meniscus curls up the wall over water's capillary length, sqrt(sigma / (rho g)) = 2.73 mm, rising 2.8 mm
     (contact angle about 28 degrees on clean glass); its volume is taken from the level, so the water's volume holds.
   - light: refraction and reflection follow the surface normal from the height field; caustics on the table under the
     glass are the real lens of the waves (the Jacobian of where each ray lands), and the glass of water throws its
     shadow and a focused line of light (a cylinder lens, focal length n R / (2 (n - 1)) from the axis) on the table.
   - bubbles: air spheres of 0.2 to 0.6 mm, clinging to the wall and the floor until they let go, then rising at their
     terminal velocity: Stokes' law, v = 2 (rho_w - rho_a) g r^2 / (9 mu), with mu = 1.0 mPa s, corrected for their
     Reynolds number (Schiller-Naumann drag), so a tiny bubble keeps Stokes and a large one rises as measured in tap
     water; each is a tiny refracting sphere whose skin is a mirror past the critical angle (a bright ring), and one now
     and then rests at the surface and breaks with a small ripple.
   - tone: the studio's light is tone mapped (ACES), the page's own colour seen through the glass passes exactly, sRGB out.

   Cost: one shared animation frame, only while a vessel is on screen and the page is visible; 60 frames a second while
   the water moves, 15 while only a bubble moves, none when all is still. Reduced motion, an automated browser and jsdom
   get one still frame. No WebGL, no high precision, a lost context or a GPU too slow even at half resolution: the painted
   2D water below (the same camera); no 2D canvas: the SVG SXWorld drew. A long press on the glass says which drew it, and why. */
(function () {
  "use strict";
  if (typeof window === "undefined" || window.SXWater) return;

  /* ---- physical constants and the glass (millimetres, seconds) ---- */
  var G = 9.81, SIGMA = 0.0728, RHO = 998, RHO_AIR = 1.2, MU = 1.0e-3, NU = MU / RHO;
  var LC = Math.sqrt(SIGMA / (RHO * G)) * 1000;           // capillary length, mm (2.73)
  var MEN = 2.8;                                           // meniscus rise at the wall, mm: LC * sqrt(2 (1 - sin 28 deg))
  var RO = 45, RI = 42, BT = 9, HG = 138, L = 2 * RI;      // outer and inner radius, base top, rim, width across
  var N = 48, M = 24, DEPTH1 = 120, MAXTILT = 10 * Math.PI / 180, GAMMA0 = 0.45;
  var J1P = [1.8412, 3.8317, 5.3314, 7.0156, 8.5363, 10.1735, 11.7060, 13.3237];   // zeros of J1' and J0' in order
  var CAM = { E: [0, 215, 700], T: [0, 72, 0], s: 0.92, cx: 75, cy: 78 };

  /* ---- physics (pure: no DOM, no animation frame; the tests drive it directly) ---- */
  function omega(k, h) { return Math.sqrt((G * k + SIGMA / RHO * k * k * k) * Math.tanh(k * h)); }   // k in 1/m, h in m
  function kOf(n) { return (n <= J1P.length ? J1P[n - 1] : (n / 2 + 0.25) * Math.PI) / (RI / 1000); }   // 1/m, round glass
  function depth(f) { return Math.max(4, DEPTH1 * Math.max(0.04, Math.min(1, f || 0))); }
  // The area mean of each mode's shape over the round surface (the even ones do not vanish on a disc): taken off in the
  // render so the water's volume in the round glass is exact too.
  var DISC = (function () {
    var c = [], n, i, S = 400, x, w, sw, s;
    for (n = 1; n <= M; n++) {
      s = 0; sw = 0;
      for (i = 0; i <= S; i++) { x = -RI + 2 * RI * i / S; w = Math.sqrt(Math.max(0, RI * RI - x * x)) * (i === 0 || i === S ? 0.5 : 1); s += w * Math.cos(n * Math.PI * (x + RI) / L); sw += w; }
      c.push(s / sw);
    }
    return c;
  })();
  function make(d) {
    var s = { n: N, h: [], v: [], depth: d, acc: 0, tilt: 0, a: [], b: [], w: [], g: [], t: [] }, i, k;
    for (i = 0; i < M; i++) {
      k = kOf(i + 1);
      s.a.push(0); s.b.push(0); s.t.push(0);
      s.w.push(omega(k, d / 1000));
      s.g.push(GAMMA0 * Math.sqrt(s.w[i] / omega(kOf(1), d / 1000)) + 2 * NU * k * k);
    }
    for (i = 0; i < N; i++) { s.h.push(d); s.v.push(0); }
    return s;
  }
  function mean(a) { var s = 0, i; for (i = 0; i < a.length; i++) s += a[i]; return s / a.length; }
  function xAt(i) { return (i + 0.5) * L / N; }                        // the column's centre, mm from the left wall
  function synth(s) {                                                    // the height field from the modes (mean exactly d)
    var i, n, x, c, h, v;
    for (i = 0; i < N; i++) {
      x = xAt(i) * Math.PI / L; h = s.depth; v = 0;
      for (n = 0; n < M; n++) { c = Math.cos((n + 1) * x); h += s.a[n] * c; v += s.b[n] * c; }
      s.h[i] = h; s.v[i] = v;
    }
  }
  // The plane the water would rest in, tilted by the phone, as modes: (x - L/2) tan(theta) = sum over odd n of -4L/(n pi)^2.
  function target(s, tilt) {
    var tn = Math.tan(Math.max(-1, Math.min(1, tilt || 0)) * MAXTILT), cap = 0.4 * s.depth / (L / 2), n;
    tn = Math.max(-cap, Math.min(cap, tn));
    for (n = 1; n <= M; n++) s.t[n - 1] = n % 2 ? tn * -4 * L / (n * n * Math.PI * Math.PI) : 0;
  }
  // Advance by dt seconds: each mode in closed form (a damped oscillator about its target), so any frame rate is stable.
  function step(s, dt, tiltX) {
    dt = Math.max(0, Math.min(0.1, dt || 0)); if (!dt) return s;
    s.tilt = tiltX || 0; target(s, s.tilt);
    for (var n = 0; n < M; n++) {
      var w = s.w[n], g = Math.min(s.g[n], w * 0.9), wd = Math.sqrt(w * w - g * g), y = s.a[n] - s.t[n], b = s.b[n];
      var e = Math.exp(-g * dt), c = Math.cos(wd * dt), sn = Math.sin(wd * dt);
      s.a[n] = s.t[n] + e * (y * c + (b + g * y) / wd * sn);
      s.b[n] = e * (b * c - (w * w * y + g * b) / wd * sn);
    }
    synth(s);
    return s;
  }
  // A poke: a push down of the surface around a column (a Gaussian about 6 mm wide), projected onto the modes.
  function splash(s, col, amount) {
    var vmax = Math.min(amount, s.depth * 0.12) * 60, i, n, x0 = xAt(Math.max(0, Math.min(N - 1, col))), dx, vi, sum;
    for (n = 0; n < M; n++) {
      sum = 0;
      for (i = 0; i < N; i++) { dx = xAt(i) - x0; vi = -vmax * Math.exp(-dx * dx / 36); sum += vi * Math.cos((n + 1) * Math.PI * xAt(i) / L); }
      s.b[n] += 2 * sum / N;
    }
    synth(s);
  }
  // The energy of the motion about the resting surface (kinetic plus potential, mm^2/s^2, scaled by 1/1000).
  function energy(s) { var e = 0, n, y; for (n = 0; n < M; n++) { y = s.a[n] - s.t[n]; e += 0.5 * (s.b[n] * s.b[n] + s.w[n] * s.w[n] * y * y); } return e / 1000; }
  function stokes(r) { var R = r / 1000; return 2 * (RHO - RHO_AIR) * G * R * R / (9 * MU) * 1000; }          // mm/s for r in mm
  // Terminal velocity with the Schiller-Naumann drag, Cd = 24/Re (1 + 0.15 Re^0.687): Stokes when Re is small.
  function rise(r) {
    var R = r / 1000, v = stokes(r) / 1000, i, Re, Cd;
    for (i = 0; i < 60; i++) { Re = Math.max(1e-9, 2 * R * v * RHO / MU); Cd = 24 / Re * (1 + 0.15 * Math.pow(Re, 0.687)); v = 0.5 * v + 0.5 * Math.sqrt(8 * R * (RHO - RHO_AIR) * G / (3 * RHO * Cd)); }
    return v * 1000;
  }
  function slosh(d) { return 2 * Math.PI / omega(kOf(1), d / 1000); }      // the period of the slosh mode, s
  function menVol() { return 2 * Math.PI * MEN * (LC * RI - LC * LC * (1 - Math.exp(-RI / LC))); }
  function eta(s, xm) {                                                     // the surface at xm (mm from the axis)
    var x = (Math.max(-RI, Math.min(RI, xm)) + RI) * Math.PI / L, e = 0, n, mf = 0;
    for (n = 0; n < M; n++) { e += s.a[n] * Math.cos((n + 1) * x); mf += s.a[n] * DISC[n]; }
    return e - mf;
  }

  /* ---- the bubbles: each one clings, lets go, rises, rests, breaks ---- */
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function seat(b, d) {                                    // a new bubble on the wall or the floor, under the water
    b.r = rnd(0.22, 0.6); b.mode = 0; b.wait = rnd(2, 12);
    if (Math.random() < 0.6) { var th = rnd(-1.3, 1.3) + (Math.random() < 0.3 ? Math.PI : 0); b.x = Math.sin(th) * (RI - b.r); b.z = Math.cos(th) * (RI - b.r); b.y = BT + rnd(2, Math.max(3, d - 4)); }
    else { var a = rnd(0, 6.283), q = Math.sqrt(Math.random()) * (RI - 3); b.x = Math.cos(a) * q; b.z = Math.sin(a) * q; b.y = BT + b.r; }
    b.ph = rnd(0, 6.283);
  }
  function bubbles(v, dt) {                                // returns true while any bubble moves
    var s = v.s, moving = false, k, b, top;
    for (k = 0; k < v.bub.length; k++) {
      b = v.bub[k];
      if (b.mode === 0) { b.wait -= dt; if (b.wait <= 0) { b.mode = 1; b.vy = rise(b.r); } continue; }
      moving = true;
      top = BT + s.depth - menVol() / (Math.PI * RI * RI) + eta(s, b.x);
      if (b.mode === 1) {
        b.y += b.vy * dt; b.ph += dt * 9; b.x += Math.cos(b.ph) * 0.03 * b.r;
        if (b.y + b.r >= top) { b.mode = 2; b.wait = rnd(0.4, 1.4); }
      } else {
        b.y = top - b.r * 0.4; b.wait -= dt;
        if (b.wait <= 0) { splash(s, (b.x + RI) / L * N - 0.5, 0.05); seat(b, s.depth); b.wait = rnd(6, 20); }
      }
    }
    return moving;
  }

  /* ---- the camera (shared by the shader and the label) ---- */
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function dot3(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function nrm(a) { var l = Math.sqrt(dot3(a, a)); return [a[0] / l, a[1] / l, a[2] / l]; }
  var CF = nrm(sub(CAM.T, CAM.E)), CU = nrm(sub([0, 1, 0], CF.map(function (x) { return x * CF[1]; }))), CD = Math.sqrt(dot3(sub(CAM.T, CAM.E), sub(CAM.T, CAM.E)));
  function project(P) { var r = sub(P, CAM.E), dp = dot3(r, CF); return [CAM.cx + r[0] * CD / dp * CAM.s, CAM.cy - dot3(r, CU) * CD / dp * CAM.s]; }

  /* ---- the ray tracer (WebGL) ---- */
  var VS = "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
  function fsSource(studio, ht) {
    return [
      "precision highp float;",
      ht ? "#define HT" : "",
      "uniform vec2 uC,uRes;uniform float uS;uniform sampler2D uH;uniform vec3 uE,uF,uU;uniform float uD;uniform mat3 uRot;",
      "uniform vec4 uA[6];uniform float uLev,uMf,uAmp;uniform vec4 uB[8];uniform vec3 uBg,uTn,uL,uInk;uniform float uAim,uDark;uniform vec3 uGlow;",
      "#define PI 3.14159265",
      "const float RO=45.,RI=42.,BT=9.,HG=138.,LW=84.,NW=1.333,NG=1.52,LC=" + LC.toFixed(3) + ",MH=" + MEN.toFixed(2) + ",ZB=150.;",
      "const vec3 SW=vec3(.45,.06,.01)*.012;",            // pure water, per mm, the path read 12 times longer (art direction)
      "const vec3 SG=vec3(.0030,.0012,.0028);",           // soda-lime glass, per mm
      studio,
      // the surface: the modes, their slope and curvature at x
      "#ifdef HT",
      // the surface sampled from a small table the CPU fills each frame (height, slope, curvature)
      "vec3 wave(float x){float u=(clamp(x,-RI,RI)+RI)/LW*127.,i=floor(u);return mix(texture2D(uH,vec2((i+.5)/128.,.5)).xyz,texture2D(uH,vec2((min(i+1.,127.)+.5)/128.,.5)).xyz,u-i);}",
      "#else",
      "vec3 wave(float x){float X=(clamp(x,-RI,RI)+RI)*(PI/LW);float c1=cos(X),s1=sin(X),c=c1,s=s1,e=0.,d1=0.,d2=0.,k0=PI/LW;",
      " for(int j=0;j<6;j++){vec4 A=uA[j];for(int q=0;q<4;q++){float a=q==0?A.x:(q==1?A.y:(q==2?A.z:A.w));float k=float(j*4+q+1)*k0;",
      "  e+=a*c;d1-=a*k*s;d2-=a*k*k*c;float cn=c*c1-s*s1;s=s*c1+c*s1;c=cn;}}return vec3(e-uMf,d1,d2);}",
      "#endif",
      "float men(float r){return MH*exp(-(RI-min(r,RI))/LC);}",
      "float Hs(vec3 p){return uLev+wave(p.x).x+men(length(p.xz));}",
      "vec3 Hn(vec3 p){vec3 w=wave(p.x);float r=max(length(p.xz),1e-3);float m=MH/LC*exp(-(RI-min(r,RI))/LC);vec2 g=vec2(w.y,0.)+p.xz/r*m;return normalize(vec3(-g.x,1.,-g.y));}",
      "vec2 cyl(vec3 o,vec3 d,float R){float a=dot(d.xz,d.xz),b=dot(o.xz,d.xz),c=dot(o.xz,o.xz)-R*R,h=b*b-a*c;if(h<0.||a<1e-9)return vec2(1e9,-1e9);h=sqrt(h);return vec2((-b-h)/a,(-b+h)/a);}",
      // Fresnel (Schlick, on the side of the thinner medium) and Snell; tir=1 when the light cannot leave
      "vec3 snell(vec3 d,vec3 n,float n1,float n2,out float F,out float tir){if(dot(d,n)>0.)n=-n;float e=n1/n2,ci=-dot(d,n),k=1.-e*e*(1.-ci*ci);tir=0.;",
      " if(k<0.){F=1.;tir=1.;return reflect(d,n);}float ct=sqrt(k),r0=(n1-n2)/(n1+n2);r0*=r0;F=r0+(1.-r0)*pow(1.-(n1>n2?ct:ci),5.);return e*d+(e*ci-ct)*n;}",
      "vec3 aces(vec3 x){return clamp(x*(2.51*x+.03)/(x*(2.43*x+.59)+.14),0.,1.);}",
      // the light from the soft box on the table: the glass's shadow, the focused line of the water's lens, the base's caustics
      "vec3 keyLight(vec3 q){float r=length(q.xz);vec3 L=uL;vec2 Lh=L.xz/L.y;",
      " if(r<RO){float D=(uLev-BT)+BT*NW/NG;vec3 tw=refract(-L,vec3(0,1,0),1./NW);float run=tw.x/-tw.y;float xs=q.x-D*run;",
      "  vec3 w;for(int i=0;i<3;i++){w=wave(xs);xs=q.x-D*run+D*(1.-1./NW)*w.y;}w=wave(xs);float J=1.-D*(1.-1./NW)*w.z;",
      "  float I=1./max(abs(J),.18);vec3 T=exp(-SW*D/max(-tw.y,.3))*uTn;float e=smoothstep(RO,RO-6.,r);",
      "  return mix(vec3(.55),T*I*.86,e);}",
      " float a=dot(Lh,Lh),y=clamp(-dot(q.xz,Lh)/a,0.,HG);vec2 c=q.xz+Lh*y;float b=length(c),sp=1.5+y*.34;",
      " float ao=1.-.6*exp(-(r-RO)/2.5);",
      " float inG=smoothstep(RO+sp,RO-sp,b);if(inG<=0.)return vec3(ao);",
      " float wet=smoothstep(uLev+1.5,uLev-1.5,y),f=y<BT?66.:84.;float dal=y*sqrt(a),m=1.-dal/f,am=max(abs(m),.07);",
      " float u0=b/am,beam=smoothstep(RI+sp/am,RI-sp/am,u0);",
      " vec3 T=exp(-SW*2.*sqrt(max(RI*RI-min(u0*u0,RI*RI),0.)))*uTn;vec3 wl=T*beam*.82/max(am,.16);",
      " float edge=smoothstep(RI-sp,RO,b)*(1.-smoothstep(RO,RO+sp,b));vec3 dl=vec3(.88-.55*edge);",
      " return mix(vec3(1.),mix(dl,wl,wet),inG)*ao;}",
      // what a ray sees once it has left the glass: the table (the page), the backdrop behind, or the room of the studio
      "vec3 glow(vec3 q){return uGlow*exp(-q.x*q.x/9000.)*smoothstep(uLev+5.,uLev-40.,q.y);}",   // the soft box's pool on the sweep, below the water line
      "vec3 glowT(vec3 q){return uGlow*.8*exp(-q.x*q.x/9000.)*smoothstep(-20.,-60.,q.z);}",   // and on the table behind the glass
      "void scene(vec3 p,vec3 d,out vec3 cb,out vec3 cs){cs=vec3(0.);cb=vec3(0.);float w=0.;",
      " bool tb=false;if(d.y<-1e-4){vec3 q=p+d*(-p.y/d.y);if(q.z>-ZB){tb=true;w=smoothstep(520.,300.,length(q.xz));cb=(uBg*(.62+.38*keyLight(q))+glowT(q))*w;}}",
      " if(!tb&&d.z<0.){vec3 q=p+d*((-ZB-p.z)/d.z);w=smoothstep(.02,-.3,d.z)*smoothstep(500.,260.,abs(q.x));cb=(uBg*(1.02+.05*clamp((q.y-90.)/120.,-1.,1.))+glow(q))*w;}",
      " float rim=smoothstep(-.1,-.4,d.z)*(smoothstep(.09,.0,abs(abs(d.x)-.42))*smoothstep(.75,.2,abs(d.y)));",
      " cs=env(d,.02)*(1.-w)+vec3(.9,.95,1.)*1.6*rim+uBg*.25*(1.-w)*(1.-uDark);}",
      "vec4 shade(vec2 px){vec2 uv=(px-uC)/uS;vec3 ro=uE,rd=normalize(uF*uD+vec3(uv.x,0.,0.)+uU*uv.y);",
      " vec3 cb=vec3(0.),cs=vec3(0.),th=vec3(1.),sb,ss;float med=0.,hit=0.,aim=0.,F,tir;vec3 p=ro,d=rd;",
      " for(int i=0;i<8;i++){if(max(th.r,max(th.g,th.b))<.03)break;",
      "  if(med<.5){",                                   // outside: the outer wall, the lip, the opening, else the scene
      "   vec2 c=cyl(p,d,RO);float t=1e9;vec3 n=vec3(0.);float to=0.;",
      "   if(c.x>1e-3){vec3 q=p+d*c.x;if(q.y>0.&&q.y<HG){t=c.x;vec3 rn=vec3(q.x,0.,q.z)/RO;float k=smoothstep(HG-1.6,HG,q.y);float kb=smoothstep(1.2,0.,q.y);n=normalize(rn+vec3(0,1,0)*k*1.4-vec3(0,1,0)*kb*1.2);to=1.;",
      "    aim=hit<.5&&abs(q.y-uAim)<.75&&fract(atan(q.x,q.z)*RO/7.)<.57?1.:0.;}}",
      "   if(d.y<0.){float tp=(HG-p.y)/d.y;vec3 q=p+d*tp;float rq=length(q.xz);if(tp>1e-3&&tp<t&&rq<RO){if(rq<RI){p=q;med=3.;hit=1.;continue;}t=tp;aim=0.;n=normalize(vec3(0,1,0)+vec3(q.x,0,q.z)/rq*((rq-43.5)/1.5)*1.2);to=1.;}}",
      "   if(to<.5){scene(p,d,sb,ss);cb+=th*sb;cs+=th*ss;break;}",
      "   p=p+d*t;vec3 nd=snell(d,n,1.,NG,F,tir);scene(p,reflect(d,dot(d,n)>0.?-n:n),sb,ss);cb+=th*F*sb;cs+=th*F*ss;th*=1.-F;",
      "   if(aim>.5){cb=mix(cb,uInk*.7,.9);cs*=.1;th*=.1;aim=0.;}hit=1.;d=nd;med=1.;continue;}",
      "  if(med<1.5){",                                  // in the glass: walls, base, lip
      "   float t=1e9,nx=0.;vec3 n=vec3(0.);vec2 c=cyl(p,d,RO);",
      "   if(c.y>1e-3){vec3 q=p+d*c.y;if(q.y>0.&&q.y<HG){t=c.y;n=vec3(q.x,0.,q.z)/RO;nx=0.;}}",
      "   vec2 ci=cyl(p,d,RI);if(ci.x>1e-3&&ci.x<t){vec3 q=p+d*ci.x;if(q.y>BT&&q.y<HG){t=ci.x;n=-vec3(q.x,0.,q.z)/RI+vec3(0,1,0)*smoothstep(HG-1.6,HG,q.y)*1.4;nx=1.;}}",
      "   if(d.y>0.){float tp=(BT-p.y)/d.y;if(tp>1e-3&&tp<t&&p.y<BT){vec3 q=p+d*tp;if(length(q.xz)<RI){t=tp;n=vec3(0,1,0);nx=2.;}}",
      "    tp=(HG-p.y)/d.y;if(tp>1e-3&&tp<t){vec3 q=p+d*tp;float rq=length(q.xz);if(rq>RI&&rq<RO){t=tp;n=normalize(vec3(0,1,0)+vec3(q.x,0,q.z)/rq*((rq-43.5)/1.5)*1.2);nx=3.;}}}",
      "   if(d.y<0.){float tp=-p.y/d.y;if(tp>1e-3&&tp<t){p=p+d*tp;th*=exp(-SG*tp);cb+=th*uBg*(.62+.38*keyLight(p));break;}}",
      "   if(t>1e8){break;}",
      "   p=p+d*t;th*=exp(-SG*t);n=normalize(n);",
      "   if(nx<.5||nx>2.5){vec3 nd=snell(d,n,NG,1.,F,tir);if(tir<.5){scene(p,nd,sb,ss);cb+=th*(1.-F)*sb;cs+=th*(1.-F)*ss;th*=F;}d=reflect(d,dot(d,n)>0.?-n:n);",
      "    if(hit>0.&&p.z<0.&&abs(p.y-uAim)<.75&&fract(atan(p.x,p.z)*RO/7.)<.57){cb=mix(cb,uInk*.55,.6);}continue;}",
      "   float wet=p.y<Hs(p)?1.:0.;float n2=wet>.5?NW:1.;vec3 nd=snell(d,n,NG,n2,F,tir);",
      "   if(tir>.5){d=nd;continue;}scene(p,reflect(d,dot(d,n)>0.?-n:n),sb,ss);cb+=th*F*sb;cs+=th*F*ss;th*=1.-F;d=nd;med=wet>.5?2.:3.;continue;}",
            "  vec2 ci=cyl(p,d,RI);float t=ci.y>1e-3?ci.y:1e9;float tf=1e9;",
      "  if(d.y<0.&&med<2.5){float tp=(BT-p.y)/d.y;if(tp>1e-3&&tp<t){t=tp;tf=tp;}}",
      "  if(d.y>0.&&med>2.5){float tp=(HG-p.y)/d.y;if(tp>1e-3&&tp<t){p=p+d*tp;med=0.;continue;}}",
      // the surface: search the band it can be in, then bisect
      "  float lo=uLev-uAmp-.5,hi=uLev+uAmp+MH+.5,t0=0.,t1=t,ts=-1.;",
      "  if(abs(d.y)>1e-5){float ta=(lo-p.y)/d.y,tb=(hi-p.y)/d.y;t0=max(0.,min(ta,tb));t1=min(t,max(ta,tb));}else if(p.y<lo||p.y>hi)t1=-1.;",
      "  if(t1>t0){float sg=med<2.5?-1.:1.,pa=t0;for(int k=1;k<=6;k++){float tt=mix(t0,t1,float(k)/6.);vec3 q=p+d*tt;if(sg*(q.y-Hs(q))<0.){float a=pa,b=tt;",
      "    for(int m=0;m<5;m++){float h=(a+b)*.5;vec3 qh=p+d*h;if(sg*(qh.y-Hs(qh))<0.)b=h;else a=h;}ts=b;break;}pa=tt;}}",
      "  if(ts>0.)t=ts;",
      "  if(med<2.5){",                                  // bubbles in the water along this run
      "   for(int k=0;k<8;k++){vec4 B=uB[k];if(B.w<=0.)continue;vec3 oc=p-B.xyz;float tb=-dot(oc,d);if(tb<0.||tb>t)continue;vec3 cp=oc+d*tb;float dd=length(cp);",
      "    float pm=length(p+d*tb-uE)/uD/uS;float cv=clamp((B.w-dd)/pm+.5,0.,1.);if(cv<=0.)continue;float u=min(dd/B.w,1.);",
      "    vec3 bn=normalize(cp/B.w-d*sqrt(max(1.-u*u,0.)));float ring=mix(smoothstep(.72,.78,u)*(1.-.75*smoothstep(.93,1.,u)),.44,clamp(pm/B.w*.5,0.,1.));",
      "    scene(B.xyz+bn*B.w,reflect(d,bn),sb,ss);cb+=th*cv*ring*sb;cs+=th*cv*ring*ss;th*=1.-cv*ring*.85;}",
      "   th*=exp(-SW*t)*mix(vec3(1.),uTn,clamp(t/60.,0.,1.));}",
      "  p=p+d*t;",
      "  if(ts>0.){vec3 n=Hn(p);vec3 nd=snell(d,n,med<2.5?NW:1.,med<2.5?1.:NW,F,tir);",
      "   if(tir>.5){d=nd;continue;}scene(p,reflect(d,dot(d,n)>0.?-n:n),sb,ss);cb+=th*F*sb;cs+=th*F*ss;th*=1.-F;d=nd;med=med<2.5?3.:2.;continue;}",
      "  vec3 n=tf<1e8&&t==tf?vec3(0,1,0):-vec3(p.x,0.,p.z)/RI;float n1=med<2.5?NW:1.;vec3 nd=snell(d,n,n1,NG,F,tir);",
      "  if(tir>.5){d=nd;continue;}scene(p,reflect(d,dot(d,n)>0.?-n:n),sb,ss);cb+=th*F*sb;cs+=th*F*ss;th*=1.-F;d=nd;med=1.;}",
      " vec3 o=cb+aces(cs);if(hit>.5)return vec4(o,1.);",
      // missed the glass: only the light on the table it changes (its shadow and its focused light), else transparent
      " vec2 ed=min(px,uRes-px)/(uS*7.);float ef=smoothstep(0.,1.,min(ed.x,ed.y));if(rd.y>=0.)return vec4(0.);vec3 k=keyLight(ro+rd*(-ro.y/rd.y));return vec4(uBg*(.62+.38*k),clamp(abs(1.-dot(k,vec3(.333)))*14.,0.,1.)*ef);}",
      "vec4 over(vec4 c){return vec4(c.rgb*c.a,c.a);}",
      // near the silhouette, three samples across the pixel, so the glass's edge is smooth
      "void main(){vec2 px=gl_FragCoord.xy;vec2 uv=(px-uC)/uS;vec3 rd=normalize(uF*uD+vec3(uv.x,0.,0.)+uU*uv.y);vec2 dh=normalize(rd.xz+1e-9);",
      " float e=abs(abs(uE.x*dh.y-uE.z*dh.x)-RO)*uS;vec4 c;",
      " if(e<1.2)c=(over(shade(px+vec2(-.33,0.)))+over(shade(px))+over(shade(px+vec2(.33,0.))))/3.;else c=over(shade(px));",
      " vec3 o=clamp(c.rgb/max(c.a,1e-4),0.,1.);o=mix(o*12.92,1.055*pow(o,vec3(1./2.4))-.055,step(.0031308,o));gl_FragColor=vec4(o*c.a,c.a);}"
    ].join("\n");
  }

  // One context for every vessel. The 2D water shows first, always; the traced water replaces it once its program is ready.
  // With KHR_parallel_shader_compile the driver compiles in the background and we poll; without it (many Android phones)
  // the compile waits for an idle moment after the first paint (requestIdleCallback, else a short timeout). A real mobile
  // GPU compiles in tens of milliseconds, so a missing extension never means the 2D water for good.
  var GL = { ok: null, gl: null, cv: null, U: {}, Q: 1, pr: null, ext: null, tex: null, ht: false, why: "", gpu: "", g: { lvl: 0, ms: [] } };
  // The speed guard (pure: the tests drive it). Only frames that animate are timed (a calm glass is drawn once and costs
  // nothing). When the median of the last 8 animating frames is over 20 ms the water drops to half resolution; only if it
  // stays over 45 ms at half resolution does it become the 2D water. A shader not ready within 1.5 s (with the parallel
  // compile) also means half resolution. Levels: 0 full, 1 half, 2 the 2D water.
  var GUARD_HALF = 20, GUARD_2D = 45, GUARD_N = 8, GUARD_KEY = "sx_water_2d", WATER_REV = "2";
  function median(a) { var m = a.slice().sort(function (x, y) { return x - y; }), h = m.length >> 1; return m.length % 2 ? m[h] : (m[h - 1] + m[h]) / 2; }
  function guard(g, ms, anim) {
    if (g.lvl >= 2) return 2;
    if (anim === false) return g.lvl;   // a still frame says nothing about the speed of the water
    g.ms.push(ms); if (g.ms.length > GUARD_N) g.ms.shift();
    if (g.ms.length === GUARD_N) {
      var m = median(g.ms);
      if (g.lvl === 0 && m > GUARD_HALF) { g.lvl = 1; g.ms = []; }
      else if (g.lvl === 1 && m > GUARD_2D) { g.lvl = 2; g.why = why2d("slow", Math.round(m)); g.ms = []; }
    }
    return g.lvl;
  }
  function guardLate(g) { if (g.lvl < 1) { g.lvl = 1; g.ms = []; } return g.lvl; }
  // Why the 2D water shows, in words a person can read (pure).
  function why2d(code, detail) {
    var t = { nogl: "this browser gave no WebGL", precision: "the GPU has no high-precision floats for the tracer", link: "the traced shader did not compile",
      lost: "the GPU context was lost", slow: "the traced water was too slow", off: "the lit materials are switched off", studio: "the studio light did not load" }[code] || String(code || "unknown");
    if (code === "slow" && detail != null) t += " (" + detail + " ms a frame at half resolution)";
    else if (detail) t += " (" + String(detail).slice(0, 80) + ")";
    return t;
  }
  // The one line the long-press shows (pure): what drew the water and, when known, the GPU.
  function drawnLine(st) {
    var t = st.ok === true ? "Drawn with: traced water (" + (st.lvl >= 1 ? "half" : "full") + ")"
      : st.ok === "pending" ? "Drawn with: 2D while the traced water compiles" : "Drawn with: 2D because " + (st.why || "the tracer has not started");
    return st.gpu ? t + ". GPU: " + st.gpu : t;
  }
  // The session remembers a fall to 2D with its reason and the version that decided it; a new version tries again (pure).
  function storedWhy(raw, ver) {
    if (!raw) return null;
    try { var o = JSON.parse(raw); return o && o.v === ver && o.why ? String(o.why) : null; } catch (e) { return null; }
  }
  function waterVer() { var b = document.getElementById("app_ver"); return WATER_REV + "|" + (b ? b.textContent.trim() : ""); }
  function noGuard() { return !!window.SXWaterNoGuard; }   // for the proof screenshots on a machine without a GPU
  function idle(f) { if (window.requestIdleCallback) requestIdleCallback(f, { timeout: 1200 }); else setTimeout(f, 120); }
  function redrawAll() { all = all.filter(function (x) { return x.el.isConnected; }); all.forEach(function (x) { render(x); }); }
  function fall(why, keep) {   // the 2D water from now on (for the session when keep), and why
    GL.ok = false; GL.why = why;
    if (keep && !noGuard()) { try { sessionStorage.setItem(GUARD_KEY, JSON.stringify({ v: waterVer(), why: why })); } catch (e) {} }
    if (window.console && console.warn) console.warn("SXWater: the 2D water, because " + why);
    redrawAll(); return false;
  }
  function guardApply() {
    if (noGuard()) return;
    GL.Q = GL.g.lvl >= 1 ? 0.5 : 1;
    if (GL.g.lvl >= 2) fall(GL.g.why || why2d("slow"), true);
  }
  function gpuName(gl) {
    try { var dbg = gl.getExtension("WEBGL_debug_renderer_info"); return String(gl.getParameter(dbg ? dbg.UNMASKED_RENDERER_WEBGL : gl.RENDERER) || "").slice(0, 90); } catch (e) { return ""; }
  }
  function glInit() {
    if (GL.ok !== null) return GL.ok !== false;
    GL.ok = false;
    try {
      if (window.SXWaterForce2D) { GL.why = String(window.SXWaterForce2D); return false; }
      if (document.documentElement.hasAttribute("data-sx-mat-off")) { GL.why = why2d("off"); return false; }
      if (!window.SXMat || !SXMat.STUDIO) { GL.why = why2d("studio"); return false; }
      var raw = null; try { raw = sessionStorage.getItem(GUARD_KEY); } catch (e) {}
      var was = storedWhy(raw, waterVer());
      if (was && !noGuard()) { GL.why = was; return false; }
      if (raw && !was) { try { sessionStorage.removeItem(GUARD_KEY); } catch (e) {} }   // an older version decided it: try again
      var cv = document.createElement("canvas"); cv.width = 300; cv.height = 340;
      var gl = cv.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: false, preserveDrawingBuffer: false });
      if (!gl) { GL.why = why2d("nogl"); return false; }
      GL.gpu = gpuName(gl);
      var hp = gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
      if (!hp || hp.precision < 16) { GL.why = why2d("precision"); return false; }
      GL.ht = !!gl.getExtension("OES_texture_float");
      GL.gl = gl; GL.cv = cv; GL.ext = gl.getExtension("KHR_parallel_shader_compile"); GL.ok = "pending";
      cv.addEventListener("webglcontextlost", function (e) { e.preventDefault(); fall(why2d("lost"), false); });
      cv.addEventListener("webglcontextrestored", function () { GL.ok = null; GL.U = {}; GL.pr = null; GL.tex = null; glInit(); });
      if (GL.ext) {
        glCompile();
        setTimeout(function () { if (GL.ok === "pending" && !noGuard()) guardLate(GL.g); GL.Q = GL.g.lvl >= 1 ? 0.5 : 1; }, 1500);
        var poll = function () { if (GL.ok !== "pending") return; if (gl.getProgramParameter(GL.pr, GL.ext.COMPLETION_STATUS_KHR)) glReady(); else setTimeout(poll, 60); };
        setTimeout(poll, 30);
      } else idle(function () { if (GL.ok !== "pending") return; glCompile(); glReady(); });   // after the first paint, never blocking it
    } catch (e) { fall(why2d("link", e && e.message), false); }
    return GL.ok !== false;
  }
  function glCompile() {
    var gl = GL.gl, sh = function (t, src) { var o = gl.createShader(t); gl.shaderSource(o, src); gl.compileShader(o); return o; };
    var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fsSource(SXMat.STUDIO, GL.ht))); gl.linkProgram(pr);
    GL.pr = pr;
  }
  function glReady() {
    var gl = GL.gl, pr = GL.pr;
    try {
      if (gl.isContextLost()) return;
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { fall(why2d("link", gl.getProgramInfoLog(pr) || "link"), true); return; }
      gl.useProgram(pr);
      var bf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      var a = gl.getAttribLocation(pr, "a"); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
      ["uC", "uRes", "uS", "uE", "uF", "uU", "uD", "uRot", "uA", "uLev", "uMf", "uAmp", "uB", "uBg", "uTn", "uL", "uInk", "uAim", "uDark", "uGlow", "uH"].forEach(function (n) { GL.U[n] = gl.getUniformLocation(pr, n); });
      if (GL.ht) {
        GL.tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, GL.tex);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.uniform1i(GL.U.uH, 0);
      }
      GL.ok = true; GL.why = "";
      all.forEach(function (x) { x.gl = true; }); redrawAll();
    } catch (e) { fall(why2d("link", e && e.message), true); }
  }
  // What drew the water, for the long-press on the glass (and the proof screenshots).
  function drawn() {
    if (!GL.gpu) { try { var c2 = document.createElement("canvas").getContext("webgl"); if (c2) { GL.gpu = gpuName(c2); var lc = c2.getExtension("WEBGL_lose_context"); if (lc) lc.loseContext(); } } catch (e) {} }
    return drawnLine({ ok: GL.ok, lvl: GL.g.lvl, why: GL.why, gpu: GL.gpu });
  }
  function explain(v) {
    var el = v.el, tip = el.querySelector(".sxw-why");
    if (!tip) {
      tip = document.createElement("div"); tip.className = "sxw-why"; tip.setAttribute("role", "status");
      tip.style.cssText = "position:absolute;left:0;top:100%;z-index:3;margin-top:4px;width:max-content;max-width:min(300px,80vw);padding:6px 10px;border-radius:10px;"
        + "font:12px/1.35 " + v.font + ";color:#f4f1e8;background:rgba(14,18,28,.94);box-shadow:0 4px 14px rgba(0,0,0,.25);cursor:pointer";
      tip.addEventListener("click", function () { tip.remove(); });
      el.appendChild(tip);
    }
    tip.textContent = drawn(); clearTimeout(tip._t); tip._t = setTimeout(function () { if (tip.isConnected) tip.remove(); }, 9000);
  }
  var HT = new Float32Array(128 * 4);
  function lin(c) { c /= 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function rot(ax, ay) { var cx = Math.cos(ax), sx = Math.sin(ax), cy = Math.cos(ay), sy = Math.sin(ay); return new Float32Array([cy, sx * sy, -cx * sy, 0, cx, sx, sy, -sx * cy, cx * cy]); }
  // The state tints the light through the water 15% of the way to amber (watch) or rust (low): never murky.
  var TINT = { good: [1, 1, 1], watch: [1, 1 - 0.15 * 0.25, 1 - 0.15 * 0.65], low: [1 - 0.15 * 0.15, 1 - 0.15 * 0.55, 1 - 0.15 * 0.7] };
  function glRender(v, bands, anim) {
    if (bands && !v.lastS) bands = null;
    var gl = GL.gl, U = GL.U, s = v.s, S = bands ? v.lastS : v.S * GL.Q, W = Math.round(VW * S), H = Math.round(VH * S), t0 = performance.now(), i, A = new Float32Array(24), B = new Float32Array(32), amp = 0, mf = 0;
    if (GL.cv.width < W || GL.cv.height < H) { GL.cv.width = Math.max(GL.cv.width, W); GL.cv.height = Math.max(GL.cv.height, H); }
    if (v.cv.width !== W || v.cv.height !== H) { v.cv.width = W; v.cv.height = H; }
    for (i = 0; i < M; i++) { A[i] = s.a[i]; amp += Math.abs(s.a[i]); mf += s.a[i] * DISC[i]; }
    if (GL.ht) {   // the surface, its slope and its curvature at 128 points across the glass
      for (i = 0; i < 128; i++) {
        var X = i / 127 * Math.PI, e = -mf, d1 = 0, d2 = 0, n, k, cc;
        for (n = 0; n < M; n++) { k = (n + 1) * Math.PI / L; cc = Math.cos((n + 1) * X); e += s.a[n] * cc; d1 -= s.a[n] * k * Math.sin((n + 1) * X); d2 -= s.a[n] * k * k * cc; }
        HT[i * 4] = e; HT[i * 4 + 1] = d1; HT[i * 4 + 2] = d2; HT[i * 4 + 3] = 0;
      }
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, GL.tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 128, 1, 0, gl.RGBA, gl.FLOAT, HT);
    }
    for (i = 0; i < 8 && i < v.bub.length; i++) { var b = v.bub[i]; if (b.y > BT + s.depth + 2) continue; B[i * 4] = b.x; B[i * 4 + 1] = b.y; B[i * 4 + 2] = b.z; B[i * 4 + 3] = b.r; }
    var lx = (window.SXTouch && SXTouch.light ? SXTouch.light.x : 0) || 0, ly = (window.SXTouch && SXTouch.light ? SXTouch.light.y : 0) || 0;
    var R = rot(ly * 0.42, lx * 0.42), Lb = nrm([-0.42, 0.62, 0.66]);
    // the key light in the world is the studio's soft box turned back by the same rotation (uRot maps world to studio)
    var Lw = [R[0] * Lb[0] + R[1] * Lb[1] + R[2] * Lb[2], R[3] * Lb[0] + R[4] * Lb[1] + R[5] * Lb[2], R[6] * Lb[0] + R[7] * Lb[1] + R[8] * Lb[2]];
    var tn = TINT[v.state] || TINT.low, ink = v.inkGold;
    gl.viewport(0, 0, W, H);
    gl.uniform2f(U.uC, CAM.cx * S, (VH - CAM.cy) * S); gl.uniform2f(U.uRes, W, H); gl.uniform1f(U.uS, CAM.s * S);
    gl.uniform3fv(U.uE, CAM.E); gl.uniform3fv(U.uF, CF); gl.uniform3fv(U.uU, CU); gl.uniform1f(U.uD, CD);
    gl.uniformMatrix3fv(U.uRot, false, R);
    gl.uniform4fv(U.uA, A); gl.uniform4fv(U.uB, B);
    gl.uniform1f(U.uLev, BT + s.depth - menVol() / (Math.PI * RI * RI)); gl.uniform1f(U.uMf, mf); gl.uniform1f(U.uAmp, amp);
    gl.uniform3fv(U.uBg, v.bg); gl.uniform3fv(U.uTn, tn); gl.uniform3fv(U.uL, nrm(Lw)); gl.uniform3fv(U.uInk, ink);
    gl.uniform1f(U.uAim, BT + DEPTH1); gl.uniform1f(U.uDark, v.dark ? 1 : 0);
    // On a dark page a soft box (daylight white) behind and above the glass lights the backdrop that only the glass sees (the page
    // around it is untouched), so light passes through the water and it reads as aqua, as in a dark-studio product shot.
    gl.uniform3f(U.uGlow, v.dark ? 0.27 : 0, v.dark ? 0.30 : 0, v.dark ? 0.31 : 0);
    var c = v.ctx, k, y0, bh, list = bands || [[0, VH]];
    c.setTransform(1, 0, 0, 1, 0, 0); gl.clearColor(0, 0, 0, 0);
    // Only the rows that can change are traced again (the surface and what is seen through it, the floor's caustics, a
    // moving bubble); the walls and the water seen through them stay as they were.
    for (k = 0; k < list.length; k++) {
      y0 = Math.max(0, Math.floor(list[k][0] * S)); bh = Math.min(H, Math.ceil(list[k][1] * S)) - y0; if (bh <= 0) continue;
      if (bands) { gl.enable(gl.SCISSOR_TEST); gl.scissor(0, H - y0 - bh, W, bh); }
      gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLES, 0, 3); gl.disable(gl.SCISSOR_TEST);
      c.clearRect(0, y0, W, bh); c.drawImage(GL.cv, 0, GL.cv.height - H + y0, W, bh, 0, y0, W, bh);
    }
    if (bands) { v.ms = performance.now() - t0; SXWater.msBand = v.ms; if (!noGuard()) { guard(GL.g, v.ms, !!anim); guardApply(); } return; }
    v.lastS = S;
    var lp = project([RO, BT + DEPTH1, 0]);
    c.setTransform(S, 0, 0, S, 0, 0); c.fillStyle = v.ink; c.globalAlpha = 0.78; c.font = "10px " + v.font; c.textBaseline = "alphabetic"; c.fillText(v.aim, lp[0] + 6, lp[1] + 3.5); c.globalAlpha = 1;
    var ms = performance.now() - t0; v.ms = ms; SXWater.ms = ms;
    if (!noGuard()) { guard(GL.g, ms, !!anim); guardApply(); }
  }

  /* ---- the 2D water (no WebGL, a lost context, too slow a GPU, or while the tracer compiles) ----
     The same camera as the tracer (project), so the glass, the level, the aim and the label sit where the traced frame puts
     them. It is painted, not traced, but painted from the same physics: a thick soda-lime wall with its refraction bands, a
     bright lip, the surface ellipse seen from above with its meniscus, absorption deepening with depth, the light the
     water focuses on the floor and the table, the glass's shadow from the studio's key light, and the real bubbles. */
  var VW = 150, VH = 170;
  // pale clear aqua, as the tracer shows a glass of water: [top, middle, deep]; the state tints it at most 10%
  var AQUA = { light: [[214, 240, 238], [186, 229, 228], [146, 207, 210]], dark: [[132, 178, 182], [94, 146, 154], [60, 112, 124]] };
  function aqua(dark, state) {
    var p = AQUA[dark ? "dark" : "light"], to = state === "watch" ? [238, 190, 100] : state === "low" ? [214, 138, 98] : null;
    return to ? p.map(function (c) { return mix(c, to, state === "watch" ? 0.07 : 0.1); }) : p;
  }
  function still() {
    try { if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return true; } catch (e) {}
    return !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
  }
  var vessels = [], all = [], raf = 0, last = 0, io = null, vis = null;

  function rgba(rgb, a) { return "rgba(" + rgb + "," + a + ")"; }
  function mix(a, b, t) { return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), Math.round(a[2] + (b[2] - a[2]) * t)]; }
  // the ellipse a circle of radius r at height y makes on screen (centre, half-width, half-height)
  function ell(y, r) { var c = project([0, y, 0]), f = project([0, y, r]), b = project([0, y, -r]); return { x: c[0], y: (f[1] + b[1]) / 2, rx: project([r, y, 0])[0] - c[0], ry: (f[1] - b[1]) / 2 }; }
  function silhouette(c, top, bot) {   // the glass seen whole: the far side of the lip, the walls, the near side of the base
    c.ellipse(top.x, top.y, top.rx, top.ry, 0, Math.PI, 2 * Math.PI); c.lineTo(bot.x + bot.rx, bot.y);
    c.ellipse(bot.x, bot.y, bot.rx, bot.ry, 0, 0, Math.PI); c.closePath();
  }
  function glow(c, x, y, rx, ry, rgb, a) {   // a soft elliptical light or shade
    c.save(); c.translate(x, y); c.scale(1, ry / rx);
    var g = c.createRadialGradient(0, 0, 0, 0, 0, rx); g.addColorStop(0, rgba(rgb, a)); g.addColorStop(0.55, rgba(rgb, a * 0.45)); g.addColorStop(1, rgba(rgb, 0));
    c.fillStyle = g; c.beginPath(); c.arc(0, 0, rx, 0, 7); c.fill(); c.restore();
  }

  function render2d(v) {
    v.ms = 0; var c = v.ctx, S = v.S, s = v.s, d = s.depth, dark = !!v.dark, A = aqua(dark, v.state), i, k, g, x, z, p, q;
    if (v.cv.width !== Math.ceil(VW * S)) { v.cv.width = Math.ceil(VW * S); v.cv.height = Math.ceil(VH * S); }
    c.setTransform(S, 0, 0, S, 0, 0); c.clearRect(0, 0, VW, VH); c.lineJoin = "round"; c.lineCap = "round";
    var top = ell(HG, RO), topIn = ell(HG, RI), bot = ell(0, RO), floor = ell(BT, RI), lev = BT + d - menVol() / (Math.PI * RI * RI);
    var ink = dark ? "0,0,0" : "40,52,58", lite = dark ? "236,246,248" : "255,255,255", wa = A.map(function (x) { return x.join(","); });

    // 1. the table: the glass's soft shadow falls back and to the right, away from the studio's key light (upper left)
    for (k = 12; k >= 0; k--) { var hh = k * 3.2; p = project([hh, 0, -0.45 * hh]); glow(c, p[0], p[1], bot.rx * (1 + k * 0.02), bot.ry * (1.15 + k * 0.03), ink, (dark ? 0.16 : 0.1) * (1 - k / 14)); }
    glow(c, bot.x + 2, bot.y + 1, bot.rx + 4, bot.ry + 3, ink, dark ? 0.55 : 0.3);   // the contact shadow under the base
    // the light the water column focuses on the table (a cylinder lens, focal length n R / (2 (n - 1)) from the axis)
    var fl = 1.333 * RI / (2 * 0.333), fp = project([0.91 * fl * 0.72, 0, -0.41 * fl * 0.72]), lit = Math.min(1, d / 60);
    glow(c, fp[0], fp[1], 10, 3.4, wa[1], (dark ? 0.5 : 0.7) * lit); glow(c, fp[0] - 1, fp[1], 5, 1.3, lite, (dark ? 0.55 : 0.9) * lit);

    // 2. inside the glass: the far wall and the empty glass above the water
    c.save(); c.beginPath(); silhouette(c, top, bot); c.clip();
    c.fillStyle = dark ? "rgba(196,214,220,.08)" : "rgba(214,232,236,.16)"; c.fillRect(0, 0, VW, VH);
    c.beginPath(); c.ellipse(top.x, top.y, topIn.rx, topIn.ry, 0, Math.PI, 2 * Math.PI); c.strokeStyle = rgba(lite, dark ? 0.25 : 0.7); c.lineWidth = 0.8; c.stroke();

    // 3. the water: the near side down to the floor, then the surface seen from slightly above
    var n = s.n, cl = [], cb = [], sf = [], sb = [];
    for (i = 0; i < n; i++) {
      x = -RI + (i + 0.5) * L / n; z = Math.sqrt(Math.max(0, RI * RI - x * x)); var hy = lev + (s.h[i] - d);
      cl.push(project([x, hy + MEN, z])); cb.push(project([x, hy + MEN, -z])); sf.push(project([x, hy, z * 0.86])); sb.push(project([x, hy, -z * 0.86]));
    }
    var eL = project([-RI, lev + (s.h[0] - d) + MEN, 0]), eR = project([RI, lev + (s.h[n - 1] - d) + MEN, 0]), fL = project([-RI, BT, 0]), fR = project([RI, BT, 0]);
    c.save(); c.beginPath(); c.moveTo(eL[0], eL[1]); c.lineTo(fL[0], fL[1]); c.ellipse(floor.x, floor.y, floor.rx, floor.ry, 0, Math.PI, 0, true); c.lineTo(eR[0], eR[1]);
    for (i = n - 1; i >= 0; i--) c.lineTo(cl[i][0], cl[i][1]);
    c.closePath(); c.clip();
    var yT = eL[1], yB = floor.y + floor.ry;
    g = c.createLinearGradient(0, yT, 0, yB); g.addColorStop(0, rgba(wa[0], 0.9)); g.addColorStop(0.35, rgba(wa[1], 0.93)); g.addColorStop(1, rgba(wa[2], 0.97));
    c.fillStyle = g; c.fillRect(0, yT - 2, VW, yB - yT + 4);
    // the round column bends the light: darker, deeper bands near the walls (the long path and total internal reflection), clearer in the middle
    g = c.createLinearGradient(fL[0], 0, fR[0], 0);
    g.addColorStop(0, rgba(wa[2], 0.85)); g.addColorStop(0.07, rgba(wa[2], 0.35)); g.addColorStop(0.16, rgba(lite, dark ? 0.06 : 0.22)); g.addColorStop(0.5, rgba(lite, 0));
    g.addColorStop(0.8, rgba(wa[2], 0.12)); g.addColorStop(0.93, rgba(wa[2], 0.45)); g.addColorStop(1, rgba(wa[2], 0.9));
    c.fillStyle = g; c.fillRect(0, yT - 2, VW, yB - yT + 4);
    // the floor seen through the water: the meniscus focuses a bright ring near the wall, the waves a net of caustic light
    c.beginPath(); c.ellipse(floor.x, floor.y, floor.rx - 4, floor.ry - 1.2, 0, 0, 7); c.strokeStyle = rgba(lite, dark ? 0.12 : 0.22); c.lineWidth = 2.4; c.stroke();
    glow(c, floor.x - 6, floor.y + 1, floor.rx * 0.6, floor.ry * 0.7, lite, dark ? 0.16 : 0.32);
    for (i = 1; i < n - 1; i++) {
      var cu = -(s.h[i - 1] - 2 * s.h[i] + s.h[i + 1]); if (cu <= 0.004) continue;   // a crest is a lens: it focuses light below it
      x = -RI + (i + 0.5) * L / n; z = Math.sqrt(Math.max(0, RI * RI - x * x)) * 0.9; p = project([x, BT, -z]); q = project([x, BT, z]);
      c.beginPath(); c.moveTo(p[0], p[1]); c.quadraticCurveTo(p[0] + 1.5, (p[1] + q[1]) / 2, q[0], q[1]); c.strokeStyle = rgba(lite, Math.min(0.55, cu * 9)); c.lineWidth = 1.1; c.stroke();
    }
    // the bubbles: tiny spheres whose skin is a mirror past the critical angle (a bright ring with a dark edge)
    for (k = 0; k < v.bub.length; k++) {
      var b = v.bub[k]; if (b.y > lev + 2 || d < 6) continue;
      p = project([b.x, b.y, b.z]); var br = Math.max(0.75, b.r * 1.7), back = b.z < 0 ? 0.55 : 1;
      c.beginPath(); c.arc(p[0], p[1], br, 0, 7); c.fillStyle = rgba(lite, 0.18 * back); c.fill(); c.strokeStyle = rgba(lite, 0.9 * back); c.lineWidth = 0.55; c.stroke();
      c.beginPath(); c.arc(p[0], p[1], br + 0.45, 0.2, 2.6); c.strokeStyle = rgba(wa[2], 0.7 * back); c.lineWidth = 0.4; c.stroke();
      c.beginPath(); c.arc(p[0] - br * 0.35, p[1] - br * 0.35, br * 0.28, 0, 7); c.fillStyle = rgba(lite, 0.95 * back); c.fill();
    }
    c.restore();
    // the surface: it mirrors the bright studio at a grazing angle (Fresnel), so the far half is brighter; a soft box highlight
    c.save(); c.beginPath(); c.moveTo(cl[0][0], cl[0][1]);
    for (i = 0; i < n; i++) c.lineTo(cl[i][0], cl[i][1]);
    for (i = n - 1; i >= 0; i--) c.lineTo(cb[i][0], cb[i][1]);
    c.closePath(); c.clip();
    var mid = (cl[n >> 1][1] + cb[n >> 1][1]) / 2;
    g = c.createLinearGradient(0, cb[n >> 1][1], 0, cl[n >> 1][1]);
    g.addColorStop(0, rgba(lite, dark ? 0.55 : 0.85)); g.addColorStop(0.45, rgba(wa[0], 0.9)); g.addColorStop(1, rgba(wa[1], 0.95));
    c.fillStyle = g; c.fillRect(0, cb[n >> 1][1] - 8, VW, cl[n >> 1][1] - cb[n >> 1][1] + 16);
    glow(c, top.x - top.rx * 0.38, mid - 1, top.rx * 0.34, Math.max(1.2, (cl[n >> 1][1] - cb[n >> 1][1]) * 0.22), lite, dark ? 0.6 : 0.9);
    c.restore();
    // the meniscus: water curls up the wall over its capillary length, so the near rim of the surface is a bright line over a dark one
    c.beginPath(); for (i = 0; i < n; i++) { if (i) c.lineTo(sf[i][0], sf[i][1]); else c.moveTo(sf[i][0], sf[i][1]); }
    c.strokeStyle = rgba(wa[2], dark ? 0.9 : 0.75); c.lineWidth = 0.9; c.stroke();
    c.beginPath(); for (i = 0; i < n; i++) { if (i) c.lineTo(cl[i][0], cl[i][1]); else c.moveTo(cl[i][0], cl[i][1]); }
    c.strokeStyle = rgba(lite, 0.95); c.lineWidth = 1.1; c.stroke();
    c.beginPath(); for (i = 0; i < n; i++) { if (i) c.lineTo(cb[i][0], cb[i][1]); else c.moveTo(cb[i][0], cb[i][1]); }
    c.strokeStyle = rgba(lite, dark ? 0.35 : 0.6); c.lineWidth = 0.7; c.stroke();
    c.restore();

    // 4. the thick base: soda-lime with the faint green of its iron, a bright refracted edge at the bottom, a dark seam at the floor
    c.save(); c.beginPath(); c.moveTo(fL[0] - 2.6, fL[1]); c.lineTo(bot.x - bot.rx, bot.y); c.ellipse(bot.x, bot.y, bot.rx, bot.ry, 0, Math.PI, 0, true);
    c.lineTo(fR[0] + 2.6, fR[1]); c.ellipse(floor.x, floor.y, floor.rx + 2.6, floor.ry + 0.4, 0, 0, Math.PI); c.closePath();
    g = c.createLinearGradient(0, floor.y, 0, bot.y + bot.ry);
    g.addColorStop(0, dark ? "rgba(150,190,186,.34)" : "rgba(196,228,222,.62)"); g.addColorStop(0.6, dark ? "rgba(120,160,158,.30)" : "rgba(176,214,210,.55)"); g.addColorStop(1, dark ? "rgba(200,230,228,.42)" : "rgba(222,242,240,.75)");
    c.fillStyle = g; c.fill(); c.restore();
    c.beginPath(); c.ellipse(floor.x, floor.y, floor.rx + 1, floor.ry + 0.3, 0, 0.05, Math.PI - 0.05); c.strokeStyle = rgba(ink, dark ? 0.5 : 0.22); c.lineWidth = 0.9; c.stroke();
    q = ell(2.2, RO - 1.2); c.beginPath(); c.ellipse(q.x, q.y, q.rx, q.ry, 0, 0.15, Math.PI - 0.15); c.strokeStyle = rgba(lite, dark ? 0.75 : 0.95); c.lineWidth = 1.2; c.stroke();

    // 5. the walls: a dark outer edge, a bright line where the wall turns, the soft box's two reflections, a darker inner edge
    c.save(); c.beginPath(); silhouette(c, top, bot); c.clip();
    var wallBand = function (x0, w, a) { g = c.createLinearGradient(x0, 0, x0 + w, 0); g.addColorStop(0, rgba(lite, 0)); g.addColorStop(0.5, rgba(lite, a)); g.addColorStop(1, rgba(lite, 0)); c.fillStyle = g; c.fillRect(x0, top.y, w, bot.y - top.y + 2); };
    wallBand(top.x - top.rx * 0.8, 8, dark ? 0.75 : 0.95); wallBand(top.x - top.rx * 0.78, 3, dark ? 0.7 : 0.9); wallBand(top.x - top.rx * 0.58, 2.4, dark ? 0.3 : 0.45); wallBand(top.x + top.rx * 0.7, 5, dark ? 0.6 : 0.85);
    g = c.createLinearGradient(top.x - top.rx, 0, top.x + top.rx, 0);
    g.addColorStop(0, rgba(dark ? "170,196,200" : "120,150,156", 0.55)); g.addColorStop(0.03, rgba(lite, dark ? 0.55 : 0.8)); g.addColorStop(0.055, rgba(dark ? "120,150,156" : "150,178,182", 0.35)); g.addColorStop(0.075, rgba(lite, 0));
    g.addColorStop(0.925, rgba(lite, 0)); g.addColorStop(0.945, rgba(dark ? "120,150,156" : "150,178,182", 0.3)); g.addColorStop(0.97, rgba(lite, dark ? 0.4 : 0.6)); g.addColorStop(1, rgba(dark ? "170,196,200" : "120,150,156", 0.55));
    c.fillStyle = g; c.fillRect(0, 0, VW, VH);
    c.restore();
    c.beginPath(); silhouette(c, top, bot); c.strokeStyle = dark ? "rgba(180,204,210,.55)" : "rgba(120,148,156,.6)"; c.lineWidth = 0.7; c.stroke();

    // 6. the aim, etched round the glass in gold (the far side faint), and the lip: a ring of glass with a bright near edge
    var ai = ell(BT + DEPTH1, RO + 0.2);
    c.save(); c.setLineDash([3.2, 2.4]); c.lineWidth = 1.3;
    c.beginPath(); c.ellipse(ai.x, ai.y, ai.rx, ai.ry, 0, Math.PI, 2 * Math.PI); c.strokeStyle = "rgba(201,168,76,.45)"; c.stroke();
    c.beginPath(); c.ellipse(ai.x, ai.y, ai.rx, ai.ry, 0, 0, Math.PI); c.strokeStyle = "#c9a84c"; c.stroke(); c.restore();
    c.beginPath(); c.ellipse(top.x, top.y, top.rx, top.ry, 0, 0, 7); c.ellipse(topIn.x, topIn.y, topIn.rx, topIn.ry, 0, 0, 7);
    c.fillStyle = dark ? "rgba(200,226,228,.28)" : "rgba(206,232,232,.6)"; c.fill("evenodd");
    c.beginPath(); c.ellipse(top.x, top.y, top.rx, top.ry, 0, 0.08, Math.PI - 0.08); c.strokeStyle = rgba(lite, 0.95); c.lineWidth = 1.15; c.stroke();
    c.beginPath(); c.ellipse(top.x, top.y, top.rx, top.ry, 0, Math.PI, 2 * Math.PI); c.strokeStyle = dark ? "rgba(190,214,220,.6)" : "rgba(130,158,166,.55)"; c.lineWidth = 0.7; c.stroke();
    c.beginPath(); c.ellipse(topIn.x, topIn.y, topIn.rx, topIn.ry, 0, 0.1, Math.PI - 0.1); c.strokeStyle = dark ? "rgba(120,150,156,.6)" : "rgba(130,158,166,.5)"; c.lineWidth = 0.6; c.stroke();
    glow(c, top.x - top.rx * 0.55, top.y + top.ry * 0.8, 6, 1.4, lite, 1);

    var lp = project([RO, BT + DEPTH1, 0]);
    c.fillStyle = v.ink; c.globalAlpha = 0.78; c.font = "10px " + v.font; c.textBaseline = "alphabetic"; c.fillText(v.aim, lp[0] + 6, lp[1] + 3.5); c.globalAlpha = 1;
  }
  function render(v, bands, anim) {
    if (v.gl && GL.ok === true) { try { glRender(v, bands, anim); return; } catch (e) { v.gl = false; if (window.console && console.warn) console.warn("SXWater:", e && e.message); } }
    render2d(v);
  }

  /* ---- vessels and the one shared loop ---- */
  function pageColour(el) {   // the colour behind the glass: the first painted background up the tree, layered as the page is
    var layers = [], e = el, m, a;
    while (e && e.nodeType === 1) {
      m = /rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)(?:[ ,/]+([\d.]+%?))?/.exec(getComputedStyle(e).backgroundColor || "");
      if (m) { a = m[4] === undefined ? 1 : (/%$/.test(m[4]) ? parseFloat(m[4]) / 100 : +m[4]); if (a > 0) { layers.push([+m[1], +m[2], +m[3], a]); if (a >= 0.99) break; } }
      e = e.parentElement;
    }
    var c = [255, 255, 255];
    if (layers.length && layers[layers.length - 1][3] >= 0.99) c = layers[layers.length - 1].slice(0, 3);
    else if (document.documentElement.getAttribute("data-theme") === "dark") c = [14, 18, 28];
    for (var i = layers.length - 1; i >= 0; i--) { var L2 = layers[i]; c = [c[0] + (L2[0] - c[0]) * L2[3], c[1] + (L2[1] - c[1]) * L2[3], c[2] + (L2[2] - c[2]) * L2[3]]; }
    return c;
  }
  function readTheme(v) {
    try {
      var cs = getComputedStyle(v.el), m = /rgba?\((\d+)[ ,]+(\d+)[ ,]+(\d+)/.exec(cs.color) || [0, 20, 20, 20], lum = (+m[1] * 299 + +m[2] * 587 + +m[3] * 114) / 1000;
      v.dark = lum > 140; v.ink = cs.color || "#222"; v.font = cs.fontFamily || "sans-serif";
      var pc = pageColour(v.el); v.bg = [lin(pc[0]), lin(pc[1]), lin(pc[2])];
      v.inkGold = [lin(201), lin(168), lin(76)];
    } catch (e) { v.ink = v.ink || "#222"; v.font = v.font || "sans-serif"; v.bg = v.bg || [1, 1, 1]; v.inkGold = v.inkGold || [0.58, 0.39, 0.07]; }
  }
  function visible(v) { return !vis || vis.get(v.el) !== false; }
  function sleepy(v) { return energy(v.s) < 0.0005; }

  function loopStart() { if (!raf && !still() && vessels.length && !document.hidden) { last = 0; raf = requestAnimationFrame(frame); } }
  function frame(now) {
    raf = 0; var dt = last ? Math.min(0.1, (now - last) / 1000) : 1 / 60, any = false, i, v, lx;
    last = now; vessels = vessels.filter(function (x) { if (x.el.isConnected) return true; if (io) io.unobserve(x.el); return false; });
    lx = (window.SXTouch && SXTouch.light ? SXTouch.light.x : 0) || 0;
    for (i = 0; i < vessels.length; i++) {
      v = vessels[i]; if (!visible(v)) continue; any = true;
      v.clock += dt;
      step(v.s, dt, lx);
      var moving = bubbles(v, dt); v.sinceDraw += dt;
      // moving water: every frame; only a bubble moving: 15 a second; all still: nothing to draw
      var turned = Math.abs(lx - v.tiltSeen) > 0.002, calm = sleepy(v), need = !calm || turned ? 0 : (moving ? 1 / 15 : 1e9);
      // a device that traces slowly draws less often (the main thread stays at least half free) rather than stutter the page
      if (v.sinceDraw < Math.max(need, Math.min(0.25, (v.ms || 0) * 2 / 1000))) continue;
      v.tiltSeen = lx; v.sinceDraw = 0;
      var bb = bubbleBand(v), full = turned || ++v.n % 90 === 1;   // the light turned (or now and then): the whole picture
      if (v.n % 90 === 1) readTheme(v);
      render(v, full ? null : (calm ? [] : waterBands(v)).concat(bb ? [bb] : []), true);   // an animating frame: the guard times it
    }
    if (any && !document.hidden) raf = requestAnimationFrame(frame);
  }

  // The rows a moving bubble covers now and covered at the last frame, in CSS pixels (refraction is horizontal in an
  // upright glass, so a band across it holds the bubble wherever the water shows it).
  function waterBands(v) {
    var s = v.s, amp = 0, n; for (n = 0; n < M; n++) amp += Math.abs(s.a[n]);
    return [[project([0, HG, -RO])[1] - 3, project([0, BT + s.depth - amp - 2, RO])[1] + 4], [project([0, BT, -RI])[1] - 4, project([0, 0, RO])[1] + 3]];
  }
  function bubbleBand(v) {
    var lo = 1e9, hi = -1e9, k, b, y;
    for (k = 0; k < v.bub.length; k++) {
      b = v.bub[k]; if (!b.mode && !b.was) continue;
      y = project([b.x, b.y, b.z])[1]; lo = Math.min(lo, y, b.py == null ? y : b.py); hi = Math.max(hi, y, b.py == null ? y : b.py);
      b.py = b.mode ? y : null; b.was = b.mode;
    }
    return hi < lo ? null : [lo - 7, hi + 7];
  }
  function vessel(el, f, state, aim, label) {
    if (!el || el.getAttribute("data-sxw")) return null;
    var cv, ctx; try { cv = document.createElement("canvas"); ctx = cv.getContext && cv.getContext("2d"); } catch (e) { ctx = null; }
    if (!ctx) return null;   // no 2D canvas: the SVG stays
    var S = Math.min(2, window.devicePixelRatio || 1), s = make(depth(f));
    cv.width = Math.ceil(VW * S); cv.height = Math.ceil(VH * S);
    cv.style.cssText = "position:absolute;left:0;top:0;width:" + VW + "px;height:" + VH + "px;touch-action:pan-y;cursor:pointer";
    var v = { el: el, cv: cv, ctx: ctx, S: S, s: s, state: state || "low", aim: String(aim || "").replace(/[<>&"]/g, ""), bub: [], clock: 0, sinceDraw: 0, n: 0, tiltSeen: 0, dark: null, ink: "#222", font: "sans-serif", gl: glInit() };
    for (var k = 0; k < 7; k++) { var b = {}; seat(b, s.depth); b.wait = k < 2 ? rnd(0.5, 4) : rnd(3, 14); v.bub.push(b); }
    if (label && !el.getAttribute("aria-label")) el.setAttribute("aria-label", label);
    var words = el.getAttribute("aria-label") || ""; cv.setAttribute("role", "img"); cv.setAttribute("aria-label", words); el.removeAttribute("role"); el.setAttribute("data-sxw", "1");
    var svg = el.querySelector("svg"); if (svg) svg.style.display = "none";
    el.appendChild(cv); readTheme(v); render(v); all.push(v);
    var col = function (e) { var r = cv.getBoundingClientRect(), xm = (((e.clientX - r.left) / (r.width || VW)) * VW - CAM.cx) / CAM.s; return Math.max(0, Math.min(N - 1, (xm + RI) / L * N - 0.5)); };
    var lastX = null;
    cv.addEventListener("pointerdown", function (e) { lastX = e.clientX; splash(s, col(e), 1.2); loopStart(); }, { passive: true });
    cv.addEventListener("pointermove", function (e) {
      if (!(e.buttons || e.pointerType === "touch") || lastX == null) return;
      var dx = e.clientX - lastX; lastX = e.clientX; splash(s, col(e), Math.min(0.8, Math.abs(dx) * 0.06 + 0.1)); loopStart();
    }, { passive: true });
    cv.addEventListener("pointerup", function () { lastX = null; }, { passive: true });
    // A long press (or the context menu a long press opens on Android) says what drew the water, and on which GPU.
    var hold = 0, hx = 0, hy = 0, unhold = function () { clearTimeout(hold); hold = 0; };
    cv.addEventListener("pointerdown", function (e) { hx = e.clientX; hy = e.clientY; unhold(); hold = setTimeout(function () { hold = 0; explain(v); }, 550); }, { passive: true });
    cv.addEventListener("pointermove", function (e) { if (hold && Math.abs(e.clientX - hx) + Math.abs(e.clientY - hy) > 10) unhold(); }, { passive: true });
    ["pointerup", "pointercancel", "pointerleave"].forEach(function (t) { cv.addEventListener(t, unhold, { passive: true }); });
    cv.addEventListener("contextmenu", function (e) { e.preventDefault(); unhold(); explain(v); });
    if (still()) return v;   // one still frame, no loop
    vessels.push(v);
    if (io) io.observe(el);
    loopStart();
    return v;
  }

  function scan(root) {
    var list = (root || document).querySelectorAll ? (root || document).querySelectorAll(".sx-water[data-f]:not([data-sxw])") : [], i, e;
    for (i = 0; i < list.length; i++) { e = list[i]; try { vessel(e, parseFloat(e.getAttribute("data-f")), e.getAttribute("data-state"), e.getAttribute("data-aim"), e.getAttribute("aria-label")); } catch (x) {} }
  }

  window.SXWater = { make: make, depth: depth, step: step, splash: splash, energy: energy, mean: mean, vessel: vessel, scan: scan,
    guard: guard, guardLate: guardLate, GUARD_HALF: GUARD_HALF, GUARD_2D: GUARD_2D, GUARD_N: GUARD_N, GUARD_KEY: GUARD_KEY,
    why2d: why2d, drawnLine: drawnLine, storedWhy: storedWhy, median: median, drawn: function () { return drawn(); }, ell: ell,
    omega: omega, kSlosh: kOf(1), slosh: slosh, stokes: stokes, rise: rise, eta: eta, project: project, render: render,
    LC: LC, MEN: MEN, G: G, MU: MU, NW: 1.333, NG: 1.52, RO: RO, RI: RI, ms: 0, vessels: function () { return vessels; } };

  // Upgrade every vessel the page draws, now and whenever a screen is redrawn.
  try {
    if (typeof document !== "undefined" && !/jsdom/i.test(navigator.userAgent || "")) {
      if (typeof IntersectionObserver === "function") { vis = new Map(); io = new IntersectionObserver(function (es) { es.forEach(function (e) { vis.set(e.target, e.isIntersecting); }); loopStart(); }, { rootMargin: "80px" }); }
      var pending = 0, go = function () { pending = 0; scan(document); };
      new MutationObserver(function () { if (!pending) pending = setTimeout(go, 40); }).observe(document.documentElement, { childList: true, subtree: true });
      document.addEventListener("visibilitychange", function () { if (!document.hidden) loopStart(); });
      new MutationObserver(function () { vessels.forEach(function (x) { readTheme(x); render(x); }); }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else setTimeout(go, 0);
    }
  } catch (e) {}
})();
