// Exercise portal. Every value from the server is put on the page with textContent, never as HTML.
"use strict";
const S = { token: "", me: null, view: "overview", team: null };
const CAT = { availability: "Availability", solve_task: "Solve task", abandon_task: "Abandon task", use_hint: "Use hint",
  attack_reports: "Attack reports", incident_reports: "Incident reports", situation_reports: "Situation reports",
  restore_from_backup: "Restore from backup", rule_breaches: "Rule breaches", special: "Special", total: "Total" };
const COLOR = { availability: "--c-availability", solve_task: "--c-solve", abandon_task: "--c-abandon", use_hint: "--c-hint",
  attack_reports: "--c-attack", incident_reports: "--c-incident", situation_reports: "--c-sitrep", restore_from_backup: "--c-restore",
  rule_breaches: "--c-rules", special: "--c-special", total: "--c-total" };
const SITREP = [["event_overview", "I. Event overview"], ["adversary_assessment", "II. Adversary assessment"],
  ["impact_on_operations", "III. Impact on operations"], ["actions_taken", "IV. Actions taken and results"], ["status", "V. Status"],
  ["other_business", "VI. Any other business"]];
const VIEWS = [
  ["Cyber range", [["overview", "Overview", "all"], ["rules", "Rules", "all"], ["plan", "Team plan", "bw"]]],
  ["Scoring", [["scorelog", "Scoring log", "bw"], ["timeline", "Team timeline", "bw"]]],
  ["Reporting", [["incident", "Incident report", "b"], ["sitrep", "Situation report", "b"], ["myreports", "Our reports", "b"]]],
  ["Judging", [["judge-incident", "Incident reports", "w"], ["judge-sitrep", "Situation reports", "w"], ["judge-task", "Task answers", "w"], ["control", "Exercise control", "w"]]],
  ["Situational awareness", [["targets", "Target checks status", "all"], ["awareness", "Team awareness", "bw"], ["news", "News injects", "all"]]],
  ["Tasks", [["missions", "Mission board", "bw"]]],
  ["Operations", [["creds", "Staff password changes", "bw"], ["restore", "Restore from backup", "b"], ["attack", "Report an attack", "rw"], ["attacks", "Attack reports", "rw"]]],
];

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") e.className = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat(Infinity)) if (k !== null && k !== undefined && k !== false) e.append(k instanceof Node ? k : document.createTextNode(String(k)));
  return e;
}
const $ = (id) => document.getElementById(id);
function store(k, v) { try { if (v === undefined) return sessionStorage.getItem(k); if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v); } catch (_) { return null; } }

async function api(path, body) {
  const q = S.team && S.me && S.me.role !== "blue" ? (path.includes("?") ? "&" : "?") + "team=" + S.team : "";
  const r = await fetch(path + q, { method: body ? "POST" : "GET", headers: { Authorization: "Bearer " + S.token, ...(body ? { "Content-Type": "application/json" } : {}) },
    body: body ? JSON.stringify(body) : undefined });
  const d = await r.json().catch(() => ({ error: "unreadable reply" }));
  if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
  return d;
}
function toast(msg, bad) {
  const t = el("div", { class: "toast " + (bad ? "bad" : ""), role: "status" }, msg);
  document.body.append(t); setTimeout(() => t.remove(), 4000);
}
function allowed(who) { const r = S.me.role[0]; return who === "all" || who.includes(r); }

function nav() {
  const n = $("nav"); n.replaceChildren();
  for (const [group, items] of VIEWS) {
    const vis = items.filter((i) => allowed(i[2]));
    if (!vis.length) continue;
    n.append(el("div", { class: "group" }, group));
    for (const [id, label] of vis) n.append(el("button", { "aria-current": S.view === id ? "page" : null, onclick: () => { go(id); n.classList.remove("open"); } }, label));
  }
}
async function go(view) { S.view = view; store("view", view); nav(); await render(); }

async function render() {
  const m = $("main");
  try {
    const ov = await api("/api/overview");
    $("title").textContent = ov.name;
    $("phase").textContent = ov.phase.name + (ov.phase.minute !== null && ov.phase.minute !== undefined ? " · minute " + Math.floor(ov.phase.minute) : "");
    const body = await (VIEW[S.view] || VIEW.overview)(ov);
    m.replaceChildren(body);
  } catch (e) { m.replaceChildren(el("div", { class: "card bad", role: "alert" }, e.message)); }
}

const card = (title, ...kids) => el("section", { class: "card" }, title ? el("h1", {}, title) : null, ...kids);
const table = (heads, rows) => el("div", { class: "scroll" }, el("table", {}, el("thead", {}, el("tr", {}, heads.map((h) => el("th", { scope: "col" }, h)))),
  el("tbody", {}, rows.length ? rows : [el("tr", {}, el("td", { colspan: heads.length, class: "muted" }, "Nothing yet."))])));
const field = (id, label, input) => [el("label", { for: id }, label), input];
function form(onsubmit, ...kids) {
  return el("form", { onsubmit: async (ev) => { ev.preventDefault(); try { await onsubmit(new FormData(ev.target)); ev.target.reset(); } catch (e) { toast(e.message, true); } } }, ...kids);
}

const VIEW = {
  async overview(ov) {
    const kids = [el("p", {}, ov.phase.about || "")];
    if (ov.totals) kids.push(table(["Category", "Points"], Object.entries(CAT).filter(([k]) => ov.totals[k]).map(([k, v]) => el("tr", {}, el("td", {}, v), el("td", {}, ov.totals[k])))));
    kids.push(el("p", { class: "muted" }, "Signed in as " + S.me.role + (S.me.team ? " team " + S.me.team : "") + ". Data refreshes every 30 seconds."));
    return card(ov.name, ...kids);
  },
  async rules() {
    const r = await api("/api/rules");
    return card("Rules", el("p", {}, "Breaking a rule the range can check costs points every round until it is fixed" + (r.breach_points_per_round ? ` (${r.breach_points_per_round} per breach per round)` : "") + ". Exercise control judges the rest."),
      el("ol", {}, r.rules.map((x) => el("li", {}, x))),
      r.green_team ? [el("h2", {}, "Green-team account: " + r.green_team.username), el("p", {}, r.green_team.about || "")] : null,
      r.checks ? [el("h2", {}, "Checked this round"), r.checks.length ? r.checks.map((c) => el("div", { class: "check" }, el("span", { class: "dot " + (c.ok ? "ok" : "no"), "aria-hidden": "true" }),
        el("span", {}, `${c.host}: ${c.rule}` + (c.ok ? "" : " — BROKEN: " + c.detail)))) : el("p", { class: "muted" }, "No rule checks have run yet.")] : null);
  },
  async plan() {
    const p = await api("/api/plan");
    const blue = S.me.role === "blue";
    const cls = { done: "good", overdue: "bad", blocked: "warn", now: "", later: "muted", "not started": "muted" };
    return card("Team plan", el("p", {}, p.minute === null ? "The clock has not started." : `Minute ${Math.floor(p.minute)}.` +
        (p.checkins_every_minutes ? ` Check-in every ${p.checkins_every_minutes} minutes: next at minute ${p.next_checkin_minute}` +
          (p.last_situation_report_minute !== null ? `; last situation report at minute ${p.last_situation_report_minute}.` : "; no situation report yet.") : "")),
      p.checkin_due ? el("p", { class: "bad", role: "alert" }, "A check-in is due: send a situation report.") : null,
      table(["When (minutes)", "Task", "Owner", "State", blue ? "Mark" : "Note"], p.items.map((i) => el("tr", {},
        el("td", {}, `${i.from_minute}–${i.to_minute}`), el("td", {}, i.task, i.note ? el("div", { class: "muted" }, i.note) : null), el("td", {}, i.owner),
        el("td", { class: "status " + (cls[i.state] || "") }, i.state),
        el("td", {}, blue ? el("div", { class: "row" }, ["done", "blocked", "todo"].map((st) => el("button", { type: "button", class: "secondary",
          onclick: async () => { const note = st === "blocked" ? (prompt("What is blocking it?") || "") : ""; await api(`/api/plan/${i.id}`, { status: st, note }).catch((e) => toast(e.message, true)); render(); } }, st)))
          : (i.by ? `${i.by} ${(i.time || "").slice(11, 16)}` : ""))))));
  },
  async scorelog() {
    const rows = await api("/api/scorelog");
    return card("Scoring log", table(["Time", "Category", "Points", "Detail", "By"], rows.map((r) => el("tr", {},
      el("td", {}, r.time.replace("T", " ").slice(0, 19)), el("td", {}, CAT[r.category] || r.category), el("td", { class: r.points < 0 ? "bad" : "good" }, r.points),
      el("td", {}, Object.entries(r.detail).map(([k, v]) => k + ": " + v).join(", ")), el("td", {}, r.by)))));
  },
  async timeline() {
    const d = await api("/api/timeline");
    const keys = Object.keys(d.series);
    if (!d.times.length) return card("Team scoring timeline", el("p", { class: "muted" }, "No scores yet."));
    const all = keys.flatMap((k) => d.series[k]); const lo = Math.min(0, ...all), hi = Math.max(1, ...all);
    const W = 800, H = 300, P = 40, x = (i) => P + (W - 2 * P) * i / Math.max(1, d.times.length - 1), y = (v) => H - P - (H - 2 * P) * (v - lo) / (hi - lo || 1);
    const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("role", "img"); svg.setAttribute("aria-label", "Cumulative points by category over time");
    const line = (x1, y1, x2, y2, cls) => { const l = document.createElementNS(ns, "line"); for (const [k, v] of Object.entries({ x1, y1, x2, y2, class: cls })) l.setAttribute(k, v); svg.append(l); };
    const text = (tx, ty, s, anchor) => { const t = document.createElementNS(ns, "text"); t.setAttribute("x", tx); t.setAttribute("y", ty); t.setAttribute("text-anchor", anchor || "end"); t.textContent = s; svg.append(t); };
    line(P, y(0), W - P, y(0), "axis"); line(P, P, P, H - P, "axis");
    for (const v of [lo, 0, hi]) text(P - 4, y(v) + 4, Math.round(v));
    text(P, H - P + 16, d.times[0].slice(11, 16), "start"); text(W - P, H - P + 16, d.times[d.times.length - 1].slice(11, 16));
    const cs = getComputedStyle(document.documentElement);
    for (const k of keys) {
      const pl = document.createElementNS(ns, "polyline");
      pl.setAttribute("points", d.series[k].map((v, i) => x(i) + "," + y(v)).join(" "));
      pl.setAttribute("fill", "none"); pl.setAttribute("stroke", cs.getPropertyValue(COLOR[k]).trim()); pl.setAttribute("stroke-width", k === "total" ? 3 : 2);
      svg.append(pl);
    }
    const legend = el("div", { class: "legend" }, keys.map((k) => el("span", {}, el("i", { style: null, "data-c": k }), (CAT[k] || k) + " " + d.series[k][d.series[k].length - 1])));
    legend.querySelectorAll("i").forEach((i) => { i.style.background = cs.getPropertyValue(COLOR[i.dataset.c]).trim(); });
    return card("Team scoring timeline", el("div", { class: "chart" }, svg), legend);
  },
  async targets() {
    const hosts = await api("/api/targets");
    return card("Target checks status", el("div", { class: "grid" }, hosts.map((h) => el("div", { class: "card host" }, el("h3", {}, h.fqdn),
      el("div", { class: "muted" }, h.ip + " · " + h.zone + (h.compromised ? " · compromised" : "")),
      h.checks ? (h.checks.length ? h.checks.map((c) => el("div", { class: "check", title: c.detail }, el("span", { class: "dot " + (!c.ok ? "no" : h.compromised ? "comp" : "ok"), "aria-hidden": "true" }),
        el("span", {}, c.service + (c.ok ? "" : " (down: " + c.detail + ")")))) : el("div", { class: "check" }, el("span", { class: "dot na", "aria-hidden": "true" }), h.deployed ? "No scored services" : "Not deployed in this range"))
        : el("div", { class: "muted" }, h.about)))));
  },
  async awareness() {
    const zs = await api("/api/awareness");
    return card("Team awareness", zs.length ? zs.map((z) => el("div", { style: null }, el("h3", {}, z.label + " — " + z.good_pct + "% good"),
      el("div", { class: "stack", role: "img", "aria-label": `${z.good_pct}% good, ${z.compromised_pct}% compromised, ${z.not_available_pct}% not available` },
        ["good", "compromised", "not_available"].map((k, i) => { const s = el("span", { class: ["bg-good", "bg-comp", "bg-bad"][i] }); s.style.width = z[k + "_pct"] + "%"; return s; }))))
      : el("p", { class: "muted" }, "No checks have run yet."), el("p", { class: "legend" }, el("span", {}, el("span", { class: "dot ok" }), " good"), el("span", {}, el("span", { class: "dot comp" }), " compromised"), el("span", {}, el("span", { class: "dot no" }), " not available")));
  },
  async news() {
    const items = await api("/api/news");
    return card("News injects", items.length ? items.map((n) => el("article", { class: "card" }, el("h2", {}, n.title), el("p", { class: "muted" }, n.time.replace("T", " ").slice(0, 16)), el("p", {}, n.body))) : el("p", { class: "muted" }, "No news yet."));
  },
  async missions() {
    const ts = await api("/api/tasks");
    const phases = [...new Set(ts.map((t) => t.phase))];
    const blue = S.me.role === "blue";
    return card("Mission board", phases.map((p) => el("div", { class: "card" }, el("h2", {}, p), ts.filter((t) => t.phase === p).map((t) => el("div", { class: "card" },
      el("div", { class: "task" }, el("strong", {}, t.points ? t.points + " pts" : "? pts"), el("span", {}, t.title), el("span", { class: "status " + (t.status === "solved" ? "good" : t.status === "abandoned" ? "bad" : "") }, t.status)),
      t.description ? [el("p", {}, t.description), el("p", {}, el("strong", {}, "Question: "), t.question), t.hint ? el("p", { class: "warn" }, "Hint: " + t.hint) : null,
        (t.submissions || []).map((s) => el("p", { class: "muted" }, `${s.time.slice(11, 16)} ${s.actor}: ${s.status}` + (s.points !== null && s.points !== undefined ? ` (${s.points} pts)` : "") + (s.feedback ? " — " + s.feedback : ""))),
        blue && ["open", "validating"].includes(t.status) ? form(async (fd) => { await api(`/api/tasks/${t.id}/submit`, { answer: fd.get("answer") }); toast("Answer sent for judging"); render(); },
          ...field("a-" + t.id, "Your answer", el("textarea", { id: "a-" + t.id, name: "answer", required: true })),
          el("div", { class: "row" }, el("button", { type: "submit" }, "Submit"),
            t.has_hint && !t.hint ? el("button", { type: "button", class: "secondary", onclick: async () => { if (confirm("A hint costs points. Use it?")) { await api(`/api/tasks/${t.id}/hint`, {}).catch((e) => toast(e.message, true)); render(); } } }, "Use hint") : null,
            el("button", { type: "button", class: "secondary", onclick: async () => { if (confirm("Giving up costs points and closes the task. Abandon it?")) { await api(`/api/tasks/${t.id}/abandon`, {}).catch((e) => toast(e.message, true)); render(); } } }, "Abandon"))) : null] : null)))));
  },
  async incident() {
    const hosts = await api("/api/targets");
    return card("Incident report", form(async (fd) => {
      await api("/api/incident", { target: fd.get("target"), compromised: fd.get("compromised") === "yes", chronology: fd.get("chronology"), impact: fd.get("impact"),
        source: fd.get("source"), action_plan: fd.get("action_plan"), additional: fd.get("additional") });
      toast("Incident report sent for judging");
    }, ...field("i-t", "Target", el("select", { id: "i-t", name: "target" }, hosts.map((h) => el("option", { value: h.host }, h.fqdn)))),
      ...field("i-c", "Incident", el("select", { id: "i-c", name: "compromised" }, el("option", { value: "yes" }, "Compromised"), el("option", { value: "no" }, "Not compromised"))),
      ...field("i-ch", "Chronology: what happened and when? Start time, end time if solved, what you observed.", el("textarea", { id: "i-ch", name: "chronology", required: true })),
      ...field("i-im", "Impact: on availability, integrity, confidentiality? None? Not known?", el("textarea", { id: "i-im", name: "impact" })),
      ...field("i-so", "Source: system failure, accident, human error, malicious activity, third party, other?", el("textarea", { id: "i-so", name: "source" })),
      ...field("i-ap", "Action plan: estimated time to recover, steps already taken, what else you plan.", el("textarea", { id: "i-ap", name: "action_plan" })),
      ...field("i-ad", "Additional information: do you need outside help? Attach evidence as text (log lines, commands, hashes).", el("textarea", { id: "i-ad", name: "additional" })),
      el("button", { type: "submit" }, "Submit")));
  },
  async sitrep() {
    return card("Situation report", form(async (fd) => { await api("/api/sitrep", Object.fromEntries(SITREP.map(([k]) => [k, fd.get(k)]))); toast("Situation report sent for judging"); },
      SITREP.map(([k, label]) => field("s-" + k, label, el("textarea", { id: "s-" + k, name: k }))), el("button", { type: "submit" }, "Submit")));
  },
  async myreports() { return reportList(await api("/api/reports"), false); },
  async "judge-incident"() { return reportList(await api("/api/reports?kind=incident"), true); },
  async "judge-sitrep"() { return reportList(await api("/api/reports?kind=sitrep"), true); },
  async "judge-task"() { return reportList(await api("/api/reports?kind=task"), true); },
  async creds() {
    const rows = await api("/api/creds");
    const blue = S.me.role === "blue";
    return card("Staff password changes", el("p", {}, "Staff accounts must keep working. Record every password you change here; the simulated staff use the latest one listed. An undocumented change makes their logins fail and costs availability points."),
      blue ? form(async (fd) => { await api("/api/creds", Object.fromEntries(["username", "system", "password", "reason"].map((k) => [k, fd.get(k)]))); toast("Recorded"); render(); },
        ...field("c-u", "Username", el("input", { id: "c-u", name: "username", required: true })), ...field("c-s", "System (a host name, or \"all\" for an account shared across systems)", el("input", { id: "c-s", name: "system", required: true })),
        ...field("c-p", "New password", el("input", { id: "c-p", name: "password", required: true, autocomplete: "off" })), ...field("c-r", "Reason", el("input", { id: "c-r", name: "reason", required: true })),
        el("button", { type: "submit" }, "Record change")) : null,
      table(["Time", "Username", "System", "New password", "Reason", "By"], rows.map((r) => el("tr", {}, el("td", {}, r.time.slice(11, 16)), el("td", {}, r.username), el("td", {}, r.system), el("td", {}, r.password), el("td", {}, r.reason), el("td", {}, r.actor)))));
  },
  async restore() {
    const hosts = await api("/api/targets");
    return card("Restore from backup", el("p", {}, "Reverting a host to its snapshot costs points. Record it here when you do it (in the lite range, run ./securax exercise revert HOST)."),
      form(async (fd) => { const r = await api("/api/restore", { host: fd.get("host"), reason: fd.get("reason") }); toast("Recorded: " + r.points + " points"); },
        ...field("r-h", "Host", el("select", { id: "r-h", name: "host" }, hosts.map((h) => el("option", { value: h.host }, h.fqdn)))), ...field("r-r", "Why", el("input", { id: "r-r", name: "reason", required: true })),
        el("button", { type: "submit" }, "Record restore")));
  },
  async attack() {
    const hosts = await api("/api/targets");
    return card("Report an attack", el("p", {}, "File one report per objective achieved, with evidence the judges can check."),
      form(async (fd) => { await api("/api/attack", { target: fd.get("target"), objective: fd.get("objective"), evidence: fd.get("evidence") }); toast("Attack recorded"); },
        ...field("k-t", "Target", el("select", { id: "k-t", name: "target" }, hosts.map((h) => el("option", { value: h.host }, h.fqdn)))),
        ...field("k-o", "Objective achieved", el("input", { id: "k-o", name: "objective", required: true })), ...field("k-e", "Evidence", el("textarea", { id: "k-e", name: "evidence" })),
        el("button", { type: "submit" }, "Submit")));
  },
  async attacks() {
    const rows = await api("/api/attacks");
    return card("Attack reports", table(["Time", "Target", "Objective", "Evidence", "By"], rows.map((a) => el("tr", {}, el("td", {}, a.time.slice(11, 16)), el("td", {}, a.target), el("td", {}, a.objective), el("td", {}, el("pre", {}, a.evidence || "")), el("td", {}, a.actor + " (" + a.source + ")")))));
  },
  async control(ov) {
    const v = await api("/api/verify");
    return card("Exercise control", el("p", {}, "Phase: " + ov.phase.name + ". " + (ov.phase.about || "")),
      ov.phase.name === "Not started" ? el("button", { class: "primary", onclick: async () => { if (confirm("Start the exercise clock now?")) { await api("/api/start", {}).catch((e) => toast(e.message, true)); render(); } } }, "Start the clock") : null,
      el("p", { class: v.problems.length ? "bad" : "good" }, v.problems.length ? "Score log problems: " + v.problems.join("; ") : "The score log verifies: no event was edited or removed."),
      el("h2", {}, "Special adjustment"),
      form(async (fd) => { await api("/api/special", { points: Number(fd.get("points")), reason: fd.get("reason") }); toast("Recorded"); },
        ...field("x-p", "Points (negative to deduct)", el("input", { id: "x-p", name: "points", type: "number", step: "1", required: true })), ...field("x-r", "Reason", el("input", { id: "x-r", name: "reason", required: true })),
        el("button", { type: "submit" }, "Apply")));
  },
};

function reportList(subs, judging) {
  const title = judging ? "Judging" : "Our reports";
  return card(title, subs.length ? subs.map((s) => el("article", { class: "card" },
    el("h2", {}, `${s.kind === "sitrep" ? "Situation report" : s.kind === "incident" ? "Incident report: " + s.ref : "Task answer: " + s.ref} · team ${s.team}`),
    el("p", { class: "muted" }, `${s.time.replace("T", " ").slice(0, 16)} by ${s.actor} · ${s.status}` + (s.status !== "pending" ? ` · ${s.points ?? 0} points (${s.verdict})` : "")),
    Object.entries(s.body).map(([k, v]) => [el("h3", {}, k.replace(/_/g, " ")), el("pre", {}, String(v) || "—")]),
    (s.red_reports || []).length ? [el("h3", {}, "What the red team reported on this target"), s.red_reports.map((a) => el("p", {}, `${a.time.slice(11, 16)}: ${a.objective} (${a.source})`))] : null,
    s.feedback ? el("p", {}, el("strong", {}, "Feedback: "), s.feedback) : null,
    judging && s.status === "pending" ? form(async (fd) => { await api("/api/judge/" + s.id, { points: Number(fd.get("points")), verdict: fd.get("verdict"), feedback: fd.get("feedback") }); toast("Judged"); render(); },
      ...field("j-p-" + s.id, s.kind === "sitrep" ? "Grade (0 to 5)" : "Points", el("input", { id: "j-p-" + s.id, name: "points", type: "number", min: "0", step: "1", required: true })),
      ...field("j-v-" + s.id, "Verdict", el("select", { id: "j-v-" + s.id, name: "verdict" }, el("option", { value: "accepted" }, "Accepted"), el("option", { value: "rejected" }, "Rejected"))),
      ...field("j-f-" + s.id, "Feedback to the team", el("textarea", { id: "j-f-" + s.id, name: "feedback" })), el("button", { type: "submit" }, "Judge")) : null)) : el("p", { class: "muted" }, "Nothing here yet."));
}

async function signin(token) {
  S.token = token;
  S.me = await api("/api/me");
  S.team = S.me.team || S.me.teams[0];
  store("token", token);
  $("whoami").textContent = S.me.role + (S.me.team ? " · team " + S.me.team : "");
  $("signout").hidden = false;
  S.view = store("view") || "overview";
  if (!VIEWS.some(([, items]) => items.some((i) => i[0] === S.view && allowed(i[2])))) S.view = "overview";
  nav(); await render();
}

function theme(next) {
  const root = document.documentElement;
  if (next) root.dataset.theme = next; else delete root.dataset.theme;
  try { if (next) localStorage.setItem("theme", next); else localStorage.removeItem("theme"); } catch (_) { /* private window */ }
}

document.addEventListener("DOMContentLoaded", () => {
  try { const t = localStorage.getItem("theme"); if (t) theme(t); } catch (_) { /* ignore */ }
  $("theme").addEventListener("click", () => { const dark = getComputedStyle(document.body).backgroundColor === "rgb(27, 36, 48)"; theme(dark ? "light" : "dark"); if (S.view === "timeline") render(); });
  $("menu").addEventListener("click", () => $("nav").classList.toggle("open"));
  $("signout").addEventListener("click", () => { store("token", null); location.reload(); });
  $("loginform").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    try { await signin($("token").value.trim()); } catch (e) { S.token = ""; $("loginerr").textContent = e.message; }
  });
  const saved = store("token");
  if (saved) signin(saved).catch(() => store("token", null));
  setInterval(() => { if (S.me && !document.querySelector("main form textarea:focus, main form input:focus") && !["incident", "sitrep", "creds", "restore", "attack", "control"].includes(S.view) && !S.view.startsWith("judge")) render(); }, 30000);
});
