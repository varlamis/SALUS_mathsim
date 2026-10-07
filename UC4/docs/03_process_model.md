# UC4 BPMN 2.0 process model

## Scope

The five detailed UC4 process families are modeled as editable BPMN 2.0 XML collaborations. Their task-level implementation contract is [processes/UC4_processes.md](processes/UC4_processes.md), and their normative guards, state transitions, invariants, and equations are in `models/formal/uc4_mathematical_model.md`.

| ID | Process family | BPMN source |
|---|---|---|
| `UC4-PR01` | Normal operation | `diagrams/process_flows/UC4_normal_operation.bpmn` |
| `UC4-PR02` | Incident/abnormal behavior | `diagrams/process_flows/UC4_incident.bpmn` |
| `UC4-PR03` | Detection and case trigger | `diagrams/process_flows/UC4_detection_case_trigger.bpmn` |
| `UC4-PR04` | Lawful policy enforcement/acquisition | `diagrams/process_flows/UC4_lawful_acquisition.bpmn` |
| `UC4-PR05` | Evidence collection/investigation | `diagrams/process_flows/UC4_evidence_investigation.bpmn` |

`diagrams/process_flows/UC4_system_collaboration.bpmn` remains the compact context-level collaboration. The five files above are authoritative for detailed behavior.

## Modeling decisions

- Pools define independent actors or systems; message flows cross pools and sequence flows remain within them.
- Lanes separate policy/acquisition/audit responsibilities inside `UC4-S02` and repository/custody responsibilities inside `UC4-S03/S04`.
- Exclusive gateways encode explicit guarded alternatives and use fail-safe default paths.
- Error and timer boundary events model ingestion failure, source unavailability, detector failure, authorization expiry/revocation, source timeout, and storage failure.
- Data stores represent bounded source records, case/audit records, content-addressed evidence, and the append-only custody chain.
- BPMN condition expressions use implementation-oriented forms of the formal model. The formal model remains normative if wording differs.

## Critical guarantees represented

1. Physical ground truth and observable telemetry are separate.
2. A detection alert or case trigger does not authorize acquisition.
3. Invalid, expired, revoked, unauthenticated, out-of-scope, empty, or timed-out requests fail closed and return no evidence payload.
4. Evidence source bytes are hashed and immutable; integrity or custody defects cause quarantine.
5. Clock uncertainty and alternative explanations survive reconstruction; an inconclusive result is valid behavior.
6. The final output is a technically audited investigation package, not a legal conclusion.

## Status and next step

Stage 5 is complete. The five process-family diagrams, consolidated lifecycle BPMN model, process catalogue, and lifecycle transition specification are present and structurally validated. Stage 6 validates every BPMN file for resolvable references, process-boundary rules, guarded exclusive gateways, and BPMNDI coverage. See `diagrams/state_machines/UC4_entity_lifecycles.bpmn`, `docs/processes/UC4_lifecycles.md`, and `docs/04_validation_plan.md`.

Stage 7 implements the deterministic simulation core, Stage 8 executes the negative/degraded matrix, and Stage 9 exports traversable runtime provenance for every process outcome. The next ordered work is Stage 10 metrics, Monte Carlo experiments, and sensitivity analysis.
