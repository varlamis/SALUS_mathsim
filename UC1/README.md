# SALUS T4.3 UC1 Car2X model

This self-contained package models a controlled forged/replayed Car2X request involving a synthetic police test vehicle, OBU, RSU, traffic-signal controller, trust validation, explainable detection, policy mitigation, Digital Twins, and forensic reconstruction.

All executions are synthetic. The code performs no real radio transmission, penetration, vehicle control, traffic-light control, or production SDN action.

## Install

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pip install --no-deps -e .
```

## Validate and test

```powershell
salus-uc1 validate --config configs/uc1/forged_message_attack.yaml
python -m pytest -q
```

## Run

```powershell
salus-uc1 run --config configs/uc1/forged_message_attack.yaml
salus-uc1 experiment --matrix configs/uc1/experiments.yaml
salus-uc1 analyze --design configs/uc1/monte_carlo.yaml
```

The canonical model is in `models/`, explanatory material is in `docs/`, editable processes are in `diagrams/`, and generated results are written below `reports/generated/uc1/`.

## Limitations

The message envelope, trust check, radio/network channel, detector, SDN response, traffic signal, and evidence services are bounded abstractions. Results do not establish pilot fidelity, standards conformance, legal compliance, safety certification, production readiness, or attainment of proposal-wide KPIs.

