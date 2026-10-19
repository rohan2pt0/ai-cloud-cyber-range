# 73 · Finish setting up, and publish the site

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The checklist, the file-name-free import, the phone layout and the site build are built and tested; the site goes live after your two GitHub settings (./securax finish product-site). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Every optional part of SecuRAX is listed in one place, with what it gives you, whether it is done, and the exact steps. You do one item whenever you have ten minutes; nothing needs a document hunt.

## Where you see it

- **Command Center:** a "Finish setting up · N of 10 done" banner. It opens the cockpit card, where the next item's steps are already unfolded.
- **Terminal:**
  - `./securax finish` lists what is done, what is left, and the steps of the next item.
  - `./securax finish ITEM` shows one item's steps.
- **Marking items done:**
  - Items the estate can check tick themselves: the control library, backup encryption, the off-site folder, phone alerts and the risk register.
  - Items you do elsewhere (GitHub, Cloudflare, Azure, each phone) are ticked once with `./securax finish done ITEM`, and un-ticked with `undo`.
  - Ticks are kept privately in `vault/finish.json`.

| Item | What it gives you |
|---|---|
| `control-library` | the control navigator, heat map and vital-few list |
| `backup-key` | backups that are safe to copy off the laptop (`./securax protect`, one guided step) |
| `offsite-backup` | an encrypted copy in OneDrive and a quarterly restore drill (doc 72) |
| `phone-alerts` | a nudge on your phone when something needs you |
| `risk-register` | the navigator ranks the controls that treat your biggest open risks |
| `product-site` | the public product site and docs, free on GitHub Pages |
| `own-domain` | the site on your own domain |
| `life-os-hosting` | install and update the Life OS with the laptop off (doc 72) |
| `azure-redirects` | Microsoft sign-in works at every address you open the app from |
| `onedrive-sync` | every device in step, end-to-end encrypted, with the laptop off |

## Importing a workbook no longer needs a file name

1. Save the workbook in Downloads (Windows or Ubuntu).
2. Run `./securax go`; it imports it by itself.

`./securax controls import` works the same way:
- **No path, a wrong path or a folder:** it finds the workbook in Downloads, Documents, Desktop or `vault/inbox`.
- **The wrong workbook:** it says so and looks for the right one.

`./securax risks import` follows the same rule.

## Publish the product site now, on any domain later

The site (`website/`) and the documentation (`/docs/`) are built by one script, `website/build.sh`. Every pull request builds them strictly; `main` publishes them.

**Where the domain comes from.** It is a variable, never code:
- `SITE_DOMAIN` in `brand.env`, or
- the repository variable `SITE_DOMAIN`, which wins. `CONTACT_EMAIL` works the same way.

**Moving later.** Moving to another domain changes that one value. Moving to another host, such as Cloudflare Pages (doc 60), Netlify or S3, reuses the same build command and output directory (`bash website/build.sh` → `website`). Because the build is portable, no host is a single point of failure.

**Publishing on GitHub Pages:** follow `./securax finish product-site`, then `./securax finish own-domain`. In short:
1. **Settings → Pages:** set Source to GitHub Actions.
2. **Repository variable:** add `SITE_PAGES` = `true`.
3. **Run the workflow:** Actions → docs → Run workflow.
4. **Your domain.** Set the custom domain in Settings → Pages. In your DNS, add:
   - four A records for the apex, pointing to GitHub's Pages addresses
   - a `www` CNAME to `<owner>.github.io`
   - DNS only, no proxy

   Verify the domain in your GitHub profile settings, then turn on Enforce HTTPS. GitHub lists the current addresses in its [custom domain guide](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site); they have changed before, so check there.

## The phone layout of the Life OS

- **Bottom tabs.** Four fixed tabs (Today, Goals, Ask, Ops) and More, so no tab is hidden off-screen.
- **Today.** The Daily Three and your one open action come first; everything else is behind "More today", which remembers if you leave it open.
- **Vitals.** They sit at the top of Today instead of in a second bottom bar.
- **Header.** It shrinks to one line once you scroll.

Wider screens keep the full tab strip. `guiding-map/tests/test24.js` checks all of this.
