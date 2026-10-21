// v32: the Command Center answers "what needs me" first (doc 100). Unknown is never "all clear"; red items come first, at most three;
// all clear only with a fresh check; a stale check says so; the feature library is folded away and searchable.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const now=Math.floor(Date.now()/1000);
const M=(id,status,imp,urgent)=>({id,label:"Fake "+id,value:"v-"+id,status,importance:imp,urgent:!!urgent,action:"Fix "+id,cmd:"./securax "+id,why:"because "+id});
function boot(files){
  return new JSDOM(fs.readFileSync('hub.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/hub.html",
    beforeParse(w){ w.eval(fs.readFileSync("features.js","utf8")); w.fetch=(u)=>{ const k=Object.keys(files).find(f=>String(u).endsWith(f));
      if(k) return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(files[k])});
      if(/\/_up\//.test(String(u))) return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve({})});
      return Promise.resolve({ok:false,status:404,json:()=>Promise.resolve({})}); }; }});
}
const T=(d)=>d.window.document.getElementById("postureText").textContent;
const items=(d)=>[...d.window.document.querySelectorAll("#needs li.need")];
const a=boot({}), b=boot({"cockpit.json":{ts:now,metrics:[M("disk","amber",3,true),M("backup","red",5),M("tls","red",2),M("x","red",4),M("y","red",1),M("ok","green",3)]},"repairs.json":{count:2,act:1,top:"Fake backup: none"}}),
      c=boot({"cockpit.json":{ts:now,metrics:[M("ok","green",3),M("ok2","green",2)]}}), s=boot({"cockpit.json":{ts:now-5*86400,metrics:[M("ok","green",3)]}}),
      w=boot({"cockpit.json":{ts:now,metrics:[M("disk","amber",3,true),M("ok","green",3)]}});
setTimeout(()=>{
  ok("no health check means 'Status unknown', never all clear", T(a)==="Status unknown", T(a));
  ok("red items lead: '4 things need you'", T(b)==="4 things need you", T(b));
  const ib=items(b);
  ok("at most three things are shown", ib.length===3, ib.length);
  ok("the most important red comes first, as an action", ib[0].querySelector(".nt").textContent==="Fix backup", ib.map(i=>i.querySelector(".nt").textContent).join(" | "));
  ok("the first item's command is the one primary button", ib[0].querySelector("button.primary")&&!ib[1].querySelector("button.primary"));
  ok("the rest are counted, not listed", /more in the/.test(b.window.document.getElementById("needs").textContent));
  ok("a repair already shown as a metric is not repeated", !ib.some(i=>/^Repair:/.test(i.querySelector(".nt").textContent)));
  ok("only amber means 'Nothing urgent'", T(w)==="Nothing urgent", T(w));
  ok("fresh and all green is 'All clear' with nothing listed", T(c)==="All clear" && items(c).length===0, T(c));
  ok("a stale check says it may be out of date", T(s)==="Status may be out of date", T(s));
  const d=c.window.document;
  ok("the health summary counts without listing on the page", /2 fine/.test(d.getElementById("healthSum").textContent) && !d.getElementById("healthBox").open, d.getElementById("healthSum").textContent);
  ok("the feature library is folded away by default", !d.getElementById("everything").open);
  const all=d.querySelectorAll(".fcard").length, q=d.getElementById("q"); q.value="backup"; q.dispatchEvent(new c.window.Event("input"));
  const shown=[...d.querySelectorAll(".fcard")].filter(x=>!x.hidden).length;
  ok("search narrows the library", all>10 && shown>0 && shown<all, all+" -> "+shown);
  q.value=""; q.dispatchEvent(new c.window.Event("input"));
  // Each card says what gets better (features.json "outcome") and where the person sees it ("shows").
  const FS=c.window.SECURAX_FEATURES.features.filter(f=>!f.service&&f.outcome), f0=FS[0], card=d.getElementById("f-"+f0.id);
  ok("a card shows its outcome", card&&card.querySelector(".o")&&card.querySelector(".o").textContent===f0.outcome, card&&card.textContent);
  ok("a card says where you see it", card&&card.querySelector(".s")&&card.querySelector(".s").textContent==="See it in: "+f0.shows);
  // A word that is in one card's outcome and nowhere else on any card: searching it must find that card.
  const cards=[...d.querySelectorAll(".fcard")];
  const rest=(el)=>{ const x=el.cloneNode(true); x.querySelectorAll(".o").forEach(n=>n.remove()); return x.textContent.toLowerCase(); };
  const others=cards.map(rest).join(" "), outs=cards.map(el=>el.querySelector(".o")?el.querySelector(".o").textContent.toLowerCase():"");
  let hit=null, word=null;
  cards.forEach((el,i)=>{ if(word||!outs[i]) return;
    const wd=(outs[i].match(/[a-z]{6,}/g)||[]).find(x=>others.indexOf(x)<0&&outs.filter((o,j)=>j!==i&&o.indexOf(x)>=0).length===0);
    if(wd){ hit=el; word=wd; } });
  ok("some word appears only in one outcome", !!word);
  if(word){ q.value=word; q.dispatchEvent(new c.window.Event("input"));
    const vis=cards.filter(x=>!x.hidden);
    ok("searching an outcome-only word finds that card", vis.length===1&&vis[0]===hit, word+" -> "+vis.map(x=>x.id).join(","));
    q.value=""; q.dispatchEvent(new c.window.Event("input")); }
  ok("the app launchers are still there", d.querySelectorAll("#apps a.card").length===3 && d.querySelectorAll("#extras a.card").length===2);
  console.log(`test32 command center: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
},900);
