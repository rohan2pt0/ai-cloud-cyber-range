# 51 · Your AI history: years of chats as one library you own

**Problem:** your best answers are spread across Claude, ChatGPT, DeepSeek and Gemini, each in its own app, and
you can only search them inside each vendor's app. **Fix:** export once, then `./securax knowledge import` turns
the exports into one folder of plain markdown, one file per conversation, that Private Docs (or any search tool)
can answer from.

## What is automatic and what is not

| Step | Who | How often |
|---|---|---|
| Ask each vendor for an export | **You** (one button per app; there is no API for chat history) | Once now, then once a quarter if you keep using the vendor apps |
| Download the ZIP into `vault/knowledge/inbox/` | **You** (links expire: Claude and ChatGPT about 24 h, Takeout about 7 days) | Same |
| Read, redact, de-duplicate, write markdown, update the index | **SecuRAX**, the daily routine `knowledge-inbox` (or run it yourself) | Every day at 21:05, silent when nothing is new |
| Upload `out/` into a Private Docs workspace | You, by dragging the folder in | After a large import |

We deliberately do **not** automate the export request with a browser robot: it would have to keep live sessions for four
accounts, would break on every MFA prompt and UI change, and probably breaches the vendors' terms. For the same reason
we do not recommend third-party "exporter" extensions: they need permission to read every chat.

## Where to click (check in the app; menus move)

| App | Path | What you get |
|---|---|---|
| Claude | Settings → Privacy → Export data | e-mailed link to a ZIP of JSON (conversations; projects if present) |
| ChatGPT | Settings → Data controls → Export data | e-mailed link to a ZIP with `conversations.json` |
| DeepSeek | Settings → Data → Export data | a JSON export |
| Gemini | takeout.google.com → deselect all → **My Activity** → activity "**Gemini Apps**" → format **JSON** (not HTML) | ZIP; Takeout can repeat it every 2 months for a year |

## Use

```bash
./securax knowledge import                     # everything in vault/knowledge/inbox
./securax knowledge import ~/Downloads/x.zip   # or name the files
./securax knowledge status                     # how many conversations per source, and the date span
```

Output (`$SECURAX_KNOWLEDGE_DIR`, default `vault/knowledge`, git-ignored; point it at an encrypted folder if you have one):

```
inbox/              drop exports here
out/<source>/       one .md per conversation: title, date, "You:" / "Claude:" turns   <- upload these
out/INDEX.md        every conversation by date, so you can skim titles
flagged/<source>/   conversations containing one of your flag terms: review before uploading anywhere
flag-terms.txt      one term per line, e.g. your employer's name, a project code name (never in the repo)
```

## What it protects

- **Read in place.** ZIPs are read in memory and never extracted, so a crafted archive cannot write files outside the vault.
- **Redaction before writing.** Credentials and the identifiers that would hurt if the archive leaked (Aadhaar, card numbers, PAN) become `[..._REDACTED]`. It uses the gateway's own rules (checksum-verified), plus API keys, bearer tokens and `password=` lines. E-mail addresses and phone numbers in your own chats are kept.
- **Flag, don't guess.** A conversation that mentions a flag term goes to `flagged/`, not `out/`. Use this for an employer's confidential work before anything is uploaded.
- **What is dropped.** Hidden reasoning (DeepSeek "think", ChatGPT "thoughts"), tool output and abandoned branches (the regenerations you did not keep) are not part of what you and the model said.

Re-running is safe. Unchanged conversations are skipped, and a renamed one replaces its old file.

## Where it goes next

- **Ask it privately:** in Private Docs, create the workspace "AI history" and upload `out/`. It answers with the local model only.
- **Distil it once:** the decisions and frameworks worth keeping get folded into your own handbook. Then the history is a reference, not something to reread.
- **Stop the pile-up:** chat through SecuRAX (Open WebUI at `chat.`), so new conversations are stored on your machine from day one.

## Formats and limits

These parsers are written against the formats as published by each vendor in 2025–26, with synthetic test fixtures
(`knowledge/tests`).

If a vendor changes its format, `import` says which file it did not recognise rather than importing it half. Gemini's
Takeout is a flat list of prompts, so it is grouped into one note per day. Uploaded files and generated images are not
in any export; only the text is.
