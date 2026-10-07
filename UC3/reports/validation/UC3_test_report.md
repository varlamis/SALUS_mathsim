# UC3 automated test report

- Execution date: 2026-09-10
- Command: `python -m pytest -q --basetemp=.pytest_tmp --junitxml=reports/validation/UC3_junit.xml`
- Result: **21 passed, 0 failed, 0 errors**
- Duration reported by isolated-environment pytest: 4.47 seconds
- Machine-readable evidence: `UC3_junit.xml`

Coverage includes strict configuration, process bounds, deterministic execution, hidden-truth isolation, complete export, entity/relationship graph integrity, experiment assertions, seeded analysis, evidence and custody tampering, integration boundaries, BPMN parsing, and artifact manifests.

Two non-failing warnings identify the upstream deprecation of `jsonschema.RefResolver`; migration to `referencing` is a maintenance action.
