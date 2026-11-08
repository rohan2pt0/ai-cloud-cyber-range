# 129 · Hunt fleet — mass deployment, generated not provisioned

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Hunt fleet mass deployment — the actuated organism rail of ./securax hunt: ./securax hunt fleet GENERATES the Velociraptor server setup, the client rollout (GPO / Intune / SCCM-msiexec / Ansible) and a throttled server-side fleet hunt (the same packs as the offline collector), pointing every binary at your internal mirror (SECURAX_HUNT_MIRROR, no vendor egress) and hash-pinned. It provisions NOTHING — standing up the server, pushing to endpoints and running a fleet hunt are your approved steps (./securax approve). RBAC/multi-org map to the platform services; the offline collector (no server) is the no-SPOF fallback. Deploy methods are data (governance/hunt-fleet.json). Tests: test_hunt.py. (doc 129) [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**What this is.** The threat hunt (doc 127) ships as an **amoeba**: a self-contained offline collector that runs on one
host with no server. When the estate grows — more endpoints, more teams, a standing server — the same packs need to run
across a **fleet**. This is the actuated *organism* rail of `./securax hunt`: it **generates everything** needed to stand
up a [Velociraptor](https://docs.velociraptor.app/docs/deployment/clients) server and roll clients out at scale, and it
**provisions nothing itself**. Generating is safe and offline; standing up a server, pushing an agent to every endpoint
and running a fleet-wide hunt are consequential, so they stay the human's approved steps (`./securax approve`) — exactly
as the growth map grades them *assisted*.

## The four steps

```bash
./securax hunt fleet plan                         # readiness: standing server? internal mirror? multi-node? multi-team?
./securax hunt fleet server                       # generate the server setup (frontend, GUI, admin, client config)
./securax hunt fleet clients --method gpo         # generate the client rollout for one method (omit --method for all)
./securax hunt fleet hunt ransomware-aftermath    # generate a throttled, server-side fleet hunt from a pack
```

- **plan** — reads the estate's conditions locally (the same signals `./securax evolve` uses) and shows what the fleet
  needs and what is in place, then the ordered next commands.
- **server** — writes `server-setup.sh`: `velociraptor config generate`, set the GUI/frontend/datastore, add an admin,
  extract the client config. The server is a control-plane single point of failure, so it tells you to give it a standby
  — and the offline collector needs no server at all (the fallback).
- **clients** — writes a rollout artifact per method, each pulling the binary from **your internal mirror**
  (`SECURAX_HUNT_MIRROR`) so endpoints never egress to a vendor, hash-pinned:
  - **msiexec / SCCM** — repack the MSI with the client config, push it with SCCM or install silently.
  - **gpo** — assign the MSI by Group Policy software-installation to an OU, or a startup task for a temporary IR push.
  - **intune** — wrap the MSI as a Win32 app and deploy to an Entra device group.
  - **ansible** — config-package the binary as a managed service (good for Linux and mixed fleets).
- **hunt** — writes a **throttled** server-side hunt definition for a pack (the *same* packs as the offline mode), with
  ops/second, a CPU limit and a row cap, because a KAPE-style collection on ten thousand endpoints can move **terabytes**.

## Governed from day one

- **RBAC & multi-org** — Velociraptor's built-in roles (administrator, analyst, investigator, reader) and orgs map to the
  platform's RBAC and tenancy services; the server setup tells you to give each team a role and, for many business units,
  an org — not hand everyone administrator.
- **No vendor egress** — every client artifact and the fleet binary come from `SECURAX_HUNT_MIRROR`; set it to your
  Nexus/Artifactory/S3 and regenerate, and no `<MIRROR>` placeholder ships.
- **Human floor** — the artifacts are generated and reviewed by you; pushing to endpoints and queuing a fleet hunt are
  consequential, so they go through your change process and `./securax approve`. Nothing here provisions or pushes on its
  own.

## No single point of failure

The fleet server is a natural single point of failure, so it is never the only way in: the **offline collector mode
needs no server** and is the fallback (doc 127). Give the server a standby, back up its datastore, and remember a single
host can always be triaged offline.

## Where it fits

- **The amoeba:** `./securax hunt` is the offline collector; this is its grown form. The growth map (`./securax evolve`,
  doc 128) shows when conditions favour growing hunt from the amoeba to the colony/organism, and this is the rail it
  names.
- **Built for one, ready for many (doc 97):** `suite.json` says hunt's enterprise edition is a managed fleet; this is how
  it gets there, generated from the same packs with no rewrite.

This generates deployment artifacts; it is not a running server, and provisioning is your approved decision.
