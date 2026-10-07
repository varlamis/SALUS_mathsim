# UC1 Evidence Package

UC1 supports the Car2X trust-before-control scenario discussed in the paper and
detailed in the appendices.

Key evidence:

- `models/instances/uc1_entities.json` and
  `models/relationships/uc1_relationships.csv` define the canonical entity and
  relationship model.
- `models/formal/` and `diagrams/` provide the formal and process views.
- `configs/uc1/forged_message_attack.yaml`,
  `configs/uc1/experiments.yaml`, and `configs/uc1/monte_carlo.yaml` define the
  nominal, degraded-branch, and uncertainty runs.
- `src/` contains the executable simulator, graph, evidence, queue, and analysis
  code.
- `tests/` contains the automated validation suite and fixtures.
- `reports/generated/uc1/` contains nominal metrics, experiment comparisons,
  Monte Carlo summaries, run manifests, evidence manifests, and validation
  reports.
- `reports/final/UC1_artifact_manifest.json` and
  `reports/final/UC1_final_handoff.md` summarize the retained evidence.
