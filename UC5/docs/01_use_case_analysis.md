# UC5 use-case analysis

## Problem and bounded objective

UC5 asks how connected medical-device behavior can be monitored while ensuring that a cyber response does not compromise care continuity. The executable slice uses one synthetic patient monitor emitting abstract flows and non-clinical health metadata. A symbolic anomalous-egress state changes rate/bytes and destination class; observation, XAI, safety policy, evidence, redaction, sharing and reconstruction services process the event.

## Safety, privacy and truth boundary

The model has no medical, EHR/PACS or live-network interface and cannot diagnose, treat or actuate. Isolation is eligible only with authorization/enforcement and either a nonessential device or approved backup monitoring. Patient identifiers and clinical payload have cardinality zero. Hidden compromise state is evaluation truth only and cannot enter alert, evidence, sharing or reconstruction inputs.

## Stakeholders and unresolved facts

HMU/5YPE/K3Y and hospital roles are proposal-level placeholders. Experts must establish topology, real device classes, flow baselines, clinical criticality/backup approval, detection calibration, response authority, evidence purpose/retention, sharing recipients/legal basis, DS8 mapping and WP6 baselines.

## Acceptance argument

The model is internally supported by strict schemas, graph integrity, deterministic execution, safety/privacy invariants, negative branches, 100-sample uncertainty analysis, tests and hashed handoff. These do not constitute clinical validation, certification, GDPR compliance or hospital performance evidence.
