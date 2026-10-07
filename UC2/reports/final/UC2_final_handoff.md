# UC2 final handoff

## Delivered vertical slice

UC2 implements deterministic passive multi-interface observation, pseudonymous association/classification, approved-device registry lookup, explainable alerting, bounded non-RF policy, minimized evidence/custody, evidence-only reconstruction, graph queries and uncertainty analysis. No live radio interface or active RF action exists.

## Reproduced results

- Baseline canonical hash: `2a813709ea8f0f7761c74a4d418d6b0bb5616fb370ce0855c168a4130746a502`.
- Nominal unapproved-device canonical hash: `1b17a1d56b53d3b78651c4c9bae773dfe05fa617f907042a664a576b22b833e7`.
- Nominal metrics: 45 delivered observations, 3 lost observations, 4 classifications, 1 alert, 0 queue overflow, 0 process effects, 0 safety violations, 0 active RF actions and 0 unauthorized disclosures.
- All 9 negative/alternative experiment branches pass the passive and privacy invariants.
- The uncertainty run exports 100 seeded samples; these characterize synthetic implementation behavior only.
- 11 automated tests pass, including schema validation of the retained event and evidence fixtures.

## Expert-owned open parameters

Observer capability and lawful collection boundary; interface feature dictionaries; association windows; classification calibration and ground truth; approved-device registry semantics/freshness; response authorization; evidence purpose/retention; DS2/DS3 access and mapping; partner interfaces; and WP6 baselines remain TBD.

## Reproduce and verify

Use the commands in `README.md`. Verify `reports/final/UC2_artifact_manifest.json` with the CLI after any change. The manifest must be regenerated only after reviewed changes because it hashes the complete package.

## Claims boundary

The deliverable is a synthetic executable specification. It does not demonstrate real-device identification accuracy, lawful operational surveillance, person attribution, production readiness or proposal KPI attainment.
