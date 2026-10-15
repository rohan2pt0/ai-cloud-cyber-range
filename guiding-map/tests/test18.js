// v18: freeze-ready. The quarterly system is taps (grade -> wheel -> pick goals), the rhythm goes into the calendar as one .ics,
// Undo can never roll back days, pausing asks first, kids are added and planned in place, and "integrations" say what they really are.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
function boot(seed){
  const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/",
    beforeParse(w){ if(seed) Object.entries(seed).forEach(([k,v])=>w.localStorage.setItem(k,JSON.stringify(v)));
      w.confirm=()=>false; w.alert=()=>{}; w.scrollTo=()=>{}; w.fetch=()=>Promise.reject(new Error("offline"));
      w.URL.createObjectURL=()=>"blob:x"; }});
  return dom;
}
setTimeout(()=>{
 const w=boot().window, d=w.document, txt=()=>d.getElementById("sections").textContent, ov=()=>d.getElementById("gmOverlay");
 setTimeout(()=>{
  // quarterly check-in with no goals yet: wheel (8 taps) -> choose
  w.gmQuarter();
  ok("check-in starts with the wheel when there are no goals", ov() && ov().textContent.includes("step 2 of 3") && ov().textContent.includes("Career"), ov()&&ov().textContent.slice(0,120));
  [6,4,5,7,6,5,3,6].forEach(v=>ov().querySelector(`[data-v="${v}"]`).click());
  const sug=[...ov().querySelectorAll("[data-i]")].map(x=>x.textContent);
  ok("goals are suggested from the lowest scores first", sug.length>=2 && /joy/i.test(sug[0]) && /money/i.test(sug[1]), sug.join(" | "));
  ov().querySelector('[data-i="0"]').click(); ov().querySelector('[data-i="1"]').click(); ov().querySelector('[data-i="2"]')&&ov().querySelector('[data-i="2"]').click();
  ov().querySelector('[data-i="3"]')&&ov().querySelector('[data-i="3"]').click();
  ok("never more than three goals", d.querySelectorAll("#gmOverlay [data-i].on").length<=3);
  d.getElementById("gmQfin").click();
  ok("goals saved with two measurable results each", w.S.okrs.length>=2 && w.S.okrs.every(o=>o.krs.length===2 && o.krs.every(k=>k.v===0)), JSON.stringify(w.S.okrs).slice(0,200));
  ok("the wheel is saved", w.S.wheel && w.S.wheel.fun===3 && w.S.wheel.career===6, JSON.stringify(w.S.wheel));
  ok("the quarter is marked done", Object.keys(JSON.parse(w.localStorage.getItem("gm_quarter_done"))).length===1);
  ok("after saving, the calendar is offered", ov() && ov().textContent.includes("Add to my calendar"));
  w.gmClose();
  // progress: one tap per result
  w.gmQuarter({gradeOnly:true});
  const n=w.S.okrs.reduce((s,o)=>s+o.krs.length,0);
  for(let i=0;i<n;i++) ov().querySelector('[data-v="0.75"]').click();
  ok("progress is one tap per result", w.S.okrs.every(o=>o.krs.every(k=>k.v===0.75)));
  w.goTab("okr");
  ok("the OKRs tab leads with the check-in and a one-tap progress update", txt().includes("Quarterly check-in done") && txt().includes("Update progress (taps)"));
  ok("the OKR guidance says monthly, not weekly", !txt().includes("grade weekly") && txt().includes("once a month"));
  // calendar file
  const ics=w.gmCalendarICS();
  ok("calendar: five repeating events", (ics.match(/BEGIN:VEVENT/g)||[]).length===5 && (ics.match(/RRULE:/g)||[]).length===5);
  ok("calendar: quarterly event on the first Saturday of Jan/Apr/Jul/Oct", ics.includes("RRULE:FREQ=YEARLY;BYMONTH=1,4,7,10;BYDAY=1SA"));
  ok("calendar: monthly review is the After-Action Review trigger", /SUMMARY:Monthly review: money \+ After-Action Review/.test(ics));
  ok("calendar: CRLF and lines folded", ics.includes("\r\n") && ics.split("\r\n").every(l=>Buffer.byteLength(l)<=75));
  ok("calendar: each event reminds 30 minutes before", (ics.match(/TRIGGER:-PT30M/g)||[]).length===5);
  // AAR is a ritual with a moment
  w.goTab("ops");
  ok("the After-Action Review is a monthly ritual in Ops", txt().includes("Monthly After-Action Review"));
  ok("Ops leads with the check-in and the calendar; advanced tools are folded", txt().indexOf("Quarterly check-in")<txt().indexOf("System health") && !!d.querySelector("#sections details") && txt().includes("Advanced tools"));
  // undo can never roll back days
  w.localStorage.setItem("gm_undo",JSON.stringify({at:Date.now()-10*86400000,label:"old change",data:{}}));
  w.renderAll();
  ok("a 10-day-old undo is never offered (Ops or System health)", !txt().includes("old change"));
  const before=Object.keys(w.S.okrs).length; w.gmUndo();
  ok("…and calling it wipes nothing", JSON.parse(w.localStorage.getItem("sovS")).okrs.length===before && w.localStorage.getItem("gm_undo")===null);
  w.gmSnap("ticked a box"); w.renderAll(); w.goTab("today");
  ok("a fresh undo says what it does and can be dismissed", txt().includes("Undo puts everything back") && !!d.querySelector('[onclick="gmUndoDismiss()"]'));
  w.gmUndoDismiss();
  ok("dismiss removes it", w.localStorage.getItem("gm_undo")===null);
  // recovery asks first
  w.gmRecoveryAsk(7);
  ok("pausing asks first and does nothing yet", !!ov() && !w.localStorage.getItem("gm_recovery"));
  w.gmClose(); w.gmRecoveryOn(7); w.goTab("ops");
  ok("when paused, Ops says until when and offers 'End it now'", txt().includes("Recovery mode is on") && txt().includes("End it now"));
  w.gmRecoveryOff();
  // kids
  w.goTab("kids");
  ok("no children: add one right here", !!d.getElementById("gmKidN"));
  d.getElementById("gmKidN").value="Aarav"; d.getElementById("gmKidD").value="2021-06-14"; w.gmKidAdd();
  ok("the child's plan appears with this quarter's three actions and the education SIP", txt().includes("Aarav") && txt().includes("This quarter") && /Education fund: about .* a month/.test(txt()), txt().slice(0,300));
  const tick=d.querySelector("[onclick^='gmKidTick']"); tick.click();
  ok("an action can be ticked", Object.keys(JSON.parse(w.localStorage.getItem("gm_kid_done"))).length===1);
  // integrations are honest
  w.goTab("growth");
  ok("integrations say they are copy-in boxes", txt().includes("not live connections") && !txt().includes("Auto-fills") && txt().includes("Health Connect"));
  // runway: a lakh field typed in rupees
  w.gmLifeSet("fFixed","80000"); w.gmLifeSet("ef","400000");
  const vit=[...d.querySelectorAll("#gmVitals > div")].map(x=>x.textContent).join(" ");
  ok("runway reads 5.0m, not 274219.5m, when the emergency fund is typed in rupees", vit.includes("5.0m"), vit);
  console.log("PASS",P,"  FAIL",F); if(F){console.log(e.join("\n"));process.exit(1);} process.exit(0);
 },700);
},100);
