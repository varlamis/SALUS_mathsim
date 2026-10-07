# UC1 automated test report

- Execution date: 2026-09-10
- Interpreter: project `.venv`
- Command: `python -m pytest -q --basetemp=.pytest_tmp --junitxml=reports/validation/UC1_junit.xml`
- Result: **22 passed, 0 failed, 0 errors**
- Duration reported by pytest: 1.50 seconds
- Machine-readable result: `UC1_junit.xml`

The suite covers schema and cross-reference validation, graph competency queries,
deterministic event ordering, simulation safety invariants, evidence minimisation
and chain-of-custody integrity, experiment/Monte Carlo analysis, integration
contracts, BPMN referential integrity, complete run-bundle export, and artifact
manifest tamper detection.

Two warnings are emitted because `jsonschema.RefResolver` is deprecated. This is
not a validation failure; migration to the `referencing` package is recorded as a
future maintenance action.
