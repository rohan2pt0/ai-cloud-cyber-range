// v33 (doc 104): items imported from the life workbooks and documents arrive in the Inbox; the vital few (80/20) are shown first and
// the rest folded; an item fixed at the source (listed as resolved) is ticked off, but never one the person captured themselves.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const today=new Date().toISOString().slice(0,10);
const feed={items:[
  {id:"lw-aaaaaaaaaaa1",t:"Set a nominee: Fake Savings Account",kind:"issue",area:"Nominees",due:today,next:"fill the form",from:"workbook",vital:true,score:9},
  {id:"lw-aaaaaaaaaaa2",t:"Add to the emergency binder: Fake Will",kind:"action",area:"Family",due:today,next:"",from:"workbook",vital:false,score:2}],
  resolved:["lw-0ldf1xed0001","ibmine123"],
  papers:{folder:"vault/life/docs",checklist:[{key:"form16",name:"Form 16 (latest year)",why:"income",where:"from HR",have:1},
    {key:"cas",name:"Fake CAS paper",why:"funds",where:"by e-mail",have:0}],figures:{gross_income:1850000,saving_rate_pct:21}}};
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/",
  beforeParse(w){ w.confirm=()=>true; w.alert=()=>{}; w.scrollTo=()=>{}; w.URL.createObjectURL=()=>"blob:x";
    w.fetch=(u)=>String(u).indexOf("inbox-import")>=0?Promise.resolve({ok:true,json:()=>Promise.resolve(feed)}):Promise.reject(new Error("offline"));
    w.localStorage.setItem("gm_inbox",JSON.stringify([
      {id:"lw-0ldf1xed0001",t:"An old imported issue now fixed",kind:"issue",due:today,done:"",from:"workbook",created:1},
      {id:"ibmine123",t:"My own captured action",kind:"action",due:today,done:"",from:"capture",created:1}])); }});
setTimeout(()=>{
  const w=dom.window, d=w.document, inbox=()=>JSON.parse(w.localStorage.getItem("gm_inbox")||"[]");
  const by=id=>inbox().find(x=>x.id===id)||{};
  ok("both imported items arrived", !!by("lw-aaaaaaaaaaa1").id && !!by("lw-aaaaaaaaaaa2").id, JSON.stringify(inbox().map(x=>x.id)));
  ok("the item fixed at the source is ticked off", !!by("lw-0ldf1xed0001").done);
  ok("an item the person captured is never ticked off by an import", !by("ibmine123").done);
  w.goTab("inbox");
  const sec=d.getElementById("sections"), html=sec.innerHTML;
  ok("the vital few come first", [...sec.querySelectorAll("h3")].some(h=>/^The vital few/.test(h.textContent.replace(/\s+/g," ").trim()) && /\(1\)/.test(h.textContent)) && html.indexOf("Fake Savings Account")<html.indexOf("All other actions"), "");
  ok("the rest are folded, one click away", !!sec.querySelector("details.ibnotes") && html.indexOf("All other actions (")>=0);
  ok("the Inbox section is visible (active)", !!sec.querySelector(".section.active"));
  ok("your papers: the count, the next one to collect, and the figures read", /Your papers \(1 of 2 in\)/.test(sec.textContent) && /Next: Fake CAS paper/.test(sec.textContent)
     && /18,50,000/.test(sec.textContent) && /21%/.test(sec.textContent), sec.textContent.slice(0,300));
  console.log(`test33 life import: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
},2600);
