# UC4 validation matrix

## Decision

Stage 11 is **Complete** for the executable synthetic UC4 scope. The clean-install test run contains 43 passing tests, zero failures, zero errors, and zero skipped tests. Both canonical configurations pass repository validation with seven schemas, 38 entities, 123 relationships, and seven BPMN files.

Allowed status values are `Complete`, `Partial`, `Missing`, `Not Applicable`, and `TBD`. `Complete` means the declared repository abstraction is implemented and automatically evidenced; it does not imply real-pilot, legal, or partner certification.

## Automated validation coverage

| ID | Validation obligation | Status | Automated evidence | Validation evidence |
|---|---|---|---|---|
| V-01 | JSON Schema validity and Pydantic round trips | Complete | `tests/test_schemas.py::test_repository_contracts_validate`; `test_valid_event_and_evidence_round_trip` | `UC4_stage11_junit.xml`; `models/schemas/*.schema.json` |
| V-02 | Stable, unique canonical identifiers | Complete | `tests/test_event_queue.py::test_queue_rejects_negative_time_and_ids_are_stable`; `tests/test_stage11_validation.py::test_canonical_ids_vocabularies_and_twin_mapping_are_unique` | `models/instances/uc4_entities.json`; `models/relationships/uc4_relationships.csv` |
| V-03 | Referential integrity and graph connectivity | Complete | `tests/test_graph_integrity.py` | `models/graph/uc4_graph.json`; `UC4_stage11_junit.xml` |
| V-04 | Controlled vocabularies | Complete | `tests/test_stage11_validation.py::test_canonical_ids_vocabularies_and_twin_mapping_are_unique`; repository validator | `models/schemas/entity.schema.json`; `models/schemas/relationship.schema.json` |
| V-05 | Versioned schema migration | Complete | `tests/test_stage11_validation.py::test_config_migration_is_explicit_non_mutating_and_idempotent` | `configs/uc4/schema_migrations.yaml`; `src/salus_mathsim/uc4/migrations.py` |
| V-06 | Legal state transitions and configured physical bounds | Complete | `tests/test_dynamics.py::test_device_transition_and_twin_monotonicity`; negative Pydantic tests in `test_schemas.py` | `models/formal/uc4_mathematical_model.md`; `UC4_stage11_junit.xml` |
| V-07 | Monotonic simulation time and deterministic tie-breaking | Complete | `tests/test_event_queue.py` and runtime `_assert_invariants` | `src/salus_mathsim/uc4/event_queue.py`; nominal run package |
| V-08 | Flow/queue conservation and bounded occupancy | Complete | `tests/test_dynamics.py::test_cpe_queue_conservation_and_overflow`; Stage 8 overflow branch | `src/salus_mathsim/uc4/traffic.py`; `reports/generated/uc4/experiments/cpe_queue_overflow/metrics.json` |
| V-09 | Authorization default deny, verification, scope, time, purpose, action and revocation | Complete | `tests/test_policy_evidence.py`; parameterized `test_authorization_terms_fail_closed`; Stage 8 authorization branches | `src/salus_mathsim/uc4/authorization.py`; `reports/generated/uc4/experiments/experiment_comparison.json` |
| V-10 | Field minimization before release | Complete | `tests/test_policy_evidence.py::test_policy_minimizes_to_permitted_fields` | nominal `policy_decisions.jsonl` and `evidence_manifest.json` |
| V-11 | No evidence payload or bytes on denied collection | Complete | `test_policy_denies_out_of_scope_with_zero_disclosure`; `tests/test_experiments.py::test_stage8_negative_paths_have_expected_effects` | five authorization-negative run packages; Stage 8 report |
| V-12 | Evidence content hashes and custody-chain verification, including deliberate corruption | Complete | `test_evidence_hash_and_custody_detect_corruption`; Stage 8 content/custody tamper branches | tampered experiment metrics and custody ledgers |
| V-13 | Unique physical-to-twin mapping and stale-update rejection | Complete | `test_every_physical_device_has_reciprocal_twin_links`; `test_canonical_ids_vocabularies_and_twin_mapping_are_unique`; `test_device_transition_and_twin_monotonicity` | canonical entity/relationship models; JUnit evidence |
| V-14 | Ground-truth isolation from investigator-visible data | Complete | `test_incident_truth_policy_evidence_and_reconstruction_separation`; `test_runtime_graph_validates_and_excludes_hidden_truth`; `test_investigator_outputs_do_not_expose_hidden_truth` | nominal graph metadata; exported investigator artefacts |
| V-15 | Equal-seed reproducibility and different-seed variation | Complete | `test_incident_run_is_reproducible_and_schema_valid`; `test_seeded_observation_streams_repeat`; `test_different_random_seeds_change_stochastic_result`; `test_seeded_monte_carlo_is_reproducible` | nominal canonical hash and Stage 10 ordered sample ledger |
| V-16 | End-to-end validated event, evidence, custody, graph, reconstruction and metric outputs | Complete | `test_export_contains_every_required_run_artifact`; `test_end_to_end_documents_are_complete_and_internally_linked` | `reports/generated/uc4/monte_carlo/nominal/` |
| V-17 | BPMN 2.0 structure, references, guarded branches and BPMNDI coverage | Complete | `tests/test_bpmn.py::test_all_bpmn_models_pass_structural_validation` | seven files under `diagrams/`; repository validator |
| V-18 | Negative-path experiment assertions | Complete | `tests/test_experiments.py` | `reports/validation/UC4_stage8_experiment_report.md`; 16 generated packages |
| V-19 | Metrics, seed ledger, confidence intervals and sensitivity | Complete | `tests/test_analysis.py` | `reports/generated/uc4/monte_carlo/monte_carlo_summary.json`; `sensitivity.svg` |

## Requirements-to-test traceability

| Source requirement | Model artefact | Executable module | Test(s) | Validation evidence | Status |
|---|---|---|---|---|---|
| `PROPOSAL-PDF-p190`: mathematically model physical entities, properties, processes, exchanges, replicas and relations | `models/formal/uc4_mathematical_model.md`; entity/relationship schemas and instances | `entities.py`, `dynamics.py`, `traffic.py`, `simulation.py` | `test_dynamics.py`, `test_graph_integrity.py`, `test_simulation.py` | JUnit; nominal package | Complete |
| `PROPOSAL-PDF-p162-p164`: physical/digital entities, graph relations, Digital Twin simulation, evidence and custody context | entity collection, relationship inventory, runtime graph schema | `graph_builder.py`, `runtime_graph.py`, `custody.py`, `simulation.py` | graph, runtime-graph, custody, twin and end-to-end tests | Stage 9 report; JUnit | Complete |
| `PROPOSAL-PDF-p169-p170`: smart-home UC4, CPE/Home Assistant acquisition, lawful scope and privacy constraints | `docs/use_cases/UC4.md`; five process-family BPMN files; lawful configuration | `authorization.py`, `collection.py`, `simulation.py`, `reconstruction.py` | policy/evidence, experiments, isolation and end-to-end tests | Stage 8 report; nominal policy/evidence files | Complete |
| `PROPOSAL-PDF-p171`: candidate research datasets | `UC4-DS14` and `UC4-DS15` inventory entries | seeded `ObservationModel` synthetic adapter | deterministic observation and Monte Carlo tests | Stage 10 report | Partial |
| `ROADMAP-Phase-1`: explicit use-case decomposition and boundary | `docs/use_cases/UC4.md` | strict configuration model | repository/config tests | validation report | Complete |
| `ROADMAP-Phase-3`: canonical entity and relationship contracts | schemas, instances, CSV inventories | `models.py`, `graph_builder.py`, `validation.py` | schema, vocabulary and graph-integrity tests | JUnit; canonical graph | Complete |
| `ROADMAP-Phase-4`: detailed process and lifecycle models | BPMN process and lifecycle files | BPMN validator in `validation.py` | `test_bpmn.py` | seven validated BPMN files | Complete |
| `ROADMAP-Phase-5`: formal hybrid mathematical model | `models/formal/uc4_mathematical_model.md` | event queue, dynamics, traffic, policy and reconstruction modules | dynamics, queue, policy and simulation tests | JUnit; Stage 7 run outputs | Complete |
| `ROADMAP-Phase-6`: executable deterministic simulation and experiment branches | baseline, lawful scenario and experiment configurations | `simulation.py`, `experiments.py` | simulation and 16-branch experiment tests | Stage 8 comparison and packages | Complete |
| `ROADMAP-Phase-7`: graph queries, metrics, sensitivity and validation | runtime graph, query/metric contract, this matrix | `queries.py`, `metrics.py`, `analysis.py`, `validation.py` | runtime graph, analysis and Stage 11 tests | Stage 9 report; Stage 10 report; JUnit | Complete |

## Partial item disposition

| Item | Synthetic fallback | Impact | Replacement path | Blocks end-to-end run? |
|---|---|---|---|---|
| Candidate research/pilot dataset calibration (`PROPOSAL-PDF-p171`) | Seeded configurable observation, sensor-error, loss, timing and load models | Numerical values demonstrate model behavior but cannot be represented as real-device or pilot performance | Implement a versioned dataset/lab adapter, map fields to canonical events, calibrate parameter distributions, rerun the same validation and analysis gates | No |

Partner feedback and external legal validation are **Not Applicable** to the agreed implementation completion gate. Their absence is not converted into a technical claim: authorization and custody are explicitly modeled abstractions, not legal certification.

## Gate result

- Missing items: **0**.
- TBD validation judgments: **0**.
- Partial items: **1**, with fallback, impact, replacement path, and non-blocking disposition above.
- Automated tests: **43 passed** in a fresh isolated installation of `.[test]`.
- JUnit SHA-256: `d90fd34c549ef97253010487c8f899f8ae8ccd58063339157556afb03d89ce50`.
- Canonical baseline and lawful-incident repository validations: **valid**.

Stage 11 gate: **PASS**.
