// v30: a crafted id in an imported or synced Inbox item cannot break out of the onclick/id attributes it is written into (doc 87),
// and the item can still be decided and deleted.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const evil="x');window.__pwned=1;('";
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/",
  beforeParse(w){ w.confirm=()=>true; w.alert=()=>{}; w.scrollTo=()=>{}; w.fetch=()=>Promise.reject(new Error("offline")); w.URL.createObjectURL=()=>"blob:x";
    w.localStorage.setItem("gm_inbox", JSON.stringify([{id:evil, t:"<img src=x onerror=window.__pwned2=1>", kind:"inbox", created:Date.now()}])); }});
setTimeout(()=>{
  const w=dom.window, d=w.document;
  w.goTab("inbox");
  const html=d.getElementById("sections").innerHTML;
  ok("the crafted id cannot break out of its attribute", html.indexOf("');window")<0, "");
  ok("the item's text is shown as text", !d.querySelector("#sections img[src='x']"));
  const btn=[...d.querySelectorAll("#sections button")].find(b=>/Delete/.test(b.textContent));
  ok("there is a Delete button", !!btn);
  if(btn) btn.click();
  ok("clicking it ran no injected code", !w.__pwned && !w.__pwned2);
  ok("…and the item was deleted", JSON.parse(w.localStorage.getItem("gm_inbox")||"[]").length===0, w.localStorage.getItem("gm_inbox"));
  console.log(`test30 inbox ids: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
},800);
