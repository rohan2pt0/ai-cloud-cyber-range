// v17: CALM MODE. The default Today is one screen: tap check-in, the one open action, what is due, one insight worked out for you,
// and what the estate already knows. Setup is four questions written once into both data models. Everything else stays one tap away.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
function boot(seed, fetcher){
  const calls=[];
  const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/",
    beforeParse(w){ if(seed) Object.entries(seed).forEach(([k,v])=>w.localStorage.setItem(k,JSON.stringify(v)));
      w.confirm=()=>false; w.alert=()=>{}; w.scrollTo=()=>{};
      w.fetch=(u,o)=>{calls.push([String(u),o]); return fetcher?fetcher(String(u),o):Promise.reject(new Error("offline"));}; }});
  return {dom,calls};
}
const feed={generated:"2026-10-14T22:00",items:[{icon:"!",level:"act",text:"Latest backup: Take a backup now",cmd:"./securax backup"},{icon:"*",level:"info",text:"Certification now: CPTS",cmd:"./securax certs next"}]};
const fetchFeed=(u)=>u.endsWith("/portal/estate-feed.json")?Promise.resolve({ok:true,json:()=>Promise.resolve(feed)}):Promise.reject(new Error("offline"));
setTimeout(()=>{
 const t=boot(null,fetchFeed);
 setTimeout(()=>{
  const w=t.dom.window,d=w.document,txt=()=>d.getElementById("sections").textContent;
  ok("Calm mode is the default on Today", d.body.classList.contains("gm-calm") && txt().includes("worked out for you"));
  ok("the three guidance banners and the duplicate numbers are hidden in calm", ["gmLost","stageBar","hstats"].every(id=>{const el=d.getElementById(id);return !el||w.getComputedStyle(el).display==="none";}));
  ok("the Live Insights wall is folded away", d.querySelector(".iw").classList.contains("gm-hide"));
  const vis=[...d.querySelectorAll("#tabBar .tab")].filter(x=>x.style.display!=="none").map(x=>x.textContent);
  ok("only 5 tabs + More are shown", vis.length===6 && vis[vis.length-1].startsWith("More"), vis.join("|"));
  ok("no daily duplicate: the 5-habit list with anchors and science text is not repeated", !txt().includes("The science:") && !txt().includes("daily check-in (5 pts each)"));
  ok("one setup strip replaces the three example banners", txt().includes("Four quick questions") && !txt().includes("fields still hold example numbers"));
  ok("from your estate: the feed is shown with its commands, no typing", txt().includes("From your estate") && txt().includes("./securax certs next"), txt().slice(-500));
  ok("the feed is fetched same-origin", t.calls.some(c=>c[0]==="/portal/estate-feed.json"));

  // energy tap: one tap stores, a second tap clears
  w.gmEnergy(4);
  const k=w.dKey(new Date());
  ok("energy is one tap", JSON.parse(w.localStorage.getItem("gm_energy"))[k]===4);
  w.gmEnergy(4);
  ok("tapping the same value again clears it", !(k in JSON.parse(w.localStorage.getItem("gm_energy"))));

  // quick setup: four questions, one at a time, written into BOTH models, example markers cleared
  w.gmQuickSetup();
  const answer=(v)=>{const i=d.getElementById("gmQin"); i.value=v; d.getElementById("gmQok").click();};
  ok("question 1 of 4 is a single field", d.querySelectorAll("#gmOverlay input").length===1 && d.getElementById("gmOverlay").textContent.includes("1 of 4"));
  answer("38"); answer("180000");
  d.getElementById("gmQskip").click();         // skip spending
  answer("2500000");
  const L=JSON.parse(w.localStorage.getItem("gm_life")), Pp=JSON.parse(w.localStorage.getItem("sovP")), ex=JSON.parse(w.localStorage.getItem("gm_example_fields")||"{}");
  ok("age and take-home land in the Life Map", L.age==="38" && L.minc==="180000", JSON.stringify(L));
  ok("take-home and net worth land in the profile too (asked once, used twice)", Pp.net===180000 && Pp.nw===2500000 && Pp.example===false, JSON.stringify(Pp));
  ok("net worth is converted to the Life Map's lakh unit", L.nw==="25", L.nw);
  ok("the answered fields are no longer marked EXAMPLE", !ex.age && !ex.minc && !ex.nw, JSON.stringify(ex));
  ok("a skipped question changes nothing", Pp.exp===60000, String(Pp.exp));
  ok("after setup the strip is gone for good", !txt().includes("Four quick questions"));
  ok("invented example people and loans no longer steer YOUR insights", !("sage" in L) && !("k1" in L) && !("page" in L) && Pp.loans.length===0 && Object.keys(ex).length===0, JSON.stringify(ex));
  ok("household income is estimated from take-home (editable, not example)", L.inc==="21.6", L.inc);

  // week summary computed from taps, never asked
  const S=w.S; const today=w.dKey(new Date()); S.daily[today]=["ex","mf"]; w.renderAll();
  ok("the week is summarised from check-ins, counting only days since you started", /Check-ins over your first 1 day: 40%/.test(txt()), (txt().match(/Check-ins[^\n]{0,60}/)||[""])[0]);
  ok("nothing is called 'slipping' after a single day", !txt().includes("Slipping"));

  // show everything / back
  w.gmCalm(false);
  ok("'Show everything' restores the full Today", !d.body.classList.contains("gm-calm") && txt().includes("daily check-in"));
  ok("…with a way back", !!d.getElementById("gmCalmBack"));
  w.gmCalm(true);
  ok("…and back to calm", d.body.classList.contains("gm-calm") && !d.getElementById("gmCalmBack"));

  // AI week review: goes to the estate gateway only, ID numbers in notes never sent
  const r=boot({gm_notes:{[k]:"great run with the kids", "2000-01-01":"x"}},(u,o)=>u.endsWith("/v1/chat/completions")?Promise.resolve({ok:true,json:()=>Promise.resolve({choices:[{message:{content:"Worked: Move. Next week: smaller Read floor."}}]})}):Promise.reject(new Error("offline")));
  setTimeout(()=>{
   const rw=r.dom.window;
   const notes=JSON.parse(rw.localStorage.getItem("gm_notes")); const fakeId=["ABCPE","1234","F"].join("");   // built at runtime: no ID-shaped literal ships (the PII gate scans this file)
   notes[rw.dKey(new Date())]="great run, PAN "+fakeId+" renewed"; rw.localStorage.setItem("gm_notes",JSON.stringify(notes));
   rw.gmWeekReview();
   setTimeout(()=>{
    const call=r.calls.find(c=>c[0].endsWith("/v1/chat/completions"));
    ok("the review goes to the estate gateway", !!call && call[0].startsWith("https://api.securax.localhost"), call&&call[0]);
    ok("a note containing an ID number is not sent", call && !call[1].body.includes(fakeId), call&&call[1].body.slice(0,200));
    ok("the answer is shown on Today", rw.document.getElementById("sections").textContent.includes("smaller Read floor"));
    // unreachable gateway: honest message, the local summary stays
    const o=boot(null,()=>Promise.reject(new Error("offline")));
    setTimeout(()=>{ o.dom.window.gmWeekReview(); setTimeout(()=>{
      const s=o.dom.window.document.getElementById("sections").textContent;
      ok("unreachable estate AI is said plainly; the on-device summary remains", s.includes("not reachable") && s.includes("No check-ins yet"), s.slice(0,300));
      console.log("PASS",P,"  FAIL",F); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
    },300);},500);
   },400);
  },600);
 },700);
},100);
