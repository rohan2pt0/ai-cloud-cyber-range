// Rebuilds the self-contained index.html after editing ops.js.
// Usage: node build.js   (expects index.html to contain the INLINED marker block)
const fs=require("fs");
const html=fs.readFileSync("index.html","utf8");
const ops=fs.readFileSync("ops.js","utf8");
const re=/<!-- ops\.js INLINED below by build\.js[\s\S]*?<\/script>\n<script>\n\/\* Failsafe[\s\S]*?<\/script>/;
if(!re.test(html)){ console.error("Marker block not found \u2014 aborting, nothing changed."); process.exit(1); }
const block=html.match(re)[0];
const rebuilt=block.replace(/(<script>\n)[\s\S]*?(\n<\/script>\n<script>\n\/\* Failsafe)/, "$1"+ops.replace(/\$/g,"$$$$")+"$2");
fs.writeFileSync("index.html", html.replace(re, rebuilt));
console.log("index.html rebuilt with current ops.js ("+ops.length+" chars).");
