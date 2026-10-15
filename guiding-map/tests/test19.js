// v19: Career compass. Floor, honest CTC, new-regime tax, offers through must-have gates, worst cases, ladder, dated plan in Due now.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const iso=d=>d.toISOString().slice(0,10), ago=n=>{const d=new Date();d.setDate(d.getDate()-n);return iso(d);};
// Dummy profile: a public-sector officer on notice, two offers. Round, made-up numbers.
const prof={cur:{gross:150000,inhand:115000,rent:20000,perks:5000,empRet:14000,empDed:10000,otherYr:150000},
 house:{exp:90000,emi:10000,wife:45000,ef:600000,nw:3000000},
 cfg:{noticeStart:ago(10),noticeMonths:3,birth:"1990-01",fiAge:50},
 offers:[{name:"Regulator · contract manager",ctc:3600000,varPct:0,pf:false,grat:false,health:false,mode:"salary",contract:true,nextPct:25,gates:{rung:"?",field:"y",commute:"y",paper:"y"},scores:{next:2,stable:2}},
  {name:"Private · CISO",ctc:0,varPct:15,basicPct:40,pf:true,grat:true,health:true,mode:"salary",contract:false,nextPct:40,gates:{rung:"y",field:"y",commute:"y",paper:"y"},scores:{next:4,stable:4,team:3}}]};
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/",
  beforeParse(w){ w.localStorage.setItem("gm_career",JSON.stringify(prof)); w.confirm=()=>false; w.alert=()=>{}; w.scrollTo=()=>{}; w.fetch=()=>Promise.reject(new Error("offline")); w.URL.createObjectURL=()=>"blob:x"; }});
setTimeout(()=>{
 const w=dom.window,d=w.document,txt=()=>d.getElementById("sections").textContent;
 // tax: the new regime as printed on a real FY 2026-27 payslip, the rebate line and marginal relief
 ok("tax on 18,39,400 matches a payslip (1,74,595)", w.gmTaxNew(1839400)===174595, w.gmTaxNew(1839400));
 ok("nil tax up to 12L", w.gmTaxNew(1200000)===0);
 ok("marginal relief just above 12L", w.gmTaxNew(1210000)===10400, w.gmTaxNew(1210000));
 ok("salary 36L: in-hand about 2.44L", Math.abs(w.gmOfferPay({ctc:3600000,mode:"salary"}).inh-244542)<5, w.gmOfferPay({ctc:3600000,mode:"salary"}).inh);
 ok("fee income is taxed in full unless 44ADA is ticked", w.gmOfferPay({ctc:3600000,mode:"fee"}).tax>w.gmOfferPay({ctc:3600000,mode:"fee",p44:true}).tax);
 ok("the tab exists and is in the calm set", [...d.querySelectorAll("#tabs button, .tabs button, nav button")].some(b=>/Career/.test(b.textContent)) || w.TABS.some(t=>t[0]==="career"));
 w.goTab("career");
 const t=txt();
 ok("the career section is the visible (active) section", !!d.querySelector("#sections .section.active .sec-t") && /Career compass/.test(d.querySelector("#sections .section.active").textContent));
 ok("break-even CTC for an offer is shown and clears today's value", w.gmOfferPay(Object.assign({},prof.offers[1],{ctc:w.gmMinCtc(1)})).wealth>=164000 && /CTC needed to match today/.test(t));
 ok("today's real value counts rent, perks and retirement (1,64,000)", t.includes("1,64,000"), t.slice(0,400));
 ok("floor adds the health and term cover you will buy (1,68,500)", t.includes("1,68,500"));
 ok("honest CTC excludes brochure items (22.5L)", t.includes("₹22.5L"));
 ok("target is +30% on the honest number (29.2-29.3L)", /Target CTC[^₹]*₹29\.[23]L/.test(t));
 ok("FI corpus and SIP are shown", /corpus\??\s*needed/.test(t) && /SIP\??\s*needed every month/.test(t));
 ok("an unknown CTC means not decidable yet", w.gmCareerVerdict(1).st==="unknown");
 ok("an offer without a CTC asks for it", t.includes("Enter the CTC"));
 ok("worst case: runway is (fund / (expenses + EMIs - spouse))", t.includes("10.9 months"));
 ok("the one-way-door warning names the last day", /One-way door/.test(t) && /withdrawing the resignation before you are relieved/.test(t));
 ok("ladder worked backwards with proof per rung", t.includes("Rung 4") && t.includes("A successor you built"));
 // enter the CISO offer's CTC: pay gate turns green on its own; runway 10.9 < 12 fails the contract, passes permanent
 w.gmCarOffer(1,"ctc",3000000);
 ok("30L with PF, gratuity and 15% variable clears today's value", w.gmCareerVerdict(1).st==="go", JSON.stringify(w.gmCareerVerdict(1)));
 w.gmCarGate(0,"rung"); // ? -> y
 ok("a contract fails survival when runway is under 12 months", w.gmCareerVerdict(0).st==="reject" && w.gmCareerVerdict(0).fail.some(f=>/survive/.test(f)), JSON.stringify(w.gmCareerVerdict(0)));
 w.goTab("career");
 ok("the call names the option that passes", /Private · CISO.*passes every must-have/.test(txt()));
 w.gmCarScore(1,"ai",5); w.gmCarScore(1,"ai",5);
 ok("tapping the same score again clears it", !(JSON.parse(w.localStorage.getItem("gm_career")).offers[1].scores.ai));
 // plan is dated from the notice start and surfaces in Due now
 const due=w.gmCareerDue(7);
 ok("first plan item (offers in writing) is due within a week of notice day 10", due.some(p=>p.id==="offer-paper"), JSON.stringify(due.map(p=>p.id)));
 w.goTab("today");
 ok("Due now shows the career item", txt().includes("CTC breakdown") || d.body.textContent.includes("CTC breakdown"));
 w.gmCarDone("offer-paper");
 ok("ticking it removes it from Due now", !w.gmCareerDue(7).some(p=>p.id==="offer-paper"));
 // gap check toggles
 w.goTab("career"); w.gmCarGap("nums");
 ok("gap tick saves", JSON.parse(w.localStorage.getItem("gm_career")).gaps.nums===true && txt().includes("1 of 8 in place"));
 // add and remove an offer (remove asks first)
 w.gmCarAdd(); const n=JSON.parse(w.localStorage.getItem("gm_career")).offers.length;
 w.gmCarDel(n-1);
 ok("remove asks first", d.getElementById("gmOverlay") && JSON.parse(w.localStorage.getItem("gm_career")).offers.length===n);
 d.getElementById("gmYes").click();
 ok("…and removes after confirming", JSON.parse(w.localStorage.getItem("gm_career")).offers.length===n-1);
 // empty state never throws
 w.localStorage.removeItem("gm_career"); w.goTab("career");
 ok("empty career screen renders with guidance", txt().includes("Fill in today's job") && txt().includes("No offers yet"));
 console.log(`test19: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n")); process.exit(1);}
},1500);
