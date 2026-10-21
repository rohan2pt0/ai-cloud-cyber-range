# {{ORG}} · API Security Checklist (before go-live, and on every change)

Aligned to the OWASP API Security Top 10. Every item: Pass / Fail / Not applicable, with evidence.

| # | Check |
|---|---|
| 1 | The API is in the API inventory with an owner, a data classification and its consumers |
| 2 | Every request is authenticated (OAuth 2.0 / mTLS for partners); no API keys in URLs |
| 3 | Object-level authorisation: a caller can only reach their own records (tested by changing IDs) |
| 4 | Function-level authorisation: admin functions are not reachable by normal users |
| 5 | Responses return only the fields needed; no internal IDs, stack traces or secrets |
| 6 | Input is validated against a schema; unexpected fields are rejected (no mass assignment) |
| 7 | Rate limits and quotas per caller; protection against enumeration and brute force |
| 8 | TLS 1.2 or higher only; strong ciphers; HSTS where relevant |
| 9 | Sensitive data is masked in logs; requests and responses are logged to the SIEM |
| 10 | Server-side request forgery is prevented (outbound calls go only to allowed destinations) |
| 11 | Old and test versions are retired; no undocumented ("shadow") endpoints |
| 12 | Third-party APIs consumed are treated as untrusted input |
| 13 | Security tests (DAST / API scan) pass with no critical or high findings |
| 14 | A WAF or API gateway policy protects it at runtime |
