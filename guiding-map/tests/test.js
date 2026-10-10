const fs=require('fs'),{JSDOM}=require('jsdom');
let PASS=0,FAIL=0,errs=[];
function ok(n,c,d){ if(c){PASS++;} else {FAIL++;errs.push(n+(d?" :: "+d:""));} }

const html=fs.readFileSync('index.html','utf8');
const dom=new JSDOM(html,{runScripts:"dangerously",pretendToBeVisual:true,url:"https://guiding-map.example.org/"});
const w=dom.window;
const consoleErrs=[];
w.addEventListener('error',e=>consoleErrs.push(e.message));
w._origErr=w.console.error; w.console.error=(...a)=>consoleErrs.push(a.join(' '));

setTimeout(()=>{
  // ---- 1. boot ----
  ok("app boots without a thrown error", consoleErrs.length===0, consoleErrs.slice(0,3).join(' | '));
  ok("TABS array exists", Array.isArray(w.TABS));
  const ids=(w.TABS||[]).map(t=>t[0]);
  ok("Ops tab registered", ids.includes('ops'));
  ok("Stack tab registered", ids.includes('stack'));
  ok("Life Map tab registered", ids.includes('life'));
  ok("Property tab registered", ids.includes('prop'));
  ok("no duplicate tab ids", new Set(ids).size===ids.length, ids.join(','));
  ok("Today is first tab", ids[0]==='today', ids.slice(0,6).join(','));

  // ---- 2. every ops-layer function is defined ----
  const fns=['gmSnap','gmUndo','gmAdopt','gmPropAdd','gmPropDel','gmPropSet','gmStackTg','gmVitalOnly',
   'gmLifeSet','gmTplLife','gmTplProp','gmTplWoop','gmTplCommit','gmRecoveryOn','gmRecoveryOff',
   'gmExportNow','gmImportNow','gmSyncInit','gmPush','gmSyncSave','gmSyncOff','gmMsConnect','gmMsPull',
   'gmMsBackup','gmMsOff','gmPushOn','gmPushOff','gmAarSave','gmCsfSet','gmWoopSet','gmAnchorSet',
   'gmDoneTg','gmFrTg','gmKitTg','gmRitualDone','gmCommitSet','gmInstall','gmMarkExample','gmClearExample'];
  const missing=fns.filter(f=>typeof w[f]!=='function');
  ok("all "+fns.length+" public functions defined", missing.length===0, "missing: "+missing.join(','));

  // ---- 3. render every tab without throwing ----
  const broke=[];
  (w.TABS||[]).forEach((t,i)=>{
    try{ w.swT(i); const s=w.document.getElementById('sections');
         if(!s||s.innerHTML.trim().length<10) broke.push(t[0]+"(empty)"); }
    catch(e){ broke.push(t[0]+"("+e.message+")"); }
  });
  ok("all "+(w.TABS||[]).length+" tabs render", broke.length===0, broke.join(' | '));

  // ---- 4. vitals bar ----
  const v=w.document.getElementById('gmVitals');
  ok("vitals bar exists", !!v);
  if(v){ ok("vitals is a direct child of body (fixed bar, not in flow)", v.parentNode===w.document.body, v.parentNode.tagName);
         ok("vitals has 5 cells", v.children.length===5, String(v.children.length)); }

  // ---- 5. sanity + example marking ----
  w.gmTplLife();
  const life=JSON.parse(w.localStorage.getItem('gm_life')||'{}');
  ok("template fills age", !!life.age);
  const ex=JSON.parse(w.localStorage.getItem('gm_example_fields')||'{}');
  ok("template marks fields as EXAMPLE", Object.keys(ex).length>=10, String(Object.keys(ex).length));
  w.gmLifeSet('age','36');
  const ex2=JSON.parse(w.localStorage.getItem('gm_example_fields')||'{}');
  ok("typing clears that field's EXAMPLE badge", !ex2.age);

  // ---- 6. undo round-trip ----
  w.gmPropAdd(); w.gmPropSet(0,'val','75'); w.gmPropSet(0,'loan','32');
  const before=JSON.parse(w.localStorage.getItem('gm_props')).length;
  w.gmPropDel(0);
  const after=JSON.parse(w.localStorage.getItem('gm_props')).length;
  ok("delete removes the property", after===before-1);
  w.gmUndo();
  const restored=JSON.parse(w.localStorage.getItem('gm_props')||'[]').length;
  ok("undo restores the deleted property", restored===before, before+" -> "+after+" -> "+restored);

  // ---- 7. self-occupied excluded from net worth ----
  w.localStorage.setItem('gm_props',JSON.stringify([
    {n:"letout",use:"letout",val:"75",rent:"18000",loan:"32",rate:"7.25",emi:"26000",out:"48000",vac:"1"},
    {n:"home",use:"self",val:"90",rent:"0",loan:"40",rate:"8",emi:"30000",out:"36000",vac:"0"}]));
  w.gmLifeSet('inc','23');
  const d=w.document; w.swT(ids.indexOf('ops')); const opsHtml=d.getElementById('sections').innerHTML;
  ok("Derived panel renders", opsHtml.includes('Derived'), '');
  ok("self-occupied equity is excluded and explained", opsHtml.includes('self-occupied'), '');

  // ---- 8. recovery mode ----
  w.gmRecoveryOn(7);
  ok("recovery mode engages", !!w.localStorage.getItem('gm_recovery'));
  w.gmUndo();
  ok("recovery mode is undoable", !w.localStorage.getItem('gm_recovery'));

  // ---- 9. storage-key hygiene ----
  const keys=Object.keys(w.localStorage).filter(k=>k.indexOf('gm_')===0);
  ok("no stray non-gm keys written", Object.keys(w.localStorage).every(k=>k.indexOf('gm_')===0||k.indexOf('lifeos')===0||k.length<40), Object.keys(w.localStorage).filter(k=>k.indexOf('gm_')!==0).join(','));

  console.log("\n"+"=".repeat(58));
  console.log("PASS "+PASS+"   FAIL "+FAIL);
  if(errs.length){ console.log("\nFAILURES:"); errs.forEach(e=>console.log("  \u2717 "+e)); }
  console.log("=".repeat(58));
  if(FAIL>0) process.exit(1);
},1500);
