# 91 · Any machine can carry the estate, and the estate finds its own weak points

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: every machine shares a capability card through sync (no secrets); ./securax resilience checks every combination of machines being off, names each single point of failure with its fix, and messages you when a new one appears; every feature declares how it survives a machine being off (fitness continuity-declared); reminders go out from one machine at a time; a peer that suddenly misses sync rounds is flagged early. Not yet run on a real multi-machine estate. Encrypted vault copies between machines, shared chat history and a password-server standby are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:**
- Any one machine (laptop, VPS, Mac mini, AWS, GCP, Azure or a private cloud) must carry the estate when the others are off, with every capability it has. For example, the VPS when the laptop is off, and the cloud when the VPS is off.
- Think through every combination.
- If a function truly cannot run somewhere, it may wait for its machine, but that must be said, never a surprise.
- Most of all: stop depending on the owner to think of each scenario. The estate should find its weak points itself.

**The answer in one line:**
- The estate now checks every combination of your machines being on or off. It names each single point of failure with its fix, and tells you when a new one appears.
- CI refuses a feature that has not declared how it survives a machine being off.

## 1. Why the owner kept finding these first

Each earlier fix answered one scenario: a lost laptop, a switched-off GPU box. Nothing looked at all of them together. And nothing stopped a new feature from quietly depending on one machine. The fix is a mechanism, not more scenarios written by hand:

| Before | Now |
|---|---|
| Scenarios were found when the owner thought of them | Every combination is checked: 2^n − 1 for n machines (7 for three, 1,023 for ten) |
| A new feature could depend on one machine unseen | Every feature declares what it needs and what happens when that is off (`governance/resilience.json`). Fitness `continuity-declared` fails a feature with no declaration, and fails any critical feature that one machine off would stop in the reference estate |
| A weak machine was noticed when it failed | A machine that misses far more sync rounds than it usually does is flagged in advance (section 4) |
| Three machines meant three copies of every reminder | Reminders run on one machine at a time; the next takes over if it stops |

## 2. How it knows what each machine can do

Every 10 minutes (the `node-card` routine), each machine shares a small **card** through the sync your Life OS already uses. The card records:
- whether it runs the estate;
- whether it has a cloud key or a model machine;
- whether it runs the online tunnel or the password manager;
- whether it holds your private registers;
- whether its backups are fresh and go off-site;
- whether its routines are scheduled.

It holds no key, no path and no data, only yes or no. Every machine therefore knows every other one, even one that is off now, because its last card is kept for 30 days.

## 3. What it reports

```bash
./securax resilience
```

1. **Every combination:** how many keep every critical feature working.
2. **Each machine alone:** what still works, what works but slower (for example the small model instead of a cloud one), and what stops.
3. **Each single point of failure,** worst first, with its fix. Accepted risks are shown with their reason and review date.

The `resilience-check` routine runs this every morning. It messages you only when something **new** appears.

### What a typical estate shows today

With a laptop (cloud key, your registers) and a VPS (tunnel, password manager, no key):

| Alone | Works | Slower | Stops until another machine is on |
|---|---|---|---|
| **Laptop** | Life OS, gateway, chat, building, the plan | backups without off-site | your own addresses from outside (the tunnel is on the VPS); saving new passwords |
| **VPS** | Life OS, your addresses, passwords | answers come from the small model (no key there); controls and incidents without your registers | your risk register |

The fixes it prints for that estate:
- `./securax keys` on the VPS (a free key);
- `./securax online invite`, with its line run on the laptop (the tunnel on both);
- copying the vault to the always-on machine.

After those three steps, either machine carries everything except the accepted password-server limit.

## 4. "Advanced AI", said honestly

- **Every combination is checked exactly.** With up to ten machines, all combinations can be tried in milliseconds. That is better than a model guessing which ones matter.
- **The early warning is statistics, not magic.** Each machine keeps a short history of whether each peer answered a sync round. A peer whose failure rate in the last day is at least three times its own usual rate, and at least 20%, is flagged.
- **Your judgement is kept for what it is good at.** You decide what to accept and when to review it. The estate does the searching.

## 5. Functions that wait for their machine (the worst cases)

| Function | Why it cannot move today | What you get meanwhile | Plan |
|---|---|---|---|
| Saving new passwords | Two password servers would not sync with each other | Every Bitwarden app keeps an offline copy for reading | A standby that restores the nightly backup: 2027-01-31 |
| Past chat history from another machine | Chat stores history per machine | New chats work anywhere | Shared history (doc 86): 2026-12-10 |
| Your private registers (risks, incidents, knowledge) | They live in one machine's `vault/` | The starter control library works anywhere | Encrypted vault copies between your machines: 2026-12-31 |

## 6. Proof

- **Unit tests** (`test_resilience.py`):
  - every combination is counted;
  - a machine that alone provides a critical feature is named;
  - accepted risks are shown but not counted;
  - the early warning fires on a sudden drop, not on a peer that is always flaky;
  - the next machine takes over the reminders, and a duplicate is preferred to none;
  - cards hold no secret.
- **Fitness `continuity-declared`:** every feature is declared, and the reference estate (laptop, VPS, cloud) has no critical single point of failure that is not accepted.
- **Sandbox `machine_alone`:** on the real estate, the card is shared through sync and the report names this machine as the only one.
