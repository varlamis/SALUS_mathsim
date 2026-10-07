# UC2 test report

- Result: **PASS**
- Automated tests: 11 passed, 0 failed
- Validation inventory: 25 entities, 26 relationships, 9 schemas, 7 BPMN files
- Experiment matrix: 9/9 branches passed
- Monte Carlo: 100/100 samples exported
- Warnings: `jsonschema.RefResolver` deprecation warning only; no correctness failure

The suite covers repository validation, passive/privacy invariants, determinism, complete observation loss, explicit queue overflow, evidence/custody verification, hidden-truth separation, matrix expectations, manifest tamper detection and two schema-valid golden fixtures.
