# UC5 metrics and uncertainty analysis

## Metric families

- Observation: generated, delivered, lost, delayed and queue-overflow counts.
- Detection: alerts, truth-only evaluation recall/precision where denominators exist, false positives and latency.
- Response: requested, applied and safety-rejected actions; containment time.
- Continuity: device/service availability and essential-monitoring interruption count, whose invariant is zero.
- Evidence: capture completeness, integrity, custody verification and reconstruction coverage.
- Privacy/sharing: authorization outcome, redaction result, patient-data disclosure count (zero invariant) and sharing delay.

Undefined rates are reported as undefined rather than coerced to zero. Ground truth participates only in evaluation metrics.

The Monte Carlo plan predeclares 100 seeded samples over normal rate/bytes, attack multiplier, loss/delay, observation probability, detector threshold, health missingness, review/enforcement delay, backup availability and sharing delay. Summaries report sample distributions and a rank-based sensitivity screen. With synthetic ranges and 100 samples, results characterize implementation behavior only; they neither establish clinical risk nor validate proposal KPIs.
