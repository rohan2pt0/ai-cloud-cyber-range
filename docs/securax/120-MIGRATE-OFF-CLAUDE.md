# Migrate off Claude without losing anything — and run the estate as one workspace

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** A runbook for moving off Claude.ai / Claude Code Pro without losing context: ./securax knowledge import (doc 51) turns your official Claude/ChatGPT/Gemini export into one redacted .md per conversation to upload into Open WebUI Knowledge or AnythingLLM (= your Claude Projects); Open WebUI + Studio become two tabs (home+projects, and code) like Claude, unified by MCP; and your keys are inventoried (./securax keys, queued), consolidated into Vaultwarden, then OpenBao (the Vault already in the estate via grow sprout). Almost every step is zero Claude tokens; the three connective tools are specced for Studio to build on your own models (queue: migration-tools). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The worry this answers:** *"I have years of chats, Projects and uploaded files in Claude.ai and
Claude Code Pro. If I move to the estate I'll lose that context, I'll be juggling three tabs instead
of one, and I've lost track of all the keys I ever made — and I'm short on tokens."*

**The good news:** the estate already has ~80% of what you need. The friction is that it isn't
surfaced, not that it's missing. Almost none of the steps below spend a single Claude token.

| What you use in Claude | What you already have here |
|---|---|
| Claude Code (build) | **Studio** — `./securax studio`, VS Code + Cline (doc 119) |
| Claude home (chat) | **Open WebUI** — `chat.<domain>` |
| Claude Projects (knowledge) | **Open WebUI → Knowledge**, or **AnythingLLM** (`docs.<domain>`) |
| Migrating years of chats | **`./securax knowledge import`** (doc 51) — already built |
| A Vault / KMS for keys | **OpenBao** (open-source HashiCorp Vault) — `./securax grow sprout` |

---

## Part 1 — Migrate your Claude knowledge (today, zero Claude tokens)

1. **Export from Claude.** In Claude.ai → **Settings → Privacy → Export data**. This exports your
   **entire account history — every conversation from the very first day, automatically**; you do
   **not** need to know when you started or pick a date range. Claude emails a download link (it can
   take minutes to hours if you have years of chats); download the ZIP. **Projects:** the project
   *conversations* are in the export, but the **files you uploaded** to a Project usually are not —
   open each Project you care about and **download its files separately**. Keep those originals.
   (Used ChatGPT, Gemini or DeepSeek too? Export each — `knowledge import` reads all of them.)
2. **Turn the export into a private library.**
   ```bash
   ./securax knowledge import ~/Downloads/claude-export.zip
   ```
   It reads the official Claude/ChatGPT/Gemini/DeepSeek export, **redacts** secrets and identifiers
   (PAN/Aadhaar/cards) with the gateway's own rules, and writes **one `.md` per conversation** to
   `vault/knowledge/out/claude/` — offline, idempotent (re-run after each quarterly export; only new
   chats are added). Conversations matching your `flag-terms.txt` go to `flagged/` for you to review
   first. `./securax knowledge status` shows what's in.
3. **Make it searchable = your Claude Projects.** Upload `vault/knowledge/out/claude/*.md` **and** your
   downloaded project files into **Open WebUI → Knowledge** (or an **AnythingLLM** workspace). Now you
   chat over your entire history, privately, on your own models.

**What transfers / what doesn't (honest):** every *conversation and file* — your knowledge — migrates
and becomes searchable. The *live* Claude threads and UI do not (no product can move those). So the
one thing that matters is **doing the export now**: once that ZIP is on disk, nothing is lost.

---

## Part 2 — Two tabs, not three (make it feel like Claude)

The three-tabs friction is role confusion. Assign roles and it drops to two — exactly Claude's
*home + code*:

- **Studio (Cline)** = your **Claude Code**: build, edit, run, git. Via **MCP connectors** it can also
  reach your knowledge and tools *from the same window*.
- **Open WebUI** = your **Claude home + Projects**: chat **and** upload docs for RAG (its *Knowledge*
  feature) **and** MCP connectors — all in one surface.
- **`docs.<domain>` / AnythingLLM is then optional.** That's why it felt useless: if Open WebUI's
  Knowledge covers you, **close that tab**.

**The "one window" trick is MCP.** Wiring your knowledge base, the gateway, the repo filesystem and a
read-only estate-control server as **MCP servers** into Cline (and Open WebUI) lets one agent reach
everything — the closest thing to Claude.ai's single-chat feel. That's a small build; hand it to
Studio (Part 4, tool C).

---

## Part 3 — Your keys, in one place (inventory first, then consolidate)

You already have the hard part — **OpenBao**, the open-source HashiCorp Vault, ships in the estate and
comes up with `./securax grow sprout`. The pragmatic order:

1. **See the sprawl.** Your estate's secrets live in just two places: **`local/compose/.env`** and
   **`~/.securax/`**. The queued `./securax keys` tool (Part 4, tool A) lists every secret — name,
   where it is, what it's for — with values masked, so you can finally *see* what you have.
2. **Consolidate the ones you made by hand** (the API keys, private keys and passwords you can't find)
   into **Vaultwarden** (`./securax start passwords`) — you already run it; it syncs to the Bitwarden
   apps on your phone and laptop.
3. **Graduate to OpenBao** for hands-free, centralized issuance and rotation when you're ready:
   `./securax grow sprout`. That's your KMS/Vault endgame — dynamic secrets, one source of truth.

Immediate rule to stop the bleed: **every new key goes straight into Vaultwarden**, never a sticky
note or a stray `.env` on another machine.

---

## Part 4 — The token-smart path, and the tools to build in Studio (not Claude)

**Almost none of this spends Claude.** `knowledge import`, uploading to Knowledge, `grow sprout`, using
Studio — all **zero Claude tokens**. Reserve Claude Code Pro purely for genuinely hard problems.

The three connective tools that remove the last friction are all **opencode-tier** — build them inside
**Studio/Cline on your own models** (paste each spec after `./securax brief`):

**A. `./securax keys` — the secret inventory.**
> Add `governance/keys.py` and a `keys` command. It scans `local/compose/.env` and `~/.securax/` for
> KEY/SECRET/TOKEN/PASSWORD/PRIVATE-KEY patterns and lists each one: its name, which file/service it
> belongs to, and a one-line purpose — **values always masked** (show only the last 4 chars), never
> printed in full. `--json` for scripts; a `--missing` flag that names which expected keys are unset.
> No write actions in v1 (read-only inventory). Wire into `help` + `selftest`; a test asserts no full
> secret is ever printed; doc it. (A later `--to-vault` exports into Vaultwarden/OpenBao.)

**B. `./securax knowledge import --to-rag` — auto-populate the knowledge base.**
> Extend `knowledge/importer.py` with a `--to-rag` option that, after writing the `.md` files, POSTs
> them into an **Open WebUI Knowledge collection** (or an AnythingLLM workspace) via its local API, so
> import directly fills your searchable base with no manual upload. Keep it offline (same-machine API
> only), idempotent, and secret-redacted as today.

**C. MCP one-window wiring.**
> Add MCP server config so **Cline** (and Open WebUI) connect to: the repo **filesystem**, the
> **gateway** (OpenAI-compatible), the **knowledge base**, and a small **read-only estate-control MCP**
> that wraps safe `./securax status|knowledge status|keys` commands. Result: one Cline window reaches
> code + knowledge + estate. Author the estate-control MCP natively (don't install an unknown
> third-party server).

**Do them in this order of value:** migrate (Part 1) → two tabs (Part 2) → `grow sprout` + tool A
(Part 3) → tools B and C. Everything but the rare hard problem now runs without Claude — which is the
whole point.
