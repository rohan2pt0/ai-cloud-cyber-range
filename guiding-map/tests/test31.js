// v31: the move to names (doc 99). The old address offers one button; the new address takes data only from a loopback
// address named in its own link, only from its opener, and never overwrites its own data without a yes.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const html=fs.readFileSync('index.html','utf8');
function page(url, before){
  return new JSDOM(html,{runScripts:"dangerously",pretendToBeVisual:true,url,
    beforeParse(w){ w.confirm=()=>true; w.alert=()=>{}; w.scrollTo=()=>{}; w.fetch=()=>Promise.reject(new Error("offline"));
      w.URL.createObjectURL=()=>"blob:x"; if(before) before(w); }});
}
const OLD="http://localhost:8088", NEW="https://hub.securax.localhost";
const a=page(OLD+"/", w=>{ w.localStorage.setItem("gm_goals", JSON.stringify([{id:"g1",t:"Fake goal"}])); });
const sent=[];
const b=page(NEW+"/#gm-move="+encodeURIComponent(OLD), w=>{ w.opener={ postMessage:(m,o)=>sent.push([m,o]) }; });
const c=page(NEW+"/#gm-move="+encodeURIComponent("https://evil.example.invalid"), w=>{ w.opener={ postMessage:(m,o)=>sent.push(["evil",o]) }; });
setTimeout(()=>{
  const wa=a.window, wb=b.window;
  ok("only plain-http loopback addresses may hand data over", wa.gmMoveAllowedFrom(OLD) && wa.gmMoveAllowedFrom("http://127.0.0.1:8088")
     && !wa.gmMoveAllowedFrom("https://evil.example.invalid") && !wa.gmMoveAllowedFrom("http://localhost.evil.example") && !wa.gmMoveAllowedFrom("javascript:x"));
  ok("the old address shows one move button", wa.gmMoveOffer(NEW+"/") && !!wa.document.getElementById("gmMoveBtn"));
  ok("the new address shows no offer to itself", !wb.gmMoveOffer(NEW+"/"));
  ok("the new address asked its opener, at the old origin only", sent.length===1 && sent[0][0].type==="gm-move-ready" && sent[0][1]===OLD, JSON.stringify(sent));
  ok("a link naming a foreign origin is ignored", !sent.some(s=>s[0]==="evil"));
  ok("the link is removed from the address bar", wb.location.hash==="");
  wb.dispatchEvent(new wb.MessageEvent("message",{origin:"https://evil.example.invalid",data:{type:"gm-move-data",data:{gm_x:"1"}}}));
  ok("data from any other origin is refused", wb.localStorage.getItem("gm_x")===null);
  wb.dispatchEvent(new wb.MessageEvent("message",{origin:OLD,data:{type:"gm-move-data",data:{gm_goals:wa.localStorage.getItem("gm_goals"),gm_n:5}}}));
  ok("data from the old address arrives", JSON.parse(wb.localStorage.getItem("gm_goals")||"[]")[0].t==="Fake goal");
  ok("only text values are written", wb.localStorage.getItem("gm_n")===null);
  ok("the old page is told how many moved", sent.some(s=>s[0].type==="gm-move-done" && s[0].n===1 && s[1]===OLD), JSON.stringify(sent));
  console.log(`test31 move to names: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
},900);
