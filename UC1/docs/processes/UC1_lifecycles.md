# UC1 lifecycle contracts

| Entity | States | Key legal transitions |
|---|---|---|
| OBU | offline, initializing, trusted, degraded, isolated | initialization precedes trusted; mitigation may isolate. |
| RSU | offline, initializing, operational, overloaded, isolated | overflow may cause overloaded; policy may isolate. |
| Trust service | available, unavailable | unavailable validation fails closed. |
| Signal controller | safe_all_red, north_south, east_west, safe_fallback, offline | transitions preserve minimum duration and conflict freedom. |
| Detector | warming, monitoring, alerted, degraded | only observable features can cause alert. |
| Mitigation | inactive, requested, applied, failed, expired, rolled_back | applied requires capability and acknowledgement. |
| Evidence | candidate, eligible, collected, verified, quarantined, retained, disposed | verification failure leads to quarantined. |
| Twin | synchronized, stale, degraded | only newer observable versions synchronize. |

