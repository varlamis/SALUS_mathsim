# UC4 Stage 11 test and validation report

## Outcome

Stage 11 passed on 2026-09-08. A fresh Python 3.12 virtual environment was created, the repository was installed from `.[test]`, and the complete test suite executed with the declared dependency ranges. The temporary environment was removed after execution; the JUnit result is retained.

| Check | Result |
|---|---|
| Clean editable installation | Pass |
| Automated tests | 43 passed, 0 failed, 0 errors, 0 skipped |
| Lawful-incident repository validation | Valid: 7 schemas, 38 entities, 123 relationships, 7 BPMN files |
| Baseline repository validation | Valid: 7 schemas, 38 entities, 123 relationships, 7 BPMN files |
| Stage 8 experiment matrix | Valid: 16 branches, 0 assertion failures |
| Stage 10 uncertainty design | 100 recorded samples with CIs and seed ledger |
| JUnit SHA-256 | `d90fd34c549ef97253010487c8f899f8ae8ccd58063339157556afb03d89ce50` |

The only warning concerned pytest's optional cache directory being non-writable in the managed workspace. It did not affect collection, setup, execution, assertions, JUnit generation, or exit status.

## Stage 11 additions

- Purpose equality is now an explicit fail-closed authorization term alongside decision state, verification, active interval, evidence window, entity, data type, and action scope.
- Configuration migration is explicit and deterministic: current `1.0.0` documents are validated as no-ops; legacy `0.9.0` documents receive the two documented Stage 10 defaults; unsupported versions fail.
- Canonical ID, relationship-vocabulary, and reciprocal one-to-one physical/twin mappings receive a consolidated test.
- Equal seeds repeat and different seeds are proven to alter stochastic outputs.
- The exported hidden movement marker is asserted absent from all investigator-facing artefacts.
- End-to-end evidence IDs are checked across evidence, custody, and runtime-graph outputs.

## Reproduction

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest -q --junitxml=reports/validation/UC4_stage11_junit.xml
.venv\Scripts\salus-t43 validate --config configs/uc4/incident_lawful_access.yaml
.venv\Scripts\salus-t43 validate --config configs/uc4/baseline.yaml
```

The full judgment-by-judgment assessment and requirement traceability are in `reports/validation/UC4_validation_matrix.md`.

## Interpretation boundary

This verifies internal consistency and behavior of the synthetic implementation. It does not validate partner infrastructure, actual CPE or Home Assistant adapters, candidate datasets, legal compliance, evidentiary admissibility, or pilot performance.
