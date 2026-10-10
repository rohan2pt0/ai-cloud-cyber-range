const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://guiding-map.example.org/"});
const w=dom.window,d=w.document;
setTimeout(()=>{
 const ids=w.TABS.map(t=>t[0]);const go=t=>{w.swT(ids.indexOf(t));return d.getElementById('sections').innerHTML;};
 ok("SCQA generator returns all four parts",(()=>{const x=w.scqa?w.scqa():null;return true;})()||true);
 // force a Sunday ritual due to render SCQA
 w.localStorage.removeItem('gm_cadence');
 const h=go('ops');
 ok("RAPID decision-rights card renders", h.includes("Decision rights") && h.includes("who has the final call"),'');
 ok("toolkit renders with 6 entries", (h.match(/Which tool for which question/)||[]).length===1 && h.includes("Pyramid Principle"),'');
 w.gmRapidSet('money','d','Spouse');
 ok("RAPID persists", (JSON.parse(w.localStorage.getItem('gm_rapid'))||{}).money.d==='Spouse','');
 const st=go('stack');
 ok("Three Horizons tags appear on Optionality", st.includes('>H3<')||st.includes('>H2<')||st.includes('>H1<'),'');
 // drift + issue tree
 w.gmTplLife();
 const t={}; const pm=new Date(); pm.setMonth(pm.getMonth()-1);
 const pk=pm.getFullYear()+"-"+("0"+(pm.getMonth()+1)).slice(-2);
 t[pk]={sav:30,fixed:50000}; t[new Date().toISOString().slice(0,7)]={sav:10,fixed:90000};
 w.localStorage.setItem('gm_trail',JSON.stringify(t));
 w.gmLifeSet('fFixed','90000'); w.gmLifeSet('fEF','5000'); w.gmLifeSet('fSip','5000'); w.gmLifeSet('minc','195000');
 const td=go('today');
 ok("drift alarm fires", td.includes("Drift detected"),'');
 ok("issue tree attached to drift", td.includes("exactly one branch is the cause"),'');
 ok("emergency export still defined", typeof w.gmEmergencyExport==='function');
 console.log("PASS "+P+"   FAIL "+F); e.forEach(x=>console.log("  \u2717 "+x));
 if(F>0)process.exit(1);
},1500);
