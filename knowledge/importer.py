"""Turn years of AI chats into a private knowledge base you own.

    ./securax knowledge import [PATH ...]   import exports (ZIP, folder or JSON file); no PATH = everything in the inbox
    ./securax knowledge status              what has been imported, and where it is

Reads the official data exports of Claude, ChatGPT, DeepSeek and Gemini (Google Takeout) and writes ONE
markdown file per conversation, ready to upload to Private Docs (or any RAG tool). It is:

  * offline   - nothing is sent anywhere; ZIPs are read in place, never extracted to disk
  * safe      - credentials and critical identifiers (Aadhaar, card numbers, PAN) are redacted before
                anything is written, with the same rules the gateway uses
  * idempotent- run it as often as you like; unchanged conversations are skipped, so a quarterly
                re-export only adds what is new
  * careful   - conversations containing your own "flag terms" (e.g. an employer's name) go to a
                separate `flagged/` folder for you to review before you upload them anywhere

Where the files go: $SECURAX_KNOWLEDGE_DIR, default <estate>/vault/knowledge (git-ignored). Point it at an
encrypted folder (e.g. a Cryptomator vault) if you keep one. Layout:
    inbox/            drop export ZIPs here
    out/<source>/     one .md per conversation          <- upload these
    flagged/<source>/ conversations that matched a flag term (review first)
    out/INDEX.md      every conversation by date, so you can skim titles
    flag-terms.txt    one term per line (case-insensitive); yours, never in the repo
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ("claude", "chatgpt", "deepseek", "gemini")
LABEL = {"claude": "Claude", "chatgpt": "ChatGPT", "deepseek": "DeepSeek", "gemini": "Gemini"}
MAX_MEMBER_BYTES = 2 * 1024 ** 3  # a single JSON file larger than this is refused (memory guard)


def _load_guardrails():
    spec = importlib.util.spec_from_file_location("gw_guardrails", ROOT / "apps/llm-gateway/app/guardrails.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules.setdefault("gw_guardrails", mod)  # dataclasses look the module up while it loads
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


G = _load_guardrails()
# Only identifiers that would be harmful if the archive leaked; e-mail and phone numbers in your own chats stay.
_PII = [r for r in G._PII_RULES if r[0] in {"AADHAAR", "CARD_PAN", "INCOME_TAX_PAN"}]
_SECRETS = list(G._SECRET_PATTERNS) + [
    ("SECRET-api-key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}\b")),
    ("SECRET-bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{20,}")),
    ("SECRET-password", re.compile(r"(?i)\b(pass(?:word|wd)?|pwd)\s*[:=]\s*\S{6,}")),
]


def redact(text: str) -> tuple[str, int]:
    n = 0
    for _rule, rx in _SECRETS:
        text, k = rx.subn("[SECRET_REDACTED]", text)
        n += k
    for label, rx, _sev, validator in _PII:
        def _sub(m: re.Match[str], label=label, validator=validator) -> str:
            nonlocal n
            if validator and not validator(m.group(0)):
                return m.group(0)
            n += 1
            return f"[{label}_REDACTED]"
        text = rx.sub(_sub, text)
    return text, n


# --------------------------------------------------------------------------- model
@dataclass
class Conversation:
    source: str
    id: str
    title: str
    created: datetime | None
    updated: datetime | None = None
    turns: list[tuple[str, str]] = field(default_factory=list)  # (role "user"|"assistant", text)
    kind: str = "chat"  # chat | project


def _dt(v) -> datetime | None:
    if v in (None, ""):
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "p", "li", "div", "tr", "h1", "h2", "h3", "h4", "pre"}:
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)


def html_to_text(s: str) -> str:
    p = _Text()
    p.feed(s or "")
    return re.sub(r"\n{3,}", "\n\n", html.unescape("".join(p.out))).strip()


# --------------------------------------------------------------------------- parsers
def parse_claude(convs: list) -> list[Conversation]:
    out = []
    for c in convs:
        if not isinstance(c, dict):
            continue
        conv = Conversation("claude", str(c.get("uuid") or c.get("id") or ""), c.get("name") or "",
                            _dt(c.get("created_at")), _dt(c.get("updated_at")))
        for m in c.get("chat_messages") or []:
            parts = [b.get("text", "") for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "text"]
            text = "\n\n".join(p for p in parts if p) or m.get("text") or ""
            for a in m.get("attachments") or []:
                if isinstance(a, dict) and a.get("extracted_content"):
                    text += f"\n\n[attachment: {a.get('file_name', 'file')}]\n{a['extracted_content']}"
            role = "user" if m.get("sender") == "human" else "assistant"
            if text.strip():
                conv.turns.append((role, text.strip()))
        out.append(conv)
    return out


def parse_claude_projects(projects: list) -> list[Conversation]:
    out = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        conv = Conversation("claude", "project-" + str(p.get("uuid") or p.get("id") or ""), "Project: " + (p.get("name") or ""),
                            _dt(p.get("created_at")), _dt(p.get("updated_at")), kind="project")
        if p.get("description"):
            conv.turns.append(("note", "Description:\n" + p["description"]))
        if p.get("prompt_template"):
            conv.turns.append(("note", "Project instructions:\n" + p["prompt_template"]))
        for d in p.get("docs") or []:
            if isinstance(d, dict) and d.get("content"):
                conv.turns.append(("note", f"Knowledge file: {d.get('filename', 'document')}\n\n{d['content']}"))
        out.append(conv)
    return out


def _walk_mapping(mapping: dict, current: str | None) -> list[dict]:
    """Return the messages on the conversation's visible branch, oldest first."""
    if current and current in mapping:
        chain, node, seen = [], current, set()
        while node and node in mapping and node not in seen:
            seen.add(node)
            chain.append(mapping[node])
            node = mapping[node].get("parent")
        return list(reversed(chain))
    # No pointer to the visible branch (DeepSeek): start at the root and follow the newest child.
    roots = [n for n in mapping.values() if isinstance(n, dict) and not n.get("parent")]
    chain, node, seen = [], roots[0] if roots else None, set()
    while node and id(node) not in seen:
        seen.add(id(node))
        chain.append(node)
        kids = [mapping[k] for k in node.get("children") or [] if k in mapping]
        node = kids[-1] if kids else None
    return chain


def _chatgpt_text(content: dict) -> str:
    ct = content.get("content_type")
    if ct in {"text", "multimodal_text"}:
        parts = []
        for p in content.get("parts") or []:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict):
                parts.append(p.get("text") or "[image]" if "asset_pointer" in p or p.get("content_type", "").startswith("image") else p.get("text", ""))
        return "\n".join(x for x in parts if x)
    if ct == "code":
        return "```\n" + (content.get("text") or "") + "\n```"
    return ""  # thoughts, tool output, browsing results: not part of what you and the model said


def parse_chatgpt(convs: list) -> list[Conversation]:
    out = []
    for c in convs:
        if not isinstance(c, dict):
            continue
        conv = Conversation("chatgpt", str(c.get("conversation_id") or c.get("id") or ""), c.get("title") or "",
                            _dt(c.get("create_time")), _dt(c.get("update_time")))
        for node in _walk_mapping(c.get("mapping") or {}, c.get("current_node")):
            m = node.get("message") or {}
            role = (m.get("author") or {}).get("role")
            if role not in {"user", "assistant"} or (m.get("metadata") or {}).get("is_visually_hidden_from_conversation"):
                continue
            text = _chatgpt_text(m.get("content") or {})
            if text.strip():
                conv.turns.append((role, text.strip()))
        out.append(conv)
    return out


def parse_deepseek(convs: list) -> list[Conversation]:
    out = []
    for c in convs:
        if not isinstance(c, dict):
            continue
        conv = Conversation("deepseek", str(c.get("id") or ""), c.get("title") or "",
                            _dt(c.get("inserted_at") or c.get("created_at")), _dt(c.get("updated_at")))
        for node in _walk_mapping(c.get("mapping") or {}, c.get("current_node")):
            m = node.get("message") or {}
            frags = m.get("fragments")
            if isinstance(frags, list):
                for f in frags:
                    kind = (f or {}).get("type", "").upper()
                    role = {"REQUEST": "user", "RESPONSE": "assistant"}.get(kind)  # THINK / SEARCH are skipped
                    if role and (f.get("content") or "").strip():
                        conv.turns.append((role, f["content"].strip()))
            elif m.get("role") in {"user", "assistant"} and isinstance(m.get("content"), str) and m["content"].strip():
                conv.turns.append((m["role"], m["content"].strip()))
        out.append(conv)
    return out


def parse_gemini(entries: list) -> list[Conversation]:
    """Takeout's Gemini Apps activity is a flat list of prompts; group them into one note per day."""
    days: dict[str, Conversation] = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        title = e.get("title") or ""
        if not title.startswith("Prompted "):
            continue  # settings changes, feedback, "Used an extension" etc.
        when = _dt(e.get("time"))
        day = when.strftime("%Y-%m-%d") if when else "undated"
        conv = days.setdefault(day, Conversation("gemini", "day-" + day, f"Gemini chats {day}", when, when))
        if when and conv.created and when < conv.created:
            conv.created = when
        conv.turns.append(("user", title[len("Prompted "):].strip()))
        reply = "\n\n".join(html_to_text(i.get("html", "")) for i in e.get("safeHtmlItem") or [] if isinstance(i, dict))
        if reply.strip():
            conv.turns.append(("assistant", reply.strip()))
    convs = list(days.values())
    for c in convs:  # Takeout lists newest first
        pairs = c.turns
        c.turns = []
        i = 0
        groups = []
        while i < len(pairs):
            g = [pairs[i]]
            if i + 1 < len(pairs) and pairs[i + 1][0] == "assistant":
                g.append(pairs[i + 1])
                i += 1
            groups.append(g)
            i += 1
        for g in reversed(groups):
            c.turns.extend(g)
    return convs


# --------------------------------------------------------------------------- detection
def detect(name: str, data) -> str | None:
    """Which export a JSON file belongs to: claude | claude-projects | chatgpt | deepseek | gemini | None."""
    base = re.split(r"[/\\:]", name)[-1].lower()
    if not isinstance(data, list) or not data:
        return None
    first = next((x for x in data if isinstance(x, dict)), None)
    if first is None:
        return None
    if base.startswith("myactivity") and ("gemini" in name.lower() or first.get("header", "").startswith("Gemini")):
        return "gemini"
    if base == "projects.json" and ("docs" in first or "prompt_template" in first):
        return "claude-projects"
    if "chat_messages" in first:
        return "claude"
    if "mapping" in first:
        if "inserted_at" in first or any(isinstance((n or {}).get("message"), dict) and "fragments" in n["message"]
                                         for n in (first.get("mapping") or {}).values() if isinstance(n, dict)):
            return "deepseek"
        return "chatgpt"
    return None


PARSERS = {"claude": parse_claude, "claude-projects": parse_claude_projects, "chatgpt": parse_chatgpt,
           "deepseek": parse_deepseek, "gemini": parse_gemini}


def _json_members(path: Path):
    """Yield (name, parsed JSON) for every JSON file in a ZIP, folder or single file. ZIPs are read in memory."""
    if path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.filename.lower().endswith(".json") and not info.is_dir():
                    if info.file_size > MAX_MEMBER_BYTES:
                        raise ValueError(f"{path.name}:{info.filename} is larger than {MAX_MEMBER_BYTES // 1024 ** 3} GB")
                    with z.open(info) as fh:
                        yield f"{path.name}:{info.filename}", _load_json(io.TextIOWrapper(fh, encoding="utf-8-sig"))
    elif path.is_dir():
        for f in sorted(path.rglob("*.json")):
            with f.open(encoding="utf-8-sig") as fh:
                yield str(f), _load_json(fh)
    elif path.is_file() and path.suffix.lower() == ".json":
        with path.open(encoding="utf-8-sig") as fh:
            yield str(path), _load_json(fh)


def _load_json(fh):
    try:
        return json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def read_export(path: Path) -> tuple[list[Conversation], list[str]]:
    convs, found = [], []
    for name, data in _json_members(path):
        kind = detect(name, data)
        if kind:
            found.append(f"{kind}: {name}")
            convs.extend(PARSERS[kind](data))
    return convs, found


# --------------------------------------------------------------------------- output
def slug(s: str, n: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", s)[:n].strip("-") or "untitled"


def render(c: Conversation) -> tuple[str, int]:
    who = {"user": "You", "assistant": LABEL[c.source], "note": ""}
    date = c.created.strftime("%Y-%m-%d") if c.created else "undated"
    title = (c.title or "").strip() or (c.turns[0][1][:70].replace("\n", " ") if c.turns else "Untitled")
    body = []
    for role, text in c.turns:
        body.append(f"**{who[role]}:**\n{text}" if who[role] else text)
    md = (f"---\nsource: {c.source}\nkind: {c.kind}\nid: {c.id}\ntitle: {json.dumps(title, ensure_ascii=False)}\n"
          f"created: {date}\nupdated: {c.updated.strftime('%Y-%m-%d') if c.updated else date}\nturns: {len(c.turns)}\n---\n\n"
          f"# {title}\n\n*{LABEL[c.source]} · {date} · {len(c.turns)} turns*\n\n" + "\n\n---\n\n".join(body) + "\n")
    return redact(md)


def vault_dir() -> Path:
    return Path(os.environ.get("SECURAX_KNOWLEDGE_DIR") or ROOT / "vault" / "knowledge").expanduser()


def flag_terms(vault: Path) -> list[str]:
    f = vault / "flag-terms.txt"
    if not f.exists():
        return []
    return [t.strip().lower() for t in f.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]


def import_paths(paths: list[Path], vault: Path) -> dict:
    manifest_f = vault / ".manifest.json"
    manifest = json.loads(manifest_f.read_text()) if manifest_f.exists() else {}
    terms = flag_terms(vault)
    stats = {"new": 0, "updated": 0, "unchanged": 0, "empty": 0, "flagged": 0, "redactions": 0, "files": [], "unrecognised": []}
    for p in paths:
        convs, found = read_export(p)
        if not found:
            stats["unrecognised"].append(str(p))
        stats["files"].extend(found)
        for c in convs:
            if not c.turns:
                stats["empty"] += 1
                continue
            md, n = render(c)
            key = f"{c.source}:{c.id}"
            digest = hashlib.sha256(md.encode()).hexdigest()
            flagged = any(t in md.lower() for t in terms)
            date = c.created.strftime("%Y-%m-%d") if c.created else "undated"
            rel = Path("flagged" if flagged else "out") / c.source / f"{date}-{slug(c.title or c.turns[0][1][:60])}-{hashlib.sha1(key.encode()).hexdigest()[:8]}.md"
            prev = manifest.get(key)
            if prev and prev["sha"] == digest and (vault / prev["path"]).exists():
                stats["unchanged"] += 1
                continue
            if prev and prev["path"] != str(rel) and (vault / prev["path"]).exists():
                (vault / prev["path"]).unlink()  # title or flag changed: keep exactly one copy
            (vault / rel).parent.mkdir(parents=True, exist_ok=True)
            (vault / rel).write_text(md, encoding="utf-8")
            stats["updated" if prev else "new"] += 1
            stats["flagged"] += flagged
            stats["redactions"] += n
            manifest[key] = {"sha": digest, "path": str(rel), "date": date, "title": c.title or "", "source": c.source,
                             "flagged": flagged, "turns": len(c.turns)}
    vault.mkdir(parents=True, exist_ok=True)
    manifest_f.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    write_index(vault, manifest)
    return stats


def write_index(vault: Path, manifest: dict) -> None:
    rows = sorted(manifest.values(), key=lambda r: r["date"], reverse=True)
    lines = ["# Your AI conversations — index", "",
             f"{len(rows)} conversations · ⚑ = matched a flag term (in `flagged/`, review before uploading)", "",
             "| Date | Source | Title | Turns | |", "|---|---|---|---|---|"]
    for r in rows:
        t = (r["title"] or "(untitled)").replace("|", "/")
        lines.append(f"| {r['date']} | {LABEL.get(r['source'], r['source'])} | {t} | {r['turns']} | {'⚑' if r['flagged'] else ''} |")
    (vault / "out").mkdir(parents=True, exist_ok=True)
    (vault / "out" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- CLI
def _inbox_items(vault: Path) -> list[Path]:
    inbox = vault / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in inbox.iterdir() if not p.name.startswith("."))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax knowledge", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    imp = sub.add_parser("import", help="import exports (no path = the inbox)")
    imp.add_argument("paths", nargs="*", type=Path)
    imp.add_argument("--quiet", action="store_true", help="print nothing when there is nothing new (for routines)")
    sub.add_parser("status", help="what has been imported")
    a = ap.parse_args(argv)
    vault = vault_dir()

    if a.cmd == "import":
        paths = a.paths or _inbox_items(vault)
        missing = [p for p in paths if not p.exists()]
        if missing:
            print("not found: " + ", ".join(map(str, missing)), file=sys.stderr)
            return 2
        if not paths:
            if not a.quiet:
                print(f"Nothing to import. Drop your export ZIPs into:\n  {vault / 'inbox'}\nthen run: ./securax knowledge import")
            return 0
        s = import_paths(paths, vault)
        if a.quiet and not (s["new"] or s["updated"] or s["unrecognised"]):
            return 0
        for f in s["files"]:
            print(f"  read {f}")
        for u in s["unrecognised"]:
            print(f"  ! not a Claude/ChatGPT/DeepSeek/Gemini export: {u}"
                  + ("  (Gemini: choose JSON, not HTML, in Takeout)" if "takeout" in u.lower() else ""))
        print(f"✔ {s['new']} new, {s['updated']} updated, {s['unchanged']} unchanged"
              + (f", {s['empty']} empty skipped" if s["empty"] else "")
              + (f" · {s['redactions']} secrets/IDs redacted" if s["redactions"] else "")
              + (f" · ⚑ {s['flagged']} flagged for review" if s["flagged"] else ""))
        print(f"  upload from: {vault / 'out'}   (index: {vault / 'out' / 'INDEX.md'})")
        if s["flagged"]:
            print(f"  review first: {vault / 'flagged'}")
        return 1 if s["unrecognised"] and not s["files"] else 0

    if a.cmd == "status":
        mf = vault / ".manifest.json"
        m = json.loads(mf.read_text()) if mf.exists() else {}
        print(f"Knowledge vault: {vault}")
        if not m:
            print(f"  nothing imported yet. Drop exports into {vault / 'inbox'} and run: ./securax knowledge import")
            return 0
        for src in SOURCES:
            rows = [r for r in m.values() if r["source"] == src]
            if rows:
                dates = sorted(r["date"] for r in rows if r["date"] != "undated")
                span = f"{dates[0]} → {dates[-1]}" if dates else "undated"
                fl = sum(r["flagged"] for r in rows)
                print(f"  {LABEL[src]:9} {len(rows):5} conversations  {span}" + (f"  ⚑ {fl} flagged" if fl else ""))
        print(f"  terms flagged from: {vault / 'flag-terms.txt'}" + ("" if (vault / "flag-terms.txt").exists() else "  (not created yet)"))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
