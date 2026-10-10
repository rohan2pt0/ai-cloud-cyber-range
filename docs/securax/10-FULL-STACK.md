# SecuRAX — Full-Scale Mode (opt-in, turn-off-able)

Go big when you need to — a real SOC, team collaboration, private cloud — then switch it off
when you don't. **Nothing here runs by default.** We never re-implement these tools; we run
their **official upstream images/repos** and wire them into the estate's network.

> Rule of thumb: full mode wants **≥16 GB RAM** (32 GB comfortable). On the Spectre, run one
> heavy stack at a time; on a mini-PC/server, run them together. Always `down` when idle —
> `./securax doctor` will warn you on RAM/disk pressure.

## 1. The light piece — ships with the repo
Mattermost (ChatOps / coordination) is light enough to include:
```bash
./securax full up      # starts Mattermost at http://localhost:8065  (set MM_DB_PASSWORD in .env first)
./securax full down    # stops it, frees RAM
```
Use it as the estate's "control room": alerts, approvals, and agent hand-offs land here.

## 2. The heavy security stack — run the official repos (don't reinvent)
Each of these publishes a maintained docker-compose. Clone, bring up, and point it at the
estate (or just run it alongside). This is the FATF/INTERPOL layer of the operating model.

**Wazuh (SIEM + XDR)** — https://github.com/wazuh/wazuh-docker
```bash
git clone https://github.com/wazuh/wazuh-docker -b v4.9.0 && cd wazuh-docker/single-node
docker compose up -d        # dashboard: https://localhost:443  (~4-6 GB RAM)
```
**MISP (threat intelligence)** — https://github.com/MISP/misp-docker
```bash
git clone https://github.com/MISP/misp-docker && cd misp-docker
cp template.env .env && docker compose up -d   # https://localhost  (~2-3 GB RAM)
```
**TheHive + Cortex (incident response)** — https://github.com/StrangeBee/docker
```bash
git clone https://github.com/StrangeBee/docker thehive-docker && cd thehive-docker
docker compose up -d        # TheHive: http://localhost:9000  (~4 GB RAM, needs Cassandra+ES)
```
Then feed them into the AI-SOC: export Wazuh/Suricata/MISP events as JSON and run
`python3 ai-soc/soc/triage.py <events.jsonl>` (or the MCP `soc_triage` tool) to correlate —
the estate's brain sits on top of the proven collectors.

## 3. Private, sovereign cloud at scale (when you outgrow a laptop)
Keep the core sovereign — run your own cloud instead of renting:
- **Proxmox VE** (https://www.proxmox.com) — the pragmatic choice: VMs + containers + HA on a
  mini-PC/server cluster. Start here.
- **OpenStack** (https://www.openstack.org) — full private-cloud IaaS when you reach
  multi-node/multi-tenant scale (this is what large sovereign clouds run).
- **k3s/Talos** for the Kubernetes layer on top (the Terraform modules already target K8s).

## 4. Turn it all off (and keep it ready)
```bash
./securax full down                    # Mattermost
# in each upstream repo you cloned:
docker compose down                    # Wazuh / MISP / TheHive
```
Everything is config + volumes on disk — stopped costs nothing, and `up` again is instant.
That is the "resource-hungry but switch-off-able, always ready to scale" property you wanted.

## 5. What runs where (so nothing is a single point of failure)
| Load | Where | Why |
|---|---|---|
| everyday (AI, Guiding Map, automation) | laptop, always-on, capped | low footprint, instant |
| full SOC (Wazuh/MISP/TheHive) | mini-PC/server or cloud VM, on-demand | heavy; run when investigating |
| multi-tenant / clients | Kubernetes (k3s → EKS/GKE/AKS) | elastic, isolated per tenant |
| sovereign private cloud | Proxmox → OpenStack | own the metal, own the data |
