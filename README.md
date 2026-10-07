# SALUS mathematical simulation Public Evidence Repository

This folder contains the curated public evidence package supporting the claims
reported in the SALUS digital-twin framework paper. It is organized by use case
(`UC1`--`UC5`) and includes only the files needed to inspect the framework
implementation, reproduce the reported synthetic evidence, and verify the
artifact chain used in the paper.

## Scope

Each use-case folder contains the relevant:

- `models/`: canonical entities, relationships, schemas, graphs, and formal
  model material.
- `configs/`: deterministic, experiment, and Monte Carlo configurations.
- `contracts/`: integration or artifact contracts used by the implementation.
- `diagrams/`: process, lifecycle, and relationship views.
- `docs/`: source-governed case descriptions, assumptions, graph queries,
  process notes, validation plans, and analysis notes.
- `src/`: executable Python implementation used to generate the reported
  artifacts.
- `tests/`: retained automated tests and fixtures.
- `reports/generated/`: generated run outputs, metrics, experiment comparisons,
  Monte Carlo summaries, evidence manifests, and validation reports.
- `reports/validation/`, `reports/final/`, and `reports/latex/`: validation
  summaries, final handoff material, manifests, and technical-report sources.

## Exclusions

The public bundle intentionally excludes caches, virtual environments, temporary
test directories, Python bytecode, placeholder files, compiled PDFs, and raw
operational data. The available data directories in the original project
describe governance and acquisition boundaries; they are not required to
support the synthetic claims reported in the paper.

## Reading Order

For each UC, start with `EVIDENCE_README.md`, then inspect `docs/`,
`models/`, `configs/`, and `reports/generated/`. The `reports/final/` manifests
link the retained artifacts to the completed handoff evidence.
