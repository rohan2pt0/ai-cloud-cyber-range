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
   get one still frame. No WebGL or no high precision: the 2D canvas below; no 2D canvas: the SVG SXWorld drew. */
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
      "vec3 glow(vec3 q){float hy=max(uLev*.55,30.);return uGlow*exp(-q.x*q.x/9000.)*(.35+exp(-(q.y-hy)*(q.y-hy)/(2.*(hy*.7+25.)*(hy*.7+25.))));}",
      "void scene(vec3 p,vec3 d,out vec3 cb,out vec3 cs){cs=vec3(0.);cb=vec3(0.);float w=0.;",
      " bool tb=false;if(d.y<-1e-4){vec3 q=p+d*(-p.y/d.y);if(q.z>-ZB){tb=true;w=smoothstep(520.,300.,length(q.xz));cb=uBg*(.62+.38*keyLight(q))*w;}}",
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

  // One context for every vessel. The program compiles in the background where the browser can (KHR_parallel_shader_compile):
  // until it is ready the 2D water shows, so a slow driver never freezes the page.
  var GL = { ok: null, gl: null, cv: null, U: {}, Q: 1, pr: null, ext: null, tex: null, ht: false, g: { lvl: 0, ms: [] } };
  // The speed guard (pure: the tests drive it). Every traced frame is timed; when the median of the last 8 is over 12 ms
  // the water drops to half resolution, and if it is still over 12 ms it becomes the 2D water for the rest of the session.
  // A shader not ready within 1.5 s also means half resolution. Levels: 0 full, 1 half, 2 the 2D water.
  var GUARD_MS = 12, GUARD_N = 8, GUARD_KEY = "sx_water_2d";
  function guard(g, ms) {
    if (g.lvl >= 2) return 2;
    g.ms.push(ms); if (g.ms.length > GUARD_N) g.ms.shift();
    if (g.ms.length === GUARD_N) { var m = g.ms.slice().sort(function (a, b) { return a - b; }); if ((m[3] + m[4]) / 2 > GUARD_MS) { g.lvl++; g.ms = []; } }
    return g.lvl;
  }
  function guardLate(g) { if (g.lvl < 1) { g.lvl = 1; g.ms = []; } return g.lvl; }
  function noGuard() { return !!window.SXWaterNoGuard; }   // for the proof screenshots on a machine without a GPU
  function guardApply() {
    if (noGuard()) return;
    GL.Q = GL.g.lvl >= 1 ? 0.5 : 1;
    if (GL.g.lvl >= 2) {
      try { sessionStorage.setItem(GUARD_KEY, "1"); } catch (e) {}
      GL.ok = false; all.forEach(function (x) { if (x.el.isConnected) render(x); });
    }
  }
  function glInit() {
    if (GL.ok !== null) return GL.ok !== false;
    GL.ok = false;
    try {
      if (!window.SXMat || !SXMat.STUDIO || document.documentElement.hasAttribute("data-sx-mat-off")) return false;
      try { if (sessionStorage.getItem(GUARD_KEY) === "1" && !noGuard()) return false; } catch (e) {}
      var cv = document.createElement("canvas"); cv.width = 300; cv.height = 340;
      var gl = cv.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: false, preserveDrawingBuffer: false });
      if (!gl) return false;
      var hp = gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
      if (!hp || hp.precision < 16) return false;
      GL.ht = !!gl.getExtension("OES_texture_float");
      var sh = function (t, src) { var o = gl.createShader(t); gl.shaderSource(o, src); gl.compileShader(o); return o; };
      var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fsSource(SXMat.STUDIO, GL.ht))); gl.linkProgram(pr);
      GL.gl = gl; GL.cv = cv; GL.pr = pr; GL.ext = gl.getExtension("KHR_parallel_shader_compile"); GL.ok = "pending";
      cv.addEventListener("webglcontextlost", function (e) { e.preventDefault(); GL.ok = false; });
      // The compile never blocks the page: only with the parallel-compile extension; without it, the 2D water stays.
      if (!GL.ext) { GL.ok = false; return false; }
      setTimeout(function () { if (GL.ok === "pending" && !noGuard()) guardLate(GL.g); GL.Q = GL.g.lvl >= 1 ? 0.5 : 1; }, 1500);
      if (GL.ext) { var poll = function () { if (GL.ok !== "pending") return; if (gl.getProgramParameter(pr, GL.ext.COMPLETION_STATUS_KHR)) glReady(); else setTimeout(poll, 60); }; setTimeout(poll, 30); }
      else glReady();
    } catch (e) { GL.ok = false; if (window.console && console.warn) console.warn("SXWater: the water falls back to 2D", e && e.message); }
    return GL.ok !== false;
  }
  function glReady() {
    var gl = GL.gl, pr = GL.pr;
    try {
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr) || "link");
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
      GL.ok = true;
      all = all.filter(function (x) { return x.el.isConnected; }); all.forEach(function (x) { render(x); });
    } catch (e) { GL.ok = false; if (window.console && console.warn) console.warn("SXWater: the water falls back to 2D", e && e.message); }
  }
  var HT = new Float32Array(128 * 4);
  function lin(c) { c /= 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function rot(ax, ay) { var cx = Math.cos(ax), sx = Math.sin(ax), cy = Math.cos(ay), sy = Math.sin(ay); return new Float32Array([cy, sx * sy, -cx * sy, 0, cx, sx, sy, -sx * cy, cx * cy]); }
  // The state tints the light through the water 15% of the way to amber (watch) or rust (low): never murky.
  var TINT = { good: [1, 1, 1], watch: [1, 1 - 0.15 * 0.25, 1 - 0.15 * 0.65], low: [1 - 0.15 * 0.15, 1 - 0.15 * 0.55, 1 - 0.15 * 0.7] };
  function glRender(v, bands) {
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
    // On a dark page a warm soft box behind and above the glass lights the backdrop that only the glass sees (the page
    // around it is untouched), so light passes through the water and it reads as aqua, as in a dark-studio product shot.
    gl.uniform3f(U.uGlow, v.dark ? 0.30 : 0, v.dark ? 0.26 : 0, v.dark ? 0.20 : 0);
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
    if (bands) { v.ms = performance.now() - t0; SXWater.msBand = v.ms; if (!noGuard()) { guard(GL.g, v.ms); guardApply(); } return; }
    v.lastS = S;
    var lp = project([RO, BT + DEPTH1, 0]);
    c.setTransform(S, 0, 0, S, 0, 0); c.fillStyle = v.ink; c.globalAlpha = 0.78; c.font = "10px " + v.font; c.textBaseline = "alphabetic"; c.fillText(v.aim, lp[0] + 6, lp[1] + 3.5); c.globalAlpha = 1;
    var ms = performance.now() - t0; v.ms = ms; SXWater.ms = ms;
    if (!noGuard()) { guard(GL.g, ms); guardApply(); }
  }

  /* ---- the 2D fallback (no WebGL or no high precision) ---- */
  var VW = 150, VH = 170, IX0 = 35, IX1 = 115, FLOOR = 152, AIMY = 32;
  var TEAL = [[128, 232, 214], [42, 170, 160], [22, 128, 134]];
  var PALETTE = { good: TEAL, watch: TEAL.map(function (c) { return mix(c, [238, 190, 100], 0.15); }), low: TEAL.map(function (c) { return mix(c, [214, 138, 98], 0.3); }) };
  function still() {
    try { if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return true; } catch (e) {}
    return !!navigator.webdriver || /jsdom/i.test(navigator.userAgent || "");
  }
  var vessels = [], all = [], raf = 0, last = 0, io = null, vis = null;

  function glassPath(c) {
    c.moveTo(30, 22); c.quadraticCurveTo(30, 16, 36, 16); c.lineTo(114, 16); c.quadraticCurveTo(120, 16, 120, 22);
    c.lineTo(120, 150); c.quadraticCurveTo(120, 160, 110, 160); c.lineTo(40, 160); c.quadraticCurveTo(30, 160, 30, 150); c.closePath();
  }
  function innerPath(c) {
    c.moveTo(IX0, 17); c.lineTo(IX0, FLOOR - 6); c.quadraticCurveTo(IX0, FLOOR, IX0 + 6, FLOOR); c.lineTo(IX1 - 6, FLOOR);
    c.quadraticCurveTo(IX1, FLOOR, IX1, FLOOR - 6); c.lineTo(IX1, 17); c.closePath();
  }
  function rgba(rgb, a) { return "rgba(" + rgb + "," + a + ")"; }
  function mix(a, b, t) { return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), Math.round(a[2] + (b[2] - a[2]) * t)]; }

  function render2d(v) {
    v.ms = 0; var c = v.ctx, S = v.S, s = v.s, d = s.depth, dark = v.dark, W = PALETTE[v.state] || PALETTE.low, i, k, p, x, g, pts = [];
    if (v.cv.width !== Math.ceil(VW * S)) { v.cv.width = Math.ceil(VW * S); v.cv.height = Math.ceil(VH * S); }
    c.setTransform(S, 0, 0, S, 0, 0); c.clearRect(0, 0, VW, VH); c.lineJoin = "round"; c.lineCap = "round";
    var w0 = W[0], w1 = W[1], w2 = W[2];
    for (i = 0; i < s.n; i++) { x = IX0 + (IX1 - IX0) * i / (s.n - 1); pts.push({ x: x, y: FLOOR - s.h[i] - Math.min(2.4 * Math.exp(-(x - IX0) / 3.4) + 2.4 * Math.exp(-(IX1 - x) / 3.4), d * 0.3) }); }
    var top = FLOOR - d;
    c.fillStyle = "rgba(0,0,0,.10)"; c.beginPath(); c.ellipse(75, 164, 58, 7, 0, 0, 7); c.fill();
    c.fillStyle = "rgba(0,0,0,.20)"; c.beginPath(); c.ellipse(75, 162.5, 46, 4.2, 0, 0, 7); c.fill();
    c.save(); c.beginPath(); innerPath(c); c.clip();
    c.fillStyle = dark ? "rgba(190,215,230,.07)" : "rgba(200,225,235,.12)"; c.fillRect(0, 0, VW, VH);
    c.save(); c.beginPath(); c.moveTo(IX0 - 1, pts[0].y);
    for (i = 0; i < s.n; i++) c.lineTo(pts[i].x, pts[i].y);
    c.lineTo(IX1 + 1, pts[s.n - 1].y); c.lineTo(IX1 + 1, VH); c.lineTo(IX0 - 1, VH); c.closePath(); c.clip();
    g = c.createLinearGradient(0, top - 4, 0, FLOOR);
    g.addColorStop(0, rgba(w0.join(","), 0.94)); g.addColorStop(0.4, rgba(w1.join(","), 0.97)); g.addColorStop(1, rgba(w2.join(","), 1));
    c.fillStyle = g; c.fillRect(IX0 - 2, top - 14, IX1 - IX0 + 4, d + 30);
    g = c.createLinearGradient(0, top, 0, top + 20); g.addColorStop(0, "rgba(255,255,255,.30)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.fillStyle = g; c.fillRect(IX0, top - 6, IX1 - IX0, 26);
    if (d > 22) for (k = 0; k < v.bub.length; k++) {
      p = v.bub[k]; var by = FLOOR - (p.y - BT), bx = 75 + p.x * 0.95; if (by < top + 2 || by > FLOOR) continue;
      c.beginPath(); c.arc(bx, by, Math.max(0.6, p.r * 1.4), 0, 7); c.strokeStyle = "rgba(255,255,255,.6)"; c.lineWidth = 0.55; c.stroke();
    }
    c.restore();
    c.beginPath(); for (i = 0; i < s.n; i++) { if (i) c.lineTo(pts[i].x, pts[i].y); else c.moveTo(pts[i].x, pts[i].y); }
    c.strokeStyle = "rgba(255,255,255,.85)"; c.lineWidth = 1.5; c.stroke();
    c.restore();
    c.save(); c.beginPath(); c.moveTo(30, AIMY); c.lineTo(120, AIMY); c.strokeStyle = "#c9a84c"; c.lineWidth = 1.5; c.setLineDash([4, 3]); c.stroke(); c.restore();
    c.save(); c.beginPath(); glassPath(c); innerPath(c);
    g = c.createLinearGradient(30, 0, 120, 0);
    g.addColorStop(0, "rgba(205,235,240,.55)"); g.addColorStop(0.1, "rgba(205,235,240,.30)"); g.addColorStop(0.5, "rgba(205,235,240,.20)"); g.addColorStop(0.9, "rgba(205,235,240,.30)"); g.addColorStop(1, "rgba(205,235,240,.50)");
    c.fillStyle = g; c.fill("evenodd"); c.restore();
    g = c.createLinearGradient(0, 22, 0, 148); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.15, "rgba(255,255,255,.85)"); g.addColorStop(0.8, "rgba(255,255,255,.7)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.beginPath(); c.moveTo(32.6, 22); c.lineTo(32.6, 148); c.strokeStyle = g; c.lineWidth = 2.4; c.stroke();
    c.beginPath(); glassPath(c); c.strokeStyle = "rgba(160,185,198,.9)"; c.lineWidth = 1.3; c.stroke();
    c.beginPath(); c.ellipse(75, 16, 45, 3.5, 0, 0, 2 * Math.PI); c.strokeStyle = "rgba(190,210,220,.9)"; c.lineWidth = 1.3; c.stroke();
    c.fillStyle = v.ink; c.globalAlpha = 0.78; c.font = "10px " + v.font; c.textBaseline = "alphabetic"; c.fillText(v.aim, 124, AIMY + 4); c.globalAlpha = 1;
  }
  function render(v, bands) {
    if (v.gl && GL.ok === true) { try { glRender(v, bands); return; } catch (e) { v.gl = false; if (window.console && console.warn) console.warn("SXWater:", e && e.message); } }
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
      render(v, full ? null : (calm ? [] : waterBands(v)).concat(bb ? [bb] : []));
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
    guard: guard, guardLate: guardLate, GUARD_MS: GUARD_MS, GUARD_N: GUARD_N, GUARD_KEY: GUARD_KEY,
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
