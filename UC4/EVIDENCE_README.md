# UC4 Evidence Package

UC4 supports the smart-home lawful evidence and reconstruction scenario.

Key evidence:

- `models/` contains the canonical entity graph, relationship model, schemas,
  and formal/equation material.
- `configs/uc4/` defines the nominal lawful-incident run, degraded branches,
  authorization cases, tamper cases, and Monte Carlo configuration.
- `docs/` and `diagrams/` describe the assumptions, legal/authorization scope,
  process views, graph queries, and validation design.
- `src/` contains the executable implementation for acquisition, evidence,
  custody, reconstruction, metrics, and analysis.
- `tests/` contains the retained automated tests and fixtures.
- `reports/generated/uc4/experiments/` contains per-branch metrics, run
  manifests, evidence manifests, validation reports, and experiment comparison
  summaries.
- `reports/generated/uc4/monte_carlo/` contains the uncertainty-analysis
  outputs used in the paper.
- `reports/final/` contains the final handoff, artifact manifest, and retained
  JUnit evidence.
