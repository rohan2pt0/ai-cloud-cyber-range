// v16: the Command Center (hub.html) over the HTTPS edge: every card link is BY NAME (no port number - ports are not published any more),
// and a stopped service is shown as stopped (the edge answers /_up/<name> with the real status; a 502 must not look "running").
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
function boot(url, status){
  const calls=[];
  const dom=new JSDOM(fs.readFileSync('hub.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url,
    beforeParse(w){w.fetch=(u,o)=>{calls.push(String(u));
      const m=String(u).match(/\/_up\/(\w+)/);
      if(m) return Promise.resolve({status:status[m[1]]??200,ok:true,json:()=>Promise.resolve({})});
      return Promise.resolve({status:200,ok:true,json:()=>Promise.resolve({})});};}});
  return {dom,calls};
}
setTimeout(()=>{
  const s=boot("https://hub.securax.localhost/hub.html",{docs:502,flows:200,chat:200});
  setTimeout(()=>{
    const d=s.dom.window.document, cards=[...d.querySelectorAll('a.card')];
    const hrefs=cards.map(a=>a.getAttribute('href'));
    ok("five cards render", cards.length===5, hrefs.join(" "));
    ok("over HTTPS no card link carries a port number", hrefs.every(h=>h.startsWith("https://")&&!/:\d{2,5}\//.test(h)), hrefs.join(" "));
    ok("Guiding Map and Cockpit are on the hub name", hrefs.includes("https://hub.securax.localhost/")&&hrefs.includes("https://hub.securax.localhost/portal/cockpit.html"), hrefs.join(" "));
    const dot=t=>{const c=cards.find(a=>a.textContent.includes(t));return c.querySelector('.dot').className;};
    ok("a service that answers 502 is shown as NOT running (grey), not green", dot("Private Docs").includes("off"), dot("Private Docs"));
    ok("a service that answers is shown running", dot("Automation").includes("up")&&dot("Chat").includes("up"), dot("Automation")+" | "+dot("Chat"));
    ok("the probe is same-origin through the edge", s.calls.some(c=>c==="/_up/docs"));
    // Plain HTTP serves the SAME /_up/ probe (guiding-map.conf), so status is REAL here too: a down service is shown
    // down (never a false green), a running one is shown running, and the hub's own dot is green because a same-origin
    // response is readable. A down add-on answers 502; Chat answers 200.
    const p=boot("http://localhost:8088/hub.html",{docs:502,chat:200});
    setTimeout(()=>{
      const pcards=[...p.dom.window.document.querySelectorAll('a.card')];
      const h2=pcards.map(a=>a.getAttribute('href'));
      ok("plain-HTTP mode keeps the localhost ports", h2.includes("http://localhost:8088/")&&h2.includes("http://localhost:3000/"), h2.join(" "));
      const pdot=t=>{const c=pcards.find(a=>a.textContent.includes(t));return c.querySelector('.dot').className;};
      ok("plain-HTTP uses the same-origin /_up/ probe", p.calls.some(c=>c==="/_up/docs"), p.calls.join(" "));
      ok("plain-HTTP: a down service is shown NOT running (grey), never a false green", pdot("Private Docs").includes("off"), pdot("Private Docs"));
      ok("plain-HTTP: a running service is shown running (real status, not a guess)", pdot("Chat").includes("up"), pdot("Chat"));
      ok("plain-HTTP: the hub's own dot is green (a same-origin response is readable)", pdot("Guiding Map").includes("up"), pdot("Guiding Map"));
      console.log("PASS",P,"  FAIL",F); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
    },400);
  },600);
},100);
