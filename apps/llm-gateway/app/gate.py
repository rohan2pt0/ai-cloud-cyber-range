"""The decision gate (deterministic backbone, slice 1): the AI proposes, code decides. No model is called here.

`decide(action)` routes one proposed action to exactly one of three routes, in plain, ordered rules:

  fallback  no action; the caller gets a structured decision request with a recommended default ("do nothing").
  ask       a person approves first (the gateway records it in app.approvals with these reasons).
  auto      it runs now, with an undo window (`undo_s`, default 300 s) a person can use to take it back.

The inputs are typed fields, never free text a model could argue with:
  type          the action type; it must be declared in the contract registry (app.actions.CONTRACTS) to be known.
  policy        "allow" | "require_approval" | "deny" | "none": what the declared policy says for this type.
  confidence    the model's own confidence, 0..1. It can only LOWER the route: a high number never buys an irreversible
                or external action its way past a person (threat db-s1).
  irreversible  payment, deletion, an outside message, an export of private data. From the contract; a claim may only add it.
  external      does the effect leave the estate (a message, a payment, an upload)?
  criticality   "low" | "medium" | "high" | "critical".
  sensitivity   "none" | "low" | "medium" | "high" | "critical": the stricter of the contract, the claim and what the PII
                rails found in the payload (guardrails.redact_pii severities).

The rules, in order (the first that fires decides; later ones only add reasons):
  1. AI switched off (kill switch), an unknown type, no matching
     policy, or a policy deny                                      -> fallback
  2. a missing, non-numeric or out-of-range confidence             -> fallback
  3. irreversible                                                  -> ask, whatever the confidence
  4. confidence below LOW                                          -> fallback
  5. confidence below HIGH (the mid band)                          -> ask
  6. a policy that requires approval, external, criticality high
     or critical, or sensitivity above low                         -> ask
  7. otherwise (high confidence, reversible, internal, low)        -> auto, with the undo window

Standard library only, pure (no I/O, no clock, no globals written), so it is easy to test and to reason about.
"""
from __future__ import annotations

import math
import os

LOW = 0.5            # below this the proposal is a guess: do nothing, ask the person what they want
HIGH = 0.9           # at or above this, a safe action may run by itself (with an undo)
UNDO_MIN_S, UNDO_MAX_S = 30, 86400
LEVELS = ("none", "low", "medium", "high", "critical")
ROUTES = ("auto", "ask", "fallback")
POLICIES = ("allow", "require_approval", "deny", "none")


def undo_window_s() -> int:
    """The undo window for an "auto" action: GATE_UNDO_S from the server's environment (never from the caller), clamped."""
    try:
        v = int(float(os.getenv("GATE_UNDO_S", "300")))
    except ValueError:
        v = 300
    return max(UNDO_MIN_S, min(UNDO_MAX_S, v))


def level(value, default: str = "none") -> str:
    """A sensitivity or criticality level by name; an unknown name reads as the strictest, so a typo never relaxes a rule."""
    if value is None:
        return default
    v = str(value).strip().lower()
    return v if v in LEVELS else "critical"


def stricter(*values) -> str:
    """The strictest of several levels."""
    return max((level(v) for v in values), key=LEVELS.index, default="none")


def _confidence(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    f = float(value)
    return f if math.isfinite(f) and 0.0 <= f <= 1.0 else None


def decide(action: dict, *, known: bool = True, undo_s: int | None = None) -> dict:
    """Route one proposed action. `known` is False when the type is not in the contract registry.
    Returns {"route", "reasons": [str], "undo_s": int, "recommended": str}: undo_s is 0 unless the route is "auto"."""
    a = action if isinstance(action, dict) else {}
    reasons: list[str] = []
    policy = str(a.get("policy") or "none").strip().lower()
    policy = policy if policy in POLICIES else "none"
    conf = _confidence(a.get("confidence"))
    irreversible = bool(a.get("irreversible"))
    external = bool(a.get("external"))
    crit = level(a.get("criticality"), "low")
    sens = level(a.get("sensitivity"), "none")

    def out(route: str, recommended: str) -> dict:
        return {"route": route, "reasons": reasons, "undo_s": (undo_s if undo_s is not None else undo_window_s())
                if route == "auto" else 0, "recommended": recommended}

    # 1. what a person switched off, the code does not know, or the policy forbids, never runs
    if a.get("ai_stopped"):
        reasons.append("ai_stopped: a person switched AI off (./securax ai stop), so nothing it proposes runs")
        return out("fallback", "do_nothing")
    if not known:
        reasons.append("unknown_action_type: no declared contract for this action")
        return out("fallback", "do_nothing")
    if policy == "deny":
        reasons.append("policy_blocked: the policy denies this action")
        return out("fallback", "do_nothing")
    if policy == "none":
        reasons.append("no_policy: no policy matches this action")
        return out("fallback", "do_nothing")
    # 2. a confidence we cannot read is no confidence
    if conf is None:
        reasons.append("confidence_invalid: missing, not a number, or outside 0..1")
        return out("fallback", "do_nothing")
    # 3. irreversible always asks, whatever the confidence
    if irreversible:
        reasons.append("irreversible: it cannot be undone, so a person decides")
        if conf < LOW:
            reasons.append(f"low_confidence: {conf:.2f} < {LOW}; check it closely")
        return out("ask", "reject" if conf < LOW else "approve")
    # 4-5. uncertainty
    if conf < LOW:
        reasons.append(f"low_confidence: {conf:.2f} < {LOW}")
        return out("fallback", "do_nothing")
    if conf < HIGH:
        reasons.append(f"mid_confidence: {LOW} <= {conf:.2f} < {HIGH}")
    # 6. what reaches out, matters most, or carries personal data asks
    if policy == "require_approval":
        reasons.append("policy_requires_approval")
    if external:
        reasons.append("external: the effect leaves the estate")
    if crit in ("high", "critical"):
        reasons.append(f"criticality_{crit}")
    if LEVELS.index(sens) > LEVELS.index("low"):
        reasons.append(f"sensitive_data_{sens}")
    if reasons:
        return out("ask", "approve")
    # 7. safe, sure and reversible: run, with an undo
    reasons.append(f"auto: confidence {conf:.2f} >= {HIGH}, reversible, internal, low sensitivity")
    return out("auto", "keep")
