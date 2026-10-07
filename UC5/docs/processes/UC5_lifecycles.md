# UC5 lifecycle contracts

| Entity | States | Required transition rule |
|---|---|---|
| Medical device | available, degraded, isolated, offline | Isolation requires authorization, enforcement and continuity eligibility. |
| Flow | generated, delivered, lost, overflowed | Every generated flow reaches exactly one terminal collection outcome. |
| Device health | normal, fault, missing | Fault/missing is not itself a cyberattack label. |
| Alert | candidate, raised, reviewed, closed | Raised only from observable feature score and threshold. |
| Safety decision | pending, allowed, rejected | Essential device without approved backup must be rejected for isolation. |
| Mitigation | requested, applied, failed, deferred | Applied action is distinct from request and cannot perform clinical actuation. |
| Evidence/share | eligible, collected, verified, redacted, shared, denied, quarantined | Tamper, redaction failure or absent authority prevents sharing. |
| Twin | synchronized, stale, degraded | Only newer observable state may synchronize. |
