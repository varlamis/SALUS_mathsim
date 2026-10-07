# Dependency and lock strategy

`pyproject.toml` pins direct runtime, test, and build dependencies exactly. `requirements.lock` additionally pins the complete transitive Python 3.12 environment used for the clean Stage 11/12 verification. This favors reproducibility of the final handoff over automatic dependency upgrades.

## Reproduce the locked environment

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pip install --no-deps -e .
.venv\Scripts\python -m pip check
.venv\Scripts\python -m pytest -q
```

The lock is a cross-platform version lock, not a wheel-hash lock. A release pipeline should generate platform-specific, hash-locked files with `pip-compile --generate-hashes` or an equivalent approved tool for every supported Python/platform combination.

## Controlled update procedure

1. Create a fresh branch and isolated Python 3.12 environment.
2. Update one direct pin or a coherent dependency group in `pyproject.toml`.
3. Resolve all transitive versions and replace `requirements.lock`; never edit only a transitive pin without recording why.
4. Run `pip check`, both repository validation commands, all tests, the 16-branch experiment matrix, and the 100-sample analysis.
5. Compare canonical hashes and explain every intentional change.
6. Update `CHANGELOG.md`, regenerate `reports/final/UC4_artifact_manifest.json`, and review dependency licenses/security advisories before release.

Generated virtual environments, caches, bytecode, editable-install metadata, credentials, and pilot data are not final artefacts and are excluded from the manifest.
