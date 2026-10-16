# 60 · Ship it on cyberbaba.org, and build SecuRAX with SecuRAX

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The site, its build and the build loop exist; going live needs your Cloudflare Pages setup, and the queued builds are not done. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Two things happen in this guide. The product site and the documentation go live on **your own domain**. Then all further
development moves to the **SecuRAX build agent on your laptop**, so you no longer need a paid coding subscription.

## 1. The product site on cyberbaba.org

**Approach: Cloudflare Pages.** Your domain's DNS is already on Cloudflare, so Pages is the shortest path: free, global,
automatic HTTPS, rebuilt on every merge to `main`, and no server to patch. One project serves both:

| Address | What | Source in the repo |
|---|---|---|
| `https://cyberbaba.org/` | the product site (Mattermost-style: hero, proof, platform, deploy, security, editions, FAQ) | `website/index.html` |
| `https://cyberbaba.org/docs/` | this documentation | `docs/` + `mkdocs.yml` |

**Never publish the estate itself** (chat, gateway, app) on this domain. It stays on your machines, behind Tailscale.

### Steps (about 15 minutes, once)

1. **Cloudflare dashboard → Workers & Pages → Create → Pages → Connect to Git.** Pick `rohan2pt0/ai-cloud-cyber-range`,
   branch `main`.
2. **Build settings:**

    | Setting | Value |
    |---|---|
    | Framework preset | None |
    | Build command | `bash website/build.sh` |
    | Build output directory | `website` |
    | Environment variable | `PYTHON_VERSION` = `3.12` |

3. **Save and Deploy.** The first build takes about 2 minutes. You get a `*.pages.dev` address to check first.
4. **Custom domains → Set up a custom domain → `cyberbaba.org`**, then add `www.cyberbaba.org` too. Cloudflare creates the
   DNS records itself, because the zone is already there.
5. **SSL/TLS → Overview: Full (strict).** Under **Edge Certificates**, turn on **Always Use HTTPS** and **HSTS**. The site
   already sends HSTS, and other security headers, from `website/_headers`.
6. **Contact address:** **Email → Email Routing → enable**, then route `hello@cyberbaba.org` to your Gmail. It is free,
   and the site's "Talk to an expert" buttons use it.

Namecheap stays the registrar. Do not change anything there while its nameservers point to Cloudflare.

??? note "Or keep GitHub Pages for the docs"
    The `docs` workflow can still publish to GitHub Pages (`DOCS_PAGES=true`). Cloudflare Pages is simpler because one
    project serves the site and the docs on one domain. Use one or the other, not both.

### What the site claims, and what it does not

Every claim on the site is true today, and its capability cards use the same 🟢🟡🔴 lights as the docs. There are no
customer logos and no certifications. The compliance section says "mapped with linked evidence, not certified".
Update `website/index.html` when a light changes, together with `docs/status.yml`.

## 2. Build SecuRAX with SecuRAX (leaving Claude Code)

The build loop already exists. Your free and cheap models write the change, and the same gates that guard every PR decide
whether it is kept:

```text
your task → build agent (free models via the gateway) → verify → diffcheck → forge → commit only if green → you push → CI → you merge
```

### One-time setup on the laptop (WSL)

1. **Let git push as you.** Pick one:

    === "GitHub CLI (simplest)"

        ```bash
        sudo apt install gh
        gh auth login
        ```

    === "SSH key"

        ```bash
        ssh-keygen -t ed25519 -C "securax-laptop"
        cat ~/.ssh/id_ed25519.pub
        ```

        Add the printed key under GitHub → Settings → SSH and GPG keys, then:

        ```bash
        git -C ~/securax remote set-url origin git@github.com:rohan2pt0/ai-cloud-cyber-range.git
        ```

2. **Check the build chain** (Groq first, then NVIDIA NIM, DeepSeek, Gemini, OpenRouter, ending on local):

    ```bash
    ./securax providers chain builder show
    ./securax opencode --check
    ```

3. **Protect `main` on GitHub:** Settings → Branches → add a rule for `main` that requires the CI checks to pass. Then
   nothing reaches `main` without the full suite and the real-estate sandbox going green.

### The everyday loop

```bash
cd ~/securax
git checkout -b feat/regulator-watch
./securax autobuild "add a regulator watch: fetch the RBI, SEBI and CERT-In RSS feeds daily, keep new items, show them in the cockpit; tests for parsing and de-duplication" --tries 3
git push -u origin feat/regulator-watch
```

`autobuild` commits only when every check is green. It never pushes on its own, and after the tries it writes an
escalation brief instead of a broken commit. Open the pull request on GitHub, wait for CI, then merge.

For interactive work, use `./securax opencode`, a terminal coding agent where every call goes through the gateway.

### Cancel the paid subscription

On claude.ai: **Settings → Billing**. Keep **usage-based credits off** until you cancel. Only you can change billing.

## 3. The next builds, queued for the SecuRAX build agent

Easiest and most valuable first. Each line is a ready `autobuild` task.

| # | Task | Light today |
|---|---|---|
| 1 | **Regulator watch:** RBI, SEBI and CERT-In feeds → `vault/regwatch.json` → a cockpit tile and an ntfy alert on new items; never summarise without the source text | 🔴 |
| 2 | **Update the site's numbers from CI:** test and journey counts written into `website/index.html` by a script, with a test | 🔴 |
| 3 | **Central logs:** wake the sprout's Prometheus and add a log store; `./securax logs` | 🟡 |
| 4 | **Keycloak SSO + MFA for Chat and the gateway** (`./securax grow sprout`) | 🟡 |
| 5 | **Voice:** local speech-to-text and text-to-speech for the Twin | 🟡 |
| 6 | **Family Android app:** a trusted-web-activity wrapper of the PWA | 🔴 |

Day-to-day setup on your devices (phones, alerts, data entry) is covered in the [Quickstart](../get-started/quickstart.md)
and [doc 58](58-PHONES-AND-REMOTE-SHELL.md).
