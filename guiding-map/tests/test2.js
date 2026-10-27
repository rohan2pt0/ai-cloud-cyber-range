const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[]; const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),
  {runScripts:"dangerously",pretendToBeVisual:true,url:"https://guiding-map.example.org/"});
const w=dom.window, d=w.document;
setTimeout(()=>{
 const ids=w.TABS.map(t=>t[0]);
 const go=t=>{w.swT(ids.indexOf(t));return d.getElementById('sections').innerHTML;};

 // ---- XSS: user-controlled strings ----
 const X='"><img src=x onerror=alert(1)>';
 w.localStorage.setItem('gm_props',JSON.stringify([{n:X,use:"letout",val:"75",rent:"1",loan:"1",rate:"7",emi:"1",out:"1",vac:"0"}]));
 w.gmWoopSet('w',X); w.gmCommitSet('who',X);
 go('prop');
 ok("property name is escaped (no live element, no unescaped markup)",
    d.getElementById('sections').querySelectorAll('img,script').length===0
    && !d.getElementById('sections').innerHTML.includes('"><img'), '');
 ok("no injected img element in Property", d.getElementById('sections').querySelectorAll('img[src="x"]').length===0);
 h=go('ops');
 ok("WOOP text is escaped", d.getElementById('sections').querySelectorAll('img[src="x"]').length===0);

 // ---- extreme numeric inputs must not produce NaN/Infinity in the UI ----
 const bad=[["val","0"],["val","999999999"],["rent","0"],["emi","0"],["vac","13"],["vac","-5"],["loan","0"],["rate","0"]];
 let nan=[];
 bad.forEach(([k,v])=>{
   w.localStorage.setItem('gm_props',JSON.stringify([{n:"t",use:"letout",val:"75",rent:"18000",loan:"32",rate:"7.25",emi:"26000",out:"48000",vac:"1"}]));
   w.gmPropSet(0,k,v);
   const s=go('prop');
   if(/NaN|Infinity|undefined%|\u20b9NaN/.test(s)) nan.push(k+"="+v);
 });
 ok("no NaN/Infinity leaks in Property for 8 extreme inputs", nan.length===0, nan.join(','));

 // ---- Life Map extremes ----
 let nan2=[];
 [["age","0"],["age","999"],["inc","0"],["nw","-500"],["k1","0"],["k1","30"],["edu","0"],["minc","0"],["ef","0"]].forEach(([k,v])=>{
   w.gmLifeSet(k,v); const s=go('life');
   if(/NaN|Infinity/.test(s)) nan2.push(k+"="+v);
 });
 ok("no NaN/Infinity leaks in Life Map for 9 extreme inputs", nan2.length===0, nan2.join(','));

 // ---- unit-confusion warning actually fires ----
 w.gmLifeSet('inc','7500000');
 ok("unit-confusion warning shown for lakh field", go('life').includes('Did you type rupees'), '');
 w.gmLifeSet('minc','2');
 ok("unit-confusion warning shown for per-month field", go('life').includes('Did you type lakh'), '');
 w.gmLifeSet('inc','23'); w.gmLifeSet('minc','195000');

 // ---- an impossible age is CLAMPED in the math, not just warned about ----
 // (saneWarn told you 200 was off but the arithmetic still used 200; saneNum caps it so it can't.)
 w.localStorage.clear();
 w.gmLifeSet('age','200'); w.gmLifeSet('inc','23');
 let lifeH=go('life');
 ok("an out-of-range age still shows the range warning", /outside the usual range/.test(lifeH), '');
 ok("an impossible age is capped in the benchmark (age 100), never used as 200",
    /age 100/.test(lifeH) && !/age 200/.test(lifeH), (lifeH.match(/age \d+/g)||[]).join(','));

 // ---- an impossible saving rate is flagged, never shown as a nonsense % ----
 // fEF+fSip (70k/mo) over a 10k/mo income computes to 700% — a data slip, not a real rate.
 w.localStorage.clear();
 w.gmLifeSet('minc','10000'); w.gmLifeSet('fEF','50000'); w.gmLifeSet('fSip','20000'); go('life');
 const vh=d.getElementById('gmVitals').innerHTML;
 ok("an impossible saving rate shows 'check', not a nonsense percentage",
    /check/.test(vh) && !/700%/.test(vh), vh.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').slice(0,120));

 // ---- sync: an unreachable estate is a calm 'working offline', a real refusal is an alarm ----
 w.localStorage.clear();
 // values are stored the way the app stores them (JSON), so the health screen reads them back.
 w.localStorage.setItem('gm_sync_cfg',JSON.stringify({url:"https://estate.example.org/sync",key:"k",user:"u"}));
 w.localStorage.setItem('gm_sync_last',JSON.stringify('2026-10-01 09:00')); w.localStorage.setItem('gm_sync_fails','5');
 w.localStorage.setItem('gm_sync_lastfail',JSON.stringify('unreachable'));
 let opsH=go('ops');
 ok("an unreachable estate reads as a calm 'working offline', not a scary failure count",
    /Working offline/.test(opsH) && !/pushes are failing/.test(opsH), opsH.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').match(/.{0,60}(offline|refused|pushing|failing).{0,40}/i)||'no sync row');
 w.localStorage.setItem('gm_sync_lastfail',JSON.stringify('rejected'));
 ok("a real refusal (the estate is up but rejects us) is surfaced as needing attention",
    /being refused/.test(go('ops')), '');

 // ---- empty states on every tab (fresh storage) ----
 w.localStorage.clear();
 let empties=[];
 ids.forEach(t=>{ try{const s=go(t); if(!s||s.trim().length<10) empties.push(t);}catch(err){empties.push(t+"!"+err.message);} });
 ok("all "+ids.length+" tabs render on empty storage", empties.length===0, empties.join(','));

 // ---- vitals show placeholders, never NaN, on empty storage ----
 const v=d.getElementById('gmVitals');
 ok("vitals render on empty storage without NaN", v && !/NaN|Infinity/.test(v.innerHTML), v?v.textContent.replace(/\s+/g,' ').slice(0,70):'missing');

 // ---- accessibility ----
 const tabs=[...d.querySelectorAll('.tab')];
 ok("tabs are keyboard reachable", tabs.length>0 && tabs.every(t=>t.hasAttribute('tabindex')||t.tagName==='BUTTON'), tabs.filter(t=>!t.hasAttribute('tabindex')).length+" without tabindex");
 const cells=v?[...v.children]:[];
 ok("vitals cells are keyboard reachable", cells.length>0 && cells.every(c=>c.hasAttribute('tabindex')||c.tagName==='BUTTON'), cells.filter(c=>!c.hasAttribute('tabindex')).length+" without tabindex");

 console.log("\n"+"=".repeat(58)+"\nPASS "+P+"   FAIL "+F);
 if(e.length){console.log("\nFAILURES:");e.forEach(x=>console.log("  \u2717 "+x));}
 console.log("=".repeat(58));
 if(F>0) process.exit(1);
},1500);
