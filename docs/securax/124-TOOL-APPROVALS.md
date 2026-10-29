# Human-in-command tool approvals — the AI asks before it acts

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Human-in-command approvals for agent tool calls (LLM06/ASI02): the gateway holds a consequential tool call (transfer/wire/email) for a human — ./securax approvals lists them, ./securax approve <id> grants a single-use, 10-minute approval scoped to that exact tool+args; a different arg, a second use or an expired grant is blocked again, and 3 blocked calls in a row stop the agent. Dangerous tools stay denied. Every grant/use/stop is on the tamper-evident audit chain; grant is operator-only (authenticated or loopback). Tests: test_approvals.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Borrowed from the way Mattermost's agent asks you to approve a tool call — but made sovereign and auditable. When an AI
agent wants to take a **consequential action** (move money, send a wire, email out), the gateway does not simply let it,
and it does not simply block it: it **holds that exact action for a human**, and only proceeds once you say yes — once, on
the record.

This is the OWASP **LLM06 / ASI02 "excessive agency"** control: a model given tools can act; the question is whether it can
act *irreversibly without you*. Here it cannot.

## How it works

The gateway already **denies** the dangerous tools outright (`shell`, `bash`, `exec*`, `run_command`, `*delete*`,
`drop_*`, `rm`, `eval*`) and already **flags** money-movement tools as needing approval (`*transfer*`, `*payment*`,
`*send_money*`, `wire_*`, `send_email`, `*refund*`). What this adds is the approve-then-proceed loop:

1. The agent asks to call an approval-required tool. The gateway **withholds** the call and records it as **pending**,
   keyed to the exact tool name and a hash of its arguments. The reply names the pending id.
2. You review it and grant it:

   ```bash
   ./securax approvals          # what is waiting, with each id, tool and arguments
   ./securax approve <id>       # grant ONE: a single-use, 10-minute approval for that exact call
   ```

3. The next time the agent emits **that exact call**, the gateway **consumes the approval once** and lets it through.

A **different argument**, a **second** attempt on the same approval, or a call **after the ten minutes** is blocked again.
And if an agent keeps hitting the wall — **three blocked tool calls in a row** in one conversation — the gateway
**stops** and tells you a human should step in, instead of letting it flail.

Every grant is written to the gateway's **tamper-evident audit chain** (`tool_approval_granted`, with who and when), and
so is every approved use (`tool_approved`) and every stop (`tool_calls_stopped`). `./securax audit verify` checks the chain.

## Who may approve

Approving is an **operator** action: allowed to an authenticated caller when gateway sign-in is on, or on **loopback** (you,
on the box) — never to an anonymous caller from off the machine. The policy itself (what is denied, what needs approval) is
data in `TOOL_POLICY_FILE`; the defaults are above.

## Why this matters

An AI agent is only safe to give tools if a person stays in command of the actions that cannot be undone. With this, your
estate's agent — in the chat, in Studio, over MCP — can be useful *and* can never move your money or act irreversibly
without your explicit, single-use, audited yes. It is the companion to the gateway's input/output rails, and the reason
the AI can be trusted with tools at all.
