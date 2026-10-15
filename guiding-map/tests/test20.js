// v20: sync converges. On an exact timestamp tie the PWA must pick the same winner as estate-sync (larger value by Unicode code point,
// i.e. Python's str order), or two devices keep different values for the same key for ever.
const fs=require('fs'),{JSDOM}=require('jsdom');
let P=0,F=0,e=[];const ok=(n,c,d)=>{c?P++:(F++,e.push(n+(d?" :: "+d:"")));};
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{runScripts:"dangerously",pretendToBeVisual:true,url:"https://hub.securax.localhost/",
  beforeParse(w){ w.confirm=()=>false; w.alert=()=>{}; w.scrollTo=()=>{}; w.fetch=()=>Promise.reject(new Error("offline")); w.URL.createObjectURL=()=>"blob:x"; }});
setTimeout(()=>{
 const w=dom.window, cp=w.gmCpAfter;
 ok("the tie-break is exported", typeof cp==="function");
 // pairs and the answer Python gives for a > b (code point order)
 const cases=[["b","a",true],["a","b",false],["ab","a",true],["a","ab",false],["x","x",false],
   ["\u{1F600}","￿",true],["￿","\u{1F600}",false],          // emoji vs a high BMP char: JS's own < gets this backwards
   ["₹2,00,000","₹10,000",true],['{"a":1}','{"a":2}',false]];
 cases.forEach(([a,b,want])=>ok(`cpAfter(${JSON.stringify(a)}, ${JSON.stringify(b)}) === ${want}`, cp(a,b)===want, cp(a,b)));
 ok("never both directions", cases.every(([a,b])=>!(cp(a,b)&&cp(b,a))));
 console.log(`test20 sync tie-break: ${P} passed, ${F} failed`); if(F){console.log(e.join("\n"));process.exit(1);}
},400);
