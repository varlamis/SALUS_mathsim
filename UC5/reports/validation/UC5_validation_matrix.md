# UC5 validation matrix

| Gate | Result | Evidence |
|---|---|---|
| Strict schemas/config | Complete | 9 schemas; CLI validation succeeds. |
| Entity/relationship integrity | Complete | 34 entities, 45 relationships, generated graph. |
| Process coverage | Complete | 7 process-flow BPMN plus 1 lifecycle BPMN. |
| Determinism | Complete | Repeated-seed canonical hash test. |
| Clinical-continuity constraint | Complete | No-backup rejection and backup-active isolation tests. |
| Privacy and sharing | Complete | Zero patient disclosures/privacy violations; unauthorized sharing denied. |
| Fault/attack separation | Complete | Health-only fault produces no cyber alert. |
| Failure behavior | Complete | Loss, flood/overflow, enforcement unavailable and sharing denied branches. |
| Evidence/custody/truth separation | Complete | Integrity verification and evidence-only reconstruction tests. |
| Uncertainty analysis | Complete | 100 predeclared seeded samples. |
| Automated verification | Complete | 13 tests pass, including event/evidence fixture validation; JUnit retained. |
| Clinical/operational validation | TBD | Requires HMU/5YPE/K3Y experts, DS8, approved safety rules and WP6 protocol. |
