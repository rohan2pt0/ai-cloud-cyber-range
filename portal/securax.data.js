/*
 * SecuRAX portal — single source of truth (content), separated from presentation.
 * ----------------------------------------------------------------------------------
 * Design pattern: "data-driven UI" + "separation of concerns". The portal (index.html)
 * knows HOW to render; this file knows WHAT to show. To extend the portal, you edit THIS
 * file only — add a pillar, a capability, a principle — and the UI updates automatically.
 * No build step, no framework, no network: it loads by double-clicking index.html.
 *
 * Every entry is deliberately commented/explained so you learn the estate by reading it.
 */
window.SECURAX = {
  meta: {
    name: "SecuRAX",
    expansion: "Security · Robust · Adaptive · eXcellence-driven",
    tagline: "One lifelong, zero-investment-to-start, vendor-agnostic foundation.",
    northStar:
      "A self-evolving, antifragile command center that uses open-source AI and security " +
      "tooling to protect what matters, compound your advantage over time, and make you — and " +
      "the people around you — a better version of themselves, while satisfying every auditor " +
      "on the first pass.",
  },

  // The five faces of one estate. `seed` = what already exists in this repo today.
  pillars: [
    { id: "P1", name: "AI Security Range", theme: "Security FOR AI",
      desc: "Guardrails, red-teaming, AI-SPM and governance for LLM/ML systems.",
      seed: "apps/ · redteam/ · governance/ · local/ · infra/", status: "built" },
    { id: "P2", name: "AI-SOC / SecOps", theme: "AI FOR security",
      desc: "Detection, correlation, triage, threat-intel and incident response.",
      seed: "ai-soc/ → grows into Wazuh + MISP + TheHive", status: "seed" },
    { id: "P3", name: "SENTINEL Command Center", theme: "The brain",
      desc: "Hybrid local+cloud LLM, data-tier router, automation, knowledge base.",
      seed: "apps/llm-gateway/ + Ollama + n8n + Obsidian (roadmap)", status: "seed" },
    { id: "P4", name: "Guiding Map / Life-OS", theme: "The human layer",
      desc: "Personal & family operating system, continuity, OPSEC, finance.",
      seed: "personal-rnd/ + Guiding-Map PWA", status: "seed" },
    { id: "P5", name: "Governance, Risk & Compliance", theme: "The proof",
      desc: "Control mapping, automated audit evidence, board-ready narratives.",
      seed: "docs/ · aispm_scan.py · model-registry", status: "built" },
  ],

  // The constitution. Ordered by priority: lower number wins a conflict.
  principles: [
    { id: "P-0", title: "Survive first (antifragility)", gist: "No single point of failure; fail-closed on security; get stronger from stress; 3-2-1 backups." },
    { id: "P-1", title: "Start at zero, earn every spend", gist: "Free/open-source on hardware you own; spend only on a documented trigger; 80/20 on cost." },
    { id: "P-2", title: "Vendor- & tool-agnostic", gist: "Program to open standards; every tool is swappable behind an interface. No lock-in." },
    { id: "P-3", title: "Don't reinvent the wheel", gist: "Compose proven open-source building blocks; write only the differentiated 20% of glue." },
    { id: "P-4", title: "Secure/private/compliant by design", gist: "Data-tiers drive routing; privacy-by-design; map controls to frameworks before building; RBI FREE-AI aligned." },
    { id: "P-5", title: "Everything-as-code & teachable", gist: "All in Git; comments & full-forms everywhere; named design patterns; learn by browsing." },
    { id: "P-6", title: "Risk-managed & measurable", gist: "Risk = likelihood × impact; best effort-to-impact first; measure defence, cost, MTTD/MTTR." },
    { id: "P-7", title: "Gradual, end in mind", gist: "Crawl→walk→run; each step independently useful; keep it simple; delete ruthlessly." },
  ],

  // The single most important control: classify before you process.
  dataTiers: [
    { tier: "Red", color: "#e5484d", label: "Restricted", rule: "Local / on-prem models only — never leaves the machine.",
      examples: "Customer data, internal IPs, incident details, Aadhaar/PAN, bank architecture." },
    { tier: "Yellow", color: "#f5a623", label: "Internal", rule: "Local preferred; cloud only after sanitisation (entity masking).",
      examples: "Security procedures, non-attributed analysis, career plans with employer context." },
    { tier: "Green", color: "#30a46c", label: "General", rule: "Cloud AI acceptable.",
      examples: "Public threat intel, certification study, general drafting." },
  ],

  // "Never re-research": capability -> primary open-source tool. phase 0 = free, laptop, now.
  catalog: [
    { group: "AI / ML brain", items: [
      { cap: "Local LLM runtime", primary: "Ollama", alt: "vLLM, llama.cpp", phase: 0, std: "Data residency (Red tier)" },
      { cap: "Multi-model router + budget", primary: "LiteLLM", alt: "Portkey", phase: 0, std: "Cost control" },
      { cap: "AI guardrails (PEP)", primary: "llm-gateway (this repo)", alt: "NeMo Guardrails, Llama Guard", phase: 0, std: "OWASP LLM Top 10" },
      { cap: "Vector database (RAG)", primary: "Qdrant", alt: "pgvector, Chroma", phase: 1, std: "Knowledge retrieval" },
      { cap: "Private doc chat", primary: "AnythingLLM", alt: "Open WebUI", phase: 0, std: "Red-tier Q&A" },
      { cap: "AI red-teaming", primary: "promptfoo + garak + PyRIT", alt: "Giskard", phase: 0, std: "NIST AI 100-2, MITRE ATLAS" },
    ]},
    { group: "Detect & respond (SOC)", items: [
      { cap: "SIEM + HIDS + compliance", primary: "Wazuh", alt: "Elastic Security, Graylog", phase: 1, std: "NIST CSF DETECT, PCI DSS 10" },
      { cap: "Threat intel (CTI)", primary: "MISP", alt: "OpenCTI", phase: 1, std: "STIX/TAXII, CERT-In" },
      { cap: "Incident response", primary: "TheHive", alt: "IRIS-DFIR", phase: 1, std: "NIST CSF RESPOND" },
      { cap: "Network IDS/IPS", primary: "Suricata", alt: "Zeek, Snort", phase: 1, std: "NIST CSF DETECT" },
      { cap: "SOAR playbooks", primary: "Shuffle", alt: "n8n, Cortex", phase: 2, std: "Automated response" },
      { cap: "AI-SOC triage", primary: "ai-soc/ (this repo)", alt: "—", phase: 0, std: "Agentic SecOps" },
    ]},
    { group: "Protect (platform/app)", items: [
      { cap: "Identity: SSO/MFA/RBAC", primary: "Keycloak", alt: "Authentik, Authelia", phase: 1, std: "ISO 27001 A.5/A.8" },
      { cap: "Secrets management", primary: "OpenBao", alt: "SOPS + age", phase: 1, std: "PCI DSS 3, DPDP" },
      { cap: "Vulnerability scanning", primary: "OpenVAS/Greenbone", alt: "Nuclei, Trivy", phase: 1, std: "NIST CSF IDENTIFY" },
      { cap: "K8s admission policy", primary: "Kyverno", alt: "OPA Gatekeeper", phase: 0, std: "CKS, ISO 42001" },
      { cap: "Runtime threat detection", primary: "Falco", alt: "Tetragon", phase: 0, std: "MITRE ATT&CK/ATLAS" },
      { cap: "Policy-as-code", primary: "OPA / Conftest", alt: "Kyverno", phase: 0, std: "Compliance-as-code" },
    ]},
    { group: "Posture & compliance", items: [
      { cap: "Config/compliance scan", primary: "OpenSCAP + Wazuh SCA", alt: "Lynis, CIS-CAT", phase: 1, std: "CIS Benchmarks" },
      { cap: "Cloud posture (CSPM)", primary: "Prowler", alt: "ScoutSuite, Steampipe", phase: 1, std: "CSA CCM" },
      { cap: "IaC misconfig scan", primary: "Trivy config / Checkov", alt: "tfsec, KICS", phase: 0, std: "Secure IaC" },
      { cap: "Immutable audit log", primary: "immudb → Hyperledger Fabric", alt: "WORM object-lock, Sigstore", phase: 2, std: "ISACA audit" },
    ]},
    { group: "Data / platform / delivery", items: [
      { cap: "Relational database", primary: "PostgreSQL", alt: "MariaDB", phase: 0, std: "Data integrity" },
      { cap: "Object storage (S3 API)", primary: "MinIO", alt: "SeaweedFS", phase: 1, std: "Backups, WORM" },
      { cap: "Orchestration", primary: "k3s / kind → EKS/GKE/AKS", alt: "Nomad", phase: 1, std: "HA, scale" },
      { cap: "Infrastructure as Code", primary: "OpenTofu / Terraform", alt: "Pulumi, Ansible", phase: 0, std: "Reproducibility" },
      { cap: "CI/CD", primary: "GitHub Actions", alt: "GitLab CI, Jenkins", phase: 0, std: "DevSecOps" },
      { cap: "Observability", primary: "Prometheus + Grafana + Loki", alt: "OTel Collector", phase: 1, std: "Monitoring, SLOs" },
      { cap: "Workflow automation", primary: "n8n", alt: "Node-RED, Temporal", phase: 0, std: "The glue" },
      { cap: "Backup / BCDR", primary: "restic / BorgBackup (3-2-1)", alt: "Velero", phase: 0, std: "ISO 22301" },
    ]},
    { group: "Human layer", items: [
      { cap: "Second brain", primary: "Obsidian (PARA + Zettelkasten)", alt: "Logseq", phase: 0, std: "Knowledge continuity" },
      { cap: "Life-OS / continuity", primary: "Guiding-Map PWA", alt: "—", phase: 0, std: "Family BCP, OPSEC" },
      { cap: "Personal OPSEC / self-OSINT", primary: "personal-rnd/ (this repo)", alt: "—", phase: 0, std: "Privacy-by-design" },
      { cap: "Personal finance / FIRE", primary: "fin_freedom.py + INDMoney", alt: "Firefly III", phase: 0, std: "Financial resilience" },
    ]},
  ],

  // Frameworks the estate maps to. `how` is one line of plain English.
  compliance: [
    { fw: "NIST CSF 2.0", how: "Backbone: Govern/Identify/Protect/Detect/Respond/Recover." },
    { fw: "NIST AI RMF + AI 100-2", how: "Trustworthy-AI lifecycle + adversarial-ML taxonomy." },
    { fw: "ISO/IEC 27001:2022", how: "ISMS controls (Annex A) across the estate." },
    { fw: "ISO/IEC 42001", how: "AI Management System — governance of AI (model registry)." },
    { fw: "ISO 22301", how: "Business continuity: everything-as-code + 3-2-1 backups + DR drills." },
    { fw: "PCI DSS 4.0", how: "Cardholder-data controls: logging, encryption, access, WAF." },
    { fw: "SWIFT CSP", how: "Financial-messaging security controls (segmentation, MFA)." },
    { fw: "RBI CSF + FREE-AI", how: "Bank cyber resilience + responsible AI (fail-closed, explainable, India residency)." },
    { fw: "RBI Master Directions", how: "KYC, IT Outsourcing, IT Governance, Digital Payment Security Controls." },
    { fw: "SEBI CSCRF", how: "Market-participant cyber resilience: SOC, VAPT, governance." },
    { fw: "CERT-In 2022", how: "≥180-day log retention; 6-hour incident reporting." },
    { fw: "DPDP Act 2023 / Rules 2025", how: "PII minimised/redacted at the boundary; Red-tier stays on-prem; DPIA." },
    { fw: "IT Act 2000 / PMLA", how: "Reasonable security practices (43A); AML/KYC auditable trails." },
    { fw: "GDPR", how: "Privacy-by-design for EU personal data." },
    { fw: "TOGAF / COBIT 2019 / ITIL 4", how: "How it's architected, governed and run (review cadence)." },
    { fw: "MITRE ATLAS/ATT&CK · OWASP · CSA", how: "Threat modelling and AI/app/cloud control matrices." },
  ],

  // The gradual path. Each phase is independently useful; `trigger` gates the next.
  roadmap: [
    { phase: "Phase 0", stage: "CRAWL", cost: "₹0", title: "Foundation on the laptop (NOW)",
      items: ["AI range (done)", "Ollama + LiteLLM + Open WebUI + AnythingLLM", "n8n five workflows", "Obsidian second brain", "Guiding-Map PWA + personal-rnd"],
      trigger: "Need always-on / family / remote access" },
    { phase: "Phase 1", stage: "WALK", cost: "one-time HW (opt.)", title: "Always-on core",
      items: ["Mini-PC / server (or cloud VM)", "Keycloak identity spine", "Wazuh + Suricata + MISP + TheHive", "Prometheus + Grafana + Loki", "OpenBao + restic backups"],
      trigger: "Multiple workloads / team / client pilot" },
    { phase: "Phase 2", stage: "RUN", cost: "pay-as-you-go ≤₹2,500/mo", title: "Cloud + orchestration",
      items: ["k3s / cloud VM", "Argo CD GitOps", "Prowler + OpenSCAP + immudb", "Shuffle SOAR", "PostgreSQL + MinIO (WORM)"],
      trigger: "HA / DR / regulated-client SLA" },
    { phase: "Phase 3", stage: "RUN+", cost: "elastic", title: "Hardened Kubernetes, multi-cloud",
      items: ["EKS/GKE/AKS via Terraform", "Zero-trust + full policy-as-code", "DR drills + chaos testing"],
      trigger: "Paying clients" },
    { phase: "Phase 4", stage: "FLY", cost: "revenue-funded", title: "Multi-tenant MSSP",
      items: ["Per-tenant isolation + SSO", "Subscription module enable/disable", "Billing + SLA dashboards", "Thought-leadership / BD engine"],
      trigger: "—" },
  ],
};
