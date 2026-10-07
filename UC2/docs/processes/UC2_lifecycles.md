# UC2 lifecycle contracts

| Entity | States | Required transition rule |
|---|---|---|
| Passive observer | available, degraded, unavailable | Degraded/unavailable produces explicit missingness; never transmits. |
| Pseudonymous hypothesis | candidate, associated, classified, expired | Association precedes classification; expiry prevents reuse. |
| Approval state | approved, unapproved, unknown, stale | Unknown/stale fails closed to review, not certainty. |
| Alert | candidate, raised, reviewed, closed | Raised only from observable evidence and declared thresholds. |
| Policy action | requested, authorized, applied, failed, expired | Applied remains non-RF and requires authorization/capability. |
| Evidence | eligible, collected, verified, quarantined, disposed | Hash/custody failure leads to quarantine. |
| Twin | synchronized, stale, degraded | Only newer observable state can synchronize. |
