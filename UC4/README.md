# SALUS T4.3 Entity and Process Modelling

Executable UC4 entity, relationship, process, lifecycle, and configuration contracts for the SALUS Digital Twin Infrastructure.

## Current implementation state

Stages 0–12 of the repository implementation plan are complete. The repository contains the frozen UC4 scenario, canonical entity/process models, deterministic simulation, a 16-branch experiment matrix, temporal runtime graphs, nine data-driven competency queries, explicit performance/privacy/integrity metrics, a reproducible 100-sample Monte Carlo sensitivity analysis, consolidated validation and traceability, seven versioned integration contracts, and a hashed final handoff manifest.

## Installation

Python 3.11 or later is required. For the reproducible Python 3.12 environment:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pip install --no-deps -e .
.venv\Scripts\python -m pip check
```

For ordinary development, `python -m pip install -e ".[test]"` installs the exact direct pins from `pyproject.toml`. The transitive lock and controlled update procedure are documented in `docs/packaging/DEPENDENCY_LOCK.md`.

## Validate the model contracts

```powershell
salus-t43 validate --config configs/uc4/incident_lawful_access.yaml --write-graph
salus-t43 validate --config configs/uc4/baseline.yaml
python -m pytest -q
```

The validator fails before simulation on invalid schemas, values, cross-file references, graph invariants, BPMN structure, or incompatible configuration options. `--write-graph` regenerates `models/graph/uc4_graph.json` from the canonical entity and relationship sources.

See `docs/04_validation_plan.md` for the validation boundary and test matrix, and `docs/use_cases/UC4.md` for the authoritative scenario contract.

## Run the simulator

The complete selected scenario executes with one command:

```powershell
salus-t43 run --config configs/uc4/incident_lawful_access.yaml
salus-t43 run --config configs/uc4/baseline.yaml
```

Use `--output <directory>` to override the configured destination. A successful run emits the 14 core files defined by the UC4 scenario contract plus Stage 9 competency-query JSON and an SVG graph overview. The generation timestamp is isolated in `run_manifest.json`; it is excluded from the canonical result hash.

The run directory contains:

```text
run_manifest.json             resolved_config.yaml
entities.json                 relationships.json
ground_truth_events.jsonl     observed_events.jsonl
policy_decisions.jsonl        evidence_manifest.json
custody_events.jsonl          reconstructed_timeline.json
graph.json                    metrics.json
validation_report.json        investigation_summary.md
competency_queries.json       graph_overview.svg
```

`ground_truth_events.jsonl` is restricted evaluation data. Reconstruction, runtime graphs, competency queries, and investigator summaries consume only observable and authorized evidence paths.

See `docs/simulation/UC4_simulation.md` for the runtime architecture, deterministic ordering rules, data-separation boundary, and module-to-equation traceability.

## Execute the experiment matrix

```powershell
salus-t43 experiment --matrix configs/uc4/experiments.yaml --output reports/generated/uc4/experiments
```

The command resolves every branch against the lawful-incident configuration, validates it, emits a separate run package, evaluates declared expectations, and writes JSON/Markdown comparison reports. The committed result summary is `reports/validation/UC4_stage8_experiment_report.md`.

## Query a runtime graph

```powershell
salus-t43 graph-query --graph reports/generated/uc4/experiments/nominal_lawful_incident/graph.json
salus-t43 graph-query --graph reports/generated/uc4/experiments/nominal_lawful_incident/graph.json --query claim_support
```

Every generated package includes all query results in `competency_queries.json` and an aggregated `graph_overview.svg`. See `docs/graph/UC4_graph_queries.md` and `reports/validation/UC4_stage9_graph_query_report.md`.

## Run the Stage 10 analysis

```powershell
salus-t43 analyze --design configs/uc4/monte_carlo.yaml --output reports/generated/uc4/monte_carlo
```

This runs the deterministic nominal case and the complete declared 100-sample uncertainty design. It records every seed and sample, reports 95% confidence intervals without converting undefined metrics to zero, and generates a sensitivity heatmap. Results are explicitly synthetic and uncalibrated. See `docs/analysis/UC4_metrics_and_sensitivity.md` and the committed `reports/generated/uc4/monte_carlo/monte_carlo_report.md`.

## Stage 11 validation evidence

The consolidated status and proposal/roadmap-to-test traceability table are in `reports/validation/UC4_validation_matrix.md`. The clean-install execution summary is `reports/validation/UC4_stage11_test_report.md`, with machine-readable test cases in `reports/validation/UC4_stage11_junit.xml`.

## Integration and final handoff

The authoritative machine-readable contract set is `contracts/integration/uc4_integration_contracts.yaml`. It defines the T4.4, T4.2, T3.3, T3.4, T3.5, T3.1/T3.6, and WP6 UC4 boundaries, including schemas, required fields, authorization constraints, failure behavior, assumptions, and adapter replacement procedures. See `docs/integration/UC4_integration_contracts.md`.

Generate and verify the final hash inventory after any change:

```powershell
salus-t43 manifest --output reports/final/UC4_artifact_manifest.json
```

The manifest excludes itself, caches, bytecode, virtual environments, and editable-install metadata. This prevents recursive hashes and keeps build products out of the deliverable inventory.

## Add an entity safely

1. Assign the next stable UC4 ID and add the entity to `models/instances/uc4_entities.json` and `data/inventory/uc4_entity_inventory.csv` with identical provenance.
2. Add typed relationships with new stable IDs to `models/relationships/uc4_relationships.csv`.
3. If the entity has a twin, add reciprocal physical/twin fields plus `MIRRORED_BY` and `SYNCHRONIZES_WITH` relations.
4. Add its validated device/runtime configuration only if it participates in simulation; never infer manufacturer, protocol, rate, or ownership.
5. Update the relevant BPMN/model documentation and tests, then run validation, tests, experiments, analysis when affected, and regenerate the artifact manifest.

## Add or replace a calibrated parameter

Copy a canonical YAML configuration rather than overwriting the synthetic reference. Record the parameter's explicit unit, measurement source, sampling period, uncertainty, device/firmware context, and assumption/provenance ID. Keep secrets and personal/pilot data outside version control. Validate the new configuration, compare equal-seed results against the reference, justify any new Monte Carlo distribution and sample count before viewing outcomes, and regenerate reports and the final manifest.

## Limitations

- The scenario, devices, observations, authorizations, custody service, network, and integrations are synthetic or abstract unless explicitly marked otherwise.
- A hash chain is not a production blockchain, and passing policy/custody tests does not prove legal compliance or evidentiary admissibility.
- T4.2 SDaaSS is disabled; T3.3 AI/XAI and T3.4 threat-intelligence endpoints are abstract; evidence sharing, encryption/KMS, and deployment RBAC require external adapters.
- Candidate datasets and real WP6 measurements are not calibrated into this model.
- Results must not be described as real-device fidelity, production readiness, partner validation, or pilot KPI performance.
