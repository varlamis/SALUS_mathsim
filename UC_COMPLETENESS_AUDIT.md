# Use-case package completeness audit

Audit basis: the UC4 implementation pattern plus `readme_UC1.md` through `readme_UC5.md`. Environment, cache and generated-run internal directories are excluded from structural-empty checks.

| Requirement family | UC1 | UC2 | UC3 | UC4 | UC5 |
|---|---:|---:|---:|---:|---:|
| Scope/use-case/entity/process/validation documents | Complete | Complete | Complete | Complete | Complete |
| Assumptions, lifecycle, simulation, graph, analysis, integration and packaging documents | Complete | Complete | Complete | Complete | Complete |
| Canonical entities/relationships/formal model/graph | Complete | Complete | Complete | Complete | Complete |
| Nine core schemas | Complete | Complete | Complete | Complete | Complete |
| Inventory and external-dataset field mapping | Complete | Complete | Complete | Complete | Complete |
| Restricted raw, processed and synthetic boundaries documented | Complete | Complete | Complete | Complete | Complete |
| Entity-relationship readable view | Complete | Complete | Complete | Complete | Complete |
| BPMN process/lifecycle artefacts | 7 | 7 | 8 | 7 | 8 |
| Integration contracts | Complete | Complete | Complete | Complete | Complete |
| Baseline/nominal/experiments/Monte Carlo outputs | Complete | Complete | Complete | Complete | Complete |
| Schema-valid event/evidence golden fixtures | Complete | Complete | Complete | Complete | Complete |
| Compiled per-UC technical report | Complete | Complete | Complete | Complete | Complete |
| Validation/JUnit/final handoff | Complete | Complete | Complete | Complete | Complete |
| Passing automated tests | 22 | 11 | 21 | 47 | 13 |
| Verified SHA-256 manifest | Complete | Complete | Complete | Complete | Complete |

## Deliberately non-populated data scope

The raw and processed boundaries contain governance documentation rather than real datasets. This is required, not an omission: the guides prohibit committing operational vehicle/RF/industrial/household/hospital traces, credentials, direct identifiers and sensitive payloads. Future imports require documented ownership, licence/authority, checksum, schema mapping, minimization, time/identity handling, access control and deletion rules.

## Schema specialization policy

UC1, UC2, UC3 and UC5 use the nine canonical strict schemas rather than copying UC4's historical per-device example documents. Each `models/schemas/entities/devices/README.md` records the extension gate. A specialized device schema is added only when an expert-confirmed field cannot be represented in the canonical envelope and must include versioning, migration and compatibility tests.

## Remaining external dependencies

All packages are internally validated synthetic implementations. Partner confirmation, licensed dataset mapping, real interface authorization, calibration and WP6/pilot evaluation remain TBD and are not silently replaced by fabricated artefacts.
