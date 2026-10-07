# UC5 medical-device monitoring digital twin

This self-contained package implements the synthetic UC5 vertical slice specified in `../../readme_UC5.md`: a compromised patient monitor produces anomalous outbound flow, an explainable detector raises an alert, and a clinical-continuity gate decides whether isolation is safe. Evidence is minimized, chained, redacted, and shared only when authorized.

The package never connects to medical equipment or hospital systems, contains no patient data or clinical payload, and cannot diagnose, treat, or actuate. Its outputs demonstrate model behavior only; they do not establish clinical safety, regulatory compliance, hospital fidelity, or proposal KPI achievement.

## Reproduce

From `UC5/`, with the repository virtual environment:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe -m salus_t43.cli validate --config configs/uc5/compromised_monitor.yaml --write-graph
..\.venv\Scripts\python.exe -m salus_t43.cli run --config configs/uc5/baseline.yaml --output reports/generated/uc5/baseline
..\.venv\Scripts\python.exe -m salus_t43.cli run --config configs/uc5/compromised_monitor.yaml --output reports/generated/uc5/compromised_monitor
..\.venv\Scripts\python.exe -m salus_t43.cli experiment --config configs/uc5/experiments.yaml --output reports/generated/uc5/experiments
..\.venv\Scripts\python.exe -m salus_t43.cli analyze --config configs/uc5/monte_carlo.yaml --output reports/generated/uc5/monte_carlo
..\.venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp
```

The nominal bundle contains separated ground truth and observations, alerts with feature contributions, safety and policy decisions, requested/applied mitigations, evidence and custody records, a redacted sharing package, evidence-only reconstruction, graph queries, metrics, validation, and a canonical run hash.

## Key model boundary

Isolation is eligible only when authorization and enforcement are available and either the monitored device is nonessential or an approved backup is active. Otherwise the model records a safety rejection and keeps essential-monitoring interruption at zero.

