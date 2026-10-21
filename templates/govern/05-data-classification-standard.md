# {{ORG}} · Data Classification and Asset Criticality Standard

Version 1.0 · effective {{DATE}} · owner: CISO

## 1. Data sensitivity (S)
| Level | Label | Examples | Handling |
|---|---|---|---|
| S4 | Restricted | Customer financial and identity data, credentials, keys, Board papers | Encrypted everywhere; named access; DLP; never on personal devices or unapproved AI |
| S3 | Confidential | Internal reports, contracts, staff data | Encrypted in transit and at rest; need-to-know |
| S2 | Internal | Policies, internal communications | Inside {{ORG}} systems only |
| S1 | Public | Published material | No restriction once approved for release |

## 2. Asset criticality (C)
| Level | Meaning | Recovery time objective |
|---|---|---|
| C4 | Stopping it stops the business or breaks the law | 4 hours or less |
| C3 | Major impact on customers or revenue | 24 hours |
| C2 | Inconvenient; workarounds exist | 3 days |
| C1 | Minor | Best effort |

## 3. Priority = criticality x sensitivity
| Score (C x S) | Priority | Means |
|---|---|---|
| 12-16 | P1 | Strongest controls first; findings fixed fastest; monitored 24x7 |
| 6-11 | P2 | Standard controls; normal SLAs |
| 1-5 | P3 | Baseline controls |

Every asset in the asset inventory carries its C, its S and its priority.
