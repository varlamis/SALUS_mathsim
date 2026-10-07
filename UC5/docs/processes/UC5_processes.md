# UC5 process specification

## P1 Normal monitoring

The monitor emits abstract flows and health status; the network exports flow records; collection applies configured delay, loss and bounded-queue rules; the twin records the latest observable state. Missing data is explicit and never imputed as benign. Failures produce loss/overflow metrics and audit events.

## P2 Detection, explanation and triage

The detector consumes observations only, computes normalized rate, byte, destination and health-mismatch features, compares the weighted score with the threshold and emits an alert with feature contributions and alternatives. No alert is created from hidden truth. A health fault without network anomaly remains a health event.

## P3 Clinical-safety response

The policy service checks alert confidence, device essentiality, approved backup, authorization and enforcement availability. Isolation can be applied only if every gate succeeds and continuity is preserved. Otherwise it is rejected/deferred with a reason, continued monitoring is selected, and an auditable safety decision is emitted. Timeouts fail safe.

## P4 Evidence and custody

Qualifying observable events and decisions are canonicalized, SHA-256 hashed and placed in a purpose-scoped evidence manifest. Every acquisition/transfer creates a chained custody event. Integrity or custody failure prevents downstream sharing.

## P5 Redaction and authorized sharing

The sharing service verifies evidence, applies the allow-list, removes disallowed keys, checks authorization and exports pseudonymous device class, evidence IDs/hashes and the incident time window. Patient identifiers and clinical payload are prohibited. Missing authority, redaction failure or tamper denies sharing.

## P6 Investigation and reconstruction

The investigator verifies custody and reconstructs the observed sequence from evidence references. Restricted ground truth is used only after reconstruction for evaluation metrics. Uncertainty and missing observations remain visible.

## Failure defaults

Collector unavailable records missingness; stale registry reduces confidence; detector degradation can suppress an alert; unavailable policy/enforcement prevents isolation; safety uncertainty rejects isolation; evidence/custody tamper invalidates the package; and sharing/redaction failure denies release.
