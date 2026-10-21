# 99 · Names, not ports, and links that never break

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested: docs links to repository files go to GitHub and the strict build fails on any broken link or anchor; tools/linkcheck.py checks every page of the built site (0 broken of about 19,800) and, weekly, the links to other sites; the site and README use your domain only after ./securax site live proves it serves the site; ./securax names is asked once with a one-click move of the Life OS data; fitness no-raw-addresses keeps localhost:PORT away from people; the cockpit's Names and site panel diagnoses names, certificate, resolution and the site. DNS-issued certificates for a private sub-domain are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:**
- Every address should be a name, like `https://hub.securax.localhost` today and `https://hub.example.org` on your own domain, never `localhost:8088`.
- Every page linked from the GitHub intro must open, with or without a custom domain.
- Mapping your own domain must take the least possible effort.
- Bring the maturity of similar tools, and keep the estate building itself without Claude Code.

## 1. What was wrong, found by opening every page

| Symptom | Cause | Now |
|---|---|---|
| A crawl of the published site found 10 pages that answered 404 | Docs linked to repository files outside `docs/` (`GETTING-STARTED.md`, `BUILD-CONTRACT.md`, `portal/`…). Those links work on GitHub but not on the site, and the build only *noted* them (`not_found: info`) | A build hook sends those links to the file on GitHub. The strict build now **fails** on any link to a page, file or anchor that exists nowhere |
| 117 links on the site and README went nowhere | Every link was written as `https://<brand domain>/…`, but that domain has no DNS records yet | Links use the domain only once it is **live** (`SITE_LIVE=yes`, set by `./securax site live` after a real check). Until then they use the GitHub Pages address, which always works |
| 8 links to other sites were dead (404 or 410) | Pages moved or were removed upstream | Replaced or removed; a weekly CI run now lists dead outside links |
| The changelog's release links were 404 | They pointed at tags that were never created | They point at the release commits |
| The estate still showed `localhost:8088` | Names were opt-in, and `tls on` stopped when Windows held port 80 (fixed in #122) | Asked once, default yes, with a one-click move of the Life OS data; every printed address goes through one function |

The check is repeatable: `bash website/build.sh` builds the site and runs `tools/linkcheck.py`. On the build that shipped with this change: 120 pages, about 19,800 internal links and anchors, 0 broken.

## 2. Names on this machine

```bash
./securax names            # or just ./securax go: it asks once, default yes
```

- **The names:** hub, chat, docs, flows and the others become `https://NAME.securax.localhost`. `.localhost` needs no DNS: Chrome, Edge and Firefox send every `*.localhost` name to this machine by themselves (RFC 6761). Safari's behaviour varies by macOS version.
- **Why not `.local`:** that suffix belongs to multicast DNS (Bonjour, Avahi). Names under it fight with printers and routers on the same network.
- **The certificate:** comes from the estate's own authority. That authority can vouch only for local names, by a name constraint. `tls trust --apply` adds it to Windows for your user.
- **Your Life OS data moves in one click:**
  1. Browsers keep data per address.
  2. For 30 days the old `http://localhost:8088` keeps answering on this machine only.
  3. It shows **Move my data there**. One press opens the new address, and the old page hands the data over directly, browser to browser.
  4. The new page accepts data only from a loopback address named in its own link, and only from the window that opened it. It never replaces data it already has without a yes.
- **Port 80 held by Windows:** the redirect moves to 8880 and HTTPS stays on 443 (doc 40).
- **One rule for every address a person is shown:** the shell's `web_url` and `governance/addr.py`. The fitness check `no-raw-addresses` fails CI if a new `localhost:PORT` is printed for a person.

## 3. Your own domain, with the least friction

One domain value, `SITE_DOMAIN` in `brand.env`, drives three things.

| What | How it gets your domain | Effort |
|---|---|---|
| **The product site and docs** | `./securax site domain example.org` prints the exact DNS records (GitHub Pages A, AAAA and www) and the one GitHub setting. `./securax site live` checks that the domain resolves and serves this site over HTTPS, and only then switches every link | Add the DNS records once, tick one setting, run one command |
| **The estate, from any device** | `./securax online setup` (doc 85): `https://hub.example.org` through a Cloudflare tunnel with sign-in in front | One command, with your Cloudflare account |
| **Names on this machine** | `.localhost` by default, so nothing to set. A private sub-domain such as `home.example.org` needs local DNS (`tls on --domain`) | Optional |

Until `site live` succeeds, no page, README or doc links to the domain. `./securax site off` goes back in one step, and the domain stays set for later.

## 4. What similar tools do, and what we took

| Tool | How it names apps | What we took |
|---|---|---|
| **Cloudron** | A sub-domain per app on your domain, with DNS records made through the DNS provider's API and certificates issued by itself | A sub-domain per app (already the edge's design). DNS through the provider's API waits for licensing and hosting (doc 97) |
| **YunoHost** | Issues Let's Encrypt certificates only after its own diagnosis has checked the DNS and web reachability | `site live` refuses to switch until DNS and HTTPS are proven: check first, then switch |
| **Coolify** | A generated sub-domain per app on a wildcard domain, or a throw-away `sslip.io` name for testing, all through its proxy | Names first, ports never. The local default needs no DNS at all |
| **Caddy** | A local authority for local names, installed into the system trust store once | The estate's own name-constrained authority plus `tls trust --apply`. Done since doc 40 |
| **Umbrel, CasaOS** | `umbrel.local:PORT` or `IP:PORT` per app | What we avoid: ports in addresses, and `.local` |

**Still to do, with a date:**
- **Diagnosis page (done 2026-10-21):** the cockpit's folded **Names and site** panel checks names, the certificate, name resolution, device trust and the site, each with the one command that fixes it (`governance/diagnose.py`), in the way YunoHost presents its checks.
- **Certificates for the domain (2027-01-31):** certificates for `home.example.org` issued through a DNS challenge, so other devices on your network need no extra trust step.

## 5. Why this needs less Claude Code next time

The fixes are checks that run by themselves. They are not rules someone has to remember.
- **Docs build:** `mkdocs build --strict` fails on any broken link or anchor.
- **Site build:** `tools/linkcheck.py` fails on a missing page or image, or a link to a domain that is not live yet.
- **Weekly CI run:** lists dead links to other sites.
- **Every change:** the fitness check `no-raw-addresses` fails a raw `localhost:PORT` shown to a person.
- **AGENTS.md:** states both rules, so `./securax autobuild` and OpenCode follow them. CI catches whoever forgets.

## 6. Proof

- **`governance/tests/test_names_and_links.py`:**
  - the site address is the domain only once live;
  - `site live` refuses until the domain serves the site, and keeps `brand.env`'s comments;
  - the link checker finds a missing page, image and anchor, and a link to a domain not live yet, and it follows the site's base folder;
  - repository links leave the docs for GitHub, and code blocks are never touched;
  - a person is shown a name once names are on;
  - the README links only to what exists and is live.
- **`guiding-map/tests/test31.js`:**
  - the old address offers one move button;
  - only plain-http loopback addresses may hand data over;
  - data from any other origin is refused;
  - only text values are written;
  - the old page is told how many items moved.
- **`website/build.sh`:** runs the link checker on every docs build in CI.

## Sources

- [GitHub Pages: managing a custom domain (A, AAAA and CNAME records)](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [Daniel Stenberg: browsers and `*.localhost` (RFC 6761)](https://daniel.haxx.se/blog/2021/05/31/)
- [Mozilla bug 1220810: Firefox resolves `localhost` names itself](https://bugzilla.mozilla.org/show_bug.cgi?id=1220810)
- [WebKit bug 160504: Safari and `*.localhost`](https://www2.webkit.org/show_bug.cgi?id=160504)
- [Caddy: automatic HTTPS and its local authority](https://caddyserver.com/docs/automatic-https)
- [Cloudron: domains and DNS providers](https://docs.cloudron.io/domains/)
- [YunoHost: certificates rely on the diagnosis](https://forum.yunohost.org/t/lets-encrypt-certificate-wont-renew-for-subdomain-no-diagnosis-result/29204)
- [Coolify: domains, wildcard and sslip.io](https://coolify.io/docs/knowledge-base/domains)
- [Umbrel: connecting to your Umbrel](https://umbrel.com/support/getting-started/connecting-to-your-umbrel)
