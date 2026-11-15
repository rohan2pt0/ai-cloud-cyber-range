# Spec: app-lock

Queue item `app-lock` in `governance/queue.json` · due 2026-12-02 · added 2026-11-11.

**The ask, as the queue holds it:** Owner, 2026-11-11: the apps hold sensitive private details and had no security; make them highly secure with the best features (biometrics) but the least friction, without over-engineering or sacrificing the experience

## Outcome for the person

Private details are safe if the phone is lost or lent, and opening the app is still one touch.

## Data

The lock record (WebAuthn credential id, recovery code hash), and next an encryption key for data at rest; threat model `lifeos-lock`.

## Screen (one action)

Lock screen: one action, `Unlock` with fingerprint or face. Recovery is folded under one line.

## Test that proves it

`test93.js`, the robustness audit with a damaged lock record (never a lock-out), and for encryption a test that stored data is unreadable without the key.

## Evolution rail (amoeba to enterprise)

- **Amoeba, today:** A screen lock with device biometrics.
- **Enterprise, when conditions call for it:** Encryption at rest with keys bound to the one-door identity, remote wipe and policy per organisation.

---

A spec, not a build: screens and commands named here are proposals until their slice ships. The next step and its
date stay in the queue item.
