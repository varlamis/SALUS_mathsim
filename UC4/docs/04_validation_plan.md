# UC4 pre-simulation validation plan

## Purpose and boundary

Stage 6 establishes a fail-fast boundary between authored UC4 contracts and executable simulation behavior. No simulator may schedule an event until `validate_repository` has accepted the selected configuration and all canonical source artefacts. This stage validates structure and internal consistency; it does not claim device fidelity, legal admissibility, partner approval, or real-pilot performance.

## Authoritative inputs

| Contract | Authoritative location | Runtime representation |
|---|---|---|
| Schema version | `configs/uc4/schema_version.yaml` | `SCHEMA_VERSION` |
| Baseline run | `configs/uc4/baseline.yaml` | `SimulationConfig` |
| Lawful incident run | `configs/uc4/incident_lawful_access.yaml` | `SimulationConfig` |
| Entities | `models/instances/uc4_entities.json` | `Entity` and `MultiDiGraph` nodes |
| Relationships | `models/relationships/uc4_relationships.csv` | canonical relationship objects and graph edges |
| Event interchange | `models/schemas/event.schema.json` | `UC4Event` |
| Evidence interchange | `models/schemas/evidence.schema.json` | `EvidenceItem` |
| Processes/lifecycles | `diagrams/**/*.bpmn` | validated BPMN 2.0 XML |

`models/graph/uc4_graph.json` is generated output. Entity JSON and relationship CSV remain its sources of truth.

## Validation order

1. Load all seven JSON Schemas and check each against Draft 2020-12, including the Stage 9 runtime-graph contract.
2. Parse YAML with safe loading; validate it against `simulation_config.schema.json`; then build the strict Pydantic model.
3. Enforce cross-field constraints: ordered scenario times, ordered authorization/evidence windows, enabled incident scope, authorization-decision compatibility, bounded clock offsets and jitter, unique authorization lists, cloud/topology agreement, and valid reconstruction weights.
4. Validate the entity collection through its referenced entity schema and strict runtime model; require lossless JSON round trips and exact CSV/JSON inventory ID parity.
5. Canonicalize each relationship CSV row, validate it, resolve both endpoints, check unique IDs and temporal ranges, and build a directed NetworkX `MultiDiGraph`.
6. Require one weakly connected graph, all physical-to-twin `MIRRORED_BY` edges, and all Digital Twin service-to-twin `SYNCHRONIZES_WITH` edges.
7. Resolve enabled topology IDs, device profiles, incident targets, and reconstruction reliability sources against canonical entities. Reject CPE-flow acquisition when network logging is disabled.
8. Parse every BPMN file; reject duplicate/unresolved IDs, sequence flows crossing process boundaries, message flows staying within a process, unguarded exclusive branches, missing defaults, and missing BPMNDI shapes/edges.
9. Validate representative event and evidence fixtures with both JSON Schema and Pydantic, including lossless JSON round trips.
10. Only after all checks pass, optionally emit the graph document.

Errors are accumulated where possible and reported with the file, object/path, and violated rule. The CLI returns exit code `2` for contract failure and does not write a graph.

## Automated test matrix

| Test area | Assertions |
|---|---|
| Valid configurations | Baseline and lawful incident validate; expected counts are 38 entities and 123 relationships. |
| Schema/runtime agreement | Event and evidence fixtures round-trip; forbidden keys and payload capture fail. |
| Cross-field negatives | Invalid event ordering, inconsistent authorization verification, and invalid device enablement fail before execution. |
| Graph integrity | Node/edge counts, endpoint resolution, connectivity, and all six twin mappings hold. |
| BPMN structure | All detailed process-family and lifecycle files pass structural and BPMNDI checks. |

Run the gate from the repository root:

```powershell
python -m pip install -e ".[test]"
salus-mathsim validate --config configs/uc4/incident_lawful_access.yaml --write-graph
salus-mathsim validate --config configs/uc4/baseline.yaml
python -m pytest -q
```

For source-tree execution without installation:

```powershell
$env:PYTHONPATH = "src"
python -m salus_mathsim.cli validate --config configs/uc4/incident_lawful_access.yaml --write-graph
python -m pytest -q
```

## Stage 11 consolidated evidence

The complete post-implementation validation matrix is maintained at `reports/validation/UC4_validation_matrix.md`. Machine-readable test evidence is `reports/validation/UC4_stage11_junit.xml`, and the execution summary is `reports/validation/UC4_stage11_test_report.md`. These extend this pre-simulation plan with migration, authorization-purpose, cross-seed, truth-isolation, end-to-end linkage, Monte Carlo, and requirements-traceability coverage.

## Stage 6 exit decision

Stage 6 passes when both supplied configurations validate, every interchange fixture round-trips, all graph and BPMN invariants hold, invalid configurations fail before simulation, and the graph can be regenerated from canonical inputs. The Stage 7 simulator imports these models and calls `validate_repository` before constructing runtime state; it does not define parallel contracts.
