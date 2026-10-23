#!/usr/bin/env python3
"""The estate map: an interactive picture of the whole AI estate, built from its own declarations (doc 113).

    ./securax map            build the map and say where to open it
    python3 tools/estate_map.py [OUT.html]

Every component the estate declares (features.json) is a node, coloured by what it is for; every platform service it is
built on (governance/suite.json: identity, audit, policy, residency ...) is a hub in the middle; an edge joins a component
to each service it uses. It is one self-contained HTML file — no network, no library, no build step — so it opens on a
phone or a laptop, online or off. Hover a node to see what it touches, click it for the detail, filter by area, or search.
This is the "built for one, ready for many" story (doc 97) made visible. Standard library only; the data is baked in at
build time, so the file works even from the filesystem.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "portal" / "estate-map.html"

# One hue per feature group (dark-theme friendly, distinct); services and the core get their own.
GROUP_COLOR = {
    "Your own tools": "#5aa9e6",
    "Keep it running": "#67c98b",
    "Comply and govern": "#c792ea",
    "Practise and defend": "#e5897b",
    "Use AI safely": "#e0b341",
}
SERVICE_COLOR = "#8a94a6"
CORE_COLOR = "#f2f4f8"
W, H = 1440, 960
CX, CY = W / 2, H / 2


def load(root: pathlib.Path) -> dict:
    def j(p):
        return json.loads((root / p).read_text("utf-8"))
    return {"features": j("features.json"), "suite": j("governance/suite.json")}


def graph(data: dict) -> dict:
    """Nodes (components + platform services) and edges (a component uses a service)."""
    feats = {f["id"]: f for f in data["features"]["features"]}
    comps = data["suite"]["components"]
    svcs = data["suite"]["services"]
    nodes, edges = [], []

    # Platform-service hubs in an inner ring.
    svc_ids = list(svcs.keys())
    for i, sid in enumerate(svc_ids):
        a = 2 * math.pi * i / max(1, len(svc_ids)) - math.pi / 2
        nodes.append({
            "id": "svc:" + sid, "kind": "service", "name": sid,
            "label": svcs[sid].get("name", sid).split(":")[0],
            "group": "Platform service", "color": SERVICE_COLOR,
            "detail": svcs[sid].get("name", sid), "status": svcs[sid].get("status", ""),
            "x": CX + 210 * math.cos(a), "y": CY + 210 * math.sin(a), "deg": 0})

    # Components grouped by their feature area, each area in its own angular sector on an outer arc.
    groups = data["features"].get("groups", [])
    by_group: dict[str, list[str]] = {g: [] for g in groups}
    for cid in comps:
        g = feats.get(cid, {}).get("group", "Other")
        by_group.setdefault(g, []).append(cid)
    glist = [g for g in by_group if by_group[g]]
    for gi, g in enumerate(glist):
        base = 2 * math.pi * gi / max(1, len(glist)) - math.pi / 2
        members = sorted(by_group[g])
        for mi, cid in enumerate(members):
            spread = (mi - (len(members) - 1) / 2) * 0.16
            a = base + spread
            r = 360 + (mi % 3) * 48                       # a little depth so labels do not stack
            f = feats.get(cid, {})
            uses = comps[cid].get("uses", [])
            nodes.append({
                "id": "cmp:" + cid, "kind": "component", "name": f.get("name", cid),
                "label": f.get("name", cid), "group": g, "color": GROUP_COLOR.get(g, "#9aa0ab"),
                "command": f.get("command", ""), "outcome": f.get("outcome", ""),
                "what": f.get("what", ""), "doc": f.get("doc", ""),
                "edition": comps[cid].get("from", ""), "enterprise": comps[cid].get("enterprise", ""),
                "uses": uses, "x": CX + r * math.cos(a), "y": CY + r * math.sin(a), "deg": len(uses)})
            for s in uses:
                if ("svc:" + s) in {n["id"] for n in nodes} or s in svcs:
                    edges.append({"s": "cmp:" + cid, "t": "svc:" + s})

    deg: dict[str, int] = {}
    for e in edges:
        deg[e["s"]] = deg.get(e["s"], 0) + 1
        deg[e["t"]] = deg.get(e["t"], 0) + 1
    for n in nodes:
        n["deg"] = deg.get(n["id"], 0)
    legend = [{"group": g, "color": GROUP_COLOR.get(g, "#9aa0ab")} for g in glist]
    legend.append({"group": "Platform service", "color": SERVICE_COLOR})
    return {"nodes": nodes, "edges": edges, "legend": legend, "w": W, "h": H}


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SecuRAX estate map</title>
<style>
:root{--bg:#0d1526;--panel:#131d31;--line:#243049;--text:#eaf0f8;--muted:#9aa6bc;--accent:#5aa9e6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:16px 18px 8px}h1{margin:0;font-size:20px}p.sub{margin:4px 0 0;color:var(--muted);font-size:13.5px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px 18px}
.bar input{flex:1 1 200px;min-width:0;background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:10px;padding:9px 12px}
.chip{background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:999px;padding:7px 12px;cursor:pointer;font-size:13px}
.chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#06101f;font-weight:600}
.wrap{position:relative}
svg{display:block;width:100%;height:auto;touch-action:none}
.edge{stroke:#2b3a57;stroke-width:1}
.node{cursor:grab}.node:active{cursor:grabbing}
.node text{fill:var(--muted);font-size:11px;paint-order:stroke;stroke:var(--bg);stroke-width:3px}
.node.svc text{fill:var(--text);font-weight:600}
.dim{opacity:.12}
.panel{position:fixed;right:12px;bottom:12px;width:min(360px,92vw);max-height:70vh;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 10px 40px #0008;display:none}
.panel h2{margin:0 0 2px;font-size:17px}.panel .k{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin-top:10px}
.panel code{background:#0c1a2e;border:1px solid var(--line);border-radius:6px;padding:1px 6px}
.panel .tag{display:inline-block;background:#0c1a2e;border:1px solid var(--line);border-radius:999px;padding:2px 9px;margin:3px 4px 0 0;font-size:12px}
.panel .x{float:right;cursor:pointer;color:var(--muted);border:0;background:none;font-size:20px}
.legend{display:flex;gap:12px;flex-wrap:wrap;padding:6px 18px 14px;color:var(--muted);font-size:12.5px}
.legend span{display:inline-flex;align-items:center;gap:6px}.dot{width:10px;height:10px;border-radius:50%}
@media (prefers-color-scheme: light){:root:not([data-theme=dark]){--bg:#f4f7fc;--panel:#fff;--line:#d7deea;--text:#16202f;--muted:#5a6678}.edge{stroke:#c3cdde}.node text{fill:#5a6678}.node.svc text{fill:#16202f}}
</style></head>
<body>
<header><h1>SecuRAX estate map</h1>
<p class="sub">Every component, and the shared platform it is built on. <b>Drag any node</b> and the ones it links to follow, like beads on a thread. Tap for the detail, hover to highlight, filter or search. One file, no network — built for one, ready for many.</p></header>
<div class="bar" id="chips"><input id="q" type="search" placeholder="Search components and services…" aria-label="Search"></div>
<div class="legend" id="legend"></div>
<div class="wrap"><svg id="svg" viewBox="0 0 __W__ __H__" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Estate map"></svg></div>
<div class="panel" id="panel" role="dialog" aria-label="Component detail"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
 var G=JSON.parse(document.getElementById("data").textContent);
 var W=G.w,H=G.h,CX=W/2,CY=H/2;
 var svg=document.getElementById("svg"),NS="http://www.w3.org/2000/svg";
 var byId={}; G.nodes.forEach(function(n){byId[n.id]=n;n.vx=0;n.vy=0;n.fixed=false;n.r=n.kind==="service"?11:Math.max(5,Math.min(13,5+n.deg*1.2));});
 var nbr={}; G.nodes.forEach(function(n){nbr[n.id]={}});
 G.edges.forEach(function(e){e.a=byId[e.s];e.b=byId[e.t];(nbr[e.s])[e.t]=1;(nbr[e.t])[e.s]=1;});
 function el(t,a){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);return e;}
 G.edges.forEach(function(e){e._l=el("line",{class:"edge"});svg.appendChild(e._l);});
 G.nodes.forEach(function(n){
   var g=el("g",{class:"node"+(n.kind==="service"?" svc":""),tabindex:"0","data-id":n.id});
   n._c=el("circle",{r:n.r,fill:n.color,stroke:"#0a1322","stroke-width":1.2});g.appendChild(n._c);
   n._t=el("text",{"text-anchor":"middle"});n._t.textContent=n.label.length>22?n.label.slice(0,21)+"…":n.label;g.appendChild(n._t);
   g.addEventListener("mouseenter",function(){if(!drag)focus(n.id)});
   g.addEventListener("mouseleave",function(){if(!pinned&&!drag)clearFocus()});
   g.addEventListener("keydown",function(ev){if(ev.key==="Enter")pick(n)});
   svg.appendChild(g);n._g=g;
 });
 function draw(){
   G.edges.forEach(function(e){e._l.setAttribute("x1",e.a.x);e._l.setAttribute("y1",e.a.y);e._l.setAttribute("x2",e.b.x);e._l.setAttribute("y2",e.b.y);});
   G.nodes.forEach(function(n){n._c.setAttribute("cx",n.x);n._c.setAttribute("cy",n.y);n._t.setAttribute("x",n.x);n._t.setAttribute("y",n.y-n.r-5);});
 }
 // Force simulation: repulsion between all nodes, springs along edges, gentle pull to centre, damping — beads on threads.
 var REP=5200,SPR=0.015,LEN=84,GRAV=0.0016,DAMP=0.9,settled=false,raf=0;
 function tick(){
   var ns=G.nodes,i,j,n,m,dx,dy,d2,d,f,E=0;
   for(i=0;i<ns.length;i++){n=ns[i];
     for(j=i+1;j<ns.length;j++){m=ns[j];dx=n.x-m.x;dy=n.y-m.y;d2=dx*dx+dy*dy||0.01;if(d2<40000){d=Math.sqrt(d2);f=REP/d2;var ux=dx/d,uy=dy/d;n.vx+=ux*f;n.vy+=uy*f;m.vx-=ux*f;m.vy-=uy*f;}}
     n.vx+=(CX-n.x)*GRAV;n.vy+=(CY-n.y)*GRAV;
   }
   G.edges.forEach(function(e){dx=e.b.x-e.a.x;dy=e.b.y-e.a.y;d=Math.sqrt(dx*dx+dy*dy)||0.01;f=(d-LEN)*SPR;var ux=dx/d,uy=dy/d;e.a.vx+=ux*f;e.a.vy+=uy*f;e.b.vx-=ux*f;e.b.vy-=uy*f;});
   for(i=0;i<ns.length;i++){n=ns[i];if(n.fixed){n.vx=n.vy=0;continue;}n.vx*=DAMP;n.vy*=DAMP;n.x+=n.vx;n.y+=n.vy;n.x=Math.max(60,Math.min(W-60,n.x));n.y=Math.max(40,Math.min(H-30,n.y));E+=n.vx*n.vx+n.vy*n.vy;}
   draw();settled=E<0.4;
 }
 function loop(){tick();if(!settled&&typeof requestAnimationFrame==="function")raf=requestAnimationFrame(loop);else raf=0;}
 function reheat(){settled=false;if(!raf&&typeof requestAnimationFrame==="function")raf=requestAnimationFrame(loop);}
 draw();reheat();
 // highlight neighbours
 var pinned=false;
 function focus(id){var keep={};keep[id]=1;for(var k in nbr[id])keep[k]=1;G.nodes.forEach(function(n){n._g.classList.toggle("dim",!keep[n.id])});G.edges.forEach(function(e){e._l.classList.toggle("dim",!(e.s===id||e.t===id))});}
 function clearFocus(){G.nodes.forEach(function(n){n._g.classList.remove("dim")});G.edges.forEach(function(e){e._l.classList.remove("dim")});}
 var panel=document.getElementById("panel");
 function esc(s){var d=document.createElement("div");d.textContent=s==null?"":s;return d.innerHTML;}
 function pick(n){
   pinned=true;focus(n.id);
   var h='<button class="x" aria-label="Close" onclick="this.parentNode.style.display=\\'none\\'">×</button>';
   h+='<h2>'+esc(n.name)+'</h2><div class="k">'+esc(n.group)+(n.edition?' · '+esc(n.edition):'')+'</div>';
   if(n.outcome)h+='<p>'+esc(n.outcome)+'</p>';
   if(n.command)h+='<div class="k">Open</div><p><code>./securax '+esc(n.command)+'</code></p>';
   if(n.detail)h+='<p>'+esc(n.detail)+'</p>';
   if(n.uses&&n.uses.length){h+='<div class="k">Built on</div><div>'+n.uses.map(function(u){return '<span class="tag">'+esc(u)+'</span>'}).join("")+'</div>';}
   if(n.enterprise)h+='<div class="k">Enterprise adds</div><p>'+esc(n.enterprise)+'</p>';
   if(n.doc)h+='<div class="k">Doc</div><p>'+esc(n.doc)+'</p>';
   panel.innerHTML=h;panel.style.display="block";
 }
 // drag (pointer = mouse + touch): grab the nearest node, pin it to the finger, let the springs pull its neighbours.
 function pt(ev){var r=svg.getBoundingClientRect();return {x:(ev.clientX-r.left)/r.width*W,y:(ev.clientY-r.top)/r.height*H};}
 function near(p){var best=null,bd=1e9;G.nodes.forEach(function(n){var dx=n.x-p.x,dy=n.y-p.y,d=dx*dx+dy*dy;if(d<bd&&d<(n.r+10)*(n.r+10)){bd=d;best=n;}});return best;}
 var drag=null,moved=false,p0=null;
 svg.addEventListener("pointerdown",function(ev){var p=pt(ev),n=near(p);if(n){drag=n;n.fixed=true;moved=false;p0=p;if(svg.setPointerCapture)try{svg.setPointerCapture(ev.pointerId)}catch(e){}reheat();ev.preventDefault();}else{pinned=false;clearFocus();panel.style.display="none";}});
 svg.addEventListener("pointermove",function(ev){if(!drag)return;var p=pt(ev);if(Math.abs(p.x-p0.x)+Math.abs(p.y-p0.y)>4)moved=true;drag.x=p.x;drag.y=p.y;drag.vx=drag.vy=0;focus(drag.id);reheat();ev.preventDefault();});
 function drop(){if(!drag)return;if(!moved)pick(drag);drag.fixed=false;drag=null;reheat();}
 svg.addEventListener("pointerup",drop);svg.addEventListener("pointercancel",drop);
 // search
 document.getElementById("q").addEventListener("input",function(e){var v=e.target.value.trim().toLowerCase();G.nodes.forEach(function(n){var hit=!v||(n.name+" "+n.group).toLowerCase().indexOf(v)>=0;n._g.classList.toggle("dim",!hit)});if(!v)clearFocus();});
 // filter chips + legend
 var chips=document.getElementById("chips"),legend=document.getElementById("legend"),groups=G.legend.map(function(l){return l.group});
 function addChip(label,val){var b=document.createElement("button");b.className="chip";b.textContent=label;b.setAttribute("aria-pressed",val==="__all__"?"true":"false");b.onclick=function(){
   [].forEach.call(chips.querySelectorAll(".chip"),function(c){c.setAttribute("aria-pressed","false")});b.setAttribute("aria-pressed","true");
   G.nodes.forEach(function(n){n._g.classList.toggle("dim",!(val==="__all__"||n.group===val))});G.edges.forEach(function(e){var show=val==="__all__"||e.a.group===val||e.b.group===val;e._l.classList.toggle("dim",!show)});};chips.appendChild(b);}
 addChip("All","__all__");groups.forEach(function(g){addChip(g,g)});
 G.legend.forEach(function(l){var s=document.createElement("span");s.innerHTML='<span class="dot" style="background:'+l.color+'"></span>'+esc(l.group);legend.appendChild(s);});
})();
</script>
</body></html>
"""


def build(root: pathlib.Path | None = None) -> str:
    g = graph(load(root or ROOT))
    data = json.dumps(g, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")                      # never let embedded data close the script tag
    return (_TEMPLATE.replace("__W__", str(g["w"])).replace("__H__", str(g["h"]))
            .replace("__DATA__", data))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = pathlib.Path(argv[0]).expanduser() if argv and not argv[0].startswith("-") else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), "utf-8")
    g = graph(load(ROOT))
    print(f"✔ estate map written: {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print(f"  {sum(1 for n in g['nodes'] if n['kind'] == 'component')} components on {sum(1 for n in g['nodes'] if n['kind'] == 'service')} platform services; open it in a browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
