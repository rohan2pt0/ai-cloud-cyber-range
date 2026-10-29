# Catch me up, and saved prompts — your own data, summarised on your models

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Two AI-UX wins from the Mattermost study, pointed at your own estate on your own models: ./securax catchup gives one short brief of what needs you now (overdue findings/risks/routines, the one next step, Life OS rhythm) — the 'act today' ground truth is always shown, a model summary rides on top only when a gateway is up (rails+allowance+audit), zero input; and ./securax ask <agent> --prompt NAME runs saved, parametrised prompts (standup, decide, threat-brief, explain-plainly) with {date}/{owner}/{extra} filled in. Tests: test_catchup.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Two small AI-UX wins borrowed from the way Mattermost's assistant summarises a channel and keeps reusable prompts — but
pointed at **your own estate** and run on **your own models**, so nothing leaves your box beyond the one gateway call you
already trust for chat.

## `./securax catchup` — what needs you right now

```bash
./securax catchup          # the brief
./securax catchup --json   # the gathered signals (for a routine or the Life OS)
```

It reads only what the estate already knows, on this machine, and gives you one short brief:

- **Act today** — the things that are genuinely overdue or red: an overdue finding, an overdue risk treatment, a failing
  routine, a red cockpit reading. This list is the **ground truth** and is **always** shown.
- **Your one next step** — the single most useful thing to set up or do next.
- **Life OS rhythm** — how many check-ins you have done this week and this month.

When a gateway is running, a model summarises those signals into *"the top three things that need you, any decision
pending, and what you can ignore"* — **through the gateway**, so it inherits the safety rails, the spending allowance and
the audit trail. With no gateway it simply prints the facts. A model summary is only an aid laid on top of the ground
truth; it can never hide a real overdue item.

Zero input: you never have to type or configure anything. Run it in the morning, or let a routine send it to your phone.

## `./securax ask <agent> --prompt NAME` — saved, reusable prompts

Stop retyping the same careful framing. Saved prompts are named templates in `governance/prompts.json`; call one by name
and the variables `{date}`, `{owner}` (from `SECURAX_OWNER`, else "you") and the words you type (`{extra}`) are filled in:

```bash
./securax ask productivity --prompt standup "ship the ZTMM PR"   # a 2-minute stand-up framing
./securax ask ciso --prompt threat-brief "a new OpenSSL CVE"     # a board-ready threat paragraph
./securax ask cfo --prompt decide "buy vs build the SOC tooling" # a structured decision aid
```

The ones that ship: **standup**, **decide**, **threat-brief**, **explain-plainly**. Add your own by editing
`governance/prompts.json` — keep them **generic and private**: no personal data, no employer or client names, because the
repository is public (a person-specific detail belongs in your environment, as `SECURAX_OWNER`, not in the file).

Both run on the estate's local/free model by default — zero Claude credits — and obey the same rails and allowance as any
other chat. See also [doc 89](89-ACCURATE-ANSWERS-WITHOUT-PROMPT-ENGINEERING.md) for `--careful`, and [doc 118](118-BUILD-WITH-YOUR-MODELS.md) for
driving the estate on your own models.
