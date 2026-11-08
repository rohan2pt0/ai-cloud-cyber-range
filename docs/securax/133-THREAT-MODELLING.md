# 133 · Threat modelling — think like the attacker first

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Threat modelling as a core principle (think like the attacker first): a component that crosses a trust boundary gets a plain-text model in governance/threat-models.json (parts, flows, boundaries, then all six STRIDE ways), each threat mitigated with evidence that exists, accepted with a reason and a review date, or ruled out with a reason. Fitness threat-modelled holds the structure, the evidence and the dates, and the number of models only goes up. The Microsoft Threat Modeling Tool (a free Windows click-to-run app, 7.3.51110 of 10 November 2025) or any other tool can be used to draw; binary .tm7 files are not committed. Two components are modelled (the Command Center door and the hosted apps) as a first pass for the owner's review; the gateway, sync, hunt fleet and crisis are dated in the queue. Tests: test_threat_models.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The rule.** Before you build anything that crosses a trust boundary, model it the way an attacker would. This is the core
principle `threat-model`, held by the fitness check `threat-modelled`. It is the first lens of the security review in AGENTS.md
section 7, but done at **design time**, when a fix is cheapest.

## The method: STRIDE per element

For every part of the component (a process, a store, an outside party) and every data flow that crosses a trust boundary, ask the six
questions: **S**poofing (pretending to be someone or something), **T**ampering (changing data), **R**epudiation (denying an action),
**I**nformation disclosure (leaking), **D**enial of service (stopping it), **E**levation of privilege (gaining more than allowed). This is
the Microsoft SDL method.

## Where the model lives

A diagram helps you think; a **text file** lets the repository check it. So the source of truth is `governance/threat-models.json`, and you
may draw in any tool you like:

- **Microsoft Threat Modeling Tool**: a free Windows click-to-run app that generates STRIDE threats from a diagram. Its latest release in
  Microsoft's notes is [7.3.51110, from 10 November 2025](https://learn.microsoft.com/en-nz/AZURE/security/develop/threat-modeling-tool-releases-73511101).
  Its files are binary (`.tm7`), so do **not** commit them to this public repository: copy the findings into the JSON.
- **Other tools** (OWASP Threat Dragon, a code-based tool such as pytm, or a whiteboard) work the same way. They were not checked for this doc.

## What the check enforces

Each model names its **boundaries**, **elements** and **flows** (at least one flow must cross a boundary), and considers **all six** STRIDE
categories. Each threat is one of:

| Status | What it needs |
|---|---|
| `mitigated` | the mitigation, and an `evidence` path that **exists** (a test, a header file, a config) |
| `accepted` | a real `reason` and a `review` date that has not passed (an overdue date fails, so a risk is pulled back into view) |
| `not-applicable` | the reason it cannot happen |

The number of models only goes up. Two are in place: the Command Center door and the hosted apps. They show the honest part too: the
accepted risks, each with a date (the shared browser origin, an altered page from the host, script in the single-file apps).

## Add a model (the template)

Add one entry under `models` in `governance/threat-models.json`, then run `./securax fitness`:

```json
"my-component": {
  "name": "What it is", "scope": "One sentence on what is in and out",
  "boundaries": ["where trust changes"],
  "elements": [{"id": "a", "kind": "process"}, {"id": "b", "kind": "external"}],
  "flows": [{"from": "a", "to": "b", "data": "what travels", "crosses": "which boundary"}],
  "threats": [
    {"id": "mc-s1", "stride": "S", "element": "b", "threat": "what could go wrong, in a sentence",
     "status": "mitigated", "mitigation": "what stops it", "evidence": "path/to/the/test"}
  ]
}
```

## What is next

The rest are modelled by risk, highest first (the AI gateway, sync, the hunt fleet, crisis), dated in the queue. A first pass is a
starting point for the owner's review, not a certificate: a threat model is only as good as the people who challenge it.
