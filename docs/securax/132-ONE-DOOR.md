# 132 · One door — sign in once, reach everything, take it away in one place

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** The one-door principle (sign in once with an account you already have; everything else comes through that one sign-in, asked for at the moment of use with the narrowest permission, and taken away in one place; everything works as a guest first) is a core principle carried into every app and held by fitness signin-declared. governance/identity.json declares every service the estate reaches, so onboarding a feature that needs a sign-in is one entry and never a new login screen or a stored password; the check refuses incomplete entries, over-broad permissions, an overdue fix date, and any new separate login (the count only goes down). The friction register is honest: AWS, Google Cloud, GitHub and the free AI provider keys are still separate, each with a fix and a date or a standing reason. Not built yet: the single Accounts panel and incremental-consent flows, and SCIM (planned). Tests: test_identity_registry.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The friction.** AWS, Google Cloud, Azure, Microsoft, Gmail, Tailscale, Cloudflare, GitHub: each asked for its own login. The
model to copy is a screen with **one button per account you already have** (a passkey, Microsoft, Google), and a way in with no
account at all. This is now a core principle, `one-door`, carried into every app and held by a fitness check.

## What a person sees

1. **Open it and use it.** Every feature works as a guest first, with nothing to sign in to for the basics. The Life OS and the
   Command Center door already do.
2. **Sign in once, when it adds something.** One choice: **Continue with Microsoft**, **Continue with Google**, or a **passkey**.
   Signing in adds sync, your own AI allowance, and your own machines.
3. **Extra services are asked for at the moment you use them.** Turn on Drive sync and only then does it ask "let SecuRAX keep one
   folder of yours?", for that one narrow permission. Nothing is asked up front "just in case".
4. **Taking it away is one place.** Remove the person from the one identity and everything behind it stops. Each service lists
   exactly where its own grant is revoked.

## The standards it follows

| Standard | In practice |
|---|---|
| OpenID Connect, authorization code with PKCE | The only way a browser app signs in. No passwords, no implicit flow |
| Passkeys (WebAuthn) | The first factor wherever the provider offers it: nothing to phish, nothing to remember |
| Incremental authorization, least privilege | A permission is asked for when the feature is used, and it is the narrowest one. The check refuses `*`, "all mail", "all drive" |
| Short-lived tokens, checked by the receiver | The gateway verifies the sign-in token itself, then treats the visitor as that person (built) |
| SAML 2.0 for enterprise apps | For AWS and the like, through their single sign-on service |
| SCIM for joiners, movers and leavers | Planned (the suite's `scim` service, 2027-06-30): offboarding is a manual step until then |

## Where you are today

The estate already has the hard parts: an `identity` service (OIDC single sign-on, MFA, device and API keys) and a gateway that
accepts a Cloudflare Access sign-in as "the signed-in person". The register of every service, and which ones are **not** yet
through the one door, is `governance/identity.json`. Each separate login carries its fix and a date, or a standing reason; the
check fails when one is overdue and when a new one appears.

| Reached through the one door | Still separate, and why |
|---|---|
| The Life OS and Vantage (Microsoft sign-in for OneDrive sync) | **AWS**: its own identity. Fix: IAM Identity Center with the one door as its sign-in. It needs AWS Organizations and supports SAML 2.0 and SCIM ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/workplace-iam-identity-center.html)) |
| The Command Center door (no account at all) | **Google Cloud**: a Google account. Fix: make Google the one door, or Workforce Identity Federation, which needs a Google Cloud organization ([Google](https://cloud.google.com/iam/docs/workforce-sign-in-microsoft-entra-id)) |
| Your own addresses (Command Center, Chat) through Cloudflare Access | **GitHub**: a personal account has no company single sign-on. Standing answer: a passkey on it |
| The AI gateway | **Free AI provider keys**: each provider issues its own. Standing answer: one place to keep them (`./securax keys`), and the local model needs none |
| Tailscale, and Azure, signed in with the same account | |

## The 15 minutes that remove most of it (no code)

The default one door is **Microsoft**, because your Azure app and OneDrive sync already use it. Switching to Google later is one word
(`primary_idp`) and one sign-in method on Cloudflare Access.

1. **Add a passkey** to that Microsoft account, in its security settings. From then on a fingerprint or a face is the whole sign-in.
2. **Cloudflare Zero Trust**: add Microsoft Entra ID as the login method for your Access application ([Cloudflare Access](https://developers.cloudflare.com/access/)
   takes any OIDC or SAML provider and has Entra built in). Once it works, remove the one-time code. Note that Cloudflare now
   offers itself as the default identity provider for new accounts ([changelog](https://developers.cloudflare.com/changelog/post/2026-05-19-cloudflare-as-identity-provider/)):
   choose Microsoft, so your sign-in is the one you already protect with a passkey.
3. **Tailscale**: sign in with that same account.
4. On every site that offers it, choose **Continue with Microsoft**. Never create a new password.

## Onboarding a new feature: one entry

A feature that needs a sign-in does not build a login screen and does not keep a password. Add one entry to `governance/identity.json`:

```json
"drive-sync": {
  "name": "Drive sync", "provider": "google", "protocol": "oauth2-pkce",
  "scopes": ["https://www.googleapis.com/auth/drive.appdata"],
  "guest": "everything else keeps working; nothing is asked until you turn it on",
  "signed_in": "your data follows you across devices through your own Drive",
  "login": "primary", "revoke": "disconnect in the app; remove the app's access in your Google account", "status": "planned"
}
```

Then run `./securax fitness`. It fails if a field is missing, if the permission is broader than the feature needs (`*`, all mail,
all drive), if a separate login has no fix date, or if the count of separate logins went up.

## Offboarding

Remove the person from the one identity, run `./securax online remove <email>` for the Access list, and revoke what the registry's
`revoke` column names for each service. Device and API keys are revoked in `./securax`.

## What this does not do

- It cannot make AWS, Google Cloud, GitHub or a third party's API key stop being a separate identity for a personal account. It
  lists each one, gives the way to federate it, dates it, and refuses to let the list grow.
- The glass pane itself, one panel that shows what you are signed in to with a connect and disconnect for each, reads this
  registry and is dated in the queue. Until then, `governance/identity.json` is the single list.
