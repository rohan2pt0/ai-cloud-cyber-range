// v15: one-link sync setup (safe by construction) and automatic server-side backup status.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const b64=o=>Buffer.from(JSON.stringify(o)).toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
function boot(hash, confirms, seed){
  const prompts=[],alerts=[];let i=0;
  const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/"+hash,
    beforeParse(w){if(seed)w.localStorage.setItem("gm_sync_cfg",JSON.stringify(seed));w.confirm=m=>{prompts.push(m);return confirms[Math.min(i++,confirms.length-1)];};w.alert=m=>alerts.push(m);w.fetch=()=>Promise.reject(new Error("offline"));}});
  return {dom,prompts,alerts};
}
const link=b64({url:"https://sync.securax.localhost/sync",key:"tok-abc",user:"me"});
const SAME={url:"https://sync.securax.localhost/sync",key:"tok-abc",user:"me"};
setTimeout(()=>{
 // 1. accepted link sets sync up, the secret leaves the address bar, and the user was told WHERE data goes
 let t=boot("#sync="+link,[true]);
 setTimeout(()=>{
  const w=t.dom.window, c=JSON.parse(w.localStorage.getItem("gm_sync_cfg")||"null");
  ok("accepted link turns sync on", c&&c.url==="https://sync.securax.localhost/sync"&&c.key==="tok-abc"&&c.user==="me", JSON.stringify(c));
  ok("the fragment is removed from the address bar immediately", w.location.hash==="");
  ok("the destination host is shown before saving", t.prompts.length>=1 && t.prompts[0].includes("sync.securax.localhost"), t.prompts[0]);

  // 2. declined link changes nothing
  let d=boot("#sync="+link,[false]);
  setTimeout(()=>{
   ok("declined link sets nothing", d.dom.window.localStorage.getItem("gm_sync_cfg")===null);
   ok("declined link still clears the address bar", d.dom.window.location.hash==="");

   // 3. garbage / hostile links are refused without side effects
   for (const [name,h] of [["not base64 json","#sync=!!!"],["javascript url","#sync="+b64({url:"javascript:alert(1)",key:"k"})],["no key","#sync="+b64({url:"https://x.example/sync"})],["huge key","#sync="+b64({url:"https://x.example/sync",key:"k".repeat(1000)})]]){
     const g=boot(h,[true,true]);
     ok("refused: "+name, g.dom.window.localStorage.getItem("gm_sync_cfg")===null);
   }

   // 4. an existing setup is never replaced without a second, explicit yes
   const pre=boot("",[true]); pre.dom.window.localStorage.setItem("gm_sync_cfg",JSON.stringify({url:"https://old.example/sync",key:"old",user:"me"}));
   const html=fs.readFileSync('index.html','utf8');
   const two=new JSDOM(html,{runScripts:"outside-only",pretendToBeVisual:true,url:"https://hub.securax.localhost/"});
   ok("(sanity) page builds", html.length>1000);
   two.window.close();

   // 4. an existing setup is never replaced without a second, explicit yes
   const old={url:"https://old.example/sync",key:"old",user:"me"};
   const r1=boot("#sync="+link,[true,false],old), r2=boot("#sync="+link,[true,true],old);
   const same=boot("#sync="+link,[true],SAME);
   setTimeout(()=>{
   ok("the SAME setup again (./securax go re-opens the link): no question at all", same.prompts.length===0 && same.alerts.length===0, JSON.stringify(same.prompts));
   ok("existing setup: a second confirmation is asked", r1.prompts.length===2 && r1.prompts[1].includes("already syncing"), JSON.stringify(r1.prompts.map(x=>x.slice(0,40))));
   ok("existing setup is kept when the second answer is no", JSON.parse(r1.dom.window.localStorage.getItem("gm_sync_cfg")).key==="old");
   ok("existing setup is replaced only after two yeses", JSON.parse(r2.dom.window.localStorage.getItem("gm_sync_cfg")).key==="tok-abc");
   },250);

   // 5. automatic server-side backup shows as a green row with a restore path
   const h2=boot("",[true]); const w2=h2.dom.window;
   setTimeout(()=>{
    w2.localStorage.setItem("gm_sync_cfg",JSON.stringify({url:"https://sync.securax.localhost/sync",key:"k",user:"me"}));
    w2.localStorage.setItem("gm_sync_snaps",JSON.stringify({n:12,latest:"2026-10-14"}));
    const ids=w2.TABS.map(x=>x[0]);const oi=ids.indexOf('ops');
    w2.swT(oi>=0?oi:0);
    const txt=w2.document.getElementById('sections').innerHTML;
    ok("automatic backup row appears", txt.includes("Backed up automatically")&&txt.includes("12 daily snapshots"), txt.slice(0,80));
    ok("restore path is offered", txt.includes("gmSnapList()")&&txt.includes('id="snapList"'));
    ok("'never backed up' is not shown while snapshots exist", !txt.includes("No local backup has ever been taken"));
    console.log("PASS",P,"  FAIL",F); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
   },700);
  },300);
 },300);
},400);
