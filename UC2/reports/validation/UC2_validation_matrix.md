# UC2 validation matrix

| Gate | Result | Evidence |
|---|---|---|
| Strict schemas/config | Complete | 9 schemas; CLI validation succeeds. |
| Entity/relationship integrity | Complete | 25 entities, 26 relationships, generated graph. |
| Process coverage | Complete | 6 process-flow BPMN plus 1 lifecycle BPMN. |
| Determinism | Complete | Repeated-seed canonical hash test. |
| Passive-only operation | Complete | All 9 experiments report zero active RF actions. |
| Privacy | Complete | All experiments report zero unauthorized disclosures; no payload capture. |
| Failure behavior | Complete | Loss, overflow, unavailable/stale registry, low confidence and policy-unavailable branches. |
| Evidence/custody | Complete | Hash and custody verification test. |
| Hidden-truth separation | Complete | Reconstruction declares `hidden_truth_used=false`. |
| Uncertainty analysis | Complete | 100 predeclared seeded samples. |
| Automated verification | Complete | 11 tests pass, including event/evidence fixture validation; JUnit retained. |
| Operational/field validation | TBD | Requires UC experts, licensed data, interfaces, baselines and WP6 protocol. |
