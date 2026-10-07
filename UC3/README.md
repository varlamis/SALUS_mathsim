# SALUS T4.3 UC3 industrial cyber-physical model

This self-contained package implements a deterministic, fully synthetic industrial level-control cell with symbolic protocol-aware fuzzing, unauthorized-write attempts, bounded application load, explainable detection, safety-constrained policy response, Digital Twins, evidence custody, graph queries, and reconstruction.

It never connects to or describes an operational nuclear facility, PLC, SCADA system, actuator, protocol endpoint, or production SDN service. The process is a mathematical surrogate and results do not establish plant fidelity, safety certification, legal compliance, protocol conformance, or proposal KPI attainment.

## Install and verify

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pip install --no-deps -e .
salus-uc3 validate --config configs/uc3/smart_fuzzing_attack.yaml
python -m pytest -q
```

## Execute

```powershell
salus-uc3 run --config configs/uc3/smart_fuzzing_attack.yaml
salus-uc3 experiment --matrix configs/uc3/experiments.yaml
salus-uc3 analyze --design configs/uc3/monte_carlo.yaml
salus-uc3 manifest
```

The implementation contract is [`../../readme_UC3.md`](../../readme_UC3.md). Canonical inputs are under `models/` and `configs/`; generated results are under `reports/generated/uc3/`.
