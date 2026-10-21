# {{ORG}} · Access Control Standard

Version 1.0 · effective {{DATE}} · owner: CISO

| Control | Requirement |
|---|---|
| Identity | One identity per person, from HR records; no shared accounts; service accounts owned and documented |
| Joiner | Access granted by role, approved by the line manager and the system owner |
| Mover | Old access removed when new access is granted |
| Leaver | All access removed on the last working day (same day for terminations) |
| Authentication | MFA for remote access, email, cloud consoles, admin access and critical applications; phishing-resistant MFA for administrators |
| Passwords | At least 14 characters or a passphrase; no forced periodic change without cause; screened against breached lists |
| Privileged access | Through PAM only: vaulted credentials, just-in-time approval, recorded sessions; separate admin accounts |
| Reviews | Quarterly for critical systems and privileged accounts; half-yearly for others; results signed by owners |
| Third parties | Named accounts, time-bound, MFA, least privilege, removed at contract end |
| Monitoring | Failed logins, privilege changes and unusual access are logged and alerted |
