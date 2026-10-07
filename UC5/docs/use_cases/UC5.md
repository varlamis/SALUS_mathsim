# UC5 scenario definition

## Objective

Determine whether an active synthetic patient monitor exhibits anomalous outbound network behaviour, explain the alert, protect clinical continuity while selecting a response, and preserve/share only authorized minimized evidence.

## Actors and systems

The active device is a patient monitor. A bedside gateway and medical-zone switch carry abstract flows to a flow collector. A security monitor, detector/XAI service, asset registry and clinical-safety policy service evaluate observations. An operator, clinical safety reviewer, investigator and sharing authority govern decisions. Evidence, custody, redaction, sharing, reconstruction, threat-intelligence and digital-twin services support the investigation. Wearable, infusion and diagnostic devices are inventory classes but inactive in this slice.

## Nominal incident path

1. Generate seeded normal flow and health truth.
2. Inject a symbolic `anomalous_egress` state after the configured attack time.
3. Apply loss/delay and bounded collection; derive observations without attack labels.
4. Score observable rate, bytes, destination class and health mismatch; export contributions.
5. Request isolation for a qualifying alert.
6. Reject isolation for an essential monitor without approved backup, or apply bounded isolation when backup is active.
7. Collect minimized evidence, append custody, redact and authorize sharing.
8. Reconstruct from evidence only and evaluate against restricted truth.

## Acceptance criteria

The same input and seed produce the same canonical hash. Baseline has no cyber alert; nominal compromise has an explainable alert; a health-only fault is not classified as a cyberattack; unauthorized sharing fails closed; no share contains patient/clinical content; and essential-monitoring interruption remains zero in every branch.

## Expert decisions still required

Hospital topology and device classes, real flow baselines, clinical criticality and backup rules, detector calibration, mitigation authority, review timeouts, retention/purpose, sharing recipients and legal basis, DS8 licensing/mapping, and WP6 KPI baselines remain TBD.
