// The 2-minute AI-risk check. Everything runs in the browser: no answer is sent or stored anywhere.
"use strict";
var Q = [
  { q: "Staff may use AI tools only under a written, approved policy.", why: "Without a policy, use goes underground (shadow AI) and nobody can show the board or the regulator what is allowed.", ref: "SEBI CSCRF governance · RBI IT governance", shield: ["amber", "Shield gives the policy a place to be enforced: one endpoint every tool must use."] },
  { q: "You know which AI tools and models your staff actually use.", why: "You cannot assess, contract or monitor a vendor you do not know about.", ref: "NIST AI 600-1 (governance) · RBI third-party risk", shield: ["green", "Every request through Shield is logged with the model that answered it."] },
  { q: "Customer data (PAN, Aadhaar, account and card numbers) is removed before prompts reach any external AI.", why: "Once personal data reaches a public model, you cannot recall it or prove where it went.", ref: "DPDP Act · RBI data protection", shield: ["green", "India-grade redaction of PAN, Aadhaar (checksum-verified), cards, mobiles and e-mail."] },
  { q: "Confidential and regulated data is processed only in India or on your own servers.", why: "Data-localisation rules apply to AI processing as much as to storage.", ref: "RBI data localisation · SEBI CSCRF data localisation", shield: ["green", "Residency routing: confidential classes go only to models in zones you allow."] },
  { q: "Every AI request and answer is logged and kept for audit.", why: "Auditors and incident responders need to see who asked what, and what came back.", ref: "RBI audit trails · SEBI CSCRF logging", shield: ["green", "A structured audit line for every request, block, redaction and route."] },
  { q: "Prompt-injection and jailbreak attempts are detected and blocked.", why: "Attackers hide instructions in documents, e-mails and web pages that your AI then obeys.", ref: "OWASP LLM01 · MITRE ATLAS", shield: ["green", "Prompt-attack rails that fail closed if a detector is down."] },
  { q: "AI answers are checked before they reach customers or systems.", why: "Models can leak data from their context or return unsafe links.", ref: "NIST AI 600-1 (information integrity)", shield: ["green", "Output checks for leaked secrets, canaries and links outside your allow-list."] },
  { q: "AI providers are covered in your third-party risk assessment (data use, training, audit rights).", why: "Most free and consumer AI terms allow your data to be used to improve the service.", ref: "RBI outsourcing directions · SEBI CSCRF third-party risk", shield: ["green", "Multi-provider failover ending on your own model, so no single vendor is unavoidable."] },
  { q: "Access to AI tools is tied to identity and roles, with MFA for privileged users.", why: "Shared keys and anonymous access make every incident impossible to attribute.", ref: "RBI MFA requirements · SEBI CSCRF access control", shield: ["amber", "Per-key roles and OIDC tokens with an MFA-claim check; single sign-on through your identity provider."] },
  { q: "You can report an AI-related cyber incident to CERT-In within 6 hours.", why: "The CERT-In directions set a 6-hour reporting window, and the regulators' own clocks run on top.", ref: "CERT-In directions (2022) · RBI / SEBI reporting", shield: ["green", "A regulator-aware incident clock that tracks every deadline from detection."] }
];
var LIGHT = { green: "Built and proven", amber: "Partly built", red: "Not built yet" };
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function render() {
  var f = document.getElementById("quiz"), h = "";
  Q.forEach(function (x, i) {
    h += '<fieldset class="q"><legend><span class="n">' + (i + 1) + '</span>' + esc(x.q) + '</legend>'
      + '<label><input type="radio" name="q' + i + '" value="1"> Yes</label>'
      + '<label><input type="radio" name="q' + i + '" value="0"> No / not sure</label></fieldset>';
  });
  f.innerHTML = h + '<button class="btn btn-gold" type="submit">See my score</button>';
}
function score(e) {
  e.preventDefault();
  var yes = 0, gaps = [], answered = 0;
  Q.forEach(function (x, i) {
    var v = document.querySelector('input[name="q' + i + '"]:checked');
    if (v) answered++;
    if (v && v.value === "1") yes++; else gaps.push(x);
  });
  var band = yes >= 8 ? ["Strong", "l-g", "You have the basics. The next step is proving it continuously."]
    : yes >= 5 ? ["Partly exposed", "l-a", "Some controls exist, but there are gaps an auditor or attacker would find."]
    : ["Highly exposed", "l-r", "AI use is likely happening without the controls your regulator expects."];
  var out = document.getElementById("result"), h = '<div class="score"><b>' + yes + ' / 10</b><span class="light ' + band[1] + '">' + band[0] + '</span><p>' + band[2] + '</p>'
    + (answered < Q.length ? '<p class="note">Unanswered questions count as gaps.</p>' : '') + '</div>';
  if (gaps.length) {
    h += '<h3>Your gaps, and how Shield helps</h3>';
    gaps.forEach(function (x) {
      h += '<div class="gap"><b>' + esc(x.q) + '</b><p>' + esc(x.why) + '</p><p class="ref">' + esc(x.ref) + '</p>'
        + '<p><span class="light l-' + (x.shield[0] === "green" ? "g" : x.shield[0] === "amber" ? "a" : "r") + '">' + LIGHT[x.shield[0]] + '</span> ' + esc(x.shield[1]) + '</p></div>';
    });
  }
  var subj = encodeURIComponent("AI-risk check: " + yes + "/10 - design partner");
  h += '<p class="cta"><a class="btn btn-gold" href="mailto:{{CONTACT_EMAIL}}?subject=' + subj + '">Get the full gap report in a 30-minute session</a></p>'
    + '<p class="note">Your answers never left this page. This is a self-assessment, not an audit or legal advice.</p>';
  out.innerHTML = h; out.hidden = false; out.scrollIntoView({ behavior: "smooth", block: "start" });
}
document.addEventListener("DOMContentLoaded", function () { render(); document.getElementById("quiz").addEventListener("submit", score); });
