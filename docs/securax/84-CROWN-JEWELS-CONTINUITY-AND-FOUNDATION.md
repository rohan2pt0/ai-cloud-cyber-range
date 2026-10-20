# 84 · Crown jewels, the crisis plan, and the foundation for scale

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: crown jewels ranked from live checks, the continuity plan with measured RPO and timed drills, the nightly code bundle and mirror (GitHub-down drill proven), nightly backups with the CA, the password manager (Vaultwarden 1.37.4, started and answering), cloud sign-in and names in one step, the Life OS Inbox with reviews that become actions and Google Keep import, SEO basics on the site. The identity broker, CRM, marketing, analytics and telephony are decided and dated, not built. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:**
- Know what the estate cannot lose, and rank its risks without anyone re-scoring them by hand.
- Have every crisis planned before it happens, with recovery times you can prove.
- Remove the friction a user meets (passwords, cloud sign-in, addresses).
- Lay the foundation now (identity, customers, marketing, telephony) so nothing has to be bolted on later.

## 1. Crown jewels: what SecuRAX cannot lose

`./securax jewels` checks the estate every time it runs and ranks what matters, worst first, with the one command that fixes each.

| Jewel | Why it matters | Single point of failure? | The fix |
|---|---|---|---|
| **Your data** (chats, workflows, registers, vault) | Years of work; code can be rebuilt, this cannot | Yes | `./securax protect`: encrypted nightly backups, a daily off-site copy |
| **The backup key** | Every encrypted backup opens only with it | Yes | A second copy away from the laptop; `./securax backup drill` each quarter |
| **The code and its history** | Everything runs from it; it lived on one laptop and one GitHub account | Yes | `./securax continuity mirror`: a code bundle in every backup folder, plus a second git host |
| **The keys in .env** | Whoever holds them spends your money and reads your traffic | No | Replace the shipped defaults; `.env` readable only by you |
| **The laptop** | The only machine running the estate | Yes | Off-site backups plus a recorded working version |
| **A version known to work** | Without one, a bad change means debugging under pressure | No | `./securax up` once healthy (doc 82) |
| **Access to AI models** | One provider is one point of failure | No | Two cloud providers on the build chain, local as the floor |
| **Your accounts** (Google, Microsoft, GitHub, Tailscale, clouds) | A lock-out stops sign-in, sync or updates | Yes | Recovery codes in the estate's password manager |
| **Free disk space** | A full disk stops the databases | No | The 6-hourly clean-up (doc 80) |

**How it scores, so you can trust the order:**
- **Likelihood** starts at 1. Each failed check adds 2, and a check that cannot be told adds 1. The most is 5.
- **Score** = impact × likelihood, × 1.5 for a single point of failure.
- **Priority:**
  - **DO NOW:** 15 or more
  - **THIS WEEK:** 8 to 14
  - **WATCH:** below 8
- **It re-scores itself.** Fix something and the ranking moves on the next run. Nobody re-scores by hand.

The jewels are data: `governance/jewels.json`. A new tool you onboard adds one entry: what it holds, its impact, and its checks.

**Found while building this, and fixed:**
- **The private TLS CA key was in no backup.** Losing it meant every device trusting a new certificate. Backups now carry it, and `restore` brings it back.
- **Backups ran once a week,** so a lost laptop could cost seven days. They now run every night.
- **When GitHub was unreachable, `update` said "you may have local changes".** It now names the real cause, and the steps to follow.

## 2. The crisis plan: every scenario, measured

`./securax continuity` lists each crisis with two targets:

- **RTO:** the most time it may stop you.
- **RPO:** the most data it may lose.

Next to each target it shows what is true **today**. RPO is measured from your newest backup, off-site copy and code bundle. RTO is proven only by a drill: a scenario never drilled reads "not proven".

| Scenario | RTO | RPO | Safe drill |
|---|---|---|---|
| A change or update broke the estate | 15 min | none | `rollback --check` |
| GitHub is down, or the account is lost | 1 h | 1 day | clone the code bundle and check it is whole |
| The laptop is lost, stolen or dead | 4 h | 1 day | open the off-site backup with the key |
| Data corrupted, deleted or encrypted | 2 h | 1 day | the same restore drill |
| The backup key is lost | 30 min | none | the same restore drill |
| An AI provider is down, or a key is revoked | none (automatic) | none | list which models answer |
| The disk is full | 30 min | none | the storage report |
| The estate may be compromised | 1 h | none | (a real stop; walk the steps instead) |
| Locked out of a key account | 1 day | none | the password manager answers |

- **The steps:** `./securax continuity show ID`, written to be read during the crisis.
- **The drills** (`./securax continuity drill ID`) never change your data. Each is timed and recorded.
- **What runs by itself:**
  - the code mirror every night
  - the GitHub-down drill every month
  - the restore drill every quarter
  - the rollback check every week
- **Failures reach your phone** through the andon.

### If GitHub fails tomorrow

1. **Nothing stops.** The estate runs from your laptop; GitHub is only where updates come from.
2. **The code exists outside GitHub:**
   - a verified bundle of every branch in your backup folder and your off-site folder, refreshed nightly
   - a private **GitLab** project, pushed to daily: `./securax continuity mirror setup` walks you through it once (about five minutes)
3. **Keep working:** commits stay local, and `./securax verify` runs every check on the laptop.
4. **On a new machine:** `git clone repo-latest.bundle ai-cloud-cyber-range`, then `./securax restore <off-site backup>`.
5. **Still dependent on GitHub (dated below):**
   - the CI pipeline
   - the public website (GitHub Pages)
   - container images on ghcr.io (Docker Hub copies come next)

## 3. Less friction: tools set up for you, not advice

| You used to be told | Now SecuRAX gives you |
|---|---|
| "Use a password manager" | `./securax start passwords`: your own **Vaultwarden** (1.37.4, the current release with October 2026's security fixes), for the official Bitwarden apps on laptop, phone and browser. The vault is encrypted on your device before it is stored; `./securax passwords lock` closes sign-ups after your account. It is in every backup |
| "Install the AWS, Google and Azure tools" | `./securax cloud login aws`, `gcp` or `azure`: the official CLI runs in a pinned container (AWS 2.38.2, Google 589.0.0, Azure 2.91.0). Open the link on any device and sign in. Your sign-in stays in `~/.securax/cloud`, never in the repository. Then: `./securax cloud aws s3 ls` |
| Notes in Google Keep that never become anything | The Life OS **Inbox**. Capture one line, then decide it: an action with a next physical step and a date, a note to keep, or delete. **Run a review** walks any ritual (Red-Team Your Life, the Quarterly Review…) step by step; each finding becomes an action due in a week. `./securax lifeos import keep` brings your Keep export (Google Takeout) into the Inbox: unticked list lines as actions to decide, notes as notes. Today shows what is due or waiting |
| `http://localhost:8088` | `./securax names`: one guided step to `https://hub.securax.localhost`, `https://chat.…`, `https://pass.…` (it warns first that the Guiding Map's browser data must be moved to the new address) |

**How the cloud sign-ins work:**
- **AWS:** `aws login --remote`, with your console account; credentials refresh for up to 12 hours.
- **Google Cloud:** `gcloud auth login`, plus application-default credentials for tools like Terraform.
- **Azure:** `az login --use-device-code`.

## 4. The foundation for scale: decided now, built in stages

Bolting identity or customer data on later is what breaks products, so each decision below is made now. Each part is built when its stage begins: on a 16 GB laptop they would compete with the estate for memory.

| Layer | Decision | Why this one | Stage |
|---|---|---|---|
| **Sign-in for every user (SSO)** | **Keycloak**, already in the estate's `sprout` stage, as the single identity broker. Users sign in with Google, Microsoft, Apple or e-mail; every app (Chat, the Command Center, Mattermost, the gateway) trusts Keycloak through OIDC | Apache 2.0; the most mature for SAML, LDAP and Active Directory federation and multiple realms (one per client organisation); fast logins in an October 2026 benchmark. The gateway already accepts OIDC tokens (doc 36) | Next: wire Google and Microsoft into Keycloak and Open WebUI's OIDC |
| **Customer records (CRM)** | **Twenty** (developer-first, TypeScript, GraphQL and REST) for SecuRAX's own sales; **EspoCRM** where non-technical teams must configure it themselves | Both self-hosted, so customer data stays in India; both top 2026 comparisons | When the first paying customer signs |
| **Marketing automation** | **Mautic** (campaigns, e-mail journeys, lead scoring) with **Listmonk** for newsletters | Open source, self-hosted, keeps consent records next to the data | With the CRM |
| **Web analytics** | **Matomo** (self-hosted, no cookies needed for basic counts) | DPDP-friendly; no data to a third party | With the product site's launch |
| **SEO** | The site has a canonical address, a sitemap, `robots.txt` and structured data (SoftwareApplication); the docs build their own sitemap | Search engines index what they can read | **Built** |
| **Telephony, IVR and voice bots** | **Asterisk** (with FreePBX to run it) and an AI voice-agent sidecar over AudioSocket. Speech through the gateway: Indian languages via Sarvam's models, or local Whisper and Piper for private calls | Asterisk is the most approachable start; the sidecar pattern keeps the AI behind the same guardrails | After the CRM. It needs a licensed Indian SIP trunk provider |
| **Data and analytics** | Every product writes events to one store (Postgres first, ClickHouse when volume needs it); dashboards in the cockpit; models trained only on consented data | One place to answer "what do customers do", without copying data around | With the CRM |

**Rules that come with calling or messaging customers in India.** Build these in from day one:
- **Telemarketing:** TRAI's rules (TCCCPR 2018, amended February 2025) require registration on the DLT platform, registered templates and headers, and the designated **140** (promotional) and **160** (service and transactional) number series for commercial calls.
- **Consent:** explicit consent for a commercial transaction is valid for 7 days. A third amendment was in draft in 2026.
- **AI calls are not exempt:** a clean consent log does not replace DLT registration.
- **Data:** the DPDP Act needs recorded consent, purpose limits and deletion on request, so the CRM and the call recordings must log all three.
- **This is not legal advice:** confirm with counsel before the first campaign.

### Two decisions taken for you (20 October 2026)

**The second git host is a private GitLab.com project.**
- **Why GitLab:**
  - private projects are free
  - a 10 GiB repository limit, against a SecuRAX history well under 1 GiB
  - deploy keys with write access on the free tier
  - you can sign in with Google
- **Why not Codeberg:** it is a good home for free software, but its rules allow only manual mirrors (our mirror runs daily), and its 2026 terms debate on AI-written code puts this repository at risk.
- **The key:** a dedicated SSH key that can push to that one project and nothing else. It is not your password. If it leaks, delete it in GitLab; nothing else changes.

**The old history is not rewritten.** The agency name you asked to drop is gone from every current file, and the private-names check stops it coming back. Rewriting the old commits would cost more than it buys:
- **It would not remove the name.** GitHub keeps the old commits reachable from the 135 pull-request records, its cached views and any clone. GitHub Support purges those only for sensitive data such as credentials,, and an agency name is not that.
- **It would break what works:**
  - every recorded working version that `./securax rollback` returns to (they are commit IDs)
  - the released tags
  - the GitHub-down bundle
  - every clone you have
- **If you ever need the history gone:** the clean way is a new repository started from today's code, not a rewrite. That is a decision to take with counsel, not by default.

## 5. Next steps (dated)

| By | Step |
|---|---|
| 2026-11-15 | Keycloak with Google and Microsoft sign-in; Open WebUI and the Command Center behind it |
| 2026-11-30 | Container images mirrored to Docker Hub, so ghcr.io is not a single point of failure |
| 2026-12-15 | The cockpit shows the top crown jewel and every continuity scenario over target |
| 2027-01-31 | CRM (Twenty), Mautic and Matomo as dormant organs, pinned and checked like the others |
| 2027-03-31 | Asterisk and the voice-agent sidecar in the lab, with DLT-registered numbers before any real call |

## Sources

- [GitLab deploy keys](https://docs.gitlab.com/user/project/deploy_keys/) (write access on Free); [GitLab usage quotas](https://docs.gitlab.com/ee/user/usage_quotas) (10 GiB per project); [Codeberg FAQ](https://docs.codeberg.org/getting-started/faq/) (licences, no automatic mirrors)
- [GitHub: removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) (pull-request refs and cached views survive a rewrite)

- [Vaultwarden releases](https://github.com/dani-garcia/vaultwarden/releases): 1.37.4, 5 October, with seven security fixes
- [AWS CLI `aws login`](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html) and its [reference](https://docs.aws.amazon.com/cli/latest/reference/login/)
- [Keycloak, authentik and Zitadel compared](https://computingforgeeks.com/?p=173202); [authentik vs Zitadel](https://wz-it.com/en/blog/authentik-vs-zitadel-identity-provider-comparison/); [Open source authentication in 2026](https://skycloak.io/?p=3288)
- [Open-source CRM benchmark 2026 (Marmelab)](https://marmelab.com/blog/2026/01/09/open-source-crm-benchmark-2026.html); [self-hosted CRMs tested (Techsy)](https://techsy.io/en/blog/open-source-crm-startups)
- [Asterisk AI voicebot with AudioSocket](https://community.asterisk.org/t/build-a-real-time-ai-voicebot-with-asterisk-audiosocket-stt-llm-tts-or-sts/109373); [Sarvam on LiveKit](https://www.sarvam.ai/integrations/livekit); [open-source AI phone receptionist](https://justcall.io/blog/open-source-ai-phone-receptionist.html)
- [TRAI's crackdown on spam and AI telemarketing (Bar & Bench)](https://www.barandbench.com/view-point/trais-crackdown-on-spam-calls-and-ai-driven-telemarketing); [TRAI consultation, 2026 draft amendment](https://www.trai.gov.in/sites/default/files/2026-04/Exotel_TRAI_TCCCPR_Comments_v2.pdf)
