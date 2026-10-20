// v29: online (doc 85). Opened at your own address behind Cloudflare Access, a device pairs its sync by itself: it asks the same
// address who signed in, then syncs with NO token (the sign-in cookie rides along). It never does this on localhost or a
// Tailscale name, never replaces a sync you set up yourself, and stays quiet when nobody signed in (404).
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const html=fs.readFileSync('index.html','utf8');
function boot(url, answer, pre){
  const calls=[];
  const dom=new JSDOM(html,{runScripts:"dangerously",pretendToBeVisual:true,url,
    beforeParse(w){ w.confirm=()=>false; w.alert=()=>{}; w.scrollTo=()=>{}; w.URL.createObjectURL=()=>"blob:x"; w.WebSocket=undefined;
      if(pre) w.localStorage.setItem("gm_sync_cfg", JSON.stringify(pre));
      w.fetch=(u,o)=>{ calls.push({u:String(u),o:o||{}});
        if(String(u).endsWith("/sync/whoami")) return Promise.resolve(answer?{ok:true,json:()=>Promise.resolve(answer)}:{ok:false,status:404,json:()=>Promise.resolve({})});
        if(/\/sync\/state/.test(String(u))) return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve({payload:{},meta:{},snapshots:1})});
        if(/\/sync\/?$/.test(String(u))) return Promise.resolve({ok:true,headers:{get:()=>null}});
        return Promise.reject(new Error("offline")); }; }});
  return {dom,calls};
}
const online=boot("https://hub.example.invalid/", {user:"me", email:"signed-in-owner"});
const local=boot("https://hub.securax.localhost/", {user:"me", email:"signed-in-owner"});
const anon=boot("https://hub.example.invalid/", null);
const mine=boot("https://hub.example.invalid/", {user:"me", email:"signed-in-owner"}, {url:"https://sync.example.invalid/sync", key:"my-own-token", user:"me"});
setTimeout(()=>{
  const c=JSON.parse(online.dom.window.localStorage.getItem("gm_sync_cfg")||"null");
  ok("signed in at your own address: sync pairs itself", c && c.access===true && c.user==="me" && c.url==="https://hub.example.invalid/sync", JSON.stringify(c));
  const puts=online.calls.filter(x=>/\/sync\/state/.test(x.u) && x.o.method==="PUT");
  ok("…and pushes to the same address", puts.length>0 && puts[0].u.indexOf("https://hub.example.invalid/sync/state?user=me")===0, online.calls.map(x=>x.u).join(" "));
  ok("…with no token header (the sign-in cookie is the credential)", puts.every(x=>!("Authorization" in (x.o.headers||{}))));
  ok("never on a .localhost name", !local.calls.some(x=>x.u.endsWith("/sync/whoami")) && !local.dom.window.localStorage.getItem("gm_sync_cfg"));
  ok("nobody signed in (404): nothing is set up", !anon.dom.window.localStorage.getItem("gm_sync_cfg"));
  const m=JSON.parse(mine.dom.window.localStorage.getItem("gm_sync_cfg"));
  ok("a sync you set up yourself is never replaced", m.key==="my-own-token" && !m.access && !mine.calls.some(x=>x.u.endsWith("/sync/whoami")));
  console.log(`test29 online pairing: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n"));process.exit(1);}
  process.exit(0);
},1500);
