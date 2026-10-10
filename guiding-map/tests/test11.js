// v11-specific behaviour checks
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://guiding-map.example.org/"});
const w=dom.window,d=w.document;
setTimeout(()=>{
 const ids=w.TABS.map(t=>t[0]);const go=t=>{w.swT(ids.indexOf(t));return d.getElementById('sections').innerHTML;};
 // EMA seeds from history and shows on Today
 const y=new Date();y.setDate(y.getDate()-1);
 const dk=w.dKey(y); w.S.daily[dk]=["ex","mf","fm"]; w.localStorage.removeItem("gm_ema");
 go('today'); const t=d.getElementById('sections').innerHTML;
 ok("habit-strength bars render on Today", t.includes("strength "), '');
 const ema=JSON.parse(w.localStorage.getItem('gm_ema')||'{}');
 ok("EMA state persisted with per-habit scores", ema.s && Object.keys(ema.s).length>=3, JSON.stringify(ema.s||{}).slice(0,60));
 // AAR save feeds resurfacing
 go('ops');
 d.getElementById('aar4').value="Route half of every raise to investment first";
 w.gmAarSave();
 const q=JSON.parse(w.localStorage.getItem('gm_resurface')||'[]');
 ok("AAR lesson queued for resurfacing", q.length===1 && q[0].iv===7, JSON.stringify(q));
 // due lesson surfaces and ladder expands
 q[0].due="2020-01-01"; w.localStorage.setItem('gm_resurface',JSON.stringify(q));
 go('today');
 ok("due lesson card appears", d.getElementById('sections').innerHTML.includes("still true?"), '');
 w.gmResAns(0,true);
 const q2=JSON.parse(w.localStorage.getItem('gm_resurface'))[0];
 ok("'still holds' doubles the interval", q2.iv===14, String(q2.iv));
 // integrity guard string present + emergency export defined
 ok("sync integrity guard compiled in", w.gmSyncInit && fs.readFileSync('ops.js','utf8').includes("merge refused"));
 ok("spouse emergency export defined", typeof w.gmEmergencyExport==='function');
 // derived panel carries assumptions + tax stamp
 w.gmTplLife(); const dh=go('ops');
 ok("assumption honesty + Budget 2026 stamp in Derived", dh.includes("Budget 2026") && dh.includes("stress-test at 9"), '');
 console.log("PASS "+P+"   FAIL "+F); e.forEach(x=>console.log("  \u2717 "+x));
 if(F>0)process.exit(1);
},1500);
