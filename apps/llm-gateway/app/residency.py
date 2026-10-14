"""Data residency at the gateway: data of a given class may only be processed in the zones the policy allows for that class.

Regulators in many jurisdictions require some data to stay inside the country (India: SEBI CSCRF 'Regulatory Data' must remain within
India; RBI's localisation expectations; DPDP cross-border rules; the same idea exists in the EU, the Gulf, Singapore...). The gateway
is the one place every prompt passes, so it is where this is enforced - for ANY jurisdiction: the policy is data, not code.

  RESIDENCY_MODE         off (default: unchanged) | monitor (decide and log, never change anything) | enforce
  RESIDENCY_POLICY_B64   the policy (base64 JSON), or RESIDENCY_POLICY_FILE, or RESIDENCY_POLICY_JSON; built-in default if none
  RESIDENCY_ACTION       reroute (default: send the request to an allowed model) | block (refuse it)

How a request is classified (the HIGHEST class wins; a caller can raise the class, never lower it):
  1. the caller's own default class (an API key's or token's `data_class`)           - e.g. the regulatory-reporting service
  2. the `X-Data-Class` request header
  3. what the gateway FINDS in the text (Aadhaar, PAN, card numbers, ... -> class_by_finding)
Each model alias lives in a ZONE (`local` = this machine/LAN, `in` = in-country cloud, `global` = anywhere). A class lists the zones
it may be processed in. A model with no zone is treated as `global` (fail-closed). Model-based DETECTORS are subject to the same
rule: a cloud detector is not sent text its class may not leave for. Redaction does not downgrade a class (redaction can miss).
Standard library only.
"""
from __future__ import annotations

import base64
import fnmatch
import json
import os
from dataclasses import dataclass, field

DEFAULT_POLICY: dict = {
    "jurisdiction": "generic",
    "order": ["public", "confidential", "regulatory"],           # least -> most sensitive
    "classes": {"public": {"zones": ["*"]}, "confidential": {"zones": ["local", "in"]}, "regulatory": {"zones": ["local"]}},
    "default_class": "public",
    "class_by_finding": {"AADHAAR": "regulatory", "CARD_PAN": "regulatory", "INCOME_TAX_PAN": "regulatory",
                         "UPI_ID": "confidential", "IN_MOBILE": "confidential", "EMAIL": "confidential"},
    "model_zones": {"*-local": "local", "coder": "local"},
    "detector_zones": {"llama-guard": "local"},                   # others default to global; set bedrock-guardrail to "in" if your region is in-country
    "reroute_to": ["bank-assistant-local"],
}


@dataclass
class Decision:
    cls: str = ""
    action: str = "allow"            # allow | rerouted | blocked
    requested: str = ""
    model: str = ""
    reason: str = ""

    def audit(self) -> dict:
        return {"class": self.cls, "action": self.action, "requested_model": self.requested, "model": self.model, "reason": self.reason}


@dataclass
class Policy:
    mode: str = "off"
    action: str = "reroute"
    data: dict = field(default_factory=lambda: dict(DEFAULT_POLICY))

    @classmethod
    def from_env(cls, env=None) -> Policy:
        env = os.environ if env is None else env
        mode = env.get("RESIDENCY_MODE", "off").strip().lower()
        action = env.get("RESIDENCY_ACTION", "reroute").strip().lower()
        if mode not in ("off", "monitor", "enforce") or action not in ("reroute", "block"):
            raise ValueError("RESIDENCY_MODE must be off|monitor|enforce and RESIDENCY_ACTION reroute|block")
        data = dict(DEFAULT_POLICY)
        raw = env.get("RESIDENCY_POLICY_JSON", "")
        if not raw and env.get("RESIDENCY_POLICY_B64"):
            raw = base64.b64decode(env["RESIDENCY_POLICY_B64"]).decode()
        if not raw and env.get("RESIDENCY_POLICY_FILE"):
            with open(env["RESIDENCY_POLICY_FILE"], encoding="utf-8") as f:
                raw = f.read()
        if raw:
            data = {**data, **json.loads(raw)}
        p = cls(mode=mode, action=action, data=data)
        bad = problems(data)
        if bad and mode != "off":
            raise ValueError("residency policy is invalid: " + "; ".join(bad))
        return p

    # ------------------------------------------------------------------------------------------------------------ zones
    def model_zone(self, model: str) -> str:
        zones = self.data["model_zones"]
        if model in zones:
            return zones[model]
        for pat, z in zones.items():
            if fnmatch.fnmatchcase(model or "", pat):
                return z
        return "global"

    def detector_zone(self, name: str) -> str:
        return self.data.get("detector_zones", {}).get(name, "global")

    def detector_allowed(self, cls: str, name: str) -> bool:
        """May a model-based detector named `name` be sent text of this class? (Always yes when residency is off.)"""
        return self.mode == "off" or not cls or self.allowed(cls, self.detector_zone(name))

    def allowed(self, cls: str, zone: str) -> bool:
        zs = self.data["classes"][cls]["zones"]
        return "*" in zs or zone in zs

    def classify(self, findings, ident_class: str = "", header: str = "") -> str:
        order = self.data["order"]
        rank = {c: i for i, c in enumerate(order)}
        got = [self.data["default_class"]]
        for c in (ident_class, (header or "").strip().lower()):
            if c in rank:
                got.append(c)
        for f in findings:
            label = f.rule[4:] if f.rule.startswith("PII-") else f.rule
            c = self.data["class_by_finding"].get(label)
            if c in rank:
                got.append(c)
        return max(got, key=lambda c: rank.get(c, 0))

    def decide(self, requested: str, findings, ident_class: str = "", header: str = "") -> Decision:
        if self.mode == "off":
            return Decision(model=requested, requested=requested)
        cls = self.classify(findings, ident_class, header)
        d = Decision(cls=cls, requested=requested, model=requested)
        zone = self.model_zone(requested)
        if self.allowed(cls, zone):
            d.reason = f"{requested or 'default model'} is in zone '{zone}', allowed for class '{cls}'"
            return d
        if self.mode == "monitor":
            d.action, d.reason = "would_" + self.action, f"VIOLATION (monitor mode): {requested!r} is in zone '{zone}', class '{cls}' may only use {self.data['classes'][cls]['zones']}"
            return d
        if self.action == "reroute":
            for alt in self.data.get("reroute_to", []):
                if self.allowed(cls, self.model_zone(alt)):
                    d.action, d.model = "rerouted", alt
                    d.reason = f"class '{cls}' may not be processed in zone '{zone}'; sent to {alt} (zone '{self.model_zone(alt)}')"
                    return d
        d.action = "blocked"
        d.reason = f"class '{cls}' may only be processed in {self.data['classes'][cls]['zones']}; {requested!r} is in zone '{zone}' and no allowed model is configured"
        return d


def problems(data: dict) -> list[str]:
    out = []
    for k in ("order", "classes", "default_class", "class_by_finding", "model_zones"):
        if k not in data:
            out.append(f"missing '{k}'")
    if out:
        return out
    cl = data["classes"]
    for c in data["order"]:
        if c not in cl or "zones" not in cl[c] or not cl[c]["zones"]:
            out.append(f"class '{c}' needs a non-empty 'zones' list")
    if data["default_class"] not in data["order"]:
        out.append("default_class is not in 'order'")
    for f, c in data["class_by_finding"].items():
        if c not in data["order"]:
            out.append(f"class_by_finding[{f}] names unknown class '{c}'")
    top = data["order"][-1]
    if "*" in cl.get(top, {}).get("zones", []):
        out.append(f"the most sensitive class '{top}' allows every zone ('*') - that is no restriction at all")
    return out
