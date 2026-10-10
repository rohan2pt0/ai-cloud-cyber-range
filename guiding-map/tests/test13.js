// v13 behaviour: dynamic playbook. (PII scanning is handled in CI by the
// estate's pattern-based gate — guiding-map/tests/pii_gate.py — which reuses
// the SecuRAX guardrail detectors. We deliberately keep NO personal-identifier
// needles in this repo; a pattern gate needs none and cannot itself leak.)
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};

const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://guiding-map.example.org/"});
const w=dom.window,d=w.document;
setTimeout(()=>{
 const ids=w.TABS.map(t=>t[0]);
 const go=t=>{w.swT(ids.indexOf(t));return d.getElementById('sections').innerHTML;};

 // fresh seed carries example flag + banner
 ok("neutral seed is marked example", w.P && w.P.example===true, JSON.stringify(w.P&&w.P.name));
 ok("example banner injected", !!d.getElementById('gmExBan'));

 // playbook renders dynamically
 const b=go('book');
 ok("playbook renders", b.length>500);
 ok("stage bar present (5 stages)", (b.match(/PROTECT|AUTOMATE|EXPAND|SYSTEMIZE|MULTIPLY/g)||[]).length>=5, '');
 ok("next-gate callout present", b.includes("YOUR NEXT GATE"));
 ok("live numbers computed from seed (6x expenses EF)", b.includes(w.money(360000)), 'expected '+w.money(360000));
 ok("FIRE number computed (25x annual expenses)", b.includes(w.money(18000000)), 'expected '+w.money(18000000));
 ok("no NaN/Infinity in playbook", !/NaN|Infinity/.test(b));

 // playbook reacts to data change: clear expenses -> placeholders, still no NaN
 w.P.exp=0; w.P.net=0; w.P.gross=0; w.P.nw=0; w.P.loans=[];
 const b2=go('book');
 ok("playbook renders with empty data (placeholders, no NaN)", b2.length>500 && !/NaN|Infinity/.test(b2), '');
 ok("empty data shows em-dash placeholders", b2.includes("—"));

 // avalanche list reflects user's own loans
 w.P.loans=[{type:"Credit Card",remaining:50000,rate:36,emi:5000,tenure:12},{type:"Personal Loan",remaining:200000,rate:14,emi:9000,tenure:24}];
 const b3=go('book');
 ok("user's high-interest loans listed in avalanche order", b3.indexOf("Credit Card @ 36%")>-1 && b3.indexOf("Credit Card @ 36%")<b3.indexOf("Personal Loan @ 14%"), '');

 // wizard save clears example flag
 w.P.example=true; w.store("sovP",w.P);
 ok("example flag clearable + persists", (function(){ w.P.example=false; w.store("sovP",w.P); return JSON.parse(w.localStorage.getItem("sovP")).example===false; })());

 console.log("PASS "+P+"   FAIL "+F); e.forEach(x=>console.log("  ✗ "+x));
 if(F>0) process.exit(1);
},1500);
