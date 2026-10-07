# UC5 test report

- Result: **PASS**
- Automated tests: 13 passed, 0 failed
- Validation inventory: 34 entities, 45 relationships, 9 schemas, 8 BPMN files
- Experiment matrix: 9/9 branches passed
- Monte Carlo: 100/100 samples exported
- Warnings: `jsonschema.RefResolver` deprecation warning only; no correctness failure

The suite covers repository validation, explainability, continuity-constrained isolation, privacy/redaction, unauthorized-sharing denial, complete observation loss, health-fault separation, determinism, evidence/custody, hidden-truth separation, experiment invariants, manifest tamper detection and two schema-valid golden fixtures.
