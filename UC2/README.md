# SALUS T4.3 UC2 passive IoT detection model

This self-contained package implements passive, synthetic multi-interface IoT
observation, pseudonymous association and categorization, approval checking,
explainable alerting, bounded review response, Digital Twins, evidence custody
and reconstruction. It has no live RF, interception, interference, subscriber
identity, payload capture, location tracking or operational response capability.

## Verify and execute

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pip install --no-deps -e .
salus-uc2 validate --config configs/uc2/unapproved_device.yaml --write-graph
salus-uc2 run --config configs/uc2/unapproved_device.yaml
salus-uc2 experiment --matrix configs/uc2/experiments.yaml
salus-uc2 analyze --design configs/uc2/monte_carlo.yaml
python -m pytest -q
```

All outputs are synthetic model evidence. They do not establish surveillance
authority, real RF/device performance, legal compliance, or project KPI
attainment.

