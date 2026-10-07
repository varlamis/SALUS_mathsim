# UC4 deterministic simulation core

## Runtime contract

The Stage 7 implementation executes the hybrid model in `models/formal/uc4_mathematical_model.md`. Every run first invokes the Stage 6 repository validator. Invalid configuration, schemas, entities, relationships, graph structure, or BPMN structure therefore stop execution before any event is scheduled.

The runtime has four deliberately separate data partitions:

| Partition | Producer | Permitted consumers |
|---|---|---|
| Hidden ground truth | Incident/device dynamics | Post-reconstruction metric evaluation only |
| Observable events and retained records | Observation, Home Assistant, and CPE models | Policy-controlled acquisition |
| Collected evidence | Authorization/minimization and evidence store | Custody verification and reconstruction |
| Investigator-visible reconstruction | Reconstruction service | Technical report/audit |

`reconstruct` accepts only verified `CollectedEvidence`; it has no ground-truth argument or import path.

## Module-to-model mapping

| Implementation | Responsibility | Formal sections |
|---|---|---|
| `uc4/identifiers.py` | Stable run-local IDs | §§2, 4, 16.1 |
| `uc4/event_queue.py` | Immutable scheduled events ordered by `(time, sequence)` | §§3–4 |
| `uc4/entities.py` | Physical state/version guards, Home Assistant registry, monotonic twins | §§6–7, 9 |
| `uc4/dynamics.py` | Source-isolated seeded random streams, loss, clocks, jitter, delays | §5 |
| `uc4/traffic.py` | CPE queue conservation, service, capacity, and overflow | §8 |
| `uc4/authorization.py` | Eligibility predicate, default deny, field projection | §11 |
| `uc4/collection.py` | RFC 8785 serialization, SHA-256, immutable evidence metadata | §12.1–12.2 |
| `uc4/custody.py` | Genesis and append-only custody hash chain | §12.3 |
| `uc4/reconstruction.py` | Evidence-only ordering and explainable support scores | §13 |
| `uc4/metrics.py` | Evidence, disclosure, latency, twin, network, and loss metrics | §14 |
| `uc4/simulation.py` | Global transition orchestration, invariants, manifest, and exports | §§3, 10, 15–18 |

## Determinism

The queue never uses wall-clock time. Equal simulation times are resolved by a strictly increasing insertion sequence. Random streams are derived from `SHA-256(seed || stream-name)`, so adding an unrelated stochastic consumer does not silently perturb another source's loss or clock sequence.

All deterministic documents are serialized canonically and hashed together. `generation_time_utc` exists only in `run_manifest.json`, with an explicit marker that it is excluded from `canonical_result_sha256`. Repeating a run with the same validated source files, configuration, code, and seed produces the same canonical result hash.

## Primary causal schedule

For the incident configuration, the engine schedules warm-up device snapshots, unauthorized door opening, possible presence corroboration, door-sensor tampering and disconnection, explainable case trigger, and a later acquisition request. An observed door event may trigger Home Assistant's entry-light rule and a versioned light acknowledgement. Lost door observations cannot trigger that automation.

The case trigger sets acquisition state to `request_received`, never `authorized`. At request time, every retained record is independently checked for authorization status, verification, validity time, evidence window, entity, data type, action, and non-empty permitted projection. A failed term returns a named deny reason and zero released bytes.

## Evidence and reconstruction

Allowed projections are canonicalized and hashed after minimization. Each evidence item references its source record, authorization, policy decision, collector, acquisition method, transformation, content hash, and content-addressed storage URI. Registration and verification actions enter one deterministic custody chain. Failed content or chain verification prevents the item from entering reconstruction.

Reconstruction emits entry, automation, and tampering claims with support scores, qualification labels, evidence IDs, missing expected observations, contradictions, alternatives, and limitations. Scores are transparent engineering support measures, not probabilities or legal conclusions.

## Execution and outputs

```powershell
salus-t43 run --config configs/uc4/incident_lawful_access.yaml
salus-t43 run --config configs/uc4/baseline.yaml
```

The run writes `run_manifest.json`, `resolved_config.yaml`, entity and relationship snapshots, hidden and observed event streams, policy decisions, evidence and custody records, reconstruction, graph, metrics, validation report, and technical Markdown summary. `--output` can redirect the package without changing scenario semantics.

## Stage 7 gate result

The baseline and incident configurations both execute without schema or invariant violations. Tests cover stable queue ties, invalid time rejection, identifier repeatability, legal/duplicate/illegal transitions, stale twin rejection, seeded clock/loss repeatability, queue conservation and overflow, scope/minimization and zero-disclosure denial, evidence/custody corruption, RFC 8785 boundary values, event/evidence schema conformance, ground-truth isolation, deterministic run hashes, baseline behavior, and the complete output set.

Stage 8 defines and executes these branches through `configs/uc4/experiments.yaml`. Stage 9 adds runtime graph construction, competency queries, and visualization as documented in `docs/graph/UC4_graph_queries.md`. The next stage is metrics, Monte Carlo experiments, and sensitivity analysis.
