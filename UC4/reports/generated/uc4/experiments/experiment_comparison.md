# UC4 Stage 8 experiment comparison

Overall status: **valid**

| Experiment | Evidence | Verified | Denies | Integrity | Disclosure bytes | Queue loss | Assertions |
|---|---:|---:|---:|---|---:|---:|---|
| `baseline` | 0 | 0 | 0 | pass | 0 | 0.0 | pass |
| `nominal_lawful_incident` | 17 | 17 | 16 | pass | 0 | 0.0 | pass |
| `authorization_absent` | 0 | 0 | 1 | pass | 0 | 0.0 | pass |
| `authorization_invalid` | 0 | 0 | 1 | pass | 0 | 0.0 | pass |
| `authorization_expired` | 0 | 0 | 1 | pass | 0 | 0.0 | pass |
| `authorization_revoked` | 0 | 0 | 1 | pass | 0 | 0.0 | pass |
| `out_of_scope_device` | 0 | 0 | 1 | pass | 0 | 0.0 | pass |
| `presence_event_missed` | 14 | 14 | 16 | pass | 0 | 0.0 | pass |
| `door_event_lost` | 9 | 9 | 16 | pass | 0 | 0.0 | pass |
| `source_records_evicted` | 0 | 0 | 1 | pass | 0 | 0.0 | pass |
| `cpe_queue_overflow` | 11 | 11 | 10 | pass | 0 | 0.8687473282079018 | pass |
| `maximum_clock_skew` | 17 | 17 | 16 | pass | 0 | 0.0 | pass |
| `evidence_content_tampered` | 17 | 16 | 16 | detected fault | 0 | 0.0 | pass |
| `custody_link_tampered` | 17 | 0 | 16 | detected fault | 0 | 0.0 | pass |
| `home_assistant_unavailable` | 8 | 8 | 12 | pass | 0 | 0.0 | pass |
| `cpe_unavailable` | 11 | 11 | 10 | pass | 0 | None | pass |

All results are synthetic and do not establish legal compliance, admissibility, or real-device performance.
