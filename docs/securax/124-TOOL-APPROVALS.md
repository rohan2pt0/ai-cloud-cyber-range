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

## The decision gate and the rejection pipeline: the AI proposes, code decides

Tool approvals ask a person about one kind of action. The **deterministic backbone** asks the same question of every write
an AI proposes, in plain code, with no model in the decision (threat model `deterministic-backbone` in
`governance/threat-models.json`).

**One pipeline for every AI-produced write** (`apps/llm-gateway/app/actions.py`, `POST /v1/actions/propose`). A proposal is
`{"type": "habit.tick", "payload": {...}, "confidence": 0.97}` and passes five stages in order:

1. **schema**: the payload matches the declared contract for its type (required fields, nothing extra);
2. **types**: each field's type, range, length, format and allowed values;
3. **gate**: the decision gate below, the action policy (`ACTION_POLICY_FILE`, the same allow / require_approval / deny
   shape as the tool policy; a broken file denies everything) and the kill switch;
4. **idempotency**: the same proposal (its `idempotency_key`, or the hash of type and payload) runs once; a key reused for
   a different payload is refused;
5. **audit**: the decision and its reasons go into the hash-chained audit log *before* the write; no audit line, no write.

A failing stage answers `422` with `{"stage", "code", "field", "message"}`, so the caller regenerates or escalates, and
nothing is written.

**The decision gate** (`apps/llm-gateway/app/gate.py`) routes each action:

| The action | Route |
|---|---|
| unknown type, no policy, a policy deny, or AI switched off | **fallback**: no action, a decision request recommending "do nothing" |
| a missing or out-of-range confidence, or confidence under 0.5 | **fallback** |
| irreversible (a payment, a deletion, an outside message, an export of private data) | **ask**, whatever the confidence |
| confidence 0.5 to 0.9, or external, high criticality, personal data, or a policy that requires approval | **ask** |
| confidence 0.9 or more, reversible, internal, low sensitivity | **auto**, with an undo window (300 s, `GATE_UNDO_S`) |

Confidence can only lower the route. Whether an action can be undone, leaves the estate or matters is a fact in the
contract, never the model's word; personal data is what the gateway's own PII rails find in the payload.

**What you see.** An **ask** appears in `./securax approvals` with the gate's reasons; approve it once and the same proposal
runs once. An **auto** action appears in `GET /v1/actions` with its undo deadline; `POST /v1/actions/{id}/undo` takes it
back inside the window (operator-only, audited). `GET /v1/actions/stats` and `/metrics` count proposals, rejections by
stage, asks, runs and undos, and `./securax progress` shows the rejection rate and the share of operations a model proposed.
