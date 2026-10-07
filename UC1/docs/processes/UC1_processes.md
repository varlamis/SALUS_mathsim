# UC1 end-to-end processes

## Normal operation

| Step | Responsible entity | Input | Action/output | Failure/audit |
|---|---|---|---|---|
| 1 | `UC1-D02` | Configured state | Emit abstract normal message | Offline state is audited. |
| 2 | `UC1-NZ02` | Message | Apply capacity, delay, jitter, and loss | Loss cause is counted. |
| 3 | `UC1-D05` / `UC1-S02` | Delivered message | Parse and validate trust/freshness/sender | Predicate result is recorded. |
| 4 | `UC1-D06` | Accepted request | Apply safe interlock and bounded phase decision | Rejection/fallback is explicit. |
| 5 | `UC1-S05` | Observable state | Update versioned twins | Stale/missing update is explicit. |

## Controlled attack

The authorized red-team actor activates `UC1-D08`, which injects configured symbolic messages. The channel may deliver, lose, or overflow each message. The RSU/trust path evaluates it without access to hidden truth. Attack reach is recorded at distinct stages; no real I/O occurs.

## Detection and alerting

Observable message and validation records feed explicit features. `UC1-S03` calculates a weighted score, compares it with the configured threshold, and emits an explanation listing contributing features. Missing observations cannot be inferred.

## Policy and mitigation

An alert triggers `UC1-S04`. It checks supported capabilities, requests the selected action, records acknowledgement, and distinguishes `requested_action` from applied `action`. Unsupported or unavailable enforcement fails visibly; controller safety remains independent.

## Evidence and investigation

`UC1-S06` selects allowed event types and fields, hashes canonical content, and appends custody records. `UC1-S07` uses verified evidence only and produces a claim with support, confidence, and alternatives. `UC1-A04` receives no hidden truth.

